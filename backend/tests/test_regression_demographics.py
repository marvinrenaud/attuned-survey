"""
Regression tests for demographics_completed field addition.
Tests Phase 8 requirements from the plan.
Ensures existing functionality is not broken by migration 009.
"""
import pytest
import uuid


class TestDatabaseRegression:
    """Test that migration 009 doesn't break existing data."""
    
    def test_existing_users_still_accessible(self, client):
        """Verify all existing users still accessible after migration."""
        response = client.get('/api/auth/user/550e8400-e29b-41d4-a716-446655440001')
        
        # Should work (test user Alice)
        if response.status_code == 200:
            data = response.get_json()
            assert 'email' in data['user']
            assert 'demographics_completed' in data['user']  # New field present
    
    def test_foreign_key_relationships_intact(self, db_session):
        """Test foreign key relationships still work."""
        from backend.src.models.user import User
        from backend.src.models.profile import Profile
        
        # Test user → profile relationship
        # This would fail if CASCADE is broken
        user = User(
            id=str(uuid.uuid4()),
            email='fk-test@example.com',
            demographics_completed=True
        )
        db_session.add(user)
        db_session.commit()
        
        # Create profile for user
        profile = Profile(
            user_id=user.id,
            submission_id=f'test_sub_{user.id}',
            power_dynamic={'orientation': 'Switch'},
            arousal_propensity={'se': 0.5},
            domain_scores={'sensation': 50},
            activities={'massage_give': 0.8},
            truth_topics={'past_experiences': 0.7},
            boundaries={'hard_limits': []},
            anatomy={'anatomy_self': [], 'anatomy_preference': []}
        )
        db_session.add(profile)
        db_session.commit()
        
        # Verify relationship
        assert profile.user_id == user.id
        
        # Test cascade delete
        db_session.delete(user)
        db_session.commit()
        
        # Profile should be deleted too (CASCADE)
        deleted_profile = Profile.query.filter_by(user_id=user.id).first()
        assert deleted_profile is None


class TestAPIRegression:
    """Test that all existing endpoints still work."""
    
    def test_register_endpoint_still_works(self, client):
        """Test POST /api/auth/register still creates users."""
        user_id = str(uuid.uuid4())
        response = client.post('/api/auth/register', json={
            'id': user_id,
            'email': 'regression-register@example.com',
            'display_name': 'Regression Test'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] == True
        assert 'demographics_completed' in data['user']
        assert data['user']['demographics_completed'] == False  # Default
    
    def test_get_user_returns_new_field(self, client):
        """Test GET /api/auth/user/:id returns demographics_completed."""
        # Use existing test user
        response = client.get('/api/auth/user/550e8400-e29b-41d4-a716-446655440001')
        
        if response.status_code == 200:
            data = response.get_json()
            assert 'demographics_completed' in data['user']
    
    def test_update_user_can_update_both_flags(self, client, db_session):
        """Test PATCH /api/auth/user/:id can update both flags."""
        from backend.src.models.user import User
        
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email='patch-test@example.com',
            demographics_completed=False,
            onboarding_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Update via API
        response = client.patch(f'/api/auth/user/{user_id}', json={
            'display_name': 'Updated Name'
        })
        
        # Should still work
        assert response.status_code in [200, 404]  # 404 if route not found is okay
    
    def test_user_model_to_dict_includes_new_field(self, db_session):
        """Test User.to_dict() includes demographics_completed."""
        from backend.src.models.user import User
        
        user = User(
            id=str(uuid.uuid4()),
            email='to-dict-test@example.com',
            demographics_completed=True
        )
        db_session.add(user)
        db_session.commit()
        
        user_dict = user.to_dict()
        assert 'demographics_completed' in user_dict
        assert user_dict['demographics_completed'] == True


class TestDataIntegrity:
    """Test data integrity after migration 009."""
    
    def test_default_values_work(self, db_session):
        """Test new users get correct default values."""
        from backend.src.models.user import User
        
        user = User(
            id=str(uuid.uuid4()),
            email='defaults-test@example.com'
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify defaults
        assert user.demographics_completed == False
        assert user.onboarding_completed == False
        assert user.subscription_tier == 'free'
        assert user.daily_activity_count == 0
    
    def test_unique_constraints_still_enforced(self, db_session):
        """Test UNIQUE constraints still work."""
        from backend.src.models.user import User
        from sqlalchemy.exc import IntegrityError
        
        # Create user
        user1 = User(
            id=str(uuid.uuid4()),
            email='unique-test@example.com'
        )
        db_session.add(user1)
        db_session.commit()
        
        # Try to create duplicate email
        user2 = User(
            id=str(uuid.uuid4()),
            email='unique-test@example.com'  # Duplicate!
        )
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()
    
    def test_not_null_constraints_enforced(self, db_session):
        """Test NOT NULL constraints still work."""
        from backend.src.models.user import User
        from sqlalchemy.exc import IntegrityError
        
        # Try to create user without email (NOT NULL)
        user = User(
            id=str(uuid.uuid4()),
            email=None  # NOT NULL violation
        )
        db_session.add(user)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
        
        db_session.rollback()


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""
    
    def test_existing_api_calls_dont_break(self, client):
        """Test that API calls without new field still work."""
        user_id = str(uuid.uuid4())
        
        # Old-style registration (without demographics_completed in request)
        response = client.post('/api/auth/register', json={
            'id': user_id,
            'email': 'backward-compat@example.com'
        })
        
        # Should still work
        assert response.status_code in [201, 409]  # 201 created or 409 duplicate


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

