#!/usr/bin/env python
"""MCP 服务启动入口（不依赖安装，直接 `python run.py` 即可）。

    python run.py                # stdio，给 MCP 客户端用
    python run.py -t sse -p 8000 # SSE / HTTP，给局域网或其他语言用
"""

from __future__ import annotations

import sys
from pathlib import Path

# 兜底：即使没有 uv sync 安装成包，也能从 src/ 导入
_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from memobird_mcp.server import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
