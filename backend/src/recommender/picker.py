"""Truth/Dare balancing logic for activity selection."""


def pick_type_balanced(seq: int, target: int, truths: int, dares: int, mode: str = 'random') -> str:
    """
    Pick activity type (truth or dare) based on balancing rules.
    
    Args:
        seq: Current sequence number (1-based)
        target: Total target activities (typically 25)
        truths: Number of truths selected so far
        dares: Number of dares selected so far
        mode: 'random', 'truth', or 'dare'
    
    Returns:
        'truth' or 'dare'
    
    Rules:
        1. If mode is 'truth' or 'dare', always return that
        2. In warmup (steps 1-5), ensure at least 2 truths
        3. Otherwise, maintain ~50/50 ratio
    """
    # Force mode if specified
    if mode == 'truth':
        return 'truth'
    if mode == 'dare':
        return 'dare'
    
    # Warmup phase (steps 1-5): ensure at least 2 truths
    if seq <= 5:
        if truths < 2:
            return 'truth'
    
    # Calculate current ratio
    total_so_far = truths + dares
    
    if total_so_far == 0:
        # First item, default to truth for warmup
        return 'truth'
    
    # Calculate how far off from 50/50 we are
    truth_ratio = truths / total_so_far if total_so_far > 0 else 0
    
    # If we're behind on truths, pick truth
    if truth_ratio < 0.4:
        return 'truth'
    
    # If we're behind on dares, pick dare
    if truth_ratio > 0.6:
        return 'dare'
    
    # Otherwise alternate based on what we picked last
    # (This creates a natural variation)
    if truths > dares:
        return 'dare'
    else:
        return 'truth'


def get_intensity_window(seq: int, target: int = 25) -> tuple[int, int]:
    """
    Get the intensity window (min, max) for a given sequence number.
    
    Progression:
    - Warmup (1-5): 1-2
    - Build (6-15): 2-3
    - Peak (16-22): 4-5
    - Afterglow (23-25): 2-3
    
    Args:
        seq: Sequence number (1-based)
        target: Total target activities
    
    Returns:
        (min_intensity, max_intensity) tuple
    """
    # Calculate phase boundaries as percentages
    warmup_end = int(target * 0.2)  # 20% = 5 for target 25
    build_end = int(target * 0.6)   # 60% = 15 for target 25
    peak_end = int(target * 0.88)   # 88% = 22 for target 25
    
    if seq <= warmup_end:
        # Warmup: gentle
        return (1, 2)
    elif seq <= build_end:
        # Build: moderate
        return (2, 3)
    elif seq <= peak_end:
        # Peak: intense
        return (4, 5)
    else:
        # Afterglow: back down
        return (2, 3)


def get_phase_name(seq: int, target: int = 25) -> str:
    """Get the phase name for a given sequence number."""
    warmup_end = int(target * 0.2)
    build_end = int(target * 0.6)
    peak_end = int(target * 0.88)
    
    if seq <= warmup_end:
        return "warmup"
    elif seq <= build_end:
        return "build"
    elif seq <= peak_end:
        return "peak"
    else:
        return "afterglow"

