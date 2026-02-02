"""Item model - the primary ingested document/content unit."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId, Source


class Item(BaseModel):
    """An ingested document or content unit.

    Items are the primary objects that enter the system via connectors
    or direct ingestion. They are chunked into Passages for indexing.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    source: Source = Field(..., description="Source system")
    external_id: str | None = Field(None, description="ID in source system")
    title: str = Field(..., description="Item title")
    content_text: str = Field(..., description="Raw extracted text content")
    content_type: str = Field(..., description="Content type (email/pdf/html/chat/etc.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
