from typing import Any, Optional, Dict, Union
import logging
from ..extensions import db
from ..models.app_config import AppConfig
from ..config import settings

logger = logging.getLogger(__name__)

# Global cache
_config_cache: Dict[str, str] = {}
_cache_initialized = False

def _ensure_cache():
    """Load all configs into cache if not already loaded."""
    global _cache_initialized, _config_cache
    if _cache_initialized:
        return

    try:
        # Load all configs at once to minimize queries
        # Wrap in try-except in case table doesn't exist yet (chicken-egg during testing)
        configs = AppConfig.query.all()
        _config_cache = {c.key: c.value for c in configs}
        _cache_initialized = True
        logger.info(f"Loaded {len(_config_cache)} config values from database")
    except Exception as e:
        logger.warning(f"Failed to load app configs from database: {e}")
        # Don't set initialized to True so we retry later? 
        # Or set True to avoid hammering DB on failure?
        # Let's verify DB connection first. If generic error, maybe retry later.

def refresh_cache():
    """Force reload of configuration cache."""
    global _cache_initialized, _config_cache
    _cache_initialized = False
    _config_cache = {}
    _ensure_cache()
    logger.info("Config cache refreshed")

def get_config(key: str, default: Any = None) -> str:
    """
    Get config value.
    Priority:
    1. Database (cached)
    2. Environment Variables (Legacy)
    3. Default value
    """
    _ensure_cache()
    
    # 1. Database
    if key in _config_cache:
        return _config_cache[key]
    
    # 2. Legacy Env Var Fallback
    # Map friendly keys to settings attributes
    env_mapping = {
        'profile_version': 'ATTUNED_PROFILE_VERSION',
        'default_target_activities': 'ATTUNED_DEFAULT_TARGET_ACTIVITIES',
        'default_bank_ratio': 'ATTUNED_DEFAULT_BANK_RATIO',
        'default_rating': 'ATTUNED_DEFAULT_RATING',
        'gen_temperature': 'GEN_TEMPERATURE',
        'repair_use_ai': 'REPAIR_USE_AI',
        'groq_model': 'GROQ_MODEL'
    }
    
    if key in env_mapping:
        env_key = env_mapping[key]
        if hasattr(settings, env_key):
            val = getattr(settings, env_key)
            if val is not None:
                return str(val) # Unified return type
                
    return str(default) if default is not None else None

def get_config_int(key: str, default: int = 0) -> int:
    """Get config as integer."""
    val = get_config(key, default)
    try:
        return int(float(val)) # float() handles "1.0" strings safely before int
    except (ValueError, TypeError):
        return default

def get_config_float(key: str, default: float = 0.0) -> float:
    """Get config as float."""
    val = get_config(key, default)
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def get_config_bool(key: str, default: bool = False) -> bool:
    """Get config as boolean."""
    val = get_config(key, str(default))
    if val is None:
        return default
    return val.lower() in ('true', '1', 'yes', 'on')
