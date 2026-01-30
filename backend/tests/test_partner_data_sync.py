"""
Tests for partner data synchronization when users update their profile.
Specifically tests Bug #3: stale email/name in remembered_partners.

When a user changes their email or display_name, the remembered_partners
table entries referencing them should be updated automatically. Currently
partners see outdated email/name in their partner list.
"""
import pytest
import uuid
import jwt
from unittest.mock import patch
from datetime import datetime, timedelta
from backend.src.models.user import User
from backend.src.models.partner import PartnerConnection, RememberedPartner


def get_auth_header(user_id):
    """Generate JWT auth header for test user."""
    token = jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        "test-secret-key",
        algorithm="HS256"
    )
    return {'Authorization': f'Bearer {token}'}


def create_user(db_session, email, display_name=None):
    """Helper to create a user and commit."""
    user = User(
        id=uuid.uuid4(),
        email=email,
        display_name=display_name or f"User {email.split('@')[0]}",
        auth_provider='email'
    )
    db_session.add(user)
    db_session.commit()
    return user


def create_partner_connection(client, db_session, user_a, user_b):
    """
    Create and accept a partner connection between two users.
    Returns the connection ID.
    """
    # A requests B - mock email to avoid side effects
    with patch('backend.src.routes.partners.send_partner_request'):
        resp = client.post('/api/partners/connect', json={
            'recipient_email': user_b.email
        }, headers=get_auth_header(user_a.id))
        assert resp.status_code == 201, f"Connect failed: {resp.get_json()}"
        conn_id = resp.get_json()['connection']['id']

    # B accepts A - mock email and notifications
    with patch('backend.src.routes.partners.send_partner_accepted'), \
         patch('backend.src.routes.partners.NotificationService'):
        resp = client.post(f'/api/partners/connections/{conn_id}/accept',
                           json={}, headers=get_auth_header(user_b.id))
        assert resp.status_code == 200, f"Accept failed: {resp.get_json()}"

    return conn_id


class TestPartnerDataSync:
    """Bug #3: remembered_partners entries should update when user changes profile."""

    def test_partner_name_updates_when_user_changes_display_name(self, client, db_session, app):
        """
        When User B changes their display_name, User A's remembered_partners
        entry for User B should reflect the new name.

        Steps:
        1. Create User A and User B with initial names
        2. Connect A and B (creates RememberedPartner entries)
        3. User B changes their display_name
        4. User A's remembered partner entry should show updated name
        """
        # 1. Create users with initial names
        user_a = create_user(db_session, "alice@test.com", "Alice Original")
        user_b = create_user(db_session, "bob@test.com", "Bob Original")

        # 2. Connect them
        create_partner_connection(client, db_session, user_a, user_b)

        # Verify initial remembered partner entry for A
        rp_for_a = RememberedPartner.query.filter_by(
            user_id=user_a.id,
            partner_user_id=user_b.id
        ).first()
        assert rp_for_a is not None, "RememberedPartner entry should exist"
        assert rp_for_a.partner_name == "Bob Original" or rp_for_a.partner_name == user_b.email

        # 3. User B changes their display_name
        user_b.display_name = "Bob Updated"
        db_session.commit()

        # 4. Refresh and check that remembered partner was updated
        db_session.refresh(rp_for_a)

        # BUG #3: This assertion should pass but currently fails because
        # the remembered_partners table is not synced when user updates their name
        assert rp_for_a.partner_name == "Bob Updated", \
            f"Expected partner_name to be 'Bob Updated' but got '{rp_for_a.partner_name}'"

    def test_partner_email_updates_when_user_changes_email(self, client, db_session, app):
        """
        When User B changes their email, User A's remembered_partners
        entry for User B should reflect the new email.

        Steps:
        1. Create User A and User B with initial emails
        2. Connect A and B (creates RememberedPartner entries)
        3. User B changes their email
        4. User A's remembered partner entry should show updated email
        """
        # 1. Create users with initial emails
        user_a = create_user(db_session, "carol@test.com", "Carol")
        user_b = create_user(db_session, "dave_old@test.com", "Dave")

        # 2. Connect them
        create_partner_connection(client, db_session, user_a, user_b)

        # Verify initial remembered partner entry for A
        rp_for_a = RememberedPartner.query.filter_by(
            user_id=user_a.id,
            partner_user_id=user_b.id
        ).first()
        assert rp_for_a is not None, "RememberedPartner entry should exist"
        assert rp_for_a.partner_email == "dave_old@test.com"

        # 3. User B changes their email
        user_b.email = "dave_new@test.com"
        db_session.commit()

        # 4. Refresh and check that remembered partner was updated
        db_session.refresh(rp_for_a)

        # BUG #3: This assertion should pass but currently fails because
        # the remembered_partners table is not synced when user updates their email
        assert rp_for_a.partner_email == "dave_new@test.com", \
            f"Expected partner_email to be 'dave_new@test.com' but got '{rp_for_a.partner_email}'"

    def test_both_partners_data_updated_bidirectionally(self, client, db_session, app):
        """
        Changes from either partner should update the other's entry.
        Both A's and B's RememberedPartner entries should stay in sync.

        Steps:
        1. Create User A and User B
        2. Connect A and B (creates bidirectional RememberedPartner entries)
        3. User A changes their display_name
        4. User B changes their email
        5. Both entries should reflect the updates
        """
        # 1. Create users
        user_a = create_user(db_session, "emma@test.com", "Emma Original")
        user_b = create_user(db_session, "frank@test.com", "Frank Original")

        # 2. Connect them
        create_partner_connection(client, db_session, user_a, user_b)

        # Get both remembered partner entries
        rp_for_a = RememberedPartner.query.filter_by(
            user_id=user_a.id,
            partner_user_id=user_b.id
        ).first()
        rp_for_b = RememberedPartner.query.filter_by(
            user_id=user_b.id,
            partner_user_id=user_a.id
        ).first()

        assert rp_for_a is not None, "A's RememberedPartner entry should exist"
        assert rp_for_b is not None, "B's RememberedPartner entry should exist"

        # 3. User A changes their display_name
        user_a.display_name = "Emma Updated"
        db_session.commit()

        # 4. User B changes their email
        user_b.email = "frank_new@test.com"
        db_session.commit()

        # 5. Refresh and verify both entries updated
        db_session.refresh(rp_for_a)
        db_session.refresh(rp_for_b)

        # BUG #3: B's entry for A should have updated name
        assert rp_for_b.partner_name == "Emma Updated", \
            f"B's entry for A: Expected 'Emma Updated' but got '{rp_for_b.partner_name}'"

        # BUG #3: A's entry for B should have updated email
        assert rp_for_a.partner_email == "frank_new@test.com", \
            f"A's entry for B: Expected 'frank_new@test.com' but got '{rp_for_a.partner_email}'"
