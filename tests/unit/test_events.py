"""Unit tests for events and jobs."""

import pytest

from kos.core.events.event_types import EventType
from kos.core.events.envelope import EventEnvelope
from kos.core.jobs.job_types import JobType, JobStatus
from kos.core.jobs.envelope import JobEnvelope


class TestEventEnvelope:
    """Tests for EventEnvelope."""

    def test_create_item_upserted_event(self):
        """Test creating an ITEM_UPSERTED event."""
        event = EventEnvelope.item_upserted(
            tenant_id="tenant-1",
            user_id="user-1",
            item_id="item-1",
            source_agent="api",
        )

        assert event.event_type == EventType.ITEM_UPSERTED
        assert event.tenant_id == "tenant-1"
        assert event.payload["item_id"] == "item-1"
        assert event.source_agent == "api"
        assert event.event_id is not None

    def test_create_passages_created_event(self):
        """Test creating a PASSAGES_CREATED event."""
        event = EventEnvelope.passages_created(
            tenant_id="tenant-1",
            user_id="user-1",
            item_id="item-1",
            passage_ids=["p1", "p2", "p3"],
            source_agent="chunk_agent",
        )

        assert event.event_type == EventType.PASSAGES_CREATED
        assert event.payload["item_id"] == "item-1"
        assert len(event.payload["passage_ids"]) == 3

    def test_event_correlation_id(self):
        """Test event correlation ID propagation."""
        event = EventEnvelope.item_upserted(
            tenant_id="tenant-1",
            user_id="user-1",
            item_id="item-1",
            correlation_id="corr-123",
        )

        assert event.correlation_id == "corr-123"


class TestJobEnvelope:
    """Tests for JobEnvelope."""

    def test_create_chunk_job(self):
        """Test creating a CHUNK_ITEM job."""
        job = JobEnvelope.chunk_item(
            tenant_id="tenant-1",
            user_id="user-1",
            item_id="item-1",
        )

        assert job.job_type == JobType.CHUNK_ITEM
        assert job.status == JobStatus.PENDING
        assert job.payload["item_id"] == "item-1"
        assert job.attempts == 0

    def test_job_lifecycle(self):
        """Test job status transitions."""
        job = JobEnvelope.embed_passages(
            tenant_id="tenant-1",
            user_id="user-1",
            passage_ids=["p1", "p2"],
        )

        assert job.status == JobStatus.PENDING

        job.mark_started("worker-1")
        assert job.status == JobStatus.IN_PROGRESS
        assert job.assigned_worker == "worker-1"
        assert job.attempts == 1

        job.mark_completed({"embedded": 2})
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"embedded": 2}

    def test_job_failure_retry(self):
        """Test job failure and retry logic."""
        job = JobEnvelope.extract_entities(
            tenant_id="tenant-1",
            user_id="user-1",
            passage_ids=["p1"],
        )
        job.max_attempts = 3

        job.mark_started("worker-1")
        job.mark_failed("Connection error")
        assert job.status == JobStatus.PENDING
        assert job.attempts == 1

        job.mark_started("worker-1")
        job.mark_failed("Connection error")
        assert job.status == JobStatus.PENDING
        assert job.attempts == 2

        job.mark_started("worker-1")
        job.mark_failed("Connection error")
        assert job.status == JobStatus.FAILED
        assert job.attempts == 3
