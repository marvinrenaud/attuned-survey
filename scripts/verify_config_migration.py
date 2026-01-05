import sys
import os

import time
from sqlalchemy import text

# Add backend/src to path
# Set path to allow importing from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from src.main import create_app
from src.extensions import db
from src.services.config_service import get_config, get_config_int, refresh_cache
from src.config import settings

def run_verification():
    app = create_app()
    
    with app.app_context():
        print("🔍 Starting Verification...")
        
        # 0. Apply Migration / Seed Data
        print("\n0️⃣  Applying Migration / Seeding Data...")
        try:
             # Try to seed data directly (INSERT is allowed on Pooler)
             seed_sql = """
             INSERT INTO app_config (key, value, description) VALUES
                ('profile_version', '0.4', 'Current profile/survey version'),
                ('default_target_activities', '25', 'Default number of activities per game session'),
                ('default_bank_ratio', '0.5', 'Ratio for activity banking algorithm'),
                ('default_rating', 'R', 'Default content rating filter (G, PG, PG13, R, NC17)'),
                ('daily_free_limit', '25', 'Daily activity limit for free tier users'),
                ('gen_temperature', '0.6', 'Default temperature for LLM generation'),
                ('repair_use_ai', 'true', 'Feature flag to use AI for relationship repair suggestions')
             ON CONFLICT (key) DO NOTHING;
             """
             db.session.execute(text(seed_sql))
             db.session.commit()
             print("✅ Seed data applied.")
        except Exception as e:
             db.session.rollback()
             print(f"⚠️ Seeding failed: {e}")

        try:
             # Try creating RPC function (Might fail on Pooler)
             rpc_sql = """
             CREATE OR REPLACE FUNCTION get_all_app_configs()
             RETURNS TABLE (key TEXT, value TEXT, description TEXT) AS $$
             BEGIN
                 RETURN QUERY SELECT ac.key, ac.value, ac.description FROM app_config ac;
             END;
             $$ LANGUAGE plpgsql SECURITY DEFINER;
             """
             db.session.execute(text(rpc_sql))
             db.session.commit()
             print("✅ RPC Function created.")
        except Exception as e:
             db.session.rollback()
             print(f"⚠️ RPC Function creation failed (Expected if using Supabase Pooler): {e}")



        # 1. Test Fallback
        print("\n1️⃣  Testing Fallback...")
        val = get_config("NON_EXISTENT_KEY", "fallback_value")
        if val == "fallback_value":
            print("✅ Default fallback works.")
        else:
            print(f"❌ Default fallback failed. Got: {val}")

        # 2. Test DB Seed Values
        print("\n2️⃣  Testing DB Seed Values...")
        rating = get_config("default_rating")
        if rating == "R":
            print("✅ 'default_rating' correctly fetched as 'R' from DB.")
        else:
            print(f"❌ 'default_rating' mismatch. Got: {rating}")
            
        target = get_config_int("default_target_activities")
        if target == 25:
             print("✅ 'default_target_activities' correctly fetched as 25.")
        else:
             print(f"❌ 'default_target_activities' mismatch. Got: {target}")

        # 3. Test RPC Function
        print("\n3️⃣  Testing RPC Function...")
        try:
            result = db.session.execute(text("SELECT * FROM get_all_app_configs()")).fetchall()
            if len(result) >= 5:
                print(f"✅ RPC returned {len(result)} rows.")
            else:
                print(f"❌ RPC returned too few rows ({len(result)}). Expected >= 5.")
        except Exception as e:
            print(f"❌ RPC call failed: {e}")

        # 4. Test Cache Refresh (Integration Style)
        print("\n4️⃣  Testing Cache Refresh...")
        # Update value in DB directly
        db.session.execute(text("UPDATE app_config SET value = 'PG-13' WHERE key = 'default_rating'"))
        db.session.commit()
        
        # Verify old value is still cached
        old_val = get_config("default_rating")
        if old_val == "R":
            print("✅ Cache is holding old value (Expected).")
        else:
             print(f"⚠️ Cache updated unexpectedly or wasn't cached. Got: {old_val}")
        
        # Trigger Refresh
        refresh_cache()
        
        new_val = get_config("default_rating")
        if new_val == "PG-13":
            print("✅ Cache refresh worked! Value is now 'PG-13'.")
        else:
            print(f"❌ Cache refresh failed. Got: {new_val}")
            
        # Cleanup
        db.session.execute(text("UPDATE app_config SET value = 'R' WHERE key = 'default_rating'"))
        db.session.commit()
        print("✅ Cleanup done.")
        
        print("\n🎉 Verification Complete!")

if __name__ == "__main__":
    run_verification()
