import unittest
from unittest.mock import MagicMock, patch
import json
from flask import Flask
from backend.src.routes.gameplay import gameplay_bp
from backend.src.models.session import Session
from backend.src.models.user import User
from backend.src.models.activity import Activity
import sys

class TestBatchGameplay(unittest.TestCase):
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
    @patch('backend.src.routes.gameplay.Activity')
    @patch('backend.src.routes.gameplay.db')
    def test_start_game_batch(self, mock_db, mock_activity, mock_user, mock_session_cls):
        # Mock User
        mock_user_instance = MagicMock()
        mock_user_instance.id = "12345678-1234-5678-1234-567812345678"
        mock_user_instance.display_name = "Alice"
        mock_user_instance.get_anatomy_self_array.return_value = ["vagina"]
        mock_user_instance.subscription_tier = "free"
        mock_user_instance.daily_activity_count = 0
        mock_user_instance.daily_activity_reset_at = None 
        mock_user.query.filter_by.return_value.first.return_value = mock_user_instance
        mock_user.query.get.return_value = mock_user_instance

        # Mock Session
        mock_session_instance = MagicMock()
        mock_session_instance.session_id = "sess_123"
        mock_session_instance.players = [{"id": "u1", "name": "Alice"}]
        mock_session_instance.game_settings = {"player_order_mode": "SEQUENTIAL"}
        # Initial empty state
        mock_session_instance.current_turn_state = {"queue": []}
        mock_session_cls.return_value = mock_session_instance

        # Mock Activity
        mock_activity_instance = MagicMock()
        mock_activity_instance.activity_id = 101
        mock_activity_instance.script = {"steps": [{"actor": "A", "do": "Action"}]}
        mock_activity_instance.intensity = 1
        mock_activity.query.filter_by.return_value.order_by.return_value.first.return_value = mock_activity_instance
        
        mock_db.func.random.return_value = "RANDOM"

        payload = {
            "player_ids": ["12345678-1234-5678-1234-567812345678", "anon2"],
            "settings": {"selection_mode": "RANDOM"}
        }

        response = self.client.post('/api/game/start', json=payload)
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify Queue
        self.assertIn("queue", data)
        self.assertEqual(len(data["queue"]), 3)
        self.assertEqual(data["queue"][0]["card_id"], "101")
        
        # Verify Credit Consumption (Should be 1)
        # We can't easily check the mock call count for increment because it's a helper,
        # but we can check if daily_activity_count was incremented on the mock user object
        # if the helper modifies it.
        # The helper calls: user.daily_activity_count += 1
        self.assertEqual(mock_user_instance.daily_activity_count, 1)

    @patch('backend.src.routes.gameplay.Session')
    @patch('backend.src.routes.gameplay.User')
    @patch('backend.src.routes.gameplay.Activity')
    @patch('backend.src.routes.gameplay.db')
    def test_next_turn_replenish(self, mock_db, mock_activity, mock_user, mock_session_cls):
        # Mock User
        mock_user_instance = MagicMock()
        mock_user_instance.id = "12345678-1234-5678-1234-567812345678"
        mock_user_instance.subscription_tier = "free"
        mock_user_instance.daily_activity_count = 5
        mock_user_instance.daily_activity_reset_at = None
        mock_user.query.get.return_value = mock_user_instance

        # Mock Session with existing queue of 3
        mock_session = MagicMock()
        mock_session.session_id = "sess_123"
        mock_session.players = [{"id": "12345678-1234-5678-1234-567812345678", "name": "Alice"}]
        mock_session.game_settings = {"player_order_mode": "SEQUENTIAL"}
        
        # Queue has 3 items: A, B, C
        initial_queue = [
            {"card_id": "A", "step": 1, "status": "SHOW_CARD", "primary_player_idx": 0},
            {"card_id": "B", "step": 2, "status": "SHOW_CARD", "primary_player_idx": 1},
            {"card_id": "C", "step": 3, "status": "SHOW_CARD", "primary_player_idx": 0}
        ]
        mock_session.current_turn_state = {"queue": list(initial_queue)} # Copy
        mock_session_cls.query.get.return_value = mock_session

        # Mock Activity for new generation
        mock_activity_instance = MagicMock()
        mock_activity_instance.activity_id = 104 # New ID
        mock_activity_instance.script = {"steps": [{"actor": "A", "do": "Action"}]}
        mock_activity_instance.intensity = 1
        mock_activity.query.filter_by.return_value.order_by.return_value.first.return_value = mock_activity_instance

        response = self.client.post('/api/game/sess_123/next', json={"action": "NEXT"})
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        # Verify Queue
        # Should have removed A, kept B, C, and added D (104)
        queue = data["queue"]
        self.assertEqual(len(queue), 3)
        self.assertEqual(queue[0]["card_id"], "B")
        self.assertEqual(queue[1]["card_id"], "C")
        self.assertEqual(queue[2]["card_id"], "104")
        
        # Verify Credit Consumption
        # Should increment by 1
        self.assertEqual(mock_user_instance.daily_activity_count, 6)

if __name__ == '__main__':
    unittest.main()
