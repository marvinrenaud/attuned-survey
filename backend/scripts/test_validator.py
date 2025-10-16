"""Test activity validator logic."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.recommender.validator import check_activity_item, is_rating_compatible


def test_intensity_window():
    """Test intensity window validation."""
    # Valid: seq 3 (warmup) should allow intensity 1-2
    activity = {
        'type': 'truth',
        'rating': 'R',
        'intensity': 2,
        'script': {'steps': [{'actor': 'A', 'do': 'Share your favorite memory'}]},
        'checks': {'respects_hard_limits': True, 'maybe_items_present': False}
    }
    
    is_valid, error = check_activity_item(activity, seq=3, rating='R', target_activities=25)
    assert is_valid, f"Valid warmup activity failed: {error}"
    print(f"✓ Valid warmup activity passed")
    
    # Invalid: seq 3 (warmup) should reject intensity 5
    activity['intensity'] = 5
    is_valid, error = check_activity_item(activity, seq=3, rating='R', target_activities=25)
    assert not is_valid, "High intensity in warmup should fail"
    assert "out of range" in error.lower(), f"Expected range error, got: {error}"
    print(f"✓ Invalid warmup intensity rejected: {error}")


def test_maybe_items_before_step_6():
    """Test that maybe items are blocked before step 6."""
    activity = {
        'type': 'dare',
        'rating': 'R',
        'intensity': 2,
        'script': {'steps': [{'actor': 'A', 'do': 'Try something new together'}]},
        'checks': {
            'respects_hard_limits': True,
            'maybe_items_present': True  # This should fail before step 6
        }
    }
    
    # Should fail at step 3
    is_valid, error = check_activity_item(activity, seq=3, rating='R')
    assert not is_valid, "Maybe item before step 6 should fail"
    assert "maybe" in error.lower(), f"Expected maybe error, got: {error}"
    print(f"✓ Maybe items blocked before step 6: {error}")
    
    # Should pass at step 10
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert is_valid, f"Maybe item after step 6 should pass: {error}"
    print(f"✓ Maybe items allowed after step 6")


def test_script_length():
    """Test script step length validation."""
    # Too short (< 3 words)
    activity = {
        'type': 'truth',
        'rating': 'R',
        'intensity': 2,
        'script': {'steps': [{'actor': 'A', 'do': 'Hi'}]},
        'checks': {'respects_hard_limits': True, 'maybe_items_present': False}
    }
    
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert not is_valid, "Too short script should fail"
    assert "too short" in error.lower(), f"Expected length error, got: {error}"
    print(f"✓ Too-short script rejected: {error}")
    
    # Too long (> 20 words)
    activity['script']['steps'][0]['do'] = ' '.join(['word'] * 25)
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert not is_valid, "Too long script should fail"
    assert "too long" in error.lower(), f"Expected length error, got: {error}"
    print(f"✓ Too-long script rejected: {error}")
    
    # Just right (6-15 words ideal)
    activity['script']['steps'][0]['do'] = 'Share your favorite memory from this year with honesty'
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert is_valid, f"Good length script should pass: {error}"
    print(f"✓ Proper length script accepted")


def test_too_many_steps():
    """Test that > 2 steps are rejected."""
    activity = {
        'type': 'dare',
        'rating': 'R',
        'intensity': 3,
        'script': {
            'steps': [
                {'actor': 'A', 'do': 'First step here'},
                {'actor': 'B', 'do': 'Second step here'},
                {'actor': 'A', 'do': 'Third step here'}  # Too many!
            ]
        },
        'checks': {'respects_hard_limits': True, 'maybe_items_present': False}
    }
    
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert not is_valid, "More than 2 steps should fail"
    assert "too many steps" in error.lower(), f"Expected steps error, got: {error}"
    print(f"✓ Too many steps rejected: {error}")


def test_hard_limits_violation():
    """Test that hard limit violations are caught."""
    activity = {
        'type': 'dare',
        'rating': 'R',
        'intensity': 3,
        'script': {'steps': [{'actor': 'A', 'do': 'Try bondage together safely'}]},
        'checks': {
            'respects_hard_limits': False,  # Marked as violating
            'maybe_items_present': False
        }
    }
    
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert not is_valid, "Hard limit violation should fail"
    assert "hard limit" in error.lower(), f"Expected hard limit error, got: {error}"
    print(f"✓ Hard limit violation rejected: {error}")


def test_rating_compatibility():
    """Test rating compatibility checks."""
    # G session should only allow G activities
    assert is_rating_compatible('G', 'G'), "G activity in G session should pass"
    assert not is_rating_compatible('R', 'G'), "R activity in G session should fail"
    assert not is_rating_compatible('X', 'G'), "X activity in G session should fail"
    
    # R session should allow G and R
    assert is_rating_compatible('G', 'R'), "G activity in R session should pass"
    assert is_rating_compatible('R', 'R'), "R activity in R session should pass"
    assert not is_rating_compatible('X', 'R'), "X activity in R session should fail"
    
    # X session should allow all
    assert is_rating_compatible('G', 'X'), "G activity in X session should pass"
    assert is_rating_compatible('R', 'X'), "R activity in X session should pass"
    assert is_rating_compatible('X', 'X'), "X activity in X session should pass"
    
    print(f"✓ Rating compatibility rules correct")


def test_invalid_actor_labels():
    """Test that invalid actor labels are rejected."""
    activity = {
        'type': 'truth',
        'rating': 'R',
        'intensity': 2,
        'script': {'steps': [{'actor': 'C', 'do': 'This has invalid actor'}]},  # Should be A or B
        'checks': {'respects_hard_limits': True, 'maybe_items_present': False}
    }
    
    is_valid, error = check_activity_item(activity, seq=10, rating='R')
    assert not is_valid, "Invalid actor label should fail"
    assert "actor" in error.lower(), f"Expected actor error, got: {error}"
    print(f"✓ Invalid actor labels rejected: {error}")


if __name__ == '__main__':
    print("Testing validator logic...")
    print()
    
    try:
        test_intensity_window()
        test_maybe_items_before_step_6()
        test_script_length()
        test_too_many_steps()
        test_hard_limits_violation()
        test_rating_compatibility()
        test_invalid_actor_labels()
        
        print()
        print("=" * 50)
        print("✅ All validator tests passed!")
        print("=" * 50)
        sys.exit(0)
    
    except AssertionError as e:
        print()
        print("=" * 50)
        print(f"❌ Test failed: {e}")
        print("=" * 50)
        sys.exit(1)
    
    except Exception as e:
        print()
        print("=" * 50)
        print(f"❌ Unexpected error: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        sys.exit(1)

