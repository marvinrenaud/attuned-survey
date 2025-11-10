#!/usr/bin/env python3
"""
Schema verification script to validate that migrations were applied correctly.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from sqlalchemy import text, inspect


def verify_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        with app.app_context():
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
    except Exception as e:
        print(f"Error checking {table_name}.{column_name}: {e}")
        return False


def verify_index_exists(index_name: str) -> bool:
    """Check if an index exists."""
    try:
        with app.app_context():
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM pg_indexes 
                WHERE indexname = :index_name
            """), {'index_name': index_name})
            count = result.scalar()
            return count > 0
    except Exception as e:
        print(f"Error checking index {index_name}: {e}")
        return False


def verify_schema():
    """Run all schema verification checks."""
    print("=" * 70)
    print("Attuned Database Schema Verification")
    print("=" * 70)
    
    checks = []
    
    # Check profiles.anatomy column
    print("\nVerifying profiles table...")
    checks.append(('profiles.anatomy', verify_column_exists('profiles', 'anatomy')))
    
    # Check activities table columns
    print("\nVerifying activities table...")
    activity_columns = [
        'audience_scope',
        'hard_boundaries',
        'required_bodyparts',
        'activity_uid',
        'source_version',
        'is_active',
        'archived_at'
    ]
    
    for col in activity_columns:
        checks.append((f'activities.{col}', verify_column_exists('activities', col)))
    
    # Check indexes
    print("\nVerifying indexes...")
    indexes = [
        'idx_activities_hard_boundaries',
        'idx_activities_required_bodyparts',
        'idx_activities_audience_scope',
        'idx_activities_activity_uid',
        'idx_activities_is_active',
        'idx_activities_active_lookup'
    ]
    
    for idx in indexes:
        checks.append((idx, verify_index_exists(idx)))
    
    # Print results
    print("\n" + "=" * 70)
    print("Verification Results")
    print("=" * 70)
    
    passed = 0
    failed = 0
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    exit_code = verify_schema()
    sys.exit(exit_code)

