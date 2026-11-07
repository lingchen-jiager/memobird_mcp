"""一行代码出纸的便捷封装。

    import memobird_mcp
    memobird_mcp.text("你好，咕咕机")
    memobird_mcp.image(r"D:\\photo.png")

凭据自动从 .env / 环境变量读取，设备实例按需创建并复用。
"""

from __future__ import annotations

import logging
from typing import Optional, Union

from PIL import Image
from io import BytesIO

from .client import MemobirdDevice, PrintPayloadBuilder
from .config import get_credentials

log = logging.getLogger(__name__)

_device: Optional[MemobirdDevice] = None


def device(refresh: bool = False) -> MemobirdDevice:
    """拿到（并缓存）当前凭据对应的设备实例。"""
    global _device
    if _device is None or refresh:
        ak, device_id = get_credentials()
        _device = MemobirdDevice(ak=ak, device_id=device_id)
    return _device


def text(content: str) -> int:
    """打印纯文本，返回 Content ID。"""
    return device().print_text(content)


def image(source: Union[str, BytesIO, Image.Image]) -> int:
    """打印图片（本地路径 / BytesIO / PIL.Image），返回 Content ID。"""
    return device().print_image(source)


def url(address: str) -> int:
    """打印公网 URL 的内容，返回 Content ID。"""
    return device().print_url(address)


def mixed(*parts: Union[str, Image.Image]) -> int:
    """文字与图片混排成一张小票。str 当文字，其余当图片。"""
    builder = PrintPayloadBuilder()
    for part in parts:
        if isinstance(part, str):
            builder.add_text(part)
        else:
            builder.add_image(part)
    return device().print_payload(builder)


def status(content_id: int) -> bool:
    """查询某个 Content ID 是否已出纸。"""
    return device().check_print_status(content_id)
