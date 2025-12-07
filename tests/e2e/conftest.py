"""Pytest configuration and fixtures for E2E tests."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import Page


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def ensure_test_data(test_data_dir: Path) -> None:
    """Ensure test data directory exists and contains test files."""
    test_data_dir.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def api_process(ensure_test_data):
    """Start the FastAPI server for E2E tests."""
    # Start server in background
    process = subprocess.Popen(
        ["uvicorn", "pdfa.api:app", "--host", "localhost", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to be ready
    time.sleep(2)

    yield process

    # Cleanup
    process.terminate()
    process.wait(timeout=5)


@pytest.fixture
def page_with_server(page: Page, api_process) -> Page:
    """Return a Playwright page with the server running."""
    return page
