#!/usr/bin/env python3
"""
Migrate activity preference_keys to new naming convention.

This script updates the preference_keys field in activities to align with
the new naming convention after compatibility algorithm fixes:
- stripping_me → stripping_self
- watched_solo_pleasure → solo_pleasure_self  
- posing, dancing, revealing_clothing → *_self
- protocols_follow → protocols_receive
- commands → commands_give/receive (context-dependent)
- begging → begging_give/receive (context-dependent)
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Simple renames (one-to-one mapping)
SIMPLE_RENAMES = {
    'stripping_me': 'stripping_self',
    'watched_solo_pleasure': 'solo_pleasure_self',
    'posing': 'posing_self',
    'dancing': 'dancing_self',
    'revealing_clothing': 'revealing_clothing_self',
    'protocols_follow': 'protocols_receive',
}

def analyze_context_dependent(activity: dict, old_key: str) -> list:
    """
    Analyze activity context to determine which directional variant to use.
    
    For 'commands' and 'begging', we need to determine if the activity is about
    giving or receiving based on the power_role and description.
    """
    power_role = activity.get('power_role', 'neutral')
    description = activity.get('description', '').lower()
    
    if old_key == 'commands':
        # If power_role is 'top' or description mentions giving/ordering
        if power_role == 'top' or any(word in description for word in ['command', 'order', 'tell', 'direct', 'instruct']):
            return ['commands_give']
        # If power_role is 'bottom' or description mentions following/obeying
        elif power_role == 'bottom' or any(word in description for word in ['follow', 'obey', 'submit', 'listen']):
            return ['commands_receive']
        # Neutral - could be either, keep both or remove
        else:
            return []  # Remove for neutral activities
    
    elif old_key == 'begging':
        # If power_role is 'top' or description mentions hearing/enjoying begging
        if power_role == 'top' or any(word in description for word in ['hear', 'listen to', 'enjoy', 'make them beg']):
            return ['begging_give']  # Top enjoys hearing begging
        # If power_role is 'bottom' or description mentions doing the begging
        elif power_role == 'bottom' or any(word in description for word in ['beg', 'plead', 'ask for']):
            return ['begging_receive']  # Bottom does the begging
        # Neutral - could be either
        else:
            return []  # Remove for neutral activities
    
    return []

def migrate_preference_keys(activity: dict, dry_run: bool = True) -> dict:
    """
    Migrate preference_keys for a single activity.
    
    Returns dict with 'changed', 'old_keys', 'new_keys'
    """
    preference_keys = activity.get('preference_keys', [])
    if not preference_keys:
        return {'changed': False, 'old_keys': [], 'new_keys': []}
    
    new_keys = []
    changes = []
    
    for key in preference_keys:
        # Simple rename
        if key in SIMPLE_RENAMES:
            new_key = SIMPLE_RENAMES[key]
            new_keys.append(new_key)
            changes.append(f"{key} → {new_key}")
        # Context-dependent (commands, begging)
        elif key in ['commands', 'begging']:
            replacements = analyze_context_dependent(activity, key)
            if replacements:
                new_keys.extend(replacements)
                changes.append(f"{key} → {', '.join(replacements)}")
            else:
                changes.append(f"{key} → [removed - neutral activity]")
        # Keep as-is
        else:
            new_keys.append(key)
    
    changed = len(changes) > 0
    
    return {
        'changed': changed,
        'old_keys': preference_keys if changed else [],
        'new_keys': new_keys if changed else [],
        'changes': changes if changed else []
    }

def migrate_json_file(filepath: str, dry_run: bool = True) -> dict:
    """
    Migrate a JSON file containing enriched activities.
    
    Returns statistics about the migration.
    """
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    stats = {
        'total': 0,
        'changed': 0,
        'by_change_type': {}
    }
    
    updated_data = {}
    
    for activity_id, activity in data.items():
        stats['total'] += 1
        
        result = migrate_preference_keys(activity, dry_run)
        
        if result['changed']:
            stats['changed'] += 1
            
            # Track change types
            for change in result['changes']:
                stats['by_change_type'][change] = stats['by_change_type'].get(change, 0) + 1
            
            if not dry_run:
                activity['preference_keys'] = result['new_keys']
                updated_data[activity_id] = activity
            else:
                print(f"  Activity {activity_id}: {', '.join(result['changes'])}")
        else:
            if not dry_run:
                updated_data[activity_id] = activity
    
    # Write back if not dry run
    if not dry_run and stats['changed'] > 0:
        backup_path = filepath + '.backup'
        print(f"  Creating backup: {backup_path}")
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  Writing updated data to: {filepath}")
        with open(filepath, 'w') as f:
            json.dump(updated_data, f, indent=2)
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Migrate activity preference_keys')
    parser.add_argument('--execute', action='store_true', help='Execute migration (default is dry-run)')
    parser.add_argument('--file', type=str, help='Specific JSON file to migrate (default: enriched_activities_v2.json)')
    args = parser.parse_args()
    
    dry_run = not args.execute
    
    if dry_run:
        print("=" * 60)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 60)
    else:
        print("=" * 60)
        print("EXECUTE MODE - Changes will be applied")
        print("=" * 60)
        confirm = input("Are you sure you want to proceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            return
    
    # Determine file to process
    if args.file:
        files = [args.file]
    else:
        backend_dir = Path(__file__).parent.parent
        files = [
            str(backend_dir / 'enriched_activities_v2.json'),
            str(backend_dir / 'scripts' / 'enriched_activities.json'),
        ]
        # Filter to existing files
        files = [f for f in files if os.path.exists(f)]
    
    if not files:
        print("No files found to process.")
        return
    
    total_stats = {
        'total': 0,
        'changed': 0,
        'by_change_type': {}
    }
    
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        
        stats = migrate_json_file(filepath, dry_run)
        
        total_stats['total'] += stats['total']
        total_stats['changed'] += stats['changed']
        
        for change_type, count in stats['by_change_type'].items():
            total_stats['by_change_type'][change_type] = total_stats['by_change_type'].get(change_type, 0) + count
    
    # Summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    print(f"Total activities processed: {total_stats['total']}")
    print(f"Activities changed: {total_stats['changed']}")
    print("\nChanges by type:")
    for change_type, count in sorted(total_stats['by_change_type'].items()):
        print(f"  {change_type}: {count} activities")
    
    if dry_run:
        print("\nTo apply these changes, run with --execute flag")

if __name__ == '__main__':
    main()

