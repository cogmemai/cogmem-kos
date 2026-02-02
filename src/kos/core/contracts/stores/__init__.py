"""Store contract interfaces."""

from kos.core.contracts.stores.admin_store import AdminStore
from kos.core.contracts.stores.object_store import ObjectStore
from kos.core.contracts.stores.outbox_store import OutboxStore

__all__ = [
    "AdminStore",
    "ObjectStore",
    "OutboxStore",
]
