#!/usr/bin/env python3
"""Apply migration 019 for notifications table."""

import os
import sys
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

migration_file = os.path.join(os.path.dirname(__file__), '..', 'migrations', '019_add_notifications_table.sql')

with open(migration_file, 'r') as f:
    migration_sql = f.read()

try:
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration 019_add_notifications_table.sql applied successfully!")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'notifications'")
    if cur.fetchone()[0] > 0:
        print("✅ notifications table exists")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
