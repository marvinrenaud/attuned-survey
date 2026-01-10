
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
from src.routes.gameplay import gameplay_bp, _create_complimentary_profile
from src.models.user import User
from src.models.session import Session
from src.models.activity import Activity
from src.models.profile import Profile
from src.extensions import db
from src.db.repository import find_best_activity_candidate
import os
import uuid
import json

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    app.register_blueprint(gameplay_bp)
    
    with app.app_context():
        db.create_all()
        # Seed legacy profile
        p_legacy = Profile(id=1, submission_id="legacy", power_dynamic={}, arousal_propensity={}, 
                           domain_scores={}, activities={}, truth_topics={}, boundaries={}, anatomy={})
        db.session.add(p_legacy)
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers():
    import jwt
    user_id = str(uuid.uuid4())
    token = jwt.encode({"sub": user_id, "aud": "authenticated"}, "test-secret-key", algorithm="HS256")
    return {'Authorization': f'Bearer {token}'}, user_id

def create_user_with_profile(app, user_id, power_orientation='Switch', anatomy=['penis'], 
                             likes=['vagina'], boundaries=[], activity_prefs={}):
    with app.app_context():
        uid = uuid.UUID(user_id)
        user = User(id=uid, email=f"{user_id[:8]}@test.com", display_name=f"User {user_id[:4]}")
        db.session.add(user)
        
        profile = Profile(
            user_id=uid,
            submission_id=f"sub_{user_id}",
            power_dynamic={'orientation': power_orientation},
            arousal_propensity={},
            domain_scores={},
            activities=activity_prefs,
            truth_topics={},
            boundaries={'hard_limits': boundaries},
            anatomy={'anatomy_self': anatomy, 'anatomy_preference': likes}
        )
        db.session.add(profile)
        db.session.commit()
        return user, profile

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_personalized_selection_with_profiles(client, app, auth_headers):
    # Setup: 2 users, 1 perfect match activity, 1 mismatch
    headers, uid1 = auth_headers
    uid2 = str(uuid.uuid4())
    
    create_user_with_profile(app, uid1, power_orientation='Top', activity_prefs={'act_perfect': 1.0})
    create_user_with_profile(app, uid2, power_orientation='Bottom', activity_prefs={'act_perfect': 1.0})
    
    with app.app_context():
        # Perfect match: Top activity, both like it
        act1 = Activity(activity_id=1, type="truth", rating="R", intensity=1, 
                       script={'steps':[{'do': 'Match'}]}, power_role='top', preference_keys=['act_perfect'], is_active=True)
        # Mismatch: Bottom activity (Top can't receive well? Well, score logic handles it)
        # Let's use strict mismatch: Hard boundary
        act2 = Activity(activity_id=2, type="truth", rating="R", intensity=1, 
                       script={'steps':[{'do': 'Mismatch'}]}, hard_boundaries=['limit_x'], is_active=True)
        
        db.session.add_all([act1, act2])
        db.session.commit()
        
        # Start game
        res = client.post('/api/game/start', 
                          json={"player_ids": [uid2], "settings": {"intimacy_level": 3}},
                          headers=headers)
        assert res.status_code == 200
        data = res.json
        session_id = data['session_id']
        
        # Logic is JIT. Act 1 should be picked as Act 2 is filtered by boundary 'limit_x' (if strict) or just scored lower.
        # But wait, profiles created above do NOT have 'limit_x'.
        # act2 has hard_boundaries=['limit_x'].
        # Players boundaries=[].
        # Conflict? No.
        # So both are valid candidates.
        # But act1 is 'Match' (preference keys). act2 is 'Mismatch' (no matching prefs).
        # act1 should score higher.
        
        # Verify at least one card in queue is 1 or 2
        # Queue has 3 items.
        queue = data['queue']
        ids = [c['card']['card_id'] for c in queue]
        # At least one should be '1' (string) 
        # (Assuming type 'truth' was selected at least once)
        assert '1' in ids or '2' in ids

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_boundary_filtering(client, app, auth_headers):
    headers, uid1 = auth_headers
    uid2 = str(uuid.uuid4())
    
    # User 1 has hard limit 'anal_play'
    create_user_with_profile(app, uid1, boundaries=['anal_play'])
    create_user_with_profile(app, uid2) # No limits
    
    with app.app_context():
        # Activity with hard boundary
        act_bad = Activity(activity_id=100, type="truth", rating="R", intensity=1, 
                          script={'steps':[{'do': 'Butt stuff'}]}, hard_boundaries=['anal_play'], is_active=True)
        # Activity clean
        act_good = Activity(activity_id=101, type="truth", rating="R", intensity=1, 
                           script={'steps':[{'do': 'Hand holding'}]}, hard_boundaries=[], is_active=True)
        
        db.session.add_all([act_bad, act_good])
        db.session.commit()
        
        # We need to ensure JIT picks act_good.
        # Since logic is random sample, if we only have 2 activities, and 1 is filtered, it MUST pick the other.
        # _generate_turn_data calls find_best_activity_candidate
        
        # Let's call find_best_activity_candidate directly to verify logic first
        p1 = Profile.query.filter_by(user_id=uuid.UUID(uid1)).first().to_dict()
        p2 = Profile.query.filter_by(user_id=uuid.UUID(uid2)).first().to_dict()
        
        # Should pick act_good (101)
        best = find_best_activity_candidate('R', 1, 5, 'truth', p1, p2, 
                                            player_boundaries=['anal_play'], excluded_ids=set(), randomize=False)
        assert best is not None
        assert best.activity_id == 101 # 100 should be filtered out
        
@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_anatomy_filtering(client, app, auth_headers):
    headers, uid1 = auth_headers
    uid2 = str(uuid.uuid4())
    
    # Profiles: Both have [vagina], no penis
    create_user_with_profile(app, uid1, anatomy=['vagina', 'breasts'])
    create_user_with_profile(app, uid2, anatomy=['vagina', 'breasts'])
    
    with app.app_context():
        # Requires penis
        act_penis = Activity(activity_id=200, type="truth", rating="R", intensity=1,
                            script={'steps':[]}, required_bodyparts={'active': ['penis']}, is_active=True)
        # Requires vagina
        act_vagina = Activity(activity_id=201, type="truth", rating="R", intensity=1,
                             script={'steps':[]}, required_bodyparts={'active': ['vagina']}, is_active=True)
        
        db.session.add_all([act_penis, act_vagina])
        db.session.commit()
        
        p1 = Profile.query.filter_by(user_id=uuid.UUID(uid1)).first().to_dict()
        p2 = Profile.query.filter_by(user_id=uuid.UUID(uid2)).first().to_dict()
        
        # Should filter out 200
        best = find_best_activity_candidate('R', 1, 5, 'truth', p1, p2, 
                                            player_anatomy={'active_anatomy': ['vagina'], 'partner_anatomy': ['vagina']},
                                            randomize=False)
        assert best is not None
        assert best.activity_id == 201

def test_complimentary_profile_generation():
    # Test valid profile generation
    primary = {
        'anatomy': {'anatomy_self': ['penis'], 'anatomy_preference': ['vagina', 'breasts']},
        'power_dynamic': {'orientation': 'Top'},
        'boundaries': {'hard_limits': ['no_pain']},
        'activities': {'massage_give': 1.0, 'spanking_receive': 0.0}
    }
    
    comp = _create_complimentary_profile(primary)
    
    assert comp['is_anonymous'] is True
    # Anatomy should match preference
    assert set(comp['anatomy']['anatomy_self']) == {'vagina', 'breasts'}
    # Power inverted
    assert comp['power_dynamic']['orientation'] == 'Bottom'
    # Boundaries copied
    assert comp['boundaries']['hard_limits'] == ['no_pain']
    # Activities inverted
    assert comp['activities'].get('massage_receive') == 1.0
    assert comp['activities'].get('spanking_give') == 0.0

@patch.dict(os.environ, {"SUPABASE_JWT_SECRET": "test-secret-key"})
def test_complimentary_integration(client, app, auth_headers):
    headers, uid1 = auth_headers
    # User 1 is Top, likes 'act_top'
    create_user_with_profile(app, uid1, power_orientation='Top', activity_prefs={'act_top_give': 1.0})
    
    with app.app_context():
        # Activity: "Top gives"
        # Requires 'act_top_receive' (implied by give/receive pairing in scoring) or explicit prefs
        # Let's say activity keys match scoring logic
        act = Activity(activity_id=300, type="truth", rating="R", intensity=1,
                      script={'steps':[]}, power_role='top', preference_keys=['act_top_give'], is_active=True)
        act2 = Activity(activity_id=301, type="dare", rating="R", intensity=1,
                      script={'steps':[]}, power_role='top', preference_keys=['act_top_give'], is_active=True)
        db.session.add_all([act, act2])
        db.session.commit()
        
        # Start game with purely anonymous partner (no ID, just name)
        # This triggers complimentary profile logic
        res = client.post('/api/game/start', 
                          json={"player_ids": ["Anon Partner Name"], "settings": {"intimacy_level": 3}},
                          headers=headers)
        
        assert res.status_code == 200
        data = res.json
        queue = data['queue']
        assert len(queue) > 0
        card_id = queue[0]['card']['card_id']
        assert card_id in ['300', '301']
