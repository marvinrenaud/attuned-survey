from typing import Dict, Any, List, Union
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

def interpret_band(score: float) -> str:
    """
    Interpret 0-1 score into descriptive band
    """
    if score <= 0.30:
        return 'Low'
    if score <= 0.55:
        return 'Moderate-Low'
    if score <= 0.75:
        return 'Moderate-High'
    return 'High'

def calculate_arousal_propensity(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate arousal propensity from survey responses
    """
    # SE items: A1-A4
    se_items = [normalize_likert(answers.get(f'A{i}')) for i in range(1, 5)]
    se_normalized = mean(se_items)

    # SIS-P items: A5-A8
    sis_p_items = [normalize_likert(answers.get(f'A{i}')) for i in range(5, 9)]
    sis_p_normalized = mean(sis_p_items)

    # SIS-C items: A9-A12
    sis_c_items = [normalize_likert(answers.get(f'A{i}')) for i in range(9, 13)]
    sis_c_normalized = mean(sis_c_items)

    return {
        "sexual_excitation": round(se_normalized, 2),
        "inhibition_performance": round(sis_p_normalized, 2),
        "inhibition_consequence": round(sis_c_normalized, 2),
        "interpretation": {
            "se": interpret_band(se_normalized),
            "sis_p": interpret_band(sis_p_normalized),
            "sis_c": interpret_band(sis_c_normalized)
        }
    }
