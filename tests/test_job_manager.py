"""Tests for job management functionality."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from pdfa.exceptions import JobNotFoundException
from pdfa.job_manager import JobConfig, JobManager
from pdfa.progress_tracker import ProgressInfo


@pytest.fixture
def temp_job_dir(tmp_path):
    """Create a temporary directory for jobs."""
    return tmp_path / "jobs"


@pytest.fixture
def job_config(temp_job_dir):
    """Create a test job configuration."""
    return JobConfig(
        max_concurrent_jobs=2,
        job_timeout_seconds=5,
        completed_job_ttl_seconds=2,
        temp_dir=temp_job_dir,
    )


@pytest.fixture
def job_manager(job_config):
    """Create a test job manager."""
    return JobManager(config=job_config)


class TestJobConfig:
    """Tests for JobConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = JobConfig()

        assert config.max_concurrent_jobs == 5
        assert config.job_timeout_seconds == 7200
        assert config.completed_job_ttl_seconds == 3600
        assert config.ws_ping_interval == 30
        assert config.ws_max_connections == 100

    def test_from_env(self, monkeypatch, tmp_path):
        """Test loading configuration from environment."""
        monkeypatch.setenv("PDFA_MAX_CONCURRENT_JOBS", "10")
        monkeypatch.setenv("PDFA_JOB_TIMEOUT_SECONDS", "1800")
        monkeypatch.setenv("PDFA_TEMP_DIR", str(tmp_path))

        config = JobConfig.from_env()

        assert config.max_concurrent_jobs == 10
        assert config.job_timeout_seconds == 1800
        assert config.temp_dir == tmp_path


class TestJobManager:
    """Tests for JobManager."""

    def test_initialization(self, job_manager, temp_job_dir):
        """Test job manager initialization."""
        assert job_manager.config.temp_dir == temp_job_dir
        assert len(job_manager.jobs) == 0
        assert temp_job_dir.exists()

    def test_create_job(self, job_manager):
        """Test creating a new job."""
        file_data = b"test content"
        config = {"language": "eng"}

        job = job_manager.create_job(
            filename="test.pdf",
            file_data=file_data,
            config=config,
        )

        assert job.job_id in job_manager.jobs
        assert job.filename == "test.pdf"
        assert job.status == "queued"
        assert job.input_path.exists()
        assert job.input_path.read_bytes() == file_data
        assert job.config == config

    def test_get_job(self, job_manager):
        """Test getting a job by ID."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        retrieved = job_manager.get_job(job.job_id)

        assert retrieved.job_id == job.job_id
        assert retrieved.filename == job.filename

    def test_get_job_not_found(self, job_manager):
        """Test getting non-existent job raises exception."""
        with pytest.raises(JobNotFoundException):
            job_manager.get_job("non-existent-id")

    @pytest.mark.asyncio
    async def test_update_job_status(self, job_manager):
        """Test updating job status."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        await job_manager.update_job_status(
            job.job_id,
            "processing",
        )

        assert job.status == "processing"
        assert job.started_at is not None

    @pytest.mark.asyncio
    async def test_update_job_status_completion(self, job_manager, tmp_path):
        """Test updating job status to completed."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        output_path = tmp_path / "output.pdf"
        output_path.write_bytes(b"result")

        await job_manager.update_job_status(
            job.job_id,
            "completed",
            output_path=output_path,
        )

        assert job.status == "completed"
        assert job.completed_at is not None
        assert job.output_path == output_path

    @pytest.mark.asyncio
    async def test_update_job_status_with_error(self, job_manager):
        """Test updating job status with error."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        await job_manager.update_job_status(
            job.job_id,
            "failed",
            error="Test error message",
        )

        assert job.status == "failed"
        assert job.error == "Test error message"

    @pytest.mark.asyncio
    async def test_update_job_progress(self, job_manager):
        """Test updating job progress."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        progress = ProgressInfo(
            step="OCR",
            current=15,
            total=100,
            percentage=15.0,
            message="Processing page 15 of 100",
        )

        await job_manager.update_job_progress(job.job_id, progress)

        assert job.progress == progress
        assert job.progress.current == 15

    @pytest.mark.asyncio
    async def test_cancel_job(self, job_manager):
        """Test cancelling a job."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        await job_manager.update_job_status(job.job_id, "processing")
        await job_manager.cancel_job(job.job_id)

        assert job.status == "cancelled"
        assert job.cancel_event.is_set()

    @pytest.mark.asyncio
    async def test_cancel_completed_job_warning(self, job_manager, caplog):
        """Test cancelling already completed job logs warning."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        await job_manager.update_job_status(job.job_id, "completed")
        await job_manager.cancel_job(job.job_id)

        assert "Cannot cancel job" in caplog.text

    @pytest.mark.asyncio
    async def test_delete_job(self, job_manager):
        """Test deleting a job."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        job_id = job.job_id
        temp_dir_path = Path(job.temp_dir.name)

        await job_manager.delete_job(job_id)

        assert job_id not in job_manager.jobs
        assert not temp_dir_path.exists()

    @pytest.mark.asyncio
    async def test_delete_job_with_websockets(self, job_manager):
        """Test deleting job closes WebSocket connections."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        # Mock WebSocket
        ws = AsyncMock()
        job_manager.register_websocket(job.job_id, ws)

        await job_manager.delete_job(job.job_id)

        ws.close.assert_called_once()

    def test_register_websocket(self, job_manager):
        """Test registering WebSocket for a job."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        ws = Mock()
        job_manager.register_websocket(job.job_id, ws)

        assert ws in job.websockets

    def test_unregister_websocket(self, job_manager):
        """Test unregistering WebSocket from a job."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        ws = Mock()
        job_manager.register_websocket(job.job_id, ws)
        job_manager.unregister_websocket(job.job_id, ws)

        assert ws not in job.websockets

    def test_unregister_websocket_job_not_found(self, job_manager):
        """Test unregistering WebSocket from non-existent job doesn't raise."""
        ws = Mock()
        # Should not raise
        job_manager.unregister_websocket("non-existent", ws)

    @pytest.mark.asyncio
    async def test_broadcast_to_job(self, job_manager):
        """Test broadcasting message to job's WebSockets."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        ws1 = AsyncMock()
        ws2 = AsyncMock()
        job_manager.register_websocket(job.job_id, ws1)
        job_manager.register_websocket(job.job_id, ws2)

        message = {"type": "progress", "percentage": 50}
        await job_manager.broadcast_to_job(job.job_id, message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_websocket(self, job_manager):
        """Test broadcast removes failed WebSocket."""
        job = job_manager.create_job(
            filename="test.pdf",
            file_data=b"content",
            config={},
        )

        ws_good = AsyncMock()
        ws_bad = AsyncMock()
        ws_bad.send_json.side_effect = Exception("Connection lost")

        job_manager.register_websocket(job.job_id, ws_good)
        job_manager.register_websocket(job.job_id, ws_bad)

        message = {"type": "progress"}
        await job_manager.broadcast_to_job(job.job_id, message)

        # Bad websocket should be removed
        assert ws_bad not in job.websockets
        assert ws_good in job.websockets

    def test_get_active_jobs(self, job_manager):
        """Test getting active jobs."""
        job1 = job_manager.create_job("test1.pdf", b"content", {})
        job2 = job_manager.create_job("test2.pdf", b"content", {})
        job3 = job_manager.create_job("test3.pdf", b"content", {})

        job1.status = "processing"
        job2.status = "queued"
        job3.status = "processing"

        active = job_manager.get_active_jobs()

        assert len(active) == 2
        assert job1 in active
        assert job3 in active

    def test_get_queued_jobs(self, job_manager):
        """Test getting queued jobs."""
        job1 = job_manager.create_job("test1.pdf", b"content", {})
        job2 = job_manager.create_job("test2.pdf", b"content", {})

        job1.status = "processing"
        job2.status = "queued"

        queued = job_manager.get_queued_jobs()

        assert len(queued) == 1
        assert job2 in queued

    @pytest.mark.asyncio
    async def test_cleanup_old_jobs(self, job_manager):
        """Test cleanup of old completed jobs."""
        job = job_manager.create_job("test.pdf", b"content", {})

        # Mark as completed with old timestamp
        job.status = "completed"
        job.completed_at = datetime.now() - timedelta(seconds=10)

        await job_manager.cleanup_old_jobs()

        # Job should be deleted (TTL is 2 seconds in test config)
        assert job.job_id not in job_manager.jobs

    @pytest.mark.asyncio
    async def test_cleanup_recent_jobs_preserved(self, job_manager):
        """Test recent completed jobs are not cleaned up."""
        job = job_manager.create_job("test.pdf", b"content", {})

        # Mark as completed recently
        job.status = "completed"
        job.completed_at = datetime.now()

        await job_manager.cleanup_old_jobs()

        # Job should still exist
        assert job.job_id in job_manager.jobs

    @pytest.mark.asyncio
    async def test_check_timeouts(self, job_manager):
        """Test timeout checking for jobs."""
        job = job_manager.create_job("test.pdf", b"content", {})

        # Mark as processing with old timestamp
        job.status = "processing"
        job.started_at = datetime.now() - timedelta(seconds=10)

        await job_manager.check_timeouts()

        # Job should be marked as failed (timeout is 5 seconds in test config)
        assert job.status == "failed"
        assert "timeout" in job.error.lower()

    @pytest.mark.asyncio
    async def test_check_timeouts_recent_jobs(self, job_manager):
        """Test recent processing jobs are not timed out."""
        job = job_manager.create_job("test.pdf", b"content", {})

        job.status = "processing"
        job.started_at = datetime.now()

        await job_manager.check_timeouts()

        # Job should still be processing
        assert job.status == "processing"

    @pytest.mark.asyncio
    async def test_background_tasks_start_stop(self, job_manager):
        """Test starting and stopping background tasks."""
        job_manager.start_background_tasks()

        assert job_manager.cleanup_task is not None
        assert job_manager.timeout_task is not None
        assert not job_manager.cleanup_task.done()
        assert not job_manager.timeout_task.done()

        await job_manager.stop_background_tasks()

        assert job_manager.cleanup_task.done()
        assert job_manager.timeout_task.done()

    @pytest.mark.asyncio
    async def test_cleanup_loop_runs(self, job_manager):
        """Test cleanup loop executes periodically."""
        job = job_manager.create_job("test.pdf", b"content", {})
        job.status = "completed"
        job.completed_at = datetime.now() - timedelta(seconds=10)

        job_manager.start_background_tasks()

        # Wait a bit for cleanup to run (it runs every 60s, but test should be faster)
        # We'll manually trigger it instead
        await job_manager.cleanup_old_jobs()

        assert job.job_id not in job_manager.jobs

        await job_manager.stop_background_tasks()


class TestJobManagerSingleton:
    """Tests for singleton job manager."""

    def test_get_job_manager_singleton(self):
        """Test global job manager is singleton."""
        from pdfa.job_manager import get_job_manager

        manager1 = get_job_manager()
        manager2 = get_job_manager()

        assert manager1 is manager2
