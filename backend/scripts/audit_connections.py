
import sys
import os

# Ensure backend src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.main import create_app, db
from src.routes.partners import PartnerConnection, RememberedPartner
from src.models.user import User
from sqlalchemy import text

def audit_connections():
    app = create_app()
    with app.app_context():
        print("--- STARTING CONNECTION AUDIT ---\n")
        
        # 1. Fetch all Remembered Relationships (A -> B)
        # Group by pair to avoid duplicates
        rps = RememberedPartner.query.all()
        print(f"Total RememberedPartner entries: {len(rps)}")
        
        inconsistent_count = 0
        
        checked_pairs = set()
        
        for rp in rps:
            u1 = str(rp.user_id)
            u2 = str(rp.partner_user_id)
            
            # Sort to check connection regardless of direction
            pair_key = tuple(sorted([u1, u2]))
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)
            
            # Find Connection
            conn = PartnerConnection.query.filter(
                ((PartnerConnection.requester_user_id == u1) & (PartnerConnection.recipient_user_id == u2)) |
                ((PartnerConnection.requester_user_id == u2) & (PartnerConnection.recipient_user_id == u1))
            ).order_by(PartnerConnection.created_at.desc()).first()
            
            if not conn:
                print(f"[MISSING] Pair {u1} <=> {u2} has RememberedPartner but NO connection record!")
                inconsistent_count += 1
            elif conn.status != 'accepted':
                print(f"[MISMATCH] Pair {u1} <=> {u2} has RememberedPartner but Connection {conn.id} is '{conn.status}'!")
                print(f"           Request: {conn.requester_user_id} -> {conn.recipient_email} (User: {conn.recipient_user_id})")
                print(f"           Created: {conn.created_at}, Expired: {conn.expires_at}")
                inconsistent_count += 1
                
                # Check users existence specifically for the reported pair
                if u1 == "9e8ee659-ec2a-4f41-8ce3-0eb81b380fd3" or u2 == "9e8ee659-ec2a-4f41-8ce3-0eb81b380fd3":
                    print("  -> DEBUG: Checking Reported User ID 9e8ee659-ec2a-4f41-8ce3-0eb81b380fd3")
                    u_chk = db.session.execute(text("SELECT id, email FROM users WHERE id = '9e8ee659-ec2a-4f41-8ce3-0eb81b380fd3'")).fetchone()
                    print(f"  -> User 9e8ee659 exists in DB? {u_chk}")

        print("\n--- AUDIT COMPLETE ---")
        print(f"Inconsistent Pairs Found: {inconsistent_count}")

if __name__ == "__main__":
    audit_connections()
