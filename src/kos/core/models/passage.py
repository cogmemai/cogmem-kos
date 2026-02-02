"""Passage model - a chunk of text from an Item."""

from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class TextSpan(BaseModel):
    """Character offsets within the source item."""

    start: int = Field(..., ge=0)
    end: int = Field(..., ge=0)


class Passage(BaseModel):
    """A chunk of text extracted from an Item.

    Passages are the unit of indexing for text search, vector search,
    and entity extraction.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    item_id: KosId = Field(..., description="Parent item ID")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    text: str = Field(..., description="Passage text content")
    span: TextSpan | None = Field(None, description="Character offsets in source item")
    sequence: int = Field(0, description="Order within the item")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
