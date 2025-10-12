# backend/src/routes/survey.py
from flask import Blueprint, request, jsonify
import json
import os
from datetime import datetime
import math
import tempfile
import shutil

survey_bp = Blueprint('survey', __name__, url_prefix='/api/survey')

# Data file path
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'database')
DATA_FILE = os.path.join(DATA_DIR, 'submissions.json')
BASELINE_FILE = os.path.join(DATA_DIR, 'baseline.json')
BACKUP_DIR = os.path.join(DATA_DIR, 'backups')


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
    """Ensure data files and directories exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
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

def _cleanup_old_backups():
    """Best-effort cleanup for old backup files."""
    try:
        backups = [
            os.path.join(BACKUP_DIR, name)
            for name in os.listdir(BACKUP_DIR)
            if name.startswith('submissions.json.bak.')
        ]
        backups.sort(key=os.path.getmtime, reverse=True)
        for stale_backup in backups[5:]:
            try:
                os.remove(stale_backup)
            except OSError:
                # Ignore cleanup issues; they shouldn't break saving.
                continue
    except OSError:
        # Best effort only; nothing to do if listing fails.
        return


def save_submissions(submissions):
    """Save all submissions to file with durable backup handling."""
    ensure_data_files()
    sanitized = sanitize_for_json(submissions)

    temp_fd, temp_path = tempfile.mkstemp(dir=DATA_DIR, prefix='submissions.', suffix='.tmp')
    backup_path = None

    try:
        with os.fdopen(temp_fd, 'w') as tmp_file:
            json.dump(sanitized, tmp_file, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())

        if os.path.exists(DATA_FILE):
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            backup_filename = f"submissions.json.bak.{timestamp}.{os.getpid()}"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            shutil.copy2(DATA_FILE, backup_path)

        os.replace(temp_path, DATA_FILE)
    except Exception:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        # Remove backup if we created one and the write failed before replace.
        if backup_path is not None:
            try:
                os.remove(backup_path)
            except OSError:
                pass
        raise
    else:
        _cleanup_old_backups()

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

