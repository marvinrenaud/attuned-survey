#!/usr/bin/env python3
"""
Fix typos in activity descriptions.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db
from sqlalchemy import text


def fix_typos():
    """Run typo fixes on activities."""
    sql_file = Path(__file__).parent / 'fix_typos.sql'
    
    print("=" * 70)
    print("Fixing Activity Typos")
    print("=" * 70)
    print()
    
    with open(sql_file, 'r') as f:
        sql_content = f.read()
    
    with app.app_context():
        try:
            # Execute all updates
            db.session.execute(text(sql_content))
            db.session.commit()
            
            print("✅ Typo fixes applied successfully!")
            print()
            
            # Show what was updated
            result = db.session.execute(text("""
                SELECT activity_id, type, rating,
                       script->'steps'->0->>'do' as description
                FROM activities
                WHERE is_active = true
                  AND updated_at > NOW() - INTERVAL '1 minute'
                ORDER BY activity_id
            """))
            
            updated = list(result)
            if updated:
                print(f"Updated {len(updated)} activities:")
                for row in updated:
                    desc_preview = row[3][:70] if row[3] else "No description"
                    print(f"  ID {row[0]}: {row[1].upper()} - {desc_preview}...")
            else:
                print("No activities were updated (typos may have been fixed already)")
            
            print()
            print("=" * 70)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            db.session.rollback()
            return 1
    
    return 0


if __name__ == '__main__':
    exit_code = fix_typos()
    sys.exit(exit_code)

