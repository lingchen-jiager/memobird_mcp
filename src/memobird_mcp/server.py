"""MCP 服务入口：stdio / sse / http 三种传输方式。"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from fastmcp import FastMCP

from .config import DEFAULT_SSE_HOST, DEFAULT_SSE_PORT, LOG_FORMAT, LOG_LEVEL, SERVER_NAME
from .tools import register_tools

log = logging.getLogger(__name__)

INSTRUCTIONS = (
    "咕咕机（Memobird）热敏打印机服务。"
    "可用工具：print_text 打印文本、print_image 打印图片、print_url 打印网页、"
    "print_mixed 图文混排、print_status 查询出纸状态。"
)


def build_server() -> FastMCP:
    """构造 FastMCP 实例并注册工具（不含启动逻辑，方便测试与嵌入）。"""
    mcp = FastMCP(SERVER_NAME, instructions=INSTRUCTIONS)
    register_tools(mcp)
    return mcp


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="memobird-mcp",
        description="咕咕机 MCP 服务。不带参数运行即 stdio 模式，由 MCP 客户端拉起。",
    )
    parser.add_argument(
        "-t",
        "--transport",
        choices=["stdio", "sse", "http"],
        default="stdio",
        help="传输方式：stdio（默认，给桌面客户端）、sse / http（给局域网或其他语言调用）",
    )
    parser.add_argument("-p", "--port", type=int, default=DEFAULT_SSE_PORT, help="监听端口")
    parser.add_argument("--host", default=DEFAULT_SSE_HOST, help="监听地址，局域网访问用 0.0.0.0")
    parser.add_argument("--ak", help="临时覆盖 MEMOBIRD_AK")
    parser.add_argument("--did", help="临时覆盖 MEMOBIRD_DEVICE_ID")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="输出 DEBUG 级日志（走 stderr）"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        stream=sys.stderr,  # 关键：日志绝不能写 stdout，否则会污染 JSON-RPC 流
    )

    # 命令行覆盖优先于 .env
    if args.ak:
        os.environ["MEMOBIRD_AK"] = args.ak
    if args.did:
        os.environ["MEMOBIRD_DEVICE_ID"] = args.did

    mcp = build_server()

    if args.transport == "stdio":
        log.info("以 stdio 方式启动，等待客户端握手…")
        mcp.run(transport="stdio", show_banner=False)
        return 0

    log.info("以 %s 方式启动：http://%s:%s", args.transport, args.host, args.port)
    asyncio.run(
        mcp.run_http_async(
            transport=args.transport,
            host=args.host,
            port=args.port,
            show_banner=False,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
