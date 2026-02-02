"""Items API routes."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from kos.kernel.api.http.schemas.items import (
    ItemResponse,
    ItemCreateRequest,
    PassageResponse,
    EntityRefResponse,
)
from kos.kernel.api.http.dependencies import get_object_store, get_outbox_store
from kos.core.models.ids import KosId, TenantId, UserId, Source
from kos.core.models.item import Item
from kos.core.events.envelope import EventEnvelope

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: str,
    object_store=Depends(get_object_store),
) -> ItemResponse:
    """Get an item with its passages and entities."""
    item = await object_store.get_item(KosId(item_id))
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    passages = await object_store.get_passages_for_item(KosId(item_id))

    return ItemResponse(
        kos_id=item.kos_id,
        tenant_id=item.tenant_id,
        user_id=item.user_id,
        source=item.source.value,
        external_id=item.external_id,
        title=item.title,
        content_text=item.content_text,
        content_type=item.content_type,
        created_at=item.created_at,
        updated_at=item.updated_at,
        metadata=item.metadata,
        passages=[
            PassageResponse(
                kos_id=p.kos_id,
                text=p.text,
                sequence=p.sequence,
                metadata=p.metadata,
            )
            for p in passages
        ],
        entities=[],
    )


@router.post("", response_model=ItemResponse, status_code=201)
async def create_item(
    request: ItemCreateRequest,
    object_store=Depends(get_object_store),
    outbox_store=Depends(get_outbox_store),
) -> ItemResponse:
    """Create a new item and trigger processing."""
    kos_id = KosId(str(uuid.uuid4()))

    try:
        source = Source(request.source)
    except ValueError:
        source = Source.OTHER

    item = Item(
        kos_id=kos_id,
        tenant_id=TenantId(request.tenant_id),
        user_id=UserId(request.user_id),
        source=source,
        external_id=request.external_id,
        title=request.title,
        content_text=request.content_text,
        content_type=request.content_type,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        metadata=request.metadata,
    )

    saved_item = await object_store.save_item(item)

    event = EventEnvelope.item_upserted(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        item_id=kos_id,
        source_agent="api",
    )

    from kos.core.contracts.stores.outbox_store import OutboxEvent

    outbox_event = OutboxEvent(
        event_id=event.event_id,
        event_type=event.event_type.value,
        tenant_id=event.tenant_id,
        payload=event.payload,
        created_at=event.created_at,
    )
    await outbox_store.enqueue_event(outbox_event)

    return ItemResponse(
        kos_id=saved_item.kos_id,
        tenant_id=saved_item.tenant_id,
        user_id=saved_item.user_id,
        source=saved_item.source.value,
        external_id=saved_item.external_id,
        title=saved_item.title,
        content_text=saved_item.content_text,
        content_type=saved_item.content_type,
        created_at=saved_item.created_at,
        updated_at=saved_item.updated_at,
        metadata=saved_item.metadata,
        passages=[],
        entities=[],
    )
