"""Job types for agent work."""

from enum import Enum


class JobType(str, Enum):
    """Types of jobs that agents can process."""

    EXTRACT_ITEM = "EXTRACT_ITEM"
    CHUNK_ITEM = "CHUNK_ITEM"
    EXTRACT_ENTITIES = "EXTRACT_ENTITIES"
    EMBED_PASSAGES = "EMBED_PASSAGES"
    INDEX_TEXT = "INDEX_TEXT"
    INDEX_GRAPH = "INDEX_GRAPH"
    BUILD_ENTITY_PAGE = "BUILD_ENTITY_PAGE"

    DELETE_ITEM = "DELETE_ITEM"
    MERGE_ENTITIES = "MERGE_ENTITIES"
    REINDEX_ALL = "REINDEX_ALL"


class JobStatus(str, Enum):
    """Status of a job."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
