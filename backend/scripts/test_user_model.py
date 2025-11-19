"""Test User model functionality with shared SQLAlchemy instance."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['GROQ_API_KEY'] = 'test_key'
os.environ['FLASK_ENV'] = 'testing'

def test_user_model_imports():
    """Test that User model can be imported correctly."""
    print("Testing User model imports...")
    
    from src.models.user import User
    from src.extensions import db
    
    # Verify User is a SQLAlchemy model
    assert hasattr(User, '__tablename__')
    assert hasattr(User, '__table__')
    
    print("✓ User model imports successfully")
    print(f"  - Table name: {User.__tablename__}")
    print(f"  - Columns: {[col.name for col in User.__table__.columns]}")


def test_user_model_db_instance():
    """Test that User model uses the shared db instance."""
    print("\nTesting User model db instance...")
    
    from src.models.user import User
    from src.extensions import db
    
    # Verify User model is bound to the shared db instance
    # Check that User.__fsa__ points to the shared db instance
    assert User.__fsa__ is db
    
    print("✓ User model uses shared db instance")


def test_user_model_with_app_context():
    """Test User model operations within Flask app context."""
    print("\nTesting User model with app context...")
    
    from src.main import create_app
    from src.models.user import User
    from src.extensions import db
    
    app = create_app()
    
    with app.app_context():
        # Test that User.query works
        users = User.query.all()
        print(f"✓ User.query works - found {len(users)} users")
        
        # Test creating a user
        test_user = User(
            id='550e8400-e29b-41d4-a716-446655440099',
            email='test@example.com',
            display_name='testuser'
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Verify user was created
        created_user = User.query.filter_by(display_name='testuser').first()
        assert created_user is not None
        assert created_user.email == 'test@example.com'
        print("✓ User creation works")
        
        # Test updating user
        created_user.email = 'updated@example.com'
        db.session.commit()
        
        updated_user = User.query.get(created_user.id)
        assert updated_user.email == 'updated@example.com'
        print("✓ User update works")
        
        # Test deleting user
        db.session.delete(created_user)
        db.session.commit()
        
        deleted_user = User.query.get(created_user.id)
        assert deleted_user is None
        print("✓ User deletion works")
        
        # Test to_dict method
        test_user2 = User(
            id='550e8400-e29b-41d4-a716-446655440098',
            email='test2@example.com',
            display_name='testuser2'
        )
        user_dict = test_user2.to_dict()
        assert user_dict['display_name'] == 'testuser2'
        assert user_dict['email'] == 'test2@example.com'
        assert 'id' in user_dict
        print("✓ User.to_dict() works")


def test_user_model_relationships():
    """Test that User model doesn't break other models."""
    print("\nTesting User model relationships...")
    
    from src.main import create_app
    from src.models.user import User
    from src.models.profile import Profile
    from src.extensions import db
    
    app = create_app()
    
    with app.app_context():
        # Verify other models still work
        profiles = Profile.query.all()
        print(f"✓ Other models still work - found {len(profiles)} profiles")
        
        # Verify db session is shared
        assert User.query.session is Profile.query.session
        print("✓ All models share the same db session")


if __name__ == '__main__':
    print("Testing User model functionality...")
    print("=" * 50)
    print()
    
    try:
        test_user_model_imports()
        test_user_model_db_instance()
        test_user_model_with_app_context()
        test_user_model_relationships()
        
        print()
        print("=" * 50)
        print("✅ User model tests passed!")
        print("=" * 50)
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ User model test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)
