"""Push notification service using Firebase Admin SDK."""
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from firebase_admin import messaging

from ..extensions import db
from ..models.notification_history import Notification
from ..models.notification import PushNotificationToken
from ..firebase_config import is_firebase_initialized


logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending push notifications via FCM."""

    @staticmethod
    def send_push_notification(
        recipient_user_id: str,
        title: str,
        body: str,
        notification_type: str,
        data: Optional[Dict[str, str]] = None,
        sender_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a push notification and record it in the database.
        
        The Firebase Admin SDK handles:
        - OAuth2 token generation and refresh
        - Retry logic with exponential backoff
        - Proper error categorization
        
        Args:
            recipient_user_id: UUID of the recipient
            title: Notification title
            body: Notification body
            notification_type: Type (e.g., 'partner_invitation', 'invitation_accepted')
            data: Optional data payload for deep linking
            sender_user_id: Optional UUID of sender (for partner notifications)
        
        Returns:
            Dict with success status and results
        """
        logger.info(f"📤 Attempting to send {notification_type} notification to user {recipient_user_id}")
        
        if not is_firebase_initialized():
            logger.warning("Firebase not initialized. Skipping push notification.")
            return {"success": False, "reason": "firebase_not_initialized"}

        # Step 1: Get the user's FCM token(s) from database
        # Convert string to UUID for proper database lookup
        try:
            recipient_uuid = uuid.UUID(str(recipient_user_id))
            tokens = PushNotificationToken.query.filter_by(
                user_id=recipient_uuid
            ).all()
            
            if not tokens:
                logger.info(f"No FCM tokens found for user {recipient_user_id}")
                return {"success": False, "reason": "no_tokens"}
            
            logger.info(f"Found {len(tokens)} FCM token(s) for user {recipient_user_id}")
        except ValueError as e:
            logger.error(f"Invalid UUID format for recipient: {recipient_user_id} - {e}")
            return {"success": False, "reason": "invalid_user_id", "error": str(e)}
        except Exception as e:
            logger.error(f"Error fetching FCM tokens: {e}")
            return {"success": False, "reason": "database_error", "error": str(e)}

        # Step 2: Record the notification in database (for history)
        notification_record = None
        try:
            notification_record = Notification(
                recipient_user_id=recipient_user_id,
                sender_user_id=sender_user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                data=data or {},
                created_at=datetime.utcnow()
            )
            db.session.add(notification_record)
            db.session.commit()
            notification_id = notification_record.id
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating notification record: {e}")
            return {"success": False, "reason": "database_error", "error": str(e)}

        # Step 3: Send to each device via FCM
        # Ensure data values are strings (FCM requirement)
        string_data = {k: str(v) for k, v in (data or {}).items()}
        
        results = []
        for token_record in tokens:
            device_token = token_record.device_token
            platform = token_record.platform

            # Build the message
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=string_data,
                token=device_token,
            )

            # Add platform-specific config
            if platform == "ios":
                message.apns = messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1
                        )
                    )
                )
            elif platform == "android":
                message.android = messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        sound="default"
                    )
                )

            try:
                # Firebase Admin SDK handles retries automatically
                response = messaging.send(message)
                results.append({
                    "token": device_token[:20] + "...",  # Truncate for logging
                    "success": True,
                    "message_id": response
                })
                logger.info(f"✅ Notification sent to {platform} device: {response}")

            except messaging.UnregisteredError:
                # Token is invalid, remove it from database
                NotificationService._remove_invalid_token(device_token)
                results.append({
                    "token": device_token[:20] + "...",
                    "success": False,
                    "reason": "unregistered"
                })

            except Exception as e:
                logger.error(f"Error sending to device: {e}")
                results.append({
                    "token": device_token[:20] + "...",
                    "success": False,
                    "reason": str(e)
                })

        # Step 4: Update notification record with send status
        successful_sends = [r for r in results if r.get("success")]
        if successful_sends and notification_record:
            try:
                notification_record.sent_at = datetime.utcnow()
                db.session.commit()
            except Exception as e:
                logger.error(f"Error updating notification record: {e}")

        return {
            "success": len(successful_sends) > 0,
            "notification_id": notification_id,
            "results": results
        }

    @staticmethod
    def _remove_invalid_token(device_token: str):
        """Remove an invalid/unregistered FCM token from the database."""
        try:
            PushNotificationToken.query.filter_by(
                device_token=device_token
            ).delete()
            db.session.commit()
            logger.info(f"🗑️ Removed invalid token: {device_token[:20]}...")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing invalid token: {e}")

    @staticmethod
    def send_partner_invitation(
        recipient_user_id: str,
        sender_user_id: str,
        sender_name: str,
        invitation_id: int
    ) -> Dict[str, Any]:
        """
        Send push notification for partner invitation.
        
        Args:
            recipient_user_id: UUID of the invitation recipient
            sender_user_id: UUID of the invitation sender
            sender_name: Display name of the sender
            invitation_id: ID of the partner connection record
        """
        return NotificationService.send_push_notification(
            recipient_user_id=recipient_user_id,
            title=f"{sender_name} has invited you to explore with them on Attuned 💞",
            body="Tap to view the invitation",
            notification_type="partner_invitation",
            data={
                "type": "partner_invitation",
                "invitation_id": str(invitation_id),
                "initial_page": "/ConnectionRequestsPage"
            },
            sender_user_id=sender_user_id
        )

    @staticmethod
    def send_invitation_accepted(
        requester_user_id: str,
        acceptor_user_id: str,
        acceptor_name: str
    ) -> Dict[str, Any]:
        """
        Send push notification when partner invitation is accepted.
        
        Args:
            requester_user_id: UUID of the original invitation sender
            acceptor_user_id: UUID of the person who accepted
            acceptor_name: Display name of the acceptor
        """
        return NotificationService.send_push_notification(
            recipient_user_id=requester_user_id,
            title=f"{acceptor_name} has accepted your invitation…enjoy each other!",
            body="Tap to see your partner",
            notification_type="invitation_accepted",
            data={
                "type": "invitation_accepted",
                "partner_id": str(acceptor_user_id),
                "initial_page": "/PartnersPage"
            },
            sender_user_id=acceptor_user_id
        )
