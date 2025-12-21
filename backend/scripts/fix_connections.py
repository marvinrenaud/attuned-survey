
import sys
import os

# Ensure backend src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import create_app, db
from src.routes.partners import PartnerConnection, RememberedPartner
from sqlalchemy import text
from datetime import datetime, timedelta

def fix_inconsistent_connections():
    app = create_app()
    with app.app_context():
        print("--- STARTING CONNECTION REPAIR ---\n")
        
        # 1. Fetch all Remembered Relationships
        rps = RememberedPartner.query.all()
        checked_pairs = set()
        
        fixed_count = 0
        
        for rp in rps:
            u1 = str(rp.user_id)
            u2 = str(rp.partner_user_id)
            
            pair_key = tuple(sorted([u1, u2]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            # Find Connection
            conn = PartnerConnection.query.filter(
                ((PartnerConnection.requester_user_id == u1) & (PartnerConnection.recipient_user_id == u2)) |
                ((PartnerConnection.requester_user_id == u2) & (PartnerConnection.recipient_user_id == u1))
            ).order_by(PartnerConnection.created_at.desc()).first()
            
            if conn:
                print(f"DEBUG: Found Conn {conn.id} for {u1}-{u2}. Status: {conn.status}")
                if conn.status == 'expired':
                    print(f"[FIXING] Resetting expired connection {conn.id} to 'accepted'")
                    conn.status = 'accepted'
                    conn.expires_at = datetime.utcnow() + timedelta(days=3650) # Set to future
                    fixed_count += 1
            else:
                print(f"DEBUG: No connection found for {u1}-{u2}")
                
        if fixed_count > 0:
            db.session.commit()
            print(f"\nSUCCESS: Fixed {fixed_count} connections.")
        else:
            print("\nNo expired connections found to fix.")

if __name__ == "__main__":
    fix_inconsistent_connections()
