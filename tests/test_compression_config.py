"""Tests for compression configuration module."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from pdfa.compression_config import PRESETS, CompressionConfig


class TestCompressionConfigDefaults:
    """Test default compression configuration values."""

    def test_default_values(self):
        """Test that default values are correctly set."""
        config = CompressionConfig()

        assert config.image_dpi == 150
        assert config.jpg_quality == 85
        assert config.optimize == 1
        assert config.remove_vectors is True
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 10

    def test_validation_passes_with_defaults(self):
        """Test that default values pass validation."""
        config = CompressionConfig()
        config.validate()  # Should not raise


class TestCompressionConfigValidation:
    """Test compression configuration validation."""

    def test_validate_image_dpi_too_low(self):
        """Test that image_dpi below 72 raises ValueError."""
        config = CompressionConfig(image_dpi=50)
        with pytest.raises(ValueError, match="image_dpi must be between 72 and 600"):
            config.validate()

    def test_validate_image_dpi_too_high(self):
        """Test that image_dpi above 600 raises ValueError."""
        config = CompressionConfig(image_dpi=700)
        with pytest.raises(ValueError, match="image_dpi must be between 72 and 600"):
            config.validate()

    def test_validate_image_dpi_valid_range(self):
        """Test that valid image_dpi values pass validation."""
        for dpi in [72, 150, 300, 600]:
            config = CompressionConfig(image_dpi=dpi)
            config.validate()  # Should not raise

    def test_validate_jpg_quality_too_low(self):
        """Test that jpg_quality below 1 raises ValueError."""
        config = CompressionConfig(jpg_quality=0)
        with pytest.raises(ValueError, match="jpg_quality must be between 1 and 100"):
            config.validate()

    def test_validate_jpg_quality_too_high(self):
        """Test that jpg_quality above 100 raises ValueError."""
        config = CompressionConfig(jpg_quality=101)
        with pytest.raises(ValueError, match="jpg_quality must be between 1 and 100"):
            config.validate()

    def test_validate_jpg_quality_valid_range(self):
        """Test that valid jpg_quality values pass validation."""
        for quality in [1, 50, 85, 100]:
            config = CompressionConfig(jpg_quality=quality)
            config.validate()  # Should not raise

    def test_validate_optimize_invalid(self):
        """Test that invalid optimize values raise ValueError."""
        config = CompressionConfig(optimize=5)  # type: ignore
        with pytest.raises(ValueError, match="optimize must be 0, 1, 2, or 3"):
            config.validate()

    def test_validate_optimize_valid_range(self):
        """Test that valid optimize values pass validation."""
        for opt in [0, 1, 2, 3]:
            config = CompressionConfig(optimize=opt)  # type: ignore
            config.validate()  # Should not raise

    def test_validate_jbig2_page_group_size_invalid(self):
        """Test that invalid jbig2_page_group_size raises ValueError."""
        # Test values outside valid range (1-10000)
        for invalid_value in [-1, 0, 10001]:
            config = CompressionConfig(jbig2_page_group_size=invalid_value)
            with pytest.raises(
                ValueError, match="jbig2_page_group_size must be between 1 and 10000"
            ):
                config.validate()

    def test_validate_jbig2_page_group_size_valid(self):
        """Test that valid jbig2_page_group_size values pass validation."""
        # Valid range: 1-10000
        for size in [1, 10, 50, 100, 10000]:
            config = CompressionConfig(jbig2_page_group_size=size)
            config.validate()  # Should not raise


class TestCompressionConfigFromEnv:
    """Test loading compression configuration from environment variables."""

    def test_from_env_defaults(self):
        """Test that from_env returns defaults when no env vars are set."""
        with patch.dict(os.environ, {}, clear=False):
            # Clear any PDFA_* variables
            for key in list(os.environ.keys()):
                if key.startswith("PDFA_"):
                    del os.environ[key]

            config = CompressionConfig.from_env()

            assert config.image_dpi == 150
            assert config.jpg_quality == 85
            assert config.optimize == 1
            assert config.remove_vectors is True
            assert config.jbig2_lossy is False
            assert config.jbig2_page_group_size == 10

    def test_from_env_custom_values(self):
        """Test that from_env loads custom values from environment."""
        env_vars = {
            "PDFA_IMAGE_DPI": "200",
            "PDFA_JPG_QUALITY": "90",
            "PDFA_OPTIMIZE": "2",
            "PDFA_REMOVE_VECTORS": "false",
            "PDFA_JBIG2_LOSSY": "true",
            "PDFA_JBIG2_PAGE_GROUP_SIZE": "20",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = CompressionConfig.from_env()

            assert config.image_dpi == 200
            assert config.jpg_quality == 90
            assert config.optimize == 2
            assert config.remove_vectors is False
            assert config.jbig2_lossy is True
            assert config.jbig2_page_group_size == 20

    def test_from_env_boolean_variations(self):
        """Test that from_env handles various boolean representations."""
        # Test "true" variations
        for value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
            with patch.dict(os.environ, {"PDFA_REMOVE_VECTORS": value}, clear=False):
                config = CompressionConfig.from_env()
                assert config.remove_vectors is True

        # Test "false" variations
        for value in ["false", "False", "FALSE", "0", "no", "No", "NO"]:
            with patch.dict(os.environ, {"PDFA_REMOVE_VECTORS": value}, clear=False):
                config = CompressionConfig.from_env()
                assert config.remove_vectors is False

    def test_from_env_partial_override(self):
        """Test that from_env allows partial override of defaults."""
        env_vars = {
            "PDFA_IMAGE_DPI": "100",
            "PDFA_JPG_QUALITY": "75",
            # Other values should use defaults
        }

        with patch.dict(os.environ, env_vars, clear=False):
            # Clear other PDFA_* variables
            for key in list(os.environ.keys()):
                if key.startswith("PDFA_") and key not in env_vars:
                    del os.environ[key]

            config = CompressionConfig.from_env()

            assert config.image_dpi == 100
            assert config.jpg_quality == 75
            # Defaults
            assert config.optimize == 1
            assert config.remove_vectors is True
            assert config.jbig2_lossy is False
            assert config.jbig2_page_group_size == 10


class TestCompressionConfigPresets:
    """Test predefined compression configuration presets."""

    def test_balanced_preset(self):
        """Test balanced preset values."""
        config = PRESETS["balanced"]

        assert config.image_dpi == 150
        assert config.jpg_quality == 85
        assert config.optimize == 1
        assert config.remove_vectors is True
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 10

    def test_quality_preset(self):
        """Test quality preset values."""
        config = PRESETS["quality"]

        assert config.image_dpi == 300
        assert config.jpg_quality == 95
        assert config.optimize == 1
        assert config.remove_vectors is False
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 10

    def test_aggressive_preset(self):
        """Test aggressive preset values."""
        config = PRESETS["aggressive"]

        assert config.image_dpi == 100
        assert config.jpg_quality == 75
        assert config.optimize == 3
        assert config.remove_vectors is True
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 20

    def test_minimal_preset(self):
        """Test minimal preset values."""
        config = PRESETS["minimal"]

        assert config.image_dpi == 72
        assert config.jpg_quality == 70
        assert config.optimize == 3
        assert config.remove_vectors is True
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 50

    def test_all_presets_validate(self):
        """Test that all presets pass validation."""
        for name, config in PRESETS.items():
            config.validate()  # Should not raise


class TestCompressionConfigCustomization:
    """Test custom compression configuration scenarios."""

    def test_custom_config(self):
        """Test creating a custom configuration."""
        config = CompressionConfig(
            image_dpi=200,
            jpg_quality=90,
            optimize=2,
            remove_vectors=False,
            jbig2_lossy=False,
            jbig2_page_group_size=15,
        )

        assert config.image_dpi == 200
        assert config.jpg_quality == 90
        assert config.optimize == 2
        assert config.remove_vectors is False
        assert config.jbig2_lossy is False
        assert config.jbig2_page_group_size == 15

        config.validate()  # Should not raise

    def test_config_immutable_after_validation(self):
        """Test that config can be changed and validated multiple times."""
        config = CompressionConfig()
        config.validate()

        # Change values
        config.image_dpi = 300
        config.validate()  # Should not raise

        # Invalid change
        config.image_dpi = 1000
        with pytest.raises(ValueError):
            config.validate()
