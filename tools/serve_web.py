# -*- coding: utf-8 -*-
"""本机预览服务器：把仓库当站点跑起来，供浏览器端（Pyodide）取引擎源码。

    python tools/serve_web.py                # 默认 127.0.0.1:8737
    python tools/serve_web.py --port 9000 --open

为什么要它：
  * 纯前端页面必须经 HTTP 访问（`file://` 下取不到引擎文件）；
  * 它直接以**仓库工作区**为站点根，改完源码刷新即生效，不必先跑 build_web；
  * 站点布局与 GitHub Pages 一致（页面在根、引擎镜像在 `engine/…`），
    所以本地看到的就是推上去之后的样子。

路由：
  /                     → web/index.html（未构建 index.html 时用 web/ 下的源文件）
  /web.css /web.js /engine_runtime.py → web/ 下的前端资源
  /manifest.json        → 现算的站点清单（与 tools/build_web.py 同源）
  /engine/<仓库相对路径> → 仓库工作区对应文件（.py/.json/.md/.txt/.css 白名单）

零第三方依赖，只监听本机回环地址。
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))
sys.path.insert(0, str(ROOT / "tools"))

from build_web import build_manifest  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

WEB_DIR = ROOT / "web"
ENGINE_PREFIX = "engine/"
ALLOWED_SUFFIX = {".py", ".json", ".css", ".md", ".txt", ".html", ".js", ".svg"}
MAX_BYTES = 2 * 1024 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "YiServeWeb/1"

    def log_message(self, fmt, *args):  # 安静一点：只记 4xx/5xx
        try:
            code = int(args[1])
        except (IndexError, ValueError):
            code = 200
        if code >= 400:
            sys.stderr.write("  %s %s\n" % (self.address_string(), fmt % args))

    # ── 响应工具 ──────────────────────────────────────────
    def _send(self, body: bytes, ctype: str, code: int = 200) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _text(self, text: str, ctype: str = "text/plain; charset=utf-8", code: int = 200):
        self._send(text.encode("utf-8"), ctype, code)

    def _notfound(self, why: str) -> None:
        self._text("404 未找到：" + why, "text/plain; charset=utf-8", 404)

    # ── 路由 ──────────────────────────────────────────────
    def do_HEAD(self):  # noqa: N802
        self.do_GET()

    def do_GET(self):  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            return self._serve_index()
        if path == "/manifest.json":
            return self._serve_manifest()
        if path.startswith("/" + ENGINE_PREFIX):
            return self._serve_engine(path[len(ENGINE_PREFIX) + 1:])
        if path.startswith("/web/"):
            return self._serve_web_file(path[len("/web/"):])
        # 前端资源（web.css / web.js / engine_runtime.py）在站点根
        return self._serve_web_file(path.lstrip("/"))

    def _serve_index(self) -> None:
        built = ROOT / "site" / "index.html"
        src = WEB_DIR / "index.html"
        target = built if built.is_file() else src
        if not target.is_file():
            return self._notfound("web/index.html")
        self._send(target.read_bytes(), "text/html; charset=utf-8")

    def _serve_web_file(self, name: str) -> None:
        if not name or "/" in name or name.startswith("."):
            return self._notfound(name)
        path = WEB_DIR / name
        if not path.is_file():
            return self._notfound(name)
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix in (".css", ".js", ".py", ".html", ".json", ".md", ".txt"):
            ctype += "; charset=utf-8"
        self._send(path.read_bytes(), ctype)

    def _serve_manifest(self) -> None:
        try:
            manifest = build_manifest(site_base="")
        except Exception as exc:  # pragma: no cover
            return self._text("清单构建失败：" + repr(exc), "text/plain; charset=utf-8", 500)
        self._text(json.dumps(manifest, ensure_ascii=False, indent=2),
                   "application/json; charset=utf-8")

    def _serve_engine(self, rel: str) -> None:
        rel = rel.replace("\\", "/").lstrip("/")
        if not rel or ".." in rel.split("/"):
            return self._notfound(rel)
        path = (ROOT / rel).resolve()
        try:
            path.relative_to(ROOT)
        except ValueError:
            return self._notfound(rel)          # 越出仓库根，拒绝
        if not path.is_file():
            return self._notfound(rel)
        if path.suffix.lower() not in ALLOWED_SUFFIX:
            return self._notfound(rel + "（后缀不在白名单）")
        if path.stat().st_size > MAX_BYTES:
            return self._notfound(rel + "（文件过大）")
        ctype = mimetypes.guess_type(path.name)[0] or "text/plain"
        if path.suffix in (".py", ".json", ".md", ".txt", ".css", ".js", ".html"):
            ctype += "; charset=utf-8"
        self._send(path.read_bytes(), ctype)


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="Yi 纯前端站点 · 本机预览服务器")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址（默认只监听回环）")
    ap.add_argument("--port", type=int, default=8737)
    ap.add_argument("--open", action="store_true", help="启动后用浏览器打开")
    args = ap.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}/"
    print("Yi 纯前端站点已启动：")
    print("  " + url)
    print("  站点根 = 仓库工作区（engine/... 直接映射仓库文件；无需先构建）")
    print("  深链示例：" + url + "?d=liuyao&q=" + "%E5%8D%A0%E6%B1%82%E8%B4%A2" + "&auto=1")
    print("  Ctrl+C 结束")
    if args.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
