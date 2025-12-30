"""
Gameplay routes for Just-in-Time architecture.
Handles session creation, player rotation, and activity selection.
"""
import logging
import uuid
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy.orm.attributes import flag_modified

from ..extensions import db
from ..models.session import Session
from ..models.user import User
from ..models.activity import Activity
from ..db import repository
from ..recommender.picker import get_intensity_window, get_phase_name
from ..game.text_resolver import resolve_activity_text

logger = logging.getLogger(__name__)

gameplay_bp = Blueprint("gameplay", __name__, url_prefix="/api/game")

# --- Helper Functions ---

def _get_next_player_indices(current_idx: int, num_players: int, mode: str) -> tuple[int, int]:
    """
    Calculate primary and secondary player indices.
    Returns (primary_idx, secondary_idx).
    """
    if mode == 'RANDOM':
        primary = random.randint(0, num_players - 1)
    else:  # SEQUENTIAL
        primary = (current_idx + 1) % num_players
        
    # Secondary is the next person in the circle (simplified logic)
    # In a 2-player game, it's always the other person.
    # In N-player, we default to "next person" for simplicity, 
    # but could be random or chosen if we wanted more complexity.
    secondary = (primary + 1) % num_players
    
    return primary, secondary

def _check_daily_limit(user_id: str) -> dict:
    """Check if user has reached daily limit (Free tier only)."""
    # Ensure ID is UUID
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return {"error": "Invalid User ID"}

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}
        
    if user.subscription_tier == 'premium':
        return {
            "limit_reached": False,
            "remaining": -1,
            "is_capped": False
        }
        
    # Reset if needed
    if user.daily_activity_reset_at:
        reset_at = user.daily_activity_reset_at
        if reset_at.tzinfo is None:
             reset_at = reset_at.replace(tzinfo=timezone.utc)
             
        if reset_at < datetime.now(timezone.utc):
            # This logic should ideally be in a central service or model method
            # But for now we rely on the subscription route logic or duplicate it here
            pass
        
    limit = 25
    return {
        "limit_reached": user.daily_activity_count >= limit,
        "remaining": max(0, limit - user.daily_activity_count),
        "is_capped": True,
        "used": user.daily_activity_count,
        "limit": limit
    }

def _increment_daily_count(user_id: str):
    """Increment daily count for free users."""
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return

    user = User.query.get(user_id)
    if user and user.subscription_tier != 'premium':
        user.daily_activity_count += 1
        db.session.commit()

def _generate_turn_data(session: Session, step_offset: int = 0, selected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate data for a single turn without committing to DB.
    Used for batch generation.
    """
    settings = session.game_settings or {}
    players = session.players or []
    state = session.current_turn_state or {}
    
    # Calculate Step
    # If we are generating ahead, we need to know the base step + offset
    # Current step in DB is the *last committed* step.
    # If queue is empty, next step is current_step + 1.
    # If queue has N items, next step is current_step + 1 + N.
    # But here we just take an offset.
    
    # We need to know the "current" state to calculate rotation.
    # This is tricky for batching because we need to simulate the state evolution.
    # For MVP, let's assume we can calculate based on (current_step + offset).
    
    base_step = state.get("step", 0)
    # If the queue exists, the "effective" current step for generation is 
    # the step of the last item in the queue.
    queue = state.get("queue", [])
    if queue and step_offset == 0:
        # If we are just appending, we start from the end of the queue
        last_item = queue[-1]
        base_step = last_item.get("step", base_step)
    
    target_step = base_step + 1 + step_offset
    
    # Infinite Loop Logic
    effective_step = (target_step - 1) % 25 + 1
    
    # Player Rotation
    # We need to calculate rotation based on the step number.
    # If SEQUENTIAL: index = (step - 1) % num_players
    # If RANDOM: we just pick random.
    
    num_players = len(players)
    if num_players == 0:
        return {} # Should not happen
        
    if settings.get("player_order_mode") == "SEQUENTIAL":
        # 0-based index for step 1 is 0.
        primary_idx = (target_step - 1) % num_players
    else:
        # RANDOM
        primary_idx = random.randint(0, num_players - 1)
        
    secondary_idx = (primary_idx + 1) % num_players
    
    primary_player = players[primary_idx]
    secondary_player = players[secondary_idx]
    
    # Activity Selection
    activity_type = selected_type if selected_type else random.choice(["truth", "dare"])
    if activity_type.lower() == "dare" and not settings.get("include_dare", True):
        activity_type = "truth"
        
    # Intensity
    intimacy_level = settings.get("intimacy_level", 3)
    rating = 'R'
    if intimacy_level <= 2: rating = 'G'
    elif intimacy_level >= 5: rating = 'X'
    
    intensity_min, intensity_max = get_intensity_window(effective_step, 25, rating)
    
    # Find Activity
    candidate = Activity.query.filter_by(
        type=activity_type.lower(),
        rating=rating
    ).order_by(db.func.random()).first()
    
    if not candidate:
        candidate = Activity(
            script={"steps": [{"actor": "A", "do": "Tell your partner something you love about them."}]},
            type="truth",
            intensity=1
        )
        # Mock ID for fallback if needed, or handle in response
        
    # Text Resolution
    try:
        script = candidate.script
        if not script or 'steps' not in script or not script['steps']:
            raise ValueError("Activity script is missing or empty")
        activity_text = script['steps'][0].get('do', "Perform the activity.")
    except Exception as e:
        logger.error(f"Failed to extract activity text: {e}")
        activity_text = "Perform a mystery activity with your partner."
        
    resolved_text = resolve_activity_text(
        activity_text,
        primary_player["name"],
        secondary_player["name"]
    )
    
    # Return Turn Object (not full response)
    return {
        "status": "SHOW_CARD",
        "primary_player_idx": primary_idx,
        "step": target_step,
        "card_id": str(candidate.activity_id) if hasattr(candidate, 'activity_id') else "fallback",
        "card": {
            "card_id": str(candidate.activity_id) if hasattr(candidate, 'activity_id') else "fallback",
            "type": activity_type.upper(),
            "primary_player": primary_player["name"],
            "secondary_players": [secondary_player["name"]],
            "display_text": resolved_text,
            "intensity_rating": candidate.intensity
        },
        "progress": {
            "current_step": target_step,
            "total_steps": 25,
            "intensity_phase": get_phase_name(effective_step, 25).capitalize()
        }
    }

def _generate_limit_card() -> Dict[str, Any]:
    """Generate a barrier card for when daily limit is reached."""
    return {
        "status": "SHOW_CARD",
        "primary_player_idx": -1,
        "step": 999, # Dummy step
        "card_id": f"limit-barrier-{uuid.uuid4()}",
        "card": {
            "card_id": f"limit-barrier-{uuid.uuid4()}",
            "type": "LIMIT_REACHED",
            "primary_player": "System",
            "secondary_players": [],
            "display_text": "Daily limit reached. Tap to unlock unlimited turns.",
            "intensity_rating": 1
        },
        "progress": {
            "current_step": 999,
            "total_steps": 25,
            "intensity_phase": "Peak"
        }
    }

def _scrub_queue_for_limit(queue: List[Dict[str, Any]], keep_first: bool = True) -> List[Dict[str, Any]]:
    """
    Replace future cards in the queue with limit barriers if they are real.
    Used when the limit is reached but the buffer still contains real cards.
    
    Args:
        queue: The turn queue
        keep_first: If True, preserves the first card (assumed to be the one just paid for).
    """
    start_idx = 1 if keep_first else 0
    
    for i in range(start_idx, len(queue)):
        item = queue[i]
        # If it's not already a limit card, replace it
        if item.get('card', {}).get('type') != 'LIMIT_REACHED':
            # Generate replacement
            barrier = _generate_limit_card()
            # Preserve some flow data? No, barrier resets step usually.
            # But we might want to keep the sequence consistent?
            # _generate_limit_card uses step 999. That's fine.
            queue[i] = barrier
            
    return queue

def _fill_queue(session: Session, target_size: int = 3, owner_id: str = None) -> List[Dict[str, Any]]:
    """
    Ensure the session queue has `target_size` items.
    Updates session.current_turn_state but caller must commit.
    Returns the updated queue.
    """
    state = session.current_turn_state or {}
    queue = state.get("queue", [])
    
    # If queue is missing (migration), init it
    if queue is None: queue = []
    
    current_size = len(queue)
    if current_size >= target_size:
        return queue
        
    needed = target_size - current_size
    
    # Check limit status if owner known
    limit_reached = False
    if owner_id:
        status = _check_daily_limit(owner_id)
        limit_reached = status["limit_reached"]
    
    for _ in range(needed):
        if limit_reached:
            turn_data = _generate_limit_card()
        else:
            turn_data = _generate_turn_data(session)
            
        queue.append(turn_data)
        
    # Update State
    state["queue"] = queue
    
    if queue:
        head = queue[0]
        state["status"] = head["status"]
        state["primary_player_idx"] = head["primary_player_idx"]
        state["step"] = head["step"]
        state["card_id"] = head["card_id"]
        
    session.current_turn_state = state
    flag_modified(session, "current_turn_state")
    
    return queue

@gameplay_bp.route("/start", methods=["POST"])
def start_game():
    """
    Start a new game session.
    Returns a queue of 3 cards.
    """
    try:
        data = request.get_json()
        player_ids = data.get("player_ids", [])
        settings = data.get("settings", {})
        
        # ... (Normalization and Validation omitted for brevity, keeping existing) ...
        # Normalize settings
        if "selection_mode" in settings:
            settings["selection_mode"] = settings["selection_mode"].upper()
        if "player_order_mode" in settings:
            settings["player_order_mode"] = settings["player_order_mode"].upper()
        if "include_dare" in settings:
            val = settings["include_dare"]
            if isinstance(val, str):
                settings["include_dare"] = val.lower() == "true"
        
        # Basic validation
        if not player_ids:
            return jsonify({"error": "No players provided"}), 400
            
        # Check limit (1 credit for start)
        limit_status = {"limit_reached": False}
        owner_id = None
        
        # Resolve players
        players = []
        for pid in player_ids:
            # Cast to UUID for query
            user = None
            if len(pid) > 10:
                try:
                    pid_uuid = uuid.UUID(pid)
                    user = User.query.get(pid_uuid)
                except (ValueError, TypeError):
                    pass
            
            if user:
                if not owner_id: owner_id = str(user.id)
                players.append({
                    "id": str(user.id),
                    "name": user.display_name or "Player",
                    "anatomy": user.get_anatomy_self_array()
                })
            else:
                players.append({
                    "id": pid,
                    "name": f"Player {pid[:4]}",
                    "anatomy": ["penis"]
                })
        
        # INITIAL LIMIT CHECK
        if owner_id:
            limit_status = _check_daily_limit(owner_id)

        # Create Session
        session = Session(
            players=players,
            game_settings=settings,
            current_turn_state={
                "status": "INIT",
                "primary_player_idx": -1,
                "step": 0,
                "queue": [] # Init empty queue
            },
            player_a_profile_id=1, 
            player_b_profile_id=1
        )
        
        db.session.add(session)
        # Commit first to get session_id 
        db.session.commit()
        
        # Fill Queue (Batch of 3)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id)
        
        # Charge 1 Credit for the first card IF it isn't a limit card
        head_card = queue[0] if queue else {}
        if owner_id and head_card.get('card', {}).get('type') != 'LIMIT_REACHED':
            _increment_daily_count(owner_id)
            # Re-check limit status after increment
            limit_status = _check_daily_limit(owner_id)
            
            # SCRUBBER: If limit is now reached, ensure only the card we paid for (Head) is real.
            if limit_status.get("limit_reached"):
                queue = _scrub_queue_for_limit(queue, keep_first=True)
                # Update session state with scrubbed queue
                state = session.current_turn_state
                state["queue"] = queue
                session.current_turn_state = state
                flag_modified(session, "current_turn_state")
            
        db.session.commit()
        
        # Response
        return jsonify({
            "session_id": session.session_id,
            "limit_status": limit_status,
            "queue": queue, # Return full queue
            "current_turn": queue[0] if queue else {} # Legacy support / convenience
        }), 200

    except Exception as e:
        logger.error(f"Start game failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@gameplay_bp.route("/<session_id>/next", methods=["POST"])
def next_turn(session_id):
    """
    Advance to next turn.
    Consumes the played card, increments credit, replenishes queue.
    """
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
            
        data = request.get_json()
        
        state = session.current_turn_state or {}
        queue = state.get("queue", [])
        
        # Determine owner
        players = session.players or []
        owner_id = None
        if players:
            first_p = players[0].get("id")
            if len(first_p) > 10: 
                owner_id = first_p
        
        # 1. Consume the current card (Head of queue)
        if queue:
            last_card = queue.pop(0)
            state["queue"] = queue
            session.current_turn_state = state
            flag_modified(session, "current_turn_state")
            
            # Charge 1 Credit for the played card IF it wasn't a barrier card
            if owner_id and last_card.get('card', {}).get('type') != 'LIMIT_REACHED':
                _increment_daily_count(owner_id)
        
        # 2. Replenish Queue (Add 1 to end)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id)
        
        # SCRUBBER: Check limit and scrub buffer if needed
        limit_status = {}
        if owner_id:
            limit_status = _check_daily_limit(owner_id)
            if limit_status.get("limit_reached"):
                # If we strictly exceeded the limit (e.g. 26 > 25), block everything immediately.
                # If we strictly HIT the limit (25 == 25), allow the current card (which is the 25th).
                # Note: valid range is 0..25. 25 is the last allowed card.
                # If used=25. We allow queue[0] (C25). We scrub queue[1:] (C26+).
                # If used=26. We block queue[0].
                
                # Check usage
                used = limit_status.get("used", 0)
                limit = limit_status.get("limit", 25)
                
                keep_first = True
                if used > limit:
                     keep_first = False
                     
                queue = _scrub_queue_for_limit(queue, keep_first=keep_first)
                
                state["queue"] = queue
                session.current_turn_state = state
                flag_modified(session, "current_turn_state")
        
        db.session.commit()
        
        # 3. Response
        response = {
            "session_id": session.session_id,
            "limit_status": limit_status,
            "queue": queue,
            "current_turn": queue[0] if queue else {}
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Next turn failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
