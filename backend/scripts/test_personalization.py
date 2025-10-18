"""Test personalization scoring engine."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.recommender.scoring import (
    score_mutual_interest,
    score_power_alignment,
    score_domain_fit,
    score_activity_for_players
)


def test_mutual_interest():
    """Test mutual interest scoring."""
    print("Test 2.1: Mutual Interest Scoring")
    print("=" * 60)
    
    # Test 1: Both love massage (0.9)
    score = score_mutual_interest(
        ['massage'],
        {'massage': 0.9, 'oral': 0.5},
        {'massage': 0.9, 'oral': 0.5}
    )
    assert score == 1.0, f"Both love massage should score 1.0, got {score}"
    print(f"✓ Both love massage (0.9): {score} (expected 1.0)")
    
    # Test 2: One yes, one maybe
    score = score_mutual_interest(
        ['bondage'],
        {'bondage': 0.9},  # Loves it
        {'bondage': 0.5}   # Neutral
    )
    assert score == 0.6, f"Yes/Maybe should score 0.6, got {score}"
    print(f"✓ One yes (0.9), one maybe (0.5): {score} (expected 0.6)")
    
    # Test 3: One yes, one no - mismatch
    score = score_mutual_interest(
        ['impact'],
        {'impact': 0.9},  # Loves it
        {'impact': 0.1}   # Hates it
    )
    assert score == 0.1, f"Yes/No mismatch should score 0.1, got {score}"
    print(f"✓ One yes (0.9), one no (0.1): {score} (expected 0.1)")
    
    # Test 4: No preference keys
    score = score_mutual_interest([], {}, {})
    assert score == 0.5, f"No preferences should score 0.5, got {score}"
    print(f"✓ No preference keys: {score} (expected 0.5)")
    
    print()


def test_power_alignment():
    """Test power alignment scoring."""
    print("Test 2.2: Power Alignment Scoring")
    print("=" * 60)
    
    # Test 1: Neutral activity - always works
    score = score_power_alignment('neutral', 'Top', 'Bottom')
    assert score == 1.0, f"Neutral should always score 1.0, got {score}"
    print(f"✓ Neutral activity (any players): {score} (expected 1.0)")
    
    # Test 2: Top activity with Top+Bottom - perfect
    score = score_power_alignment('top', 'Top', 'Bottom')
    assert score == 1.0, f"Top activity with Top+Bottom should score 1.0, got {score}"
    print(f"✓ Top activity + Top+Bottom players: {score} (expected 1.0)")
    
    # Test 3: Top activity with both Bottom - filtered
    score = score_power_alignment('top', 'Bottom', 'Bottom')
    assert score == 0.0, f"Top activity with both Bottom should score 0.0, got {score}"
    print(f"✓ Top activity + Both Bottom: {score} (expected 0.0 - FILTERED)")
    
    # Test 4: Bottom activity with Top+Bottom - perfect
    score = score_power_alignment('bottom', 'Top', 'Bottom')
    assert score == 1.0, f"Bottom activity with Top+Bottom should score 1.0, got {score}"
    print(f"✓ Bottom activity + Top+Bottom players: {score} (expected 1.0)")
    
    # Test 5: Bottom activity with both Top - filtered
    score = score_power_alignment('bottom', 'Top', 'Top')
    assert score == 0.0, f"Bottom activity with both Top should score 0.0, got {score}"
    print(f"✓ Bottom activity + Both Top: {score} (expected 0.0 - FILTERED)")
    
    # Test 6: Top activity with Switch - works but not perfect
    score = score_power_alignment('top', 'Switch', 'Bottom')
    assert score == 0.6, f"Top activity with Switch+Bottom should score 0.6, got {score}"
    print(f"✓ Top activity + Switch+Bottom: {score} (expected 0.6 - Switch adapts)")
    
    # Test 7: Switch activity - always works
    score = score_power_alignment('switch', 'Top', 'Top')
    assert score == 1.0, f"Switch activity should always work, got {score}"
    print(f"✓ Switch activity (any players): {score} (expected 1.0)")
    
    print()


def test_complete_scoring():
    """Test complete activity scoring with all components."""
    print("Test 2.3: Complete Activity Scoring")
    print("=" * 60)
    
    # Perfect match: Top+Bottom, both love massage, high sensual domain
    activity = {
        'power_role': 'neutral',
        'preference_keys': ['massage', 'sensual'],
        'domains': ['sensual', 'connection']
    }
    
    player_a = {
        'power_dynamic': {'orientation': 'Top', 'intensity': 0.8},
        'activities': {'massage': 0.9, 'sensual': 0.9},
        'domain_scores': {'sensual': 0.9, 'connection': 0.8}
    }
    
    player_b = {
        'power_dynamic': {'orientation': 'Bottom', 'intensity': 0.7},
        'activities': {'massage': 0.9, 'sensual': 0.8},
        'domain_scores': {'sensual': 0.9, 'connection': 0.9}
    }
    
    result = score_activity_for_players(activity, player_a, player_b)
    
    print(f"Activity: Neutral, massage/sensual, sensual domain")
    print(f"Players: Top+Bottom, both love massage (0.9), high sensual")
    print()
    print(f"  Mutual interest: {result['mutual_interest_score']} (weight: 0.5)")
    print(f"  Power alignment: {result['power_alignment_score']} (weight: 0.3)")
    print(f"  Domain fit:      {result['domain_fit_score']} (weight: 0.2)")
    print(f"  ─────────────────────────")
    print(f"  Overall score:   {result['overall_score']}")
    
    # Should be very high (near 1.0)
    assert result['overall_score'] > 0.9, f"Perfect match should score > 0.9, got {result['overall_score']}"
    print(f"\n✓ Perfect match scores high: {result['overall_score']} > 0.9")
    
    # Test mismatch
    activity_mismatch = {
        'power_role': 'top',  # Needs someone to take control
        'preference_keys': ['impact', 'pain'],
        'domains': ['edge', 'power']
    }
    
    # Both Bottom players (can't do top activities)
    player_c = {
        'power_dynamic': {'orientation': 'Bottom', 'intensity': 0.5},
        'activities': {'impact': 0.1, 'pain': 0.1},  # Hate impact
        'domain_scores': {'edge': 0.2, 'power': 0.3}
    }
    
    player_d = {
        'power_dynamic': {'orientation': 'Bottom', 'intensity': 0.6},
        'activities': {'impact': 0.2, 'pain': 0.1},  # Also hate impact
        'domain_scores': {'edge': 0.3, 'power': 0.2}
    }
    
    result2 = score_activity_for_players(activity_mismatch, player_c, player_d)
    
    print()
    print(f"Activity: Top role, impact/pain, edge domain")
    print(f"Players: Both Bottom, hate impact (0.1), low edge")
    print()
    print(f"  Mutual interest: {result2['mutual_interest_score']}")
    print(f"  Power alignment: {result2['power_alignment_score']}")
    print(f"  Domain fit:      {result2['domain_fit_score']}")
    print(f"  ─────────────────────────")
    print(f"  Overall score:   {result2['overall_score']}")
    
    # Should be very low (power=0, mutual=low)
    assert result2['overall_score'] < 0.3, f"Mismatch should score < 0.3, got {result2['overall_score']}"
    print(f"\n✓ Mismatch scores low: {result2['overall_score']} < 0.3")
    
    print()


if __name__ == '__main__':
    print("Testing Personalization Scoring Engine")
    print("=" * 60)
    print()
    
    try:
        test_mutual_interest()
        test_power_alignment()
        test_complete_scoring()
        
        print("=" * 60)
        print("✅ All scoring engine tests PASSED!")
        print("=" * 60)
        sys.exit(0)
    
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ Test failed: {e}")
        print("=" * 60)
        sys.exit(1)
    
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)

