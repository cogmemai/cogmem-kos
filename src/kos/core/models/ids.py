"""Core ID types and source enumeration."""

from enum import Enum
from typing import NewType

KosId = NewType("KosId", str)
TenantId = NewType("TenantId", str)
UserId = NewType("UserId", str)


class Source(str, Enum):
    """Source types for items."""

    FILES = "files"
    CHAT = "chat"
    GMAIL = "gmail"
    NOTION = "notion"
    SLACK = "slack"
    CONFLUENCE = "confluence"
    JIRA = "jira"
    GITHUB = "github"
    WEB = "web"
    API = "api"
    OTHER = "other"
