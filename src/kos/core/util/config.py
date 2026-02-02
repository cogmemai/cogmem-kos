"""Configuration utilities."""

from functools import lru_cache
from typing import Any

from pydantic import BaseModel


def get_env_or_default(key: str, default: Any = None) -> Any:
    """Get environment variable or return default."""
    import os
    return os.environ.get(key, default)


def load_dotenv_if_exists(path: str = ".env") -> bool:
    """Load .env file if it exists."""
    try:
        from dotenv import load_dotenv
        return load_dotenv(path)
    except ImportError:
        return False
