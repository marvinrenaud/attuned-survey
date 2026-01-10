import resend
from typing import Optional
import logging

from ..config import settings
from .email_templates import PARTNER_REQUEST_TEMPLATE, PARTNER_ACCEPTED_TEMPLATE

logger = logging.getLogger(__name__)

# Initialize Resend with API key from settings
resend.api_key = settings.RESEND_API_KEY

DEFAULT_FROM = "Attuned <love@getattuned.app>"  # All emails from love@

def send_partner_request(recipient_email: str, requester_name: str, request_url: str) -> bool:
    """Send partner request notification."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Skipping email sending.")
        return False

    try:
        html_content = PARTNER_REQUEST_TEMPLATE.format(
            partner_name=requester_name,
            invite_url=request_url
        )

        params: resend.Emails.SendParams = {
            "from": DEFAULT_FROM,
            "to": [recipient_email],
            "subject": "Attuned: You have a new play partner request, love.",
            "html": html_content
        }
        resend.Emails.send(params)
        logger.info(f"Partner request email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email error (send_partner_request): {e}")
        return False


def send_partner_accepted(recipient_email: str, partner_name: str, user_name: str = "Love") -> bool:
    """
    Notify user their partner request was accepted.
    
    :param recipient_email: Email of the user who sent the original request (now receiving acceptance)
    :param partner_name: Name of the partner who accepted the request
    :param user_name: Name of the recipient (original requester)
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Skipping email sending.")
        return False

    try:
        app_url = "https://getattuned.app/home" # Or a specific deep link if needed
        
        html_content = PARTNER_ACCEPTED_TEMPLATE.format(
            user_name=user_name,
            partner_name=partner_name,
            app_url=app_url
        )

        params: resend.Emails.SendParams = {
            "from": DEFAULT_FROM,
            "to": [recipient_email],
            "subject": "Attuned: You have a new play partner, love.",
            "html": html_content
        }
        resend.Emails.send(params)
        logger.info(f"Partner acceptance email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email error (send_partner_accepted): {e}")
        return False
