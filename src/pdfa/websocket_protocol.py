"""WebSocket message protocol schemas and validation."""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class ClientMessage:
    """Base class for client-to-server messages."""

    type: str


@dataclass
class SubmitJobMessage(ClientMessage):
    """Message to submit a new conversion job.

    Supports both single-file and multi-file modes for multi-page documents.

    Attributes:
        type: Always "submit"
        filename: Original filename (single-file mode)
        fileData: Base64-encoded file content (single-file mode)
        multi_file_mode: If True, use filenames and filesData (multi-file mode)
        filenames: List of filenames (multi-file mode only)
        filesData: List of base64-encoded file contents (multi-file mode only)
        config: Conversion configuration parameters

    """

    type: Literal["submit"] = "submit"
    filename: str = ""
    fileData: str = ""  # noqa: N815 (camelCase for WebSocket protocol)
    multi_file_mode: bool = False
    filenames: list[str] | None = None
    filesData: list[str] | None = None  # noqa: N815 (camelCase for WebSocket protocol)
    config: dict[str, Any] | None = None

    def validate(self) -> None:
        """Validate the submit message.

        Raises:
            ValueError: If validation fails

        """
        if self.config is None:
            self.config = {}

        if self.multi_file_mode:
            # Multi-file mode validation
            if not self.filenames or not self.filesData:
                raise ValueError(
                    "filenames and filesData are required in multi-file mode"
                )
            if len(self.filenames) != len(self.filesData):
                raise ValueError("filenames and filesData must have same length")
            if len(self.filenames) == 0:
                raise ValueError("At least one file required in multi-file mode")

            # Validate all base64 encodings
            for i, file_data in enumerate(self.filesData):
                try:
                    base64.b64decode(file_data, validate=True)
                except Exception as e:
                    raise ValueError(
                        f"Invalid base64 encoding for file {i}: {e}"
                    ) from e
        else:
            # Single-file mode validation (backward compatibility)
            if not self.filename:
                raise ValueError("filename is required")
            if not self.fileData:
                raise ValueError("fileData is required")

            # Validate base64 encoding
            try:
                base64.b64decode(self.fileData, validate=True)
            except Exception as e:
                raise ValueError(f"Invalid base64 encoding: {e}") from e

    def get_file_bytes(self) -> bytes:
        """Decode and return the file content as bytes (single-file mode).

        Returns:
            The decoded file content

        Raises:
            ValueError: If called in multi-file mode

        """
        if self.multi_file_mode:
            raise ValueError("Use get_files_bytes() in multi-file mode")
        return base64.b64decode(self.fileData)

    def get_files_bytes(self) -> list[bytes]:
        """Decode and return all file contents as bytes (multi-file mode).

        Returns:
            List of decoded file contents

        Raises:
            ValueError: If called in single-file mode or if filesData is None

        """
        if not self.multi_file_mode:
            raise ValueError("Use get_file_bytes() in single-file mode")
        if not self.filesData:
            raise ValueError("No files data available")
        return [base64.b64decode(file_data) for file_data in self.filesData]


@dataclass
class CancelJobMessage(ClientMessage):
    """Message to cancel a running job.

    Attributes:
        type: Always "cancel"
        job_id: UUID of the job to cancel

    """

    type: Literal["cancel"] = "cancel"
    job_id: str = ""

    def validate(self) -> None:
        """Validate the cancel message.

        Raises:
            ValueError: If validation fails

        """
        if not self.job_id:
            raise ValueError("job_id is required")


@dataclass
class PingMessage(ClientMessage):
    """Keepalive ping message.

    Attributes:
        type: Always "ping"

    """

    type: Literal["ping"] = "ping"


@dataclass
class ServerMessage:
    """Base class for server-to-client messages."""

    type: str

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the message

        """
        return {
            k: v for k, v in self.__dict__.items() if v is not None and k != "type"
        } | {"type": self.type}


@dataclass
class JobAcceptedMessage(ServerMessage):
    """Message sent when job is accepted.

    Attributes:
        type: Always "job_accepted"
        job_id: UUID of the accepted job
        status: Current job status

    """

    type: Literal["job_accepted"] = "job_accepted"
    job_id: str = ""
    status: str = "queued"


@dataclass
class ProgressMessage(ServerMessage):
    """Progress update message.

    Attributes:
        type: Always "progress"
        job_id: UUID of the job
        step: Current processing step
        current: Current progress value
        total: Total progress value
        percentage: Progress percentage (0-100)
        message: Human-readable progress message

    """

    type: Literal["progress"] = "progress"
    job_id: str = ""
    step: str = ""
    current: int = 0
    total: int = 100
    percentage: float = 0.0
    message: str = ""


@dataclass
class CompletedMessage(ServerMessage):
    """Message sent when job completes successfully.

    Attributes:
        type: Always "completed"
        job_id: UUID of the completed job
        download_url: URL to download the result
        filename: Name of the output file
        size_bytes: Size of the output file in bytes

    """

    type: Literal["completed"] = "completed"
    job_id: str = ""
    download_url: str = ""
    filename: str = ""
    size_bytes: int | None = None


@dataclass
class ErrorMessage(ServerMessage):
    """Error message.

    Attributes:
        type: Always "error"
        job_id: UUID of the job (may be empty for connection errors)
        error_code: Machine-readable error code
        message: Human-readable error message

    """

    type: Literal["error"] = "error"
    job_id: str = ""
    error_code: str = ""
    message: str = ""


@dataclass
class CancelledMessage(ServerMessage):
    """Message sent when job is cancelled.

    Attributes:
        type: Always "cancelled"
        job_id: UUID of the cancelled job

    """

    type: Literal["cancelled"] = "cancelled"
    job_id: str = ""


@dataclass
class PongMessage(ServerMessage):
    """Keepalive pong response.

    Attributes:
        type: Always "pong"

    """

    type: Literal["pong"] = "pong"


@dataclass
class JobEventMessage(ServerMessage):
    """Job event message.

    Sent when conversion events occur (OCR decisions, format conversions, etc.).

    Attributes:
        type: Always "job_event"
        job_id: UUID of the job
        event_type: Type of event (format_conversion, ocr_decision, etc.)
        timestamp: ISO 8601 timestamp when event occurred
        message: Human-readable event description (English fallback)
        details: Additional structured event data including i18n keys

    """

    type: Literal["job_event"] = "job_event"
    job_id: str = ""
    event_type: str = ""
    timestamp: str = ""
    message: str = ""
    details: dict[str, Any] | None = None


def parse_client_message(data: dict[str, Any]) -> ClientMessage:
    """Parse a client message from a dictionary.

    Args:
        data: Dictionary containing the message data

    Returns:
        Parsed client message

    Raises:
        ValueError: If message type is invalid or parsing fails

    """
    msg_type = data.get("type")

    if msg_type == "submit":
        msg = SubmitJobMessage(
            filename=data.get("filename", ""),
            fileData=data.get("fileData", ""),
            multi_file_mode=data.get("multi_file_mode", False),
            filenames=data.get("filenames"),
            filesData=data.get("filesData"),
            config=data.get("config"),
        )
        msg.validate()
        return msg
    elif msg_type == "cancel":
        msg = CancelJobMessage(job_id=data.get("job_id", ""))
        msg.validate()
        return msg
    elif msg_type == "ping":
        return PingMessage()
    else:
        raise ValueError(f"Unknown message type: {msg_type}")
