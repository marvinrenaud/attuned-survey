"""Test truth/dare picker logic."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.recommender.picker import pick_type_balanced, get_intensity_window, get_phase_name


def test_warmup_truths():
    """Test that warmup phase gets at least 2 truths."""
    truths = 0
    dares = 0
    
    for seq in range(1, 6):  # Steps 1-5 (warmup)
        picked = pick_type_balanced(seq, 25, truths, dares, 'random')
        if picked == 'truth':
            truths += 1
        else:
            dares += 1
    
    assert truths >= 2, f"Expected at least 2 truths in warmup, got {truths}"
    print(f"✓ Warmup phase: {truths} truths, {dares} dares (requirement: ≥2 truths)")


def test_fifty_fifty_balance():
    """Test that full session maintains ~50/50 balance."""
    truths = 0
    dares = 0
    
    for seq in range(1, 26):  # 25 activities
        picked = pick_type_balanced(seq, 25, truths, dares, 'random')
        if picked == 'truth':
            truths += 1
        else:
            dares += 1
    
    # Should be within ±3 of 50/50
    assert abs(truths - dares) <= 3, f"Imbalanced: {truths} truths vs {dares} dares"
    print(f"✓ Full session: {truths} truths, {dares} dares (balanced)")


def test_forced_modes():
    """Test forced truth/dare modes."""
    # Truth-only mode
    for seq in range(1, 11):
        picked = pick_type_balanced(seq, 25, 0, 0, 'truth')
        assert picked == 'truth', f"Expected truth in truth-only mode, got {picked}"
    
    # Dare-only mode
    for seq in range(1, 11):
        picked = pick_type_balanced(seq, 25, 0, 0, 'dare')
        assert picked == 'dare', f"Expected dare in dare-only mode, got {picked}"
    
    print(f"✓ Forced modes work correctly")


def test_intensity_windows():
    """Test intensity windows for progression."""
    # Warmup (1-5): intensity 1-2
    for seq in [1, 3, 5]:
        min_i, max_i = get_intensity_window(seq, 25)
        assert min_i == 1 and max_i == 2, f"Warmup step {seq}: expected 1-2, got {min_i}-{max_i}"
    
    # Build (6-15): intensity 2-3
    for seq in [6, 10, 15]:
        min_i, max_i = get_intensity_window(seq, 25)
        assert min_i == 2 and max_i == 3, f"Build step {seq}: expected 2-3, got {min_i}-{max_i}"
    
    # Peak (16-22): intensity 4-5
    for seq in [16, 20, 22]:
        min_i, max_i = get_intensity_window(seq, 25)
        assert min_i == 4 and max_i == 5, f"Peak step {seq}: expected 4-5, got {min_i}-{max_i}"
    
    # Afterglow (23-25): intensity 2-3
    for seq in [23, 25]:
        min_i, max_i = get_intensity_window(seq, 25)
        assert min_i == 2 and max_i == 3, f"Afterglow step {seq}: expected 2-3, got {min_i}-{max_i}"
    
    print(f"✓ Intensity windows correct for all phases")


def test_phase_names():
    """Test phase name detection."""
    assert get_phase_name(3, 25) == "warmup"
    assert get_phase_name(10, 25) == "build"
    assert get_phase_name(20, 25) == "peak"
    assert get_phase_name(25, 25) == "afterglow"
    print(f"✓ Phase names correct")


if __name__ == '__main__':
    print("Testing picker logic...")
    print()
    
    try:
        test_warmup_truths()
        test_fifty_fifty_balance()
        test_forced_modes()
        test_intensity_windows()
        test_phase_names()
        
        print()
        print("=" * 50)
        print("✅ All picker tests passed!")
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

