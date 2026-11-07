"""把打印能力注册成 MCP 工具。"""

from __future__ import annotations

import logging
from typing import Optional

from fastmcp import FastMCP

from .client import MemobirdDevice, MemobirdError, PrintPayloadBuilder
from .config import get_credentials

log = logging.getLogger(__name__)

_state: dict[str, Optional[MemobirdDevice]] = {"device": None}


def _device() -> MemobirdDevice:
    """惰性创建设备：MCP 握手阶段不碰网络，第一次调工具才绑定设备。"""
    if _state["device"] is None:
        ak, device_id = get_credentials()
        _state["device"] = MemobirdDevice(ak=ak, device_id=device_id)
    return _state["device"]  # type: ignore[return-value]


def register_tools(mcp: FastMCP) -> None:
    """把 5 个工具挂到给定的 FastMCP 实例上。"""

    @mcp.tool
    def print_text(text: str) -> str:
        """把一段纯文本打印到咕咕机。

        文本按 GBK 编码发送，emoji 和部分生僻字会被静默丢弃。

        :param text: 要打印的文本内容
        """
        try:
            content_id = _device().print_text(text)
            return f"已发送到打印机，Content ID: {content_id}"
        except MemobirdError as exc:
            return f"打印失败：{exc}"

    @mcp.tool
    def print_image(image_path: str) -> str:
        """把一张图片打印到咕咕机。

        图片会等比缩放到 384px 宽并转成黑白，细节多的图建议先用高对比度版本。

        :param image_path: 本地图片绝对路径，或 data:image/png;base64,... 形式的字符串
        """
        try:
            content_id = _device().print_image(image_path)
            return f"已发送到打印机，Content ID: {content_id}"
        except MemobirdError as exc:
            return f"打印失败：{exc}"

    @mcp.tool
    def print_url(url: str) -> str:
        """打印某个网页的内容（由咕咕机服务端抓取渲染）。

        URL 必须公网可访问，内网地址、需要登录的页面打不出来。

        :param url: 目标网页地址
        """
        try:
            content_id = _device().print_url(url)
            return f"已发送到打印机，Content ID: {content_id}"
        except MemobirdError as exc:
            return f"打印失败：{exc}"

    @mcp.tool
    def print_mixed(text: str, image_path: str = "") -> str:
        """把文字和图片混排打印在同一张小票上。

        :param text: 文字内容
        :param image_path: 可选的图片绝对路径，留空则只打文字
        """
        try:
            builder = PrintPayloadBuilder().add_text(text)
            if image_path:
                builder.add_image(image_path)
            content_id = _device().print_payload(builder)
            return f"已发送到打印机，Content ID: {content_id}"
        except MemobirdError as exc:
            return f"打印失败：{exc}"

    @mcp.tool
    def print_status(content_id: int) -> str:
        """查询一张小票是否已经出纸。

        :param content_id: 打印时返回的 Content ID
        """
        try:
            done = _device().check_print_status(content_id)
            return f"Content ID {content_id}：{'已出纸' if done else '尚未出纸或排队中'}"
        except MemobirdError as exc:
            return f"查询失败：{exc}"

    log.info("已注册工具：print_text / print_image / print_url / print_mixed / print_status")
