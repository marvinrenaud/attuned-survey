import resend
from typing import Optional
import logging

from ..config import settings

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
        params: resend.Emails.SendParams = {
            "from": DEFAULT_FROM,
            "to": [recipient_email],
            "subject": f"{requester_name} wants to connect on Attuned",
            "html": f"""
                <div style="font-family: Inter, Arial, sans-serif; max-width: 480px; margin: 0 auto;">
                    <h1 style="color: #2D2926;">Partner Request</h1>
                    <p style="color: #5C5653; font-size: 16px;">
                        {requester_name} has invited you to be their partner on Attuned.
                    </p>
                    <a href="{request_url}" 
                       style="display: inline-block; background: #C4A39B; color: #fff; 
                              padding: 16px 32px; border-radius: 8px; text-decoration: none;">
                        View Request
                    </a>
                </div>
            """
        }
        resend.Emails.send(params)
        logger.info(f"Partner request email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email error (send_partner_request): {e}")
        return False


def send_partner_accepted(recipient_email: str, partner_name: str) -> bool:
    """Notify user their partner request was accepted."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set. Skipping email sending.")
        return False

    try:
        params: resend.Emails.SendParams = {
            "from": DEFAULT_FROM,
            "to": [recipient_email],
            "subject": f"{partner_name} accepted your partner request!",
            "html": f"""
                <div style="font-family: Inter, Arial, sans-serif; max-width: 480px; margin: 0 auto;">
                    <h1 style="color: #2D2926;">You're Connected! 💕</h1>
                    <p style="color: #5C5653; font-size: 16px;">
                        {partner_name} has accepted your partner request. 
                        Open Attuned to start exploring together.
                    </p>
                </div>
            """
        }
        resend.Emails.send(params)
        logger.info(f"Partner acceptance email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Email error (send_partner_accepted): {e}")
        return False
