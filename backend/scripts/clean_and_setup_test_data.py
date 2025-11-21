"""
Clean and Setup Test Data Script
Safely cleans existing test data and creates fresh test users.

Usage:
    python backend/scripts/clean_and_setup_test_data.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.extensions import db
from backend.src.main import create_app


def clean_test_users(app):
    """
    Clean existing test users from database.
    Uses raw SQL to avoid model attribute issues.
    """
    print("\n🧹 Cleaning existing test data...")
    
    test_emails = [
        'alice@test.com',
        'bob@test.com',
        'charlie@test.com',
        'diana@test.com',
        'eve@test.com',
        'uat-test@example.com',
        'dev@attuned.com',
        'test@attuned.com'
    ]
    
    with app.app_context():
        try:
            # Delete test users (CASCADE will delete related data)
            deleted = 0
            for email in test_emails:
                result = db.session.execute(
                    db.text("DELETE FROM users WHERE email = :email"),
                    {'email': email}
                )
                deleted += result.rowcount
            
            # Delete test anonymous profiles
            result = db.session.execute(
                db.text("""
                    DELETE FROM profiles 
                    WHERE is_anonymous = true 
                    AND anonymous_session_id LIKE 'test_%'
                """)
            )
            deleted_anon = result.rowcount
            
            db.session.commit()
            
            print(f"✅ Cleaned {deleted} test users and {deleted_anon} test anonymous profiles")
            
        except Exception as e:
            print(f"⚠️  Cleanup had issues: {e}")
            db.session.rollback()


def create_test_users_sql(app):
    """
    Create test users using raw SQL for reliability.
    """
    print("\n👥 Creating test users...")
    
    with app.app_context():
        try:
            # Create 5 test users
            db.session.execute(db.text("""
                INSERT INTO users (
                    id, email, display_name, auth_provider, 
                    subscription_tier, daily_activity_count,
                    demographics, profile_sharing_setting,
                    notification_preferences, profile_completed, onboarding_completed,
                    last_login_at, daily_activity_reset_at
                ) VALUES
                (
                    '550e8400-e29b-41d4-a716-446655440001'::uuid,
                    'alice@test.com',
                    'Alice (Top/Premium)',
                    'email',
                    'premium',
                    0,
                    '{"gender": "woman", "sexual_orientation": "bisexual", "relationship_structure": "open", "anatomy_self": ["vagina", "breasts"], "anatomy_preference": ["penis", "vagina"]}'::jsonb,
                    'overlapping_only',
                    '{}'::jsonb,
                    true,
                    true,
                    NOW(),
                    NOW()
                ),
                (
                    '550e8400-e29b-41d4-a716-446655440002'::uuid,
                    'bob@test.com',
                    'Bob (Bottom/Free)',
                    'google',
                    'free',
                    20,
                    '{"gender": "man", "sexual_orientation": "straight", "relationship_structure": "monogamous", "anatomy_self": ["penis"], "anatomy_preference": ["vagina", "breasts"]}'::jsonb,
                    'overlapping_only',
                    '{}'::jsonb,
                    true,
                    true,
                    NOW(),
                    NOW()
                ),
                (
                    '550e8400-e29b-41d4-a716-446655440003'::uuid,
                    'charlie@test.com',
                    'Charlie (Switch)',
                    'apple',
                    'free',
                    0,
                    '{"gender": "non-binary", "sexual_orientation": "bisexual", "relationship_structure": "rather_not_say", "anatomy_self": ["penis", "breasts"], "anatomy_preference": ["penis", "vagina", "breasts"]}'::jsonb,
                    'overlapping_only',
                    '{}'::jsonb,
                    true,
                    true,
                    NOW(),
                    NOW()
                ),
                (
                    '550e8400-e29b-41d4-a716-446655440004'::uuid,
                    'diana@test.com',
                    'Diana (Free/Limit)',
                    'facebook',
                    'free',
                    25,
                    '{"gender": "woman", "sexual_orientation": "gay", "relationship_structure": "monogamous", "anatomy_self": ["vagina"], "anatomy_preference": ["vagina"]}'::jsonb,
                    'overlapping_only',
                    '{}'::jsonb,
                    true,
                    true,
                    NOW(),
                    NOW()
                ),
                (
                    '550e8400-e29b-41d4-a716-446655440005'::uuid,
                    'eve@test.com',
                    'Eve (New User)',
                    'email',
                    'free',
                    0,
                    '{}'::jsonb,
                    'overlapping_only',
                    '{}'::jsonb,
                    false,
                    false,
                    NOW(),
                    NOW()
                );
            """))
            
            db.session.commit()
            
            print("   Created: Alice (Premium, demographics + survey complete)")
            print("   Created: Bob (Free near limit, demographics + survey complete)")
            print("   Created: Charlie (Free, demographics + survey complete)")
            print("   Created: Diana (Free at limit, demographics + survey complete)")
            print("   Created: Eve (New user, no demographics or survey)")
            print("✅ Created 5 test users")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Failed to create test users: {e}")
            raise


def verify_test_data(app):
    """Verify test data was created correctly."""
    print("\n✅ Verifying test data...")
    
    with app.app_context():
        # Count users
        result = db.session.execute(db.text("SELECT COUNT(*) FROM users WHERE email LIKE '%@test.com'"))
        user_count = result.scalar()
        
        print(f"   Users: {user_count}")
        
        # Show user details
        result = db.session.execute(db.text("""
            SELECT email, display_name, subscription_tier, profile_completed, onboarding_completed
            FROM users 
            WHERE email LIKE '%@test.com'
            ORDER BY email
        """))
        
        print("\n   Test user details:")
        print(f"     {'Email':<20} | {'Name':<25} | {'Tier':<10} | Demographics | Survey")
        print("     " + "-" * 85)
        for row in result:
            demo_status = '✅' if row[3] else '❌'
            survey_status = '✅' if row[4] else '❌'
            print(f"     {row[0]:<20} | {row[1]:<25} | {row[2]:<10} | {demo_status:<12} | {survey_status}")


def main():
    """Main execution."""
    print("=" * 60)
    print("  Attuned Test Data Setup (Clean & Create)")
    print("=" * 60)
    
    # Create Flask app
    app = create_app()
    
    # Step 1: Clean
    clean_test_users(app)
    
    # Step 2: Create
    create_test_users_sql(app)
    
    # Step 3: Verify
    verify_test_data(app)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Data Setup Complete!")
    print("=" * 60)
    print("\n  Test user credentials:")
    print("    alice@test.com    - Premium, 0/unlimited activities")
    print("    bob@test.com      - Free, 20/25 activities (near limit)")
    print("    charlie@test.com  - Free, 0/25 activities")
    print("    diana@test.com    - Free, 25/25 activities (at limit)")
    print("    eve@test.com      - Free, incomplete onboarding")
    print("\n✅ Ready for UAT testing!")
    print("\nNext steps:")
    print("  1. Start Flask backend: python src/main.py")
    print("  2. Execute UAT-002 from UAT_TEST_CASES.md")
    print("  3. Test API endpoints")


if __name__ == '__main__':
    main()

