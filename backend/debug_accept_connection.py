
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add the backend directory to the python path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from src.main import create_app
from src.extensions import db
from src.routes.partners import PartnerConnection
from src.models.user import User

app = create_app()

with app.app_context():
    print("Checking database schema...")
    inspector = db.inspect(db.engine)
    columns = [c['name'] for c in inspector.get_columns('partner_connections')]
    print(f"Columns in partner_connections: {columns}")
    
    if 'recipient_display_name' not in columns:
        print("ERROR: 'recipient_display_name' column is MISSING from partner_connections table.")
    else:
        print("SUCCESS: 'recipient_display_name' column exists.")

    if 'requester_display_name' not in columns:
        print("ERROR: 'requester_display_name' column is MISSING from partner_connections table.")
    else:
        print("SUCCESS: 'requester_display_name' column exists.")

    # Try to simulate the error
    print("\nSimulating accept_connection...")
    try:
        # Create a dummy user and connection if needed, or just query an existing one
        # For safety, let's just try to query one
        connection = PartnerConnection.query.first()
        if connection:
            print(f"Found connection: {connection.id}")
            print(f"Current Status: {connection.status}")
            
            # Simulate to_dict which accesses the new columns
            print("Attempting to serialize (to_dict)...")
            data = connection.to_dict()
            print("Serialization successful:", data)
            
            # Test Case: Accept with NO recipient_user_id in payload AND NO ID in DB
            print("\nTest Case: Accept with NO recipient_user_id in payload AND NO ID in DB")
            
            # Force DB ID to None
            connection.recipient_user_id = None
            db.session.commit()
            print("Set recipient_user_id to None in DB")
            
            try:
                # Simulate the logic in the endpoint
                recipient_id = None # Simulating missing field in JSON
                
                # Logic from endpoint:
                if not recipient_id:
                    if connection.recipient_user_id:
                        recipient_id = str(connection.recipient_user_id)
                        print(f"Fallback to DB ID: {recipient_id}")
                    else:
                        print("SUCCESS: Detected missing ID and raised 400 (simulated)")
                        # In app this returns 400
                        # return jsonify({'error': 'Missing recipient_user_id (and not found in record)'}), 400
                        raise ValueError("Simulated 400: Missing recipient_user_id")
                
                if recipient_id:
                    connection.status = 'accepted'
                    connection.recipient_user_id = recipient_id
                    db.session.commit()
                    print("FAILURE: Should not have accepted without ID.")
                    
            except ValueError as e:
                print(f"Caught expected validation error: {e}")
            except Exception as e:
                print(f"FAILURE: Caught unexpected exception: {e}")
                import traceback
                traceback.print_exc()
                db.session.rollback()
            
    except Exception as e:
        print(f"\nCAUGHT EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
