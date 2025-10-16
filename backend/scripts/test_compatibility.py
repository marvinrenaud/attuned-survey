"""Test compatibility calculator."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.compatibility.calculator import (
    calculate_power_complement,
    calculate_domain_similarity,
    calculate_activity_overlap,
    calculate_truth_overlap,
    calculate_compatibility,
    interpret_compatibility
)


def test_power_complement():
    """Test power dynamic complement calculation."""
    # Perfect complement: Top + Bottom
    power_a = {'orientation': 'Top', 'intensity': 0.8}
    power_b = {'orientation': 'Bottom', 'intensity': 0.7}
    result = calculate_power_complement(power_a, power_b)
    assert result >= 0.8, f"Top+Bottom should be high: {result}"
    print(f"✓ Top+Bottom complement: {result:.2f}")
    
    # Both Switch
    power_a = {'orientation': 'Switch', 'intensity': 0.5}
    power_b = {'orientation': 'Switch', 'intensity': 0.5}
    result = calculate_power_complement(power_a, power_b)
    assert result == 0.85, f"Switch+Switch should be 0.85: {result}"
    print(f"✓ Switch+Switch complement: {result:.2f}")
    
    # Same pole (lower but not zero)
    power_a = {'orientation': 'Top', 'intensity': 0.8}
    power_b = {'orientation': 'Top', 'intensity': 0.7}
    result = calculate_power_complement(power_a, power_b)
    assert result == 0.50, f"Top+Top should be 0.50: {result}"
    print(f"✓ Top+Top complement: {result:.2f}")


def test_domain_similarity():
    """Test domain similarity calculation."""
    domains_a = {
        'dominance': 0.8,
        'submission': 0.2,
        'sensual': 0.7,
        'playful': 0.6
    }
    domains_b = {
        'dominance': 0.3,
        'submission': 0.9,
        'sensual': 0.7,
        'playful': 0.5
    }
    
    # For Top+Bottom pair (complementary)
    power_a = {'orientation': 'Top'}
    power_b = {'orientation': 'Bottom'}
    
    result = calculate_domain_similarity(domains_a, domains_b, power_a, power_b)
    assert 0 <= result <= 1, f"Result should be 0-1: {result}"
    print(f"✓ Domain similarity (complementary): {result:.2f}")
    
    # For Switch+Switch (normal similarity)
    power_a = {'orientation': 'Switch'}
    power_b = {'orientation': 'Switch'}
    
    result = calculate_domain_similarity(domains_a, domains_b, power_a, power_b)
    assert 0 <= result <= 1, f"Result should be 0-1: {result}"
    print(f"✓ Domain similarity (normal): {result:.2f}")


def test_activity_overlap():
    """Test activity overlap calculation."""
    activities_a = {
        'massage': 0.9,
        'kissing': 0.8,
        'bondage': 0.2,
        'oral': 0.7
    }
    activities_b = {
        'massage': 0.9,
        'kissing': 0.7,
        'bondage': 0.1,
        'oral': 0.8
    }
    
    power_a = {'orientation': 'Switch'}
    power_b = {'orientation': 'Switch'}
    
    result = calculate_activity_overlap(activities_a, activities_b, power_a, power_b)
    assert 0 <= result <= 1, f"Result should be 0-1: {result}"
    assert result > 0.5, f"High overlap should score high: {result}"
    print(f"✓ Activity overlap: {result:.2f}")


def test_truth_overlap():
    """Test truth topic overlap."""
    truth_a = {
        'fantasies': 0.8,
        'turn_ons': 0.7,
        'boundaries': 0.9,
        'past_experiences': 0.4
    }
    truth_b = {
        'fantasies': 0.9,
        'turn_ons': 0.8,
        'boundaries': 0.8,
        'past_experiences': 0.3
    }
    
    result = calculate_truth_overlap(truth_a, truth_b)
    assert 0 <= result <= 1, f"Result should be 0-1: {result}"
    assert result > 0.5, f"High overlap should score high: {result}"
    print(f"✓ Truth overlap: {result:.2f}")


def test_full_compatibility():
    """Test full compatibility calculation."""
    player_a = {
        'power_dynamic': {'orientation': 'Top', 'intensity': 0.7},
        'domain_scores': {
            'dominance': 0.8,
            'submission': 0.2,
            'sensual': 0.7
        },
        'activities': {
            'massage': 0.9,
            'kissing': 0.8
        },
        'truth_topics': {
            'fantasies': 0.8,
            'turn_ons': 0.7
        },
        'boundaries': {
            'hard_limits': ['impact']
        }
    }
    
    player_b = {
        'power_dynamic': {'orientation': 'Bottom', 'intensity': 0.6},
        'domain_scores': {
            'dominance': 0.3,
            'submission': 0.9,
            'sensual': 0.8
        },
        'activities': {
            'massage': 0.8,
            'kissing': 0.9
        },
        'truth_topics': {
            'fantasies': 0.9,
            'turn_ons': 0.8
        },
        'boundaries': {
            'hard_limits': []
        }
    }
    
    result = calculate_compatibility(player_a, player_b)
    
    # Verify structure
    assert 'overall_compatibility' in result
    assert 'breakdown' in result
    assert 'mutual_activities' in result
    
    # Check score range
    score = result['overall_compatibility']['score']
    assert 0 <= score <= 100, f"Score should be 0-100: {score}"
    
    # Top+Bottom with good overlap should score well
    assert score >= 60, f"Good compatibility should score ≥60: {score}"
    
    print(f"✓ Full compatibility: {score}% - {result['overall_compatibility']['interpretation']}")
    print(f"  - Power: {result['breakdown']['power_complement']}%")
    print(f"  - Domain: {result['breakdown']['domain_similarity']}%")
    print(f"  - Activity: {result['breakdown']['activity_overlap']}%")
    print(f"  - Truth: {result['breakdown']['truth_overlap']}%")
    print(f"  - Mutual activities: {result['mutual_activities']}")


def test_interpretation():
    """Test compatibility interpretation strings."""
    assert interpret_compatibility(90) == 'Exceptional compatibility'
    assert interpret_compatibility(75) == 'High compatibility'
    assert interpret_compatibility(60) == 'Moderate compatibility'
    assert interpret_compatibility(45) == 'Lower compatibility'
    assert interpret_compatibility(30) == 'Challenging compatibility'
    print(f"✓ Interpretation strings correct")


if __name__ == '__main__':
    print("Testing compatibility calculator...")
    print()
    
    try:
        test_power_complement()
        test_domain_similarity()
        test_activity_overlap()
        test_truth_overlap()
        test_interpretation()
        test_full_compatibility()
        
        print()
        print("=" * 50)
        print("✅ All compatibility tests passed!")
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

