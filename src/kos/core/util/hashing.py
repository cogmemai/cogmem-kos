"""Hashing utilities for content deduplication."""

import hashlib
from typing import Any


def hash_text(text: str) -> str:
    """Generate a SHA-256 hash of text content.

    Args:
        text: Text to hash.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_content(content: bytes) -> str:
    """Generate a SHA-256 hash of binary content.

    Args:
        content: Binary content to hash.

    Returns:
        Hex-encoded SHA-256 hash.
    """
    return hashlib.sha256(content).hexdigest()


def generate_content_id(
    tenant_id: str,
    source: str,
    external_id: str | None = None,
    content_hash: str | None = None,
) -> str:
    """Generate a deterministic content ID.

    Creates a stable ID based on tenant, source, and either
    external ID or content hash.

    Args:
        tenant_id: Tenant identifier.
        source: Source system.
        external_id: ID in source system (preferred).
        content_hash: Hash of content (fallback).

    Returns:
        Deterministic content ID.
    """
    if external_id:
        key = f"{tenant_id}:{source}:{external_id}"
    elif content_hash:
        key = f"{tenant_id}:{source}:hash:{content_hash}"
    else:
        raise ValueError("Either external_id or content_hash required")

    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
