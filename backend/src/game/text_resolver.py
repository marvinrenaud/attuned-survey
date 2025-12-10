"""
Text resolver for gameplay activities.
Handles heuristic replacement of placeholders like "your partner" with actual player names.
"""
import re

def resolve_activity_text(text: str, primary_name: str, secondary_name: str) -> str:
    """
    Resolve activity text by replacing placeholders with player names.
    
    Args:
        text: The original activity text (e.g., "Kiss your partner").
        primary_name: The name of the primary player (the "doer").
        secondary_name: The name of the secondary player (the "recipient").
        
    Returns:
        The resolved text with names inserted.
    """
    if not text:
        return ""
        
    # Replace "your partner" (case-insensitive) with secondary_name
    # We use a regex to handle case insensitivity while preserving the case of the replacement if needed
    # But here we just want to replace the phrase with the name.
    
    # Pattern: "your partner" or "Your partner"
    pattern = re.compile(r'\byour partner\b', re.IGNORECASE)
    
    resolved_text = pattern.sub(secondary_name, text)
    
    return resolved_text
