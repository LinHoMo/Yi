# -*- coding: utf-8 -*-
"""网页端与本地端**同源验收**：同一请求两边出报告，逐例比对。

  python tools/verify_web_parity.py            # 六科各一例
  python tools/verify_web_parity.py --verbose  # 附两边首段摘要

为什么需要这个脚本：
  网页端（Pyodide / 同进程 runpy）与本地端（子进程）是**同一条四段契约的两个
  执行器**。执行器可以不同，产出必须同源——否则"点开链接看到的报告"与"CI 出的
  报告"会长成两个样子，而没人会发现。本脚本把这件事变成一条命令。

比对口径：
  * Markdown：**逐字节**必须一致（两边都只写学科 render 段产出的文本）。
  * HTML   ：只有页头小字里的「运行环境」标签允许不同（这是有意标注），
             其余逐字节必须一致。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report import normalize_request, report_meta  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CASES = (
    {"discipline": "liuyao", "question": "占本周面试能否通过", "mode": "time",
     "datetime": "2026-09-30 10:30"},
    {"discipline": "liuyao", "question": "占求财", "mode": "manual",
     "datetime": "2026-09-22 23:40", "yao": "7,8,9,7,6,8"},
    {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
    {"discipline": "ziwei", "datetime": "1990-05-20 10:30", "gender": "女"},
    {"discipline": "meihua", "question": "占投资", "datetime": "2026-09-30 10:30"},
    {"discipline": "xiaoliuren", "question": "占出行", "datetime": "2026-09-30 10:30"},
    {"discipline": "zeji", "date": "2026-09-30", "activity": "开市"},
    # 回归：曾经会崩或会静默降级的请求，现在必须与另一侧同源
    {"discipline": "meihua", "question": "占失物", "way": "numbers", "numbers": "3,5,7"},
    {"discipline": "xiaoliuren", "question": "占寻人", "way": "numbers", "numbers": "7,7,2"},
    {"discipline": "zeji", "date": "2026/09/30", "activity": "嫁娶"},
)


def _load_web_runtime():
    path = ROOT / "web" / "engine_runtime.py"
    spec = importlib.util.spec_from_file_location("yi_web_engine_runtime", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_local(req: dict, outdir: Path) -> dict:
    req_file = outdir / "request.json"
    req_file.write_text(json.dumps(req, ensure_ascii=False), encoding="utf-8")
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "report.py"),
         "--request", str(req_file), "--outdir", str(outdir), "--name", "report"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if proc.returncode != 0:
        raise RuntimeError(f"本机链路失败（exit {proc.returncode}）：\n"
                           f"{(proc.stdout or '')[-800:]}\n{(proc.stderr or '')[-800:]}")
    return {"md": (outdir / "report.md").read_text(encoding="utf-8"),
            "html": (outdir / "report.html").read_text(encoding="utf-8")}


def _run_web(web_mod, req: dict, outdir: Path) -> dict:
    res = web_mod.build_report(ROOT, req, outdir)
    return {"md": res["md"], "html": res["html"]}


def _html_without_runtime_tag(html: str, req: dict) -> str:
    """把页头 meta 行整行替换成占位，只放行"运行环境"这一处有意差异。"""
    keep = report_meta(normalize_request(req), runtime="")
    prefix = keep.rsplit("生成：", 1)[0]
    out_lines = []
    for line in html.splitlines():
        if 'class="meta"' in line:
            out_lines.append('<p class="meta">__META__</p>')
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="网页端/本地端同源验收")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--keep", action="store_true", help="保留临时目录")
    args = ap.parse_args()

    web_mod = _load_web_runtime()
    base = Path(tempfile.mkdtemp(prefix="yi_parity_"))
    failures: list[str] = []
    print(f"临时目录：{base}\n")
    print("%-3s %-11s %-34s %-8s %-8s" % ("#", "学科", "请求摘要", "MD", "HTML"))

    for i, case in enumerate(CASES, 1):
        local_dir = base / f"{i:02d}-local"
        web_dir = base / f"{i:02d}-web"
        local_dir.mkdir(parents=True, exist_ok=True)
        web_dir.mkdir(parents=True, exist_ok=True)
        try:
            local = _run_local(case, local_dir)
        except Exception as exc:
            failures.append(f"#{i} {case['discipline']} 本机链路：{exc}")
            print("%-3d %-11s %-34s %-8s %-8s" % (i, case["discipline"], "本机链路失败", "×", "-"))
            continue
        try:
            web = _run_web(web_mod, case, web_dir)
        except Exception as exc:
            failures.append(f"#{i} {case['discipline']} 网页链路：{exc}")
            print("%-3d %-11s %-34s %-8s %-8s" % (i, case["discipline"], "网页链路失败", "-", "×"))
            continue

        md_same = local["md"] == web["md"]
        html_same = (_html_without_runtime_tag(local["html"], case)
                     == _html_without_runtime_tag(web["html"], case))
        req_brief = json.dumps({k: v for k, v in case.items() if k != "discipline"},
                               ensure_ascii=False)
        if len(req_brief) > 32:
            req_brief = req_brief[:31] + "…"
        print("%-3d %-11s %-34s %-8s %-8s" % (
            i, case["discipline"], req_brief,
            "√" if md_same else "×", "√" if html_same else "×"))
        if not md_same:
            failures.append(f"#{i} {case['discipline']} Markdown 两侧不一致")
            if args.verbose:
                _diff(local["md"], web["md"])
        if not html_same:
            failures.append(f"#{i} {case['discipline']} HTML 两侧不一致")
            if args.verbose:
                _diff(local["html"], web["html"])

    print()
    if failures:
        print(f"同源验收失败 {len(failures)} 项：")
        for f in failures:
            print("  × " + f)
        if not args.keep:
            pass
        return 1
    print(f"同源验收通过（{len(CASES)} 例）：网页端与本地端产出同源。")
    return 0


def _diff(a: str, b: str) -> None:
    import difflib
    al, bl = a.splitlines(), b.splitlines()
    shown = 0
    for line in difflib.unified_diff(al, bl, "本机", "网页", lineterm="", n=1):
        print("    " + line[:200])
        shown += 1
        if shown > 24:
            print("    …（截断）")
            break


if __name__ == "__main__":
    raise SystemExit(main())
