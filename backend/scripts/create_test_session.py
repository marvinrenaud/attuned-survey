import sys
import os
from pathlib import Path
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from backend.src.main import app, db
from backend.src.models.session import Session

def create_session():
    with app.app_context():
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            players=[
                {"id": "p1", "name": "Alice", "anatomy": ["vagina"]},
                {"id": "p2", "name": "Bob", "anatomy": ["penis"]}
            ],
            game_settings={
                "intimacy_level": 3,
                "player_order_mode": "SEQUENTIAL",
                "selection_mode": "MANUAL"
            },
            current_turn_state={
                "status": "WAITING_FOR_SELECTION",
                "primary_player_idx": 0,
                "step": 0
            },
            # Legacy fields required by constraints
            player_a_profile_id=1,
            player_b_profile_id=1
        )
        db.session.add(session)
        db.session.commit()
        print(f"SESSION_ID:{session_id}")

if __name__ == "__main__":
    create_session()
