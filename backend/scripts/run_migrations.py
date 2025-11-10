#!/usr/bin/env python3
"""
Migration runner script for Attuned database schema updates.
Executes SQL migration files in order with idempotent operations.
"""
import sys
import os
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from sqlalchemy import text


def run_migration_file(filepath: Path, dry_run: bool = False) -> bool:
    """
    Execute a single migration SQL file.
    
    Args:
        filepath: Path to SQL file
        dry_run: If True, only print SQL without executing
    
    Returns:
        True if successful, False otherwise
    """
    if not filepath.exists():
        print(f"❌ Migration file not found: {filepath}")
        return False
    
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Running migration: {filepath.name}")
    print("─" * 70)
    
    with open(filepath, 'r') as f:
        sql_content = f.read()
    
    if dry_run:
        print(sql_content)
        print("─" * 70)
        print(f"✓ [DRY RUN] Would execute {filepath.name}")
        return True
    
    try:
        # Execute entire SQL file as one transaction
        # PostgreSQL can handle multiple statements including DO blocks
        with app.app_context():
            db.session.execute(text(sql_content))
            db.session.commit()
            
            print(f"✅ Successfully executed {filepath.name}")
            return True
    
    except Exception as e:
        print(f"❌ Error executing {filepath.name}: {str(e)}")
        # Rollback must happen inside app context
        try:
            with app.app_context():
                db.session.rollback()
        except:
            pass  # Rollback already happened or context issue
        return False


def run_migrations(dry_run: bool = False, rollback: bool = False) -> int:
    """
    Run all migrations in order.
    
    Args:
        dry_run: If True, only print SQL without executing
        rollback: If True, run rollback script instead
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    migrations_dir = Path(__file__).parent.parent / 'migrations'
    
    if not migrations_dir.exists():
        print(f"❌ Migrations directory not found: {migrations_dir}")
        return 1
    
    print("=" * 70)
    print("Attuned Database Migration Runner")
    print("=" * 70)
    
    if rollback:
        # Run rollback script
        rollback_file = migrations_dir / 'rollback_001.sql'
        if not rollback_file.exists():
            print(f"❌ Rollback file not found: {rollback_file}")
            return 1
        
        print("\n⚠️  WARNING: Running rollback will result in data loss!")
        if not dry_run:
            response = input("Are you sure you want to continue? (type 'yes' to confirm): ")
            if response.lower() != 'yes':
                print("Rollback cancelled.")
                return 0
        
        success = run_migration_file(rollback_file, dry_run)
        return 0 if success else 1
    
    # Run forward migrations
    migration_files = [
        '000_add_profiles_anatomy.sql',
        '001_add_activity_extensions.sql',
        '002_add_activity_indexes.sql'
    ]
    
    failed = []
    for filename in migration_files:
        filepath = migrations_dir / filename
        if not run_migration_file(filepath, dry_run):
            failed.append(filename)
    
    print("\n" + "=" * 70)
    if failed:
        print(f"❌ Migration failed! {len(failed)} file(s) had errors:")
        for f in failed:
            print(f"  - {f}")
        print("=" * 70)
        return 1
    else:
        print(f"✅ All migrations {'would be' if dry_run else ''} completed successfully!")
        print("=" * 70)
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run database migrations for Attuned',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview migrations without executing
  python run_migrations.py --dry-run
  
  # Execute migrations
  python run_migrations.py --apply
  
  # Rollback migrations (WARNING: data loss)
  python run_migrations.py --rollback --apply
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Preview migrations without executing')
    group.add_argument('--apply', action='store_true',
                      help='Execute migrations')
    
    parser.add_argument('--rollback', action='store_true',
                       help='Run rollback script instead of forward migrations')
    
    args = parser.parse_args()
    
    dry_run = args.dry_run
    
    exit_code = run_migrations(dry_run=dry_run, rollback=args.rollback)
    sys.exit(exit_code)

