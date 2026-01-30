import pytest
import jwt
import uuid
import os
from unittest.mock import patch, MagicMock
from backend.src.models.survey import SurveySubmission

TEST_USER_ID = str(uuid.uuid4())

@pytest.fixture
def app():
    """Create application for testing with mocked DB creation."""
    from backend.src.main import create_app
    from backend.src.extensions import db

    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })

    with app.app_context():
        # Mock create_all to avoid JSONB error in SQLite
        with patch.object(db, 'create_all'):
            yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_db_session(app):
    with patch('backend.src.routes.survey.SurveySubmission') as mock_model:
        yield mock_model

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def get_auth_header():
    token = jwt.encode({"sub": TEST_USER_ID, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    return {'Authorization': f'Bearer {token}'}

def test_compatibility_endpoint(client, mock_db_session):
    """Test the GET /api/survey/compatibility/<source_id>/<target_id> endpoint with mocks."""

    # Mock source submission - owned by test user
    source_sub = MagicMock()
    source_sub.submission_id = "sub_a"
    source_sub.user_id = uuid.UUID(TEST_USER_ID)  # User owns this submission
    source_sub.payload_json = {
        "derived": {
            "profile_version": "0.4",
            "power_dynamic": {"orientation": "Top", "confidence": 0.8},
            "domain_scores": {"sensation": 50, "connection": 50, "power": 50, "exploration": 50, "verbal": 50},
            "activities": {"physical_touch": {"massage_give": 1.0}},
            "truth_topics": {},
            "boundaries": {}
        }
    }

    # Mock target submission - owned by another user (OK since user owns source)
    other_user_id = uuid.uuid4()
    target_sub = MagicMock()
    target_sub.submission_id = "sub_b"
    target_sub.user_id = other_user_id
    target_sub.payload_json = {
        "derived": {
            "profile_version": "0.4",
            "power_dynamic": {"orientation": "Bottom", "confidence": 0.8},
            "domain_scores": {"sensation": 50, "connection": 50, "power": 50, "exploration": 50, "verbal": 50},
            "activities": {"physical_touch": {"massage_receive": 1.0}},
            "truth_topics": {},
            "boundaries": {}
        }
    }

    # Setup mock query return values
    # The endpoint calls filter_by(submission_id=...).first()
    # We need to handle two different calls

    def side_effect(**kwargs):
        mock_query = MagicMock()
        if kwargs.get('submission_id') == 'sub_a':
            mock_query.first.return_value = source_sub
        elif kwargs.get('submission_id') == 'sub_b':
            mock_query.first.return_value = target_sub
        else:
            mock_query.first.return_value = None
        return mock_query

    mock_db_session.query.filter_by.side_effect = side_effect

    # Call endpoint
    response = client.get("/api/survey/compatibility/sub_a/sub_b", headers=get_auth_header())

    assert response.status_code == 200
    data = response.get_json()

    # Verify structure
    assert "overall_compatibility" in data
    assert "score" in data["overall_compatibility"]

    # Verify logic (Top/Bottom should be high)
    score = data["overall_compatibility"]["score"]
    assert score > 80

def test_compatibility_endpoint_not_found(client, mock_db_session):
    """Test compatibility endpoint with non-existent IDs."""

    # Mock query to return None
    mock_query = MagicMock()
    mock_query.first.return_value = None
    mock_db_session.query.filter_by.return_value = mock_query

    response = client.get("/api/survey/compatibility/fake_a/fake_b", headers=get_auth_header())
    assert response.status_code == 404
