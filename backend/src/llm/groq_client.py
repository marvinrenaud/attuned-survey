"""Groq API client wrapper with retry logic."""
import os
import time
import logging
import json
from typing import List, Dict, Any, Optional
from groq import Groq

from ..services.config_service import get_config, get_config_float, get_config_bool
from ..config import settings

logger = logging.getLogger(__name__)


class GroqClient:
    """Wrapper for Groq API with retry logic and structured output support."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key (defaults to settings.GROQ_API_KEY)
            model: Model name (defaults to settings.GROQ_MODEL)
        """
        self.api_key = api_key or get_config('groq_api_key', settings.GROQ_API_KEY)
        self.model = model or get_config('groq_model', settings.GROQ_MODEL)
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required but not set")
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"Groq client initialized with model: {self.model}")
    
    def chat_json_schema(
        self,
        messages: List[Dict[str, str]],
        json_schema: dict,
        temperature: float = None,
        max_retries: int = 2,
        initial_backoff: float = 0.25
    ) -> str:
        """
        Call Groq with JSON Schema structured output.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            json_schema: JSON schema dict for structured output
            temperature: Sampling temperature (defaults to settings.GEN_TEMPERATURE)
            max_retries: Number of retries on failure
            initial_backoff: Initial backoff time in seconds
        
        Returns:
            JSON string response
        
        Raises:
            Exception: If all retries fail
        """
        if temperature is None:
            temperature = get_config_float('gen_temperature', settings.GEN_TEMPERATURE)
        
        last_error = None
        backoff = initial_backoff
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    messages=messages,
                    timeout=30.0,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": json_schema.get("name", "response"),
                            "schema": json_schema.get("schema", json_schema),
                            "strict": json_schema.get("strict", True)
                        }
                    }
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                
                content = response.choices[0].message.content
                
                logger.info(
                    f"Groq request successful",
                    extra={
                        "elapsed_ms": elapsed_ms,
                        "model": self.model,
                        "temperature": temperature,
                        "attempt": attempt + 1,
                        "response_length": len(content) if content else 0
                    }
                )
                
                return content
            
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Groq request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}",
                    extra={"error_type": type(e).__name__}
                )
                
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
        
        # All retries failed
        logger.error(f"Groq request failed after {max_retries + 1} attempts: {str(last_error)}")
        raise Exception(f"Groq API call failed after {max_retries + 1} attempts: {str(last_error)}")
    
    def chat_simple(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_retries: int = 2
    ) -> str:
        """
        Simple chat completion without structured output.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            temperature: Sampling temperature
            max_retries: Number of retries on failure
        
        Returns:
            Response text
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        if temperature is None:
            temperature = get_config_float('gen_temperature', settings.GEN_TEMPERATURE)
        
        last_error = None
        backoff = 0.25
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    temperature=temperature,
                    messages=messages,
                    timeout=30.0
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                content = response.choices[0].message.content
                
                logger.info(
                    f"Groq simple chat successful",
                    extra={"elapsed_ms": elapsed_ms, "attempt": attempt + 1}
                )
                
                return content
            
            except Exception as e:
                last_error = e
                logger.warning(f"Groq simple chat failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries:
                    time.sleep(backoff)
                    backoff *= 2
        
        raise Exception(f"Groq simple chat failed after {max_retries + 1} attempts: {str(last_error)}")


# Global client instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """Get or create global Groq client instance."""
    global _groq_client
    
    if _groq_client is None:
        _groq_client = GroqClient()
    
    return _groq_client

