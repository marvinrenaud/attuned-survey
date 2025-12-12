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
    if user.daily_activity_reset_at and user.daily_activity_reset_at < datetime.now(timezone.utc):
        # This logic should ideally be in a central service or model method
        # But for now we rely on the subscription route logic or duplicate it here
        # Actually, let's just check the count vs limit. 
        # The reset logic is in subscriptions.py. 
        # We should probably call a shared service, but for MVP we'll just check.
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
    user = User.query.get(user_id)
    if user and user.subscription_tier != 'premium':
        user.daily_activity_count += 1
        db.session.commit()

def _advance_turn(session: Session, selected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Advance the session to the next turn.
    Handles step increment, player rotation, activity selection, and state update.
    Returns the response dictionary.
    """
    settings = session.game_settings or {}
    players = session.players or []
    state = session.current_turn_state or {}
    
    # 1. Increment Step
    current_step = state.get("step", 0) + 1
    
    # Infinite Loop Logic
    # Effective step for intensity calculation (1-25)
    effective_step = (current_step - 1) % 25 + 1
    
    # 2. Player Rotation
    current_idx = state.get("primary_player_idx", -1)
    primary_idx, secondary_idx = _get_next_player_indices(
        current_idx, len(players), settings.get("player_order_mode", "SEQUENTIAL")
    )
    
    primary_player = players[primary_idx]
    secondary_player = players[secondary_idx]
    
    # 3. Activity Selection
    # If MANUAL and we just finished a card (no selected_type provided), 
    # we stop and ask for selection.
    if settings.get("selection_mode") == "MANUAL" and not selected_type:
        # Transition to WAITING state
        new_state = {
            "status": "WAITING_FOR_SELECTION",
            "primary_player_idx": primary_idx,
            "step": current_step
        }
        session.current_turn_state = new_state
        flag_modified(session, "current_turn_state")
        db.session.commit()
        
        return {
            "session_id": session.session_id,
            "current_turn": {
                "status": "WAITING_FOR_SELECTION",
                "primary_player": primary_player
            }
        }

    # Generate Card (RANDOM mode or MANUAL+SELECTED)
    activity_type = selected_type if selected_type else random.choice(["truth", "dare"])
    if activity_type.lower() == "dare" and not settings.get("include_dare", True):
        activity_type = "truth"
        
    # Get Intensity
    intimacy_level = settings.get("intimacy_level", 3)
    rating = 'R'
    if intimacy_level <= 2: rating = 'G'
    elif intimacy_level >= 5: rating = 'X'
    
    intensity_min, intensity_max = get_intensity_window(effective_step, 25, rating)
    
    # Find Activity
    # HACK: Direct DB query for MVP speed. 
    # In production, use repository.find_best_activity_candidate
    candidate = Activity.query.filter_by(
        type=activity_type.lower(),
        rating=rating
    ).order_by(db.func.random()).first()
    
    if not candidate:
        # Fallback
        candidate = Activity(
            script={"steps": [{"actor": "A", "do": "Tell your partner something you love about them."}]},
            type="truth",
            intensity=1
        )
        
    # 4. Text Resolution
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
    
    # 5. Update State
    new_state = {
        "status": "SHOW_CARD",
        "primary_player_idx": primary_idx,
        "step": current_step,
        "card_id": str(candidate.id) if hasattr(candidate, 'id') else "fallback"
    }
    session.current_turn_state = new_state
    flag_modified(session, "current_turn_state")
    
    db.session.commit()
    
    # Response
    phase = get_phase_name(effective_step, 25)
    
    return {
        "session_id": session.session_id,
        "progress": {
            "current_step": current_step,
            "total_steps": 25,
            "intensity_phase": phase.capitalize()
        },
        "current_turn": {
            "status": "SHOW_CARD",
            "card": {
                "card_id": str(candidate.id) if hasattr(candidate, 'id') else "fallback",
                "type": activity_type.upper(),
                "primary_player": primary_player["name"],
                "secondary_players": [secondary_player["name"]],
                "display_text": resolved_text,
                "intensity_rating": candidate.intensity
            }
        }
    }

# --- Routes ---

@gameplay_bp.route("/start", methods=["POST"])
def start_game():
    """
    Start a new game session.
    
    Payload:
    {
        "player_ids": ["uuid1", "uuid2"], (or anonymous objects)
        "settings": {
            "intimacy_level": 1-5,
            "player_order_mode": "SEQUENTIAL" | "RANDOM",
            "selection_mode": "RANDOM" | "MANUAL",
            "include_dare": true/false
        }
    }
    """
    try:
        data = request.get_json()
        player_ids = data.get("player_ids", [])
        settings = data.get("settings", {})
        
        # Normalize settings to uppercase
        if "selection_mode" in settings:
            settings["selection_mode"] = settings["selection_mode"].upper()
        if "player_order_mode" in settings:
            settings["player_order_mode"] = settings["player_order_mode"].upper()
            
        # Normalize boolean settings
        if "include_dare" in settings:
            val = settings["include_dare"]
            if isinstance(val, str):
                settings["include_dare"] = val.lower() == "true"
        
        # Basic validation
        if not player_ids:
            return jsonify({"error": "No players provided"}), 400
            
        # Check limit for the requesting user (assuming first player is owner/requester)
        # In a real app, we'd use the auth token user_id.
        # For now, we'll check the first player if they are a registered user.
        # If anonymous, we might skip or use IP-based? MVP: Skip check for anon.
        limit_status = {"limit_reached": False}
        owner_id = None
        
        # Resolve players (Mocking resolution for now, assuming IDs are passed)
        # In reality, we'd fetch User objects or use provided anonymous data.
        players = []
        for pid in player_ids:
            # Try to find user
            user = User.query.filter_by(id=pid).first() if len(pid) > 10 else None # Simple UUID check
            if user:
                if not owner_id: owner_id = user.id
                players.append({
                    "id": str(user.id),
                    "name": user.display_name or "Player",
                    "anatomy": user.get_anatomy_self_array()
                })
            else:
                # Anonymous / Mock
                players.append({
                    "id": pid,
                    "name": f"Player {pid[:4]}",
                    "anatomy": ["penis"] # Default fallback
                })
        
        if owner_id:
            limit_status = _check_daily_limit(owner_id)
            if limit_status["limit_reached"]:
                return jsonify({
                    "error": "Daily limit reached",
                    "limit_status": limit_status
                }), 403

        # Create Session
        session = Session(
            players=players,
            game_settings=settings,
            current_turn_state={
                "status": "INIT",
                "primary_player_idx": -1, # Will increment to 0 on first turn
                "step": 0
            },
            # Legacy fields required by DB constraint (using dummy IDs or first player)
            # We need to handle the foreign keys if we want to be strict.
            # For this MVP refactor, we might need to relax constraints or use dummy profiles.
            # Assuming we can use nullable fields if we updated the model, 
            # but the model has nullable=False for player_a_profile_id.
            # We might need to fetch/create dummy profiles for legacy compat.
            # For now, let's assume we can pass 0 or 1 if constraints allow, 
            # or we need to actually find profiles.
            # HACK: Use existing profile IDs if possible, or 1.
            player_a_profile_id=1, 
            player_b_profile_id=1
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Initial Response
        response = {
            "session_id": session.session_id,
            "limit_status": limit_status,
            "current_turn": {
                "status": "WAITING_FOR_SELECTION" if settings.get("selection_mode") == "MANUAL" else "SHOW_CARD",
            }
        }
        
        if settings.get("selection_mode") == "RANDOM":
            # Auto-trigger first turn to avoid "Skipped Turn" bug
            response = _advance_turn(session)
            # Add limit status back to response
            response["limit_status"] = limit_status
            
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Start game failed: {str(e)}")
        return jsonify({"error": str(e)}), 500

@gameplay_bp.route("/<session_id>/next", methods=["POST"])
def next_turn(session_id):
    """
    Advance to next turn.
    
    Payload:
    {
        "action": "NEXT" | "SKIP",
        "selected_type": "TRUTH" | "DARE" (Optional)
    }
    """
    start_time = time.time()
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
            
        data = request.get_json()
        action = data.get("action", "NEXT")
        selected_type = data.get("selected_type")
        
        # Normalize selected_type
        if selected_type == "null":
            selected_type = None
        
        # Determine Flow
        response = _advance_turn(session, selected_type)
        
        # Add limit status
        # Assuming first player is owner/requester as in start_game
        players = session.players or []
        if players:
            owner_id = players[0].get("id")
            # Check if it's a valid UUID (not anonymous)
            if len(owner_id) > 10:
                limit_status = _check_daily_limit(owner_id)
                response["limit_status"] = limit_status
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Next turn failed: {str(e)}")
        return jsonify({"error": str(e)}), 500
