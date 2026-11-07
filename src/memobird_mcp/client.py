"""咕咕机开放平台 HTTP 客户端。

三层结构：
  PrintPayloadBuilder  把文字/图片拼成开放平台要的 printcontent 字符串
  MemobirdApiClient    负责真实 HTTP 请求（setuserbind / printpaper / getprintstatus）
  MemobirdDevice       面向使用者的门面：print_text / print_image / print_url
"""

from __future__ import annotations

import base64
import logging
from datetime import datetime
from io import BytesIO
from typing import Any, List, Optional, Tuple, Union

import requests
from PIL import Image, UnidentifiedImageError

from .config import API_BASE_URL, IMAGE_MAX_WIDTH, REQUEST_TIMEOUT

log = logging.getLogger(__name__)

__all__ = [
    "MemobirdError",
    "ApiError",
    "NetworkError",
    "ContentError",
    "PrintPayloadBuilder",
    "MemobirdApiClient",
    "MemobirdDevice",
]


def _now() -> str:
    """开放平台要求的 timestamp 格式。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class MemobirdError(Exception):
    """所有咕咕机相关异常的基类。"""


class ApiError(MemobirdError):
    """开放平台返回了业务错误（showapi_res_code != 1）。"""

    def __init__(self, res_code: int, res_error: str, status_code: Optional[int] = None):
        self.res_code = res_code
        self.res_error = res_error
        self.status_code = status_code
        super().__init__(
            f"API 错误（HTTP {status_code}，业务码 {res_code}）：{res_error}"
        )


class NetworkError(MemobirdError):
    """网络层错误：超时、连接失败、响应不是 JSON 等。"""


class ContentError(MemobirdError):
    """待打印内容有问题：文件不存在、图片无法识别等。"""


def _check_api_response(resp: requests.Response) -> dict[str, Any]:
    """统一校验响应，成功时返回 JSON。"""
    try:
        resp.raise_for_status()
        data = resp.json()
        if data.get("showapi_res_code") != 1:
            raise ApiError(
                res_code=data.get("showapi_res_code", -1),
                res_error=data.get("showapi_res_error", "未知错误"),
                status_code=resp.status_code,
            )
        return data
    except requests.exceptions.HTTPError as exc:
        body = ""
        try:
            body = f" 响应片段：{resp.text[:200]}"
        except Exception:  # pragma: no cover
            pass
        raise NetworkError(f"HTTP 错误：{exc}。{body}") from exc
    except requests.exceptions.JSONDecodeError as exc:
        raise ApiError(
            res_code=-2,
            res_error=f"响应不是合法 JSON：{exc}",
            status_code=resp.status_code,
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise NetworkError(f"请求失败：{exc}") from exc


class PrintPayloadBuilder:
    """构建 printcontent：多段内容用 | 分隔，每段是 <类型>:<base64>。"""

    def __init__(self) -> None:
        self._parts: List[Tuple[str, Union[str, bytes]]] = []

    def add_text(self, text: str) -> "PrintPayloadBuilder":
        if not isinstance(text, str):
            raise TypeError("文本内容必须是 str")
        self._parts.append(("T", text))
        return self

    def add_image(
        self, image_source: Union[str, BytesIO, Image.Image]
    ) -> "PrintPayloadBuilder":
        """接受本地路径、BytesIO 或 PIL.Image；内部统一转成 384px 宽的 1 位 BMP。"""
        try:
            image = (
                image_source
                if isinstance(image_source, Image.Image)
                else Image.open(image_source)
            )
            if image.mode != "RGB":
                image = image.convert("RGB")

            width, height = image.size
            if width > IMAGE_MAX_WIDTH:
                new_height = max(1, int(height * IMAGE_MAX_WIDTH / width))
                log.info("图片缩放：%sx%s -> %sx%s", width, height, IMAGE_MAX_WIDTH, new_height)
                image = image.resize(
                    (IMAGE_MAX_WIDTH, new_height), Image.Resampling.LANCZOS
                )

            image = image.convert("1")
            with BytesIO() as buf:
                image.save(buf, "BMP")
                self._parts.append(("P", buf.getvalue()))
        except FileNotFoundError as exc:
            raise ContentError(f"图片文件不存在：{image_source}") from exc
        except UnidentifiedImageError as exc:
            raise ContentError(f"无法识别的图片格式：{image_source}") from exc
        except MemobirdError:
            raise
        except Exception as exc:
            raise ContentError(f"图片处理失败：{exc}") from exc
        return self

    def build(self) -> str:
        encoded: List[str] = []
        total = len(self._parts)
        for index, (kind, data) in enumerate(self._parts):
            if kind == "T":
                text = str(data)
                if index < total - 1 and not text.endswith("\n"):
                    text += "\n"
                # 开放平台要求 GBK；无法编码的字符（emoji、部分生僻字）会被静默丢弃
                payload = base64.b64encode(text.encode("GBK", errors="ignore")).decode("ascii")
                encoded.append(f"T:{payload}")
            else:
                payload = base64.b64encode(data).decode("ascii")  # type: ignore[arg-type]
                encoded.append(f"P:{payload}")
        return "|".join(encoded)


class MemobirdApiClient:
    """开放平台 HTTP 客户端。"""

    def __init__(self, ak: str, session: Optional[requests.Session] = None) -> None:
        if not ak:
            raise ValueError("AK 不能为空")
        self._ak = ak
        self._session = session or requests.Session()
        self._headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        timeout: int = REQUEST_TIMEOUT,
    ) -> dict[str, Any]:
        url = API_BASE_URL + path
        log.debug("%s %s params=%s json=%s", method, url, params, json_data)
        try:
            resp = self._session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=self._headers,
                timeout=timeout,
            )
            return _check_api_response(resp)
        except MemobirdError:
            raise
        except Exception as exc:  # pragma: no cover
            raise NetworkError(f"请求异常：{exc}") from exc

    def get_user_id(self, device_id: str, user_identifying: str = "") -> str:
        """绑定设备并取回 userID（每次启动都要调一次，幂等）。"""
        data = self._request(
            "GET",
            "/setuserbind",
            params={
                "ak": self._ak,
                "timestamp": _now(),
                "memobirdID": device_id,
                "useridentifying": user_identifying,
            },
        )
        user_id = data.get("showapi_userid")
        if not user_id:
            raise ApiError(data.get("showapi_res_code", -1), "响应中缺少 showapi_userid")
        return str(user_id)

    def print_content(self, device_id: str, user_id: str, payload: "PrintPayloadBuilder") -> int:
        content = payload.build()
        if not content:
            raise ContentError("内容为空，无法打印")
        data = self._request(
            "POST",
            "/printpaper",
            json_data={
                "ak": self._ak,
                "timestamp": _now(),
                "printcontent": content,
                "memobirdID": device_id,
                "userID": user_id,
            },
            timeout=20,
        )
        content_id = data.get("printcontentid")
        if content_id is None:
            raise ApiError(data.get("showapi_res_code", -1), "响应中缺少 printcontentid")
        return int(content_id)

    def print_url(self, device_id: str, user_id: str, url: str) -> int:
        data = self._request(
            "POST",
            "/printpaperFromUrl",
            json_data={
                "ak": self._ak,
                "timestamp": _now(),
                "printUrl": url,
                "memobirdID": device_id,
                "userID": user_id,
            },
            timeout=30,
        )
        content_id = data.get("printcontentid")
        if content_id is None:
            raise ApiError(data.get("showapi_res_code", -1), "响应中缺少 printcontentid")
        return int(content_id)

    def check_print_status(self, content_id: int) -> bool:
        data = self._request(
            "GET",
            "/getprintstatus",
            params={"ak": self._ak, "timestamp": _now(), "printcontentid": content_id},
        )
        return data.get("printflag") == 1


class MemobirdDevice:
    """面向使用者的门面，一个实例对应一台打印机。"""

    def __init__(self, ak: str, device_id: str, user_identifying: str = "") -> None:
        self._client = MemobirdApiClient(ak)
        self.device_id = device_id
        self.user_id = self._client.get_user_id(device_id, user_identifying)
        log.info("设备绑定成功：device=%s user=%s", device_id, self.user_id)

    def print_text(self, text: str) -> int:
        return self._client.print_content(
            self.device_id, self.user_id, PrintPayloadBuilder().add_text(text)
        )

    def print_image(self, image_source: Union[str, BytesIO, Image.Image]) -> int:
        return self._client.print_content(
            self.device_id, self.user_id, PrintPayloadBuilder().add_image(image_source)
        )

    def print_payload(self, payload: PrintPayloadBuilder) -> int:
        return self._client.print_content(self.device_id, self.user_id, payload)

    def print_url(self, url: str) -> int:
        return self._client.print_url(self.device_id, self.user_id, url)

    def check_print_status(self, content_id: int) -> bool:
        return self._client.check_print_status(content_id)
