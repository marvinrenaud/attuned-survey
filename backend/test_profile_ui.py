

import pytest
from unittest.mock import MagicMock, patch
from src.main import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    return app.test_client()

@patch('src.routes.profile_ui.User')
@patch('src.routes.profile_ui.SurveySubmission')
def test_profile_ui_endpoint(mock_submission_cls, mock_user_cls, client):
    # 1. Setup Mock User
    user_id = "user_123"
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user_cls.query.get.return_value = mock_user
    
    # 2. Setup Mock Submission
    submission_id = "sub_123"
    mock_submission = MagicMock()
    mock_submission.submission_id = submission_id
    mock_submission.user_id = user_id
    
    # Payload with known answers
    mock_submission.payload_json = {
        "answers": {
            # Arousal
            "A1": 7, "A2": 7, "A3": 7, "A4": 7, # SE High
            "A5": 1, "A6": 1, "A7": 1, "A8": 1, # SIS-P Low
            "A9": 1, "A10": 1, "A11": 1, "A12": 1, # SIS-C Low
            
            # Power (Switch)
            "A13": 7, "A15": 7, # Top High
            "A14": 7, "A16": 7, # Bottom High
            
            # Activities (Physical Touch)
            "B1a": "Y", # massage_receive -> Massage (Receiving)
            "B1b": "N", # massage_give
            
            # Activities (Oral) - To test ordering
            "B11a": "Y", # oral_sex_receive -> Oral Sex (Receiving)
        },
        "derived": {
            "arousal_propensity": {
                "sexual_excitation": 1.0,
                "inhibition_performance": 0.0,
                "inhibition_consequence": 0.0
            },
            "power_dynamic": {
                "orientation": "Switch",
                "top_score": 100,
                "bottom_score": 100,
                "interpretation": "High confidence Switch"
            },
            "domain_scores": {
                "sensation": 50,
                "connection": 80,
                "power": 60,
                "exploration": 40,
                "verbal": 30
            },
            "boundaries": {
                "hard_limits": ["No blood", "No scat"]
            },
            "activities": {
                "physical_touch": {
                    "massage_receive": 1.0,
                    "massage_give": 0.0
                },
                "oral": {
                    "oral_sex_receive": 1.0
                },
                "verbal_roleplay": {
                    "dirty_talk": 0.0
                }
            }
        }
    }
    
    # Mock the query chain: SurveySubmission.query.filter_by(...).order_by(...).first()
    mock_query = mock_submission_cls.query.filter_by.return_value
    mock_query.order_by.return_value.first.return_value = mock_submission
    
    # 3. Call Endpoint
    response = client.get(f"/api/users/{user_id}/profile-ui")
    assert response.status_code == 200
    
    data = response.json
    
    # 4. Verify Structure
    assert data["user_id"] == user_id
    assert data["submission_id"] == submission_id
    
    # General
    assert data["general"]["arousal_profile"]["sexual_excitation"] == 1.0
    assert data["general"]["power"]["label"] == "Switch"
    assert data["general"]["power"]["top_percentage"] == 50
    assert data["general"]["power"]["bottom_percentage"] == 50
    assert len(data["general"]["domains"]) == 5
    assert "No blood" in data["general"]["boundaries"]
    
    # Interests
    interests = data["interests"]
    assert len(interests) > 0
    
    # Verify Sorting & Filtering
    section_names = [s["section"] for s in interests]
    
    # Check for specific order (Survey Order)
    assert "Physical Touch" in section_names
    assert "Oral Activities" in section_names
    assert "Verbal & Roleplay" not in section_names # Should be excluded (empty)
    
    # Verify Physical Touch comes BEFORE Oral Activities
    pt_index = section_names.index("Physical Touch")
    oral_index = section_names.index("Oral Activities")
    assert pt_index < oral_index
    
    # Verify Tags
    pt_section = next(s for s in interests if s["section"] == "Physical Touch")
    assert "Massage (Receiving)" in pt_section["tags"]
    assert "Massage (Giving)" not in pt_section["tags"] # Score 0
    
    print("Test passed!")

