from flask import Blueprint, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.survey import SurveySubmission
from ..models.profile import Profile
from ..models.user import User
from ..scoring.profile import calculate_profile
from ..db.repository import sync_user_anatomy_to_profile
from ..middleware.auth import internal_webhook_required

process_submission_bp = Blueprint('process_submission', __name__, url_prefix='/api/survey/submissions')


@process_submission_bp.route('/<submission_id>/process', methods=['POST'])
@internal_webhook_required
def process_submission(submission_id):
    """
    Process a raw survey submission to generate a profile.
    This endpoint is intended to be called by a database trigger/webhook
    when a new submission is inserted (e.g., from the mobile app).

    Security: Requires X-Internal-Secret header (INTERNAL_WEBHOOK_SECRET env var).
    """
    try:
        current_app.logger.info(f"Processing submission: {submission_id}")

        # 1. Fetch the submission
        submission = SurveySubmission.query.filter_by(submission_id=submission_id).first()
        if not submission:
            current_app.logger.error(f"Submission not found: {submission_id}")
            return jsonify({'error': 'Submission not found'}), 404

        # 2. Check idempotency (if profile already exists)
        existing_profile = Profile.query.filter_by(submission_id=submission_id).first()
        if existing_profile:
            current_app.logger.info(f"Profile already exists for submission: {submission_id}")
            return jsonify({'message': 'Profile already exists', 'profile_id': existing_profile.id}), 200

        # 3. Extract Payload and User ID
        # FlutterFlow writes user_id directly to the column
        user_id = str(submission.user_id) if submission.user_id else None
        
        payload = submission.payload_json or {}
        answers = {}

        # Detect Payload Structure
        if 'answers' in payload:
            # Web Prototype structure
            answers = payload['answers']
        else:
            # FlutterFlow flat structure
            answers = payload
        
        if not answers:
             current_app.logger.warning(f"No answers found in payload for submission: {submission_id}")

        # 4. Calculate Profile
        # We pass the submission_id as a fallback for user_id if needed by the calculator, 
        # though calculate_profile signature is (user_id, answers).
        # ideally we pass the actual user_id if we have it.
        calc_user_id = user_id if user_id else submission_id
        
        derived_profile = calculate_profile(calc_user_id, answers)

        # 5. Create Profile Record
        # We need to handle the anatomy carefully. 
        # If it's a mobile submission, anatomy might be missing from answers but present in User table.
        
        # Ensure anatomy has required structure for DB constraint
        anatomy = derived_profile.get('anatomy', {})
        if not anatomy or 'anatomy_self' not in anatomy:
            anatomy = {
                'anatomy_self': ['penis', 'vagina', 'breasts'],
                'anatomy_preference': ['penis', 'vagina', 'breasts']
            }

        profile = Profile(
            submission_id=submission_id,
            user_id=user_id, # Link to the user
            profile_version=derived_profile.get('profile_version', '0.4'),
            power_dynamic=derived_profile.get('power_dynamic', {}),
            arousal_propensity=derived_profile.get('arousal_propensity', {}),
            domain_scores=derived_profile.get('domain_scores', {}),
            activities=derived_profile.get('activities', {}),
            truth_topics=derived_profile.get('truth_topics', {}),
            boundaries=derived_profile.get('boundaries', {}),
            anatomy=anatomy,
            activity_tags=derived_profile.get('activity_tags', {})
        )

        db.session.add(profile)
        db.session.commit()
        
        current_app.logger.info(f"Profile created: {profile.id} for user: {user_id}")

        # 6. Sync Anatomy (Critical for Mobile)
        # If we have a user_id, we should sync anatomy to ensure the profile reflects 
        # the user's settings, especially if the survey didn't include anatomy questions (mobile flow).
        if user_id:
            sync_success = sync_user_anatomy_to_profile(user_id)
            if sync_success:
                 current_app.logger.info(f"Synced anatomy from user {user_id} to profile {profile.id}")
            else:
                 current_app.logger.warning(f"Failed to sync anatomy for user {user_id}")

        # 7. Update Submission Payload (Optional, for consistency)
        # We can write the derived data back to the submission payload so it looks like the web one
        if 'derived' not in payload:
             # Create a new payload dict to avoid mutating the existing one in place if it causes issues
             new_payload = dict(payload)
             new_payload['derived'] = derived_profile
             submission.payload_json = new_payload
             db.session.commit()

        return jsonify({
            'message': 'Profile processed successfully',
            'profile_id': profile.id,
            'user_id': user_id
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing submission {submission_id}: {str(e)}")
        return jsonify({'error': 'Processing failed'}), 500
