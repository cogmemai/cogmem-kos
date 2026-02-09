"""Entity model - extracted named entities."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from kos.core.models.ids import KosId, TenantId, UserId


class EntityType(str, Enum):
    """Types of entities that can be extracted."""

    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    CONCEPT = "concept"
    LOCATION = "location"
    EVENT = "event"
    PRODUCT = "product"
    TECHNOLOGY = "technology"
    DATE = "date"
    OTHER = "other"


class Entity(BaseModel):
    """An extracted named entity.

    Entities are canonical representations of people, projects, concepts,
    tools, or places. They are nodes in the knowledge graph, linked to
    passages via MENTIONS relationships and to claims as subjects.
    """

    kos_id: KosId = Field(..., description="Stable global identifier")
    tenant_id: TenantId = Field(..., description="Tenant identifier")
    user_id: UserId = Field(..., description="User identifier")
    name: str = Field(..., description="Canonical entity name")
    entity_type: EntityType = Field(..., description="Entity type")
    aliases: list[str] = Field(default_factory=list, description="Alternative names")
    created_from: list[KosId] = Field(
        default_factory=list,
        description="Passage IDs that led to this entity's creation",
    )
    last_updated_at: datetime | None = Field(
        None,
        description="When this entity was last updated with new information",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }
