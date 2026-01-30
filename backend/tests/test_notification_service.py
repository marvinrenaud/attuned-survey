"""Tests for NotificationService."""
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from datetime import datetime

from src.extensions import db
from src.models.user import User
from src.models.notification_history import Notification
from src.models.notification import PushNotificationToken
from src.services.notification_service import NotificationService
import uuid


@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user_id = uuid.uuid4()
        user = User(id=user_id, email="test@example.com", display_name="Test User")
        db.session.add(user)
        db.session.commit()
        return str(user_id)


@pytest.fixture
def test_user_with_token(app, test_user):
    """Create a test user with FCM token."""
    with app.app_context():
        token = PushNotificationToken(
            user_id=test_user,
            device_token="test_fcm_token_12345",
            platform="ios"
        )
        db.session.add(token)
        db.session.commit()
        return test_user


@pytest.fixture
def sender_user(app):
    """Create a sender user."""
    with app.app_context():
        user_id = uuid.uuid4()
        user = User(id=user_id, email="sender@example.com", display_name="Sender User")
        db.session.add(user)
        db.session.commit()
        return str(user_id)


class TestNotificationService:
    """Test cases for NotificationService."""

    def test_send_notification_no_firebase(self, app, test_user_with_token):
        """Test that notification record is created but push skipped when Firebase not initialized."""
        with app.app_context():
            with patch('src.services.notification_service.is_firebase_initialized', return_value=False):
                result = NotificationService.send_push_notification(
                    recipient_user_id=test_user_with_token,
                    title="Test Title",
                    body="Test Body",
                    notification_type="test"
                )

                assert result['success'] is False
                assert result['reason'] == 'firebase_not_initialized'
                # Notification record should still be created for in-app display
                assert 'notification_id' in result

                notification = Notification.query.get(result['notification_id'])
                assert notification is not None
                assert notification.title == "Test Title"
                assert notification.sent_at is None  # Push not sent

    def test_send_notification_no_tokens(self, app, test_user):
        """Test that notification record is created but push skipped when no FCM tokens."""
        with app.app_context():
            with patch('src.services.notification_service.is_firebase_initialized', return_value=True):
                result = NotificationService.send_push_notification(
                    recipient_user_id=test_user,
                    title="Test Title",
                    body="Test Body",
                    notification_type="test"
                )

                assert result['success'] is False
                assert result['reason'] == 'no_tokens'
                # Notification record should still be created for in-app display
                assert 'notification_id' in result

                notification = Notification.query.get(result['notification_id'])
                assert notification is not None
                assert notification.title == "Test Title"
                assert notification.sent_at is None  # Push not sent

    def test_send_notification_creates_record(self, app, test_user_with_token, sender_user):
        """Test that notification creates a record in the database."""
        with app.app_context():
            with patch('src.services.notification_service.is_firebase_initialized', return_value=True), \
                 patch('src.services.notification_service.messaging.send') as mock_send:
                
                mock_send.return_value = "message_id_12345"
                
                result = NotificationService.send_push_notification(
                    recipient_user_id=test_user_with_token,
                    title="Test Title",
                    body="Test Body",
                    notification_type="partner_invitation",
                    data={"key": "value"},
                    sender_user_id=sender_user
                )
                
                assert result['success'] is True
                assert 'notification_id' in result
                
                # Verify record was created
                notification = Notification.query.get(result['notification_id'])
                assert notification is not None
                assert notification.title == "Test Title"
                assert notification.body == "Test Body"
                assert notification.notification_type == "partner_invitation"
                assert notification.sent_at is not None

    def test_send_partner_invitation(self, app, test_user_with_token, sender_user):
        """Test convenience method for partner invitation."""
        with app.app_context():
            with patch('src.services.notification_service.is_firebase_initialized', return_value=True), \
                 patch('src.services.notification_service.messaging.send') as mock_send:
                
                mock_send.return_value = "message_id_12345"
                
                result = NotificationService.send_partner_invitation(
                    recipient_user_id=test_user_with_token,
                    sender_user_id=sender_user,
                    sender_name="Alice",
                    invitation_id=123
                )
                
                assert result['success'] is True
                
                # Verify notification content
                notification = Notification.query.get(result['notification_id'])
                assert "Alice" in notification.title
                assert notification.notification_type == "partner_invitation"
                assert notification.data['initialPageName'] == "ConnectionRequestsPage"
                assert notification.data['type'] == "partner_invitation"
                assert notification.data['invitation_id'] == "123"

    def test_send_invitation_accepted(self, app, test_user_with_token, sender_user):
        """Test convenience method for invitation accepted."""
        with app.app_context():
            with patch('src.services.notification_service.is_firebase_initialized', return_value=True), \
                 patch('src.services.notification_service.messaging.send') as mock_send:
                
                mock_send.return_value = "message_id_12345"
                
                result = NotificationService.send_invitation_accepted(
                    requester_user_id=test_user_with_token,
                    acceptor_user_id=sender_user,
                    acceptor_name="Bob"
                )
                
                assert result['success'] is True
                
                # Verify notification content
                notification = Notification.query.get(result['notification_id'])
                assert "Bob" in notification.title
                assert notification.notification_type == "invitation_accepted"
                assert notification.data['initialPageName'] == "TapToPlay"
                assert notification.data['type'] == "invitation_accepted"

    def test_invalid_token_removed(self, app, test_user_with_token):
        """Test that invalid FCM tokens are removed from database."""
        with app.app_context():
            # Verify token exists
            tokens = PushNotificationToken.query.filter_by(user_id=test_user_with_token).all()
            assert len(tokens) == 1
            
            with patch('src.services.notification_service.is_firebase_initialized', return_value=True), \
                 patch('src.services.notification_service.messaging.send') as mock_send:
                
                # Simulate unregistered token error
                from firebase_admin import messaging
                mock_send.side_effect = messaging.UnregisteredError("Token unregistered")
                
                result = NotificationService.send_push_notification(
                    recipient_user_id=test_user_with_token,
                    title="Test",
                    body="Test",
                    notification_type="test"
                )
                
                # Notification record still created but not sent
                assert 'notification_id' in result
                assert result['results'][0]['success'] is False
                assert result['results'][0]['reason'] == 'unregistered'
                
                # Token should be removed
                tokens = PushNotificationToken.query.filter_by(user_id=test_user_with_token).all()
                assert len(tokens) == 0
