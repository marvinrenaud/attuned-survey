from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
import math

survey_bp = Blueprint('survey', __name__, url_prefix='/api/survey')

# Data file path
DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'submissions.json')
BASELINE_FILE = os.path.join(os.path.dirname(__file__), '..', 'database', 'baseline.json')


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

def ensure_data_files():
    """Ensure data files exist"""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            json.dump([], f)
    if not os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, 'w') as f:
            json.dump(None, f)

def load_submissions():
    """Load all submissions from file"""
    ensure_data_files()
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_submissions(submissions):
    """Save all submissions to file"""
    ensure_data_files()
    sanitized = sanitize_for_json(submissions)
    with open(DATA_FILE, 'w') as f:
        json.dump(sanitized, f, indent=2)

def load_baseline():
    """Load baseline submission ID"""
    ensure_data_files()
    with open(BASELINE_FILE, 'r') as f:
        return json.load(f)

def save_baseline(baseline_id):
    """Save baseline submission ID"""
    ensure_data_files()
    with open(BASELINE_FILE, 'w') as f:
        json.dump(baseline_id, f)

@survey_bp.route('/submissions', methods=['GET'])
def get_submissions():
    """Get all submissions"""
    try:
        submissions = sanitize_for_json(load_submissions())
        baseline = load_baseline()
        return jsonify({
            'submissions': submissions,
            'baseline': baseline
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/submissions', methods=['POST'])
def create_submission():
    """Create a new submission"""
    try:
        data = request.json
        submissions = load_submissions()
        
        # Add timestamp if not present
        if 'createdAt' not in data:
            data['createdAt'] = datetime.now().isoformat()
        
        # Generate ID if not present
        if 'id' not in data:
            data['id'] = str(int(datetime.now().timestamp() * 1000))
        
        sanitized_submission = sanitize_for_json(data)
        submissions.append(sanitized_submission)
        save_submissions(submissions)

        return jsonify(sanitized_submission), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/submissions/<submission_id>', methods=['GET'])
def get_submission(submission_id):
    """Get a specific submission"""
    try:
        submissions = load_submissions()
        submission = next((s for s in submissions if s['id'] == submission_id), None)
        
        if not submission:
            return jsonify({'error': 'Submission not found'}), 404
        
        return jsonify(sanitize_for_json(submission))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/baseline', methods=['GET'])
def get_baseline():
    """Get baseline submission ID"""
    try:
        baseline = load_baseline()
        return jsonify({'baseline': baseline})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/baseline', methods=['POST'])
def set_baseline():
    """Set baseline submission"""
    try:
        data = request.json
        baseline_id = data.get('id')
        
        if not baseline_id:
            return jsonify({'error': 'Baseline ID required'}), 400
        
        # Verify submission exists
        submissions = load_submissions()
        if not any(s['id'] == baseline_id for s in submissions):
            return jsonify({'error': 'Submission not found'}), 404
        
        save_baseline(baseline_id)
        return jsonify({'baseline': baseline_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/baseline', methods=['DELETE'])
def clear_baseline():
    """Clear baseline submission"""
    try:
        save_baseline(None)
        return jsonify({'baseline': None})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@survey_bp.route('/export', methods=['GET'])
def export_data():
    """Export all data as JSON"""
    try:
        submissions = sanitize_for_json(load_submissions())
        baseline = load_baseline()

        export_data = {
            'exportedAt': datetime.now().isoformat(),
            'baseline': baseline,
            'submissions': submissions
        }
        
        return jsonify(export_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

