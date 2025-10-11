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

@bp.post("/submissions")
def submit_survey():
    submission = request.get_json(force=True) or {}
    respondent_id = submission.get("respondent_id")
    entry = SurveySubmission(
        respondent_id=respondent_id,
        payload_json=submission
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({"ok": True, "id": entry.id}), 201