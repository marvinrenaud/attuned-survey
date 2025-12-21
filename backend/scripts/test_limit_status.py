import sys
import os
from pathlib import Path
import json
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from flask import Flask
from backend.src.routes.gameplay import gameplay_bp
from backend.src.models.session import Session
from backend.src.models.user import User
from backend.src.extensions import db
from backend.src.main import create_app

def test_limit_status():
    app = create_app()
    
    with app.app_context():
        # Mock User to ensure we have a valid user for limit check
        with patch('backend.src.routes.gameplay.User') as mock_user_cls:
            mock_user = MagicMock()
            mock_user.id = "12345678-1234-5678-1234-567812345678"
            mock_user.subscription_tier = "free"
            mock_user.daily_activity_count = 5
            mock_user.daily_activity_reset_at = None
            mock_user_cls.query.get.return_value = mock_user
            
            client = app.test_client()
            
            # Start Game with valid user ID
            start_payload = {
                "player_ids": ["12345678-1234-5678-1234-567812345678", "anon2"],
                "settings": {
                    "intimacy_level": 3,
                    "player_order_mode": "SEQUENTIAL",
                    "selection_mode": "RANDOM",
                    "include_dare": True
                }
            }
            
            print("--- Starting Game ---")
            res = client.post('/api/game/start', json=start_payload)
            if res.status_code != 200:
                print(f"Start failed: {res.get_json()}")
                return
                
            data = res.get_json()
            session_id = data['session_id']
            print(f"Session ID: {session_id}")
            
            # Call Next
            print("\n--- Calling Next ---")
            next_payload = {"action": "NEXT"}
            res = client.post(f'/api/game/{session_id}/next', json=next_payload)
            
            data = res.get_json()
            print(f"Status Code: {res.status_code}")
            
            if "limit_status" in data:
                print("SUCCESS: limit_status found in response.")
                print(f"limit_status: {data['limit_status']}")
            else:
                print("FAILURE: limit_status missing from response.")
                print(f"Keys found: {list(data.keys())}")

if __name__ == "__main__":
    test_limit_status()
