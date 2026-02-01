from datetime import datetime
import uuid
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..extensions import db, limiter
from ..models.survey import SurveySubmission, SurveyProgress
from ..models.profile import Profile
from ..models.user import User
from ..scoring.profile import calculate_profile
from ..middleware.auth import token_required
import logging

logger = logging.getLogger(__name__)

survey_submit_bp = Blueprint('survey_submit', __name__, url_prefix='/api/survey')


@survey_submit_bp.route('/submit', methods=['POST'])
@token_required
@limiter.limit("10 per hour")
def submit_survey(current_user_id):
    """
    Handle atomic survey submission.
    1. Validate User (JWT via decorator)
    2. Check Progress (Idempotency)
    3. Atomic Transaction:
       - Create Submission
       - Calculate & Create/Update Profile (Upsert)
       - Update Progress
       - Update User
    """
    try:
        user_id = current_user_id
        # Convert to UUID object for SQLAlchemy UUID(as_uuid=True) compatibility
        try:
             user_id = uuid.UUID(str(user_id))
        except ValueError:
             return jsonify({'error': 'Invalid user_id format'}), 400

        data = request.get_json() or {}
        survey_version = data.get('survey_version', '0.4')
        answers = data.get('answers') or {}

        # Basic Validation
        if not answers:
             return jsonify({'error': 'No answers provided'}), 400

        # 2. Fetch Progress First (Needed for FK)
        # We assume one active progress per version per user
        progress = SurveyProgress.query.filter_by(
            user_id=user_id, 
            survey_version=survey_version
        ).first()

        if not progress:
            # Edge case: User submitting without a progress record? 
            # Possible if they cleared cache or something, but backend should have it.
            # For now, return 404 as per plan.
            return jsonify({'error': 'No survey in progress found'}), 404

        retake = data.get('retake', False)

        # 3. Idempotency Guard
        # If already completed AND not a forced retake, return existing info
        if progress.status == 'completed' and not retake:
            logger.info(f"Duplicate submission attempt for user {user_id}")
            
            # Try to find the existing profile
            # We can look up by submission linked to this progress
            submission = SurveySubmission.query.filter_by(survey_progress_id=progress.id).first()
            if submission:
                existing_profile = Profile.query.filter_by(submission_id=submission.submission_id).first()
                if existing_profile:
                    return jsonify({
                        'message': 'Survey already completed',
                        'profile_id': existing_profile.id
                    }), 200
            
            # Fallback if we can't find the specific profile but status is completed
            return jsonify({'message': 'Survey already completed'}), 200
        
        if retake:
             logger.info(f"Processing survey retake for user {user_id}")

        # 4. Atomic Transaction
        with db.session.begin_nested():
            # A. Create Submission
            submission_id = str(uuid.uuid4())
            submission = SurveySubmission(
                submission_id=submission_id,
                user_id=user_id,
                survey_version=survey_version,
                survey_progress_id=progress.id,
                payload_json=answers,
                # Add metadata if available
                created_at=datetime.utcnow()
            )
            db.session.add(submission)
            db.session.flush() # Flush to ensure we can reference it if needed, though we generated ID manually

            # B. Calculate Profile
            # calculate_profile expects (user_id, answers)
            profile_data = calculate_profile(str(user_id), answers)

            # C. Create or Update Profile
            # Ensure anatomy is handled
            anatomy = profile_data.get('anatomy', {})
            if not anatomy:
                anatomy = {'anatomy_self': [], 'anatomy_preference': []}

            # Check for existing profile
            # We use lock or upsert pattern. Since we are in transaction, unique constraint will fail if we insert.
            # But we want to UPDATE if exists.
            
            existing_profile = Profile.query.filter_by(user_id=user_id).first()
            
            if existing_profile:
                # UPDATE existing profile
                existing_profile.submission_id = submission_id
                existing_profile.profile_version = profile_data.get('profile_version', '0.4')
                existing_profile.power_dynamic = profile_data.get('power_dynamic', {})
                existing_profile.arousal_propensity = profile_data.get('arousal_propensity', {})
                existing_profile.domain_scores = profile_data.get('domain_scores', {})
                existing_profile.activities = profile_data.get('activities', {})
                existing_profile.truth_topics = profile_data.get('truth_topics', {})
                existing_profile.boundaries = profile_data.get('boundaries', {})
                existing_profile.anatomy = anatomy
                existing_profile.activity_tags = profile_data.get('activity_tags', {})
                # Updated_at is handled by SQLAlchemy event or manually if needed, 
                # but default onupdate=datetime.utcnow should trigger.
                profile = existing_profile
            else:
                # INSERT new profile
                profile = Profile(
                    user_id=user_id,
                    submission_id=submission_id,
                    profile_version=profile_data.get('profile_version', '0.4'),
                    power_dynamic=profile_data.get('power_dynamic', {}),
                    arousal_propensity=profile_data.get('arousal_propensity', {}),
                    domain_scores=profile_data.get('domain_scores', {}),
                    activities=profile_data.get('activities', {}),
                    truth_topics=profile_data.get('truth_topics', {}),
                    boundaries=profile_data.get('boundaries', {}),
                    anatomy=anatomy,
                    activity_tags=profile_data.get('activity_tags', {})
                )
                db.session.add(profile)

            # D. Update Progress
            progress.status = 'completed'
            progress.completed_at = datetime.utcnow()
            # Ensure answers are updated to the final set
            progress.answers = answers 
            progress.completion_percentage = 100

            # E. Update User
            user = User.query.get(user_id)
            if user:
                user.onboarding_completed = True
                # Optional: Sync anatomy from profile to user if needed, 
                # but usually we sync User -> Profile. 
                # If this is the source of truth, maybe we should?
                # For now, stick to the plan: just update onboarding_completed.

        db.session.commit()
        
        logger.info(f"Survey submitted successfully for user {user_id}. Profile: {profile.id}")
        return jsonify({
            'message': 'Survey submitted successfully',
            'profile_id': profile.id
        }), 200

    except IntegrityError as e:
        # db.session.rollback() handled by begin_nested or request teardown
        logger.error(f"Integrity error in survey submit: {e}")
        return jsonify({'error': 'Database integrity error'}), 409
    except Exception as e:
        # db.session.rollback() handled by begin_nested or request teardown
        logger.exception(f"Error in survey submit: {e}")
        return jsonify({'error': 'Submission failed'}), 500
