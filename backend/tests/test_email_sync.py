"""
Tests for email sync between auth.users and public.users (Migration 028).

This module tests:
1. Migration file structure and syntax
2. The sync function logic (when database is available)
3. Integration tests for the full sync flow

Note: Full trigger testing requires a Supabase instance with auth schema.
The trigger fires on auth.users updates, which can only be tested in
a real Supabase environment or via manual testing.
"""
import pytest
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestMigration028Structure:
    """Test migration 028 file structure and syntax."""

    @pytest.fixture
    def migration_path(self):
        return Path(__file__).parent.parent / 'migrations' / '028_sync_auth_email_to_users.sql'

    @pytest.fixture
    def rollback_path(self):
        return Path(__file__).parent.parent / 'migrations' / 'rollback_028.sql'

    def test_migration_file_exists(self, migration_path):
        """Test that migration 028 file exists."""
        assert migration_path.exists(), "Migration 028 file not found"

    def test_rollback_file_exists(self, rollback_path):
        """Test that rollback 028 file exists."""
        assert rollback_path.exists(), "Rollback 028 file not found"

    def test_migration_creates_function(self, migration_path):
        """Test that migration creates the sync function."""
        content = migration_path.read_text()

        assert 'CREATE OR REPLACE FUNCTION' in content
        assert 'handle_auth_user_email_update' in content
        assert 'RETURNS TRIGGER' in content

    def test_migration_uses_security_definer(self, migration_path):
        """Test that function uses SECURITY DEFINER (required for cross-schema access)."""
        content = migration_path.read_text()

        assert 'SECURITY DEFINER' in content, \
            "Function must use SECURITY DEFINER to update public.users from auth context"

    def test_migration_sets_search_path(self, migration_path):
        """Test that function sets search_path = '' (security best practice)."""
        content = migration_path.read_text()

        assert "SET search_path = ''" in content or "set search_path = ''" in content.lower(), \
            "Function must set search_path = '' to prevent search_path attacks"

    def test_migration_creates_trigger(self, migration_path):
        """Test that migration creates the trigger on auth.users."""
        content = migration_path.read_text()

        assert 'CREATE TRIGGER' in content
        assert 'on_auth_user_email_updated' in content
        assert 'auth.users' in content
        assert 'AFTER UPDATE' in content

    def test_migration_triggers_on_email_column(self, migration_path):
        """Test that trigger specifically fires on email column updates."""
        content = migration_path.read_text()

        # Should use "AFTER UPDATE OF email" for efficiency
        assert 'UPDATE OF email' in content or 'update of email' in content.lower(), \
            "Trigger should fire only on email column updates for efficiency"

    def test_migration_updates_public_users(self, migration_path):
        """Test that function updates public.users table."""
        content = migration_path.read_text()

        assert 'UPDATE public.users' in content
        assert 'SET email = NEW.email' in content
        assert 'WHERE id = NEW.id' in content

    def test_migration_handles_unchanged_email(self, migration_path):
        """Test that function only updates when email actually changes."""
        content = migration_path.read_text()

        # Should check for actual change using IS DISTINCT FROM (NULL-safe)
        assert 'IS DISTINCT FROM' in content or 'is distinct from' in content.lower(), \
            "Function should use IS DISTINCT FROM for NULL-safe comparison"

    def test_rollback_drops_trigger(self, rollback_path):
        """Test that rollback drops the trigger."""
        content = rollback_path.read_text()

        assert 'DROP TRIGGER' in content
        assert 'on_auth_user_email_updated' in content

    def test_rollback_drops_function(self, rollback_path):
        """Test that rollback drops the function."""
        content = rollback_path.read_text()

        assert 'DROP FUNCTION' in content
        assert 'handle_auth_user_email_update' in content

    def test_migration_has_documentation(self, migration_path):
        """Test that migration has proper documentation."""
        content = migration_path.read_text()

        # Should have header comment explaining the problem and solution
        assert 'Problem:' in content or 'problem:' in content.lower()
        assert 'Solution:' in content or 'solution:' in content.lower()


class TestEmailSyncFunction:
    """
    Test the email sync function logic.

    These tests verify the sync behavior using the backend database connection.
    They test the public.users update logic, not the auth.users trigger
    (which requires a real Supabase auth environment).
    """

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.fixture
    def db_session(self, app):
        """Get database session."""
        from src.extensions import db
        with app.app_context():
            yield db.session
            db.session.rollback()

    @pytest.mark.skipif(
        not os.environ.get('DATABASE_URL'),
        reason="Requires DATABASE_URL for database tests"
    )
    def test_users_email_can_be_updated(self, app, db_session):
        """Test that public.users.email can be updated (simulating trigger behavior)."""
        from src.models.user import User
        from sqlalchemy import text
        import uuid

        with app.app_context():
            # Create a test user
            test_user_id = uuid.uuid4()
            test_user = User(
                id=test_user_id,
                email=f'test_original_{test_user_id}@example.com',
                auth_provider='email'
            )
            db_session.add(test_user)
            db_session.commit()

            try:
                # Simulate what the trigger does: update email
                new_email = f'test_updated_{test_user_id}@example.com'
                test_user.email = new_email
                db_session.commit()

                # Verify the update worked
                db_session.refresh(test_user)
                assert test_user.email == new_email

            finally:
                # Clean up
                db_session.delete(test_user)
                db_session.commit()

    @pytest.mark.skipif(
        not os.environ.get('DATABASE_URL') or 'sqlite' in os.environ.get('DATABASE_URL', ''),
        reason="Requires PostgreSQL DATABASE_URL for raw SQL tests"
    )
    def test_email_update_with_raw_sql(self, app, db_session):
        """Test email update using raw SQL (closer to trigger behavior)."""
        from src.models.user import User
        from sqlalchemy import text
        import uuid

        with app.app_context():
            # Create a test user
            test_user_id = uuid.uuid4()
            original_email = f'test_sql_original_{test_user_id}@example.com'
            new_email = f'test_sql_updated_{test_user_id}@example.com'

            test_user = User(
                id=test_user_id,
                email=original_email,
                auth_provider='email'
            )
            db_session.add(test_user)
            db_session.commit()

            try:
                # Simulate trigger using raw SQL (how the trigger function works)
                # Using public.users schema qualification (PostgreSQL-specific)
                db_session.execute(
                    text("UPDATE public.users SET email = :new_email WHERE id = :user_id"),
                    {"new_email": new_email, "user_id": str(test_user_id)}
                )
                db_session.commit()

                # Verify the update
                result = db_session.execute(
                    text("SELECT email FROM public.users WHERE id = :user_id"),
                    {"user_id": str(test_user_id)}
                ).fetchone()

                assert result[0] == new_email

            finally:
                # Clean up
                db_session.execute(
                    text("DELETE FROM public.users WHERE id = :user_id"),
                    {"user_id": str(test_user_id)}
                )
                db_session.commit()


class TestEmailSyncIntegration:
    """
    Integration tests for email sync.

    These tests require a real Supabase instance to test the full trigger flow.
    Run manually against staging/development environments.
    """

    @pytest.fixture
    def app(self):
        """Create Flask app for testing."""
        from src.main import create_app
        app = create_app()
        app.config['TESTING'] = True
        return app

    @pytest.mark.skipif(
        not os.environ.get('RUN_INTEGRATION_TESTS'),
        reason="Set RUN_INTEGRATION_TESTS=1 to run integration tests"
    )
    def test_trigger_function_exists(self, app):
        """Test that the sync function exists in the database."""
        from src.extensions import db
        from sqlalchemy import text

        with app.app_context():
            result = db.session.execute(text("""
                SELECT proname, prosecdef, proconfig
                FROM pg_proc
                WHERE proname = 'handle_auth_user_email_update'
            """)).fetchone()

            assert result is not None, "Function handle_auth_user_email_update not found"
            assert result[1] is True, "Function should be SECURITY DEFINER"

            # Check search_path is set
            proconfig = result[2] or []
            has_search_path = any('search_path' in str(c) for c in proconfig)
            assert has_search_path, "Function should have search_path set"

    @pytest.mark.skipif(
        not os.environ.get('RUN_INTEGRATION_TESTS'),
        reason="Set RUN_INTEGRATION_TESTS=1 to run integration tests"
    )
    def test_trigger_exists(self, app):
        """Test that the trigger exists on auth.users."""
        from src.extensions import db
        from sqlalchemy import text

        with app.app_context():
            result = db.session.execute(text("""
                SELECT tgname, tgenabled
                FROM pg_trigger
                WHERE tgname = 'on_auth_user_email_updated'
            """)).fetchone()

            assert result is not None, "Trigger on_auth_user_email_updated not found"
            # tgenabled: 'O' = enabled in origin and local modes (default)
            assert result[1] in ('O', 'A'), "Trigger should be enabled"


# Manual verification script
def verify_email_sync_manually():
    """
    Manual verification script for email sync.

    Run this after applying migration 028 to verify the trigger works:

    1. python -c "from tests.test_email_sync import verify_email_sync_manually; verify_email_sync_manually()"
    2. Or: pytest tests/test_email_sync.py -v -k "integration" --run-integration

    Steps:
    1. Check current email in public.users for a test user
    2. Change email via Supabase Auth dashboard
    3. Check that public.users.email was automatically updated
    """
    print("""
    Manual Verification Steps for Email Sync (Migration 028):
    =========================================================

    1. Find a test user:
       SELECT id, email FROM public.users WHERE email LIKE '%test%' LIMIT 1;

    2. Note their current email in public.users

    3. Change their email via Supabase Auth dashboard:
       - Go to Authentication > Users
       - Find the user and edit their email
       - Save the change

    4. Verify sync worked:
       SELECT email FROM public.users WHERE id = '<user_id>';

       The email should now match the new value from Supabase Auth.

    5. Check trigger fired (in Supabase logs):
       Look for: "Synced email change for user <id>: old@email -> new@email"

    Alternative: Use the test user from the bug investigation:
    - User ID: 66792973-aa07-4299-a8dc-66d8604b8c43
    - Change email back and verify sync
    """)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
