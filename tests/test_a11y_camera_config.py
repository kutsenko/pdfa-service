"""Tests for accessibility camera configuration module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pdfa.a11y_camera_config import A11yCameraConfig


class TestA11yCameraConfigDefaults:
    """Test default accessibility camera configuration values."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = A11yCameraConfig()

        # Debug Settings
        assert config.debug_enabled is False

        # Hysteresis Thresholds
        assert config.hysteresis_upper == 0.45
        assert config.hysteresis_lower == 0.35

        # Confidence Calculation
        assert config.confidence_min_area == 0.10
        assert config.confidence_max_area == 0.90
        assert config.confidence_peak_area == 0.40

        # Auto-Capture Settings
        assert config.stable_frame_count == 10
        assert config.countdown_seconds == 2

        # Performance Settings
        assert config.analysis_fps == 10
        assert config.analysis_canvas_width == 640
        assert config.analysis_canvas_height == 480

        # Quality Settings
        assert config.jpeg_quality_normal == 0.85
        assert config.jpeg_quality_autocrop == 0.90

        # Audio Feedback
        assert config.tone_success_freq == 880
        assert config.tone_success_duration == 200
        assert config.tone_warning_freq == 440
        assert config.tone_warning_duration == 150
        assert config.tone_countdown_freq == 523
        assert config.tone_countdown_duration == 100
        assert config.announcement_throttle_ms == 2000

        # Edge Detection
        assert config.edge_margin_pixels == 20

    def test_validation_passes_with_defaults(self):
        """Test that default values pass validation."""
        config = A11yCameraConfig()
        config.validate()  # Should not raise

    def test_to_dict(self):
        """Test that to_dict returns correct dictionary."""
        config = A11yCameraConfig()
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["debug_enabled"] is False
        assert config_dict["hysteresis_upper"] == 0.45
        assert config_dict["stable_frame_count"] == 10


class TestA11yCameraConfigValidation:
    """Test accessibility camera configuration validation."""

    # Hysteresis Thresholds
    def test_validate_hysteresis_upper_too_low(self):
        """Test that hysteresis_upper below 0.3 raises ValueError."""
        with pytest.raises(
            ValueError, match="hysteresis_upper must be between 0.3 and 0.7"
        ):

            A11yCameraConfig(hysteresis_upper=0.2)

    def test_validate_hysteresis_upper_too_high(self):
        """Test that hysteresis_upper above 0.7 raises ValueError."""
        with pytest.raises(
            ValueError, match="hysteresis_upper must be between 0.3 and 0.7"
        ):

            A11yCameraConfig(hysteresis_upper=0.8)

    def test_validate_hysteresis_lower_too_low(self):
        """Test that hysteresis_lower below 0.2 raises ValueError."""
        with pytest.raises(
            ValueError, match="hysteresis_lower must be between 0.2 and 0.6"
        ):

            A11yCameraConfig(hysteresis_lower=0.1)

    def test_validate_hysteresis_lower_too_high(self):
        """Test that hysteresis_lower above 0.6 raises ValueError."""
        with pytest.raises(
            ValueError, match="hysteresis_lower must be between 0.2 and 0.6"
        ):

            A11yCameraConfig(hysteresis_lower=0.7)

    def test_validate_hysteresis_lower_greater_than_upper(self):
        """Test that hysteresis_lower >= hysteresis_upper raises ValueError."""
        with pytest.raises(
            ValueError,
            match="hysteresis_lower .* must be less than hysteresis_upper",
        ):

            A11yCameraConfig(hysteresis_lower=0.5, hysteresis_upper=0.4)

    def test_validate_hysteresis_valid_range(self):
        """Test that valid hysteresis values pass validation."""
        config = A11yCameraConfig(hysteresis_lower=0.3, hysteresis_upper=0.5)
        config.validate()  # Should not raise

    # Confidence Calculation
    def test_validate_confidence_min_area_too_low(self):
        """Test that confidence_min_area below 0.05 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_min_area must be between 0.05 and 0.20"
        ):

            A11yCameraConfig(confidence_min_area=0.04)

    def test_validate_confidence_min_area_too_high(self):
        """Test that confidence_min_area above 0.20 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_min_area must be between 0.05 and 0.20"
        ):

            A11yCameraConfig(confidence_min_area=0.25)

    def test_validate_confidence_max_area_too_low(self):
        """Test that confidence_max_area below 0.70 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_max_area must be between 0.70 and 0.95"
        ):

            A11yCameraConfig(confidence_max_area=0.65)

    def test_validate_confidence_max_area_too_high(self):
        """Test that confidence_max_area above 0.95 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_max_area must be between 0.70 and 0.95"
        ):

            A11yCameraConfig(confidence_max_area=0.96)

    def test_validate_confidence_peak_area_too_low(self):
        """Test that confidence_peak_area below 0.30 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_peak_area must be between 0.30 and 0.50"
        ):

            A11yCameraConfig(confidence_peak_area=0.25)

    def test_validate_confidence_peak_area_too_high(self):
        """Test that confidence_peak_area above 0.50 raises ValueError."""
        with pytest.raises(
            ValueError, match="confidence_peak_area must be between 0.30 and 0.50"
        ):

            A11yCameraConfig(confidence_peak_area=0.55)

    def test_validate_confidence_areas_valid_relationship(self):
        """Test that valid confidence areas with correct relationships pass validation.

        Note: The relationship checks (min < peak < max) are guaranteed by the
        individual range checks since the ranges don't overlap:
        - min_area: 0.05-0.20
        - peak_area: 0.30-0.50
        - max_area: 0.70-0.95
        """
        config = A11yCameraConfig(
            confidence_min_area=0.10,
            confidence_peak_area=0.40,
            confidence_max_area=0.90,
        )
        config.validate()  # Should not raise

    # Auto-Capture Settings
    def test_validate_stable_frame_count_too_low(self):
        """Test that stable_frame_count below 5 raises ValueError."""
        with pytest.raises(
            ValueError, match="stable_frame_count must be between 5 and 20"
        ):

            A11yCameraConfig(stable_frame_count=4)

    def test_validate_stable_frame_count_too_high(self):
        """Test that stable_frame_count above 20 raises ValueError."""
        with pytest.raises(
            ValueError, match="stable_frame_count must be between 5 and 20"
        ):

            A11yCameraConfig(stable_frame_count=25)

    def test_validate_countdown_seconds_too_low(self):
        """Test that countdown_seconds below 1 raises ValueError."""
        with pytest.raises(
            ValueError, match="countdown_seconds must be between 1 and 5"
        ):

            A11yCameraConfig(countdown_seconds=0)

    def test_validate_countdown_seconds_too_high(self):
        """Test that countdown_seconds above 5 raises ValueError."""
        with pytest.raises(
            ValueError, match="countdown_seconds must be between 1 and 5"
        ):

            A11yCameraConfig(countdown_seconds=6)

    # Performance Settings
    def test_validate_analysis_fps_too_low(self):
        """Test that analysis_fps below 5 raises ValueError."""
        with pytest.raises(ValueError, match="analysis_fps must be between 5 and 30"):

            A11yCameraConfig(analysis_fps=4)

    def test_validate_analysis_fps_too_high(self):
        """Test that analysis_fps above 30 raises ValueError."""
        with pytest.raises(ValueError, match="analysis_fps must be between 5 and 30"):

            A11yCameraConfig(analysis_fps=35)

    def test_validate_analysis_canvas_width_too_low(self):
        """Test that analysis_canvas_width below 320 raises ValueError."""
        with pytest.raises(
            ValueError, match="analysis_canvas_width must be between 320 and 1280"
        ):

            A11yCameraConfig(analysis_canvas_width=300)

    def test_validate_analysis_canvas_width_too_high(self):
        """Test that analysis_canvas_width above 1280 raises ValueError."""
        with pytest.raises(
            ValueError, match="analysis_canvas_width must be between 320 and 1280"
        ):

            A11yCameraConfig(analysis_canvas_width=1300)

    def test_validate_analysis_canvas_height_too_low(self):
        """Test that analysis_canvas_height below 240 raises ValueError."""
        with pytest.raises(
            ValueError, match="analysis_canvas_height must be between 240 and 960"
        ):

            A11yCameraConfig(analysis_canvas_height=200)

    def test_validate_analysis_canvas_height_too_high(self):
        """Test that analysis_canvas_height above 960 raises ValueError."""
        with pytest.raises(
            ValueError, match="analysis_canvas_height must be between 240 and 960"
        ):

            A11yCameraConfig(analysis_canvas_height=1000)

    # Quality Settings
    def test_validate_jpeg_quality_normal_too_low(self):
        """Test that jpeg_quality_normal below 0.70 raises ValueError."""
        with pytest.raises(
            ValueError, match="jpeg_quality_normal must be between 0.70 and 0.95"
        ):

            A11yCameraConfig(jpeg_quality_normal=0.65)

    def test_validate_jpeg_quality_normal_too_high(self):
        """Test that jpeg_quality_normal above 0.95 raises ValueError."""
        with pytest.raises(
            ValueError, match="jpeg_quality_normal must be between 0.70 and 0.95"
        ):

            A11yCameraConfig(jpeg_quality_normal=0.96)

    def test_validate_jpeg_quality_autocrop_too_low(self):
        """Test that jpeg_quality_autocrop below 0.80 raises ValueError."""
        with pytest.raises(
            ValueError, match="jpeg_quality_autocrop must be between 0.80 and 1.0"
        ):

            A11yCameraConfig(jpeg_quality_autocrop=0.75)

    def test_validate_jpeg_quality_autocrop_too_high(self):
        """Test that jpeg_quality_autocrop above 1.0 raises ValueError."""
        with pytest.raises(
            ValueError, match="jpeg_quality_autocrop must be between 0.80 and 1.0"
        ):

            A11yCameraConfig(jpeg_quality_autocrop=1.1)

    # Audio Feedback
    def test_validate_tone_success_freq_too_low(self):
        """Test that tone_success_freq below 400 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_success_freq must be between 400 and 1200"
        ):

            A11yCameraConfig(tone_success_freq=300)

    def test_validate_tone_success_freq_too_high(self):
        """Test that tone_success_freq above 1200 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_success_freq must be between 400 and 1200"
        ):

            A11yCameraConfig(tone_success_freq=1300)

    def test_validate_tone_success_duration_too_low(self):
        """Test that tone_success_duration below 100 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_success_duration must be between 100 and 500"
        ):

            A11yCameraConfig(tone_success_duration=50)

    def test_validate_tone_success_duration_too_high(self):
        """Test that tone_success_duration above 500 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_success_duration must be between 100 and 500"
        ):

            A11yCameraConfig(tone_success_duration=600)

    def test_validate_tone_warning_freq_too_low(self):
        """Test that tone_warning_freq below 200 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_warning_freq must be between 200 and 800"
        ):

            A11yCameraConfig(tone_warning_freq=150)

    def test_validate_tone_warning_freq_too_high(self):
        """Test that tone_warning_freq above 800 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_warning_freq must be between 200 and 800"
        ):

            A11yCameraConfig(tone_warning_freq=900)

    def test_validate_tone_warning_duration_too_low(self):
        """Test that tone_warning_duration below 100 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_warning_duration must be between 100 and 400"
        ):

            A11yCameraConfig(tone_warning_duration=50)

    def test_validate_tone_warning_duration_too_high(self):
        """Test that tone_warning_duration above 400 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_warning_duration must be between 100 and 400"
        ):

            A11yCameraConfig(tone_warning_duration=500)

    def test_validate_tone_countdown_freq_too_low(self):
        """Test that tone_countdown_freq below 400 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_countdown_freq must be between 400 and 800"
        ):

            A11yCameraConfig(tone_countdown_freq=300)

    def test_validate_tone_countdown_freq_too_high(self):
        """Test that tone_countdown_freq above 800 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_countdown_freq must be between 400 and 800"
        ):

            A11yCameraConfig(tone_countdown_freq=900)

    def test_validate_tone_countdown_duration_too_low(self):
        """Test that tone_countdown_duration below 50 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_countdown_duration must be between 50 and 200"
        ):

            A11yCameraConfig(tone_countdown_duration=40)

    def test_validate_tone_countdown_duration_too_high(self):
        """Test that tone_countdown_duration above 200 raises ValueError."""
        with pytest.raises(
            ValueError, match="tone_countdown_duration must be between 50 and 200"
        ):

            A11yCameraConfig(tone_countdown_duration=250)

    def test_validate_announcement_throttle_too_low(self):
        """Test that announcement_throttle_ms below 1000 raises ValueError."""
        with pytest.raises(
            ValueError, match="announcement_throttle_ms must be between 1000 and 5000"
        ):

            A11yCameraConfig(announcement_throttle_ms=500)

    def test_validate_announcement_throttle_too_high(self):
        """Test that announcement_throttle_ms above 5000 raises ValueError."""
        with pytest.raises(
            ValueError, match="announcement_throttle_ms must be between 1000 and 5000"
        ):

            A11yCameraConfig(announcement_throttle_ms=6000)

    # Edge Detection
    def test_validate_edge_margin_pixels_too_low(self):
        """Test that edge_margin_pixels below 10 raises ValueError."""
        with pytest.raises(
            ValueError, match="edge_margin_pixels must be between 10 and 50"
        ):

            A11yCameraConfig(edge_margin_pixels=5)

    def test_validate_edge_margin_pixels_too_high(self):
        """Test that edge_margin_pixels above 50 raises ValueError."""
        with pytest.raises(
            ValueError, match="edge_margin_pixels must be between 10 and 50"
        ):

            A11yCameraConfig(edge_margin_pixels=60)


class TestA11yCameraConfigFromEnv:
    """Test loading accessibility camera configuration from environment variables."""

    def test_from_env_defaults(self):
        """Test that from_env returns defaults when no env vars are set."""
        with patch.dict(os.environ, {}, clear=False):
            # Clear any A11Y_CAMERA_* variables
            for key in list(os.environ.keys()):
                if key.startswith("A11Y_CAMERA_"):
                    del os.environ[key]

            config = A11yCameraConfig.from_env()

            # Verify defaults
            assert config.debug_enabled is False
            assert config.hysteresis_upper == 0.45
            assert config.hysteresis_lower == 0.35
            assert config.stable_frame_count == 10

    def test_from_env_custom_values(self):
        """Test that from_env loads custom values from environment."""
        env_vars = {
            "A11Y_CAMERA_DEBUG": "true",
            "A11Y_CAMERA_HYSTERESIS_UPPER": "0.50",
            "A11Y_CAMERA_HYSTERESIS_LOWER": "0.30",
            "A11Y_CAMERA_CONFIDENCE_MIN_AREA": "0.15",
            "A11Y_CAMERA_CONFIDENCE_MAX_AREA": "0.85",
            "A11Y_CAMERA_CONFIDENCE_PEAK_AREA": "0.45",
            "A11Y_CAMERA_STABLE_FRAMES": "15",
            "A11Y_CAMERA_COUNTDOWN_SECONDS": "3",
            "A11Y_CAMERA_ANALYSIS_FPS": "15",
            "A11Y_CAMERA_JPEG_QUALITY_NORMAL": "0.90",
            "A11Y_CAMERA_JPEG_QUALITY_AUTOCROP": "0.95",
            "A11Y_CAMERA_TONE_SUCCESS_FREQ": "800",
            "A11Y_CAMERA_TONE_SUCCESS_DURATION": "250",
            "A11Y_CAMERA_TONE_WARNING_FREQ": "500",
            "A11Y_CAMERA_TONE_WARNING_DURATION": "200",
            "A11Y_CAMERA_TONE_COUNTDOWN_FREQ": "600",
            "A11Y_CAMERA_TONE_COUNTDOWN_DURATION": "150",
            "A11Y_CAMERA_ANNOUNCEMENT_THROTTLE": "3000",
            "A11Y_CAMERA_EDGE_MARGIN": "30",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = A11yCameraConfig.from_env()

            assert config.debug_enabled is True
            assert config.hysteresis_upper == 0.50
            assert config.hysteresis_lower == 0.30
            assert config.confidence_min_area == 0.15
            assert config.confidence_max_area == 0.85
            assert config.confidence_peak_area == 0.45
            assert config.stable_frame_count == 15
            assert config.countdown_seconds == 3
            assert config.analysis_fps == 15
            assert config.jpeg_quality_normal == 0.90
            assert config.jpeg_quality_autocrop == 0.95
            assert config.tone_success_freq == 800
            assert config.tone_success_duration == 250
            assert config.tone_warning_freq == 500
            assert config.tone_warning_duration == 200
            assert config.tone_countdown_freq == 600
            assert config.tone_countdown_duration == 150
            assert config.announcement_throttle_ms == 3000
            assert config.edge_margin_pixels == 30

    def test_from_env_boolean_variations(self):
        """Test that from_env handles various boolean representations."""
        # Test "true" variations
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
            with patch.dict(os.environ, {"A11Y_CAMERA_DEBUG": value}, clear=False):
                config = A11yCameraConfig.from_env()
                assert config.debug_enabled is True

        # Test "false" variations
        for value in ["false", "False", "FALSE", "0", "no", "No", "NO"]:
            with patch.dict(os.environ, {"A11Y_CAMERA_DEBUG": value}, clear=False):
                config = A11yCameraConfig.from_env()
                assert config.debug_enabled is False

    def test_from_env_partial_override(self):
        """Test that from_env allows partial override of defaults."""
        env_vars = {
            "A11Y_CAMERA_DEBUG": "true",
            "A11Y_CAMERA_ANALYSIS_FPS": "20",
            # Other values should use defaults
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Clear other A11Y_CAMERA_* variables
            for key in list(os.environ.keys()):
                if key.startswith("A11Y_CAMERA_") and key not in env_vars:
                    del os.environ[key]

            config = A11yCameraConfig.from_env()

            assert config.debug_enabled is True
            assert config.analysis_fps == 20
            # Defaults
            assert config.hysteresis_upper == 0.45
            assert config.stable_frame_count == 10


class TestA11yCameraConfigCustomization:
    """Test custom accessibility camera configuration scenarios."""

    def test_custom_config(self):
        """Test creating a custom configuration."""
        config = A11yCameraConfig(
            debug_enabled=True,
            hysteresis_upper=0.50,
            hysteresis_lower=0.30,
            stable_frame_count=15,
            analysis_fps=20,
        )

        assert config.debug_enabled is True
        assert config.hysteresis_upper == 0.50
        assert config.hysteresis_lower == 0.30
        assert config.stable_frame_count == 15
        assert config.analysis_fps == 20

        config.validate()  # Should not raise

    def test_config_can_be_changed_and_revalidated(self):
        """Test that config can be changed and validated multiple times."""
        config = A11yCameraConfig()
        config.validate()

        # Change values
        config.analysis_fps = 20
        config.validate()  # Should not raise

        # Invalid change
        config.analysis_fps = 100
        with pytest.raises(ValueError):
            config.validate()

    def test_all_parameters_customizable(self):
        """Test that all parameters can be customized."""
        config = A11yCameraConfig(
            debug_enabled=True,
            hysteresis_upper=0.60,
            hysteresis_lower=0.25,
            confidence_min_area=0.08,
            confidence_max_area=0.92,
            confidence_peak_area=0.35,
            stable_frame_count=12,
            countdown_seconds=3,
            analysis_fps=15,
            analysis_canvas_width=800,
            analysis_canvas_height=600,
            jpeg_quality_normal=0.80,
            jpeg_quality_autocrop=0.92,
            tone_success_freq=1000,
            tone_success_duration=300,
            tone_warning_freq=600,
            tone_warning_duration=200,
            tone_countdown_freq=700,
            tone_countdown_duration=120,
            announcement_throttle_ms=2500,
            edge_margin_pixels=25,
        )

        config.validate()  # Should not raise
        assert config.debug_enabled is True
        assert config.hysteresis_upper == 0.60
        assert config.edge_margin_pixels == 25
