"""
Pytest configuration and fixtures for Attuned tests.
"""
import pytest
import sys
import os
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.ext.compiler import compiles

# 1. Set environment variables BEFORE importing app
# This ensures create_app() uses SQLite and doesn't fail on missing DATABASE_URL
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['FLASK_ENV'] = 'testing'
os.environ['SUPABASE_JWT_SECRET'] = 'test-secret-key'
os.environ['RATELIMIT_ENABLED'] = 'False'
os.environ['PROPAGATE_EXCEPTIONS'] = 'True'

import logging
logging.basicConfig(level=logging.ERROR)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 2. Register SQLite hooks BEFORE importing app
# This ensures that when create_app() runs DDL, it knows how to handle JSONB
@compiles(JSONB, 'sqlite')
def compile_jsonb(element, compiler, **kw):
    return compiler.visit_JSON(element, **kw)

# 3. Import app and extensions
# Note: importing main executes create_app() immediately due to the 'app = create_app()' line at the bottom of main.py
from backend.src.main import create_app
from backend.src.extensions import db, limiter
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event, String
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
from sqlalchemy.dialects.postgresql import UUID as pg_UUID
import uuid
# Import models to ensure they are registered for create_all
from backend.src.models.activity_history import UserActivityHistory

# SQLite UUID handling
@compiles(pg_UUID, 'sqlite')
def compile_uuid(element, compiler, **kw):
    """SQLite: treat UUID as CHAR(36)"""
    return "CHAR(36)"

def make_uuid(val=None):
    """Always returns a uuid.UUID object."""
    if val is None:
        return uuid.uuid4()
    return val if isinstance(val, uuid.UUID) else uuid.UUID(val)

@pytest.fixture(scope='session')
def app():
    """Create application for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'RATELIMIT_ENABLED': False,
        'PROPAGATE_EXCEPTIONS': True,
        'ENV': 'development',  # Forces ConsoleRenderer in logging_config.py
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False}
        }
    })
    
    # Force disable limiter
    limiter.enabled = False
    
    with app.app_context():
        # Enable Foreign Keys for SQLite
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            event.listen(db.engine, 'connect', lambda c, _: c.execute('PRAGMA foreign_keys=ON'))
            
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
        transaction = connection.begin_nested() # Start nested transaction for rollback safety

        
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
        'id': uuid.uuid4(),
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
        'session_id': str(uuid.uuid4()), # Sessions use String ID in some places but UUID in model. Wait. 
        # Session model: session_id = Column(String(128), primary_key=True)
        # So Session ID IS A STRING!
        # Re-checking Session model...
        'rating': 'R',
        'intimacy_level': 'R',
        'status': 'active',
        'current_step': 5
    }
