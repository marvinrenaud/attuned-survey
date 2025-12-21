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

def test_null_type():
    app = create_app()
    
    with app.app_context():
        client = app.test_client()
        
        # Start Game
        start_payload = {
            "player_ids": ["anon1", "anon2"],
            "settings": {
                "intimacy_level": 3,
                "player_order_mode": "SEQUENTIAL",
                "selection_mode": "RANDOM",
                "include_dare": True
            }
        }
        
        print("--- Starting Game ---")
        res = client.post('/api/game/start', json=start_payload)
        session_id = res.get_json()['session_id']
        
        # Case 1: selected_type is None (JSON null)
        print("\n--- Calling Next (selected_type: None) ---")
        next_payload = {"action": "NEXT", "selected_type": None}
        res = client.post(f'/api/game/{session_id}/next', json=next_payload)
        data = res.get_json()
        card_type = data['current_turn']['card']['type']
        print(f"Result Type: {card_type}")
        
        # Case 2: selected_type is "null" (String)
        print("\n--- Calling Next (selected_type: 'null') ---")
        next_payload = {"action": "NEXT", "selected_type": "null"}
        res = client.post(f'/api/game/{session_id}/next', json=next_payload)
        data = res.get_json()
        card_type = data['current_turn']['card']['type']
        print(f"Result Type: {card_type}")
        
        if card_type == "NULL":
            print("CONFIRMED: Sending string 'null' results in type 'NULL'.")

if __name__ == "__main__":
    test_null_type()
