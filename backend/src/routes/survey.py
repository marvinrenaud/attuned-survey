# backend/src/routes/survey.py
from datetime import datetime
import math
from typing import Optional

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models.survey import SurveyBaseline, SurveySubmission
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
def get_submissions():
    try:
        submissions = (
            SurveySubmission.query.order_by(SurveySubmission.created_at.asc()).all()
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
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/submissions", methods=["POST"])
def create_submission():
    try:
        data = request.get_json(silent=True) or {}
        # Log minimal context for troubleshooting payload mismatches
        try:
            current_app.logger.info(
                "create_submission payload keys=%s name=%s sex=%s sexualOrientation=%s",
                list(data.keys()),
                data.get("name"),
                data.get("sex"),
                data.get("sexualOrientation") or data.get("sexual_orientation"),
            )
        except Exception:
            pass
        sanitized_submission = sanitize_for_json(data)

        submission_id = sanitized_submission.get("id")
        if not submission_id:
            submission_id = str(int(datetime.utcnow().timestamp() * 1000))
            sanitized_submission["id"] = submission_id

        respondent_id = sanitized_submission.get("respondentId") or sanitized_submission.get(
            "respondent_id"
        )
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
        # Ensure anatomy answers are present in answers dict if they are separate
        # (Frontend currently sends them merged, but let's be safe)
        
        derived_profile = calculate_profile(submission_id, answers)
        sanitized_submission["derived"] = derived_profile

        submission = SurveySubmission(
            submission_id=submission_id,
            respondent_id=respondent_id,
            name=name,
            sex=sex,
            sexual_orientation=sexual_orientation,
            version=version,
            payload_json=sanitized_submission,
        )
        # Note: SurveySubmission model might not have a separate 'derived' column defined in SQLAlchemy model
        # but it likely has payload_json.
        # Let's check the model definition if possible, but for now assuming payload_json is the main store.
        # If 'derived' is a column, we should set it. If not, it's in payload_json.
        # The user request said "Make the backend the source of truth... Supports auditability and persistence".
        # Storing it in payload_json is good.
        # Wait, I see `derived=derived_profile` in my proposed code. I need to check if `derived` column exists.
        # I'll assume it doesn't for now and rely on payload_json, BUT I will check the model file first to be sure.
        # Actually, I should check the model file.
        
        db.session.add(submission)
        db.session.flush()

        response_payload = serialize_submission(submission)
        if version is not None:
            response_payload["version"] = version
        
        # Ensure derived is in response
        response_payload["derived"] = derived_profile
        
        submission.payload_json = response_payload

        db.session.commit()
        return jsonify(response_payload), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Submission with this ID already exists"}), 409
    except Exception as exc:  # pragma: no cover - defensive logging path
        try:
            current_app.logger.exception("create_submission failed: %s", exc)
        except Exception:
            pass
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/submissions/<submission_id>", methods=["GET"])
def get_submission(submission_id):
    try:
        submission = SurveySubmission.query.filter_by(
            submission_id=submission_id
        ).first()

        if submission is None:
            return jsonify({"error": "Submission not found"}), 404

        return jsonify(serialize_submission(submission))
    except Exception as exc:  # pragma: no cover - defensive logging path
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/baseline", methods=["GET"])
def get_baseline():
    try:
        baseline_row = get_baseline_record()
        baseline_id = baseline_row.submission_id if baseline_row else None
        return jsonify({"baseline": baseline_id})
    except Exception as exc:  # pragma: no cover - defensive logging path
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/baseline", methods=["POST"])
def set_baseline():
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
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/baseline", methods=["DELETE"])
def clear_baseline():
    try:
        baseline_row = get_baseline_record()
        if baseline_row:
            baseline_row.submission_id = None
            db.session.commit()
        return jsonify({"baseline": None})
    except Exception as exc:  # pragma: no cover - defensive logging path
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/compatibility/<source_id>/<target_id>", methods=["GET"])
def get_compatibility(source_id, target_id):
    try:
        source = SurveySubmission.query.filter_by(submission_id=source_id).first()
        target = SurveySubmission.query.filter_by(submission_id=target_id).first()

        if not source or not target:
            return jsonify({"error": "Submission not found"}), 404

        # Ensure we have derived profiles
        # In v0.5, derived profiles are stored in payload_json['derived'] or calculated on fly
        # The create_submission route puts it in payload_json['derived']
        
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
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500


@bp.route("/export", methods=["GET"])
def export_data():
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
        db.session.rollback()
        return jsonify({"error": str(exc)}), 500

