"""memobird-mcp：咕咕机热敏打印机的 MCP 服务与 Python 客户端。"""

from __future__ import annotations

from . import quick
from .client import (
    ApiError,
    ContentError,
    MemobirdDevice,
    MemobirdError,
    NetworkError,
    PrintPayloadBuilder,
)
from .config import get_credentials
from .quick import device, image, mixed, status, text, url

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "quick",
    "device",
    "text",
    "image",
    "url",
    "mixed",
    "status",
    "get_credentials",
    "MemobirdDevice",
    "PrintPayloadBuilder",
    "MemobirdError",
    "ApiError",
    "NetworkError",
    "ContentError",
]
