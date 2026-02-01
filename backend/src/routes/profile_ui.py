
from flask import Blueprint, jsonify, current_app
from ..models.user import User
from ..models.survey import SurveySubmission
from ..models.profile import Profile
from ..scoring.profile import calculate_profile
from ..scoring.display_names import (
    DOMAIN_DISPLAY_NAMES,
    ACTIVITY_SECTION_DISPLAY_NAMES,
    ACTIVITY_DISPLAY_NAMES,
    POWER_ORIENTATION_DISPLAY_NAMES
)
from ..middleware.auth import token_required
import logging
import uuid
from sqlalchemy.exc import DataError

logger = logging.getLogger(__name__)

bp = Blueprint("profile_ui", __name__, url_prefix="/api/users")
profile_ui_bp = bp

@bp.route("/profile-ui", methods=["GET"])
@token_required
def get_profile_ui(current_user_id):
    try:
        try:
            user_uuid = uuid.UUID(current_user_id)
        except ValueError:
             return jsonify({'error': 'Invalid User ID token'}), 400

        # 1. Fetch User
        user = User.query.get(user_uuid)
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 2. Fetch Latest Profile
        # We query the Profile table directly as it contains the derived data
        profile = Profile.query.filter_by(user_id=user_uuid).order_by(Profile.created_at.desc()).first()
        
        if not profile:
            return jsonify({"error": "No profile found"}), 404

        # 3. Use Profile Data
        # The profile object already has the derived data as attributes/columns
        derived = {
            'arousal_propensity': profile.arousal_propensity,
            'power_dynamic': profile.power_dynamic,
            'domain_scores': profile.domain_scores,
            'activities': profile.activities,
            'boundaries': profile.boundaries
        }

        # 3. Transform Data for UI

        # --- Arousal Charts ---
        arousal = derived.get('arousal_propensity', {})
        arousal_ui = {
            "sexual_excitation": arousal.get('sexual_excitation', 0.0),
            "inhibition_performance": arousal.get('inhibition_performance', 0.0),
            "inhibition_consequence": arousal.get('inhibition_consequence', 0.0)
        }

        # --- Power Dynamic ---
        power = derived.get('power_dynamic', {})
        top_score = power.get('top_score', 0)
        bottom_score = power.get('bottom_score', 0)
        total_power = top_score + bottom_score
        
        # Calculate percentages for slider (avoid div by zero)
        if total_power > 0:
            top_pct = int((top_score / total_power) * 100)
            bottom_pct = 100 - top_pct
        else:
            top_pct = 50
            bottom_pct = 50

        orientation = power.get('orientation', 'Switch')
        power_ui = {
            "label": POWER_ORIENTATION_DISPLAY_NAMES.get(orientation, orientation),
            "top_percentage": top_pct,
            "bottom_percentage": bottom_pct,
            "confidence": power.get('interpretation', '')
        }

        # --- Domain Radar ---
        domains = derived.get('domain_scores', {})
        domain_ui = []
        
        # Desired Order: Sensation > Power > Connection > Exploration > Verbal
        ordered_keys = ['sensation', 'power', 'connection', 'exploration', 'verbal']
        
        for key in ordered_keys:
            score = domains.get(key, 0)
            display_name = DOMAIN_DISPLAY_NAMES.get(key, key.title())
            domain_ui.append({
                "domain": display_name,
                "score": score
            })

        # --- Boundaries ---
        boundaries_data = derived.get('boundaries', {})
        hard_limits = boundaries_data.get('hard_limits', [])
        if not hard_limits:
            boundaries_ui = ["No hard limits listed"]
        else:
            boundaries_ui = hard_limits

        # --- Interests (Activities) ---
        activities = derived.get('activities', {})
        interests_ui = []

        # Iterate through defined sections to maintain logical grouping (Survey Order)
        # ACTIVITY_SECTION_DISPLAY_NAMES is defined in survey order
        for section_key, section_name in ACTIVITY_SECTION_DISPLAY_NAMES.items():
            section_items = activities.get(section_key, {})
            tags = []

            # Process items in this section
            for act_key, score in section_items.items():
                if score > 0:  # Yes (1.0) or Maybe (0.5)
                    display_name = ACTIVITY_DISPLAY_NAMES.get(act_key, act_key.replace('_', ' ').title())
                    tags.append(display_name)
            
            # Sort tags alphabetically
            tags.sort()

            # Only add section if it has tags
            if tags:
                interests_ui.append({
                    "section": section_name,
                    "tags": tags
                })

        # 4. Construct Final Response
        response = {
            "user_id": str(user_uuid),
            "display_name": user.display_name,
            "submission_id": profile.submission_id,
            "general": {
                "arousal_profile": arousal_ui,
                "power": power_ui,
                "domains": domain_ui,
                "boundaries": boundaries_ui
            },
            "interests": interests_ui
        }

        return jsonify(response)

    except Exception as e:
        logger.exception(f"Error generating profile UI for user {current_user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
