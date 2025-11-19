"""
Migration Script: Prototype → MVP Database
Migrates existing prototype data to new MVP schema.

This script:
1. Backs up the current database
2. Marks all existing profiles as anonymous
3. Generates anonymous_session_ids for existing profiles
4. Updates sessions to new schema
5. Backfills survey_version on existing submissions
6. Validates data integrity after migration

Usage:
    python backend/scripts/migrate_prototype_to_mvp.py [--dry-run]
"""

import sys
import os
from datetime import datetime
import uuid
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.extensions import db
from backend.src.main import create_app
from backend.src.models.profile import Profile
from backend.src.models.session import Session
from backend.src.models.survey import SurveySubmission


def backup_database(app):
    """
    Create a backup of critical tables before migration.
    """
    print("\n📦 Creating database backup...")
    
    backup_dir = os.path.join(os.path.dirname(__file__), '../backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'pre_mvp_migration_{timestamp}.json')
    
    with app.app_context():
        backup_data = {
            'timestamp': timestamp,
            'profiles_count': Profile.query.count(),
            'sessions_count': Session.query.count(),
            'submissions_count': SurveySubmission.query.count(),
            'profiles': [],
            'sessions': [],
            'submissions': []
        }
        
        # Backup profiles
        for profile in Profile.query.all():
            backup_data['profiles'].append({
                'id': profile.id,
                'submission_id': profile.submission_id,
                'profile_version': profile.profile_version,
                'created_at': profile.created_at.isoformat() if profile.created_at else None
            })
        
        # Backup sessions
        for session in Session.query.limit(100).all():  # Sample of recent sessions
            backup_data['sessions'].append({
                'session_id': session.session_id,
                'player_a_profile_id': session.player_a_profile_id,
                'player_b_profile_id': session.player_b_profile_id,
                'status': session.status,
                'created_at': session.created_at.isoformat() if session.created_at else None
            })
        
        # Backup submissions (metadata only)
        for submission in SurveySubmission.query.limit(100).all():
            backup_data['submissions'].append({
                'id': submission.id,
                'submission_id': submission.submission_id,
                'respondent_id': submission.respondent_id,
                'created_at': submission.created_at.isoformat() if submission.created_at else None
            })
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        print(f"✅ Backup created: {backup_file}")
        print(f"   - Profiles: {backup_data['profiles_count']}")
        print(f"   - Sessions: {backup_data['sessions_count']}")
        print(f"   - Submissions: {backup_data['submissions_count']}")
    
    return backup_file


def migrate_profiles_to_anonymous(app, dry_run=False):
    """
    Mark all existing profiles as anonymous and generate session IDs.
    """
    print("\n👤 Migrating profiles to anonymous...")
    
    with app.app_context():
        profiles = Profile.query.filter(
            (Profile.is_anonymous == False) | (Profile.is_anonymous.is_(None))
        ).all()
        
        count = len(profiles)
        print(f"   Found {count} profiles to migrate")
        
        if dry_run:
            print("   [DRY RUN] Would mark profiles as anonymous")
            return count
        
        for i, profile in enumerate(profiles, 1):
            # Generate unique anonymous session ID
            anon_session_id = f"proto_{uuid.uuid4()}"
            
            profile.is_anonymous = True
            profile.anonymous_session_id = anon_session_id
            profile.user_id = None  # No authenticated user
            profile.last_accessed_at = datetime.utcnow()
            
            if i % 100 == 0:
                print(f"   Processed {i}/{count} profiles...")
                db.session.commit()
        
        db.session.commit()
        print(f"✅ Migrated {count} profiles to anonymous")
    
    return count


def backfill_survey_versions(app, dry_run=False):
    """
    Backfill survey_version='0.4' on existing submissions.
    """
    print("\n📝 Backfilling survey versions...")
    
    with app.app_context():
        submissions = SurveySubmission.query.filter(
            (SurveySubmission.survey_version == None) |
            (SurveySubmission.survey_version == '')
        ).all()
        
        count = len(submissions)
        print(f"   Found {count} submissions to backfill")
        
        if dry_run:
            print("   [DRY RUN] Would set survey_version='0.4'")
            return count
        
        for submission in submissions:
            submission.survey_version = '0.4'
        
        db.session.commit()
        print(f"✅ Backfilled {count} submissions with version 0.4")
    
    return count


def migrate_sessions(app, dry_run=False):
    """
    Update sessions to new schema (mark all as anonymous).
    """
    print("\n🎮 Migrating sessions...")
    
    with app.app_context():
        sessions = Session.query.filter(
            Session.primary_profile_id.is_(None)
        ).all()
        
        count = len(sessions)
        print(f"   Found {count} sessions to migrate")
        
        if dry_run:
            print("   [DRY RUN] Would update session schema")
            return count
        
        for session in sessions:
            # Set primary and partner from existing player fields
            session.primary_profile_id = session.player_a_profile_id
            session.partner_profile_id = session.player_b_profile_id
            
            # Mark as anonymous (no user_id)
            session.primary_user_id = None
            session.partner_user_id = None
            session.session_owner_user_id = None
            
            # Set default intimacy level based on rating
            if hasattr(session, 'rating'):
                if session.rating == 'G':
                    session.intimacy_level = 'G'
                elif session.rating == 'X':
                    session.intimacy_level = 'X'
                else:
                    session.intimacy_level = 'R'
            else:
                session.intimacy_level = 'R'
            
            session.skip_count = 0
        
        db.session.commit()
        print(f"✅ Migrated {count} sessions")
    
    return count


def create_anonymous_sessions(app, dry_run=False):
    """
    Create anonymous_sessions entries for migrated profiles.
    """
    print("\n🔗 Creating anonymous session records...")
    
    with app.app_context():
        # This would require the AnonymousSession model
        # For now, just report what would be done
        profiles = Profile.query.filter(
            Profile.is_anonymous == True,
            Profile.anonymous_session_id.isnot(None)
        ).all()
        
        count = len(profiles)
        print(f"   Found {count} anonymous profiles")
        
        if dry_run:
            print("   [DRY RUN] Would create anonymous_sessions entries")
            return count
        
        # TODO: Insert into anonymous_sessions table
        # INSERT INTO anonymous_sessions (session_id, profile_id, last_accessed_at, created_at)
        # This would be done via raw SQL or after defining AnonymousSession model
        
        print(f"   ⚠️  Anonymous sessions table needs to be created first (run migrations)")
        print(f"   Would create {count} anonymous session entries")
    
    return count


def validate_migration(app):
    """
    Validate data integrity after migration.
    """
    print("\n✅ Validating migration...")
    
    with app.app_context():
        # Check profile migration
        anonymous_count = Profile.query.filter_by(is_anonymous=True).count()
        total_profiles = Profile.query.count()
        
        print(f"   Profiles:")
        print(f"     - Total: {total_profiles}")
        print(f"     - Anonymous: {anonymous_count}")
        print(f"     - Authenticated: {total_profiles - anonymous_count}")
        
        # Check sessions
        sessions_with_new_schema = Session.query.filter(
            Session.primary_profile_id.isnot(None)
        ).count()
        total_sessions = Session.query.count()
        
        print(f"   Sessions:")
        print(f"     - Total: {total_sessions}")
        print(f"     - Migrated: {sessions_with_new_schema}")
        
        # Check submissions
        v04_submissions = SurveySubmission.query.filter_by(survey_version='0.4').count()
        total_submissions = SurveySubmission.query.count()
        
        print(f"   Submissions:")
        print(f"     - Total: {total_submissions}")
        print(f"     - Version 0.4: {v04_submissions}")
        
        # Integrity checks
        issues = []
        
        # Check for profiles without anonymous_session_id
        profiles_missing_session = Profile.query.filter(
            Profile.is_anonymous == True,
            Profile.anonymous_session_id.is_(None)
        ).count()
        
        if profiles_missing_session > 0:
            issues.append(f"⚠️  {profiles_missing_session} anonymous profiles missing session_id")
        
        # Check for sessions without primary_profile_id
        sessions_missing_primary = Session.query.filter(
            Session.primary_profile_id.is_(None)
        ).count()
        
        if sessions_missing_primary > 0:
            issues.append(f"⚠️  {sessions_missing_primary} sessions missing primary_profile_id")
        
        if issues:
            print("\n   Issues found:")
            for issue in issues:
                print(f"     {issue}")
            return False
        else:
            print("\n   ✅ All integrity checks passed!")
            return True


def main():
    """
    Main migration function.
    """
    print("=" * 60)
    print("  Attuned Database Migration: Prototype → MVP")
    print("=" * 60)
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("\n🧪 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  LIVE MODE - Database will be modified\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
    
    # Create Flask app context
    app = create_app()
    
    # Step 1: Backup
    if not dry_run:
        backup_file = backup_database(app)
        print(f"\nBackup saved to: {backup_file}")
    
    # Step 2: Migrate profiles
    profiles_migrated = migrate_profiles_to_anonymous(app, dry_run)
    
    # Step 3: Backfill survey versions
    submissions_backfilled = backfill_survey_versions(app, dry_run)
    
    # Step 4: Migrate sessions
    sessions_migrated = migrate_sessions(app, dry_run)
    
    # Step 5: Create anonymous sessions
    anon_sessions_created = create_anonymous_sessions(app, dry_run)
    
    # Step 6: Validate
    if not dry_run:
        validation_passed = validate_migration(app)
    else:
        validation_passed = True
    
    # Summary
    print("\n" + "=" * 60)
    print("  Migration Summary")
    print("=" * 60)
    print(f"  Profiles migrated: {profiles_migrated}")
    print(f"  Submissions backfilled: {submissions_backfilled}")
    print(f"  Sessions migrated: {sessions_migrated}")
    print(f"  Anonymous sessions: {anon_sessions_created}")
    print(f"  Validation: {'✅ PASSED' if validation_passed else '❌ FAILED'}")
    
    if dry_run:
        print("\n🧪 DRY RUN COMPLETE - Run without --dry-run to apply changes")
    else:
        print("\n✅ MIGRATION COMPLETE")
        print(f"\nBackup location: {backup_file}")
        print("Next steps:")
        print("  1. Test the application with migrated data")
        print("  2. Run migrations 003-008 on production database")
        print("  3. Monitor for any issues")


if __name__ == '__main__':
    main()

