"""Custom progress tracking for OCRmyPDF with WebSocket support."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProgressInfo:
    """Progress information for a conversion job.

    Attributes:
        step: Current processing step name
        current: Current progress value (e.g., page number)
        total: Total progress value (e.g., total pages)
        percentage: Progress percentage (0-100)
        message: Human-readable progress message

    """

    step: str
    current: int
    total: int
    percentage: float
    message: str


class WebSocketProgressBar:
    """Custom progress bar for OCRmyPDF that sends updates via callback.

    This class implements the OCRmyPDF ProgressBar protocol and sends
    progress updates through a callback function.

    Attributes:
        total: Total number of units (pages or percentage)
        desc: Description of current step
        unit: Unit label (e.g., "page", "%")
        callback: Function to call with progress updates
        cancel_event: Event to check for cancellation requests

    """

    def __init__(
        self,
        total: int | float | None = None,
        desc: str | None = None,
        unit: str = "page",
        disable: bool = False,
        callback: Callable[[ProgressInfo], None] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ):
        """Initialize the progress bar.

        Args:
            total: Total number of units to process
            desc: Description of the current step
            unit: Unit label for progress
            disable: Whether to disable progress reporting
            callback: Function to call with progress updates
            cancel_event: Event to check for cancellation
            **kwargs: Additional arguments (ignored, for compatibility)

        """
        self.total = total or 100
        self.desc = desc or "Processing"
        self.unit = unit
        self.disable = disable
        self.callback = callback
        self.cancel_event = cancel_event
        self.current = 0
        self.last_update_time = 0.0
        self.min_update_interval = 1.0  # Throttle to max 1 update/second

    def __enter__(self) -> WebSocketProgressBar:
        """Context manager entry.

        Returns:
            Self

        """
        logger.info(
            f"Progress tracking started: {self.desc} (0/{self.total} {self.unit})"
        )
        if not self.disable and self.callback:
            self._send_progress()
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit.

        Args:
            *args: Exception information (if any)

        """
        if not self.disable and self.callback:
            # Send final progress at 100%
            self.current = self.total
            self._send_progress(force=True)
        logger.info(
            f"Progress tracking completed: {self.desc} "
            f"({self.current}/{self.total} {self.unit})"
        )

    def update(self, n: int = 1, *, completed: int | None = None) -> None:
        """Update progress.

        Args:
            n: Increment value (if completed is None)
            completed: Absolute progress value (overrides n)

        """
        if self.disable:
            return

        # Check for cancellation
        if self.cancel_event and self.cancel_event.is_set():
            from pdfa.exceptions import JobCancelledException

            raise JobCancelledException("Job was cancelled by user request")

        # Update current progress
        if completed is not None:
            self.current = completed
        else:
            self.current += n

        # Ensure we don't exceed total
        if self.current > self.total:
            self.current = self.total

        # Send progress update (throttled)
        if self.callback:
            self._send_progress()

    def _send_progress(self, force: bool = False) -> None:
        """Send progress update via callback.

        Args:
            force: If True, bypass throttling and send immediately

        """
        now = time.time()

        # Throttle updates unless forced
        if not force and (now - self.last_update_time) < self.min_update_interval:
            return

        self.last_update_time = now

        # Calculate percentage
        percentage = (self.current / self.total) * 100 if self.total > 0 else 0
        percentage = round(percentage, 1)

        # Build message
        if self.unit == "page":
            message = f"{self.desc}: page {self.current} of {self.total}"
        else:
            message = f"{self.desc}: {self.current}/{self.total} {self.unit}"

        # Create progress info
        progress_info = ProgressInfo(
            step=self.desc,
            current=int(self.current),
            total=int(self.total),
            percentage=percentage,
            message=message,
        )

        # Log progress event
        logger.info(
            f"Progress event: {self.desc} - {percentage:.1f}% "
            f"({self.current}/{self.total} {self.unit})"
        )

        # Call the callback
        try:
            self.callback(progress_info)
            logger.debug(f"Progress callback executed successfully for {self.desc}")
        except Exception as e:
            logger.error(f"Error in progress callback: {e}", exc_info=True)


class ThrottledProgressCallback:
    """Wrapper for progress callbacks with throttling.

    This class ensures that progress callbacks are not called too frequently,
    which is important for WebSocket sends to avoid overwhelming the client.

    Attributes:
        callback: The actual callback function to call
        min_interval: Minimum interval between calls (in seconds)

    """

    def __init__(
        self, callback: Callable[[ProgressInfo], None], min_interval: float = 1.0
    ):
        """Initialize the throttled callback.

        Args:
            callback: The callback function to wrap
            min_interval: Minimum interval between calls in seconds

        """
        self.callback = callback
        self.min_interval = min_interval
        self.last_call_time = 0.0
        self.pending_info: ProgressInfo | None = None

    def __call__(self, progress_info: ProgressInfo) -> None:
        """Call the callback with throttling.

        Args:
            progress_info: Progress information to send

        """
        now = time.time()

        if (now - self.last_call_time) >= self.min_interval:
            # Enough time has passed, send immediately
            self.callback(progress_info)
            self.last_call_time = now
            self.pending_info = None
        else:
            # Too soon, store for later
            self.pending_info = progress_info

    def flush(self) -> None:
        """Flush any pending progress update."""
        if self.pending_info:
            self.callback(self.pending_info)
            self.last_call_time = time.time()
            self.pending_info = None
