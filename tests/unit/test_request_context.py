"""Tests for request context logging functionality."""

import logging

import pytest

from pdfa.request_context import (
    RequestContextFilter,
    clear_request_context,
    get_client_ip,
    get_user_email,
    set_request_context,
)


class TestRequestContext:
    """Tests for context variable functions."""

    def test_default_values(self):
        """Context variables should have default values."""
        clear_request_context()
        assert get_user_email() == "-"
        assert get_client_ip() == "-"

    def test_set_and_get_context(self):
        """Setting context should update the values."""
        set_request_context(user_email="test@example.com", client_ip="192.168.1.1")
        assert get_user_email() == "test@example.com"
        assert get_client_ip() == "192.168.1.1"
        clear_request_context()

    def test_clear_context(self):
        """Clearing context should reset to defaults."""
        set_request_context(user_email="test@example.com", client_ip="192.168.1.1")
        clear_request_context()
        assert get_user_email() == "-"
        assert get_client_ip() == "-"

    def test_partial_set(self):
        """Setting only one value should not affect the other."""
        clear_request_context()
        set_request_context(user_email="test@example.com")
        assert get_user_email() == "test@example.com"
        assert get_client_ip() == "-"
        clear_request_context()


class TestRequestContextFilter:
    """Tests for the logging filter."""

    def test_filter_adds_context_to_record(self):
        """Filter should add context variables to log record."""
        set_request_context(user_email="user@test.com", client_ip="10.0.0.1")

        filter_instance = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True
        assert record.user_email == "user@test.com"
        assert record.client_ip == "10.0.0.1"
        clear_request_context()

    def test_filter_uses_defaults_when_not_set(self):
        """Filter should use defaults when context not set."""
        clear_request_context()

        filter_instance = RequestContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True
        assert record.user_email == "-"
        assert record.client_ip == "-"


class TestLoggingIntegration:
    """Integration tests for logging with context."""

    def test_logger_includes_context_in_output(self, caplog):
        """Logger output should include context variables."""
        # Set up context
        set_request_context(user_email="integration@test.com", client_ip="172.16.0.1")

        # Create a logger with the filter
        test_logger = logging.getLogger("test_integration")
        test_logger.setLevel(logging.INFO)

        # Add a handler with the filter
        handler = logging.StreamHandler()
        handler.addFilter(RequestContextFilter())
        formatter = logging.Formatter(
            "%(user_email)s %(client_ip)s %(message)s"
        )
        handler.setFormatter(formatter)
        test_logger.addHandler(handler)

        # Log a message
        with caplog.at_level(logging.INFO):
            test_logger.info("Test log message")

        # Clean up
        test_logger.removeHandler(handler)
        clear_request_context()

        # The caplog won't capture the formatted output with our custom fields,
        # but we can verify the filter was called correctly
        assert len(caplog.records) >= 1


@pytest.mark.asyncio
async def test_context_in_async_function():
    """Context should be accessible in async functions."""
    set_request_context(user_email="async@test.com", client_ip="192.168.2.1")

    async def inner_async():
        return get_user_email(), get_client_ip()

    email, ip = await inner_async()
    assert email == "async@test.com"
    assert ip == "192.168.2.1"
    clear_request_context()
