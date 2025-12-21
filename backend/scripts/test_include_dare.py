import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask
from backend.src.routes.gameplay import gameplay_bp
from backend.src.models.session import Session
from backend.src.extensions import db
from backend.src.main import create_app

def test_include_dare_string():
    app = create_app()
    
    with app.app_context():
        client = app.test_client()
        
        # Send "false" as a string
        start_payload = {
            "player_ids": ["anon1", "anon2"],
            "settings": {
                "intimacy_level": 3,
                "player_order_mode": "SEQUENTIAL",
                "selection_mode": "RANDOM",
                "include_dare": "false" # <--- String "false"
            }
        }
        
        print("--- Starting Game (include_dare='false') ---")
        # We need to force a DARE to see if it gets converted to TRUTH
        # But we can't easily force random choice.
        # However, we can check the stored setting.
        
        res = client.post('/api/game/start', json=start_payload)
        
        if res.status_code != 200:
            print(f"Start failed: {res.get_json()}")
            return
            
        data = res.get_json()
        session_id = data['session_id']
        print(f"Session ID: {session_id}")
        
        # Check stored session settings
        session = Session.query.get(session_id)
        stored_val = session.game_settings.get('include_dare')
        print(f"Stored include_dare: {stored_val} (Type: {type(stored_val)})")
        
        # Manually invoke _advance_turn logic check
        # Logic is: if activity_type == "dare" and not settings.get("include_dare", True):
        # If stored_val is "false", not "false" is False.
        # So if we pick DARE, it will NOT be converted to TRUTH.
        
        if stored_val == "false":
            print("FAILURE: 'false' string stored directly. This will cause logic errors (non-empty string is Truthy).")
        elif stored_val is False:
            print("SUCCESS: 'false' string converted to boolean False.")
        else:
            print(f"Unexpected value: {stored_val}")

if __name__ == "__main__":
    test_include_dare_string()
