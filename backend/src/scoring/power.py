from typing import Dict, Any, List, Optional
import math

def normalize_likert(value: Any) -> float:
    """
    Map Likert 1-7 response to 0-1 scale
    """
    try:
        n = float(value)
        if not math.isfinite(n) or n < 1 or n > 7:
            return 0.0
        return (n - 1) / 6
    except (ValueError, TypeError):
        return 0.0

def mean(values: List[float]) -> float:
    """
    Calculate mean of list
    """
    if not values:
        return 0.0
    return sum(values) / len(values)

def interpret_confidence(confidence: float) -> str:
    """
    Interpret confidence score
    """
    if confidence <= 0.30:
        return 'Low confidence'
    if confidence <= 0.60:
        return 'Moderate confidence'
    if confidence <= 0.85:
        return 'High confidence'
    return 'Very high confidence'

def calculate_power_dynamic(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate power dynamic from survey responses
    """
    # Configuration from v0.4 schema
    THETA_FLOOR = 30  # Minimum threshold for engagement
    DELTA_BAND = 15   # Band for determining Switch

    # Top items: A13, A15
    top_items = [normalize_likert(answers.get(qid)) for qid in ['A13', 'A15']]
    top_score = mean(top_items) * 100

    # Bottom items: A14, A16
    bottom_items = [normalize_likert(answers.get(qid)) for qid in ['A14', 'A16']]
    bottom_score = mean(bottom_items) * 100

    # Determine orientation
    orientation: str
    confidence: float
    interpretation: str

    if top_score < THETA_FLOOR and bottom_score < THETA_FLOOR:
        # Both scores low - still exploring
        orientation = 'Versatile/Undefined'
        confidence = max(top_score, bottom_score) / 100
        interpretation = 'Low engagement - still exploring preferences'
    elif abs(top_score - bottom_score) <= DELTA_BAND and min(top_score, bottom_score) >= THETA_FLOOR:
        # Scores close and both engaged - Switch
        orientation = 'Switch'
        confidence = min(top_score, bottom_score) / 100
        interpretation = f"{interpret_confidence(confidence)} Switch"
    elif top_score > bottom_score:
        # Top-leaning
        orientation = 'Top'
        confidence = (top_score / 100) * (1 - 0.3 * (bottom_score / 100))
        interpretation = f"{interpret_confidence(confidence)} Top"
    else:
        # Bottom-leaning
        orientation = 'Bottom'
        confidence = (bottom_score / 100) * (1 - 0.3 * (top_score / 100))
        interpretation = f"{interpret_confidence(confidence)} Bottom"

    return {
        "orientation": orientation,
        "top_score": round(top_score),
        "bottom_score": round(bottom_score),
        "confidence": round(confidence, 2),
        "interpretation": interpretation
    }
