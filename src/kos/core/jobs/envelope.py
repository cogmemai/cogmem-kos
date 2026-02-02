"""Job envelope for wrapping jobs with metadata."""

from datetime import datetime
from typing import Any
import uuid

from pydantic import BaseModel, Field

from kos.core.jobs.job_types import JobType, JobStatus


class JobEnvelope(BaseModel):
    """Envelope wrapping a job with tracking metadata."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_type: JobType = Field(..., description="Type of job")
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: str | None = Field(None, description="User identifier")
    status: JobStatus = Field(default=JobStatus.PENDING)
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(0, description="Higher = more urgent")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(None)
    completed_at: datetime | None = Field(None)
    attempts: int = Field(0)
    max_attempts: int = Field(3)
    error: str | None = Field(None)
    result: dict[str, Any] | None = Field(None)
    correlation_id: str | None = Field(None, description="For tracing related jobs")
    assigned_worker: str | None = Field(None)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }

    @classmethod
    def chunk_item(
        cls,
        tenant_id: str,
        user_id: str,
        item_id: str,
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create a CHUNK_ITEM job."""
        return cls(
            job_type=JobType.CHUNK_ITEM,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"item_id": item_id},
            priority=priority,
            correlation_id=correlation_id,
        )

    @classmethod
    def extract_entities(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create an EXTRACT_ENTITIES job."""
        return cls(
            job_type=JobType.EXTRACT_ENTITIES,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids},
            priority=priority,
            correlation_id=correlation_id,
        )

    @classmethod
    def embed_passages(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create an EMBED_PASSAGES job."""
        return cls(
            job_type=JobType.EMBED_PASSAGES,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids},
            priority=priority,
            correlation_id=correlation_id,
        )

    @classmethod
    def index_text(
        cls,
        tenant_id: str,
        user_id: str,
        passage_ids: list[str],
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create an INDEX_TEXT job."""
        return cls(
            job_type=JobType.INDEX_TEXT,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"passage_ids": passage_ids},
            priority=priority,
            correlation_id=correlation_id,
        )

    @classmethod
    def index_graph(
        cls,
        tenant_id: str,
        user_id: str,
        entity_ids: list[str],
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create an INDEX_GRAPH job."""
        return cls(
            job_type=JobType.INDEX_GRAPH,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"entity_ids": entity_ids},
            priority=priority,
            correlation_id=correlation_id,
        )

    @classmethod
    def build_entity_page(
        cls,
        tenant_id: str,
        user_id: str,
        entity_id: str,
        priority: int = 0,
        correlation_id: str | None = None,
    ) -> "JobEnvelope":
        """Create a BUILD_ENTITY_PAGE job."""
        return cls(
            job_type=JobType.BUILD_ENTITY_PAGE,
            tenant_id=tenant_id,
            user_id=user_id,
            payload={"entity_id": entity_id},
            priority=priority,
            correlation_id=correlation_id,
        )

    def mark_started(self, worker_id: str) -> None:
        """Mark job as started."""
        self.status = JobStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.assigned_worker = worker_id
        self.attempts += 1

    def mark_completed(self, result: dict[str, Any] | None = None) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_failed(self, error: str) -> None:
        """Mark job as failed."""
        self.error = error
        if self.attempts >= self.max_attempts:
            self.status = JobStatus.FAILED
        else:
            self.status = JobStatus.PENDING
        self.completed_at = datetime.utcnow()
