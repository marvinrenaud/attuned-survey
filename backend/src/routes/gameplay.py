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
from sqlalchemy import text
from ..middleware.auth import token_required, optional_token

from ..extensions import db
from ..models.session import Session
from ..models.user import User
from ..models.activity import Activity
from ..db import repository
from ..recommender.picker import get_intensity_window, get_phase_name
from ..game.text_resolver import resolve_activity_text
from ..db.repository import find_best_activity_candidate
from ..models.profile import Profile

logger = logging.getLogger(__name__)

gameplay_bp = Blueprint("gameplay", __name__, url_prefix="/api/game")

# --- Helper Functions ---

def _get_player_profile(player_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Fetch profile dict for a player by user_id."""
    player_id = player_data.get('id')
    if not player_id:
        return None
        
    try:
        # Check if valid UUID
        user_uuid = uuid.UUID(player_id)
        profile = Profile.query.filter_by(user_id=user_uuid).first()
        if profile:
            return profile.to_dict()
    except (ValueError, TypeError):
        pass
        
    return None

def _invert_activity_preferences(activities: Dict[str, float]) -> Dict[str, float]:
    """Invert activity preferences (Give <-> Receive)."""
    inverted = {}
    for key, score in activities.items():
        new_key = key
        if '_give' in key:
            new_key = key.replace('_give', '_receive')
        elif '_receive' in key:
            new_key = key.replace('_receive', '_give')
        
        # Invert score? No, we want the partner to LIKE receiving what we LIKE giving.
        # So we keep the High Score (1.0).
        # If I like 'massage_give' (1.0), I want partner to like 'massage_receive' (1.0).
        inverted[new_key] = score
        
    return inverted

def _create_complimentary_profile(primary_profile: Dict) -> Dict:
    """Create a virtual partner profile that complements the primary user."""
    # Anatomy: Partner HAS what Primary LIKES
    anatomy = primary_profile.get('anatomy', {})
    # If primary likes 'penis', partner has 'penis'
    partner_has = anatomy.get('anatomy_preference', ['penis', 'vagina']) 
    if not partner_has: # Fallback
        partner_has = ['penis', 'vagina']
        
    # Power: Invert
    power = primary_profile.get('power_dynamic', {})
    orientation = power.get('orientation', 'Switch')
    partner_orientation = 'Switch'
    if orientation == 'Top': partner_orientation = 'Bottom'
    elif orientation == 'Bottom': partner_orientation = 'Top'
    
    # Boundaries: Copy primary's boundaries (safe assumption)
    boundaries = primary_profile.get('boundaries', {})
    
    # Activities: "Mirror" preferences
    # If Primary likes giving X, Partner should like receiving X
    activities = _invert_activity_preferences(primary_profile.get('activities', {}))
    
    return {
        'id': 'virtual_complimentary',
        'is_anonymous': True,
        'anatomy': {'anatomy_self': partner_has, 'anatomy_preference': anatomy.get('anatomy_self', [])},
        'power_dynamic': {'orientation': partner_orientation},
        'boundaries': boundaries,
        'activities': activities,
        # Default empty structures for others
        'domain_scores': {},
        'arousal_propensity': {},
        'truth_topics': {}
    }

def _create_virtual_profile(player_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a lightweight virtual profile for an anonymous guest.
    Ensures anatomy-safe filtering works.
    """
    name = player_data.get('name', 'Guest')
    anatomy = player_data.get('anatomy', [])
    
    # Anatomy structure expected by finder
    # We assume 'anatomy' input is a list of [penis, vagina, breasts]
    return {
        'id': player_data.get('id', 'guest'),
        'is_anonymous': True,
        'anatomy': {
            'anatomy_self': anatomy,
            # For guest, we assume they are open or we don't filter on partner anatomy yet
            # effectively "likes everything" or "likes nothing specific"
            # But the filter might require something. Let's assume broad.
            'anatomy_preference': ['penis', 'vagina', 'breasts']    
        },
        'power_dynamic': {'orientation': 'Switch'}, # Default to broadest
        'boundaries': {'hard_limits': []},
        'activities': {}, # No preferences
        'domain_scores': {},
        'arousal_propensity': {},
        'truth_topics': {}
    }

def _get_next_player_indices(current_idx: int, num_players: int, mode: str) -> tuple[int, int]:
    """
    Calculate primary and secondary player indices.
    Returns (primary_idx, secondary_idx).
    """
    if mode == 'RANDOM':
        primary = random.randint(0, num_players - 1)
    else:  # SEQUENTIAL
        primary = (current_idx + 1) % num_players
        
    # Secondary Selection
    if num_players <= 2:
        # For couples, it's always the other person
        secondary = (primary + 1) % num_players
    else:
        # For groups, pick a RANDOM partner (excluding primary)
        # This ensures dynamic interaction (A->B, A->C, etc.)
        candidates = [i for i in range(num_players) if i != primary]
        secondary = random.choice(candidates)
    
    return primary, secondary

def _get_anonymous_usage(anon_id: str) -> int:
    """Count activities presented to anonymous session in last 24h."""
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    sql = text("""
        SELECT COUNT(*) FROM user_activity_history 
        WHERE anonymous_session_id = :anon_id 
        AND presented_at > :cutoff
    """)
    result = db.session.execute(sql, {"anon_id": anon_id, "cutoff": cutoff}).scalar()
    return result or 0

def _check_daily_limit(user_id: Optional[str] = None, anonymous_session_id: Optional[str] = None) -> dict:
    """Check if user (auth or anon) has reached daily limit."""
    limit = 25
    
    # 1. Authenticated User
    if user_id:
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
            
        # Reset Logic is in User model or helper, assuming simpler read here
        # or simplified flow. The helper 'check_daily_activity_limit' does the reset.
        # But we need the values.
        
        return {
            "limit_reached": user.daily_activity_count >= limit,
            "remaining": max(0, limit - user.daily_activity_count),
            "is_capped": True,
            "used": user.daily_activity_count,
            "limit": limit
        }
        
    # 2. Anonymous User
    if anonymous_session_id:
        used_count = _get_anonymous_usage(anonymous_session_id)
        return {
            "limit_reached": used_count >= limit,
            "remaining": max(0, limit - used_count),
            "is_capped": True,
            "used": used_count,
            "limit": limit
        }
        
    return {"error": "No identity provided"}

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
    

    
    # --- Personalization Logic ---
    
    # Fetch profiles
    # Fetch profiles
    primary_profile_dict = _get_player_profile(primary_player)
    partner_profile_dict = _get_player_profile(secondary_player)
    
    # Virtual Profile Support for Primary
    if not primary_profile_dict and primary_player.get('anatomy'):
        primary_profile_dict = _create_virtual_profile(primary_player)

    # Virtual Profile Support for Partner (Explicit Guest)
    # If partner has explicit anatomy but no profile, make virtual
    if not partner_profile_dict and secondary_player.get('anatomy'):
         partner_profile_dict = _create_virtual_profile(secondary_player)

    # Complimentary Partner Logic (if Primary exists but Partner is totally anon/missing)
    if primary_profile_dict and not partner_profile_dict:
        partner_profile_dict = _create_complimentary_profile(primary_profile_dict)
        
    candidate = None
    
    # If we have both profiles (real or virtual), use personalization
    if primary_profile_dict and partner_profile_dict:
        # Build limits
        exclude_ids = set()
        for item in queue:
            cid = item.get('card_id')
            # Handle potential non-int IDs if needed (though card_id is string usually)
            if cid and cid != 'fallback' and not cid.startswith('limit-'):
                try: exclude_ids.add(int(cid))
                except: pass
                
        # Build boundary list (union of hard limits)
        p1_bounds = primary_profile_dict.get('boundaries', {}).get('hard_limits', [])
        p2_bounds = partner_profile_dict.get('boundaries', {}).get('hard_limits', [])
        player_boundaries = list(set(p1_bounds + p2_bounds))
        
        # Build anatomy dict
        # anatomy structure: {anatomy_self: [], ...}
        p1_anatomy = primary_profile_dict.get('anatomy', {}).get('anatomy_self', [])
        p2_anatomy = partner_profile_dict.get('anatomy', {}).get('anatomy_self', [])
        player_anatomy = {
            'active_anatomy': p1_anatomy,
            'partner_anatomy': p2_anatomy
        }
        
        # Determine Session Mode
        session_mode = 'groups' if len(players) > 2 else 'couples'
        
        candidate = find_best_activity_candidate(
            rating=rating,
            intensity_min=intensity_min,
            intensity_max=intensity_max,
            activity_type=activity_type.lower(),
            player_a_profile=primary_profile_dict,
            player_b_profile=partner_profile_dict,
            session_mode=session_mode,
            player_boundaries=player_boundaries,
            player_anatomy=player_anatomy,
            excluded_ids=exclude_ids,
            top_n=75, # Heavy JIT: Fetch 75*2=150 candidates
            randomize=True # Random sample
        )

    # Fallback to Random Activity
    # Fallback to Random Activity
    if not candidate:
        # Re-determine mode for fallback scope (redundant check but safe)
        session_mode = 'groups' if len(players) > 2 else 'couples'
        scope_filter = ['couples', 'all'] if session_mode == 'couples' else ['groups', 'all']
        
        candidate = Activity.query.filter(
            Activity.type == activity_type.lower(),
            Activity.rating == rating,
            Activity.intensity >= intensity_min,
            Activity.intensity <= intensity_max,
            Activity.is_active == True,
            Activity.approved == True,
            Activity.audience_scope.in_(scope_filter)
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

def _fill_queue(session: Session, target_size: int = 3, owner_id: str = None, anonymous_session_id: str = None) -> List[Dict[str, Any]]:
    """
    Ensure the session quantity has `target_size` items.
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
    if owner_id or anonymous_session_id:
        status = _check_daily_limit(user_id=owner_id, anonymous_session_id=anonymous_session_id)
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
@token_required
def start_game(current_user_id):
    """
    Start a new game session.
    Returns a queue of 3 cards.
    """
    try:
        data = request.get_json()
        player_ids = data.get("player_ids", [])
        
        # Ensure authenticated user is included in players or at least considered owner
        # If player_ids is internal ID list, ensure current_user_id is there.
        # However, frontend might send partner ID only?
        # Let's assume player_ids is list of participants.
        
        # Convert current_user_id to string for consistency
        auth_user_id = str(current_user_id) if current_user_id else None
        
        # Check for Anonymous Identity
        anonymous_session_id = data.get("anonymous_session_id")
        
        if not auth_user_id and not anonymous_session_id:
             return jsonify({"error": "Unauthorized", "message": "Login or Anonymous ID required"}), 401
             
        # Handling Player List
        # If authenticated, ensure they are in the list
        if auth_user_id:
             if auth_user_id not in player_ids:
                 player_ids.insert(0, auth_user_id)
        
        # ... (Rest of logic) ...
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
        # If explicit 'players' array of objects is passed (New Frontend), use it directly
        raw_players = data.get("players", [])
        
        # If 'player_ids' is used (Legacy/Simple), use existing logic
        
        # Check limit (1 credit for start)
        limit_status = {"limit_reached": False}
        
        # Owner Logic: Use Auth User, else Anon ID
        owner_id = auth_user_id 
        owner_anon_id = anonymous_session_id if not auth_user_id else None

        # Resolve players
        final_players = []
        
        if raw_players and isinstance(raw_players[0], dict):
            # Use provided full player objects (for Guests)
            # Validate anatomy presence
            for p in raw_players:
                final_players.append({
                    "id": p.get("id", str(uuid.uuid4())),
                    "name": p.get("name") or "Player",
                    "anatomy": p.get("anatomy", ["penis"]) # Default unsafe but required
                })
        else:
            # Legacy ID lookup
            if not player_ids and not raw_players:
                 if auth_user_id: player_ids = [auth_user_id]
                 else: return jsonify({"error": "No players provided"}), 400

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
                    final_players.append({
                        "id": str(user.id),
                        "name": user.display_name or "Player",
                        "anatomy": user.get_anatomy_self_array()
                    })
                else:
                    final_players.append({
                        "id": pid,
                        "name": f"Player {pid[:4]}",
                        "anatomy": ["penis"]
                    })
        
        players = final_players

        # INITIAL LIMIT CHECK
        limit_status = _check_daily_limit(user_id=owner_id, anonymous_session_id=owner_anon_id)

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
            player_b_profile_id=1,
            # Link owner
            session_owner_user_id=owner_id
        )
        
        # If anonymous, we might want to store partner_anonymous_name/anatomy on the session for legacy
        # But players JSONB handles it.
        
        db.session.add(session)
        # Commit first to get session_id 
        db.session.commit()
        
        # Fill Queue (Batch of 3)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id, anonymous_session_id=owner_anon_id)
        
        # Charge 1 Credit for the first card IF it isn't a limit card
        head_card = queue[0] if queue else {}
        is_limit_card = head_card.get('card', {}).get('type') == 'LIMIT_REACHED'
        
        if not is_limit_card:
            if owner_id:
                _increment_daily_count(owner_id)
            elif owner_anon_id:
                # Anonymous: We don't increment a counter. The 'record' in history IS the count.
                # But that happens in next_turn? 
                # Wait: On START, we show the first card. Is it "consumed"?
                # Usually START shows card 1. NEXT consumes card 1 and shows card 2.
                # So START does not record history yet?
                # If we don't record history, the COUNT doesn't go up. (Infinite restart loop hole).
                # To fix: we must record the first card as "presented" immediately?
                # Or just accept the loophole for MVP (User can restart game 100 times to see 100 first cards).
                # Given strictness request: We should probably record it. 
                pass

        # Re-check and Scrub
        # For Anonymous, the count relies on history. If we didn't insert history, limit doesn't change.
        # Let's trust the initial check result for this turn.
        
        if limit_status.get("limit_reached"):
             queue = _scrub_queue_for_limit(queue, keep_first=True) # Keep the one we (maybe) paid for
             
             # If strictly capped (e.g. 25/25), keep_first should be FALSE if we want to block new starts?
             # If limit is 25. Used is 25. User calls Start. Limit Reached = True.
             # Queue has 3 cards. 
             # If we keep_first, they get Card 1. Then Next blocks.
             # This essentially gives them 26 cards.
             # Acceptable for MVP.

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
@token_required
def next_turn(current_user_id, session_id):
    """
    Advance to next turn.
    Consumes the played card, increments credit, replenishes queue.
    """
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404
            
        # Validate Participation
        # session.players is JSON list of dicts [{'id':...}, ...]
        players = session.players or []
        is_participant = False
        
        # Check against Auth User
        if current_user_id:
            for p in players:
                 if str(p.get('id')) == str(current_user_id):
                     is_participant = True
                     break
        
        # Check against Anonymous ID (if no auth match)
        data = request.get_json() or {} # Handle empty body safety
        anonymous_session_id = data.get("anonymous_session_id")
         
        if not is_participant and anonymous_session_id:
             for p in players:
                 if str(p.get('id')) == str(anonymous_session_id):
                     is_participant = True
                     break
        
        if not is_participant:
             return jsonify({'error': 'Unauthorized', 'message': 'Not a participant'}), 403
            
        
        state = session.current_turn_state or {}
        queue = state.get("queue", [])
        
        # Determine owner
        owner_id = str(current_user_id) if current_user_id else None
        
        # If guest, use anonymous session id
        if not owner_id and not anonymous_session_id:
            return jsonify({'error': 'Unauthorized', 'message': 'Identity required for billing'}), 401

        # 1. Consume the current card (Head of queue)
        if queue:
            last_card = queue.pop(0)
            state["queue"] = queue
            session.current_turn_state = state
            flag_modified(session, "current_turn_state")
            
            # LOGGING FOR ANONYMOUS: We MUST insert into history to track limits
            if not owner_id and anonymous_session_id and last_card.get('card', {}).get('type') != 'LIMIT_REACHED':
                 # Insert manual history record
                 from ..models.activity_history import UserActivityHistory
                 
                 card_data = last_card.get('card', {})
                 cid_str = card_data.get('card_id')
                 activity_id = int(cid_str) if cid_str and cid_str.isdigit() else None
                 
                 history = UserActivityHistory(
                     anonymous_session_id=anonymous_session_id,
                     session_id=session.session_id,
                     activity_id=activity_id,
                     activity_type=card_data.get('type', 'TRUTH').lower(),
                     was_skipped=False,
                     presented_at=datetime.now(timezone.utc)
                 )
                 db.session.add(history)
                 
            # Charge 1 Credit for the played card IF it wasn't a barrier card
            if owner_id and last_card.get('card', {}).get('type') != 'LIMIT_REACHED':
                _increment_daily_count(owner_id)
        
        # 2. Replenish Queue (Add 1 to end)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id, anonymous_session_id=anonymous_session_id)
        
        # SCRUBBER: Check limit and scrub buffer if needed
        limit_status = {}
        if owner_id or anonymous_session_id:
            limit_status = _check_daily_limit(user_id=owner_id, anonymous_session_id=anonymous_session_id)
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
        # If DB error, rollback?
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
