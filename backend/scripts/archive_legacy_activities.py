#!/usr/bin/env python3
"""
Archive legacy activities by source_version.
Marks activities from previous imports as inactive while preserving data.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from src.models.activity import Activity


def archive_legacy_activities(current_version: str = 'Consolidated_ToD_Activities_v20', dry_run: bool = True):
    """
    Archive activities that don't match the current source version.
    
    Args:
        current_version: Current source version to keep active
        dry_run: If True, preview without committing
    """
    print("=" * 70)
    print("Archive Legacy Activities")
    print("=" * 70)
    
    if dry_run:
        print("\n[DRY RUN MODE] - No changes will be committed\n")
    else:
        print(f"\nArchiving activities NOT from source: {current_version}\n")
    
    with app.app_context():
        # Find legacy activities (different source_version or null)
        legacy_activities = Activity.query.filter(
            Activity.source_version != current_version,
            Activity.is_active == True
        ).all()
        
        # Also find activities with null source_version (very old)
        null_source = Activity.query.filter(
            Activity.source_version.is_(None),
            Activity.is_active == True
        ).all()
        
        # Combine
        to_archive = legacy_activities + null_source
        
        if not to_archive:
            print("✓ No legacy activities found to archive\n")
            print("=" * 70)
            return 0
        
        print(f"Found {len(to_archive)} legacy activities to archive:")
        print(f"  - {len(legacy_activities)} with different source_version")
        print(f"  - {len(null_source)} with null source_version")
        print()
        
        # Show breakdown by source
        source_counts = {}
        for activity in to_archive:
            source = activity.source_version or 'null'
            source_counts[source] = source_counts.get(source, 0) + 1
        
        print("Breakdown by source_version:")
        for source, count in sorted(source_counts.items()):
            print(f"  {source}: {count} activities")
        print()
        
        # Show samples
        if len(to_archive) <= 10:
            print("Activities to archive:")
            for activity in to_archive:
                desc = activity.script.get('steps', [{}])[0].get('do', 'No description')[:60]
                print(f"  ID {activity.activity_id}: {activity.type} - {desc}...")
            print()
        else:
            print(f"Sample of activities to archive (first 5):")
            for activity in to_archive[:5]:
                desc = activity.script.get('steps', [{}])[0].get('do', 'No description')[:60]
                print(f"  ID {activity.activity_id}: {activity.type} - {desc}...")
            print(f"  ... and {len(to_archive) - 5} more")
            print()
        
        if dry_run:
            print(f"[DRY RUN] Would archive {len(to_archive)} activities")
        else:
            # Archive them
            archived_count = Activity.query.filter(
                Activity.activity_id.in_([a.activity_id for a in to_archive])
            ).update({
                'is_active': False,
                'archived_at': datetime.utcnow()
            }, synchronize_session='fetch')
            
            db.session.commit()
            print(f"✅ Archived {archived_count} legacy activities")
        
        print()
        print("=" * 70)
        
        # Show current state
        with app.app_context():
            total = Activity.query.count()
            active = Activity.query.filter_by(is_active=True).count()
            archived = Activity.query.filter_by(is_active=False).count()
            current_version_count = Activity.query.filter_by(
                source_version=current_version,
                is_active=True
            ).count()
            
            print("\nCurrent Activity Bank State:")
            print(f"  Total activities in database: {total}")
            print(f"  Active: {active}")
            print(f"  Archived: {archived}")
            print(f"  Active from {current_version}: {current_version_count}")
        
        print("=" * 70)
        
        if dry_run:
            print("\n💡 Run with --apply to commit these changes")
        
        return 0


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Archive legacy activities by source_version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview what would be archived
  python archive_legacy_activities.py --dry-run
  
  # Execute archiving
  python archive_legacy_activities.py --apply
  
  # Specify custom version to keep
  python archive_legacy_activities.py --apply --keep-version "MyVersion"
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Preview archiving without committing')
    group.add_argument('--apply', action='store_true',
                      help='Execute archiving and commit changes')
    
    parser.add_argument('--keep-version', default='Consolidated_ToD_Activities_v20',
                       help='Source version to keep active (default: Consolidated_ToD_Activities_v20)')
    
    args = parser.parse_args()
    
    exit_code = archive_legacy_activities(
        current_version=args.keep_version,
        dry_run=args.dry_run
    )
    
    sys.exit(exit_code)

