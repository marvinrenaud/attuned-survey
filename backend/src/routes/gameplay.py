"""
Gameplay routes for Just-in-Time architecture.
Handles session creation, player rotation, and activity selection.
"""
from ..logging_config import get_logger, timed
import uuid
import random
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from flask import Blueprint, jsonify, request
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import text
from ..middleware.auth import token_required, optional_token

from ..extensions import db, limiter
from ..models.session import Session
from ..models.user import User
from ..models.activity import Activity
from ..db import repository
from ..recommender.picker import get_intensity_window, get_phase_name
from ..game.text_resolver import resolve_activity_text
from ..db.repository import find_best_activity_candidate
from ..models.profile import Profile
from ..models.partner import PartnerConnection

logger = get_logger()

gameplay_bp = Blueprint("gameplay", __name__, url_prefix="/api/game")

# --- Helper Functions ---

def _resolve_player(player_data: Dict[str, Any], current_user_id: str) -> Dict[str, Any]:
    """
    Resolve player info for session storage.
    
    SECURITY: Only performs DB lookup for current_user_id (IDOR protection).
    Other players use frontend-provided values.
    
    Args:
        player_data: Player dict from frontend (may have id, name, anatomy, anatomy_preference)
                     Or could be a JSON string or plain ID string
        current_user_id: The authenticated user's ID
        
    Returns:
        Resolved player dict with name, anatomy, and anatomy_preference
    """
    import json
    
    # Handle case where player_data is a string
    if isinstance(player_data, str):
        # Try to parse as JSON first (e.g., '{"name": "Guest", "anatomy": [...]}')
        try:
            parsed = json.loads(player_data)
            if isinstance(parsed, dict):
                player_data = parsed
            else:
                # Parsed to something else (unlikely), treat as ID
                player_data = {"id": player_data}
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, treat as a plain ID string (e.g., "uuid-here")
            player_data = {"id": player_data}
    
    player_id = player_data.get('id')
    
    # SECURITY: Check for authenticated user OR valid partner connection
    allow_lookup = False
    
    # 1. Self lookup
    if player_id and str(player_id) == str(current_user_id):
        allow_lookup = True
    
    # 2. Partner lookup (if connected)
    if not allow_lookup and player_id and current_user_id:
        # Check for accepted connection
        # (requester=me, recipient=them) OR (requester=them, recipient=me)
        # Convert to UUIDs for strict comparison if possible
        try:
            uid_obj = uuid.UUID(str(current_user_id))
            pid_obj = uuid.UUID(str(player_id))
            
            conn = PartnerConnection.query.filter(
                ((PartnerConnection.requester_user_id == uid_obj) & (PartnerConnection.recipient_user_id == pid_obj)) |
                ((PartnerConnection.requester_user_id == pid_obj) & (PartnerConnection.recipient_user_id == uid_obj))
            ).filter_by(status='accepted').first()
        except (ValueError, TypeError):
             conn = None
        
        if conn:
            allow_lookup = True

    if allow_lookup:
        try:
            user = User.query.get(uuid.UUID(player_id))
            if user:
                # Get display name with fallbacks
                display_name = user.display_name
                if not display_name:
                    profile = Profile.query.filter_by(user_id=user.id).first()
                    if profile and profile.submission and profile.submission.payload_json:
                        display_name = profile.submission.payload_json.get('name')
                
                return {
                    "id": str(user.id),
                    "name": display_name or "Player",
                    "anatomy": user.get_anatomy_self_array(),
                    "anatomy_preference": user.get_anatomy_preference_array()
                }
        except (ValueError, TypeError):
            pass
    
    # Guest player - use provided values with safe defaults
    return {
        "id": player_id or str(uuid.uuid4()),
        "name": player_data.get("name") or "Guest",
        "anatomy": player_data.get("anatomy", []),
        "anatomy_preference": player_data.get("anatomy_preference", [])
    }



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
    
    # Anatomy preferences (defaults to "likes everything" if missing)
    anatomy_pref = player_data.get('anatomy_preference')
    if not anatomy_pref:
        anatomy_pref = ['penis', 'vagina', 'breasts']

    return {
        'id': player_data.get('id', 'guest'),
        'is_anonymous': True,
        'anatomy': {
            'anatomy_self': anatomy,
            'anatomy_preference': anatomy_pref    
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

def _check_activity_limit(user_id: Optional[str] = None, anonymous_session_id: Optional[str] = None) -> dict:
    """Check if user (auth or anon) has reached lifetime activity limit."""
    from ..services.config_service import get_config_int

    limit = get_config_int('free_tier_activity_limit', 10)

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

        used = user.lifetime_activity_count or 0

        return {
            "limit_reached": used >= limit,
            "remaining": max(0, limit - used),
            "is_capped": True,
            "used": used,
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


# Alias for backwards compatibility
def _check_daily_limit(user_id: Optional[str] = None, anonymous_session_id: Optional[str] = None) -> dict:
    """Deprecated: Use _check_activity_limit instead."""
    return _check_activity_limit(user_id, anonymous_session_id)

def _increment_activity_count(user_id: str):
    """Increment lifetime activity count for free users."""
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return

    user = User.query.get(user_id)
    if user and user.subscription_tier != 'premium':
        user.lifetime_activity_count = (user.lifetime_activity_count or 0) + 1
        db.session.commit()


# Alias for backwards compatibility
def _increment_daily_count(user_id: str):
    """Deprecated: Use _increment_activity_count instead."""
    _increment_activity_count(user_id)


def _enforce_activity_limit(
    queue: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    anonymous_session_id: Optional[str] = None,
    charge_credit: bool = True
) -> tuple:
    """
    Single source of truth for activity limit enforcement.

    This function handles the complete limit enforcement logic:
    1. Checks if first card is a limit card (if so, no charge needed)
    2. Increments activity count if charge_credit=True and card is real
    3. Re-checks limit status AFTER increment (fresh status)
    4. Scrubs queue if limit reached, with appropriate keep_first logic
    5. Returns fresh limit_status and modified queue

    Args:
        queue: The turn queue to potentially scrub
        user_id: Authenticated user ID (optional)
        anonymous_session_id: Anonymous session ID (optional)
        charge_credit: Whether to charge a credit for the first card

    Returns:
        tuple: (limit_status: dict, queue: list)
            - limit_status is ALWAYS fresh (post-increment if applicable)
            - queue is scrubbed if limit was reached
    """
    from ..services.config_service import get_config_int

    # Check if first card is a limit card (no charge needed)
    # In RANDOM mode: check card['type']
    # In MANUAL mode: check truth_card['type'] (card is None)
    head_card = queue[0] if queue else {}
    card_obj = head_card.get('card')
    truth_card_obj = head_card.get('truth_card')

    is_limit_card = False
    if card_obj and card_obj.get('type') == 'LIMIT_REACHED':
        is_limit_card = True
    elif truth_card_obj and truth_card_obj.get('type') == 'LIMIT_REACHED':
        is_limit_card = True

    # Charge credit if requested and card is real
    if charge_credit and not is_limit_card:
        if user_id:
            _increment_activity_count(user_id)
        # Anonymous users: count is tracked via history, not incremented here

    # Get FRESH limit status (post-increment)
    limit_status = _check_activity_limit(user_id=user_id, anonymous_session_id=anonymous_session_id)

    # Scrub queue if limit reached
    if limit_status.get("limit_reached"):
        # Determine keep_first logic:
        # - If we just charged (card was real), keep first card (it's paid for)
        # - If we're over limit (used > limit), don't keep first
        # - If first card was already a limit card, doesn't matter
        used = limit_status.get("used", 0)
        limit = limit_status.get("limit", get_config_int('free_tier_activity_limit', 10))

        # Keep first if we're exactly at limit (not over), and card was real
        keep_first = (used <= limit) and not is_limit_card

        queue = _scrub_queue_for_limit(queue, keep_first=keep_first)

    return limit_status, queue


def _generate_single_card(
    activity_type: str,
    rating: str,
    intensity_min: int,
    intensity_max: int,
    primary_player: Dict[str, Any],
    secondary_player: Dict[str, Any],
    primary_profile_dict: Optional[Dict],
    partner_profile_dict: Optional[Dict],
    session_mode: str,
    player_boundaries: List[str],
    player_anatomy: Dict[str, List[str]],
    p1_truth_topics: Dict,
    p2_truth_topics: Dict,
    exclude_ids: set,
    session: Session
) -> Optional[Dict[str, Any]]:
    """
    Generate a single card of the specified type.

    Returns:
        Card dict with card_id, type, display_text, etc. or None if no activity found.
    """
    candidate = None

    # If we have both profiles, use personalization
    if primary_profile_dict and partner_profile_dict:
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
            player_a_truth_topics=p1_truth_topics,
            player_b_truth_topics=p2_truth_topics,
            excluded_ids=exclude_ids,
            top_n=75,
            randomize=True
        )

    # Fallback to random activity
    if not candidate:
        scope_filter = ['couples', 'all'] if session_mode == 'couples' else ['groups', 'all']

        candidate = Activity.query.filter(
            Activity.type == activity_type.lower(),
            Activity.rating == rating,
            Activity.intensity >= intensity_min,
            Activity.intensity <= intensity_max,
            Activity.is_active == True,
            Activity.approved == True,
            Activity.audience_scope.in_(scope_filter),
            ~Activity.activity_id.in_(exclude_ids) if exclude_ids else True
        ).order_by(db.func.random()).first()

    if not candidate:
        return None

    # Text Resolution
    try:
        script = candidate.script
        if not script or 'steps' not in script or not script['steps']:
            raise ValueError("Activity script is missing or empty")
        activity_text = script['steps'][0].get('do', "Perform the activity.")
    except Exception as e:
        logger.error("activity_text_extraction_failed", error=str(e), activity_id=str(candidate.activity_id) if candidate else None)
        activity_text = "Perform a mystery activity with your partner."

    resolved_text = resolve_activity_text(
        activity_text,
        primary_player.get("name", "Player"),
        secondary_player.get("name", "Partner")
    )

    return {
        "card_id": str(candidate.activity_id),
        "type": activity_type.upper(),
        "primary_player": primary_player.get("name", "Player"),
        "secondary_players": [secondary_player.get("name", "Partner")],
        "display_text": resolved_text,
        "intensity_rating": candidate.intensity
    }


def _generate_turn_data(session: Session, step_offset: int = 0, selected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate data for a single turn without committing to DB.

    In MANUAL mode: generates both truth_card and dare_card, sets card to null.
    In RANDOM mode: generates single card (existing behavior).
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
    
    # Check selection mode
    is_manual_mode = settings.get("selection_mode", "RANDOM").upper() == "MANUAL"
    include_dare = settings.get("include_dare", True)

    # Intensity
    intimacy_level = settings.get("intimacy_level", 3)
    rating = 'R'
    if intimacy_level <= 2: rating = 'G'
    elif intimacy_level >= 5: rating = 'X'

    intensity_min, intensity_max = get_intensity_window(effective_step, 25, rating)

    # --- Personalization Logic ---

    # Fetch profiles
    primary_profile_dict = _get_player_profile(primary_player)
    partner_profile_dict = _get_player_profile(secondary_player)

    # Virtual Profile Support for Primary
    if not primary_profile_dict and primary_player.get('anatomy'):
        primary_profile_dict = _create_virtual_profile(primary_player)

    # Virtual Profile Support for Partner (Explicit Guest)
    if not partner_profile_dict and secondary_player.get('anatomy'):
         partner_profile_dict = _create_virtual_profile(secondary_player)

    # Complimentary Partner Logic (if Primary exists but Partner is totally anon/missing)
    if primary_profile_dict and not partner_profile_dict:
        partner_profile_dict = _create_complimentary_profile(primary_profile_dict)

    # Build exclusion set
    exclude_ids = set()
    for item in queue:
        cid = item.get('card_id')
        if cid and cid != 'fallback' and not str(cid).startswith('limit-'):
            try: exclude_ids.add(int(cid))
            except (ValueError, TypeError): pass
        # Also exclude cards from truth_card and dare_card in MANUAL mode
        for card_field in ['truth_card', 'dare_card']:
            card_obj = item.get(card_field)
            if card_obj:
                cid = card_obj.get('card_id')
                if cid and cid != 'fallback' and not str(cid).startswith('limit-'):
                    try: exclude_ids.add(int(cid))
                    except (ValueError, TypeError): pass

    # --- REPETITION PREVENTION ---
    # 1. Session Exclusion (Strict): Exclude ANY activity played in this session by ANYONE
    try:
         from ..models.activity_history import UserActivityHistory

         session_history = db.session.query(UserActivityHistory.activity_id)\
             .filter(UserActivityHistory.session_id == session.session_id)\
             .filter(UserActivityHistory.activity_id.isnot(None))\
             .all()

         for (hid,) in session_history:
             exclude_ids.add(hid)
    except Exception as e:
        logger.error("session_history_fetch_failed", error=str(e))

    # 2. Player History Exclusion (Long-term)
    try:
         primary_uid = primary_player.get('id')
         if primary_uid:
             recent_history = db.session.query(UserActivityHistory.activity_id)\
                 .filter(UserActivityHistory.primary_player_id == str(primary_uid))\
                 .filter(UserActivityHistory.activity_id.isnot(None))\
                 .order_by(UserActivityHistory.presented_at.desc())\
                 .limit(100)\
                 .all()

             for (hid,) in recent_history:
                 exclude_ids.add(hid)
    except Exception as e:
        logger.error("player_history_fetch_failed", error=str(e))

    # Build common context for card generation
    session_mode = 'groups' if len(players) > 2 else 'couples'
    player_boundaries = []
    player_anatomy = {'active_anatomy': [], 'partner_anatomy': []}
    p1_truth_topics = {}
    p2_truth_topics = {}

    if primary_profile_dict and partner_profile_dict:
        p1_bounds = primary_profile_dict.get('boundaries', {}).get('hard_limits', [])
        p2_bounds = partner_profile_dict.get('boundaries', {}).get('hard_limits', [])
        player_boundaries = list(set(p1_bounds + p2_bounds))

        p1_anatomy = primary_profile_dict.get('anatomy', {}).get('anatomy_self', [])
        p2_anatomy = partner_profile_dict.get('anatomy', {}).get('anatomy_self', [])
        player_anatomy = {
            'active_anatomy': p1_anatomy,
            'partner_anatomy': p2_anatomy
        }

        p1_truth_topics = primary_profile_dict.get('truth_topics', {})
        p2_truth_topics = partner_profile_dict.get('truth_topics', {})

    # Progress object (common to all cards)
    progress = {
        "current_step": target_step,
        "total_steps": 25,
        "intensity_phase": get_phase_name(effective_step, 25).capitalize()
    }

    # --- MANUAL MODE: Generate paired cards ---
    if is_manual_mode:
        # Generate TRUTH card
        truth_card = _generate_single_card(
            activity_type="truth",
            rating=rating,
            intensity_min=intensity_min,
            intensity_max=intensity_max,
            primary_player=primary_player,
            secondary_player=secondary_player,
            primary_profile_dict=primary_profile_dict,
            partner_profile_dict=partner_profile_dict,
            session_mode=session_mode,
            player_boundaries=player_boundaries,
            player_anatomy=player_anatomy,
            p1_truth_topics=p1_truth_topics,
            p2_truth_topics=p2_truth_topics,
            exclude_ids=exclude_ids,
            session=session
        )

        # Generate DARE card (if dares enabled)
        dare_card = None
        if include_dare:
            # Expand exclusions to avoid using same activity as truth
            dare_exclude = exclude_ids.copy()
            if truth_card:
                try: dare_exclude.add(int(truth_card["card_id"]))
                except (ValueError, TypeError): pass

            dare_card = _generate_single_card(
                activity_type="dare",
                rating=rating,
                intensity_min=intensity_min,
                intensity_max=intensity_max,
                primary_player=primary_player,
                secondary_player=secondary_player,
                primary_profile_dict=primary_profile_dict,
                partner_profile_dict=partner_profile_dict,
                session_mode=session_mode,
                player_boundaries=player_boundaries,
                player_anatomy=player_anatomy,
                p1_truth_topics=p1_truth_topics,
                p2_truth_topics=p2_truth_topics,
                exclude_ids=dare_exclude,
                session=session
            )

        # Fallback if no truth card found
        if not truth_card:
            truth_card = {
                "card_id": "fallback",
                "type": "TRUTH",
                "primary_player": primary_player.get("name", "Player"),
                "secondary_players": [secondary_player.get("name", "Partner")],
                "display_text": "Tell your partner something you love about them.",
                "intensity_rating": 1
            }

        logger.info("manual_mode_cards_generated",
            step=target_step,
            truth_card_id=truth_card.get("card_id") if truth_card else None,
            dare_card_id=dare_card.get("card_id") if dare_card else None
        )

        return {
            "status": "SHOW_CARD",
            "primary_player_idx": primary_idx,
            "step": target_step,
            "card_id": None,
            "card": None,
            "truth_card": truth_card,
            "dare_card": dare_card,
            "progress": progress
        }

    # --- RANDOM MODE: Generate single card (existing behavior) ---
    activity_type = selected_type if selected_type else random.choice(["truth", "dare"])
    if activity_type.lower() == "dare" and not include_dare:
        activity_type = "truth"

    card = _generate_single_card(
        activity_type=activity_type,
        rating=rating,
        intensity_min=intensity_min,
        intensity_max=intensity_max,
        primary_player=primary_player,
        secondary_player=secondary_player,
        primary_profile_dict=primary_profile_dict,
        partner_profile_dict=partner_profile_dict,
        session_mode=session_mode,
        player_boundaries=player_boundaries,
        player_anatomy=player_anatomy,
        p1_truth_topics=p1_truth_topics,
        p2_truth_topics=p2_truth_topics,
        exclude_ids=exclude_ids,
        session=session
    )

    # Fallback for random mode
    if not card:
        card = {
            "card_id": "fallback",
            "type": activity_type.upper(),
            "primary_player": primary_player.get("name", "Player"),
            "secondary_players": [secondary_player.get("name", "Partner")],
            "display_text": "Tell your partner something you love about them.",
            "intensity_rating": 1
        }

    logger.info("activity_selected",
        activity_id=card.get("card_id"),
        type=card.get("type"),
        step=target_step
    )

    return {
        "status": "SHOW_CARD",
        "primary_player_idx": primary_idx,
        "step": target_step,
        "card_id": card.get("card_id"),
        "card": card,
        "truth_card": None,
        "dare_card": None,
        "progress": progress
    }

def _generate_limit_card() -> Dict[str, Any]:
    """Generate a barrier card for when activity limit is reached."""
    limit_card_data = {
        "card_id": f"limit-barrier-{uuid.uuid4()}",
        "type": "LIMIT_REACHED",
        "primary_player": "System",
        "secondary_players": [],
        "display_text": "Activity limit reached. Tap to unlock unlimited turns.",
        "intensity_rating": 1
    }
    return {
        "status": "SHOW_CARD",
        "primary_player_idx": -1,
        "step": 999,
        "card_id": limit_card_data["card_id"],
        "card": limit_card_data,
        "truth_card": limit_card_data,  # Same limit card for both in MANUAL mode
        "dare_card": limit_card_data,
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
        # Check if it's already a limit card
        # In RANDOM mode: check item['card']['type']
        # In MANUAL mode: check item['truth_card']['type'] (card is None)
        card_obj = item.get('card')
        truth_card_obj = item.get('truth_card')

        is_limit_card = False
        if card_obj and card_obj.get('type') == 'LIMIT_REACHED':
            is_limit_card = True
        elif truth_card_obj and truth_card_obj.get('type') == 'LIMIT_REACHED':
            is_limit_card = True

        if not is_limit_card:
            # Generate replacement
            barrier = _generate_limit_card()
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
        status = _check_activity_limit(user_id=owner_id, anonymous_session_id=anonymous_session_id)
        limit_reached = status.get("limit_reached", False)
    
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
@limiter.limit("30 per hour")
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
        # Sanitize player_ids to remove invalid entries (e.g. empty lists from frontend bugs)
        if isinstance(player_ids, list):
            cleaned_ids = []
            for p in player_ids:
                if p and isinstance(p, (str, uuid.UUID)):
                     s_p = str(p).strip()
                     # Basic UUID length check or similar to avoid "[]" strings
                     if len(s_p) > 20: 
                         cleaned_ids.append(s_p)
            player_ids = cleaned_ids

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

        # Resolve players using IDOR-safe helper
        final_players = []
        
        if raw_players and isinstance(raw_players[0], dict):
            # New format: players array with objects
            for p in raw_players:
                final_players.append(_resolve_player(p, auth_user_id))
        else:
            # Legacy format: player_ids array
            if not player_ids and not raw_players:
                if auth_user_id: 
                    player_ids = [auth_user_id]
                else: 
                    return jsonify({"error": "No players provided"}), 400

            for pid in player_ids:
                final_players.append(_resolve_player({"id": pid}, auth_user_id))
        
        players = final_players

        # Create Session
        # Convert owner_id to UUID for SQLite compatibility
        owner_uuid = uuid.UUID(owner_id) if owner_id else None
        
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
            session_owner_user_id=owner_uuid
        )
        
        # If anonymous, we might want to store partner_anonymous_name/anatomy on the session for legacy
        # But players JSONB handles it.
        
        db.session.add(session)
        # Commit first to get session_id 
        db.session.commit()
        
        # Fill Queue (Batch of 3)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id, anonymous_session_id=owner_anon_id)

        # Enforce activity limit: charge credit, get fresh status, scrub if needed
        # This returns FRESH limit_status (post-increment) and modified queue
        limit_status, queue = _enforce_activity_limit(
            queue=queue,
            user_id=owner_id,
            anonymous_session_id=owner_anon_id,
            charge_credit=True
        )

        # Update session state with scrubbed queue
        state = session.current_turn_state
        state["queue"] = queue
        session.current_turn_state = state
        flag_modified(session, "current_turn_state")
            
        db.session.commit()
        
        logger.info("game_session_started",
            session_id=str(session.session_id),
            player_count=len(players),
            intimacy_level=settings.get('intimacy_level')
        )
        
        # Response
        return jsonify({
            "session_id": session.session_id,
            "selection_mode": settings.get("selection_mode", "RANDOM").upper(),
            "limit_status": limit_status,
            "queue": queue,
            "current_turn": queue[0] if queue else {}
        }), 200

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error("start_game_failed", error=str(e), error_type=type(e).__name__, traceback=tb)
        db.session.rollback()
        return jsonify({"error": "Internal server error", "debug_message": str(e)}), 500

@gameplay_bp.route("/<session_id>/next", methods=["POST"])
@token_required
@limiter.limit("300 per hour")
def next_turn(current_user_id, session_id):
    """
    Advance to next turn.
    Consumes the played card, increments credit, replenishes queue.

    In MANUAL mode:
    - Requires selected_type in request body ("TRUTH" or "DARE")
    - Tracks only the selected card (truth_card or dare_card)
    - Charges 1 credit for the selected card
    """
    try:
        session = Session.query.get(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Ensure session is active
        if session.status != 'active':
            return jsonify({"error": "Session is not active"}), 400

        # Validate Participation
        players = session.players or []
        is_participant = False

        if current_user_id:
            for p in players:
                 if str(p.get('id')) == str(current_user_id):
                     is_participant = True
                     break

        # Check against Anonymous ID (if no auth match)
        data = request.get_json() or {}
        anonymous_session_id = data.get("anonymous_session_id")
        selected_type = data.get("selected_type")  # NEW: Read selection for MANUAL mode

        if not is_participant and anonymous_session_id:
             for p in players:
                 if str(p.get('id')) == str(anonymous_session_id):
                     is_participant = True
                     break

        if not is_participant:
             return jsonify({'error': 'Unauthorized', 'message': 'Not a participant'}), 403

        # Get session settings
        settings = session.game_settings or {}
        is_manual_mode = settings.get("selection_mode", "RANDOM").upper() == "MANUAL"

        state = session.current_turn_state or {}
        queue = state.get("queue", [])

        # Determine owner
        owner_id = str(current_user_id) if current_user_id else None

        if not owner_id and not anonymous_session_id:
            return jsonify({'error': 'Unauthorized', 'message': 'Identity required for billing'}), 401

        # 1. Consume the current card (Head of queue)
        if queue:
            consumed_item = queue.pop(0)
            state["queue"] = queue
            session.current_turn_state = state
            flag_modified(session, "current_turn_state")

            # Determine which card was played based on mode
            if is_manual_mode:
                # MANUAL MODE: Validate and extract selected card
                if not selected_type:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': 'selected_type required in MANUAL mode'
                    }), 400

                selected_type = selected_type.upper()

                if selected_type == "TRUTH":
                    card_data = consumed_item.get("truth_card")
                elif selected_type == "DARE":
                    card_data = consumed_item.get("dare_card")
                else:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': 'selected_type must be TRUTH or DARE'
                    }), 400

                if card_data is None:
                    return jsonify({
                        'error': 'Bad Request',
                        'message': f'{selected_type} not available for this turn'
                    }), 400

                logger.info("manual_mode_card_consumed",
                    session_id=session_id,
                    selected_type=selected_type,
                    card_id=card_data.get('card_id')
                )
            else:
                # RANDOM MODE: Use existing card field
                card_data = consumed_item.get('card', {})

            # LOGGING: Record history for the played card
            if card_data and card_data.get('type') != 'LIMIT_REACHED':
                 from ..models.activity_history import UserActivityHistory

                 cid_str = card_data.get('card_id')
                 activity_id = int(cid_str) if cid_str and str(cid_str).isdigit() else None

                 turn_primary_idx = consumed_item.get('primary_player_idx')
                 turn_primary_id = None
                 if turn_primary_idx is not None and 0 <= turn_primary_idx < len(players):
                     turn_primary_id = str(players[turn_primary_idx].get('id'))

                 history = UserActivityHistory(
                     user_id=owner_id,
                     anonymous_session_id=anonymous_session_id,
                     session_id=session.session_id,
                     activity_id=activity_id,
                     activity_type=card_data.get('type', 'TRUTH').lower(),
                     primary_player_id=turn_primary_id,
                     was_skipped=False,
                     presented_at=datetime.utcnow()
                 )
                 db.session.add(history)

            # Charge 1 Credit for the played card IF it wasn't a barrier card
            if owner_id and card_data and card_data.get('type') != 'LIMIT_REACHED':
                _increment_activity_count(owner_id)

        # 2. Replenish Queue (Add 1 to end)
        queue = _fill_queue(session, target_size=3, owner_id=owner_id, anonymous_session_id=anonymous_session_id)

        # Enforce activity limit
        limit_status, queue = _enforce_activity_limit(
            queue=queue,
            user_id=owner_id,
            anonymous_session_id=anonymous_session_id,
            charge_credit=False
        )

        # Update session state
        state["queue"] = queue
        session.current_turn_state = state
        flag_modified(session, "current_turn_state")

        db.session.commit()

        # 3. Response
        response = {
            "session_id": session.session_id,
            "selection_mode": settings.get("selection_mode", "RANDOM").upper(),
            "limit_status": limit_status,
            "queue": queue,
            "current_turn": queue[0] if queue else {}
        }

        return jsonify(response)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error("next_turn_failed", session_id=session_id, error=str(e))
        # If DB error, rollback?
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500
