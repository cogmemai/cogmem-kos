"""Passage model - a chunk of text from an Item."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class ExtractionMethod(str, Enum):
    """How the passage was extracted from the source item."""

    CHUNKING = "chunking"
    SEMANTIC = "semantic"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    MANUAL = "manual"
    OTHER = "other"


class TextSpan(BaseModel):
    """Character offsets within the source item."""

    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


class Passage(BaseModel):
    """A chunk of text extracted from an Item.

    Passages are semantically meaningful fragments that serve as the unit
    of indexing for text search, vector search, entity extraction, and
    claim extraction.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    item_id: KosId = Field(..., description="Parent item ID")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    text: str = Field(..., description="Passage text content")
    span: TextSpan | None = Field(None, description="Character offsets in source item")
    sequence: int = Field(0, description="Order within the item")
    extraction_method: ExtractionMethod = Field(
        ExtractionMethod.CHUNKING,
        description="How this passage was extracted",
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in extraction quality (0.0 to 1.0)",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
