#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""四科共享 MCP JSON-RPC 路由器（meihua / xiaoliuren / zeji / ming）。

薄层：只把各科已有四段脚本（chart → analyze → narrate → render）挂到
JSON-RPC 2.0 over stdio，**不写任何新的推演/起课/断语逻辑**。

传输协议：JSON-RPC 2.0 over stdio（每行一个请求，每行一个响应）。

方法（每科一套，`<disc>` ∈ meihua | xiaoliuren | zeji | ming）：
  - `<disc>.chart`    params → chart JSON
  - `<disc>.analyze`  params → analyze JSON（params 可直接给 chart，或给起盘参数）
  - `<disc>.narrate`  params → {text, ...}（复用 narrate 段，不另写推演）
  - `<disc>.render`   params → {content, format}（md；html 视该科 render 是否支持）
  - `list_methods`    列出全部方法（另提供 `<disc>.list_methods`）

入口：
  python tools/mcp_router.py --discipline meihua            # 单科 stdio 服务
  python tools/mcp_router.py --all                          # 四科同一进程
  python tools/mcp_router.py --discipline meihua --list-methods
  python tools/mcp_router.py --discipline meihua --test-narrate

各科亦可经薄入口调用：
  python disciplines/meihua/scripts/mcp_server.py --help
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

# =============================================================================
# 路径与学科注册表
# =============================================================================

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
DISC_ROOT = ROOT / "disciplines"

for _p in (str(CORE), str(ROOT / "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from yishu_core.runtime import force_utf8_stdio as _force_utf8_stdio
except Exception:  # pragma: no cover - core 缺失时仍允许 --help
    def _force_utf8_stdio() -> None:  # type: ignore[misc]
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass


# 各科四段模块的加载顺序（依赖靠前）。ming 额外有 pattern.py。
_STAGE_ORDER: dict[str, tuple[str, ...]] = {
    "meihua": ("chart", "analyze", "narrate", "render"),
    "xiaoliuren": ("chart", "analyze", "narrate", "render"),
    "zeji": ("chart", "analyze", "narrate", "render"),
    "ming": ("chart", "pattern", "analyze", "narrate", "render"),
}

DISCIPLINES: dict[str, str] = {
    "meihua": "梅花易数",
    "xiaoliuren": "小六壬",
    "zeji": "择吉",
    "ming": "命（四柱）",
}

# 冒烟/演示用缺省起盘参数（与各科金标准自检同源，可复现）。
_DEMO_PARAMS: dict[str, dict] = {
    "meihua": {
        "way": "numbers",
        "year_num": 5, "month": 12, "day": 17, "hour_num": 9,
        "month_branch": "子",
        "question": "明晚会有女子来折花吗？",
    },
    "xiaoliuren": {
        "way": "month_day_hour",
        "month": 8, "day": 15, "hour_ordinal": 9,
        "question": "去朋友家，测有人否",
        "topic": "行人",
    },
    "zeji": {
        "date": "2026-09-25",
        "question": "结婚嫁娶吉否",
        "activity": "嫁娶",
    },
    "ming": {
        "datetime": "1990-05-20 10:30",
        "gender": "男",
        "question": "命局排盘",
    },
}

# JSON-RPC 2.0 错误码
ERROR_PARSE_ERROR = -32700
ERROR_INVALID_REQUEST = -32600
ERROR_METHOD_NOT_FOUND = -32601
ERROR_INVALID_PARAMS = -32602
ERROR_INTERNAL_ERROR = -32603


# =============================================================================
# 学科模块加载（同名 chart/analyze/… 按科缓存，切科时重挂 sys.modules）
# =============================================================================

class DisciplineLoader:
    """按科加载四段脚本；同进程可切换多科，互不污染。"""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self._active: Optional[str] = None

    def _script_dir(self, disc: str) -> Path:
        d = DISC_ROOT / disc / "scripts"
        if not d.is_dir():
            raise ValueError(f"未知学科或缺少 scripts 目录: {disc}")
        return d

    def activate(self, disc: str) -> dict[str, Any]:
        if disc not in _STAGE_ORDER:
            raise ValueError(
                f"未知学科: {disc}（可选 {', '.join(sorted(_STAGE_ORDER))}）"
            )
        if self._active == disc and disc in self._cache:
            return self._cache[disc]

        stages = _STAGE_ORDER[disc]
        # 先卸掉旧科同名模块，避免 from chart import … 拿到别科的 chart
        for name in stages:
            sys.modules.pop(name, None)
        for name in ("chart", "analyze", "narrate", "render", "pattern"):
            sys.modules.pop(name, None)

        scripts = self._script_dir(disc)
        # 把本 scripts 目录顶到 sys.path 最前；去掉其它学科的 scripts
        sys.path[:] = [
            p for p in sys.path
            if not (p.endswith("scripts") and "disciplines" in p)
        ]
        sys.path.insert(0, str(scripts))
        if str(CORE) not in sys.path:
            sys.path.insert(0, str(CORE))

        if disc in self._cache:
            mods = self._cache[disc]
            for name, mod in mods.items():
                sys.modules[name] = mod
        else:
            mods = {}
            for name in stages:
                mods[name] = importlib.import_module(name)
            self._cache[disc] = mods

        self._active = disc
        return mods


_LOADER = DisciplineLoader()


def _mods(disc: str) -> dict[str, Any]:
    return _LOADER.activate(disc)


# =============================================================================
# 参数 → 四段调用（纯装配，不写推演）
# =============================================================================

def _norm_params(params: Any) -> dict:
    if params is None:
        return {}
    if isinstance(params, dict):
        return dict(params)
    raise ValueError("params 应为 JSON 对象")


def _call_chart(disc: str, params: dict) -> dict:
    mods = _mods(disc)
    chart_fn = mods["chart"].chart
    if disc == "ming":
        # ming.chart(question, *, datetime_str, gender, longitude) 位置参数风格
        return chart_fn(
            params.get("question") or "命局排盘",
            datetime_str=params.get("datetime") or params.get("datetime_str"),
            gender=params.get("gender"),
            longitude=params.get("longitude"),
        )
    # 其余三科：chart(params: dict)
    p = dict(params)
    # 便捷别名：numbers 列表 → meihua 的 year_num/… 四数（way 缺省时）
    if disc == "meihua" and isinstance(p.get("numbers"), (list, tuple)):
        nums = list(p.pop("numbers"))
        if len(nums) >= 4 and "year_num" not in p:
            p.setdefault("way", "numbers")
            p["year_num"] = int(nums[0])
            p["month"] = int(nums[1])
            p["day"] = int(nums[2])
            p["hour_num"] = int(nums[3])
    out = chart_fn(p)
    # 小六壬 CLI 会补 palace_name；MCP chart 对齐 CLI 输出
    if disc == "xiaoliuren" and isinstance(out, dict) and "palace" in out:
        try:
            out.setdefault("palace_name", mods["chart"].palace_name(out["palace"]))
        except Exception:
            pass
    return out


def _chart_or_input(disc: str, params: dict) -> dict:
    """params.chart 已给 chart JSON 则直用，否则走 chart 段。"""
    pre = params.get("chart")
    if isinstance(pre, dict) and pre:
        return pre
    return _call_chart(disc, params)


def _call_analyze(disc: str, params: dict) -> dict:
    mods = _mods(disc)
    return mods["analyze"].analyze(_chart_or_input(disc, params))


# =============================================================================
# 各科方法实现
# =============================================================================

def _make_chart_handler(disc: str) -> Callable[[dict], dict]:
    def handler(params: dict) -> dict:
        return _call_chart(disc, _norm_params(params))
    return handler


def _make_analyze_handler(disc: str) -> Callable[[dict], dict]:
    def handler(params: dict) -> dict:
        return _call_analyze(disc, _norm_params(params))
    return handler


def _make_narrate_handler(disc: str) -> Callable[[dict], dict]:
    def handler(params: dict) -> dict:
        p = _norm_params(params)
        a = _call_analyze(disc, p)
        text = _mods(disc)["narrate"].narrate(a)
        out: dict[str, Any] = {"text": text}
        if isinstance(a, dict):
            if "conclusion" in a:
                out["conclusion"] = a.get("conclusion")
            if "chart_summary" in a:
                out["chart_summary"] = a.get("chart_summary")
            if "question" in a:
                out["question"] = a.get("question")
        return out
    return handler


def _make_render_handler(disc: str) -> Callable[[dict], dict]:
    def handler(params: dict) -> dict:
        p = _norm_params(params)
        fmt = p.get("format") or p.get("fmt") or "md"
        if fmt not in ("md", "html"):
            raise ValueError(f"format 仅支持 md|html，收到: {fmt}")
        mods = _mods(disc)
        render_fn = mods["render"].render
        a = _call_analyze(disc, p)
        # 各科 render(analyze_out, out_path=None) -> str；ming 为 render(analyze_out)
        if fmt == "html":
            # 仅当该科 render 真正支持 html 才走；现四科均只出 Markdown
            raise ValueError(
                f"{disc} 的 render 段目前仅支持 format=md，不支持 html"
            )
        content = render_fn(a)
        return {"content": content, "format": "md"}
    return handler


def _method_list_methods(params: dict = None) -> dict:
    return {"methods": dict(METHOD_DESCRIPTIONS)}


def _make_list_methods(disc: str) -> Callable[[dict], dict]:
    def handler(params: dict = None) -> dict:
        prefix = f"{disc}."
        return {
            "methods": {
                k: v for k, v in METHOD_DESCRIPTIONS.items()
                if k.startswith(prefix) or k == "list_methods"
            },
            "discipline": disc,
            "discipline_label": DISCIPLINES.get(disc, disc),
        }
    return handler


# =============================================================================
# 方法路由表（进程内可挂单科或四科；由 build_methods 决定挂载范围）
# =============================================================================

METHOD_DESCRIPTIONS: dict[str, str] = {
    "list_methods": "（内建）列出所有可用方法的帮助信息",
}

for _disc, _label in DISCIPLINES.items():
    METHOD_DESCRIPTIONS[f"{_disc}.chart"] = (
        f"{_label}·chart 段：起盘/起课，返回 chart JSON（纯机械）"
    )
    METHOD_DESCRIPTIONS[f"{_disc}.analyze"] = (
        f"{_label}·analyze 段：chart → 因子与判据 JSON（纯机械，断语取 data/verdicts.json）"
    )
    METHOD_DESCRIPTIONS[f"{_disc}.narrate"] = (
        f"{_label}·narrate 段：唯一交付正文（复用 narrate，不另写推演）"
    )
    METHOD_DESCRIPTIONS[f"{_disc}.render"] = (
        f"{_label}·render 段：报告导出 md（复用 render 段单一出口）"
    )
    METHOD_DESCRIPTIONS[f"{_disc}.list_methods"] = (
        f"{_label}·列出本学科可用方法"
    )


def build_methods(disciplines: Optional[list[str]] = None) -> dict[str, Callable]:
    """构造方法表。disciplines 为 None 时挂载全部四科。"""
    if disciplines is None:
        discs = list(DISCIPLINES)
    else:
        discs = []
        for d in disciplines:
            if d not in DISCIPLINES:
                raise ValueError(
                    f"未知学科: {d}（可选 {', '.join(sorted(DISCIPLINES))}）"
                )
            discs.append(d)

    methods: dict[str, Callable] = {"list_methods": _method_list_methods}
    for disc in discs:
        methods[f"{disc}.chart"] = _make_chart_handler(disc)
        methods[f"{disc}.analyze"] = _make_analyze_handler(disc)
        methods[f"{disc}.narrate"] = _make_narrate_handler(disc)
        methods[f"{disc}.render"] = _make_render_handler(disc)
        methods[f"{disc}.list_methods"] = _make_list_methods(disc)
    return methods


# =============================================================================
# JSON-RPC 2.0
# =============================================================================

class RpcServer:
    def __init__(self, methods: dict[str, Callable]) -> None:
        self.methods = methods

    def handle_request(self, request_data: dict) -> Optional[dict]:
        if request_data.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request_data.get("id"),
                "error": {
                    "code": ERROR_INVALID_REQUEST,
                    "message": "Invalid JSON-RPC version (expected '2.0')",
                },
            }

        req_id = request_data.get("id")
        method_name = request_data.get("method", "")
        params = request_data.get("params", {})

        if not method_name:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": ERROR_INVALID_REQUEST,
                    "message": "Missing 'method' field",
                },
            }

        handler = self.methods.get(method_name)
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": ERROR_METHOD_NOT_FOUND,
                    "message": f"Method not found: {method_name}",
                    "data": {"available_methods": list(self.methods.keys())},
                },
            }

        try:
            result = handler(params)
        except ValueError as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": ERROR_INVALID_PARAMS, "message": str(e)},
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": ERROR_INTERNAL_ERROR,
                    "message": f"Internal error: {type(e).__name__}: {e}",
                },
            }

        if req_id is None:
            return None
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def run_stdio(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": ERROR_PARSE_ERROR,
                        "message": f"JSON parse error: {e}",
                    },
                }
                sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
                sys.stdout.flush()
                continue
            response = self.handle_request(request)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()


# =============================================================================
# CLI
# =============================================================================

def _build_parser(default_disc: Optional[str] = None) -> argparse.ArgumentParser:
    epilog = """
传输协议: JSON-RPC 2.0 over stdio
  每行一个 JSON 请求，响应同样为一行 JSON。

方法:
  <disc>.chart / <disc>.analyze / <disc>.narrate / <disc>.render
  list_methods
  （<disc> ∈ meihua | xiaoliuren | zeji | ming）

示例:
  python tools/mcp_router.py --discipline meihua
  python tools/mcp_router.py --all
  python tools/mcp_router.py --discipline zeji --list-methods
  python tools/mcp_router.py --discipline ming --test-narrate

JSON-RPC 请求示例:
  {"jsonrpc":"2.0","id":1,"method":"meihua.narrate","params":{"way":"numbers","year_num":5,"month":12,"day":17,"hour_num":9,"question":"测花"}}
  {"jsonrpc":"2.0","id":2,"method":"zeji.chart","params":{"date":"2026-09-25","activity":"嫁娶"}}
  {"jsonrpc":"2.0","id":3,"method":"xiaoliuren.render","params":{"way":"month_day_hour","month":8,"day":15,"hour_ordinal":9}}
  {"jsonrpc":"2.0","id":4,"method":"list_methods","params":{}}
"""
    parser = argparse.ArgumentParser(
        description="四科 MCP JSON-RPC 服务器（meihua/xiaoliuren/zeji/ming）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    parser.add_argument(
        "--discipline",
        choices=sorted(DISCIPLINES),
        default=default_disc,
        help="只挂载该学科的方法（缺省且未给 --all 时报错）",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="同一进程挂载全部四科方法",
    )
    parser.add_argument(
        "--list-methods",
        action="store_true",
        help="列出可用 JSON-RPC 方法后退出",
    )
    parser.add_argument(
        "--list-disciplines",
        action="store_true",
        help="列出支持的学科后退出",
    )
    parser.add_argument(
        "--test-chart",
        action="store_true",
        help="直接跑一次 chart 段（不启动服务）",
    )
    parser.add_argument(
        "--test-analyze",
        action="store_true",
        help="直接跑一次 analyze 段（不启动服务）",
    )
    parser.add_argument(
        "--test-narrate",
        action="store_true",
        help="直接跑一次 narrate 段（不启动服务）",
    )
    parser.add_argument(
        "--test-render",
        action="store_true",
        help="直接跑一次 render 段（不启动服务）",
    )
    parser.add_argument(
        "--params",
        type=str,
        default=None,
        help='测试参数 JSON（缺省用该科演示盘），如 \'{"question":"测投资"}\'',
    )
    parser.add_argument(
        "--question",
        type=str,
        default=None,
        help="测试用求测问题（覆盖 --params 里的 question）",
    )
    parser.add_argument(
        "--format",
        choices=["md", "html"],
        default="md",
        help="--test-render 的导出格式（默认 md）",
    )
    return parser


def _resolve_discs(args: argparse.Namespace, parser: argparse.ArgumentParser) -> list[str]:
    if args.all:
        return list(DISCIPLINES)
    if args.discipline:
        return [args.discipline]
    parser.error("必须指定 --discipline {meihua,xiaoliuren,zeji,ming} 或 --all")
    return []  # unreachable


def _demo_params_for(disc: str, args: argparse.Namespace) -> dict:
    p = dict(_DEMO_PARAMS[disc])
    if args.params:
        try:
            user = json.loads(args.params)
        except json.JSONDecodeError as e:
            raise SystemExit(f"--params 不是合法 JSON: {e}")
        if not isinstance(user, dict):
            raise SystemExit("--params 必须是 JSON 对象")
        p.update(user)
    if args.question is not None:
        p["question"] = args.question
    return p


def run_cli(
    argv: Optional[list[str]] = None,
    default_disc: Optional[str] = None,
    lock_disc: bool = False,
) -> int:
    """CLI 入口。lock_disc=True 时（各科薄入口）忽略用户改学科。"""
    parser = _build_parser(default_disc=default_disc)
    args = parser.parse_args(argv)

    if args.list_disciplines:
        for k, v in DISCIPLINES.items():
            print(f"  {k}: {v}")
        return 0

    if lock_disc and default_disc:
        args.discipline = default_disc
        args.all = False

    discs = _resolve_discs(args, parser)
    methods = build_methods(discs)

    if args.list_methods:
        print("可用方法:")
        for name, desc in sorted(METHOD_DESCRIPTIONS.items()):
            if name == "list_methods" or any(
                name.startswith(f"{d}.") for d in discs
            ):
                print(f"  {name}: {desc}")
        print("\nJSON-RPC 2.0 over stdio 协议。")
        return 0

    test_mode = args.test_chart or args.test_analyze or args.test_narrate or args.test_render
    if test_mode:
        disc = discs[0]
        params = _demo_params_for(disc, args)
        try:
            if args.test_chart:
                result = methods[f"{disc}.chart"](params)
            elif args.test_analyze:
                result = methods[f"{disc}.analyze"](params)
            elif args.test_narrate:
                result = methods[f"{disc}.narrate"](params)
            else:
                params = dict(params)
                params["format"] = args.format
                result = methods[f"{disc}.render"](params)
        except Exception as e:
            print(f"测试调用失败: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
        if isinstance(result, dict) and "content" in result and "format" in result:
            print(result["content"])
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0

    # 默认：stdio 服务
    RpcServer(methods).run_stdio()
    return 0


def main_for_discipline(disc: str) -> int:
    """各科 scripts/mcp_server.py 薄入口用：锁定学科。"""
    if disc not in DISCIPLINES:
        print(f"未知学科: {disc}", file=sys.stderr)
        return 2
    return run_cli(default_disc=disc, lock_disc=True)


def main(argv: Optional[list[str]] = None) -> int:
    _force_utf8_stdio()
    return run_cli(argv)


if __name__ == "__main__":
    raise SystemExit(main())
