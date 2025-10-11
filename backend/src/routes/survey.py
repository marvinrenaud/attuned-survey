# backend/src/routes/survey.py
from flask import Blueprint, request, jsonify
from ..main import db, SurveySubmission

bp = Blueprint("survey", __name__, url_prefix="/api/survey")

@bp.get("/submissions")
def list_submissions():
    rows = (SurveySubmission.query
            .order_by(SurveySubmission.created_at.desc())
            .limit(1000)
            .all())
    # Preserve prior response shape so the frontend remains unchanged
    return jsonify({
        "baseline": None,
        "submissions": [
            {
                "id": str(r.id),
                "name": (r.payload_json.get("name")
                         if isinstance(r.payload_json, dict) else None),
                "answers": (r.payload_json.get("answers")
                            if isinstance(r.payload_json, dict) else r.payload_json),
                "derived": (r.payload_json.get("derived")
                            if isinstance(r.payload_json, dict) else None),
                "createdAt": r.created_at.isoformat(),
            }
            for r in rows
        ]
    }), 200

def _create_submission():
    """Private handler for creating survey submissions."""
    submission = request.get_json(force=True) or {}
    respondent_id = submission.get("respondent_id")
    entry = SurveySubmission(
        respondent_id=respondent_id,
        payload_json=submission
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"ok": True, "id": entry.id}), 201

@bp.post("/submissions")
def post_submissions():
    """POST /api/survey/submissions - legacy endpoint."""
    return _create_submission()

@bp.post("/submit")
def post_submit():
    """POST /api/survey/submit - alias for backward compatibility."""
    return _create_submission()