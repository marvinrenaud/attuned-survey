import os
import sys
from pathlib import Path
from sqlalchemy import text

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app
from src.extensions import db

def verify_migration():
    """Verify that migration 012 was applied correctly."""
    print("Verifying Migration 012...")
    print("-" * 50)
    
    with app.app_context():
        # 1. Check if user_id column exists
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'survey_submissions' AND column_name = 'user_id';
        """)).fetchone()
        
        if result:
            print("✅ user_id column exists in survey_submissions")
        else:
            print("❌ user_id column MISSING in survey_submissions")
            return False

        # 2. Check RLS policies
        policies = db.session.execute(text("""
            SELECT policyname 
            FROM pg_policies 
            WHERE tablename = 'survey_submissions';
        """)).fetchall()
        
        policy_names = [p[0] for p in policies]
        expected_policies = ['survey_submissions_insert_own', 'survey_submissions_select_own']
        
        if all(p in policy_names for p in expected_policies):
             print(f"✅ RLS policies found: {', '.join(expected_policies)}")
        else:
             print(f"❌ Missing RLS policies. Found: {policy_names}")
             return False
             
        # 3. Check Index
        indexes = db.session.execute(text("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE tablename = 'survey_submissions' AND indexname = 'idx_survey_submissions_user_id';
        """)).fetchone()
        
        if indexes:
            print("✅ Index idx_survey_submissions_user_id exists")
        else:
            print("❌ Index idx_survey_submissions_user_id MISSING")
            return False

    print("-" * 50)
    print("Verification Complete!")
    return True

if __name__ == "__main__":
    verify_migration()
