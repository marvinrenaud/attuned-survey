
import sys
import os
from datetime import datetime

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.routes.partners import PartnerConnection

app = create_app()

def debug_expiry():
    with app.app_context():
        print(f"Current Server Time (UTC): {datetime.utcnow()}")
        
        # Get recent connections
        connections = PartnerConnection.query.order_by(PartnerConnection.created_at.desc()).limit(5).all()
        
        print("\nRecent Connections:")
        for conn in connections:
            print(f"ID: {conn.id}")
            print(f"  Status: {conn.status}")
            print(f"  Created At: {conn.created_at}")
            print(f"  Expires At: {conn.expires_at}")
            
            # Check expiry logic
            expires_at = conn.expires_at
            if expires_at.tzinfo:
                print(f"  (Aware datetime detected, converting to naive)")
                expires_at = expires_at.replace(tzinfo=None)
            
            time_left = expires_at - datetime.utcnow()
            print(f"  Time Left: {time_left}")
            
            if expires_at < datetime.utcnow():
                print("  -> EXPIRED")
            else:
                print("  -> VALID")
            print("-" * 30)

if __name__ == "__main__":
    debug_expiry()
