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

def test_case_sensitivity():
    app = create_app()
    
    with app.app_context():
        client = app.test_client()
        
        # Send lowercase settings
        start_payload = {
            "player_ids": ["anon1", "anon2"],
            "settings": {
                "intimacy_level": 3,
                "player_order_mode": "sequential", # lowercase
                "selection_mode": "random",        # lowercase
                "include_dare": True
            }
        }
        
        print("--- Starting Game (Lowercase Settings) ---")
        res = client.post('/api/game/start', json=start_payload)
        
        if res.status_code != 200:
            print(f"Start failed: {res.get_json()}")
            return
            
        data = res.get_json()
        session_id = data['session_id']
        print(f"Session ID: {session_id}")
        
        # Verify that RANDOM mode logic triggered (should return a card)
        status = data.get('current_turn', {}).get('status')
        print(f"Current Turn Status: {status}")
        
        if status == "SHOW_CARD":
            print("SUCCESS: Lowercase 'random' was correctly normalized and triggered auto-selection.")
        else:
            print(f"FAILURE: Expected SHOW_CARD, got {status}")

        # Verify DB storage
        session = Session.query.get(session_id)
        print(f"Stored Selection Mode: {session.game_settings.get('selection_mode')}")
        
        if session.game_settings.get('selection_mode') == "RANDOM":
             print("SUCCESS: Settings stored as uppercase.")
        else:
             print("FAILURE: Settings not stored as uppercase.")

if __name__ == "__main__":
    test_case_sensitivity()
