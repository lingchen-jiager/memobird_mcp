"""命令行快速出纸工具。

    uv run memobird text "今天下午三点开会"
    uv run memobird image D:\\photo.png
    uv run memobird url https://example.com
    uv run memobird status 71514704
    uv run memobird whoami          # 只验证凭据，不出纸
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .client import MemobirdDevice, MemobirdError, PrintPayloadBuilder
from .config import LOG_FORMAT, LOG_LEVEL, MissingCredentialsError, get_credentials


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="memobird",
        description="咕咕机快速出纸。凭据读 .env 或环境变量。",
    )
    parser.add_argument("--ak", help="临时覆盖 MEMOBIRD_AK")
    parser.add_argument("--did", help="临时覆盖 MEMOBIRD_DEVICE_ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="打印 DEBUG 日志")

    sub = parser.add_subparsers(dest="command", required=True)

    p_text = sub.add_parser("text", help="打印纯文本")
    p_text.add_argument("content", nargs="+", help="文本内容，多段用空格分隔会自动拼接")

    p_image = sub.add_parser("image", help="打印图片")
    p_image.add_argument("path", help="本地图片路径")

    p_mixed = sub.add_parser("mixed", help="图文混排成一张小票")
    p_mixed.add_argument("content", help="文字内容")
    p_mixed.add_argument("-i", "--image", default="", help="可选的图片路径")

    p_url = sub.add_parser("url", help="打印网页（需公网可访问）")
    p_url.add_argument("address", help="网页地址")

    p_status = sub.add_parser("status", help="查询出纸状态")
    p_status.add_argument("content_id", type=int, help="打印时返回的 Content ID")

    sub.add_parser("whoami", help="校验凭据并显示绑定的 userID，不出纸")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        stream=sys.stderr,
    )

    if args.ak:
        os.environ["MEMOBIRD_AK"] = args.ak
    if args.did:
        os.environ["MEMOBIRD_DEVICE_ID"] = args.did

    try:
        ak, device_id = get_credentials()
        device = MemobirdDevice(ak=ak, device_id=device_id)

        if args.command == "whoami":
            print(f"设备 {device_id} 绑定成功，userID = {device.user_id}")

        elif args.command == "text":
            content_id = device.print_text(" ".join(args.content))
            print(f"已发送，Content ID: {content_id}")

        elif args.command == "image":
            content_id = device.print_image(args.path)
            print(f"已发送，Content ID: {content_id}")

        elif args.command == "mixed":
            builder = PrintPayloadBuilder().add_text(args.content)
            if args.image:
                builder.add_image(args.image)
            content_id = device.print_payload(builder)
            print(f"已发送，Content ID: {content_id}")

        elif args.command == "url":
            content_id = device.print_url(args.address)
            print(f"已发送，Content ID: {content_id}")

        elif args.command == "status":
            done = device.check_print_status(args.content_id)
            print(f"Content ID {args.content_id}：{'已出纸' if done else '尚未出纸或排队中'}")

        return 0

    except MissingCredentialsError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    except MemobirdError as exc:
        print(f"打印失败：{exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
