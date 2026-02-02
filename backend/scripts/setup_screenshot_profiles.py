"""
Screenshot Profile Setup Script
Creates realistic profiles for app store screenshots using diverse test fixtures.

Usage:
    cd backend
    source venv/bin/activate
    python scripts/setup_screenshot_profiles.py

Prerequisites:
    - 4 accounts must already exist in Supabase Auth (created via normal signup)
    - Update EMAIL_TO_PROFILE mapping below with actual email addresses

Profiles Created:
    1. Jordan - Confident Top (95/10)
    2. Sam - Eager Bottom (10/95), partner with Morgan
    3. Morgan - Romantic Switch (50/55), 2+ partners (Jordan, Sam)
    4. Taylor - Reserved Versatile (25/30), solo
"""

import sys
import os
import uuid
import secrets
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extensions import db
from src.main import create_app
from src.models.user import User
from src.models.profile import Profile
from src.models.survey import SurveySubmission
from src.models.partner import PartnerConnection, RememberedPartner

# =============================================================================
# CONFIGURATION - Update these emails to match the accounts you created
# =============================================================================

EMAIL_TO_PROFILE = {
    'logger_faced.0p+jordan@icloud.com': 'jordan',   # Confident Top
    'logger_faced.0p+sammie@icloud.com': 'sam',      # Eager Bottom
    'logger_faced.0p+morgan@icloud.com': 'morgan',   # Romantic Switch - will have 2 partners
    'logger_faced.0p+taylor@icloud.com': 'taylor',   # Reserved Versatile
}

# =============================================================================
# Profile Data (based on diverse_test_profiles.py)
# =============================================================================

PROFILES = {
    'jordan': {
        'display_name': 'Jordan',
        'demographics': {
            'gender': 'man',
            'sexual_orientation': 'bisexual',
            'relationship_structure': 'open'
        },
        'anatomy': {
            'has_penis': True,
            'has_vagina': False,
            'has_breasts': False,
            'likes_penis': True,
            'likes_vagina': True,
            'likes_breasts': True,
        },
        'profile_data': {
            'power_dynamic': {
                'orientation': 'Top',
                'top_score': 95,
                'bottom_score': 10,
                'confidence': 0.90,
                'interpretation': 'Very high confidence Top'
            },
            'arousal_propensity': {
                'sexual_excitation': 0.80,
                'inhibition_performance': 0.25,
                'inhibition_consequence': 0.30,
            },
            'domain_scores': {
                'sensation': 65,
                'connection': 85,
                'power': 75,
                'exploration': 50,
                'verbal': 70,
            },
            'activities': {
                'physical_touch': {
                    'massage_give': 1.0, 'massage_receive': 1.0,
                    'hair_pull_gentle_give': 1.0, 'hair_pull_gentle_receive': 0.5,
                    'spanking_moderate_give': 1.0, 'spanking_moderate_receive': 0.5,
                    'biting_moderate_give': 0.8, 'biting_moderate_receive': 0.5,
                    'hands_genitals_give': 1.0, 'hands_genitals_receive': 1.0,
                },
                'oral': {
                    'oral_sex_give': 1.0, 'oral_sex_receive': 1.0,
                    'oral_body_give': 1.0, 'oral_body_receive': 1.0,
                },
                'power_exchange': {
                    'restraints_give': 1.0, 'restraints_receive': 0.0,
                    'blindfold_give': 1.0, 'blindfold_receive': 0.5,
                    'orgasm_control_give': 1.0, 'orgasm_control_receive': 0.0,
                },
                'verbal_roleplay': {
                    'dirty_talk': 1.0,
                    'moaning': 1.0,
                    'commands_give': 1.0, 'commands_receive': 0.0,
                    'begging_give': 0.0, 'begging_receive': 1.0,
                },
            },
            'truth_topics': {
                'past_experiences': 0.8,
                'fantasies': 0.9,
                'turn_ons': 0.9,
                'turn_offs': 0.8,
                'insecurities': 0.7,
                'boundaries': 0.9,
                'future_fantasies': 0.8,
                'feeling_desired': 0.9,
            },
            'boundaries': {'hard_limits': [], 'soft_limits': [], 'maybe_items': []},
        }
    },
    'sam': {
        'display_name': 'Sam',
        'demographics': {
            'gender': 'woman',
            'sexual_orientation': 'straight',
            'relationship_structure': 'open'
        },
        'anatomy': {
            'has_penis': False,
            'has_vagina': True,
            'has_breasts': True,
            'likes_penis': True,
            'likes_vagina': False,
            'likes_breasts': False,
        },
        'profile_data': {
            'power_dynamic': {
                'orientation': 'Bottom',
                'top_score': 10,
                'bottom_score': 95,
                'confidence': 0.90,
                'interpretation': 'Very high confidence Bottom'
            },
            'arousal_propensity': {
                'sexual_excitation': 0.85,
                'inhibition_performance': 0.20,
                'inhibition_consequence': 0.25,
            },
            'domain_scores': {
                'sensation': 65,
                'connection': 85,
                'power': 75,
                'exploration': 55,
                'verbal': 70,
            },
            'activities': {
                'physical_touch': {
                    'massage_give': 1.0, 'massage_receive': 1.0,
                    'hair_pull_gentle_give': 0.5, 'hair_pull_gentle_receive': 1.0,
                    'spanking_moderate_give': 0.5, 'spanking_moderate_receive': 1.0,
                    'biting_moderate_give': 0.5, 'biting_moderate_receive': 0.8,
                    'hands_genitals_give': 1.0, 'hands_genitals_receive': 1.0,
                },
                'oral': {
                    'oral_sex_give': 1.0, 'oral_sex_receive': 1.0,
                    'oral_body_give': 1.0, 'oral_body_receive': 1.0,
                },
                'power_exchange': {
                    'restraints_give': 0.0, 'restraints_receive': 1.0,
                    'blindfold_give': 0.5, 'blindfold_receive': 1.0,
                    'orgasm_control_give': 0.0, 'orgasm_control_receive': 1.0,
                },
                'verbal_roleplay': {
                    'dirty_talk': 1.0,
                    'moaning': 1.0,
                    'commands_give': 0.0, 'commands_receive': 1.0,
                    'begging_give': 1.0, 'begging_receive': 0.0,
                },
            },
            'truth_topics': {
                'past_experiences': 0.8,
                'fantasies': 0.9,
                'turn_ons': 0.9,
                'turn_offs': 0.8,
                'insecurities': 0.7,
                'boundaries': 0.9,
                'future_fantasies': 0.8,
                'feeling_desired': 0.9,
            },
            'boundaries': {'hard_limits': [], 'soft_limits': [], 'maybe_items': []},
        }
    },
    'morgan': {
        'display_name': 'Morgan',
        'demographics': {
            'gender': 'non-binary',
            'sexual_orientation': 'bisexual',
            'relationship_structure': 'open'
        },
        'anatomy': {
            'has_penis': False,
            'has_vagina': True,
            'has_breasts': True,
            'likes_penis': True,
            'likes_vagina': True,
            'likes_breasts': True,
        },
        'profile_data': {
            'power_dynamic': {
                'orientation': 'Switch',
                'top_score': 50,
                'bottom_score': 55,
                'confidence': 0.55,
                'interpretation': 'Moderate confidence Switch'
            },
            'arousal_propensity': {
                'sexual_excitation': 0.55,
                'inhibition_performance': 0.45,
                'inhibition_consequence': 0.50,
            },
            'domain_scores': {
                'sensation': 45,
                'connection': 90,
                'power': 15,
                'exploration': 25,
                'verbal': 40,
            },
            'activities': {
                'physical_touch': {
                    'massage_give': 1.0, 'massage_receive': 1.0,
                    'hair_pull_gentle_give': 0.5, 'hair_pull_gentle_receive': 0.5,
                    'biting_moderate_give': 0.5, 'biting_moderate_receive': 0.5,
                    'hands_genitals_give': 1.0, 'hands_genitals_receive': 1.0,
                },
                'oral': {
                    'oral_sex_give': 1.0, 'oral_sex_receive': 1.0,
                    'oral_body_give': 1.0, 'oral_body_receive': 1.0,
                },
                'power_exchange': {},
                'verbal_roleplay': {
                    'dirty_talk': 0.5,
                    'moaning': 1.0,
                },
            },
            'truth_topics': {
                'past_experiences': 0.7,
                'fantasies': 0.7,
                'turn_ons': 0.8,
                'turn_offs': 0.8,
                'insecurities': 0.5,
                'boundaries': 0.9,
                'future_fantasies': 0.6,
                'feeling_desired': 0.9,
            },
            'boundaries': {'hard_limits': ['breath_play', 'impact_play'], 'soft_limits': [], 'maybe_items': []},
        }
    },
    'taylor': {
        'display_name': 'Taylor',
        'demographics': {
            'gender': 'woman',
            'sexual_orientation': 'straight',
            'relationship_structure': 'monogamous'
        },
        'anatomy': {
            'has_penis': False,
            'has_vagina': True,
            'has_breasts': True,
            'likes_penis': True,
            'likes_vagina': False,
            'likes_breasts': False,
        },
        'profile_data': {
            'power_dynamic': {
                'orientation': 'Versatile',
                'top_score': 25,
                'bottom_score': 30,
                'confidence': 0.35,
                'interpretation': 'Low confidence, versatile'
            },
            'arousal_propensity': {
                'sexual_excitation': 0.30,
                'inhibition_performance': 0.55,
                'inhibition_consequence': 0.60,
            },
            'domain_scores': {
                'sensation': 35,
                'connection': 65,
                'power': 25,
                'exploration': 20,
                'verbal': 40,
            },
            'activities': {
                'physical_touch': {
                    'massage_give': 1.0, 'massage_receive': 1.0,
                    'hands_genitals_give': 1.0, 'hands_genitals_receive': 1.0,
                },
                'oral': {
                    'oral_sex_give': 0.8, 'oral_sex_receive': 0.8,
                    'oral_body_give': 0.8, 'oral_body_receive': 0.8,
                },
                'power_exchange': {},
                'verbal_roleplay': {
                    'moaning': 0.8,
                },
            },
            'truth_topics': {
                'past_experiences': 0.5,
                'fantasies': 0.4,
                'turn_ons': 0.6,
                'turn_offs': 0.7,
                'insecurities': 0.3,
                'boundaries': 0.8,
                'future_fantasies': 0.4,
                'feeling_desired': 0.7,
            },
            'boundaries': {
                'hard_limits': ['breath_play', 'impact_play', 'anal', 'watersports'],
                'soft_limits': ['roleplay', 'restraints'],
                'maybe_items': ['blindfold']
            },
        }
    },
}

# Partner connections: Morgan has multiple partners
PARTNER_CONNECTIONS = [
    ('morgan', 'jordan'),  # Morgan <-> Jordan
    ('morgan', 'sam'),     # Morgan <-> Sam
]


def get_user_by_email(email):
    """Find user by email."""
    return User.query.filter_by(email=email).first()


def create_survey_submission(user, profile_key):
    """Create a survey submission for the user."""
    submission_id = f'screenshot_{profile_key}_{uuid.uuid4().hex[:8]}'

    # Create a minimal but valid payload
    submission = SurveySubmission(
        submission_id=submission_id,
        user_id=user.id,
        respondent_id=str(user.id),
        name=PROFILES[profile_key]['display_name'],
        survey_version='0.4',
        payload_json={
            'source': 'screenshot_setup',
            'created_by': 'setup_screenshot_profiles.py'
        }
    )

    db.session.add(submission)
    db.session.flush()  # Get submission_id

    return submission


def create_profile(user, submission, profile_key):
    """Create a profile from the fixture data."""
    profile_config = PROFILES[profile_key]
    profile_data = profile_config['profile_data']

    # Flatten activities for storage
    flat_activities = {}
    for category, activities in profile_data['activities'].items():
        flat_activities.update(activities)

    profile = Profile(
        user_id=user.id,
        submission_id=submission.submission_id,
        profile_version='0.4',
        survey_version='0.4',
        is_anonymous=False,
        power_dynamic=profile_data['power_dynamic'],
        arousal_propensity=profile_data['arousal_propensity'],
        domain_scores=profile_data['domain_scores'],
        activities=flat_activities,
        truth_topics=profile_data['truth_topics'],
        boundaries=profile_data['boundaries'],
        anatomy={
            'anatomy_self': user.get_anatomy_self_array(),
            'anatomy_preference': user.get_anatomy_preference_array(),
        },
    )

    db.session.add(profile)
    return profile


def update_user(user, profile_key):
    """Update user with profile-specific data."""
    profile_config = PROFILES[profile_key]

    user.display_name = profile_config['display_name']
    user.demographics = profile_config['demographics']

    # Anatomy
    anatomy = profile_config['anatomy']
    user.has_penis = anatomy['has_penis']
    user.has_vagina = anatomy['has_vagina']
    user.has_breasts = anatomy['has_breasts']
    user.likes_penis = anatomy['likes_penis']
    user.likes_vagina = anatomy['likes_vagina']
    user.likes_breasts = anatomy['likes_breasts']

    # Mark as completed
    user.onboarding_completed = True
    user.profile_completed = True

    # Make Morgan premium for screenshots (the one with multiple partners)
    if profile_key == 'morgan':
        user.subscription_tier = 'premium'
        user.subscription_expires_at = datetime.utcnow() + timedelta(days=365)


def create_partner_connection(requester, recipient):
    """Create accepted partner connection between two users."""
    token = secrets.token_urlsafe(32)

    connection = PartnerConnection(
        requester_user_id=requester.id,
        requester_display_name=requester.display_name,
        recipient_email=recipient.email,
        recipient_user_id=recipient.id,
        recipient_display_name=recipient.display_name,
        status='accepted',
        connection_token=token,
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    db.session.add(connection)
    return connection


def create_remembered_partners(user1, user2):
    """Create remembered partner records (bidirectional)."""
    # User1 remembers User2
    rp1 = RememberedPartner(
        user_id=user1.id,
        partner_user_id=user2.id,
        partner_name=user2.display_name,
        partner_email=user2.email,
        last_played_at=datetime.utcnow() - timedelta(hours=2),
    )

    # User2 remembers User1
    rp2 = RememberedPartner(
        user_id=user2.id,
        partner_user_id=user1.id,
        partner_name=user1.display_name,
        partner_email=user1.email,
        last_played_at=datetime.utcnow() - timedelta(hours=2),
    )

    db.session.add(rp1)
    db.session.add(rp2)


def cleanup_existing_data(users):
    """Remove existing profiles and connections for these users."""
    for user in users.values():
        if user:
            # Delete existing profiles
            Profile.query.filter_by(user_id=user.id).delete()

            # Delete existing survey submissions
            SurveySubmission.query.filter_by(user_id=user.id).delete()

            # Delete existing partner connections
            PartnerConnection.query.filter(
                (PartnerConnection.requester_user_id == user.id) |
                (PartnerConnection.recipient_user_id == user.id)
            ).delete(synchronize_session=False)

            # Delete existing remembered partners
            RememberedPartner.query.filter(
                (RememberedPartner.user_id == user.id) |
                (RememberedPartner.partner_user_id == user.id)
            ).delete(synchronize_session=False)

    db.session.commit()


def main():
    print("=" * 60)
    print("  Screenshot Profile Setup")
    print("=" * 60)

    app = create_app()

    with app.app_context():
        # Step 1: Find all users
        print("\n1. Looking up users...")
        users = {}
        missing = []

        for email, profile_key in EMAIL_TO_PROFILE.items():
            user = get_user_by_email(email)
            if user:
                users[profile_key] = user
                print(f"   Found: {email} -> {profile_key}")
            else:
                missing.append(email)
                print(f"   MISSING: {email}")

        if missing:
            print(f"\n   ERROR: {len(missing)} accounts not found!")
            print("   Please create these accounts first via normal app signup:")
            for email in missing:
                print(f"     - {email}")
            print("\n   Then update EMAIL_TO_PROFILE in this script if needed.")
            return

        # Step 2: Clean up existing data
        print("\n2. Cleaning up existing profile data...")
        cleanup_existing_data(users)
        print("   Done")

        # Step 3: Update users and create profiles
        print("\n3. Creating profiles...")
        for profile_key, user in users.items():
            update_user(user, profile_key)
            submission = create_survey_submission(user, profile_key)
            profile = create_profile(user, submission, profile_key)
            print(f"   Created: {user.display_name} ({profile.power_dynamic['orientation']})")

        db.session.commit()

        # Step 4: Create partner connections
        print("\n4. Creating partner connections...")
        for requester_key, recipient_key in PARTNER_CONNECTIONS:
            requester = users[requester_key]
            recipient = users[recipient_key]

            create_partner_connection(requester, recipient)
            create_remembered_partners(requester, recipient)
            print(f"   Connected: {requester.display_name} <-> {recipient.display_name}")

        db.session.commit()

        # Summary
        print("\n" + "=" * 60)
        print("  Setup Complete!")
        print("=" * 60)
        print("\n  Screenshot Accounts:")
        for profile_key, user in users.items():
            profile = Profile.query.filter_by(user_id=user.id).first()
            partner_count = RememberedPartner.query.filter_by(user_id=user.id).count()
            tier = "Premium" if user.subscription_tier == 'premium' else "Free"
            print(f"    {user.display_name:10} | {profile.power_dynamic['orientation']:10} | {partner_count} partner(s) | {tier}")

        print("\n  Login with your passwords to capture screenshots.")
        print("  Morgan has multiple partners for the partners list screenshot.")


if __name__ == '__main__':
    main()
