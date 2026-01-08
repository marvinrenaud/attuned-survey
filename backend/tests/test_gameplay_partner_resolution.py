
import pytest
import uuid
from flask import Flask
from src.extensions import db
from src.models.user import User
from src.models.profile import Profile
from src.models.partner import PartnerConnection
from src.routes.gameplay import _resolve_player, gameplay_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def create_user(user_id, name, anatomy=None):
    uid = uuid.UUID(user_id)
    user = User(id=uid, email=f"{name}@test.com", display_name=name)
    
    if anatomy:
        if 'penis' in anatomy: user.has_penis = True
        if 'vagina' in anatomy: user.has_vagina = True
        if 'breasts' in anatomy: user.has_breasts = True
    
    db.session.add(user)
    
    if anatomy:
        profile = Profile(
            user_id=uid,
            submission_id=f"sub_{user_id}",
            anatomy={'anatomy_self': anatomy, 'anatomy_preference': []},
            power_dynamic={}, arousal_propensity={}, domain_scores={}, activities={}, truth_topics={}, boundaries={}
        )
        db.session.add(profile)
    
    db.session.commit()
    return user

def create_connection(requester_id, recipient_id, status='accepted'):
    conn = PartnerConnection(
        requester_user_id=requester_id,
        recipient_user_id=recipient_id,
        recipient_email="test@test.com",
        status=status,
        connection_token=str(uuid.uuid4()),
        expires_at=None # Assume simplified for test or valid date
    )
    # Fix: expires_at cannot be None usually, but let's see model definition.
    # Model says nullable=False.
    from datetime import datetime, timedelta
    conn.expires_at = datetime.utcnow() + timedelta(days=1)
    
    db.session.add(conn)
    db.session.commit()
    return conn

def test_resolve_player_auth_user(app):
    """Test that resolving the auth user always looks up DB."""
    uid = str(uuid.uuid4())
    with app.app_context():
        create_user(uid, "Auth User", anatomy=['penis'])
        
        # Pass minimal data
        player_data = {"id": uid}
        
        resolved = _resolve_player(player_data, uid)
        
        assert resolved['name'] == "Auth User"
        assert resolved['anatomy'] == ['penis']

def test_resolve_player_partner_no_connection(app):
    """Test that partner *without* connection returns guest/fallback data."""
    auth_id = str(uuid.uuid4())
    partner_id = str(uuid.uuid4())
    
    with app.app_context():
        create_user(auth_id, "Auth User")
        create_user(partner_id, "Partner User", anatomy=['vagina'])
        
        # Check logic: current code only looks up if user_id == auth_id
        player_data = {"id": partner_id} 
        
        resolved = _resolve_player(player_data, auth_id)
        
        # Should NOT look up DB (security feature)
        # So name should be Guest (default) and anatomy should be empty
        assert resolved['name'] == "Guest" 
        assert resolved['anatomy'] == []
        
        # If frontend sent name, custom usage
        player_data_with_name = {"id": partner_id, "name": "Frontend Name"}
        resolved = _resolve_player(player_data_with_name, auth_id)
        assert resolved['name'] == "Frontend Name"
        assert resolved['anatomy'] == [] # Still empty anatomy

def test_resolve_player_partner_with_connection(app):
    """Test that partner *with* connection should look up DB (after fix)."""
    auth_id = str(uuid.uuid4())
    partner_id = str(uuid.uuid4())
    
    with app.app_context():
        create_user(auth_id, "Auth User")
        create_user(partner_id, "Partner User", anatomy=['vagina'])
        
        create_connection(auth_id, partner_id, status='accepted')
        
        # Pass minimal data
        player_data = {"id": partner_id}
        
        resolved = _resolve_player(player_data, auth_id)
        
        # CURRENT BEHAVIOR: Returns Guest because check is strict (id == auth)
        # DESIRED BEHAVIOR: Returns "Partner User"
        
        # This claim should FAIL before the fix is implemented
        assert resolved['name'] == "Partner User"
        assert resolved['anatomy'] == ['vagina']
