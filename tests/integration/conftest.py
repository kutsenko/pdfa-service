"""Integration test configuration and fixtures."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def mongodb_integration_container():
    """Start MongoDB test container for integration tests."""
    project_root = Path(__file__).parent.parent.parent
    compose_file = project_root / "docker-compose.test.yml"

    # Stop any existing test containers
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )

    # Start MongoDB test container
    print("\n[Integration Setup] Starting MongoDB test container...")
    result = subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "up", "-d"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[Integration Setup] Failed to start MongoDB: {result.stderr}")
        pytest.skip("Could not start MongoDB test container")

    # Wait for MongoDB to be healthy
    print("[Integration Setup] Waiting for MongoDB to be ready...")
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
            print("[Integration Setup] MongoDB is ready!")
            break
        time.sleep(1)
    else:
        print("[Integration Setup] MongoDB failed to become healthy")
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down", "-v"],
            cwd=project_root,
        )
        pytest.skip("MongoDB test container did not become healthy")

    # Set environment variables for integration tests
    os.environ["MONGODB_URI"] = "mongodb://admin:test_password@localhost:27018/pdfa_test?authSource=admin"
    os.environ["MONGODB_DATABASE"] = "pdfa_test"
    os.environ["PDFA_ENABLE_AUTH"] = "false"
    os.environ["PDFA_OCR_ENABLED"] = "false"

    yield

    # Cleanup
    print("\n[Integration Teardown] Stopping MongoDB test container...")
    subprocess.run(
        ["docker", "compose", "-f", str(compose_file), "down", "-v"],
        cwd=project_root,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def integration_client(mongodb_integration_container):
    """Return a TestClient with real MongoDB for integration tests."""
    from fastapi.testclient import TestClient
    from pdfa import api

    # Create client that will use real MongoDB
    with TestClient(api.app) as client:
        yield client
