#!/usr/bin/env python3
"""Debug script to check push notification status."""

import os
import sys
from dotenv import load_dotenv
import psycopg

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not found")
    sys.exit(1)

try:
    conn = psycopg.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("=" * 60)
    print("PUSH NOTIFICATION DEBUG REPORT")
    print("=" * 60)
    
    # Check FCM tokens
    print("\n📱 FCM Tokens Registered:")
    print("-" * 60)
    cur.execute("""
        SELECT 
            u.display_name,
            u.email,
            pnt.platform,
            LEFT(pnt.device_token, 30) || '...' as token_preview,
            pnt.created_at
        FROM push_notification_tokens pnt
        JOIN users u ON u.id = pnt.user_id
        ORDER BY pnt.created_at DESC
        LIMIT 10
    """)
    tokens = cur.fetchall()
    if tokens:
        for t in tokens:
            print(f"  {t[0]} ({t[1]}) - {t[2]} - {t[3]} - {t[4]}")
    else:
        print("  ⚠️ No FCM tokens registered!")
    
    # Check recent notifications
    print("\n📬 Recent Notifications (last 10):")
    print("-" * 60)
    cur.execute("""
        SELECT 
            n.id,
            n.notification_type,
            n.title,
            n.sent_at,
            n.created_at,
            u.display_name as recipient
        FROM notifications n
        LEFT JOIN users u ON u.id = n.recipient_user_id
        ORDER BY n.created_at DESC
        LIMIT 10
    """)
    notifications = cur.fetchall()
    if notifications:
        for n in notifications:
            sent_status = "✅ SENT" if n[3] else "❌ NOT SENT"
            print(f"  [{n[0]}] {n[1]} → {n[5]} | {sent_status} | {n[4]}")
    else:
        print("  ⚠️ No notifications in database!")
    
    # Check recent partner connections
    print("\n🤝 Recent Partner Connections:")
    print("-" * 60)
    cur.execute("""
        SELECT 
            pc.id,
            pc.status,
            pc.recipient_email,
            pc.created_at,
            u.display_name as requester
        FROM partner_connections pc
        JOIN users u ON u.id = pc.requester_user_id
        ORDER BY pc.created_at DESC
        LIMIT 5
    """)
    connections = cur.fetchall()
    for c in connections:
        print(f"  [{c[0]}] {c[4]} → {c[2]} | status: {c[1]} | {c[3]}")
    
    print("\n" + "=" * 60)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
