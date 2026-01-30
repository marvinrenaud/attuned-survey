#!/usr/bin/env python3
"""
Diagnostic script for email sync issue (Migration 028).
Investigates the state of triggers, notifications, and user data.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from sqlalchemy import text


def run_query(name: str, sql: str, params: dict = None):
    """Run a query and print results."""
    print(f"\n{'='*70}")
    print(f"📊 {name}")
    print('='*70)

    try:
        if params:
            result = db.session.execute(text(sql), params)
        else:
            result = db.session.execute(text(sql))

        rows = result.fetchall()
        columns = result.keys() if hasattr(result, 'keys') else None

        if not rows:
            print("   (no results)")
            return []

        # Print column headers
        if columns:
            print(f"   {' | '.join(str(c) for c in columns)}")
            print(f"   {'-'*60}")

        # Print rows
        for row in rows:
            print(f"   {' | '.join(str(v)[:50] for v in row)}")

        return rows
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []


def main():
    test_user_id = '66792973-aa07-4299-a8dc-66d8604b8c43'
    new_email = 'logger_faced.0p+test55_changed@icloud.com'

    print("\n" + "="*70)
    print("🔍 EMAIL SYNC DIAGNOSTIC REPORT")
    print("="*70)
    print(f"Test User ID: {test_user_id}")
    print(f"Expected New Email: {new_email}")

    with app.app_context():
        # 1. Check if function exists
        run_query(
            "1. Check sync function exists",
            """
            SELECT proname, prosecdef as security_definer, proconfig
            FROM pg_proc
            WHERE proname = 'handle_auth_user_email_update'
            """
        )

        # 2. Check if trigger exists
        run_query(
            "2. Check trigger exists on auth.users",
            """
            SELECT tgname, tgenabled, tgrelid::regclass as table_name
            FROM pg_trigger
            WHERE tgname = 'on_auth_user_email_updated'
            """
        )

        # 3. Check current email in public.users
        run_query(
            "3. Current email in public.users",
            """
            SELECT id, email, updated_at
            FROM public.users
            WHERE id = :user_id
            """,
            {"user_id": test_user_id}
        )

        # 4. Check email in auth.users (if accessible)
        print(f"\n{'='*70}")
        print("📊 4. Email in auth.users (may fail due to permissions)")
        print('='*70)
        try:
            result = db.session.execute(text("""
                SELECT id, email
                FROM auth.users
                WHERE id = :user_id
            """), {"user_id": test_user_id})
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(f"   {row}")
            else:
                print("   (no results)")
        except Exception as e:
            print(f"   ⚠️  Cannot access auth.users: {e}")

        # 5. Check push tokens
        run_query(
            "5. Push notification tokens for user",
            """
            SELECT id, device_token, platform, created_at, updated_at
            FROM push_notification_tokens
            WHERE user_id = :user_id
            """,
            {"user_id": test_user_id}
        )

        # 6. Check recent notifications TO this user
        run_query(
            "6. Recent notifications TO this user",
            """
            SELECT id, notification_type, title, created_at, sent_at, is_read
            FROM notifications
            WHERE recipient_user_id = :user_id
            ORDER BY created_at DESC
            LIMIT 10
            """,
            {"user_id": test_user_id}
        )

        # 7. Check partner invitations to the NEW email
        run_query(
            "7. Partner invitations to NEW email",
            """
            SELECT id, requester_id, recipient_email, status, created_at
            FROM partner_connections
            WHERE recipient_email = :email
            ORDER BY created_at DESC
            LIMIT 5
            """,
            {"email": new_email}
        )

        # 8. Check partner invitations to the OLD email
        run_query(
            "8. Partner invitations to OLD email",
            """
            SELECT id, requester_id, recipient_email, status, created_at
            FROM partner_connections
            WHERE recipient_email = 'logger_faced.0p+test55@icloud.com'
            ORDER BY created_at DESC
            LIMIT 5
            """,
        )

        # 9. Check all triggers on auth.users
        run_query(
            "9. ALL triggers on auth.users",
            """
            SELECT tgname, tgenabled, pg_get_triggerdef(oid) as definition
            FROM pg_trigger
            WHERE tgrelid = 'auth.users'::regclass
            AND NOT tgisinternal
            """
        )

        # 10. Check for any recent errors in function
        run_query(
            "10. Check function definition",
            """
            SELECT pg_get_functiondef(oid)
            FROM pg_proc
            WHERE proname = 'handle_auth_user_email_update'
            """
        )

        print("\n" + "="*70)
        print("📋 SUMMARY")
        print("="*70)
        print("""
Next steps based on results:
1. If function/trigger don't exist → Migration didn't apply correctly
2. If public.users has old email → Trigger didn't fire (email changed before migration)
3. If no notifications exist → Partner invitation lookup failed
4. If no tokens exist → Push token was deleted
5. If notifications exist but sent_at is NULL → FCM send failed
        """)


if __name__ == '__main__':
    main()
