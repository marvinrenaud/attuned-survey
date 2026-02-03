"""Data repository for accessing profiles, sessions, activities, and compatibility."""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from ..extensions import db
from ..models.profile import Profile
from ..models.session import Session
from ..models.activity import Activity
from ..models.session_activity import SessionActivity
from ..models.compatibility import Compatibility
from ..models.survey import SurveySubmission
from ..models.user import User

logger = logging.getLogger(__name__)


# ==============================================================================
# Profile Operations
# ==============================================================================

def sync_user_anatomy_to_profile(user_id: str) -> bool:
    """
    Sync anatomy booleans from users table to profiles.anatomy JSONB.
    
    Called whenever:
    - Profile is created
    - User updates anatomy
    - Survey is completed
    
    Args:
        user_id: User UUID
    
    Returns:
        True if sync successful, False if user or profile not found
    """
    try:
        user = User.query.filter_by(id=user_id).first()
        profile = Profile.query.filter_by(user_id=user_id).first()
        
        if not user:
            logger.warning(f"User not found for anatomy sync: {user_id}")
            return False
        
        if not profile:
            logger.info(f"No profile found for user {user_id} - will sync when profile created")
            return False
        
        # Sync anatomy from user booleans to profile JSONB
        profile.anatomy = {
            'anatomy_self': user.get_anatomy_self_array(),
            'anatomy_preference': user.get_anatomy_preference_array()
        }
        
        db.session.commit()
        logger.info(f"Synced anatomy for user {user_id} to profile {profile.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync anatomy for user {user_id}: {e}")
        db.session.rollback()
        return False

def get_or_create_profile(submission_id: str) -> Profile:
    """
    Get or create a profile linked to a survey submission.
    
    Args:
        submission_id: Survey submission ID
    
    Returns:
        Profile instance
    
    Raises:
        ValueError: If submission doesn't exist
    """
    # Check if profile already exists
    profile = Profile.query.filter_by(submission_id=submission_id).first()
    if profile:
        logger.info(f"Profile found for submission {submission_id}: profile_id={profile.id}")
        return profile
    
    # Get submission to extract profile data
    submission = SurveySubmission.query.filter_by(submission_id=submission_id).first()
    if not submission:
        raise ValueError(f"Survey submission not found: {submission_id}")
    
    # Extract derived data from submission payload
    payload = submission.payload_json or {}
    derived = payload.get('derived', {})
    
    if not derived:
        raise ValueError(f"Submission {submission_id} has no derived profile data")
    
    # Extract anatomy data (with defaults for legacy profiles)
    anatomy = derived.get('anatomy', {})
    anatomy_self = anatomy.get('anatomy_self', [])
    anatomy_preference = anatomy.get('anatomy_preference', [])
    
    # Default to all anatomy if not specified (backward compatibility)
    if not anatomy_self:
        anatomy_self = ['penis', 'vagina', 'breasts']
    if not anatomy_preference:
        anatomy_preference = ['penis', 'vagina', 'breasts']
    
    # Create new profile
    profile = Profile(
        submission_id=submission_id,
        profile_version=derived.get('profile_version', '0.4'),
        power_dynamic=derived.get('power_dynamic', {}),
        arousal_propensity=derived.get('arousal_propensity', {}),
        domain_scores=derived.get('domain_scores', {}),
        activities=derived.get('activities', {}),
        truth_topics=derived.get('truth_topics', {}),
        boundaries=derived.get('boundaries', {}),
        anatomy={'anatomy_self': anatomy_self, 'anatomy_preference': anatomy_preference},
        activity_tags=derived.get('activity_tags', {})
    )
    
    db.session.add(profile)
    db.session.commit()
    
    logger.info(f"Profile created for submission {submission_id}: profile_id={profile.id}")
    return profile


def get_profile(profile_id: int) -> Optional[Profile]:
    """Get profile by ID."""
    return Profile.query.get(profile_id)


def get_profile_by_submission(submission_id: str) -> Optional[Profile]:
    """Get profile by submission ID."""
    return Profile.query.filter_by(submission_id=submission_id).first()


# ==============================================================================
# Session Operations
# ==============================================================================

def create_session(
    player_a_profile_id: int,
    player_b_profile_id: int,
    rating: str = 'R',
    activity_type: str = 'random',
    target_activities: int = 25,
    bank_ratio: float = 0.5,
    rules: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None
) -> Session:
    """
    Create a new game session.
    
    Args:
        player_a_profile_id: Profile ID for player A
        player_b_profile_id: Profile ID for player B
        rating: Content rating (G/R/X)
        activity_type: random, truth, or dare
        target_activities: Number of activities to generate
        bank_ratio: Ratio of bank vs AI activities (0.0-1.0)
        rules: Optional rules dict
        session_id: Optional custom session ID
    
    Returns:
        New Session instance
    """
    session = Session(
        session_id=session_id,  # Will use default UUID if None
        player_a_profile_id=player_a_profile_id,
        player_b_profile_id=player_b_profile_id,
        rating=rating,
        activity_type=activity_type,
        target_activities=target_activities,
        bank_ratio=bank_ratio,
        rules=rules or {'avoid_maybe_until': 6}
    )
    
    db.session.add(session)
    db.session.commit()
    
    logger.info(f"Session created: {session.session_id}")
    return session


def get_session(session_id: str) -> Optional[Session]:
    """Get session by ID."""
    return Session.query.get(session_id)


def update_session_progress(session_id: str, current_step: int, truths: int, dares: int) -> None:
    """Update session progress counters."""
    session = get_session(session_id)
    if session:
        session.current_step = current_step
        session.truth_so_far = truths
        session.dare_so_far = dares
        db.session.commit()


def complete_session(session_id: str) -> None:
    """Mark session as completed."""
    session = get_session(session_id)
    if session:
        session.status = 'completed'
        session.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Session completed: {session_id}")


# ==============================================================================
# Activity Bank Operations
# ==============================================================================

def meets_anatomy_requirements(activity: Activity, player_anatomy: Dict[str, List[str]]) -> bool:
    """
    Check if players have required body parts for activity.
    
    Args:
        activity: Activity instance
        player_anatomy: Dict with 'active_anatomy' and 'partner_anatomy' keys
    
    Returns:
        True if anatomy requirements are met, False otherwise
    """
    req = activity.required_bodyparts or {"active": [], "partner": []}
    active_req = req.get('active', [])
    partner_req = req.get('partner', [])
    
    # Get player anatomy (default to all if not specified)
    active_has = player_anatomy.get('active_anatomy', ['penis', 'vagina', 'breasts'])
    partner_has = player_anatomy.get('partner_anatomy', ['penis', 'vagina', 'breasts'])
    
    # Check if all required parts are present
    for part in active_req:
        if part not in active_has:
            return False
    for part in partner_req:
        if part not in partner_has:
            return False
    
    return True


def has_boundary_conflict(activity_boundaries: List[str], player_boundaries: List[str]) -> bool:
    """
    Check if activity hits any player hard boundary.

    Args:
        activity_boundaries: List of boundary keys from activity.hard_boundaries
        player_boundaries: Combined list of player hard boundaries

    Returns:
        True if there's a conflict, False otherwise
    """
    if not activity_boundaries or not player_boundaries:
        return False
    return any(b in player_boundaries for b in activity_boundaries)


def has_truth_topic_conflict(
    activity_truth_topics: Optional[List[str]],
    player_a_truth_topics: Optional[Dict[str, float]],
    player_b_truth_topics: Optional[Dict[str, float]]
) -> bool:
    """
    Check if activity touches a truth topic that either player said NO to.

    This is a HARD FILTER: if either player has score 0.0 for any of the
    activity's truth topics, the activity should not be shown.

    Args:
        activity_truth_topics: List of topic keys from activity.truth_topics
        player_a_truth_topics: Player A's topic preferences {topic: 0.0-1.0}
        player_b_truth_topics: Player B's topic preferences {topic: 0.0-1.0}

    Returns:
        True if there's a conflict (activity should be filtered), False otherwise
    """
    # No topics = bypass filter (no conflict)
    if not activity_truth_topics:
        return False

    # Default to empty dicts if not provided
    player_a_topics = player_a_truth_topics or {}
    player_b_topics = player_b_truth_topics or {}

    for topic in activity_truth_topics:
        # Check if either player said NO (0.0) to this topic
        # Default to 0.5 (neutral) if topic not in player's preferences
        if player_a_topics.get(topic, 0.5) == 0.0:
            return True
        if player_b_topics.get(topic, 0.5) == 0.0:
            return True

    return False


def find_activity_candidates(
    rating: str,
    intensity_min: int,
    intensity_max: int,
    activity_type: Optional[str] = None,
    session_mode: str = 'couples',
    player_boundaries: Optional[List[str]] = None,
    player_anatomy: Optional[Dict[str, List[str]]] = None,
    player_a_truth_topics: Optional[Dict[str, float]] = None,
    player_b_truth_topics: Optional[Dict[str, float]] = None,
    hard_limits: Optional[List[str]] = None,  # LEGACY, deprecated
    tags: Optional[List[str]] = None,
    randomize: bool = False,
    limit: int = 50
) -> List[Activity]:
    """
    Find activity candidates matching criteria with pre-filters for anatomy, boundaries, and audience.

    Args:
        rating: Content rating (G/R/X)
        intensity_min: Minimum intensity
        intensity_max: Maximum intensity
        activity_type: Optional type filter (truth/dare)
        session_mode: Session mode ('couples' or 'groups')
        player_boundaries: List of combined player hard boundaries
        player_anatomy: Dict with 'active_anatomy' and 'partner_anatomy' lists
        player_a_truth_topics: Player A's truth topic preferences {topic: 0.0-1.0}
        player_b_truth_topics: Player B's truth topic preferences {topic: 0.0-1.0}
        hard_limits: LEGACY - List of hard limit keys to exclude (deprecated)
        tags: Optional tag filters
        randomize: Whether to sort results randomly
        limit: Maximum results to return

    Returns:
        List of matching Activity instances
    """
    # Base query: active, approved activities only
    query = Activity.query.filter(
        Activity.is_active == True,
        Activity.approved == True,
        Activity.rating == rating,
        Activity.intensity >= intensity_min,
        Activity.intensity <= intensity_max
    )
    
    # Filter by audience scope
    if session_mode == 'couples':
        query = query.filter(Activity.audience_scope.in_(['couples', 'all']))
    elif session_mode == 'groups':
        query = query.filter(Activity.audience_scope.in_(['groups', 'all']))
    
    # Filter by activity type
    if activity_type:
        query = query.filter(Activity.type == activity_type)
        
    # Apply randomization if requested
    if randomize:
        query = query.order_by(db.func.random())
    
    # Fetch candidates (over-fetch to account for post-filtering)
    candidates = query.limit(limit * 3).all()
    
    # Post-filter: anatomy requirements
    if player_anatomy:
        filtered = []
        for activity in candidates:
            if not meets_anatomy_requirements(activity, player_anatomy):
                continue
            filtered.append(activity)
        candidates = filtered
    
    # Post-filter: hard boundaries (new system)
    if player_boundaries:
        filtered = []
        for activity in candidates:
            if has_boundary_conflict(activity.hard_boundaries or [], player_boundaries):
                continue
            filtered.append(activity)
        candidates = filtered
    
    # Legacy hard limits filter (for backward compatibility)
    if hard_limits:
        filtered = []
        for activity in candidates:
            if activity.hard_limit_keys:
                if any(limit in hard_limits for limit in activity.hard_limit_keys):
                    continue
            filtered.append(activity)
        candidates = filtered

    # Post-filter: truth topics (for truth activities only)
    # If either player said NO (0.0) to a topic, filter out activities with that topic
    if player_a_truth_topics or player_b_truth_topics:
        filtered = []
        for activity in candidates:
            # Only apply to truth activities with truth_topics tags
            if activity.type == 'truth' and activity.truth_topics:
                if has_truth_topic_conflict(
                    activity.truth_topics,
                    player_a_truth_topics,
                    player_b_truth_topics
                ):
                    continue
            filtered.append(activity)
        candidates = filtered

    # Return up to limit
    candidates = candidates[:limit]
    
    logger.debug(
        f"Found {len(candidates)} activity candidates",
        extra={
            "rating": rating,
            "intensity_range": f"{intensity_min}-{intensity_max}",
            "type": activity_type,
            "session_mode": session_mode
        }
    )
    return candidates


def get_activity(activity_id: int) -> Optional[Activity]:
    """Get activity by ID."""
    return Activity.query.get(activity_id)


def find_best_activity_candidate(
    rating: str,
    intensity_min: int,
    intensity_max: int,
    activity_type: str,
    player_a_profile: Dict[str, Any],
    player_b_profile: Dict[str, Any],
    session_mode: str = 'couples',
    player_boundaries: Optional[List[str]] = None,
    player_anatomy: Optional[Dict[str, List[str]]] = None,
    player_a_truth_topics: Optional[Dict[str, float]] = None,
    player_b_truth_topics: Optional[Dict[str, float]] = None,
    hard_limits: Optional[List[str]] = None,  # LEGACY
    excluded_ids: Optional[set] = None,
    top_n: int = 20,
    randomize: bool = True
) -> Optional[Activity]:
    """
    Find best-matching activity using preference-based scoring with anatomy and boundary filters.

    Args:
        rating: Content rating (G/R/X)
        intensity_min: Minimum intensity
        intensity_max: Maximum intensity
        activity_type: 'truth' or 'dare'
        player_a_profile: Player A's complete profile dict
        player_b_profile: Player B's complete profile dict
        session_mode: Session mode ('couples' or 'groups')
        player_boundaries: Combined list of player hard boundaries
        player_anatomy: Dict with 'active_anatomy' and 'partner_anatomy' lists
        player_a_truth_topics: Player A's truth topic preferences {topic: 0.0-1.0}
        player_b_truth_topics: Player B's truth topic preferences {topic: 0.0-1.0}
        hard_limits: LEGACY - List of hard limit keys to exclude (deprecated)
        excluded_ids: Set of activity IDs already used (for deduplication)
        top_n: Consider top N candidates for scoring
        randomize: Whether to fetch candidates randomly (default True)

    Returns:
        Best-matching Activity or None
    """
    from ..recommender.scoring import score_activity_for_players, filter_by_power_dynamics
    
    if excluded_ids is None:
        excluded_ids = set()
    
    # Get candidates using enhanced filter
    candidates = find_activity_candidates(
        rating=rating,
        intensity_min=intensity_min,
        intensity_max=intensity_max,
        activity_type=activity_type,
        session_mode=session_mode,
        player_boundaries=player_boundaries,
        player_anatomy=player_anatomy,
        player_a_truth_topics=player_a_truth_topics,
        player_b_truth_topics=player_b_truth_topics,
        hard_limits=hard_limits,
        randomize=randomize,
        limit=top_n * 2  # Get more to account for exclusions
    )
    
    if not candidates:
        return None
    
    # Filter out already-used activities
    candidates = [c for c in candidates if c.activity_id not in excluded_ids]
    
    if not candidates:
        logger.warning("All candidates already used, no activities available")
        return None
    
    # Convert to dicts for scoring
    candidate_dicts = [c.to_dict() for c in candidates]
    
    # Filter by power dynamics first (removes hard mismatches)
    player_a_orientation = player_a_profile.get('power_dynamic', {}).get('orientation', 'Switch')
    player_b_orientation = player_b_profile.get('power_dynamic', {}).get('orientation', 'Switch')
    
    compatible_dicts = filter_by_power_dynamics(
        candidate_dicts,
        player_a_orientation,
        player_b_orientation,
        min_score=0.3  # Moderate filtering
    )
    
    if not compatible_dicts:
        # No power-compatible activities, return first candidate anyway
        logger.warning(f"No power-compatible activities found, using first candidate")
        return candidates[0]
    
    # Score each compatible activity
    scored_activities = []
    
    for activity_dict in compatible_dicts:
        scores = score_activity_for_players(
            activity_dict,
            player_a_profile,
            player_b_profile
        )
        
        scored_activities.append({
            'activity_id': activity_dict['activity_id'],
            'score': scores['overall_score'],
            'scores': scores
        })
    
    # Sort by overall score descending
    scored_activities.sort(key=lambda x: x['score'], reverse=True)
    
    # Get best activity
    best = scored_activities[0]
    best_activity = next(c for c in candidates if c.activity_id == best['activity_id'])
    
    logger.debug(
        f"Selected activity with score {best['score']:.3f}",
        extra={
            'activity_id': best['activity_id'],
            'mutual_interest': best['scores']['mutual_interest_score'],
            'power_alignment': best['scores']['power_alignment_score'],
            'domain_fit': best['scores']['domain_fit_score']
        }
    )
    
    return best_activity


# ==============================================================================
# Session Activity Operations
# ==============================================================================

def save_session_activities(session_id: str, activities: List[Dict[str, Any]]) -> None:
    """
    Save or update activities for a session.
    
    Args:
        session_id: Session ID
        activities: List of activity dicts with seq, type, rating, intensity, script, etc.
    """
    for activity_data in activities:
        seq = activity_data.get('seq')
        
        # Check if already exists
        existing = SessionActivity.query.filter_by(
            session_id=session_id,
            seq=seq
        ).first()
        
        if existing:
            # Update existing
            existing.type = activity_data.get('type')
            existing.rating = activity_data.get('rating')
            existing.intensity = activity_data.get('intensity')
            existing.script = activity_data.get('script')
            existing.tags = activity_data.get('tags', [])
            existing.roles = activity_data.get('roles')
            existing.source = activity_data.get('provenance', {}).get('source', 'ai_generated')
            existing.template_id = activity_data.get('provenance', {}).get('template_id')
            existing.checks = activity_data.get('checks', {})
        else:
            # Create new
            session_activity = SessionActivity(
                session_id=session_id,
                seq=seq,
                activity_id=activity_data.get('provenance', {}).get('template_id'),
                type=activity_data.get('type'),
                rating=activity_data.get('rating'),
                intensity=activity_data.get('intensity'),
                script=activity_data.get('script'),
                tags=activity_data.get('tags', []),
                roles=activity_data.get('roles'),
                source=activity_data.get('provenance', {}).get('source', 'ai_generated'),
                template_id=activity_data.get('provenance', {}).get('template_id'),
                checks=activity_data.get('checks', {})
            )
            db.session.add(session_activity)
    
    db.session.commit()
    logger.info(f"Saved {len(activities)} activities for session {session_id}")


def get_session_activities(session_id: str) -> List[SessionActivity]:
    """Get all activities for a session, ordered by sequence."""
    return SessionActivity.query.filter_by(
        session_id=session_id
    ).order_by(SessionActivity.seq).all()


# ==============================================================================
# Compatibility Operations
# ==============================================================================

def save_compatibility_result(
    player_a_id: int,
    player_b_id: int,
    result: Dict[str, Any]
) -> Compatibility:
    """
    Save or update compatibility result.
    
    Args:
        player_a_id: Profile ID for player A
        player_b_id: Profile ID for player B
        result: Compatibility result dict
    
    Returns:
        Compatibility instance
    """
    # Ensure consistent ordering (lower ID first)
    ordered_a, ordered_b = Compatibility.get_or_create_key(player_a_id, player_b_id)
    
    # Check if already exists
    existing = Compatibility.query.filter_by(
        player_a_id=ordered_a,
        player_b_id=ordered_b
    ).first()
    
    # Extract data from result
    overall = result.get('overall_compatibility', {})
    overall_score = overall.get('score', 0) / 100.0  # Convert percentage to 0-1
    overall_percentage = overall.get('score', 0)
    interpretation = overall.get('interpretation', '')
    
    breakdown = result.get('breakdown', {})
    mutual_activities = result.get('mutual_activities', [])
    growth_opportunities = result.get('growth_opportunities', [])
    mutual_truth_topics = result.get('mutual_truth_topics', [])
    blocked_activities = result.get('blocked_activities', {})
    boundary_conflicts = result.get('boundary_conflicts', [])
    
    if existing:
        # Update existing
        existing.overall_score = overall_score
        existing.overall_percentage = overall_percentage
        existing.interpretation = interpretation
        existing.breakdown = breakdown
        existing.mutual_activities = mutual_activities
        existing.growth_opportunities = growth_opportunities
        existing.mutual_truth_topics = mutual_truth_topics
        existing.blocked_activities = blocked_activities
        existing.boundary_conflicts = boundary_conflicts
        existing.created_at = datetime.now(timezone.utc)  # Update timestamp
        
        compatibility = existing
    else:
        # Create new
        compatibility = Compatibility(
            player_a_id=ordered_a,
            player_b_id=ordered_b,
            overall_score=overall_score,
            overall_percentage=overall_percentage,
            interpretation=interpretation,
            breakdown=breakdown,
            mutual_activities=mutual_activities,
            growth_opportunities=growth_opportunities,
            mutual_truth_topics=mutual_truth_topics,
            blocked_activities=blocked_activities,
            boundary_conflicts=boundary_conflicts
        )
        db.session.add(compatibility)
    
    db.session.commit()
    logger.info(f"Saved compatibility for profiles {ordered_a} and {ordered_b}: {overall_percentage}%")
    
    return compatibility


def get_compatibility_result(player_a_id: int, player_b_id: int) -> Optional[Compatibility]:
    """Get compatibility result for two players."""
    ordered_a, ordered_b = Compatibility.get_or_create_key(player_a_id, player_b_id)
    
    return Compatibility.query.filter_by(
        player_a_id=ordered_a,
        player_b_id=ordered_b
    ).first()

