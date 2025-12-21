import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask
from backend.src.routes.gameplay import gameplay_bp
from backend.src.models.session import Session
from backend.src.models.user import User
from backend.src.models.activity import Activity
from backend.src.extensions import db
from backend.src.main import create_app

def test_random_mode():
    app = create_app()
    
    with app.app_context():
        # 1. Create a session with RANDOM mode
        client = app.test_client()
        
        start_payload = {
            "player_ids": ["anon1", "anon2"],
            "settings": {
                "intimacy_level": 3,
                "player_order_mode": "SEQUENTIAL",
                "selection_mode": "RANDOM",  # <--- Crucial
                "include_dare": True
            }
        }
        
        print("--- Starting Game (RANDOM Mode) ---")
        res = client.post('/api/game/start', json=start_payload)
        if res.status_code != 200:
            print(f"Start failed: {res.get_json()}")
            return
            
        session_id = res.get_json()['session_id']
        print(f"Session ID: {session_id}")
        
        # 2. Call Next without selected_type
        print("\n--- Calling Next (No Type) ---")
        next_payload = {"action": "NEXT"}
        res = client.post(f'/api/game/{session_id}/next', json=next_payload)
        
        data = res.get_json()
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            status = data.get('current_turn', {}).get('status')
            print(f"Current Turn Status: {status}")
            
            if status == "SHOW_CARD":
                print("SUCCESS: Random mode auto-selected a card.")
                print(f"Card Text: {data.get('current_turn', {}).get('card', {}).get('display_text')}")
            elif status == "WAITING_FOR_SELECTION":
                print("FAILURE: Random mode returned WAITING_FOR_SELECTION.")
            else:
                print(f"Unexpected status: {status}")
        else:
            print(f"Next failed: {data}")

if __name__ == "__main__":
    test_random_mode()
