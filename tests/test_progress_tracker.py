"""Tests for progress tracking functionality."""

from __future__ import annotations

import asyncio
import time
from unittest.mock import Mock

import pytest

from pdfa.exceptions import JobCancelledException
from pdfa.progress_tracker import (
    ProgressInfo,
    ThrottledProgressCallback,
    WebSocketProgressBar,
)


class TestProgressInfo:
    """Tests for ProgressInfo dataclass."""

    def test_progress_info_creation(self):
        """Test creating progress info."""
        info = ProgressInfo(
            step="OCR",
            current=15,
            total=100,
            percentage=15.0,
            message="Processing page 15 of 100",
        )

        assert info.step == "OCR"
        assert info.current == 15
        assert info.total == 100
        assert info.percentage == 15.0
        assert "page 15" in info.message


class TestWebSocketProgressBar:
    """Tests for WebSocketProgressBar."""

    def test_basic_progress_update(self):
        """Test basic progress update."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            unit="page",
            callback=callback,
        )

        with progress_bar:
            progress_bar.update(10)

        # Should be called at least for __enter__ and __exit__
        assert callback.call_count >= 2

    def test_progress_percentage_calculation(self):
        """Test progress percentage calculation."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=0.0,  # Disable throttling for test
        )

        progress_bar.update(25)

        # Get the last call's progress info
        call_args = callback.call_args_list[-1]
        progress_info = call_args[0][0]

        assert progress_info.current == 25
        assert progress_info.total == 100
        assert progress_info.percentage == 25.0

    def test_completed_parameter(self):
        """Test using completed parameter instead of increment."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=0.0,
        )

        progress_bar.update(completed=75)

        call_args = callback.call_args_list[-1]
        progress_info = call_args[0][0]

        assert progress_info.current == 75

    def test_progress_clamping(self):
        """Test progress doesn't exceed total."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=0.0,
        )

        progress_bar.update(150)  # More than total

        call_args = callback.call_args_list[-1]
        progress_info = call_args[0][0]

        assert progress_info.current == 100  # Clamped to total

    def test_throttling(self):
        """Test progress updates are throttled."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=1.0,  # 1 second throttle
        )

        # Rapid updates
        for i in range(10):
            progress_bar.update(1)

        # Should be throttled to fewer calls
        assert callback.call_count < 10

    def test_force_update_on_exit(self):
        """Test that exit forces a final update."""
        callback = Mock()

        with WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=999.0,  # Very long throttle
        ) as bar:
            bar.update(50)

        # Exit should force update even with long throttle interval
        final_call = callback.call_args_list[-1]
        progress_info = final_call[0][0]

        assert progress_info.current == 100  # Exit sets to 100%

    def test_disable_flag(self):
        """Test disabled progress bar."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            disable=True,
        )

        with progress_bar:
            progress_bar.update(50)

        # Should not call callback when disabled
        callback.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancellation_check(self):
        """Test cancellation event is checked."""
        callback = Mock()
        cancel_event = asyncio.Event()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            cancel_event=cancel_event,
        )

        # Set cancellation before update
        cancel_event.set()

        with pytest.raises(JobCancelledException):
            progress_bar.update(10)

    def test_message_formatting_pages(self):
        """Test message formatting for pages."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="OCR",
            unit="page",
            callback=callback,
            min_update_interval=0.0,
        )

        progress_bar.update(15)

        call_args = callback.call_args_list[-1]
        progress_info = call_args[0][0]

        assert "page 15 of 100" in progress_info.message

    def test_message_formatting_generic(self):
        """Test message formatting for generic units."""
        callback = Mock()
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Processing",
            unit="item",
            callback=callback,
            min_update_interval=0.0,
        )

        progress_bar.update(25)

        call_args = callback.call_args_list[-1]
        progress_info = call_args[0][0]

        assert "25/100 item" in progress_info.message

    def test_callback_exception_handling(self):
        """Test that exceptions in callback don't crash the bar."""
        callback = Mock(side_effect=Exception("Test error"))
        progress_bar = WebSocketProgressBar(
            total=100,
            desc="Test",
            callback=callback,
            min_update_interval=0.0,
        )

        # Should not raise even though callback raises
        progress_bar.update(10)


class TestThrottledProgressCallback:
    """Tests for ThrottledProgressCallback."""

    def test_immediate_first_call(self):
        """Test first call is immediate."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=1.0)

        info = ProgressInfo(
            step="Test", current=10, total=100, percentage=10.0, message="Test"
        )
        throttled(info)

        callback.assert_called_once_with(info)

    def test_throttling_rapid_calls(self):
        """Test rapid calls are throttled."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=1.0)

        info = ProgressInfo(
            step="Test", current=10, total=100, percentage=10.0, message="Test"
        )

        # First call
        throttled(info)
        # Second call immediately after
        throttled(info)

        # Should only call once
        assert callback.call_count == 1

    def test_throttling_with_delay(self):
        """Test calls after interval are sent."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=0.1)

        info1 = ProgressInfo(
            step="Test", current=10, total=100, percentage=10.0, message="Test"
        )
        info2 = ProgressInfo(
            step="Test", current=20, total=100, percentage=20.0, message="Test"
        )

        throttled(info1)
        time.sleep(0.15)  # Wait longer than interval
        throttled(info2)

        # Should call twice
        assert callback.call_count == 2

    def test_pending_info_stored(self):
        """Test that pending info is stored."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=1.0)

        info1 = ProgressInfo(
            step="Test", current=10, total=100, percentage=10.0, message="Test"
        )
        info2 = ProgressInfo(
            step="Test", current=20, total=100, percentage=20.0, message="Test"
        )

        throttled(info1)
        throttled(info2)  # This should be stored as pending

        assert throttled.pending_info == info2

    def test_flush(self):
        """Test flushing pending info."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=1.0)

        info1 = ProgressInfo(
            step="Test", current=10, total=100, percentage=10.0, message="Test"
        )
        info2 = ProgressInfo(
            step="Test", current=20, total=100, percentage=20.0, message="Test"
        )

        throttled(info1)
        throttled(info2)  # Pending

        callback.reset_mock()
        throttled.flush()

        # Should send the pending info
        callback.assert_called_once_with(info2)
        assert throttled.pending_info is None

    def test_flush_without_pending(self):
        """Test flush with no pending info."""
        callback = Mock()
        throttled = ThrottledProgressCallback(callback, min_interval=1.0)

        throttled.flush()

        # Should not call callback
        callback.assert_not_called()
