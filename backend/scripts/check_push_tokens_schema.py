#!/usr/bin/env python3
"""
Quick script to verify the push_notification_tokens table schema in Supabase.
"""

import os
import sys
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'push_notification_tokens'
        );
    """)
    table_exists = cur.fetchone()[0]
    
    if not table_exists:
        print("❌ Table 'push_notification_tokens' does NOT exist!")
        sys.exit(1)
    
    print("✅ Table 'push_notification_tokens' EXISTS\n")
    
    # Get column details
    print("📋 Column Schema:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            udt_name,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' 
        AND table_name = 'push_notification_tokens'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    for col in columns:
        col_name, data_type, udt_name, nullable, default = col
        print(f"  {col_name:20} | {udt_name:20} | nullable={nullable:3} | default={default}")
    
    print()
    
    # Get constraints
    print("🔒 Constraints:")
    print("-" * 80)
    cur.execute("""
        SELECT 
            tc.constraint_name,
            tc.constraint_type,
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
            ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'public' 
        AND tc.table_name = 'push_notification_tokens';
    """)
    
    constraints = cur.fetchall()
    for c in constraints:
        print(f"  {c[1]:15} | {c[0]:40} | column: {c[2]}")
    
    print()
    
    # Get foreign key details
    print("🔗 Foreign Keys:")
    print("-" * 80)
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name = 'push_notification_tokens';
    """)
    
    fks = cur.fetchall()
    for fk in fks:
        print(f"  {fk[0]} → {fk[1]}.{fk[2]}")
    
    if not fks:
        print("  (none)")
    
    print()
    
    # Get indexes
    print("📇 Indexes:")
    print("-" * 80)
    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = 'push_notification_tokens';
    """)
    
    indexes = cur.fetchall()
    for idx in indexes:
        print(f"  {idx[0]}")
        print(f"    {idx[1]}")
    
    print()
    
    # Get row count
    cur.execute("SELECT COUNT(*) FROM push_notification_tokens;")
    count = cur.fetchone()[0]
    print(f"📊 Current row count: {count}")
    
    cur.close()
    conn.close()
    
    print("\n✅ Schema verification complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
