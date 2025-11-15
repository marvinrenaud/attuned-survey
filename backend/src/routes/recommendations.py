"""API routes for activity recommendations and compatibility."""
import logging
import uuid
import time
from typing import Dict, Any, List

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.profile import Profile
from ..models.session import Session
from ..models.activity import Activity
from ..db import repository
from ..recommender.picker import pick_type_balanced, get_intensity_window
from ..recommender.validator import check_activity_item, ValidationError
from ..recommender.repair import fast_repair, get_safe_fallback, create_placeholder_activity
from ..llm.generator import generate_recommendations
from ..compatibility.calculator import calculate_compatibility
from ..config import settings

logger = logging.getLogger(__name__)

bp = Blueprint("recommendations", __name__, url_prefix="/api")


@bp.route("/recommendations", methods=["POST"])
def create_recommendations():
    """
    Generate activity recommendations for a session.
    
    Request body:
    {
        "player_a": {"submission_id": "..."} or complete profile,
        "player_b": {"submission_id": "..."} or complete profile,
        "session": {
            "session_id": "optional",
            "rating": "G|R|X",
            "target_activities": 25,
            "bank_ratio": 0.6,
            "activity_type": "random|truth|dare",
            "rules": {"avoid_maybe_until": 6}
        },
        "curated_bank": [optional templates]
    }
    
    Returns:
    {
        "session_id": "...",
        "activities": [...],
        "stats": {
            "bank_count": N,
            "ai_count": M,
            "repaired_count": R,
            "elapsed_ms": T
        }
    }
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        data = request.get_json(silent=True) or {}
        
        # Extract players
        player_a_data = data.get('player_a', {})
        player_b_data = data.get('player_b', {})
        
        # Get or create profiles
        if 'submission_id' in player_a_data:
            profile_a = repository.get_or_create_profile(player_a_data['submission_id'])
            player_a_profile = profile_a.to_dict()
        else:
            player_a_profile = player_a_data
            profile_a = None
        
        if 'submission_id' in player_b_data:
            profile_b = repository.get_or_create_profile(player_b_data['submission_id'])
            player_b_profile = profile_b.to_dict()
        else:
            player_b_profile = player_b_data
            profile_b = None
        
        # Flatten nested activities structure for scoring
        # Profile activities are nested: {category: {activity: score}}
        # We need flat: {activity: score}
        def flatten_activities(activities_dict):
            flat = {}
            if not activities_dict or not isinstance(activities_dict, dict):
                return {}
            
            for category, items in activities_dict.items():
                if isinstance(items, dict):
                    # Nested structure - flatten it
                    for activity_key, score in items.items():
                        # KEEP directional suffixes (_give/_receive) for accurate matching
                        flat[activity_key] = score if isinstance(score, (int, float)) else 0.5
                else:
                    # Already flat
                    flat[category] = items if isinstance(items, (int, float)) else 0.5
            return flat
        
        player_a_profile['activities'] = flatten_activities(player_a_profile.get('activities', {}))
        player_b_profile['activities'] = flatten_activities(player_b_profile.get('activities', {}))
        
        # Extract session config
        session_config = data.get('session', {})
        rating = session_config.get('rating', settings.ATTUNED_DEFAULT_RATING)
        target_activities = session_config.get('target_activities', settings.ATTUNED_DEFAULT_TARGET_ACTIVITIES)
        bank_ratio = session_config.get('bank_ratio', settings.ATTUNED_DEFAULT_BANK_RATIO)
        activity_type = session_config.get('activity_type', 'random')
        rules = session_config.get('rules', {'avoid_maybe_until': 6})
        session_id = session_config.get('session_id')
        
        # Collect hard limits (boundaries)
        a_hard_limits = player_a_profile.get('boundaries', {}).get('hard_limits', [])
        b_hard_limits = player_b_profile.get('boundaries', {}).get('hard_limits', [])
        all_hard_limits = list(set(a_hard_limits + b_hard_limits))
        
        # Extract anatomy data from profiles
        a_anatomy = player_a_profile.get('anatomy', {})
        b_anatomy = player_b_profile.get('anatomy', {})
        
        player_anatomy = {
            'active_anatomy': a_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts']),
            'partner_anatomy': b_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts'])
        }
        
        # Determine session mode (couples by default, groups if specified in session config)
        session_mode = session_config.get('session_mode', 'couples')
        
        logger.info(
            f"Starting recommendations generation",
            extra={
                "request_id": request_id,
                "rating": rating,
                "target_activities": target_activities,
                "activity_type": activity_type,
                "session_mode": session_mode,
                "hard_limits_count": len(all_hard_limits),
                "player_a_anatomy": player_anatomy['active_anatomy'],
                "player_b_anatomy": player_anatomy['partner_anatomy']
            }
        )
        
        # Create or get session
        if session_id:
            session = repository.get_session(session_id)
            if not session and profile_a and profile_b:
                session = repository.create_session(
                    profile_a.id, profile_b.id, rating, activity_type,
                    target_activities, bank_ratio, rules, session_id
                )
        elif profile_a and profile_b:
            session = repository.create_session(
                profile_a.id, profile_b.id, rating, activity_type,
                target_activities, bank_ratio, rules
            )
            session_id = session.session_id
        else:
            session_id = str(uuid.uuid4())
            session = None
        
        # Generate activities
        activities = []
        truth_count = 0
        dare_count = 0
        bank_count = 0
        ai_count = 0
        repaired_count = 0
        used_activity_ids = set()  # Track used bank activity IDs
        used_fallback_keys = set()  # Track used fallback templates by (type, intensity)
        
        for seq in range(1, target_activities + 1):
            # 1. Pick type (truth or dare)
            picked_type = pick_type_balanced(seq, target_activities, truth_count, dare_count, activity_type)
            
            # 2. Get intensity window (rating-aware)
            intensity_min, intensity_max = get_intensity_window(seq, target_activities, rating)
            
            # 3. Determine actor FIRST (before candidate selection for correct anatomy filtering)
            actor = 'A' if seq % 2 == 1 else 'B'
            partner = 'B' if actor == 'A' else 'A'
            
            # 4. Create dynamic anatomy mapping based on which player is active
            # This ensures anatomy requirements are checked against the correct player
            if actor == 'A':
                current_player_anatomy = {
                    'active_anatomy': a_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts']),
                    'partner_anatomy': b_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts'])
                }
            else:  # actor == 'B'
                current_player_anatomy = {
                    'active_anatomy': b_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts']),
                    'partner_anatomy': a_anatomy.get('anatomy_self', ['penis', 'vagina', 'breasts'])
                }
            
            # 5. Try to find from bank FIRST (bank-first priority, fallback as last resort)
            activity_item = None
            
            # Always try bank first (removed bank_ratio limitation)
            best_candidate = repository.find_best_activity_candidate(
                rating=rating,
                intensity_min=intensity_min,
                intensity_max=intensity_max,
                activity_type=picked_type,
                player_a_profile=player_a_profile,
                player_b_profile=player_b_profile,
                session_mode=session_mode,
                player_boundaries=all_hard_limits,
                player_anatomy=current_player_anatomy,  # Use dynamic anatomy for this step
                excluded_ids=used_activity_ids,  # Prevent duplicates
                top_n=30  # Consider top 30 candidates for better variety
            )
            
            if best_candidate:
                # Mark this activity as used
                used_activity_ids.add(best_candidate.activity_id)
                
                # Actor already determined above - just use it
                # Update script with the actor
                script = best_candidate.script.copy() if best_candidate.script else {'steps': []}
                if script.get('steps'):
                    for step in script['steps']:
                        step['actor'] = actor
                
                activity_item = {
                    'id': f'bank_{best_candidate.activity_id}',
                    'seq': seq,
                    'type': best_candidate.type,
                    'rating': best_candidate.rating,
                    'intensity': best_candidate.intensity,
                    'roles': {'active_player': actor, 'partner_player': partner},
                    'script': script,
                    'tags': best_candidate.tags or [],
                    'power_role': best_candidate.power_role,
                    'preference_keys': best_candidate.preference_keys or [],
                    'domains': best_candidate.domains or [],
                    'hard_boundaries': best_candidate.hard_boundaries or [],
                    'provenance': {
                        'source': 'bank',
                        'template_id': best_candidate.activity_id
                    },
                    'checks': {
                        'respects_hard_limits': True,
                        'uses_yes_overlap': True,
                        'maybe_items_present': False,
                        'anatomy_ok': True,
                        'power_alignment': True,  # Verified by scoring
                        'notes': 'Selected via preference scoring'
                    }
                }
                bank_count += 1
            
            # 4. If no bank activity, use AI generation or fallback (last resort)
            if not activity_item:
                # For now, use safe fallback instead of calling Groq for each activity
                # TODO: Implement batch AI generation or per-activity AI calls
                fallback = get_safe_fallback(
                    picked_type, seq, rating, intensity_min, intensity_max,
                    used_fallback_keys  # Prevent fallback duplicates
                )
                
                if fallback:
                    activity_item = {
                        'id': f'fallback_{seq}',
                        'seq': seq,
                        **fallback
                    }
                    ai_count += 1
                else:
                    # Last resort: placeholder
                    intensity = (intensity_min + intensity_max) // 2
                    activity_item = create_placeholder_activity(seq, picked_type, rating, intensity)
            
            # 5. Validate
            is_valid, error = check_activity_item(
                activity_item,
                seq,
                rating,
                rules.get('avoid_maybe_until', 6),
                all_hard_limits,
                target_activities
            )
            
            # 6. Repair if needed
            if not is_valid:
                logger.warning(f"Activity {seq} failed validation: {error}")
                
                # Try repair
                repaired = fast_repair(
                    activity_item, seq, rating, picked_type,
                    intensity_min, intensity_max,
                    [c.to_dict() for c in repository.find_activity_candidates(
                        rating, intensity_min, intensity_max, picked_type,
                        session_mode=session_mode,
                        player_boundaries=all_hard_limits,
                        player_anatomy=player_anatomy,
                        limit=20
                    )],
                    all_hard_limits,
                    used_fallback_keys,  # Pass tracking
                    used_activity_ids    # Pass tracking
                )
                
                if repaired:
                    # Extract only the needed fields from repaired activity
                    activity_item = {
                        'id': f'repaired_{seq}',
                        'seq': seq,
                        'type': repaired.get('type'),
                        'rating': repaired.get('rating'),
                        'intensity': repaired.get('intensity'),
                        'roles': repaired.get('roles', {'active_player': 'A', 'partner_player': 'B'}),
                        'script': repaired.get('script'),
                        'tags': repaired.get('tags', []),
                        'power_role': repaired.get('power_role'),
                        'preference_keys': repaired.get('preference_keys', []),
                        'domains': repaired.get('domains', []),
                        'hard_boundaries': repaired.get('hard_boundaries', []),
                        'provenance': repaired.get('provenance', {'source': 'bank', 'template_id': None}),
                        'checks': repaired.get('checks', {})
                    }
                    repaired_count += 1
                else:
                    # Keep the failed item but log it
                    logger.error(f"Could not repair activity {seq}")
            
            # 7. Check for duplicates before adding (safety net)
            activity_text = activity_item['script']['steps'][0]['do']
            existing_texts = [a['script']['steps'][0]['do'] for a in activities]
            
            if activity_text in existing_texts:
                logger.warning(
                    f"Duplicate activity detected at seq {seq}: {activity_text[:50]}...",
                    extra={"request_id": request_id, "seq": seq}
                )
                # Skip this duplicate and try to get another
                continue
            
            # 8. Add to list
            activities.append(activity_item)
            
            # Update counters
            if activity_item['type'] == 'truth':
                truth_count += 1
            else:
                dare_count += 1
        
        # Save activities to database
        if session:
            repository.save_session_activities(session_id, activities)
            repository.update_session_progress(session_id, target_activities, truth_count, dare_count)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Recommendations generated successfully",
            extra={
                "request_id": request_id,
                "session_id": session_id,
                "activity_count": len(activities),
                "bank_count": bank_count,
                "ai_count": ai_count,
                "repaired_count": repaired_count,
                "elapsed_ms": elapsed_ms
            }
        )
        
        return jsonify({
            'session_id': session_id,
            'activities': activities,
            'stats': {
                'total': len(activities),
                'truths': truth_count,
                'dares': dare_count,
                'bank_count': bank_count,
                'ai_count': ai_count,
                'repaired_count': repaired_count,
                'elapsed_ms': elapsed_ms
            }
        }), 200
    
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}", extra={"request_id": request_id})
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Recommendation generation failed: {str(e)}", extra={"request_id": request_id})
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@bp.route("/recommendations/<session_id>", methods=["GET"])
def get_recommendations(session_id):
    """Get activities for a session."""
    try:
        session = repository.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        activities = repository.get_session_activities(session_id)
        
        return jsonify({
            'session_id': session_id,
            'session': session.to_dict(),
            'activities': [a.to_dict() for a in activities]
        }), 200
    
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}")
        return jsonify({'error': str(e)}), 500


@bp.route("/compatibility", methods=["POST"])
def calculate_and_store_compatibility():
    """
    Calculate and store compatibility between two players.
    
    Request body:
    {
        "submission_id_a": "...",
        "submission_id_b": "..."
    }
    
    Returns compatibility result and stores in database.
    """
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        data = request.get_json(silent=True) or {}
        
        submission_id_a = data.get('submission_id_a')
        submission_id_b = data.get('submission_id_b')
        
        if not submission_id_a or not submission_id_b:
            return jsonify({'error': 'Both submission_id_a and submission_id_b are required'}), 400
        
        # Get or create profiles
        profile_a = repository.get_or_create_profile(submission_id_a)
        profile_b = repository.get_or_create_profile(submission_id_b)
        
        logger.info(
            f"Calculating compatibility",
            extra={
                "request_id": request_id,
                "profile_a_id": profile_a.id,
                "profile_b_id": profile_b.id
            }
        )
        
        # Calculate compatibility
        result = calculate_compatibility(profile_a.to_dict(), profile_b.to_dict())
        
        # Store in database
        compatibility = repository.save_compatibility_result(
            profile_a.id,
            profile_b.id,
            result
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Compatibility calculated and stored",
            extra={
                "request_id": request_id,
                "compatibility_id": compatibility.id,
                "score": result['overall_compatibility']['score'],
                "elapsed_ms": elapsed_ms
            }
        )
        
        return jsonify({
            **result,
            'players': [profile_a.submission_id, profile_b.submission_id],
            'timestamp': compatibility.created_at.isoformat(),
            'elapsed_ms': elapsed_ms
        }), 200
    
    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}", extra={"request_id": request_id})
        return jsonify({'error': str(e)}), 400
    
    except Exception as e:
        logger.error(f"Compatibility calculation failed: {str(e)}", extra={"request_id": request_id})
        db.session.rollback()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500


@bp.route("/compatibility/<submission_id_a>/<submission_id_b>", methods=["GET"])
def get_compatibility(submission_id_a, submission_id_b):
    """
    Get stored compatibility result, or calculate if not exists.
    """
    try:
        # Get profiles
        profile_a = repository.get_profile_by_submission(submission_id_a)
        profile_b = repository.get_profile_by_submission(submission_id_b)
        
        if not profile_a or not profile_b:
            return jsonify({'error': 'One or both profiles not found'}), 404
        
        # Try to get existing result
        compatibility = repository.get_compatibility_result(profile_a.id, profile_b.id)
        
        if compatibility:
            # Return cached result
            logger.info(f"Returning cached compatibility for {profile_a.id} and {profile_b.id}")
            return jsonify(compatibility.to_dict()), 200
        
        # Calculate new result
        logger.info(f"No cached compatibility, calculating for {profile_a.id} and {profile_b.id}")
        result = calculate_compatibility(profile_a.to_dict(), profile_b.to_dict())
        
        # Store it
        compatibility = repository.save_compatibility_result(
            profile_a.id,
            profile_b.id,
            result
        )
        
        return jsonify(compatibility.to_dict()), 200
    
    except Exception as e:
        logger.error(f"Failed to get compatibility: {str(e)}")
        return jsonify({'error': str(e)}), 500

