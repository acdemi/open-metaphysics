#!/usr/bin/env python3
"""静态文件服务器：为 OpenMetaphysics 前端 MVP 提供本地演示入口。

前端是零构建的单页应用（原生 ES modules），因此只需要一个静态服务器，
不需要 Node/npm，也不引入任何新的运行时依赖。

用法（仓库根目录执行）：

    uv run python frontend/serve.py            # http://127.0.0.1:5173
    uv run python frontend/serve.py --port 8080

注意：浏览器会跨域访问后端 http://127.0.0.1:8000，因此启动后端时必须允许
本页面的来源（仓库既有配置项 OM_CORS_ORIGINS）：

    PowerShell:  $env:OM_CORS_ORIGINS='http://127.0.0.1:5173'; uv run openmetaphysics
    bash:        OM_CORS_ORIGINS=http://127.0.0.1:5173 uv run openmetaphysics
"""

from __future__ import annotations

import argparse
import functools
import http.server
import os
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """静态演示用：禁用缓存，避免修改前端后看到旧文件。"""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        sys.stderr.write(f"[frontend] {self.address_string()} - {format % args}\n")


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((host, port))
        except OSError:
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve the OpenMetaphysics frontend MVP.")
    parser.add_argument("--host", default="127.0.0.1", help="bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5173, help="bind port (default: 5173)")
    args = parser.parse_args()

    os.chdir(ROOT)
    handler = functools.partial(NoCacheHandler, directory=str(ROOT))

    if not port_available(args.host, args.port):
        print(f"[frontend] port {args.port} is already in use; try --port <other>", file=sys.stderr)
        return 1

    url = f"http://{args.host}:{args.port}/"
    print("OpenMetaphysics 前端 MVP")
    print(f"  页面地址: {url}")
    print("  后端要求: 先启动 API，并允许本页面来源跨域：")
    print(
        f"    PowerShell:  $env:OM_CORS_ORIGINS='http://{args.host}:{args.port}'; uv run openmetaphysics"
    )
    print(f"    bash:        OM_CORS_ORIGINS=http://{args.host}:{args.port} uv run openmetaphysics")
    print("  Ctrl+C 退出。")
    print()

    httpd = http.server.ThreadingHTTPServer((args.host, args.port), handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[frontend] stopped")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
