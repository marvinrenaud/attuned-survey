"""Compatibility routes for retrieving scores."""
from flask import Blueprint, jsonify, current_app
from sqlalchemy import or_
import uuid
import re

from ..extensions import db
from ..models.user import User
from ..models.profile import Profile
from ..models.compatibility import Compatibility
from .partners import PartnerConnection
from ..scoring.display_names import (
    DOMAIN_DISPLAY_NAMES,
    ACTIVITY_SECTION_DISPLAY_NAMES,
    ACTIVITY_DISPLAY_NAMES
)
from ..middleware.auth import token_required
import logging

logger = logging.getLogger(__name__)

compatibility_bp = Blueprint('compatibility', __name__, url_prefix='/api/compatibility')


@compatibility_bp.route('/<user_id>/<partner_id>', methods=['GET'])
@token_required
def get_compatibility(current_user_id, user_id, partner_id):
    try:
        logger.info(f"Compatibility request raw inputs - User: {repr(user_id)}, Partner: {repr(partner_id)}")
        
        # 0. Sanitize Inputs using Regex Extraction (Nuclear Option)
        # Finds a 32-char hex string (with optional dashes) anywhere in the input
        uuid_pattern = re.compile(r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}', re.IGNORECASE)
        
        def extract_uuid_safe(val, label):
            s_val = str(val)
            match = uuid_pattern.search(s_val)
            if not match:
                # Log the exact ascii values to debug hidden chars if this fails
                ascii_debug = [ord(c) for c in s_val]
                raise ValueError(f"No valid UUID pattern found in input. Ascii: {ascii_debug}")
            return uuid.UUID(match.group())

        try:
            u_uuid = extract_uuid_safe(user_id, "User")
            p_uuid = extract_uuid_safe(partner_id, "Partner")
            
            # Canonical strings for querying PartnerConnection (model uses String)
            u_str = str(u_uuid)
            p_str = str(p_uuid)
            
        except ValueError as val_err:
             logger.error(f"Invalid UUID input: User='{user_id}', Partner='{partner_id}'. Error: {val_err}")
             return jsonify({'error': f"Invalid UUID format: {str(val_err)}", 'received_user': str(user_id), 'received_partner': str(partner_id)}), 400

        # Verify Authorization
        auth_uid_str = str(current_user_id)
        if auth_uid_str != str(u_uuid) and auth_uid_str != str(p_uuid):
             return jsonify({'error': 'Unauthorized access to compatibility data'}), 403
             
        # 1. Verify connection exists (active or accepted)
        # Use sanitized strings to prevent "invalid input syntax" DB errors
        connection = PartnerConnection.query.filter(
            or_(
                (PartnerConnection.requester_user_id == u_str) & (PartnerConnection.recipient_user_id == p_str),
                (PartnerConnection.requester_user_id == p_str) & (PartnerConnection.recipient_user_id == u_str)
            )
        ).filter_by(status='accepted').first()
        
        if not connection:
            return jsonify({'error': 'No active connection found'}), 403
            
        # 2. Get Partner's settings
        partner = User.query.filter_by(id=p_uuid).first()
        if not partner:
            return jsonify({'error': 'Partner not found'}), 404
            
        sharing_setting = partner.profile_sharing_setting
        
        # 3. Fetch Compatibility Record
        # Determine order (lower ID first)
        req_profile = Profile.query.filter_by(user_id=u_uuid).order_by(Profile.created_at.desc()).first()
        partner_profile = Profile.query.filter_by(user_id=p_uuid).order_by(Profile.created_at.desc()).first()
        
        if not req_profile or not partner_profile:
             return jsonify({'error': 'Profiles not found'}), 404
             
        if req_profile.id < partner_profile.id:
            p1, p2 = req_profile.id, partner_profile.id
        else:
            p1, p2 = partner_profile.id, req_profile.id
            
        compat_record = Compatibility.query.filter_by(player_a_id=p1, player_b_id=p2).first()
        
        if not compat_record:
            return jsonify({'error': 'Compatibility not calculated yet'}), 404
            
        # 4. Construct Response based on Privacy Settings
        
        # Base response (Always allowed)
        response = {
            'overall_compatibility': {
                'score': compat_record.overall_percentage,
                'interpretation': compat_record.interpretation
            },
            'sharing_setting': sharing_setting,
            'calculation_date': compat_record.created_at.isoformat()
        }
        
        # Logic for "demographics_only"
        # - Hide breakdown
        # - Hide detailed lists
        # - Show only basic score
        if sharing_setting == 'demographics_only':
            return jsonify(response), 200
            
        # Logic for "overlapping_only" and "all_responses" (MVP treatment: currently treated similarly for score breakdown)
        # Detailed breakdown is allowed
        response['breakdown'] = compat_record.breakdown or {}
        response['mutual_activities'] = compat_record.mutual_activities or []
        response['growth_opportunities'] = compat_record.growth_opportunities or []
        
        # Mutual truth topics logic
        # If partner shares ONLY overlapping, we show mutual truth topics (as they are by definition overlapping)
        # If partner shares ALL, we definitely show them.
        response['mutual_truth_topics'] = compat_record.mutual_truth_topics or []
        
        # Blocked / Conflicts
        # These inherently reveal partner's hard limits.
        # "overlapping_only" -> usually implies positive overlap. Conflicts might be sensitive.
        # However, for a functional app, knowing hard limit conflicts is critical for safety.
        # We will assume conflicts are shared in Overlapping mode for safety reasons, unless explicitly forbidden.
        # Given prompt constraints ("strict enforcement"), let's be safe:
        # If overlapping_only, maybe we mask the specific limit name if it's too sensitive? 
        # But the plan said "Return Score, breakdown, and filtered partner_profile".
        # Let's include conflicts as they are "interactions" between the two users.
        response['blocked_activities'] = compat_record.blocked_activities or []
        response['boundary_conflicts'] = compat_record.boundary_conflicts or []
        
        # 5. Add Partner Profile Snippet (Filtered)
        # Using existing get_partner_profile logic re-use or simplified fetch?
        # The prompt asked for "Partner survey details only if permitted".
        # We can re-use the logic from profile_sharing.py or just let the frontend call that separately.
        # The PROMPT Requirement: "The frontend needs to display... The frontend will also show each partners full intimacy profile results if the user has it set that way"
        # Since we are building an API, we can leave the Full Profile fetch to the existing `partner-profile` endpoint to keep this response clean,
        # OR we can embed a summary. 
        # Let's embed the 'derived' profile summary if allowed, to save a roundtrip.
        
        if sharing_setting == 'all_responses':
            response['partner_profile'] = partner_profile.to_dict()
        elif sharing_setting == 'overlapping_only':
             # Filter activities to only ones where both > 0.5
             # Reuse identifying logic?
             # For now, let's keep it lightweight. The frontend can fetch the full overlapping profile from generic endpoint.
             # We will just return the compatibility data here as requested by "Compatibility API" section.
             pass
             
        return jsonify(response), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Get compatibility failed: {str(e)}")
        return jsonify({'error': 'Failed to retrieve compatibility'}), 500


@compatibility_bp.route('/<user_id>/<partner_id>/ui', methods=['GET'])
@token_required
def get_compatibility_ui(current_user_id, user_id, partner_id):
    """
    UI-Optimized Compatibility Endpoint.
    - Flattens structure for frontend.
    - Ensures Null Safety (0 for ints, [] for lists).
    - Enforces strict visualization order (Radar Chart).
    - Performs smart interest matching (Giving vs Receiving).
    """
    try:
        logger.info(f"Compatibility UI request for {repr(user_id)} and {repr(partner_id)}")
        
        # 0. Sanitize Inputs (Reuse Logic)
        # Finds a 32-char hex string (with optional dashes) anywhere in the input
        uuid_pattern = re.compile(r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}', re.IGNORECASE)
        
        def extract_uuid_safe(val):
            s_val = str(val)
            match = uuid_pattern.search(s_val)
            if not match:
                raise ValueError(f"No valid UUID pattern found")
            return uuid.UUID(match.group())

        try:
            u_uuid = extract_uuid_safe(user_id)
            p_uuid = extract_uuid_safe(partner_id)
            u_str = str(u_uuid)
            p_str = str(p_uuid)
        except ValueError as val_err:
             return jsonify({'error': f"Invalid UUID format"}), 400

        # Verify Authorization
        auth_uid_str = str(current_user_id)
        if auth_uid_str != str(u_uuid) and auth_uid_str != str(p_uuid):
             return jsonify({'error': 'Unauthorized access to compatibility data'}), 403

        # 1. Fetch Users
        user_u = User.query.get(u_uuid)
        user_p = User.query.get(p_uuid)
        
        if not user_u or not user_p:
             return jsonify({'error': 'Users not found'}), 404

        # 2. Fetch Latest Profiles
        p_u_profile = Profile.query.filter_by(user_id=u_uuid).order_by(Profile.created_at.desc()).first()
        p_p_profile = Profile.query.filter_by(user_id=p_uuid).order_by(Profile.created_at.desc()).first()
        
        if not p_u_profile or not p_p_profile:
             return jsonify({'error': 'Profiles not found'}), 404

        # 3. Fetch Compatibility Record
        if p_u_profile.id < p_p_profile.id:
            p1, p2 = p_u_profile.id, p_p_profile.id
        else:
            p1, p2 = p_p_profile.id, p_u_profile.id
            
        compat_record = Compatibility.query.filter_by(player_a_id=p1, player_b_id=p2).first()
        
        if not compat_record:
            return jsonify({'error': 'Compatibility not calculated yet'}), 404

        # 4. Prepare Data
        # Flatten derived data from profiles
        # Note: We duplicate some logic from profile_ui to ensure stability without refactoring
        
        # Helper to get safe int/float
        def safe_val(val, default=0):
            return val if val is not None else default

        # --- A. Partner Profile (Mirrored UI Schema) ---
        # Only show if allowed, but structure must exist (empty if restricted)
        sharing_setting = user_p.profile_sharing_setting
        
        partner_ui_profile = _transform_profile_for_ui(p_p_profile, user_p, sharing_setting)
        
        # --- B. Comparison Data ---
        
        # Domains Radar - Critical Order
        # Strict order: Sensation, Connection, Power, Exploration, Verbal
        # Map internal keys to this order
        domain_keys_ordered = ['sensation', 'connection', 'power', 'exploration', 'verbal']
        u_domains = p_u_profile.domain_scores or {}
        p_domains = p_p_profile.domain_scores or {}
        
        comparison_domains = []
        for key in domain_keys_ordered:
            display_name = DOMAIN_DISPLAY_NAMES.get(key, key.title())
            # Apply privacy to partner score
            p_score = safe_val(p_domains.get(key, 0))
            if sharing_setting == 'demographics_only':
                p_score = 0
            
            comparison_domains.append({
                "domain": display_name,
                "user_score": safe_val(u_domains.get(key, 0)),
                "partner_score": p_score
            })

        # Comparison Scores (Flattened Breakdown)
        # Handle privacy for scores? Usually scores are shared unless Demographics Only.
        # Demographics Only -> show overall only?
        # Requirement: "If data is restricted, return an empty state (e.g., 0 or [])"
        breakdown = compat_record.breakdown or {}
        if sharing_setting == 'demographics_only':
             breakdown = {}

        comparison_scores = {
            "overall_score": compat_record.overall_percentage,
            "power_score": safe_val(breakdown.get('power_complement', 0)),
            "domain_score": safe_val(breakdown.get('domain_similarity', 0)),
            "activity_score": safe_val(breakdown.get('activity_overlap', 0)),
            "truth_score": safe_val(breakdown.get('truth_overlap', 0))
        }
        
        # Power Overlap
        # Re-calculate simple labels
        u_power = p_u_profile.power_dynamic or {}
        p_power = p_p_profile.power_dynamic or {}
        
        power_overlap = {
            "user_label": u_power.get('orientation', 'Switch'),
            "partner_label": p_power.get('orientation', 'Switch') if sharing_setting != 'demographics_only' else "Hidden",
            "complement_score": safe_val(breakdown.get('power', 0))
        }

        # Flattened Arousal Comparison
        u_arousal = p_u_profile.arousal_propensity or {}
        p_arousal = p_p_profile.arousal_propensity or {}
        
        arousal_comparison = {
            "user_sexual_excitation": safe_val(u_arousal.get('sexual_excitation', 0)),
            "user_inhibition_performance": safe_val(u_arousal.get('inhibition_performance', 0)),
            "user_inhibition_consequence": safe_val(u_arousal.get('inhibition_consequence', 0)),
            "partner_sexual_excitation": safe_val(p_arousal.get('sexual_excitation', 0)) if sharing_setting != 'demographics_only' else 0,
            "partner_inhibition_performance": safe_val(p_arousal.get('inhibition_performance', 0)) if sharing_setting != 'demographics_only' else 0,
            "partner_inhibition_consequence": safe_val(p_arousal.get('inhibition_consequence', 0)) if sharing_setting != 'demographics_only' else 0
        }

        # Interests Comparison (Smart Matching)
        interests_comp = []
        if sharing_setting != 'demographics_only':
            interests_comp = _compare_interests(
                p_u_profile.activities or {},
                p_u_profile.boundaries or {},
                p_p_profile.activities or {},
                p_p_profile.boundaries or {},
                sharing_setting == 'overlapping_only'
            )

        # 5. Final Assembly
        response = {
            "compatibility_summary": {
                "overall_score": compat_record.overall_percentage,
                "interpretation": compat_record.interpretation,
                "sharing_setting": sharing_setting,
                "comparison_scores": comparison_scores
            },
            "comparison_data": {
                "domains": comparison_domains,
                "power_overlap": power_overlap,
                "arousal": arousal_comparison
            },
            "interests_comparison": interests_comp,
            "partner_profile": partner_ui_profile
        }
        
        return jsonify(response), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Get compatibility UI failed: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def _transform_profile_for_ui(profile, user, sharing_setting):
    """
    Transforms profile into UI schema.
    Applies privacy: if restricted, returns empty structs, not nulls.
    """
    # Defaults
    arousal_ui = {"sexual_excitation": 0.0, "inhibition_performance": 0.0, "inhibition_consequence": 0.0}
    power_ui = {"label": "Hidden", "top_percentage": 50, "bottom_percentage": 50, "confidence": ""}
    domain_ui = []
    boundaries_ui = []
    interests_ui = []

    if sharing_setting == 'demographics_only':
        # Return skeleton
        pass
    else:
        # 1. Arousal
        arousal = profile.arousal_propensity or {}
        arousal_ui = {
            "sexual_excitation": arousal.get('sexual_excitation', 0.0),
            "inhibition_performance": arousal.get('inhibition_performance', 0.0),
            "inhibition_consequence": arousal.get('inhibition_consequence', 0.0)
        }
        
        # 2. Power
        power = profile.power_dynamic or {}
        top = power.get('top_score', 0)
        btm = power.get('bottom_score', 0)
        total = top + btm
        if total > 0:
            top_pct = int((top/total)*100)
        else:
            top_pct = 50
        power_ui = {
            "label": power.get('orientation', 'Switch'),
            "top_percentage": top_pct,
            "bottom_percentage": 100 - top_pct,
            "confidence": power.get('interpretation', '')
        }
        
        # 3. Domains
        domains = profile.domain_scores or {}
        for key in ['sensation', 'connection', 'power', 'exploration', 'verbal']: # Use same order
             display = DOMAIN_DISPLAY_NAMES.get(key, key.title())
             domain_ui.append({"domain": display, "score": domains.get(key, 0)})
             
        # 4. Boundaries
        # In Overlapping Only, do we show full hard limits? 
        # "Safety is critical". We'll list them unless prohibited.
        # But for UI safety, if overlapping_only, usually we only show what matches.
        # The prompt said "If data is restricted, return empty state".
        # Let's assume for partner_profile snippet, overlapping_only hides non-shared info.
        # But this is "Self" view of "Partner".
        # We'll leave boundaries empty for overlapping_only to be conservative, 
        # they appear in "conflict" check anyway.
        if sharing_setting == 'all_responses':
            bounds = profile.boundaries or {}
            boundaries_ui = bounds.get('hard_limits', [])

        # 5. Interests
        # For Partner Profile UI, we only show what is allowed.
        # If overlapping_only, we probably shouldn't show their full list here, 
        # only the comparison list.
        # So we keep this empty for overlapping_only.
        if sharing_setting == 'all_responses':
            acts = profile.activities or {}
            for section_key, section_name in ACTIVITY_SECTION_DISPLAY_NAMES.items():
                section_items = acts.get(section_key, {})
                tags = []
                for k, v in section_items.items():
                    if v > 0:
                        tags.append(ACTIVITY_DISPLAY_NAMES.get(k, k.replace('_', ' ').title()))
                tags.sort()
                if tags:
                    interests_ui.append({"section": section_name, "tags": tags})

    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "submission_id": str(profile.submission_id),
        "general": {
            "arousal_profile": arousal_ui,
            "power": power_ui,
            "domains": domain_ui,
            "boundaries": boundaries_ui
        },
        "interests": interests_ui    
    }

def _compare_interests(u_acts, u_bounds, p_acts, p_bounds, overlapping_only):
    """
    Generates comparison list with Smart Matching & Conflicts.
    
    Returns tags with:
    - status: 'mutual', 'conflict', 'user_only', 'partner_only'
    - compatible: True if directional activities align (give/receive cross-match)
    """
    results = []
    
    # Normalize hard limits to lowercase for easier matching
    # Limits might be stored as "Spanking" or "massage".
    u_hard = {str(h).lower() for h in u_bounds.get('hard_limits', [])}
    p_hard = {str(h).lower() for h in p_bounds.get('hard_limits', [])}

    for section_key, section_name in ACTIVITY_SECTION_DISPLAY_NAMES.items():
        u_section = u_acts.get(section_key, {})
        p_section = p_acts.get(section_key, {})
        
        # Collect all unique keys appearing in either
        all_keys = set(u_section.keys()) | set(p_section.keys())
        
        section_tags = []
        
        # We need to handle "Giving" vs "Receiving" pairs to avoid double counting
        processed_keys = set()
        
        sorted_keys = sorted(list(all_keys))
        
        for k in sorted_keys:
            if k in processed_keys:
                continue
            
            u_score = u_section.get(k, 0)
            p_score = p_section.get(k, 0)
            
            # Smart Match Logic
            base = k
            complement = None
            is_receive = k.endswith('_receive')
            is_give = k.endswith('_give')
            is_directional = is_give or is_receive
            
            if is_receive:
                base = k[:-8] # strip _receive
                complement = f"{base}_give"
            elif is_give:
                base = k[:-5] # strip _give
                complement = f"{base}_receive"
            
            # Improved Fallback Formatting
            display_name = ACTIVITY_DISPLAY_NAMES.get(k, k.replace('_', ' ').title())
            
            # Status determination
            status = None

            # 1. Direct Conflict Logic
            # Normalize key and base for checking
            # We check if the OTHER person has any limit matching this activity
            
            # Check matches for Partner's limits (User likes 'k')
            if u_score > 0:
                # Does partner hate this?
                # Check raw key, base key, and display name
                checks = [k.lower(), base.lower(), base.replace('_', ' ').lower(), display_name.lower()]
                if any(c in p_hard for c in checks):
                    status = "conflict"

            # Check matches for User's limits (Partner likes 'k')
            if not status and p_score > 0:
                 checks = [k.lower(), base.lower(), base.replace('_', ' ').lower(), display_name.lower()]
                 if any(c in u_hard for c in checks):
                     status = "conflict"
            
            if not status:
                # 2. Smart Match
                if u_score > 0 and p_score > 0:
                    status = "mutual"
                elif complement and complement in p_section:
                    # Check cross match: User(Receive) & Partner(Give)
                    if u_score > 0 and p_section[complement] > 0:
                        status = "mutual"
                        # De-duplicate: Mark complement as processed so it's not listed again
                        processed_keys.add(complement)
            
            if not status:
                if u_score > 0:
                    status = "user_only"
                elif p_score > 0:
                    status = "partner_only"
            
            # Calculate compatibility (directional cross-match)
            # compatible=True means the activity can actually happen with both satisfied
            compatible = False
            
            if status == "conflict":
                # Hard limit conflict - never compatible
                compatible = False
            elif is_directional:
                # For directional activities, check if roles complement
                if is_give:
                    # This is a "give" activity - compatible if user wants to receive
                    receive_key = f"{base}_receive"
                    # Partner gives → User receives?
                    if p_score > 0 and u_section.get(receive_key, 0) > 0:
                        compatible = True
                    # User gives → Partner receives?
                    if u_score > 0 and p_section.get(receive_key, 0) > 0:
                        compatible = True
                elif is_receive:
                    # This is a "receive" activity - compatible if the other wants to give
                    give_key = f"{base}_give"
                    # Partner receives → User gives?
                    if p_score > 0 and u_section.get(give_key, 0) > 0:
                        compatible = True
                    # User receives → Partner gives?
                    if u_score > 0 and p_section.get(give_key, 0) > 0:
                        compatible = True
            else:
                # Non-directional activities: compatible if mutual
                compatible = (status == "mutual")
            
            if status:
                tag_data = {"name": display_name, "status": status, "compatible": compatible}
                
                # Privacy Filter
                if overlapping_only:
                    if status in ['mutual', 'conflict']:
                        section_tags.append(tag_data)
                    # Hide one-sided things
                else:
                    section_tags.append(tag_data)
            
            processed_keys.add(k)

        if section_tags:
            results.append({"section": section_name, "tags": section_tags})
            
    return results

