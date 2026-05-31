"""
Email service for sending property alerts via Resend.
Handles both confirmation emails and monthly digest emails.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import pystache
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = os.getenv("RESEND_API_KEY")

# Email templates directory
TEMPLATES_DIR = Path(__file__).parent / "email_templates"


def _load_template(template_name: str) -> str:
    """Load email template from file."""
    template_path = TEMPLATES_DIR / f"{template_name}.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def _render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render email template with context using Mustache."""
    template = _load_template(template_name)
    renderer = pystache.Renderer()
    return renderer.render(template, context)


def send_confirmation_email(
    email: str,
    address: str,
    radius_km: float,
    county: Optional[str],
    unsubscribe_token: str,
    properties: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Send subscription confirmation email with recent matching properties.

    Args:
        email: Recipient email address
        address: Search address/area
        radius_km: Search radius in km
        county: Optional county filter
        unsubscribe_token: Token for unsubscribe link
        properties: Optional list of recent properties (up to 10)

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Format properties for template (limit to 10)
        formatted_properties = []
        if properties:
            for prop in properties[:10]:
                formatted_properties.append({
                    "id": prop.get("id"),
                    "property_address": prop.get("address", ""),
                    "price_formatted": f"{int(prop.get('price', 0)):,}",
                    "sale_date": prop.get("sale_date", ""),
                    "county": prop.get("county", ""),
                    "address_encoded": quote(prop.get("address", "")),  # Use property address, not subscription address
                    "radius_km": radius_km,
                })

        context = {
            "address": address,
            "radius_km": radius_km,
            "county": county if county else None,
            "address_encoded": quote(address),
            "unsubscribe_token": unsubscribe_token,
            "has_properties": len(formatted_properties) > 0,
            "properties": formatted_properties,
            "property_count": len(formatted_properties),
        }

        html_content = _render_template("confirmation", context)

        # Plain text fallback
        property_lines = []
        if properties:
            for prop in properties[:10]:
                property_lines.append(f"€{int(prop.get('price', 0)):,} - {prop.get('address', '')}")
                property_lines.append(f"  Sold: {prop.get('sale_date', '')}")
                property_lines.append("")

        plain_text = f"""
HomeIQ - Subscription Confirmed

You've successfully subscribed to property price alerts for:

Location: {address}
Radius: {radius_km} km
{f'County: {county}' if county else ''}

You'll receive monthly email alerts when new properties matching your criteria are added to the Property Price Register.

{f'Recent properties in this area:{chr(10)}{chr(10)}{chr(10).join(property_lines)}' if property_lines else ''}

View current properties: https://homeiq.ie/?q={quote(address)}&radius_km={radius_km}

Privacy Notice: Your information will not be shared with third parties. You will receive at most one email per month.

Unsubscribe: https://homeiq.ie/email-alerts/unsubscribe/{unsubscribe_token}
        """.strip()

        params = {
            "from": "HomeIQ Property Alerts <alerts@homeiq.ie>",
            "to": [email],
            "subject": f"Subscription Confirmed: Property Alerts for {address}",
            "html": html_content,
            "text": plain_text,
            "headers": {
                "List-Unsubscribe": f"<https://homeiq.ie/email-alerts/unsubscribe/{unsubscribe_token}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
            }
        }

        response = resend.Emails.send(params)
        logger.info(f"Confirmation email sent to {email}: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send confirmation email to {email}: {e}")
        return False


def send_monthly_digest(
    email: str,
    address: str,
    radius_km: float,
    county: Optional[str],
    properties: List[Dict[str, Any]],
    unsubscribe_token: str
) -> bool:
    """
    Send monthly property digest email.

    Args:
        email: Recipient email address
        address: Search address/area
        radius_km: Search radius in km
        county: Optional county filter
        properties: List of property dicts with keys: id, address, price, sale_date, county, description
        unsubscribe_token: Token for unsubscribe link

    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        if not properties:
            logger.info(f"No properties to send for {email}, skipping email")
            return False

        # Limit to 15 properties in email, show "and X more"
        MAX_PROPERTIES = 15
        display_properties = properties[:MAX_PROPERTIES]
        has_more = len(properties) > MAX_PROPERTIES
        remaining_count = len(properties) - MAX_PROPERTIES if has_more else 0

        # Format properties for template
        formatted_properties = []
        for prop in display_properties:
            formatted_properties.append({
                "id": prop.get("id"),
                "property_address": prop.get("address", ""),
                "price_formatted": f"{int(prop.get('price', 0)):,}",
                "sale_date": prop.get("sale_date", ""),
                "county": prop.get("county", ""),
                "description": prop.get("description", ""),
                "address_encoded": quote(prop.get("address", "")),  # Use property address, not subscription address
                "radius_km": radius_km,
            })

        context = {
            "address": address,
            "radius_km": radius_km,
            "property_count": len(properties),
            "plural": len(properties) > 1,
            "properties": formatted_properties,
            "has_more": has_more,
            "remaining_count": remaining_count,
            "address_encoded": quote(address),
            "unsubscribe_token": unsubscribe_token,
        }

        html_content = _render_template("monthly_digest", context)

        # Plain text fallback
        property_lines = []
        for prop in display_properties[:10]:  # Limit plain text to 10
            property_lines.append(f"€{int(prop.get('price', 0)):,} - {prop.get('address', '')}")
            property_lines.append(f"  Sold: {prop.get('sale_date', '')}")
            property_lines.append("")

        plain_text = f"""
HomeIQ - New Properties in {address}

{len(properties)} new {'properties' if len(properties) > 1 else 'property'} this month within {radius_km}km:

{chr(10).join(property_lines)}

View all properties: https://homeiq.ie/?q={quote(address)}&radius_km={radius_km}

You're receiving this because you subscribed to property alerts for {address} ({radius_km}km radius).

Unsubscribe: https://homeiq.ie/email-alerts/unsubscribe/{unsubscribe_token}
        """.strip()

        params = {
            "from": "HomeIQ Property Alerts <alerts@homeiq.ie>",
            "to": [email],
            "subject": f"New Properties in {address}: {len(properties)} {'properties' if len(properties) > 1 else 'property'} this month",
            "html": html_content,
            "text": plain_text,
            "headers": {
                "List-Unsubscribe": f"<https://homeiq.ie/email-alerts/unsubscribe/{unsubscribe_token}>",
                "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
            }
        }

        response = resend.Emails.send(params)
        logger.info(f"Monthly digest sent to {email}: {len(properties)} properties, response: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send monthly digest to {email}: {e}")
        return False
