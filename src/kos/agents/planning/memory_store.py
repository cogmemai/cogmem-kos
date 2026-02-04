"""Memory store contract for the personal planning agent."""

from abc import ABC, abstractmethod
from typing import Any

from kos.agents.planning.models import Memory, MemoryType


class MemoryStore(ABC):
    """Abstract base class for memory store implementations.
    
    The memory store provides persistent, user-specific memory for the
    personal planning agent, enabling learning and adaptation over time.
    """

    @abstractmethod
    async def save_memory(self, memory: Memory) -> Memory:
        """Save or update a memory."""
        ...

    @abstractmethod
    async def get_memory(self, memory_id: str) -> Memory | None:
        """Get a memory by ID."""
        ...

    @abstractmethod
    async def search_memories(
        self,
        tenant_id: str,
        user_id: str,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int = 10,
    ) -> list[Memory]:
        """Search memories by semantic similarity to query.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            query: Search query for semantic matching
            memory_types: Optional filter by memory types
            limit: Maximum number of memories to return
            
        Returns:
            List of relevant memories, ordered by relevance
        """
        ...

    @abstractmethod
    async def list_memories(
        self,
        tenant_id: str,
        user_id: str,
        memory_type: MemoryType | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Memory]:
        """List memories for a user.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            memory_type: Optional filter by memory type
            limit: Maximum number of memories to return
            offset: Offset for pagination
            
        Returns:
            List of memories
        """
        ...

    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory. Returns True if deleted."""
        ...

    @abstractmethod
    async def update_access(self, memory_id: str) -> None:
        """Update the access count and last accessed timestamp for a memory."""
        ...

    @abstractmethod
    async def decay_memories(
        self,
        tenant_id: str,
        user_id: str,
        decay_factor: float = 0.95,
    ) -> int:
        """Apply decay to memory relevance scores.
        
        Memories that are not accessed frequently will have their
        relevance scores reduced over time.
        
        Args:
            tenant_id: Tenant identifier
            user_id: User identifier
            decay_factor: Factor to multiply relevance scores by
            
        Returns:
            Number of memories updated
        """
        ...
