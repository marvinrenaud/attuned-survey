import unittest
from unittest.mock import MagicMock, patch
import json
from flask import Flask
from backend.src.routes.gameplay import gameplay_bp
from backend.src.models.session import Session
from backend.src.models.user import User
from backend.src.models.activity import Activity
import sys

class TestGameplayEndpoints(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(gameplay_bp)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    @patch('backend.src.routes.gameplay.Session')
    @patch('backend.src.routes.gameplay.User')
    @patch('backend.src.routes.gameplay.db')
    def test_start_game(self, mock_db, mock_user, mock_session_cls):
        # Mock User
        mock_user_instance = MagicMock()
        mock_user_instance.id = "12345678-1234-5678-1234-567812345678"
        mock_user_instance.display_name = "Alice"
        mock_user_instance.get_anatomy_self_array.return_value = ["vagina"]
        mock_user_instance.subscription_tier = "free"
        mock_user_instance.daily_activity_count = 0
        mock_user_instance.daily_activity_reset_at = None # Fix datetime comparison
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        mock_user.query.get.return_value = mock_user_instance

        # Mock Session creation
        mock_session_instance = MagicMock()
        mock_session_instance.session_id = "sess_123"
        mock_session_cls.return_value = mock_session_instance

        payload = {
            "player_ids": ["12345678-1234-5678-1234-567812345678", "87654321-4321-8765-4321-876543218765"],
            "settings": {
                "intimacy_level": 3,
                "player_order_mode": "SEQUENTIAL",
                "selection_mode": "RANDOM"
            }
        }

        response = self.client.post('/api/game/start', json=payload)
        
        if response.status_code != 200:
            sys.stderr.write(f"Start Game Error: {response.get_json()}\n")
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['session_id'], "sess_123")
        self.assertEqual(data['current_turn']['status'], "SHOW_CARD")
        
        # Verify Session was created with correct players
        args, kwargs = mock_session_cls.call_args
        self.assertEqual(len(kwargs['players']), 2)
        self.assertEqual(kwargs['players'][0]['name'], "Alice")

    @patch('backend.src.routes.gameplay.Session')
    @patch('backend.src.routes.gameplay.Activity')
    @patch('backend.src.routes.gameplay.db')
    def test_next_turn_random(self, mock_db, mock_activity, mock_session_cls):
        # Mock Session
        mock_session = MagicMock()
        mock_session.session_id = "sess_123"
        mock_session.players = [
            {"id": "u1", "name": "Alice", "anatomy": ["vagina"]},
            {"id": "u2", "name": "Bob", "anatomy": ["penis"]}
        ]
        mock_session.game_settings = {"player_order_mode": "SEQUENTIAL", "selection_mode": "RANDOM"}
        mock_session.current_turn_state = {"status": "SHOW_CARD", "primary_player_idx": 0, "step": 1}
        mock_session_cls.query.get.return_value = mock_session

        # Mock Activity
        mock_activity_instance = MagicMock()
        mock_activity_instance.id = "act_1"
        mock_activity_instance.description = "Kiss your partner."
        mock_activity_instance.intensity = 1
        mock_activity.query.filter_by.return_value.order_by.return_value.first.return_value = mock_activity_instance

        # Mock db.func.random
        mock_db.func.random.return_value = "RANDOM"

        payload = {"action": "NEXT"}
        response = self.client.post('/api/game/sess_123/next', json=payload)

        if response.status_code != 200:
            sys.stderr.write(f"Next Turn Error: {response.get_json()}\n")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify rotation: Alice (0) -> Bob (1)
        # Primary should be Bob
        self.assertEqual(data['current_turn']['card']['primary_player'], "Bob")
        self.assertEqual(data['current_turn']['card']['secondary_players'][0], "Alice")
        
        # Verify text resolution
        self.assertEqual(data['current_turn']['card']['display_text'], "Kiss Alice.")
        
        # Verify progress
        self.assertEqual(data['progress']['current_step'], 2)

    @patch('backend.src.routes.gameplay.Session')
    @patch('backend.src.routes.gameplay.db')
    def test_next_turn_manual_waiting(self, mock_db, mock_session_cls):
        # Mock Session
        mock_session = MagicMock()
        mock_session.session_id = "sess_123" # Fix missing session_id
        mock_session.players = [{"name": "Alice"}, {"name": "Bob"}]
        mock_session.game_settings = {"selection_mode": "MANUAL", "player_order_mode": "SEQUENTIAL"}
        mock_session.current_turn_state = {"status": "SHOW_CARD", "primary_player_idx": 0, "step": 1}
        mock_session_cls.query.get.return_value = mock_session

        payload = {"action": "NEXT"} # No selected_type
        response = self.client.post('/api/game/sess_123/next', json=payload)

        if response.status_code != 200:
            sys.stderr.write(f"Manual Waiting Error: {response.get_json()}\n")

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Should transition to WAITING_FOR_SELECTION
        self.assertEqual(data['current_turn']['status'], "WAITING_FOR_SELECTION")
        # Primary should rotate to Bob
        self.assertEqual(data['current_turn']['primary_player']['name'], "Bob")

if __name__ == '__main__':
    unittest.main()
