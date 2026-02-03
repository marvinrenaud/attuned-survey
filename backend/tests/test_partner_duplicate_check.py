"""
Tests for partner connection duplicate detection logic.
Specifically tests Bug #1: incorrect query matching unrelated connections
when the recipient email doesn't exist in the system.

Bug Description:
When a user (A) who has accepted connections as a recipient tries to invite
a nonexistent email, the query at lines 73-81 in partners.py incorrectly
matches unrelated connections where A is the recipient, leading to false
"You are already connected" errors.

The buggy query:
    (PartnerConnection.recipient_user_id == requester_uuid) &
    (PartnerConnection.recipient_email == requester.email)

This matches connections where the current user (A) was the RECIPIENT,
not connections to the new email being invited.
"""
import pytest
import uuid
import jwt
import os
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from backend.src.models.user import User
from backend.src.models.partner import PartnerConnection
from backend.src.extensions import db


def get_auth_header(user_id):
    """Generate a valid JWT auth header for testing."""
    secret = os.environ.get('SUPABASE_JWT_SECRET', 'test-secret-key')
    token = jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        secret,
        algorithm="HS256"
    )
    return {'Authorization': f'Bearer {token}'}


def create_test_user(db_session, email, display_name=None):
    """Helper to create a test user."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        display_name=display_name or f"User {email.split('@')[0]}",
        auth_provider='email'
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_connection(db_session, requester, recipient_email, recipient_user=None, status='pending'):
    """Helper to create a partner connection."""
    connection = PartnerConnection(
        requester_user_id=requester.id,
        recipient_email=recipient_email,
        recipient_user_id=recipient_user.id if recipient_user else None,
        status=status,
        connection_token=str(uuid.uuid4()),
        expires_at=datetime.now(timezone.utc) + timedelta(days=1)
    )
    db_session.add(connection)
    db_session.commit()
    return connection


class TestDuplicateCheckBug:
    """
    Tests for Bug #1: Inviting a nonexistent email incorrectly matches
    unrelated connections where the user is the recipient.
    """

    @patch('backend.src.routes.partners.send_partner_request')
    def test_invite_to_nonexistent_email_should_not_match_unrelated_connections(
        self, mock_send_email, client, db_session
    ):
        """
        Scenario: User A has an accepted connection FROM User C (A is recipient).
        User A tries to invite a nonexistent email address.

        Expected: Should succeed - no existing connection to that email.
        Bug Behavior: Fails with "You are already connected" because the
        buggy query matches the A<-C connection (where A is recipient).
        """
        # Setup: Create User A (the one making the request) and User C
        user_a = create_test_user(db_session, "user_a@example.com", "User A")
        user_c = create_test_user(db_session, "user_c@example.com", "User C")

        # User C sent a connection request to User A, which was accepted
        # So User A is the RECIPIENT of this connection
        create_connection(
            db_session,
            requester=user_c,  # C is the requester
            recipient_email=user_a.email,  # A's email
            recipient_user=user_a,  # A is the recipient
            status='accepted'
        )

        # User A tries to invite a brand new email that doesn't exist
        nonexistent_email = "newperson@example.com"

        response = client.post(
            '/api/partners/connect',
            json={'recipient_email': nonexistent_email},
            headers=get_auth_header(user_a.id)
        )

        # Should succeed - there's no connection to newperson@example.com
        # Bug causes this to fail with 400 "You are already connected"
        assert response.status_code == 201, (
            f"Expected 201 but got {response.status_code}. "
            f"Response: {response.json}. "
            "Bug: Query incorrectly matches unrelated connections where user is recipient."
        )
        assert response.json.get('success') is True

    @patch('backend.src.routes.partners.send_partner_request')
    def test_invite_to_nonexistent_email_with_multiple_accepted_connections(
        self, mock_send_email, client, db_session
    ):
        """
        Scenario: User A has multiple accepted connections as recipient
        (from User B, User C, and User D). User A tries to invite a
        nonexistent email.

        Expected: Should succeed.
        Bug Behavior: Matches one of the existing connections incorrectly.
        """
        # Create all users
        user_a = create_test_user(db_session, "user_a@example.com", "User A")
        user_b = create_test_user(db_session, "user_b@example.com", "User B")
        user_c = create_test_user(db_session, "user_c@example.com", "User C")
        user_d = create_test_user(db_session, "user_d@example.com", "User D")

        # All these users sent requests TO User A (A is always recipient)
        for requester in [user_b, user_c, user_d]:
            create_connection(
                db_session,
                requester=requester,
                recipient_email=user_a.email,
                recipient_user=user_a,
                status='accepted'
            )

        # User A invites a brand new nonexistent email
        nonexistent_email = "totallynew@example.com"

        response = client.post(
            '/api/partners/connect',
            json={'recipient_email': nonexistent_email},
            headers=get_auth_header(user_a.id)
        )

        # Should succeed - no connection to totallynew@example.com
        assert response.status_code == 201, (
            f"Expected 201 but got {response.status_code}. "
            f"Response: {response.json}. "
            "Bug: Multiple accepted connections as recipient causes false positive."
        )
        assert response.json.get('success') is True

    @patch('backend.src.routes.partners.send_partner_request')
    def test_correct_duplicate_detection_still_works(
        self, mock_send_email, client, db_session
    ):
        """
        Verify that legitimate duplicate detection still works correctly.

        Scenario: User A sent request to User B (accepted).
        User A tries to invite User B again.

        Expected: Should fail with "already connected".
        """
        user_a = create_test_user(db_session, "user_a@example.com", "User A")
        user_b = create_test_user(db_session, "user_b@example.com", "User B")

        # A sent request to B, which was accepted
        create_connection(
            db_session,
            requester=user_a,  # A is requester
            recipient_email=user_b.email,
            recipient_user=user_b,
            status='accepted'
        )

        # User A tries to invite User B again
        response = client.post(
            '/api/partners/connect',
            json={'recipient_email': user_b.email},
            headers=get_auth_header(user_a.id)
        )

        # Should fail - they are already connected
        assert response.status_code == 400
        assert 'already connected' in response.json.get('error', '').lower()

    @patch('backend.src.routes.partners.send_partner_request')
    def test_pending_request_detection_both_directions(
        self, mock_send_email, client, db_session
    ):
        """
        Verify pending request detection works both ways.

        Scenario 1: A sent pending request to B. A tries again -> "already sent"
        Scenario 2: A sent pending request to B. B tries to invite A -> "pending from"
        """
        user_a = create_test_user(db_session, "user_a@example.com", "User A")
        user_b = create_test_user(db_session, "user_b@example.com", "User B")

        # A sent pending request to B
        create_connection(
            db_session,
            requester=user_a,
            recipient_email=user_b.email,
            recipient_user=user_b,
            status='pending'
        )

        # Scenario 1: A tries to send again
        response = client.post(
            '/api/partners/connect',
            json={'recipient_email': user_b.email},
            headers=get_auth_header(user_a.id)
        )

        assert response.status_code == 400
        assert 'already sent' in response.json.get('error', '').lower(), (
            f"Expected 'already sent' error but got: {response.json.get('error')}"
        )

        # Scenario 2: B tries to invite A (reverse direction)
        response = client.post(
            '/api/partners/connect',
            json={'recipient_email': user_a.email},
            headers=get_auth_header(user_b.id)
        )

        assert response.status_code == 400
        error_msg = response.json.get('error', '').lower()
        assert 'pending' in error_msg, (
            f"Expected 'pending request' error but got: {response.json.get('error')}"
        )
