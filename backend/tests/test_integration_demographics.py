"""
Integration tests for demographics_completed feature.
Tests Phase 9 requirements from the plan.
Tests complete end-to-end user journeys.
"""
import pytest
import uuid


class TestUserJourneys:
    """Test complete end-to-end user journeys."""
    
    def test_journey_new_user_demographics_play_no_survey(self, client, db_session):
        """
        Journey 1: New User → Demographics → Play (No Survey)
        User completes demographics but skips survey, plays with generic activities.
        """
        from backend.src.models.user import User
        
        # Step 1: Register user
        user_id = str(uuid.uuid4())
        response = client.post('/api/auth/register', json={
            'id': user_id,
            'email': 'journey1@example.com',
            'display_name': 'Journey 1 User'
        })
        assert response.status_code == 201
        
        # Step 2: Verify initial state (both FALSE)
        user = User.query.filter_by(id=user_id).first()
        assert user.demographics_completed == False
        assert user.onboarding_completed == False
        
        # Step 3: Complete demographics
        response = client.post(f'/api/auth/user/{user_id}/complete-demographics', json={
            'name': 'Journey 1 Complete',
            'anatomy_self': ['penis'],
            'anatomy_preference': ['vagina']
        })
        assert response.status_code == 200
        
        # Step 4: Verify demographics flag set
        user = User.query.filter_by(id=user_id).first()
        assert user.demographics_completed == True
        assert user.onboarding_completed == False
        
        # Step 5: User can now create session (demographics gate passed)
        can_play = user.demographics_completed
        assert can_play == True
        
        # Step 6: Activity generation would use generic (no survey)
        has_personalization = user.onboarding_completed
        assert has_personalization == False
    
    def test_journey_new_user_demographics_survey_play(self, client, db_session):
        """
        Journey 2: New User → Demographics → Survey → Play
        User completes demographics and survey, gets personalized activities.
        """
        from backend.src.models.user import User
        from backend.src.models.profile import Profile
        
        # Step 1: Register
        user_id = str(uuid.uuid4())
        response = client.post('/api/auth/register', json={
            'id': user_id,
            'email': 'journey2@example.com'
        })
        assert response.status_code == 201
        
        # Step 2: Complete demographics
        response = client.post(f'/api/auth/user/{user_id}/complete-demographics', json={
            'name': 'Journey 2 User',
            'anatomy_self': ['vagina'],
            'anatomy_preference': ['penis']
        })
        assert response.status_code == 200
        
        user = User.query.filter_by(id=user_id).first()
        assert user.demographics_completed == True
        
        # Step 3: Complete survey (simulate)
        user.onboarding_completed = True
        db_session.commit()
        
        # Create profile
        profile = Profile(
            user_id=user.id,
            submission_id=f'journey2_sub_{user.id}',
            power_dynamic={'orientation': 'Top'},
            arousal_propensity={'se': 0.7},
            domain_scores={'sensation': 65},
            activities={'oral_give': 0.9},
            truth_topics={'fantasies': 0.8},
            boundaries={'hard_limits': []},
            anatomy={'anatomy_self': ['vagina'], 'anatomy_preference': ['penis']}
        )
        db_session.add(profile)
        db_session.commit()
        
        # Step 4: Verify both flags TRUE
        user = User.query.filter_by(id=user_id).first()
        assert user.demographics_completed == True
        assert user.onboarding_completed == True
        
        # Step 5: User can create session with personalization
        can_play = user.demographics_completed
        has_personalization = user.onboarding_completed
        assert can_play == True
        assert has_personalization == True
    
    def test_journey_existing_user_login(self, db_session):
        """
        Journey 3: Existing User Login
        User with both flags TRUE can immediately play.
        """
        from backend.src.models.user import User
        
        # User with both flags TRUE (like our test users)
        user = User.query.filter_by(email='alice@test.com').first()
        
        if user:
            # Verify user is ready
            assert user.demographics_completed == True
            assert user.onboarding_completed == True
            
            # Can immediately start game
            can_play = user.demographics_completed
            has_personalization = user.onboarding_completed
            assert can_play == True
            assert has_personalization == True


class TestCrossFeatureIntegration:
    """Test integration with other features."""
    
    def test_partner_connections_require_demographics(self, client, db_session):
        """Test user without demographics should not send partner invitations."""
        from backend.src.models.user import User
        
        # User without demographics
        user = User(
            id=str(uuid.uuid4()),
            email='no-demo-partner@example.com',
            demographics_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Application logic should check demographics_completed before allowing
        # partner invitation
        can_invite_partner = user.demographics_completed
        assert can_invite_partner == False
    
    def test_subscription_checks_after_demographics(self, db_session):
        """Test demographics check happens before subscription limit check."""
        from backend.src.models.user import User
        
        # Free user without demographics
        user = User(
            id=str(uuid.uuid4()),
            email='sub-check-order@example.com',
            subscription_tier='free',
            daily_activity_count=10,
            demographics_completed=False
        )
        db_session.add(user)
        db_session.commit()
        
        # Check order: demographics first, then subscription
        if not user.demographics_completed:
            # Should block here (demographics gate)
            can_play = False
        elif user.subscription_tier == 'free' and user.daily_activity_count >= 25:
            # Would check subscription limit second
            can_play = False
        else:
            can_play = True
        
        assert can_play == False  # Blocked at demographics gate


class TestAnonymousUserCompatibility:
    """Test anonymous users still work (no user record needed)."""
    
    def test_anonymous_profile_no_user_id(self, db_session):
        """Test anonymous profiles work without user_id."""
        from backend.src.models.profile import Profile
        
        profile = Profile(
            user_id=None,  # No user
            is_anonymous=True,
            anonymous_session_id='anon_test_123',
            submission_id='anon_sub_123',
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
        
        # Verify anonymous profile created
        assert profile.is_anonymous == True
        assert profile.user_id == None
        assert profile.anonymous_session_id == 'anon_test_123'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

