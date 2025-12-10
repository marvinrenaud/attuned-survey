
from flask import Blueprint, jsonify, current_app
from ..models.user import User
from ..models.survey import SurveySubmission
from ..scoring.profile import calculate_profile
from ..scoring.display_names import (
    DOMAIN_DISPLAY_NAMES,
    ACTIVITY_SECTION_DISPLAY_NAMES,
    ACTIVITY_DISPLAY_NAMES
)

bp = Blueprint("profile_ui", __name__, url_prefix="/api/users")
profile_ui_bp = bp

@bp.route("/<user_id>/profile-ui", methods=["GET"])
def get_profile_ui(user_id):
    try:
        # 1. Fetch User and Submission
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        submission = SurveySubmission.query.filter_by(user_id=user_id).order_by(SurveySubmission.created_at.desc()).first()
        
        if not submission:
            return jsonify({"error": "No survey submission found"}), 404

        # 2. Get Derived Profile (use payload or calculate)
        derived = submission.payload_json.get('derived')
        if not derived:
            derived = calculate_profile(submission.submission_id, submission.payload_json.get('answers', {}))

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

        power_ui = {
            "label": power.get('orientation', 'Switch'),
            "top_percentage": top_pct,
            "bottom_percentage": bottom_pct,
            "confidence": power.get('interpretation', '')
        }

        # --- Domain Radar ---
        domains = derived.get('domain_scores', {})
        domain_ui = []
        for key, score in domains.items():
            display_name = DOMAIN_DISPLAY_NAMES.get(key, key.title())
            domain_ui.append({
                "domain": display_name,
                "score": score
            })
        # Sort domains alphabetically or by a fixed order? 
        # User didn't specify, but fixed order is usually better for radar charts.
        # Let's stick to the order in DOMAIN_DISPLAY_NAMES if possible, or just list them.
        # For now, list is fine.

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
            "user_id": user_id,
            "submission_id": submission.submission_id,
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
        current_app.logger.exception(f"Error generating profile UI for user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
