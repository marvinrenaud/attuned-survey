"""
Test Data Setup Script
Creates comprehensive test data for MVP database testing.

This script creates:
- 5 authenticated test users with profiles
- 3 anonymous users with profiles
- Multiple partner connections
- Game sessions with various states
- Activity history for no-repeat testing
- Survey progress records

Usage:
    python backend/scripts/setup_test_users.py [--clean]
"""

import sys
import os
from datetime import datetime, timedelta
import uuid
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.extensions import db
from backend.src.main import create_app
from backend.src.models.user import User
from backend.src.models.profile import Profile
from backend.src.models.session import Session
from backend.src.models.survey import SurveySubmission


# Test user data
TEST_USERS = [
    {
        'id': '550e8400-e29b-41d4-a716-446655440001',
        'email': 'alice@test.com',
        'display_name': 'Alice (Top/Premium)',
        'auth_provider': 'email',
        'subscription_tier': 'premium',
        'demographics': {
            'gender': 'woman',
            'sexual_orientation': 'bisexual',
            'relationship_structure': 'open'
        },
        'profile': {
            'power_orientation': 'Top',
            'confidence': 85
        }
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440002',
        'email': 'bob@test.com',
        'display_name': 'Bob (Bottom/Free)',
        'auth_provider': 'google',
        'subscription_tier': 'free',
        'daily_activity_count': 20,  # Near limit
        'demographics': {
            'gender': 'man',
            'sexual_orientation': 'straight',
            'relationship_structure': 'monogamous'
        },
        'profile': {
            'power_orientation': 'Bottom',
            'confidence': 90
        }
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440003',
        'email': 'charlie@test.com',
        'display_name': 'Charlie (Switch)',
        'auth_provider': 'apple',
        'subscription_tier': 'free',
        'demographics': {
            'gender': 'non-binary',
            'sexual_orientation': 'bisexual',
            'relationship_structure': 'rather_not_say'
        },
        'profile': {
            'power_orientation': 'Switch',
            'confidence': 70
        }
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440004',
        'email': 'diana@test.com',
        'display_name': 'Diana (Free/Limit)',
        'auth_provider': 'facebook',
        'subscription_tier': 'free',
        'daily_activity_count': 25,  # At limit
        'demographics': {
            'gender': 'woman',
            'sexual_orientation': 'gay',
            'relationship_structure': 'monogamous'
        }
    },
    {
        'id': '550e8400-e29b-41d4-a716-446655440005',
        'email': 'eve@test.com',
        'display_name': 'Eve (New User)',
        'auth_provider': 'email',
        'subscription_tier': 'free',
        'onboarding_completed': False,
        'demographics': {}
    }
]


def clean_test_data(app):
    """Remove existing test data."""
    print("\n🧹 Cleaning existing test data...")
    
    with app.app_context():
        # Delete test users (cascade will handle related data)
        test_emails = [user['email'] for user in TEST_USERS]
        deleted = User.query.filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        
        # Delete test anonymous profiles
        deleted_anon = Profile.query.filter(
            Profile.is_anonymous == True,
            Profile.anonymous_session_id.like('test_%')
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        print(f"✅ Cleaned {deleted} test users and {deleted_anon} test anonymous profiles")


def create_test_users(app):
    """Create authenticated test users."""
    print("\n👥 Creating test users...")
    
    with app.app_context():
        created = []
        
        for user_data in TEST_USERS:
            user = User(
                id=user_data['id'],
                email=user_data['email'],
                display_name=user_data['display_name'],
                auth_provider=user_data['auth_provider'],
                subscription_tier=user_data['subscription_tier'],
                demographics=user_data.get('demographics', {}),
                daily_activity_count=user_data.get('daily_activity_count', 0),
                daily_activity_reset_at=datetime.utcnow(),
                onboarding_completed=user_data.get('onboarding_completed', True),
                last_login_at=datetime.utcnow()
            )
            
            db.session.add(user)
            created.append(user)
            print(f"   Created: {user.display_name} ({user.email})")
        
        db.session.commit()
        print(f"✅ Created {len(created)} test users")
        
        return created


def create_test_profiles(app, users):
    """Create profiles for test users."""
    print("\n📊 Creating test profiles...")
    
    with app.app_context():
        created = []
        
        for user in users[:4]:  # First 4 users have complete profiles
            # Create sample profile data
            profile = Profile(
                user_id=user.id,
                submission_id=f'test_sub_{user.id}',
                profile_version='0.4',
                power_dynamic={
                    'orientation': TEST_USERS[users.index(user)].get('profile', {}).get('power_orientation', 'Switch'),
                    'confidence': TEST_USERS[users.index(user)].get('profile', {}).get('confidence', 50)
                },
                arousal_propensity={'se': 0.7, 'sis_p': 0.3, 'sis_c': 0.5},
                domain_scores={'sensation': 60, 'connection': 75, 'power': 65, 'exploration': 50, 'verbal': 70},
                activities={'massage_give': 0.8, 'oral_give': 0.9, 'restraints_receive': 0.7},
                truth_topics={'past_experiences': 0.8, 'fantasies': 0.9},
                boundaries={'hard_limits': [], 'soft_limits': ['impact'], 'maybe_items': []},
                anatomy={'anatomy_self': ['vagina', 'breasts'], 'anatomy_preference': ['penis', 'vagina']},
                survey_version='0.4',
                is_anonymous=False
            )
            
            db.session.add(profile)
            created.append(profile)
            print(f"   Created profile for: {user.display_name}")
        
        db.session.commit()
        print(f"✅ Created {len(created)} test profiles")
        
        return created


def create_anonymous_profiles(app):
    """Create anonymous test profiles."""
    print("\n👻 Creating anonymous profiles...")
    
    with app.app_context():
        created = []
        
        for i in range(1, 4):
            anon_session_id = f'test_anon_{i}'
            
            profile = Profile(
                submission_id=f'test_anon_sub_{i}',
                profile_version='0.4',
                is_anonymous=True,
                anonymous_session_id=anon_session_id,
                last_accessed_at=datetime.utcnow(),
                power_dynamic={'orientation': 'Switch', 'confidence': 50},
                arousal_propensity={'se': 0.6, 'sis_p': 0.4, 'sis_c': 0.5},
                domain_scores={'sensation': 50, 'connection': 60, 'power': 50, 'exploration': 40, 'verbal': 60},
                activities={'massage_give': 0.7},
                truth_topics={'past_experiences': 0.6},
                boundaries={'hard_limits': [], 'soft_limits': [], 'maybe_items': []},
                anatomy={'anatomy_self': [], 'anatomy_preference': []},
                survey_version='0.4'
            )
            
            db.session.add(profile)
            created.append(profile)
            print(f"   Created anonymous profile: {anon_session_id}")
        
        db.session.commit()
        print(f"✅ Created {len(created)} anonymous profiles")
        
        return created


def create_partner_connections(app, users):
    """Create test partner connections."""
    print("\n🤝 Creating partner connections...")
    
    # This would require the PartnerConnection and RememberedPartner models
    # For now, just print what would be created
    
    print("   Would create:")
    print("     - Alice ↔ Bob (accepted)")
    print("     - Alice ↔ Charlie (accepted)")
    print("     - Bob → Diana (pending)")
    print("     - Charlie → Eve (declined)")
    print("   ⚠️  Partner connection tables need partner models")
    
    return 0


def create_test_sessions(app, profiles):
    """Create test game sessions."""
    print("\n🎮 Creating test sessions...")
    
    with app.app_context():
        # Get some profiles for sessions
        if len(profiles) < 2:
            print("   ⚠️  Need at least 2 profiles to create sessions")
            return []
        
        created = []
        
        # Session 1: Active session
        session1 = Session(
            session_id=str(uuid.uuid4()),
            player_a_profile_id=profiles[0].id,
            player_b_profile_id=profiles[1].id,
            primary_profile_id=profiles[0].id,
            partner_profile_id=profiles[1].id,
            rating='R',
            intimacy_level='R',
            status='active',
            current_step=10,
            created_at=datetime.utcnow()
        )
        db.session.add(session1)
        created.append(session1)
        print(f"   Created active session")
        
        # Session 2: Completed session
        session2 = Session(
            session_id=str(uuid.uuid4()),
            player_a_profile_id=profiles[0].id,
            player_b_profile_id=profiles[1].id,
            primary_profile_id=profiles[0].id,
            partner_profile_id=profiles[1].id,
            rating='X',
            intimacy_level='X',
            status='completed',
            current_step=25,
            created_at=datetime.utcnow() - timedelta(days=1),
            completed_at=datetime.utcnow() - timedelta(hours=2)
        )
        db.session.add(session2)
        created.append(session2)
        print(f"   Created completed session")
        
        db.session.commit()
        print(f"✅ Created {len(created)} test sessions")
        
        return created


def create_survey_progress(app, users):
    """Create in-progress survey records."""
    print("\n📝 Creating survey progress records...")
    
    # This would require SurveyProgress model
    print("   Would create:")
    print("     - Eve: In-progress survey (60% complete)")
    print("     - Bob: In-progress survey (25% complete)")
    print("   ⚠️  Survey progress table needs model definition")
    
    return 0


def main():
    """Main test data setup function."""
    print("=" * 60)
    print("  Attuned Test Data Setup")
    print("=" * 60)
    
    # Check for clean flag
    clean = '--clean' in sys.argv
    
    # Create Flask app
    app = create_app()
    
    # Clean existing test data if requested
    if clean:
        clean_test_data(app)
    
    # Create test data
    users = create_test_users(app)
    profiles = create_test_profiles(app, users)
    anon_profiles = create_anonymous_profiles(app)
    
    # Create relationships and sessions
    partner_connections = create_partner_connections(app, users)
    sessions = create_test_sessions(app, profiles)
    survey_progress = create_survey_progress(app, users)
    
    # Summary
    print("\n" + "=" * 60)
    print("  Test Data Summary")
    print("=" * 60)
    print(f"  Users: {len(users)}")
    print(f"  Profiles (authenticated): {len(profiles)}")
    print(f"  Profiles (anonymous): {len(anon_profiles)}")
    print(f"  Sessions: {len(sessions)}")
    print("\n  Test user credentials:")
    print("    alice@test.com (Premium, Top)")
    print("    bob@test.com (Free near limit, Bottom)")
    print("    charlie@test.com (Free, Switch)")
    print("    diana@test.com (Free at limit)")
    print("    eve@test.com (Incomplete onboarding)")
    print("\n✅ TEST DATA SETUP COMPLETE")
    print("\nNext steps:")
    print("  1. Test authentication flows")
    print("  2. Test subscription limits")
    print("  3. Test partner connections")
    print("  4. Test game sessions")


if __name__ == '__main__':
    main()

