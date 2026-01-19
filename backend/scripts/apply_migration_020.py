#!/usr/bin/env python3
"""Apply migration 020 for is_read column."""

import os
import sys
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

migration_file = os.path.join(os.path.dirname(__file__), '..', 'migrations', '020_add_notification_is_read.sql')

with open(migration_file, 'r') as f:
    migration_sql = f.read()

try:
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute(migration_sql)
    conn.commit()
    
    print("✅ Migration 020_add_notification_is_read.sql applied successfully!")
    
    # Verify
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'notifications' AND column_name = 'is_read'")
    if cur.fetchone():
        print("✅ is_read column exists")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Migration failed: {e}")
    sys.exit(1)
