#!/usr/bin/env python3
"""
Migrate legacy boundary keys to new 8-key taxonomy.
Updates profile boundaries to use the standardized boundary keys.
"""
import sys
import os
from pathlib import Path
from collections import Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from src.models.profile import Profile
from src.models.activity import ALLOWED_BOUNDARIES


# Mapping from legacy boundary keys to new 8-key taxonomy
LEGACY_TO_NEW_MAPPING = {
    # Old keys → New keys
    'impact_play': 'hardBoundaryImpact',
    'restraints_bondage': 'hardBoundaryRestrain',
    'breath_play': 'hardBoundaryBreath',
    'degradation_humiliation': 'hardBoundaryDegrade',
    'public_activities': 'hardBoundaryPublic',
    'recording': 'hardBoundaryRecord',
    'anal_activities': 'hardBoundaryAnal',
    'watersports': 'hardBoundaryWatersports',
    
    # Alternative spellings/formats
    'impact': 'hardBoundaryImpact',
    'restraints': 'hardBoundaryRestrain',
    'bondage': 'hardBoundaryRestrain',
    'breath': 'hardBoundaryBreath',
    'choking': 'hardBoundaryBreath',
    'degradation': 'hardBoundaryDegrade',
    'humiliation': 'hardBoundaryDegrade',
    'public': 'hardBoundaryPublic',
    'public_play': 'hardBoundaryPublic',
    'recording_photos': 'hardBoundaryRecord',
    'recording_videos': 'hardBoundaryRecord',
    'photos': 'hardBoundaryRecord',
    'videos': 'hardBoundaryRecord',
    'anal': 'hardBoundaryAnal',
    'watersports_scat': 'hardBoundaryWatersports',
    'bodily_fluids': 'hardBoundaryWatersports',
    
    # Already in new format (keep as-is)
    'hardBoundaryImpact': 'hardBoundaryImpact',
    'hardBoundaryRestrain': 'hardBoundaryRestrain',
    'hardBoundaryBreath': 'hardBoundaryBreath',
    'hardBoundaryDegrade': 'hardBoundaryDegrade',
    'hardBoundaryPublic': 'hardBoundaryPublic',
    'hardBoundaryRecord': 'hardBoundaryRecord',
    'hardBoundaryAnal': 'hardBoundaryAnal',
    'hardBoundaryWatersports': 'hardBoundaryWatersports',
}


def migrate_profile_boundaries(profile: Profile, dry_run: bool = True) -> dict:
    """
    Migrate legacy boundary keys in a single profile.
    
    Args:
        profile: Profile instance to migrate
        dry_run: If True, don't commit changes
    
    Returns:
        Dict with migration stats for this profile
    """
    stats = {
        'profile_id': profile.id,
        'had_boundaries': False,
        'keys_migrated': [],
        'keys_deprecated': [],
        'keys_kept': []
    }
    
    boundaries = profile.boundaries or {}
    hard_limits = boundaries.get('hard_limits', [])
    
    if not hard_limits:
        return stats
    
    stats['had_boundaries'] = True
    original_count = len(hard_limits)
    
    # Migrate keys
    migrated = []
    deprecated = []
    
    for old_key in hard_limits:
        old_key_clean = str(old_key).strip()
        
        if old_key_clean in LEGACY_TO_NEW_MAPPING:
            new_key = LEGACY_TO_NEW_MAPPING[old_key_clean]
            if new_key in ALLOWED_BOUNDARIES:
                migrated.append(new_key)
                if old_key_clean != new_key:
                    stats['keys_migrated'].append(f"{old_key_clean} → {new_key}")
                else:
                    stats['keys_kept'].append(old_key_clean)
            else:
                deprecated.append(old_key_clean)
                stats['keys_deprecated'].append(old_key_clean)
        else:
            # Unknown key - try to keep if it's in allowed list
            if old_key_clean in ALLOWED_BOUNDARIES:
                migrated.append(old_key_clean)
                stats['keys_kept'].append(old_key_clean)
            else:
                deprecated.append(old_key_clean)
                stats['keys_deprecated'].append(old_key_clean)
    
    # Remove duplicates, preserve order
    migrated_unique = []
    seen = set()
    for key in migrated:
        if key not in seen:
            migrated_unique.append(key)
            seen.add(key)
    
    # Update profile
    boundaries['hard_limits'] = migrated_unique
    profile.boundaries = boundaries
    
    if not dry_run:
        db.session.add(profile)
    
    return stats


def run_migration(dry_run: bool = True) -> dict:
    """
    Run boundary taxonomy migration on all profiles.
    
    Args:
        dry_run: If True, preview changes without committing
    
    Returns:
        Dict with overall migration stats
    """
    print("=" * 70)
    print("Boundary Taxonomy Migration")
    print("=" * 70)
    
    if dry_run:
        print("\n[DRY RUN MODE] - No changes will be committed\n")
    
    with app.app_context():
        profiles = Profile.query.all()
        
        print(f"Found {len(profiles)} profiles to check\n")
        
        # Overall stats
        overall = {
            'total_profiles': len(profiles),
            'profiles_with_boundaries': 0,
            'profiles_migrated': 0,
            'total_keys_migrated': Counter(),
            'total_keys_deprecated': Counter()
        }
        
        detailed_stats = []
        
        for profile in profiles:
            stats = migrate_profile_boundaries(profile, dry_run)
            
            if stats['had_boundaries']:
                overall['profiles_with_boundaries'] += 1
                
                if stats['keys_migrated'] or stats['keys_deprecated']:
                    overall['profiles_migrated'] += 1
                    detailed_stats.append(stats)
                    
                    # Count migrations
                    for migration in stats['keys_migrated']:
                        old, new = migration.split(' → ')
                        overall['total_keys_migrated'][migration] += 1
                    
                    # Count deprecations
                    for deprecated in stats['keys_deprecated']:
                        overall['total_keys_deprecated'][deprecated] += 1
        
        # Commit if not dry run
        if not dry_run:
            try:
                db.session.commit()
                print("✅ Changes committed to database\n")
            except Exception as e:
                print(f"❌ Error committing changes: {e}\n")
                db.session.rollback()
                return overall
        
        # Print summary
        print("─" * 70)
        print("Migration Summary")
        print("─" * 70)
        print(f"Total profiles: {overall['total_profiles']}")
        print(f"Profiles with boundaries: {overall['profiles_with_boundaries']}")
        print(f"Profiles migrated: {overall['profiles_migrated']}")
        
        if overall['total_keys_migrated']:
            print(f"\nKey Migrations:")
            for migration, count in overall['total_keys_migrated'].most_common():
                print(f"  {migration} ({count} profiles)")
        
        if overall['total_keys_deprecated']:
            print(f"\nDeprecated Keys (removed):")
            for key, count in overall['total_keys_deprecated'].most_common():
                print(f"  {key} ({count} profiles)")
        
        # Show sample of detailed migrations
        if detailed_stats and len(detailed_stats) <= 10:
            print(f"\nDetailed migrations:")
            for stats in detailed_stats:
                print(f"\n  Profile {stats['profile_id']}:")
                if stats['keys_migrated']:
                    print(f"    Migrated: {', '.join(stats['keys_migrated'])}")
                if stats['keys_deprecated']:
                    print(f"    Deprecated: {', '.join(stats['keys_deprecated'])}")
                if stats['keys_kept']:
                    print(f"    Kept: {', '.join(stats['keys_kept'])}")
        
        print("\n" + "=" * 70)
        
        if dry_run:
            print("\n💡 Run with --apply to commit these changes")
        
        return overall


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Migrate legacy boundary keys to new 8-key taxonomy',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migration (dry-run)
  python migrate_boundary_taxonomy.py --dry-run
  
  # Execute migration
  python migrate_boundary_taxonomy.py --apply
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Preview migration without committing changes')
    group.add_argument('--apply', action='store_true',
                      help='Execute migration and commit changes')
    
    args = parser.parse_args()
    
    result = run_migration(dry_run=args.dry_run)
    
    sys.exit(0)

