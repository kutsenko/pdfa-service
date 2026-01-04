"""Pytest configuration and fixtures for E2E tests."""

from __future__ import annotations

import os
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
def mongodb_test_container():
    """Start MongoDB test container using docker compose."""
    project_root = Path(__file__).parent.parent.parent
    compose_file = project_root / "docker-compose.test.yml"

    # Stop any existing test containers
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )

    # Start MongoDB test container
    print("\n[E2E Setup] Starting MongoDB test container...")
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[E2E Setup] Failed to start MongoDB: {result.stderr}")
        pytest.skip("Could not start MongoDB test container")

    # Wait for MongoDB to be healthy
    print("[E2E Setup] Waiting for MongoDB to be ready...")
    for i in range(30):
        health_check = subprocess.run(
            [
                "docker",
                "exec",
                "pdfa-mongodb-test",
                "mongosh",
                "--eval",
                "db.adminCommand('ping')",
            ],
            capture_output=True,
        )
        if health_check.returncode == 0:
            print("[E2E Setup] MongoDB is ready!")
            break
        time.sleep(1)
    else:
        print("[E2E Setup] MongoDB failed to become healthy")
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down", "-v"],
            cwd=project_root,
        )
        pytest.skip("MongoDB test container did not become healthy")

    yield

    # Cleanup
    print("\n[E2E Teardown] Stopping MongoDB test container...")
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )


@pytest.fixture(scope="session")
def api_process(ensure_test_data, mongodb_test_container):
    """Start the FastAPI server for E2E tests."""
    # Set test environment variables
    test_env = os.environ.copy()
    test_env.update(
        {
            "MONGODB_URI": "mongodb://admin:test_password@localhost:27018/pdfa_test?authSource=admin",
            "MONGODB_DATABASE": "pdfa_test",
            "PDFA_ENABLE_AUTH": "false",  # Disable OAuth for tests
            "PYTHONUNBUFFERED": "1",
            # Disable OCR for tests (Tesseract language data not installed)
            "PDFA_OCR_ENABLED": "false",
            # Disable static file caching to prevent browser caching issues in tests
            "ENABLE_STATIC_CACHE": "false",
        }
    )

    # Start server in background on port 8001 (to avoid conflicts with dev server)
    print("[E2E Setup] Starting FastAPI server on port 8001...")
    process = subprocess.Popen(
        ["uvicorn", "pdfa.api:app", "--host", "localhost", "--port", "8001"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=test_env,
    )

    # Wait for server to be ready
    print("[E2E Setup] Waiting for server to start...")
    time.sleep(4)

    # Check if server started successfully
    if process.poll() is not None:
        stdout, stderr = process.communicate()
        print("[E2E Setup] Server failed to start!")
        print(f"STDOUT: {stdout.decode()}")
        print(f"STDERR: {stderr.decode()}")
        pytest.skip("FastAPI server failed to start")

    print("[E2E Setup] Server is ready on http://localhost:8001!")

    yield process

    # Cleanup
    print("\n[E2E Teardown] Stopping FastAPI server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture(scope="session")
def browser_launch_args(browser_launch_args):
    """Configure browser launch arguments to disable caching.

    These arguments are passed to Chromium/Firefox on launch to completely
    disable all forms of caching.
    """
    return {
        **browser_launch_args,
        "args": [
            "--disable-http-cache",
            "--disable-cache",
            "--disable-application-cache",
            "--disable-offline-load-stale-cache",
            "--disk-cache-size=0",
            "--disable-dev-shm-usage",
            "--disable-gpu-shader-disk-cache",
        ],
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context to disable caching for E2E tests.

    This ensures that JavaScript and CSS changes are immediately reflected
    in tests without requiring manual cache clearing.
    """
    return {
        **browser_context_args,
        "ignore_https_errors": True,
        "bypass_csp": True,
        # Disable service workers that might cache resources
        "service_workers": "block",
    }


@pytest.fixture
def context(browser, browser_context_args):
    """Create a fresh browser context with cache disabled for each test.

    This prevents caching issues where old JavaScript/CSS files are loaded
    instead of updated versions.
    """
    # Create new context with our custom args
    ctx = browser.new_context(**browser_context_args)

    # Clear any existing cookies/storage
    ctx.clear_cookies()

    yield ctx

    # Clean up
    ctx.close()


@pytest.fixture
def page(context, api_process):
    """Create a fresh page with all caches cleared for each test.

    This overrides the default Playwright page fixture to ensure
    no cached resources are used.
    """
    # Create new page
    pg = context.new_page()

    yield pg

    # Clean up
    pg.close()


@pytest.fixture
def page_with_server(page: Page, api_process) -> Page:
    """Return a Playwright page with the server running."""
    return page
