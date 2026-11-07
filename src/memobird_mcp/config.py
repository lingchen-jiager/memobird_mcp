"""配置与凭据读取。

设计原则：本模块（以及整个代码库）不出现任何真实密钥。
凭据只从环境变量读取；如果环境变量缺失，再尝试项目根目录的 .env。
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

try:  # python-dotenv 是必需依赖，缺失时也不该让服务起不来
    from dotenv import load_dotenv

    # 依次尝试：项目根目录的 .env、当前工作目录的 .env
    # （uvx 从 Git 安装时没有项目根，凭据走客户端配置里的 env，不依赖这个文件）
    for candidate in (PROJECT_ROOT / ".env", Path.cwd() / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)
except ImportError:  # pragma: no cover
    pass

# --- 环境变量名 ---
ENV_AK = "MEMOBIRD_AK"
ENV_DEVICE_ID = "MEMOBIRD_DEVICE_ID"

# --- 服务参数 ---
SERVER_NAME = "Memobird Printer Server"
DEFAULT_SSE_PORT = 8000
DEFAULT_SSE_HOST = "127.0.0.1"

# --- 开放平台参数 ---
API_BASE_URL = os.environ.get("MEMOBIRD_API_BASE_URL", "http://open.memobird.cn/home")
REQUEST_TIMEOUT = 15
IMAGE_MAX_WIDTH = 384  # 咕咕机打印头宽度（像素）

# --- 日志 ---
LOG_LEVEL = os.environ.get("MEMOBIRD_LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


class MissingCredentialsError(RuntimeError):
    """凭据缺失时抛出，提示用户去配置 .env。"""


def get_credentials() -> tuple[str, str]:
    """返回 (ak, device_id)。缺失则抛出带指引的异常。"""
    ak = (os.environ.get(ENV_AK) or "").strip()
    device_id = (os.environ.get(ENV_DEVICE_ID) or "").strip()

    missing = [name for name, val in ((ENV_AK, ak), (ENV_DEVICE_ID, device_id)) if not val]
    if missing:
        raise MissingCredentialsError(
            "缺少 "
            + " 和 ".join(missing)
            + "。二选一配置：\n"
            "  1) 本地开发：把 .env.example 复制为 .env 并填入凭据（"
            + str(PROJECT_ROOT)
            + "）\n"
            "  2) MCP 客户端：在你的客户端配置 mcpServers 里加 env 字段，写入 "
            + ENV_AK
            + " 与 "
            + ENV_DEVICE_ID
        )
    return ak, device_id
