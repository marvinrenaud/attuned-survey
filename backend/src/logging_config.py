"""
Structured logging configuration for Attuned backend.
Provides JSON-formatted logs with request correlation and timing.
"""
import logging
import sys
import structlog
from functools import wraps
from time import perf_counter
from flask import g, request
import uuid


def configure_logging(app):
    """Configure structlog with JSON output for production."""
    
    # Determine if we're in production or dev
    # default to production if not specified, to be safe (JSON logs in prod)
    env = app.config.get('ENV', 'production')
    is_prod = env == 'production'
    
    # Configure structlog processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if is_prod:
        # Production: JSON format for log aggregation
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    else:
        # Development: Human-readable colored output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger():
    """Get a logger instance with current request context."""
    return structlog.get_logger()


def request_context_middleware():
    """
    Middleware to add request context to all logs.
    Call this in before_request hook.
    """
    # Clear contextvars at start of request to prevent leaking from previous request (if thread reused)
    structlog.contextvars.clear_contextvars()

    # Generate or propagation unique request ID
    request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
    g.request_id = request_id
    g.request_start = perf_counter()
    
    # Bind context for all logs in this request
    try:
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )
        
        # Add user context if authenticated
        if hasattr(g, 'current_user_id') and g.current_user_id:
            structlog.contextvars.bind_contextvars(
                user_id=str(g.current_user_id)[:8] + '...'
            )
    except Exception:
        import traceback
        traceback.print_exc()
        raise


def log_request_complete(response):
    """
    Middleware to log request completion with timing.
    Call this in after_request hook.
    """
    if hasattr(g, 'request_start'):
        duration_ms = (perf_counter() - g.request_start) * 1000
        logger = get_logger()
        logger.info(
            "request_complete",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
    return response


def timed(operation_name):
    """
    Decorator to time and log function execution.
    
    Usage:
        @timed("groq_generation")
        def generate_activities(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            start = perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (perf_counter() - start) * 1000
                logger.info(
                    f"{operation_name}_complete",
                    duration_ms=round(duration_ms, 2),
                    success=True
                )
                return result
            except Exception as e:
                duration_ms = (perf_counter() - start) * 1000
                logger.error(
                    f"{operation_name}_failed",
                    duration_ms=round(duration_ms, 2),
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
        return wrapper
    return decorator
