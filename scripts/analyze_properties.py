#!/usr/bin/env python3
"""
Property data analysis tool for HomeIQ database.
Quick queries for common analysis tasks.
"""
import os
import sys
import asyncpg
import asyncio
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv('backend/.env')


async def total_properties():
    """Total properties in database."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    total = await conn.fetchval('SELECT COUNT(*) FROM properties')
    geocoded = await conn.fetchval('SELECT COUNT(*) FROM properties WHERE latitude IS NOT NULL')
    await conn.close()

    print(f"Total properties: {total:,}")
    print(f"Geocoded: {geocoded:,} ({geocoded/total*100:.1f}%)")


async def multi_sale_analysis():
    """Analyze properties sold multiple times."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    stats = await conn.fetchrow('''
        WITH address_counts AS (
            SELECT address, COUNT(*) as sale_count
            FROM properties
            GROUP BY address
            HAVING COUNT(*) > 1
        )
        SELECT
            COUNT(*) as unique_properties,
            SUM(sale_count) as total_records,
            MAX(sale_count) as max_sales
        FROM address_counts
    ''')

    await conn.close()

    print(f"Properties sold multiple times: {stats['unique_properties']:,}")
    print(f"Total multi-sale records: {stats['total_records']:,}")
    print(f"Maximum sales for one property: {stats['max_sales']}")


async def price_trends_by_county(county):
    """Show price trends for a county."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    trends = await conn.fetch('''
        SELECT
            EXTRACT(YEAR FROM sale_date) as year,
            COUNT(*) as sales,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM properties
        WHERE county = $1
          AND not_full_market_price = FALSE
          AND price > 0
        GROUP BY year
        ORDER BY year
    ''', county)

    await conn.close()

    print(f"\nPrice Trends for {county}:")
    print("-" * 80)
    print(f"{'Year':<6} {'Sales':<8} {'Median':<12} {'Average':<12} {'Min':<12} {'Max':<12}")
    print("-" * 80)

    for row in trends:
        print(f"{int(row['year']):<6} {row['sales']:<8,} "
              f"€{row['median_price']:>10,.0f} "
              f"€{row['avg_price']:>10,.0f} "
              f"€{row['min_price']:>10,.0f} "
              f"€{row['max_price']:>10,.0f}")


async def search_address(query):
    """Search for properties by address."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    results = await conn.fetch('''
        SELECT sale_date, address, county, price, eircode
        FROM properties
        WHERE address ILIKE $1
        ORDER BY sale_date DESC
        LIMIT 50
    ''', f'%{query}%')

    await conn.close()

    print(f"\nFound {len(results)} sales matching '{query}':")
    print("-" * 100)

    for i, row in enumerate(results, 1):
        print(f"{i}. {row['sale_date']} | €{row['price']:>10,.0f} | {row['address']}")


async def geocoding_stats():
    """Geocoding quality statistics."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    stats = await conn.fetchrow('''
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL) as geocoded,
            COUNT(*) FILTER (WHERE eircode IS NOT NULL) as with_eircode,
            COUNT(*) FILTER (WHERE latitude IS NOT NULL AND eircode IS NOT NULL) as both
        FROM properties
    ''')

    await conn.close()

    total = stats['total']
    print(f"Total properties: {total:,}")
    print(f"Geocoded: {stats['geocoded']:,} ({stats['geocoded']/total*100:.1f}%)")
    print(f"With Eircode: {stats['with_eircode']:,} ({stats['with_eircode']/total*100:.1f}%)")
    print(f"Both geocoded + Eircode: {stats['both']:,} ({stats['both']/total*100:.1f}%)")


async def county_summary():
    """Sales count and average price by county."""
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))

    counties = await conn.fetch('''
        SELECT
            county,
            COUNT(*) as sales,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
            AVG(price) as avg_price
        FROM properties
        WHERE not_full_market_price = FALSE
          AND price > 0
        GROUP BY county
        ORDER BY sales DESC
    ''')

    await conn.close()

    print("\nSales by County:")
    print("-" * 70)
    print(f"{'County':<20} {'Sales':<10} {'Median Price':<15} {'Avg Price':<15}")
    print("-" * 70)

    for row in counties:
        print(f"{row['county']:<20} {row['sales']:<10,} "
              f"€{row['median_price']:>12,.0f} "
              f"€{row['avg_price']:>12,.0f}")


COMMANDS = {
    'total': ('Show total properties and geocoding rate', total_properties),
    'multi': ('Analyze properties with multiple sales', multi_sale_analysis),
    'trends': ('Price trends by county (e.g., trends Dublin)', lambda county: price_trends_by_county(county)),
    'search': ('Search properties by address (e.g., search Broomfield)', lambda query: search_address(query)),
    'geocoding': ('Geocoding quality statistics', geocoding_stats),
    'counties': ('Sales and prices by county', county_summary),
}


def print_help():
    print("\nHomeIQ Property Data Analysis Tool")
    print("=" * 80)
    print("\nUsage: python3 scripts/analyze_properties.py <command> [args]")
    print("\nAvailable commands:")
    for cmd, (desc, _) in COMMANDS.items():
        print(f"  {cmd:<12} {desc}")
    print("\nExamples:")
    print("  python3 scripts/analyze_properties.py total")
    print("  python3 scripts/analyze_properties.py trends Dublin")
    print("  python3 scripts/analyze_properties.py search 'Broomfield, Midleton'")
    print()


async def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command not in COMMANDS:
        print(f"Unknown command: {command}")
        print_help()
        return

    desc, func = COMMANDS[command]

    # Check if command needs arguments
    if command in ['trends', 'search']:
        if len(sys.argv) < 3:
            print(f"Error: '{command}' requires an argument")
            print(f"Example: python3 scripts/analyze_properties.py {command} <value>")
            return
        arg = ' '.join(sys.argv[2:])
        await func(arg)
    else:
        await func()


if __name__ == '__main__':
    asyncio.run(main())
