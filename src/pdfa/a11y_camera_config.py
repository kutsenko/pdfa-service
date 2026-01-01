"""Configuration for accessibility camera assistance.

This module provides configuration options for the accessibility camera feature,
allowing fine-tuning of edge detection, audio feedback, and auto-capture behavior.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass


@dataclass
class A11yCameraConfig:
    """Configuration for accessibility camera assistance parameters.

    Attributes:
        # Debug Settings
        debug_enabled: Enable debug logging in browser console (default: False).
            - False: Production mode, minimal logging
            - True: Debug mode, verbose logging for troubleshooting

        # Hysteresis Thresholds
        hysteresis_upper: Upper threshold for edge detection (default: 0.45).
            - Confidence must exceed this to transition from "lost" to "detected"
            - Range: 0.3-0.7
            - Higher = stricter detection

        hysteresis_lower: Lower threshold for edge detection (default: 0.35).
            - Confidence must fall below this to transition from "detected" to "lost"
            - Range: 0.2-0.6
            - Lower = more forgiving (less flickering)

        # Confidence Calculation
        confidence_min_area: Minimum document area ratio (default: 0.10).
            - Documents smaller than this are rejected
            - Range: 0.05-0.20
            - Lower = allows smaller/farther documents

        confidence_max_area: Maximum document area ratio (default: 0.90).
            - Documents larger than this are rejected (too close)
            - Range: 0.70-0.95
            - Higher = allows closer documents

        confidence_peak_area: Optimal document area ratio (default: 0.40).
            - Area where confidence is 1.0 (100%)
            - Range: 0.30-0.50
            - Adjust based on typical use case

        # Auto-Capture Settings
        stable_frame_count: Frames required for stable recognition (default: 10).
            - Number of consecutive good frames before auto-capture
            - Range: 5-20
            - Higher = more stable but slower

        countdown_seconds: Auto-capture countdown duration (default: 2).
            - Seconds to count down before capturing
            - Range: 1-5
            - Gives user time to hold steady

        # Performance Settings
        analysis_fps: Frame analysis rate in Hz (default: 10).
            - How often to analyze frames for edge detection
            - Range: 5-30
            - Higher = more responsive but more CPU usage

        analysis_canvas_width: Analysis canvas width in pixels (default: 640).
            - Smaller = faster but less accurate
            - Range: 320-1280
            - Must maintain 4:3 aspect ratio

        analysis_canvas_height: Analysis canvas height in pixels (default: 480).
            - Smaller = faster but less accurate
            - Range: 240-960
            - Must maintain 4:3 aspect ratio

        # Quality Settings
        jpeg_quality_normal: JPEG quality for normal captures (default: 0.85).
            - Scale: 0.1-1.0 (higher = better quality, larger files)
            - Range: 0.70-0.95

        jpeg_quality_autocrop: JPEG quality for auto-cropped images (default: 0.90).
            - Higher quality for perspective-corrected images
            - Range: 0.80-1.0

        # Audio Feedback
        tone_success_freq: Success tone frequency in Hz (default: 880).
            - A5 note, played when edges detected
            - Range: 400-1200

        tone_success_duration: Success tone duration in ms (default: 200).
            - Range: 100-500

        tone_warning_freq: Warning tone frequency in Hz (default: 440).
            - A4 note, played when edges lost
            - Range: 200-800

        tone_warning_duration: Warning tone duration in ms (default: 150).
            - Range: 100-400

        tone_countdown_freq: Countdown beep frequency in Hz (default: 523).
            - C5 note, played during countdown
            - Range: 400-800

        tone_countdown_duration: Countdown beep duration in ms (default: 100).
            - Range: 50-200

        announcement_throttle_ms: TTS announcement throttle in ms (default: 2000).
            - Minimum time between voice announcements
            - Range: 1000-5000
            - Prevents announcement spam

        # Edge Detection
        edge_margin_pixels: Margin for edge visibility check (default: 20).
            - Pixels from canvas edge to consider "edge not visible"
            - Range: 10-50
            - Lower = stricter centering requirement

    """

    # Debug Settings
    debug_enabled: bool = False

    # Hysteresis Thresholds
    hysteresis_upper: float = 0.45
    hysteresis_lower: float = 0.35

    # Confidence Calculation
    confidence_min_area: float = 0.10
    confidence_max_area: float = 0.90
    confidence_peak_area: float = 0.40

    # Auto-Capture Settings
    stable_frame_count: int = 10
    countdown_seconds: int = 2

    # Performance Settings
    analysis_fps: int = 10
    analysis_canvas_width: int = 640
    analysis_canvas_height: int = 480

    # Quality Settings
    jpeg_quality_normal: float = 0.85
    jpeg_quality_autocrop: float = 0.90

    # Audio Feedback
    tone_success_freq: int = 880
    tone_success_duration: int = 200
    tone_warning_freq: int = 440
    tone_warning_duration: int = 150
    tone_countdown_freq: int = 523
    tone_countdown_duration: int = 100
    announcement_throttle_ms: int = 2000

    # Edge Detection
    edge_margin_pixels: int = 20

    def __post_init__(self) -> None:
        """Validate configuration after initialization.

        This ensures that invalid configurations cannot be created.
        Automatically called by dataclass after __init__.

        Raises:
            ValueError: If any parameter is out of valid range.

        """
        self.validate()

    @classmethod
    def from_env(cls) -> A11yCameraConfig:
        """Load accessibility camera configuration from environment variables.

        Reads the following environment variables:
            - A11Y_CAMERA_DEBUG: Enable debug logging (default: false)
            - A11Y_CAMERA_HYSTERESIS_UPPER: Upper threshold 0.3-0.7 (default: 0.45)
            - A11Y_CAMERA_HYSTERESIS_LOWER: Lower threshold 0.2-0.6 (default: 0.35)
            - A11Y_CAMERA_CONFIDENCE_MIN_AREA: Min area 0.05-0.20 (default: 0.10)
            - A11Y_CAMERA_CONFIDENCE_MAX_AREA: Max area 0.70-0.95 (default: 0.90)
            - A11Y_CAMERA_CONFIDENCE_PEAK_AREA: Peak area 0.30-0.50 (default: 0.40)
            - A11Y_CAMERA_STABLE_FRAMES: Stable frames 5-20 (default: 10)
            - A11Y_CAMERA_COUNTDOWN_SECONDS: Countdown 1-5 (default: 2)
            - A11Y_CAMERA_ANALYSIS_FPS: Analysis FPS 5-30 (default: 10)
            - A11Y_CAMERA_ANALYSIS_WIDTH: Canvas width 320-1280 (default: 640)
            - A11Y_CAMERA_ANALYSIS_HEIGHT: Canvas height 240-960 (default: 480)
            - A11Y_CAMERA_JPEG_QUALITY_NORMAL: JPEG quality 0.70-0.95 (default: 0.85)
            - A11Y_CAMERA_JPEG_QUALITY_AUTOCROP: JPEG quality 0.80-1.0 (default: 0.90)
            - A11Y_CAMERA_TONE_SUCCESS_FREQ: Success tone Hz 400-1200 (default: 880)
            - A11Y_CAMERA_TONE_SUCCESS_DURATION: Success tone ms 100-500 (default: 200)
            - A11Y_CAMERA_TONE_WARNING_FREQ: Warning tone Hz 200-800 (default: 440)
            - A11Y_CAMERA_TONE_WARNING_DURATION: Warning tone ms 100-400 (default: 150)
            - A11Y_CAMERA_TONE_COUNTDOWN_FREQ: Countdown Hz 400-800 (default: 523)
            - A11Y_CAMERA_TONE_COUNTDOWN_DURATION: Countdown ms 50-200 (default: 100)
            - A11Y_CAMERA_ANNOUNCEMENT_THROTTLE: Throttle ms 1000-5000 (default: 2000)
            - A11Y_CAMERA_EDGE_MARGIN: Edge margin 10-50 (default: 20)

        Returns:
            A11yCameraConfig instance with values from environment or defaults.

        """
        return cls(
            debug_enabled=os.getenv("A11Y_CAMERA_DEBUG", "false").lower()
            in ("true", "1", "yes"),
            hysteresis_upper=float(os.getenv("A11Y_CAMERA_HYSTERESIS_UPPER", "0.45")),
            hysteresis_lower=float(os.getenv("A11Y_CAMERA_HYSTERESIS_LOWER", "0.35")),
            confidence_min_area=float(
                os.getenv("A11Y_CAMERA_CONFIDENCE_MIN_AREA", "0.10")
            ),
            confidence_max_area=float(
                os.getenv("A11Y_CAMERA_CONFIDENCE_MAX_AREA", "0.90")
            ),
            confidence_peak_area=float(
                os.getenv("A11Y_CAMERA_CONFIDENCE_PEAK_AREA", "0.40")
            ),
            stable_frame_count=int(os.getenv("A11Y_CAMERA_STABLE_FRAMES", "10")),
            countdown_seconds=int(os.getenv("A11Y_CAMERA_COUNTDOWN_SECONDS", "2")),
            analysis_fps=int(os.getenv("A11Y_CAMERA_ANALYSIS_FPS", "10")),
            analysis_canvas_width=int(os.getenv("A11Y_CAMERA_ANALYSIS_WIDTH", "640")),
            analysis_canvas_height=int(os.getenv("A11Y_CAMERA_ANALYSIS_HEIGHT", "480")),
            jpeg_quality_normal=float(
                os.getenv("A11Y_CAMERA_JPEG_QUALITY_NORMAL", "0.85")
            ),
            jpeg_quality_autocrop=float(
                os.getenv("A11Y_CAMERA_JPEG_QUALITY_AUTOCROP", "0.90")
            ),
            tone_success_freq=int(os.getenv("A11Y_CAMERA_TONE_SUCCESS_FREQ", "880")),
            tone_success_duration=int(
                os.getenv("A11Y_CAMERA_TONE_SUCCESS_DURATION", "200")
            ),
            tone_warning_freq=int(os.getenv("A11Y_CAMERA_TONE_WARNING_FREQ", "440")),
            tone_warning_duration=int(
                os.getenv("A11Y_CAMERA_TONE_WARNING_DURATION", "150")
            ),
            tone_countdown_freq=int(
                os.getenv("A11Y_CAMERA_TONE_COUNTDOWN_FREQ", "523")
            ),
            tone_countdown_duration=int(
                os.getenv("A11Y_CAMERA_TONE_COUNTDOWN_DURATION", "100")
            ),
            announcement_throttle_ms=int(
                os.getenv("A11Y_CAMERA_ANNOUNCEMENT_THROTTLE", "2000")
            ),
            edge_margin_pixels=int(os.getenv("A11Y_CAMERA_EDGE_MARGIN", "20")),
        )

    def validate(self) -> None:
        """Validate accessibility camera configuration parameters.

        Raises:
            ValueError: If any parameter is out of valid range.

        """
        # Hysteresis Thresholds
        if not 0.3 <= self.hysteresis_upper <= 0.7:
            raise ValueError(
                f"hysteresis_upper must be between 0.3 and 0.7, "
                f"got {self.hysteresis_upper}"
            )

        if not 0.2 <= self.hysteresis_lower <= 0.6:
            raise ValueError(
                f"hysteresis_lower must be between 0.2 and 0.6, "
                f"got {self.hysteresis_lower}"
            )

        if self.hysteresis_lower >= self.hysteresis_upper:
            raise ValueError(
                f"hysteresis_lower ({self.hysteresis_lower}) must be less than "
                f"hysteresis_upper ({self.hysteresis_upper})"
            )

        # Confidence Calculation
        if not 0.05 <= self.confidence_min_area <= 0.20:
            raise ValueError(
                f"confidence_min_area must be between 0.05 and 0.20, "
                f"got {self.confidence_min_area}"
            )

        if not 0.70 <= self.confidence_max_area <= 0.95:
            raise ValueError(
                f"confidence_max_area must be between 0.70 and 0.95, "
                f"got {self.confidence_max_area}"
            )

        if not 0.30 <= self.confidence_peak_area <= 0.50:
            raise ValueError(
                f"confidence_peak_area must be between 0.30 and 0.50, "
                f"got {self.confidence_peak_area}"
            )

        if self.confidence_min_area >= self.confidence_peak_area:
            raise ValueError(
                f"confidence_min_area ({self.confidence_min_area}) must be less than "
                f"confidence_peak_area ({self.confidence_peak_area})"
            )

        if self.confidence_peak_area >= self.confidence_max_area:
            raise ValueError(
                f"confidence_peak_area ({self.confidence_peak_area}) must be less than "
                f"confidence_max_area ({self.confidence_max_area})"
            )

        # Auto-Capture Settings
        if not 5 <= self.stable_frame_count <= 20:
            raise ValueError(
                f"stable_frame_count must be between 5 and 20, "
                f"got {self.stable_frame_count}"
            )

        if not 1 <= self.countdown_seconds <= 5:
            raise ValueError(
                f"countdown_seconds must be between 1 and 5, "
                f"got {self.countdown_seconds}"
            )

        # Performance Settings
        if not 5 <= self.analysis_fps <= 30:
            raise ValueError(
                f"analysis_fps must be between 5 and 30, got {self.analysis_fps}"
            )

        if not 320 <= self.analysis_canvas_width <= 1280:
            raise ValueError(
                f"analysis_canvas_width must be between 320 and 1280, "
                f"got {self.analysis_canvas_width}"
            )

        if not 240 <= self.analysis_canvas_height <= 960:
            raise ValueError(
                f"analysis_canvas_height must be between 240 and 960, "
                f"got {self.analysis_canvas_height}"
            )

        # Quality Settings
        if not 0.70 <= self.jpeg_quality_normal <= 0.95:
            raise ValueError(
                f"jpeg_quality_normal must be between 0.70 and 0.95, "
                f"got {self.jpeg_quality_normal}"
            )

        if not 0.80 <= self.jpeg_quality_autocrop <= 1.0:
            raise ValueError(
                f"jpeg_quality_autocrop must be between 0.80 and 1.0, "
                f"got {self.jpeg_quality_autocrop}"
            )

        # Audio Feedback
        if not 400 <= self.tone_success_freq <= 1200:
            raise ValueError(
                f"tone_success_freq must be between 400 and 1200, "
                f"got {self.tone_success_freq}"
            )

        if not 100 <= self.tone_success_duration <= 500:
            raise ValueError(
                f"tone_success_duration must be between 100 and 500, "
                f"got {self.tone_success_duration}"
            )

        if not 200 <= self.tone_warning_freq <= 800:
            raise ValueError(
                f"tone_warning_freq must be between 200 and 800, "
                f"got {self.tone_warning_freq}"
            )

        if not 100 <= self.tone_warning_duration <= 400:
            raise ValueError(
                f"tone_warning_duration must be between 100 and 400, "
                f"got {self.tone_warning_duration}"
            )

        if not 400 <= self.tone_countdown_freq <= 800:
            raise ValueError(
                f"tone_countdown_freq must be between 400 and 800, "
                f"got {self.tone_countdown_freq}"
            )

        if not 50 <= self.tone_countdown_duration <= 200:
            raise ValueError(
                f"tone_countdown_duration must be between 50 and 200, "
                f"got {self.tone_countdown_duration}"
            )

        if not 1000 <= self.announcement_throttle_ms <= 5000:
            raise ValueError(
                f"announcement_throttle_ms must be between 1000 and 5000, "
                f"got {self.announcement_throttle_ms}"
            )

        # Edge Detection
        if not 10 <= self.edge_margin_pixels <= 50:
            raise ValueError(
                f"edge_margin_pixels must be between 10 and 50, "
                f"got {self.edge_margin_pixels}"
            )

    def to_dict(self) -> dict:
        """Convert configuration to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the configuration.

        """
        return asdict(self)
