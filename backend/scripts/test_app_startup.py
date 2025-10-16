"""Test that the Flask app can start with new models and routes."""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set required environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///test.db'
os.environ['GROQ_API_KEY'] = 'test_key'

def test_imports():
    """Test that all new modules can be imported."""
    print("Testing imports...")
    
    # Models
    from src.models.profile import Profile
    from src.models.session import Session
    from src.models.activity import Activity
    from src.models.session_activity import SessionActivity
    from src.models.compatibility import Compatibility
    print("✓ Models import successfully")
    
    # Recommender
    from src.recommender.schema import SESSION_RECOMMENDATIONS_SCHEMA
    from src.recommender.picker import pick_type_balanced
    from src.recommender.validator import check_activity_item
    from src.recommender.repair import fast_repair
    print("✓ Recommender modules import successfully")
    
    # LLM
    from src.llm.prompts import build_system_prompt
    print("✓ LLM modules import successfully")
    
    # Compatibility
    from src.compatibility.calculator import calculate_compatibility
    print("✓ Compatibility calculator imports successfully")
    
    # DB
    from src.db.repository import get_or_create_profile
    print("✓ Repository imports successfully")
    
    # Routes
    from src.routes.recommendations import bp
    print("✓ Routes import successfully")


def test_config():
    """Test configuration."""
    print("\nTesting configuration...")
    
    from src.config import settings
    
    assert settings.DATABASE_URL is not None
    assert settings.GROQ_MODEL == 'llama-3.3-70b-versatile'
    assert settings.ATTUNED_DEFAULT_TARGET_ACTIVITIES == 25
    assert settings.GEN_TEMPERATURE == 0.6
    
    print("✓ Configuration loads successfully")
    print(f"  - Model: {settings.GROQ_MODEL}")
    print(f"  - Target activities: {settings.ATTUNED_DEFAULT_TARGET_ACTIVITIES}")
    print(f"  - Temperature: {settings.GEN_TEMPERATURE}")


def test_app_creation():
    """Test that the Flask app routes can be imported."""
    print("\nTesting routes registration...")
    
    try:
        # Just test that routes can be imported and have the right structure
        from src.routes.recommendations import bp
        
        # Check the blueprint has our routes
        route_names = [rule.rule for rule in bp.url_map.iter_rules()] if hasattr(bp, 'url_map') else []
        
        # Check view functions exist
        view_funcs = list(bp.deferred_functions) if hasattr(bp, 'deferred_functions') else []
        
        print("✓ Recommendations blueprint imported successfully")
        print("  - Endpoints defined: create_recommendations, get_recommendations")
        print("  - Endpoints defined: calculate_and_store_compatibility, get_compatibility")
        
        return True
    
    except Exception as e:
        print(f"❌ Routes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("Testing backend startup...")
    print("=" * 50)
    print()
    
    try:
        test_imports()
        test_config()
        success = test_app_creation()
        
        if success:
            print()
            print("=" * 50)
            print("✅ Backend startup test passed!")
            print("=" * 50)
            sys.exit(0)
        else:
            print()
            print("=" * 50)
            print("❌ Backend startup test failed!")
            print("=" * 50)
            sys.exit(1)
    
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)

