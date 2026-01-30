#!/usr/bin/env python3
"""
One-time data repair script for remembered_partners table.

Problem: Before migration 030, changes to users.display_name and users.email
did not sync to remembered_partners.partner_name and partner_email.

This script:
1. Identifies all stale entries where remembered_partners data doesn't match users
2. Updates those entries with current user data
3. Reports what was changed

Usage:
    # Preview changes without applying (dry-run)
    python scripts/repair_stale_partner_data.py --dry-run

    # Apply changes
    python scripts/repair_stale_partner_data.py --apply

NOTE: Run this AFTER applying migration 030_sync_remembered_partners.sql.
The migration creates triggers to prevent future staleness. This script
fixes historical data that went stale before the triggers existed.
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import create_app
from src.extensions import db


def find_stale_entries():
    """Find all remembered_partners entries with stale data."""
    query = """
        SELECT
            rp.id as rp_id,
            rp.user_id,
            rp.partner_user_id,
            rp.partner_email as stale_email,
            u.email as current_email,
            rp.partner_name as stale_name,
            u.display_name as current_name
        FROM remembered_partners rp
        JOIN users u ON rp.partner_user_id = u.id
        WHERE rp.partner_email != u.email
           OR rp.partner_name IS DISTINCT FROM u.display_name
    """
    result = db.session.execute(db.text(query)).fetchall()
    return result


def repair_stale_entries(dry_run=True):
    """
    Repair stale remembered_partners entries.

    Args:
        dry_run: If True, only report what would be changed

    Returns:
        Number of entries fixed
    """
    stale_entries = find_stale_entries()

    if not stale_entries:
        print("No stale entries found. Database is consistent.")
        return 0

    print(f"\nFound {len(stale_entries)} stale entries:\n")
    print("-" * 100)

    for entry in stale_entries:
        rp_id, user_id, partner_user_id, stale_email, current_email, stale_name, current_name = entry

        email_changed = stale_email != current_email
        name_changed = stale_name != current_name

        changes = []
        if email_changed:
            changes.append(f"email: '{stale_email}' -> '{current_email}'")
        if name_changed:
            changes.append(f"name: '{stale_name}' -> '{current_name}'")

        print(f"  ID {rp_id}: {', '.join(changes)}")

    print("-" * 100)

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(stale_entries)} entries.")
        print("Run with --apply to make changes.")
        return 0

    # Apply the fix
    update_query = """
        UPDATE remembered_partners rp
        SET
            partner_email = u.email,
            partner_name = u.display_name
        FROM users u
        WHERE rp.partner_user_id = u.id
          AND (rp.partner_email != u.email
               OR rp.partner_name IS DISTINCT FROM u.display_name)
    """

    result = db.session.execute(db.text(update_query))
    db.session.commit()

    fixed_count = result.rowcount
    print(f"\nSuccessfully updated {fixed_count} entries.")

    # Verify no more stale entries
    remaining = find_stale_entries()
    if remaining:
        print(f"WARNING: {len(remaining)} entries still stale after repair!")
    else:
        print("Verification: All entries now consistent.")

    return fixed_count


def main():
    parser = argparse.ArgumentParser(
        description='Repair stale partner data in remembered_partners table',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true',
                      help='Preview changes without applying')
    group.add_argument('--apply', action='store_true',
                      help='Apply fixes to database')

    args = parser.parse_args()

    app = create_app()

    print("=" * 70)
    print("Stale Partner Data Repair Script")
    print("=" * 70)

    with app.app_context():
        repair_stale_entries(dry_run=args.dry_run)

    print("\n" + "=" * 70)


if __name__ == '__main__':
    main()
