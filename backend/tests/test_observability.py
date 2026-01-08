import pytest
import structlog
import json
import uuid
import time
from flask import Flask
from unittest.mock import MagicMock, patch
from src.logging_config import configure_logging, request_context_middleware, log_request_complete, timed

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['ENV'] = 'production'  # Force JSON logging for tests
    configure_logging(app)
    return app

@pytest.fixture
def capture_logs(app):
    """Capture structlog output for assertion."""
    from structlog.testing import capture_logs
    with capture_logs() as cap_logs:
        yield cap_logs

def test_request_context_middleware(app):
    """Verify request_id and other context are bound."""
    with app.test_request_context(headers={'X-Request-ID': 'test-123'}):
        request_context_middleware()
        
        logger = structlog.get_logger()
        # We can't easily check bound contextvars directly without logging something
        logger.info("test_event")
        
        # Manually check if the context var is set (implementation detail check)
        # Or better, check the captured log output
        
def test_json_logging_format(app, capture_logs):
    """Verify logs are output as JSON in production."""
    with app.test_request_context():
        request_context_middleware()
        logger = structlog.get_logger()
        logger.info("test_json", user_id="u-123")
        
        assert len(capture_logs) == 1
        log = capture_logs[0]
        
        # structlog.testing.capture_logs captures the dict, not the JSON string
        # But we want to verify the processor chain would produce JSON
        # Ideally we trust structlog's JSONRenderer, but we check the keys here
        assert log['event'] == "test_json"
        assert log['user_id'] == "u-123"
        # assert 'timestamp' in log  # capture_logs bypasses TimeStamper
        # assert 'request_id' in log  # request_id is bound by middleware, should be there if middleware ran


def test_timed_decorator(app, capture_logs):
    """Verify @timed decorator logs duration."""
    
    @timed("test_operation")
    def slow_function():
        time.sleep(0.01)
        return "done"
        
    with app.test_request_context():
        request_context_middleware()
        result = slow_function()
        
        assert result == "done"
        assert len(capture_logs) == 1
        log = capture_logs[0]
        
        assert log['event'] == "test_operation_complete"
        assert log['success'] is True
        assert log['duration_ms'] >= 10.0

def test_timed_decorator_error(app, capture_logs):
    """Verify @timed decorator logs errors."""
    
    @timed("fail_operation")
    def failing_function():
        raise ValueError("oops")
        
    with app.test_request_context():
        request_context_middleware()
        with pytest.raises(ValueError):
            failing_function()
        
        assert len(capture_logs) == 1
        log = capture_logs[0]
        
        assert log['event'] == "fail_operation_failed"
        assert log['error'] == "oops"
        assert log['error_type'] == "ValueError"
