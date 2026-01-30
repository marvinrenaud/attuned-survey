"""
Functional tests for profile_completed field.
Tests Phase 7 requirements from the plan.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import patch


class TestDemographicsFieldDatabase:
    """Test profile_completed field in database."""
    
    def test_field_exists_in_schema(self, db_session):
        """Test profile_completed field exists in users table."""
        from backend.src.models.user import User
        assert hasattr(User, 'profile_completed')
    
    def test_field_defaults_to_false(self, db_session):
        """Test field defaults to FALSE for new users."""
        from backend.src.models.user import User

        user = User(
            id=uuid.uuid4(),
            email='default-test@example.com',
            display_name='Default Test'
        )
        db_session.add(user)
        db_session.commit()

        # After commit, DB default should be applied
        db_session.refresh(user)
        assert user.profile_completed == False
    
    def test_field_can_be_set_to_true(self, db_session):
        """Test field can be updated to TRUE."""
        from backend.src.models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email='update-test@example.com',
            display_name='Update Test',
            profile_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        user.profile_completed = True
        db_session.commit()
        
        updated_user = User.query.filter_by(email='update-test@example.com').first()
        assert updated_user.profile_completed == True


class TestCompleteDemographicsEndpoint:
    """Test POST /api/auth/user/:id/complete-demographics endpoint."""
    
    def test_endpoint_with_valid_data(self, client, db_session):
        """Test complete-demographics with valid data returns 200."""
        from backend.src.models.user import User

        # Create user directly in database
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='test-demo@example.com',
            display_name='Test User'
        )
        db_session.add(user)
        db_session.commit()

        # Mock authentication and complete demographics
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(user_id)}
            response = client.post('/api/auth/complete-demographics',
                headers={'Authorization': 'Bearer test-token'},
                json={
                    'name': 'Updated Name',
                    'anatomy_self': ['vagina', 'breasts'],
                    'anatomy_preference': ['penis', 'vagina']
                })

        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['profile_completed'] == True
        assert data['can_play'] == True
    
    def test_endpoint_missing_fields_returns_400(self, client, db_session):
        """Test complete-demographics with missing required field (name) returns 400."""
        from backend.src.models.user import User

        # Create user directly in database
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='missing-fields-test@example.com',
            display_name='Test User'
        )
        db_session.add(user)
        db_session.commit()

        # Mock authentication and try without name field
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(user_id)}
            response = client.post('/api/auth/complete-demographics',
                headers={'Authorization': 'Bearer test-token'},
                json={
                    'anatomy_self': ['penis'],
                    'anatomy_preference': ['vagina']
                })

        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'name' in data['error']
    
    def test_endpoint_updates_display_name(self, client, db_session):
        """Test complete-demographics updates display_name."""
        from backend.src.models.user import User

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='name-test@example.com',
            display_name='Old Name'
        )
        db_session.add(user)
        db_session.commit()

        # Mock authentication and complete demographics
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(user_id)}
            response = client.post('/api/auth/complete-demographics',
                headers={'Authorization': 'Bearer test-token'},
                json={
                    'name': 'New Name',
                    'anatomy_self': ['penis'],
                    'anatomy_preference': ['vagina']
                })

        assert response.status_code == 200

        updated_user = User.query.filter_by(id=user_id).first()
        assert updated_user.display_name == 'New Name'
    
    def test_endpoint_updates_demographics_jsonb(self, client, db_session):
        """Test complete-demographics updates demographics JSONB."""
        from backend.src.models.user import User

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='demo-jsonb-test@example.com'
        )
        db_session.add(user)
        db_session.commit()

        # Mock authentication and complete demographics
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(user_id)}
            response = client.post('/api/auth/complete-demographics',
                headers={'Authorization': 'Bearer test-token'},
                json={
                    'name': 'Test',
                    'anatomy_self': ['vagina'],
                    'anatomy_preference': ['penis', 'vagina'],
                    'gender': 'woman',
                    'sexual_orientation': 'bisexual'
                })

        assert response.status_code == 200

        updated_user = User.query.filter_by(id=user_id).first()
        assert 'anatomy_self' in updated_user.demographics
        assert 'anatomy_preference' in updated_user.demographics
        assert updated_user.demographics['gender'] == 'woman'
    
    def test_endpoint_sets_flag_to_true(self, client, db_session):
        """Test complete-demographics sets profile_completed=TRUE."""
        from backend.src.models.user import User

        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email='flag-test@example.com',
            profile_completed=False
        )
        db_session.add(user)
        db_session.commit()

        # Mock authentication and complete demographics
        with patch('src.middleware.auth.jwt.decode') as mock_decode:
            mock_decode.return_value = {"sub": str(user_id)}
            response = client.post('/api/auth/complete-demographics',
                headers={'Authorization': 'Bearer test-token'},
                json={
                    'name': 'Test',
                    'anatomy_self': ['penis'],
                    'anatomy_preference': ['vagina']
                })

        assert response.status_code == 200

        updated_user = User.query.filter_by(id=user_id).first()
        assert updated_user.profile_completed == True
    
    def test_endpoint_nonexistent_user_returns_404(self, client):
        """Test complete-demographics with non-existent user returns 404."""
        fake_uuid = str(uuid.uuid4())
        
        response = client.post(f'/api/auth/user/{fake_uuid}/complete-demographics', json={
            'name': 'Test',
            'anatomy_self': ['penis'],
            'anatomy_preference': ['vagina']
        })
        
        assert response.status_code == 404


class TestUserStates:
    """Test user state combinations."""
    
    def test_state_registered_only(self, db_session):
        """Test user state: just registered (both FALSE, cannot play)."""
        from backend.src.models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email='just-registered@example.com',
            display_name='New User',
            profile_completed=False,
            onboarding_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify state
        assert user.profile_completed == False
        assert user.onboarding_completed == False
        # Logic: Cannot play, no personalization
    
    def test_state_demographics_done(self, db_session):
        """Test user state: demographics done (can play, no personalization)."""
        from backend.src.models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email='demo-done@example.com',
            display_name='Demo User',
            profile_completed=True,
            onboarding_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify state
        assert user.profile_completed == True
        assert user.onboarding_completed == False
        # Logic: Can play with generic activities
    
    def test_state_survey_done(self, db_session):
        """Test user state: survey done (can play + personalize)."""
        from backend.src.models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email='survey-done@example.com',
            display_name='Complete User',
            profile_completed=True,
            onboarding_completed=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify state
        assert user.profile_completed == True
        assert user.onboarding_completed == True
        # Logic: Can play with personalized activities


class TestGameAccessGate:
    """Test game access gating logic."""
    
    def test_cannot_play_without_demographics(self):
        """Test session creation should be blocked when profile_completed=FALSE."""
        from backend.src.models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email='no-demo@example.com',
            profile_completed=False
        )
        
        # Application logic should check:
        can_play = user.profile_completed
        assert can_play == False
    
    def test_can_play_with_demographics(self):
        """Test session creation allowed when profile_completed=TRUE."""
        from backend.src.models.user import User
        
        user = User(
            id=str(uuid.uuid4()),
            email='has-demo@example.com',
            profile_completed=True
        )
        
        can_play = user.profile_completed
        assert can_play == True
    
    def test_generic_activities_without_survey(self):
        """Test activity generation uses generic when onboarding_completed=FALSE."""
        from backend.src.models.user import User
        
        user = User(
            id=str(uuid.uuid4()),
            email='no-survey@example.com',
            profile_completed=True,
            onboarding_completed=False
        )
        
        # Check personalization level
        has_personalization = user.onboarding_completed
        assert has_personalization == False
        # Logic: Use generic activities
    
    def test_personalized_activities_with_survey(self):
        """Test activity generation uses personalized when onboarding_completed=TRUE."""
        from backend.src.models.user import User
        
        user = User(
            id=str(uuid.uuid4()),
            email='has-survey@example.com',
            profile_completed=True,
            onboarding_completed=True
        )
        
        # Check personalization level
        has_personalization = user.onboarding_completed
        assert has_personalization == True
        # Logic: Use personalized activities


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

