"""Configuration module for environment validation and settings."""
import os
from typing import Optional


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""
    pass


class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str
    
    # Groq AI
    GROQ_API_KEY: str
    GROQ_MODEL: str
    GROQ_BASE_URL: str
    
    # Recommender Engine
    ATTUNED_PROFILE_VERSION: str
    ATTUNED_DEFAULT_TARGET_ACTIVITIES: int
    ATTUNED_DEFAULT_BANK_RATIO: float
    ATTUNED_DEFAULT_RATING: str
    
    # Feature Flags
    REPAIR_USE_AI: bool
    GEN_TEMPERATURE: float
    
    # Email
    RESEND_API_KEY: str
    
    # Flask
    FLASK_ENV: str
    
    def __init__(self):
        """Initialize settings from environment variables with validation."""
        # Required settings
        self.DATABASE_URL = self._get_required("DATABASE_URL")
        
        # Groq settings (required for recommendations)
        self.GROQ_API_KEY = self._get_optional("GROQ_API_KEY", "")
        self.GROQ_MODEL = self._get_optional("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.GROQ_BASE_URL = self._get_optional("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        
        # Recommender defaults
        self.ATTUNED_PROFILE_VERSION = self._get_optional("ATTUNED_PROFILE_VERSION", "0.4")
        self.ATTUNED_DEFAULT_TARGET_ACTIVITIES = int(
            self._get_optional("ATTUNED_DEFAULT_TARGET_ACTIVITIES", "25")
        )
        self.ATTUNED_DEFAULT_BANK_RATIO = float(
            self._get_optional("ATTUNED_DEFAULT_BANK_RATIO", "0.5")
        )
        self.ATTUNED_DEFAULT_RATING = self._get_optional("ATTUNED_DEFAULT_RATING", "R")
        
        # Feature flags
        self.REPAIR_USE_AI = self._get_optional("REPAIR_USE_AI", "true").lower() in ("true", "1", "yes")
        self.GEN_TEMPERATURE = float(self._get_optional("GEN_TEMPERATURE", "0.6"))
        
        # Email
        self.RESEND_API_KEY = self._get_optional("RESEND_API_KEY", "")
        
        # Flask
        self.FLASK_ENV = self._get_optional("FLASK_ENV", "production")
    
    def _get_required(self, key: str) -> str:
        """Get required environment variable or raise ConfigurationError."""
        value = os.getenv(key)
        if not value:
            raise ConfigurationError(
                f"Missing required environment variable: {key}. "
                f"Please set it in your environment or .env file."
            )
        return value
    
    def _get_optional(self, key: str, default: str) -> str:
        """Get optional environment variable with default fallback."""
        return os.getenv(key, default)
    
    def validate_groq_config(self) -> bool:
        """Check if Groq configuration is complete."""
        return bool(self.GROQ_API_KEY)
    
    def mask_sensitive(self, value: str, visible_chars: int = 4) -> str:
        """Mask sensitive values for logging."""
        if len(value) <= visible_chars:
            return "***"
        return value[:visible_chars] + "***"
    
    def get_masked_config(self) -> dict:
        """Get configuration dict with masked sensitive values."""
        return {
            "DATABASE_URL": self.mask_sensitive(self.DATABASE_URL, 20),
            "GROQ_API_KEY": self.mask_sensitive(self.GROQ_API_KEY),
            "GROQ_MODEL": self.GROQ_MODEL,
            "GROQ_BASE_URL": self.GROQ_BASE_URL,
            "ATTUNED_PROFILE_VERSION": self.ATTUNED_PROFILE_VERSION,
            "ATTUNED_DEFAULT_TARGET_ACTIVITIES": self.ATTUNED_DEFAULT_TARGET_ACTIVITIES,
            "ATTUNED_DEFAULT_BANK_RATIO": self.ATTUNED_DEFAULT_BANK_RATIO,
            "ATTUNED_DEFAULT_RATING": self.ATTUNED_DEFAULT_RATING,
            "REPAIR_USE_AI": self.REPAIR_USE_AI,
            "GEN_TEMPERATURE": self.GEN_TEMPERATURE,
            "RESEND_API_KEY": self.mask_sensitive(self.RESEND_API_KEY),
            "FLASK_ENV": self.FLASK_ENV,
        }


# Global settings instance
settings = Settings()

