# -*- coding: utf-8 -*-
"""浏览器内（Pyodide）运行 Yi 推演引擎的适配层。

为什么需要这一层：
  * Yi 的学科脚本彼此用**裸模块名**互相 import（`from chart import ...`），
    而两科的 scripts/ 目录**同名**（每科都有 chart.py）。同一个解释器里连着跑两科
    会互相遮蔽——实测：先跑六爻再跑小六壬，小六壬的 `from chart import PALACES`
    拿到的是六爻的 chart。所以跑某科之前必须把别的学科模块清出 sys.modules。
  * Pyodide 没有 subprocess，`tools/report.py` 那种"分步起子进程"跑不了，
    改用 runpy 在同一进程里分步执行。

与 tools/report.py 的分工：
  * 请求 → 命令行参数的映射**两边共用**内核 `yishu_core.report`（单一真值源）；
  * 本模块只负责"在浏览器这个宿主里怎么跑"，不重复任何映射逻辑。

产出（MD 文本、HTML 文本）应与 tools/report.py 一致，
可用 `python tools/verify_web_parity.py` 逐例校验。
"""
from __future__ import annotations

import contextlib
import io
import json
import runpy
import sys
import traceback
from pathlib import Path

# web 通道支持的学科：与 tools/build_web.py 的 DISCIPLINE_META 同口径，
# 也与本地 CLI / 通道 B 的学科集合一致——通道 A 挂载两科（liuyao/ming）。
WEB_DISCIPLINES = ("liuyao", "ming")

RUNTIME_LABEL = "浏览器内 Pyodide"

_CORE_READY = False


def _ensure_core(engine_root: Path) -> None:
    """把内核挂上 sys.path（幂等）。"""
    global _CORE_READY
    core = str((engine_root / "core").resolve())
    if core not in sys.path:
        sys.path.insert(0, core)
    _CORE_READY = True


# ── 模块隔离：模拟"一科一个解释器"的子进程语义 ──────────────────────────────

def _isolate(engine_root: Path, disc: str) -> list[str]:
    """把解释器收拾成"只服务这一科"的状态。

    做三件事：
      1. 清掉 sys.modules 里**别的学科**的模块（同名遮蔽的根源）；
      2. 把 sys.path 上**所有**学科的 scripts/ 目录全部移除
         （否则先跑 A 再跑 B 时，A 的 scripts 目录仍留在 path 上，
         B 里一个只存在于 A 目录的裸模块名仍会解析到 A —— 遮蔽并未根除）；
      3. 把本学科 scripts/ 目录提到 sys.path 最前，裸模块名只可能解析到本学科。
    返回被清掉的模块名（供联调观察；正常使用无需关心）。
    """
    disc_dir = (engine_root / "disciplines").resolve()
    purged: list[str] = []
    for name in list(sys.modules):
        mod = sys.modules.get(name)
        f = getattr(mod, "__file__", None)
        if not f:
            continue
        try:
            rel = Path(f).resolve().relative_to(disc_dir)
        except (ValueError, OSError):
            continue
        if rel.parts and rel.parts[0] != disc:
            sys.modules.pop(name, None)
            purged.append(name)

    # 2. 先把所有学科的 scripts 目录从 sys.path 剥离（含本学科，第 3 步再放回最前）
    all_scripts = {str(p.resolve()) for p in disc_dir.glob("*/scripts") if p.is_dir()}
    sys.path[:] = [p for p in sys.path if p not in all_scripts]

    # 3. 只把当前学科提到最前
    scripts = (disc_dir / disc / "scripts").resolve()
    if scripts.is_dir():
        sys.path.insert(0, str(scripts))
    return purged


# ── 四段契约的浏览器侧执行器 ────────────────────────────────────────────────

def _run_script(script: Path, argv: list[str]) -> tuple[int, str]:
    """在同一进程里以 `__main__` 语义执行学科脚本，返回 (退出码, 捕获输出)。"""
    buf = io.StringIO()
    old_argv = sys.argv[:]
    sys.argv = [str(script), *argv[1:]]
    code = 0
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            runpy.run_path(str(script), run_name="__main__")
    except SystemExit as exc:
        code = int(exc.code or 0)
    except BaseException:
        code = 99
        buf.write("\n" + traceback.format_exc())
    finally:
        sys.argv = old_argv
    return code, buf.getvalue()


def build_report(engine_root: str | Path, req: dict, outdir: str | Path) -> dict:
    """端到端出报告（chart→analyze→render→HTML），返回 dict（含 MD/HTML 全文）。"""
    engine_root = Path(engine_root).resolve()
    outdir = Path(outdir).resolve()
    _ensure_core(engine_root)

    # 内核的映射层：与 tools/report.py 同一份
    from yishu_core.report import (  # noqa: E402
        MD_FEEDBACK_NOTE,
        REPORT_FOOTER,
        analyze_argv,
        chart_argv,
        normalize_request,
        render_argv,
        report_meta,
        report_title,
    )

    req = normalize_request(req)
    d = req["discipline"]
    if d not in WEB_DISCIPLINES or not (engine_root / "disciplines" / d / "scripts").is_dir():
        raise ValueError(
            f"学科 {d!r} 未挂载 web 站点通道（仅本地 CLI 可用）；"
            f"web 支持科目：{'、'.join(WEB_DISCIPLINES)}")
    _isolate(engine_root, d)

    outdir.mkdir(parents=True, exist_ok=True)
    stem = req.get("name") or "report"
    chart_p = outdir / f"{stem}.chart.json"
    analyze_p = outdir / f"{stem}.analyze.json"
    md_p = outdir / f"{stem}.md"
    html_p = outdir / f"{stem}.html"
    scripts = engine_root / "disciplines" / d / "scripts"

    code, out = _run_script(
        scripts / "chart.py",
        chart_argv(req, str(scripts / "chart.py"), str(chart_p)))
    if code != 0:
        raise RuntimeError(f"chart 段失败（exit {code}）：\n{out[-1500:]}")

    code, out = _run_script(
        scripts / "analyze.py",
        analyze_argv(req, str(scripts / "analyze.py"), str(chart_p), str(analyze_p)))
    if code != 0:
        raise RuntimeError(f"analyze 段失败（exit {code}）：\n{out[-1500:]}")

    code, out = _run_script(
        scripts / "render.py",
        render_argv(req, str(scripts / "render.py"), str(analyze_p), str(md_p)))
    if code != 0:
        raise RuntimeError(f"render 段失败（exit {code}）：\n{out[-1500:]}")

    md_text = md_p.read_text(encoding="utf-8") + MD_FEEDBACK_NOTE
    md_p.write_text(md_text, encoding="utf-8")

    from yishu_core.report.html import report_page_from_markdown  # noqa: E402
    title = report_title(req)
    html = report_page_from_markdown(
        title=title, markdown=md_text,
        meta=report_meta(req, runtime=RUNTIME_LABEL), footer=REPORT_FOOTER)
    html_p.write_text(html, encoding="utf-8")

    # 结构化证据（Evidence Contract 派生视图）——与本机 YiRuntime.execute 同一份
    # core 提取器（纯函数），宿主差异不进证据；MD/HTML 不受影响（同源验收照旧）。
    from yishu_core.evidence import evidence_envelope, evidence_from_analyze  # noqa: E402
    from yishu_core.execution.registry import evaluation_baseline_of  # noqa: E402
    analysis_data = json.loads(analyze_p.read_text(encoding="utf-8"))
    baseline = evaluation_baseline_of(d)
    evidence = evidence_envelope(
        d, evidence_from_analyze(d, analysis_data, evaluation_baseline=baseline),
        evaluation_baseline=baseline)

    return {"discipline": d, "title": title, "md": md_text, "html": html,
            "evidence": evidence,
            "md_path": str(md_p), "html_path": str(html_p)}


# ── Pyodide 入口 ────────────────────────────────────────────────────────────
# 页面侧负责用 pyfetch 把源码镜像取回、按 engine/<仓库相对路径> 落盘；
# 本模块只负责在已就位的文件系统上执行四段契约。


def run(request_json: str, engine_root: str, outdir: str) -> str:
    """页面调用入口：入参 JSON 字符串，返回结果 JSON 字符串。"""
    res = build_report(engine_root, json.loads(request_json), outdir)
    return json.dumps(res, ensure_ascii=False)


DEMO = {
    "liuyao": {"discipline": "liuyao", "question": "自检占", "mode": "time",
               "datetime": "2026-09-30 10:30"},
    "ming": {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
}


def smoke(engine_root: str, disc: str = "liuyao") -> str:
    """自检：跑一例并返回摘要（供页面"自检"按钮与联调用）。"""
    res = build_report(engine_root, DEMO[disc], "/out")
    return json.dumps({"discipline": disc, "title": res["title"],
                       "md_bytes": len(res["md"].encode("utf-8")),
                       "html_bytes": len(res["html"].encode("utf-8"))},
                      ensure_ascii=False)
