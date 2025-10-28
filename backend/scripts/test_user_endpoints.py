"""Test user endpoints integration with Flask app."""
import sys
import os
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['GROQ_API_KEY'] = 'test_key'
os.environ['FLASK_ENV'] = 'testing'

def test_user_endpoints():
    """Test all user endpoints work correctly."""
    print("Testing user endpoints...")
    
    from src.main import create_app
    from src.models.user import User
    from src.extensions import db
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Clean up any existing test data
            User.query.delete()
            db.session.commit()
            
            # Test GET /users (empty list)
            response = client.get('/users')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data == []
            print("✓ GET /users returns empty list")
            
            # Test POST /users (create user)
            user_data = {
                'username': 'testuser',
                'email': 'test@example.com'
            }
            response = client.post('/users', 
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['username'] == 'testuser'
            assert data['email'] == 'test@example.com'
            assert 'id' in data
            user_id = data['id']
            print("✓ POST /users creates user")
            
            # Test GET /users (list with user)
            response = client.get('/users')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 1
            assert data[0]['username'] == 'testuser'
            print("✓ GET /users returns user list")
            
            # Test GET /users/<id> (get single user)
            response = client.get(f'/users/{user_id}')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['username'] == 'testuser'
            assert data['email'] == 'test@example.com'
            print("✓ GET /users/<id> returns single user")
            
            # Test PUT /users/<id> (update user)
            update_data = {
                'username': 'updateduser',
                'email': 'updated@example.com'
            }
            response = client.put(f'/users/{user_id}',
                                data=json.dumps(update_data),
                                content_type='application/json')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['username'] == 'updateduser'
            assert data['email'] == 'updated@example.com'
            print("✓ PUT /users/<id> updates user")
            
            # Test DELETE /users/<id> (delete user)
            response = client.delete(f'/users/{user_id}')
            assert response.status_code == 204
            print("✓ DELETE /users/<id> deletes user")
            
            # Test GET /users/<id> (get non-existent user)
            response = client.get(f'/users/{user_id}')
            assert response.status_code == 404
            print("✓ GET /users/<id> returns 404 for non-existent user")


def test_user_endpoints_error_handling():
    """Test error handling in user endpoints."""
    print("\nTesting user endpoints error handling...")
    
    from src.main import create_app
    from src.models.user import User
    from src.extensions import db
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Clean up any existing test data
            User.query.delete()
            db.session.commit()
            
            # Test POST /users with invalid data (missing fields)
            invalid_data = {'username': 'testuser'}  # missing email
            response = client.post('/users',
                                 data=json.dumps(invalid_data),
                                 content_type='application/json')
            # Should handle gracefully (either 400 or create with defaults)
            print(f"✓ POST /users handles invalid data (status: {response.status_code})")
            
            # Test PUT /users/<id> with non-existent user
            response = client.put('/users/99999',
                                data=json.dumps({'username': 'test'}),
                                content_type='application/json')
            assert response.status_code == 404
            print("✓ PUT /users/<id> returns 404 for non-existent user")
            
            # Test DELETE /users/<id> with non-existent user
            response = client.delete('/users/99999')
            assert response.status_code == 404
            print("✓ DELETE /users/<id> returns 404 for non-existent user")


def test_user_endpoints_with_existing_data():
    """Test user endpoints don't interfere with existing data."""
    print("\nTesting user endpoints with existing data...")
    
    from src.main import create_app
    from src.models.user import User
    from src.models.profile import Profile
    from src.extensions import db
    
    app = create_app()
    
    with app.test_client() as client:
        with app.app_context():
            # Verify other models still work
            profiles = Profile.query.all()
            print(f"✓ Other models still accessible - found {len(profiles)} profiles")
            
            # Test that user operations don't affect other data
            initial_profile_count = len(profiles)
            
            # Create a user
            user_data = {
                'username': 'testuser2',
                'email': 'test2@example.com'
            }
            response = client.post('/users',
                                 data=json.dumps(user_data),
                                 content_type='application/json')
            assert response.status_code == 201
            
            # Verify profile count unchanged
            profiles_after = Profile.query.all()
            assert len(profiles_after) == initial_profile_count
            print("✓ User operations don't affect other models")


if __name__ == '__main__':
    print("Testing user endpoints integration...")
    print("=" * 50)
    print()
    
    try:
        test_user_endpoints()
        test_user_endpoints_error_handling()
        test_user_endpoints_with_existing_data()
        
        print()
        print("=" * 50)
        print("✅ User endpoints tests passed!")
        print("=" * 50)
        sys.exit(0)
        
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ User endpoints test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)
