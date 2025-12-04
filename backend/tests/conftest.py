"""
Pytest configuration and fixtures for Attuned tests.
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import scoped_session, sessionmaker

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.src.main import create_app
from backend.src.extensions import db


@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': os.getenv('TEST_DATABASE_URL', 'postgresql://localhost/attuned_test'),
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        # Create all tables
        db.create_all()
        yield app
        # Teardown
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        # Bind session to connection
        # Bind session to connection
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # Save old session
        old_session = db.session
        db.session = session
        
        yield session
        
        # Rollback transaction
        transaction.rollback()
        connection.close()
        session.remove()
        db.session = old_session


@pytest.fixture
def test_user_data():
    """Sample user data for testing."""
    return {
        'id': str(uuid.uuid4()),
        'email': 'test@example.com',
        'display_name': 'Test User',
        'auth_provider': 'email',
        'demographics': {
            'gender': 'woman',
            'sexual_orientation': 'bisexual',
            'relationship_structure': 'open'
        }
    }


@pytest.fixture
def test_profile_data():
    """Sample profile data for testing."""
    return {
        'submission_id': f'test_sub_{uuid.uuid4()}',
        'profile_version': '0.4',
        'power_dynamic': {'orientation': 'Switch', 'confidence': 75},
        'arousal_propensity': {'se': 0.7, 'sis_p': 0.3, 'sis_c': 0.5},
        'domain_scores': {
            'sensation': 65,
            'connection': 70,
            'power': 60,
            'exploration': 55,
            'verbal': 75
        },
        'activities': {
            'massage_give': 0.8,
            'oral_give': 0.9,
            'restraints_receive': 0.6
        },
        'truth_topics': {
            'past_experiences': 0.7,
            'fantasies': 0.8
        },
        'boundaries': {
            'hard_limits': [],
            'soft_limits': ['impact'],
            'maybe_items': ['public']
        },
        'anatomy': {
            'anatomy_self': ['vagina', 'breasts'],
            'anatomy_preference': ['penis', 'vagina']
        }
    }


@pytest.fixture
def test_session_data():
    """Sample session data for testing."""
    return {
        'session_id': str(uuid.uuid4()),
        'rating': 'R',
        'intimacy_level': 'R',
        'status': 'active',
        'current_step': 5
    }

