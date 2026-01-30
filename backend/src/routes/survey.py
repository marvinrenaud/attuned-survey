# backend/src/routes/survey.py
from datetime import datetime
import math
import uuid
from typing import Optional

from flask import Blueprint, jsonify, request
import logging
from ..middleware.auth import token_required, is_admin_user, require_admin, has_partner_relationship

logger = logging.getLogger(__name__)
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.survey import SurveyBaseline, SurveySubmission
from ..models.user import User
from ..scoring.profile import calculate_profile


bp = Blueprint("survey", __name__, url_prefix="/api/survey")


def sanitize_for_json(value):
    """Recursively replace NaN/Infinity so Flask can JSON encode data."""

    if isinstance(value, dict):
        return {key: sanitize_for_json(val) for key, val in value.items()}
    if isinstance(value, list):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, (tuple, set)):
        return [sanitize_for_json(item) for item in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0
    return value


def serialize_submission(submission: SurveySubmission) -> dict:
    payload = dict(submission.payload_json or {})
    if "sexual_orientation" in payload and "sexualOrientation" not in payload:
        payload["sexualOrientation"] = payload.get("sexual_orientation")
    payload.setdefault("id", submission.submission_id)
    payload.setdefault("createdAt", submission.created_at.isoformat())
    if submission.name is not None:
        payload.setdefault("name", submission.name)
    if submission.sex is not None:
        payload.setdefault("sex", submission.sex)
    if submission.sexual_orientation is not None:
        payload.setdefault("sexualOrientation", submission.sexual_orientation)
    

        
    return sanitize_for_json(payload)


def get_baseline_record(create: bool = False) -> Optional[SurveyBaseline]:
    baseline = SurveyBaseline.query.get(1)
    if baseline is None and create:
        baseline = SurveyBaseline(id=1)
        db.session.add(baseline)
    return baseline


@bp.route("/submissions", methods=["GET"])
@token_required
def get_submissions(current_user_id):
    """
    Get survey submissions.

    Security: Returns only the authenticated user's submissions.
    Admins can pass ?all=true to get all submissions.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)

        # Admin can request all submissions with ?all=true
        if request.args.get('all') == 'true' and is_admin_user(current_user_id):
            submissions = (
                SurveySubmission.query.order_by(SurveySubmission.created_at.asc()).all()
            )
        else:
            # Regular users only see their own submissions
            submissions = (
                SurveySubmission.query
                .filter_by(user_id=user_uuid)
                .order_by(SurveySubmission.created_at.asc())
                .all()
            )

        baseline_row = get_baseline_record()
        baseline_id = baseline_row.submission_id if baseline_row else None
        return jsonify(
            {
                "submissions": [serialize_submission(s) for s in submissions],
                "baseline": baseline_id,
            }
        )
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"get_submissions failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Failed to retrieve submissions"}), 500


@bp.route("/submissions", methods=["POST"])
@token_required
def create_submission(current_user_id):
    """
    Create a new survey submission.

    Security: Requires authentication. User ID is taken from JWT token,
    not from request body, to prevent spoofing.
    """
    try:
        # Use authenticated user ID (prevents spoofing)
        user_id_val = uuid.UUID(current_user_id)

        data = request.get_json(silent=True) or {}
        # Log minimal context for troubleshooting payload mismatches
        try:
            logger.info(
                "create_submission payload keys=%s name=%s sex=%s sexualOrientation=%s user=%s",
                list(data.keys()),
                data.get("name"),
                data.get("sex"),
                data.get("sexualOrientation") or data.get("sexual_orientation"),
                current_user_id,
            )
        except Exception:
            pass
        sanitized_submission = sanitize_for_json(data)

        submission_id = sanitized_submission.get("id")
        if not submission_id:
            submission_id = str(int(datetime.utcnow().timestamp() * 1000))
            sanitized_submission["id"] = submission_id

        name = sanitized_submission.get("name")
        sex = sanitized_submission.get("sex")
        sexual_orientation = sanitized_submission.get("sexualOrientation") or sanitized_submission.get(
            "sexual_orientation"
        )
        version = sanitized_submission.get("version")

        if sex is not None:
            sanitized_submission["sex"] = sex
        if sexual_orientation is not None:
            sanitized_submission["sexualOrientation"] = sexual_orientation
        sanitized_submission.pop("sexual_orientation", None)

        # Calculate profile server-side
        answers = sanitized_submission.get("answers", {})

        derived_profile = calculate_profile(submission_id, answers)
        sanitized_submission["derived"] = derived_profile

        submission = SurveySubmission(
            submission_id=submission_id,
            respondent_id=str(user_id_val),  # Use authenticated user ID
            user_id=user_id_val,
            name=name,
            sex=sex,
            sexual_orientation=sexual_orientation,
            survey_version=version,
            payload_json=sanitized_submission,
        )

        db.session.add(submission)
        db.session.flush()

        response_payload = serialize_submission(submission)
        if version is not None:
            response_payload["version"] = version

        # Ensure derived is in response
        response_payload["derived"] = derived_profile

        submission.payload_json = response_payload

        db.session.commit()

        # Check and update onboarding status
        if submission.user_id:
            user = User.query.get(submission.user_id)
            if user and user.profile_completed and not user.onboarding_completed:
                user.onboarding_completed = True
                db.session.commit()
                logger.info(f"Onboarding marked as complete for user: {user.id}")

        return jsonify(response_payload), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Submission with this ID already exists"}), 409
    except Exception as exc:  # pragma: no cover - defensive logging path
        try:
            logger.exception("create_submission failed: %s", exc)
        except Exception:
            pass
        db.session.rollback()
        return jsonify({"error": "Submission failed"}), 500


@bp.route("/submissions/<submission_id>", methods=["GET"])
@token_required
def get_submission(current_user_id, submission_id):
    """
    Get a specific submission by ID.

    Security: Only the submission owner can access it (or admin).
    """
    try:
        user_uuid = uuid.UUID(current_user_id)

        submission = SurveySubmission.query.filter_by(
            submission_id=submission_id
        ).first()

        if submission is None:
            return jsonify({"error": "Submission not found"}), 404

        # Ownership check: user can only access their own submissions (unless admin)
        if submission.user_id and submission.user_id != user_uuid:
            if not is_admin_user(current_user_id):
                return jsonify({"error": "Forbidden"}), 403

        return jsonify(serialize_submission(submission))
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"get_submission failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Failed to retrieve submission"}), 500


@bp.route("/baseline", methods=["GET"])
@token_required
def get_baseline(current_user_id):
    try:
        baseline_row = get_baseline_record()
        baseline_id = baseline_row.submission_id if baseline_row else None
        return jsonify({"baseline": baseline_id})
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"get_baseline failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Failed to get baseline"}), 500


@bp.route("/baseline", methods=["POST"])
@token_required
def set_baseline(current_user_id):
    try:
        data = request.get_json(silent=True) or {}
        baseline_id = data.get("id")

        if not baseline_id:
            return jsonify({"error": "Baseline ID required"}), 400

        submission_exists = SurveySubmission.query.filter_by(
            submission_id=baseline_id
        ).first()
        if submission_exists is None:
            return jsonify({"error": "Submission not found"}), 404

        baseline_row = get_baseline_record(create=True)
        baseline_row.submission_id = baseline_id
        db.session.commit()
        return jsonify({"baseline": baseline_id})
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"set_baseline failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Failed to set baseline"}), 500


@bp.route("/baseline", methods=["DELETE"])
@token_required
def clear_baseline(current_user_id):
    try:
        baseline_row = get_baseline_record()
        if baseline_row:
            baseline_row.submission_id = None
            db.session.commit()
        return jsonify({"baseline": None})
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"clear_baseline failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Failed to clear baseline"}), 500


@bp.route("/compatibility/<source_id>/<target_id>", methods=["GET"])
@token_required
def get_compatibility(current_user_id, source_id, target_id):
    """
    Calculate compatibility between two submissions.

    Security: User must own at least one of the submissions to compute compatibility.
    """
    try:
        user_uuid = uuid.UUID(current_user_id)

        source = SurveySubmission.query.filter_by(submission_id=source_id).first()
        target = SurveySubmission.query.filter_by(submission_id=target_id).first()

        if not source or not target:
            return jsonify({"error": "Submission not found"}), 404

        # Authorization: user must own at least one submission (unless admin)
        owns_source = source.user_id == user_uuid
        owns_target = target.user_id == user_uuid

        if not owns_source and not owns_target and not is_admin_user(current_user_id):
            return jsonify({"error": "Forbidden"}), 403

        # Ensure we have derived profiles
        source_profile = source.payload_json.get('derived')
        target_profile = target.payload_json.get('derived')

        if not source_profile:
            # Fallback: calculate if missing (shouldn't happen for new subs)
            source_profile = calculate_profile(source.submission_id, source.payload_json.get('answers', {}))

        if not target_profile:
            target_profile = calculate_profile(target.submission_id, target.payload_json.get('answers', {}))

        # Import here to avoid circular imports if any
        from ..compatibility.calculator import calculate_compatibility

        result = calculate_compatibility(source_profile, target_profile)

        return jsonify(result)
    except Exception as exc:
        logger.error(f"get_compatibility failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Compatibility calculation failed"}), 500


@bp.route("/export", methods=["GET"])
@token_required
@require_admin
def export_data(current_user_id):
    """
    Export all survey data.

    Security: Admin-only endpoint.
    """
    try:
        submissions = (
            SurveySubmission.query.order_by(SurveySubmission.created_at.asc()).all()
        )
        baseline_row = get_baseline_record()
        export_payload = {
            "exportedAt": datetime.utcnow().isoformat(),
            "baseline": baseline_row.submission_id if baseline_row else None,
            "submissions": [serialize_submission(s) for s in submissions],
        }
        return jsonify(export_payload)
    except Exception as exc:  # pragma: no cover - defensive logging path
        logger.error(f"export_data failed: {str(exc)}")
        db.session.rollback()
        return jsonify({"error": "Export failed"}), 500

