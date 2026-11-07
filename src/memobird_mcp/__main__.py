"""支持 `python -m memobird_mcp` 直接启动服务。"""

from .server import main

if __name__ == "__main__":
    raise SystemExit(main())
