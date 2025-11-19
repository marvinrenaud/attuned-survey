"""
Test API routes for syntax and structure.
"""
import pytest
import sys
import os
from pathlib import Path

# Test imports work
def test_auth_routes_import():
    """Test that auth routes can be imported."""
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from backend.src.routes import auth
        assert hasattr(auth, 'auth_bp')
    except ImportError as e:
        pytest.fail(f"Failed to import auth routes: {e}")


def test_partners_routes_import():
    """Test that partners routes can be imported."""
    try:
        from backend.src.routes import partners
        assert hasattr(partners, 'partners_bp')
    except ImportError as e:
        pytest.fail(f"Failed to import partners routes: {e}")


def test_subscriptions_routes_import():
    """Test that subscriptions routes can be imported."""
    try:
        from backend.src.routes import subscriptions
        assert hasattr(subscriptions, 'subscriptions_bp')
    except ImportError as e:
        pytest.fail(f"Failed to import subscriptions routes: {e}")


def test_profile_sharing_routes_import():
    """Test that profile_sharing routes can be imported."""
    try:
        from backend.src.routes import profile_sharing
        assert hasattr(profile_sharing, 'profile_sharing_bp')
    except ImportError as e:
        pytest.fail(f"Failed to import profile_sharing routes: {e}")


class TestAuthRoutesStructure:
    """Test auth routes file structure."""
    
    def test_auth_routes_file_exists(self):
        """Test that auth.py exists."""
        auth_file = Path(__file__).parent.parent / 'src' / 'routes' / 'auth.py'
        assert auth_file.exists()
    
    def test_auth_routes_has_endpoints(self):
        """Test that auth routes has expected endpoints."""
        auth_file = Path(__file__).parent.parent / 'src' / 'routes' / 'auth.py'
        content = auth_file.read_text()
        
        # Check for route decorators
        assert '@auth_bp.route' in content
        assert '/register' in content
        assert '/login' in content
        assert '/user/<user_id>' in content
    
    def test_auth_routes_has_methods(self):
        """Test that auth routes has proper HTTP methods."""
        auth_file = Path(__file__).parent.parent / 'src' / 'routes' / 'auth.py'
        content = auth_file.read_text()
        
        assert "methods=['POST']" in content
        assert "methods=['GET']" in content
        assert "methods=['PATCH']" in content or "methods=['PUT']" in content
        assert "methods=['DELETE']" in content


class TestPartnersRoutesStructure:
    """Test partners routes file structure."""
    
    def test_partners_routes_file_exists(self):
        """Test that partners.py exists."""
        partners_file = Path(__file__).parent.parent / 'src' / 'routes' / 'partners.py'
        assert partners_file.exists()
    
    def test_partners_routes_has_endpoints(self):
        """Test that partners routes has expected endpoints."""
        partners_file = Path(__file__).parent.parent / 'src' / 'routes' / 'partners.py'
        content = partners_file.read_text()
        
        assert '@partners_bp.route' in content
        assert '/connect' in content
        assert '/accept' in content
        assert '/decline' in content
        assert '/remembered' in content


class TestSubscriptionsRoutesStructure:
    """Test subscriptions routes file structure."""
    
    def test_subscriptions_routes_file_exists(self):
        """Test that subscriptions.py exists."""
        subs_file = Path(__file__).parent.parent / 'src' / 'routes' / 'subscriptions.py'
        assert subs_file.exists()
    
    def test_subscriptions_routes_has_endpoints(self):
        """Test that subscriptions routes has expected endpoints."""
        subs_file = Path(__file__).parent.parent / 'src' / 'routes' / 'subscriptions.py'
        content = subs_file.read_text()
        
        assert '@subscriptions_bp.route' in content
        assert '/validate' in content
        assert '/check-limit' in content
        assert '/increment-activity' in content
        assert '/webhook' in content


class TestProfileSharingRoutesStructure:
    """Test profile_sharing routes file structure."""
    
    def test_profile_sharing_routes_file_exists(self):
        """Test that profile_sharing.py exists."""
        ps_file = Path(__file__).parent.parent / 'src' / 'routes' / 'profile_sharing.py'
        assert ps_file.exists()
    
    def test_profile_sharing_routes_has_endpoints(self):
        """Test that profile_sharing routes has expected endpoints."""
        ps_file = Path(__file__).parent.parent / 'src' / 'routes' / 'profile_sharing.py'
        content = ps_file.read_text()
        
        assert '@profile_sharing_bp.route' in content
        assert '/settings' in content
        assert '/partner-profile' in content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

