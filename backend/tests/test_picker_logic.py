
import pytest
from src.recommender.picker import get_intensity_window

def test_picker_intensity_logic():
    # Test G Rating - Always 1
    for step in range(1, 26):
        min_i, max_i = get_intensity_window(step, 25, 'G')
        assert min_i == 1
        assert max_i == 1

    # Test R Rating - New Logic
    # Warmup (1-5): 1-2
    for step in range(1, 6):
        min_i, max_i = get_intensity_window(step, 25, 'R')
        assert min_i == 1
        assert max_i == 2
        
    # Build (6-15): 2-3
    for step in range(6, 16):
        min_i, max_i = get_intensity_window(step, 25, 'R')
        assert min_i == 2
        assert max_i == 3
        
    # Peak (16-22): 3-3
    for step in range(16, 23):
        min_i, max_i = get_intensity_window(step, 25, 'R')
        assert min_i == 3
        assert max_i == 3

    # Test X Rating - New Logic
    # Warmup (1-5): 2-3
    for step in range(1, 6):
        min_i, max_i = get_intensity_window(step, 25, 'X')
        assert min_i == 2
        assert max_i == 3
        
    # Build (6-15): 3-4
    for step in range(6, 16):
        min_i, max_i = get_intensity_window(step, 25, 'X')
        assert min_i == 3
        assert max_i == 4
        
    # Peak (16-22): 4-5
    for step in range(16, 23):
        min_i, max_i = get_intensity_window(step, 25, 'X')
        assert min_i == 4
        assert max_i == 5
