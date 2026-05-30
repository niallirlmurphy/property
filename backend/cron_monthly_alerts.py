"""
Monthly property alert cron job.
Queries active subscriptions and sends digest emails for new properties.
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
import asyncpg
from dotenv import load_dotenv
from email_service import send_monthly_digest

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_new_properties_for_subscription(
    pool: asyncpg.Pool,
    subscription: Dict[str, Any],
    geocode_query: str
) -> List[Dict[str, Any]]:
    """
    Find properties added since last_sent_at that match subscription criteria.

    Args:
        pool: Database connection pool
        subscription: Subscription dict with email, address, radius_km, county, last_sent_at
        geocode_query: SQL query to geocode the address

    Returns:
        List of property dicts
    """
    try:
        # First, geocode the address to get lat/lon
        geocode_result = await pool.fetchrow(geocode_query, subscription['address'])

        if not geocode_result or not geocode_result['latitude']:
            logger.warning(f"Could not geocode address: {subscription['address']}")
            return []

        lat = geocode_result['latitude']
        lon = geocode_result['longitude']

        # Find properties within radius added since last_sent_at (or created_at if never sent)
        since_date = subscription['last_sent_at'] or subscription['created_at']

        query = """
            SELECT id, address, price, sale_date, county, description,
                   ST_Distance(geog, ST_MakePoint($1, $2)::geography) / 1000 AS distance_km
            FROM properties
            WHERE geog IS NOT NULL
              AND ST_DWithin(geog, ST_MakePoint($1, $2)::geography, $3 * 1000)
              AND created_at > $4
              AND not_full_market_price = FALSE
        """

        params = [lon, lat, subscription['radius_km'], since_date]

        # Add county filter if specified
        if subscription.get('county'):
            query += " AND county = $5"
            params.append(subscription['county'])

        query += " ORDER BY sale_date DESC LIMIT 50"

        rows = await pool.fetch(query, *params)

        properties = []
        for row in rows:
            properties.append({
                "id": row['id'],
                "address": row['address'],
                "price": row['price'],
                "sale_date": row['sale_date'].strftime("%Y-%m-%d") if row['sale_date'] else "",
                "county": row['county'] or "",
                "description": row['description'] or "",
                "distance_km": round(row['distance_km'], 2)
            })

        logger.info(f"Found {len(properties)} new properties for {subscription['email']} ({subscription['address']})")
        return properties

    except Exception as e:
        logger.error(f"Error finding properties for {subscription['email']}: {e}")
        return []


async def process_monthly_alerts():
    """Main cron job function to process all active email alerts."""
    logger.info("Starting monthly property alerts job")

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=5)

    try:
        # Get all active subscriptions
        subscriptions = await pool.fetch("""
            SELECT id, email, address, radius_km, county, created_at, last_sent_at, unsubscribe_token
            FROM email_alerts
            WHERE is_active = TRUE
            ORDER BY created_at ASC
        """)

        logger.info(f"Processing {len(subscriptions)} active subscriptions")

        # Geocode query (reuse from main.py logic)
        geocode_query = """
            SELECT latitude, longitude
            FROM properties
            WHERE address ILIKE $1 || '%'
              AND latitude IS NOT NULL
            LIMIT 1
        """

        emails_sent = 0
        errors = 0

        for sub in subscriptions:
            try:
                # Find new properties for this subscription
                properties = await get_new_properties_for_subscription(pool, dict(sub), geocode_query)

                if properties:
                    # Send digest email
                    success = send_monthly_digest(
                        email=sub['email'],
                        address=sub['address'],
                        radius_km=sub['radius_km'],
                        county=sub['county'],
                        properties=properties,
                        unsubscribe_token=sub['unsubscribe_token']
                    )

                    if success:
                        # Update last_sent_at timestamp
                        await pool.execute("""
                            UPDATE email_alerts
                            SET last_sent_at = CURRENT_TIMESTAMP
                            WHERE id = $1
                        """, sub['id'])
                        emails_sent += 1
                        logger.info(f"✓ Sent digest to {sub['email']}: {len(properties)} properties")
                    else:
                        logger.error(f"✗ Failed to send digest to {sub['email']}")
                        errors += 1
                else:
                    logger.info(f"No new properties for {sub['email']} ({sub['address']}), skipping email")

            except Exception as e:
                logger.error(f"Error processing subscription {sub['id']} ({sub['email']}): {e}")
                errors += 1

        logger.info(f"Monthly alerts job complete: {emails_sent} emails sent, {errors} errors")

    except Exception as e:
        logger.error(f"Fatal error in monthly alerts job: {e}")
        raise

    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(process_monthly_alerts())
