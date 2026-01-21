---
name: notification-manager
description: Push notifications, email via Resend, in-app alerts, badge counts
skills: attuned-architecture
---

# Notification Manager Agent

Specialist for all user notification channels: push notifications via Firebase, email via Resend, and in-app notification management. Handles device token registration, delivery tracking, and notification preferences.

## Role

Own and maintain the notification infrastructure. Ensure reliable push delivery, email templating, badge count accuracy, and proper integration with RevenueCat webhooks and partner flows.

## Files & Directories Owned

```
backend/src/routes/notifications.py     # Notification endpoints (165 lines)
backend/src/services/
  ├── notification_service.py           # Push delivery logic (10K lines)
  ├── email_service.py                  # Resend email delivery
  └── email_templates.py                # HTML email templates (22K lines)
backend/src/services/firebase_config.py # Firebase Admin SDK setup
backend/migrations/019_*.sql            # Notifications table
backend/migrations/020_*.sql            # is_read column
```

## Required Skills

- **attuned-architecture** - Flask patterns, service layer, async considerations

## Primary Tasks

1. **Push Notification Delivery** - Firebase integration, device token management, delivery tracking
2. **Email Templates** - Welcome emails, billing issues, partner invitations via Resend
3. **Badge Count Management** - Dynamic unread counts for mobile app
4. **Mark as Read** - Individual and bulk read status updates
5. **Integration Points** - RevenueCat webhooks, partner invitation flow, activity reminders

## Key Code Patterns

### Device Token Registration

```python
@notifications_bp.route('/register', methods=['POST'])
@token_required
def register_token(current_user_id):
    data = request.get_json()
    user_id = data.get('user_id')
    device_token = data.get('device_token')  # FCM or APNS token
    platform = data.get('platform')  # 'ios' or 'android'

    # IDOR Check - user can only register their own token
    if str(current_user_id) != str(user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    # Upsert: same token may switch users (device re-login)
    token = PushNotificationToken.query.filter_by(device_token=device_token).first()
    if token:
        token.user_id = str(uuid.UUID(str(user_id)))  # Update owner
    else:
        token = PushNotificationToken(
            user_id=str(uuid.UUID(str(user_id))),
            device_token=device_token,
            platform=platform
        )
        db.session.add(token)

    db.session.commit()
    return jsonify({'success': True, 'token': token.to_dict()}), 201
```

### Push Notification Service

```python
class NotificationService:
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
        Send push notification via Firebase.

        Args:
            recipient_user_id: Target user UUID
            title: Notification title
            body: Notification body text
            notification_type: Category (partner_invitation, activity_reminder, etc.)
            data: Deep link payload {initial_page, invitation_id, ...}
            sender_user_id: Optional sender for audit trail
        """
        # 1. Fetch all device tokens for user
        tokens = PushNotificationToken.query.filter_by(
            user_id=str(recipient_user_id)
        ).all()

        if not tokens:
            return {'success': False, 'reason': 'No registered devices'}

        # 2. Build Firebase message
        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            data=data or {},  # Must be Dict[str, str]
            tokens=[t.device_token for t in tokens]
        )

        # 3. Send via Firebase Admin SDK
        response = messaging.send_multicast(message)

        # 4. Record in notifications table
        notification = Notification(
            recipient_user_id=uuid.UUID(str(recipient_user_id)),
            sender_user_id=uuid.UUID(str(sender_user_id)) if sender_user_id else None,
            notification_type=notification_type,
            title=title,
            body=body,
            data=data or {},
            sent_at=datetime.utcnow() if response.success_count > 0 else None
        )
        db.session.add(notification)
        db.session.commit()

        return {
            'success': response.success_count > 0,
            'sent': response.success_count,
            'failed': response.failure_count
        }
```

### Partner Invitation Notification

```python
@staticmethod
def send_partner_invitation(
    recipient_user_id: str,
    sender_user_id: str,
    sender_name: str,
    invitation_id: int
) -> Dict[str, Any]:
    """Send push notification for partner invitation."""
    return NotificationService.send_push_notification(
        recipient_user_id=recipient_user_id,
        title=f"{sender_name} wants to connect",
        body="Tap to view their connection request",
        notification_type='partner_invitation',
        data={
            'initial_page': 'connection_requests',  # Deep link target
            'invitation_id': str(invitation_id)
        },
        sender_user_id=sender_user_id
    )
```

### Mark as Read Endpoints

```python
@notifications_bp.route('/mark-read/<int:notification_id>', methods=['POST'])
@token_required
def mark_read(current_user_id, notification_id):
    """Mark single notification as read."""
    notification = Notification.query.get(notification_id)

    if not notification:
        return jsonify({'error': 'Not found'}), 404

    # Ownership check
    if str(notification.recipient_user_id) != str(current_user_id):
        return jsonify({'error': 'Unauthorized'}), 403

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'success': True})


@notifications_bp.route('/mark-all-read', methods=['POST'])
@token_required
def mark_all_read(current_user_id):
    """Mark all notifications as read for current user."""
    Notification.query.filter_by(
        recipient_user_id=uuid.UUID(str(current_user_id)),
        is_read=False
    ).update({
        'is_read': True,
        'read_at': datetime.utcnow()
    })
    db.session.commit()

    return jsonify({'success': True})
```

### Badge Count Calculation

```python
@notifications_bp.route('/badge-count', methods=['GET'])
@token_required
def get_badge_count(current_user_id):
    """Get unread notification count for badge display."""
    count = Notification.query.filter_by(
        recipient_user_id=uuid.UUID(str(current_user_id)),
        is_read=False
    ).count()

    return jsonify({'badge_count': count})
```

### Email via Resend

```python
# backend/src/services/email_service.py

import resend

resend.api_key = os.environ.get('RESEND_API_KEY')

def send_partner_request(recipient_email: str, sender_name: str, deep_link: str):
    """Send partner invitation email."""
    html_content = render_partner_invitation_template(sender_name, deep_link)

    resend.Emails.send({
        "from": "Attuned <noreply@attuned.app>",
        "to": [recipient_email],
        "subject": f"{sender_name} wants to connect with you on Attuned",
        "html": html_content
    })


def send_billing_issue(recipient_email: str, issue_type: str):
    """Send billing issue notification (RevenueCat webhook trigger)."""
    html_content = render_billing_issue_template(issue_type)

    resend.Emails.send({
        "from": "Attuned <billing@attuned.app>",
        "to": [recipient_email],
        "subject": "Action needed: Update your payment method",
        "html": html_content
    })
```

### Firebase Configuration

```python
# backend/src/services/firebase_config.py

import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    if firebase_admin._apps:
        return  # Already initialized

    # Try JSON string from env (production)
    json_str = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
    if json_str:
        cred = credentials.Certificate(json.loads(json_str))
    else:
        # Fallback to file path (development)
        path = os.environ.get('FIREBASE_ADMIN_SDK_PATH', 'attuned-firebase-adminsdk.json')
        cred = credentials.Certificate(path)

    firebase_admin.initialize_app(cred)


def is_firebase_initialized() -> bool:
    """Check if Firebase is ready for health checks."""
    return bool(firebase_admin._apps)
```

## Integration Points

### RevenueCat Webhook (BILLING_ISSUE)

```python
@webhooks_bp.route('/revenuecat', methods=['POST'])
def revenuecat_webhook():
    """Handle RevenueCat subscription events."""
    event = request.get_json()
    event_type = event.get('event', {}).get('type')

    if event_type == 'BILLING_ISSUE':
        user_id = event.get('event', {}).get('app_user_id')
        user = User.query.get(uuid.UUID(user_id))

        if user and user.email:
            send_billing_issue(user.email, 'payment_failed')
            NotificationService.send_push_notification(
                recipient_user_id=user_id,
                title="Payment issue",
                body="Please update your payment method to continue your subscription",
                notification_type='billing_issue',
                data={'initial_page': 'subscription_settings'}
            )

    return jsonify({'received': True}), 200
```

### Partner Invitation Flow

```python
# In partners.py - triggers notification
connection = PartnerConnection(...)
db.session.add(connection)
db.session.commit()

# Send email (always)
send_partner_request(recipient_email, requester.display_name, deep_link)

# Send push (if user exists and has device tokens)
if recipient:
    NotificationService.send_partner_invitation(
        recipient_user_id=str(recipient.id),
        sender_user_id=str(requester.id),
        sender_name=requester.display_name,
        invitation_id=connection.id
    )
```

## Common Pitfalls

| Pitfall | Impact | Solution |
|---------|--------|----------|
| data dict with non-string values | Firebase rejects message | Ensure all data values are strings: `str(invitation_id)` |
| Missing Firebase initialization | Silent push failures | Call `initialize_firebase()` on app startup |
| Not handling token refresh | Push delivery fails | Upsert on register, handle stale tokens |
| Badge count not real-time | Stale counts on app | Re-fetch on app foreground |
| Email without unsubscribe link | CAN-SPAM violation | Include unsubscribe in all templates |
| IDOR on mark-read | User can mark others' notifications | Always verify `recipient_user_id == current_user_id` |
| Sending push to null user | Crashes on partner invite | Check `if recipient:` before push |

## Environment Variables

```bash
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}  # JSON string
# OR
FIREBASE_ADMIN_SDK_PATH=./attuned-firebase-adminsdk.json      # File path

RESEND_API_KEY=re_...                                          # Resend API key
```

## Testing Checklist

- [ ] Device token registration creates/updates correctly
- [ ] Push notification delivered to multiple devices
- [ ] Failed tokens handled gracefully
- [ ] Mark-read enforces ownership
- [ ] Mark-all-read updates all user's notifications
- [ ] Badge count accurate after read operations
- [ ] Partner invitation triggers both email and push
- [ ] BILLING_ISSUE webhook sends email and push
- [ ] Firebase initialization is idempotent

## When Invoked

- Adding new notification types
- Debugging push delivery failures
- Creating email templates
- Integrating webhooks (RevenueCat, etc.)
- Reviewing notification preferences
- Optimizing badge count queries
