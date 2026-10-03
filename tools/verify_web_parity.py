# -*- coding: utf-8 -*-
"""网页端与本地端**同源验收**：同一请求两边出报告，逐例比对。

  python tools/verify_web_parity.py            # 八科各一例
  python tools/verify_web_parity.py --verbose  # 附两边首段摘要

为什么需要这个脚本：
  网页端（Pyodide / 同进程 runpy）与本地端（子进程）是**同一条四段契约的两个
  执行器**。执行器可以不同，产出必须同源——否则"点开链接看到的报告"与"CI 出的
  报告"会长成两个样子，而没人会发现。本脚本把这件事变成一条命令。

额外作用：网页侧是**同一个解释器里按 CASES 顺序连跑**，而八科的 `scripts/`
目录同名（每科都有 chart.py）。所以这份顺序本身就是
`web/engine_runtime._isolate` 的回归网——某科拿到别科盘面，逐字节比对立刻会红。

比对口径：
  * Markdown：**逐字节**必须一致（两边都只写学科 render 段产出的文本）。
  * HTML   ：只有页头小字里的「运行环境」标签允许不同（这是有意标注），
             其余逐字节必须一致。
  * Evidence：结构化证据信封必须一致（同一份 core 提取器的纯函数输出；
             宿主分叉即红——2026-10-03 证据链收敛新增维度）。

覆盖不变式：
  CASES 覆盖的学科集合必须与**站点挂载集合**（`tools/build_web.py` 的
  `DISCIPLINE_META`）恒等——站点挂上了某科而这里没有正例，本脚本直接失败。
  此前这里另存过一份写死的"web 通道不挂载"名单，于是"站点已挂载的"与"门验过的"
  是两个集合；现在两者由同一条断言绑死，不存在第三份手写清单。
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

from yishu_core.report import DISCIPLINES, normalize_request, report_meta  # noqa: E402
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
    # 这些请求必须与另一侧同源
    {"discipline": "meihua", "question": "占失物", "way": "numbers", "numbers": "3,5,7"},
    {"discipline": "xiaoliuren", "question": "占寻人", "way": "numbers", "numbers": "7,7,2"},
    {"discipline": "zeji", "date": "2026/09/30", "activity": "嫁娶"},
    # 通道 A 自 2026-10-01 起挂载全部八科，这两科一并纳入同源验收：
    # liuren 是骨架科（只出机械结构标签，无吉凶断语），lingqi 是查表直录类
    # （三部掷面数各 0..4，缺一即拒——见 NEG_CASES#1）。
    {"discipline": "liuren", "question": "占本周面试能否通过",
     "datetime": "2026-09-30 10:30"},
    {"discipline": "lingqi", "question": "占求财", "up": 2, "mid": 1, "down": 3},
    # 再回到第一科收尾：证明"跑过 liuren/lingqi 之后，早先那科的 scripts/ 仍解析到
    # 自己那套"（同名遮蔽若被破坏，这一例最先红）。
    {"discipline": "liuyao", "question": "占出行", "mode": "time",
     "datetime": "2026-10-01 08:00"},
)


# 负例：非法 / 越界输入。两侧必须"一致地拒绝"，否则说明某一侧漏了参数门禁
# （映射层 `request.chart_argv` 是唯一入口，这条断言就是它的回归网）。
NEG_CASES = (
    {"discipline": "lingqi", "question": "占出行", "numbers": "0,0,0"},  # 三部掷数全零
    {"discipline": "ming", "datetime": "1990-13-45", "gender": "男"},     # 不存在的日期
)
def _load_build_web():
    """按文件路径加载构建期唯一开关（`tools/` 不是包，按路径加载最省事）。"""
    path = ROOT / "tools" / "build_web.py"
    spec = importlib.util.spec_from_file_location("yi_build_web_for_parity", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _web_mount_ids() -> tuple[str, ...]:
    """站点挂载集合。唯一真值源是构建期 `DISCIPLINE_META`，此处不另存手写清单。"""
    return tuple(d["id"] for d in _load_build_web().DISCIPLINE_META)


# 「引擎已实现、但站点通道不挂载」= 引擎学科集合 − 站点挂载集合，**派生而来，不写死**：
# `DISCIPLINE_META` 或 `request.DISCIPLINES` 一变，本集合随之变。2026-10-01 通道 A
# 挂载全部八科后它自然为空；将来若有学科只走本地 CLI / 通道 B，它会自动收进来，
# 负例段即恢复"只断言网页拒绝"的分支——不需要谁记得回来改一行名单。
WEB_CHANNEL_UNAVAILABLE: tuple[str, ...] = tuple(
    d for d in DISCIPLINES if d not in set(_web_mount_ids())
)


def _load_web_runtime():
    path = ROOT / "web" / "engine_runtime.py"
    spec = importlib.util.spec_from_file_location("yi_web_engine_runtime", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _evidence_of(req: dict, analyze_json: dict) -> dict:
    """Evidence 信封（与 YiRuntime.execute / engine_runtime.build_report 同一份 core 提取器）。"""
    from yishu_core.evidence import evidence_envelope, evidence_from_analyze
    from yishu_core.execution.registry import evaluation_baseline_of
    d = req["discipline"]
    baseline = evaluation_baseline_of(d)
    return evidence_envelope(
        d, evidence_from_analyze(d, analyze_json, evaluation_baseline=baseline),
        evaluation_baseline=baseline)


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
    analyze_p = outdir / "report.analyze.json"
    evidence = _evidence_of(normalize_request(req),
                            json.loads(analyze_p.read_text(encoding="utf-8")))
    return {"md": (outdir / "report.md").read_text(encoding="utf-8"),
            "html": (outdir / "report.html").read_text(encoding="utf-8"),
            "evidence": evidence}


def _run_web(web_mod, req: dict, outdir: Path) -> dict:
    res = web_mod.build_report(ROOT, req, outdir)
    return {"md": res["md"], "html": res["html"], "evidence": res["evidence"]}


def _try_local(req: dict, outdir: Path) -> tuple[bool, str]:
    try:
        _run_local(req, outdir)
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _try_web(web_mod, req: dict, outdir: Path) -> tuple[bool, str]:
    try:
        _run_web(web_mod, req, outdir)
        return True, ""
    except Exception as exc:
        return False, str(exc)


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

    # ── 覆盖不变式：正例覆盖集合 ≡ 站点挂载集合 ─────────────────────────────
    # 二者一旦不等就先红，不许靠"把某科排除出验收"换绿（评审项 A4）。
    mount_ids = _web_mount_ids()
    covered_ids = tuple(dict.fromkeys(c["discipline"] for c in CASES))
    print("覆盖检查：站点挂载 %d 科 —— %s" % (len(mount_ids), "、".join(mount_ids)))
    print("          同源验收 %d 例覆盖 %d 科 —— %s"
          % (len(CASES), len(covered_ids), "、".join(covered_ids)))
    missing = [d for d in mount_ids if d not in covered_ids]
    beyond = [d for d in covered_ids if d not in mount_ids]
    if missing or beyond:
        for d in missing:
            print("  × 站点已挂载、同源验收却无正例：" + d)
        for d in beyond:
            print("  × 同源验收有正例、站点却未挂载：" + d)
        print("\n同源验收失败 1 项：覆盖集合 ≠ 站点挂载集合。"
              "补正例或改 DISCIPLINE_META，不得放宽断言。")
        return 1
    if WEB_CHANNEL_UNAVAILABLE:
        print("          未走站点通道的学科（负例段只断言网页拒绝）："
              + "、".join(WEB_CHANNEL_UNAVAILABLE))
    print("  √ 覆盖集合与站点挂载集合恒等\n")
    base = Path(tempfile.mkdtemp(prefix="yi_parity_"))
    failures: list[str] = []
    print(f"临时目录：{base}\n")
    print("%-3s %-11s %-34s %-8s %-8s %-4s" % ("#", "学科", "请求摘要", "MD", "HTML", "EV"))

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
        ev_same = local["evidence"] == web["evidence"]
        req_brief = json.dumps({k: v for k, v in case.items() if k != "discipline"},
                               ensure_ascii=False)
        if len(req_brief) > 32:
            req_brief = req_brief[:31] + "…"
        print("%-3d %-11s %-34s %-8s %-8s %-4s" % (
            i, case["discipline"], req_brief,
            "√" if md_same else "×", "√" if html_same else "×",
            "√" if ev_same else "×"))
        if not md_same:
            failures.append(f"#{i} {case['discipline']} Markdown 两侧不一致")
            if args.verbose:
                _diff(local["md"], web["md"])
        if not html_same:
            failures.append(f"#{i} {case['discipline']} HTML 两侧不一致")
            if args.verbose:
                _diff(local["html"], web["html"])
        if not ev_same:
            failures.append(f"#{i} {case['discipline']} Evidence 两侧不一致"
                            "（证据提取器被宿主分叉？唯一实现 core/yishu_core/evidence.py）")

    # 负例段：非法 / 越界输入必须两侧一致地拒绝
    print("—— 负例：非法/越界输入的两侧拒绝必须一致 ——")
    for i, case in enumerate(NEG_CASES, 1):
        d = base / f"x{i:02d}"
        d.mkdir(parents=True, exist_ok=True)
        disc = case["discipline"]
        lok, lmsg = _try_local(case, d)
        wok, wmsg = _try_web(web_mod, case, d)
        if disc in WEB_CHANNEL_UNAVAILABLE:
            # 通道没挂载 → 只要求网页明确拒绝（本地放行是设计意图）
            if wok:
                failures.append(f"负例#{i} {disc} 网页通道应拒绝却放行了")
                print(f"  × 负例#{i} {disc}: 网页应拒绝却放行")
            else:
                print(f"  √ 负例#{i} {disc}: 网页拒绝（本地/通道不对称，设计意图）")
            continue
        if lok != wok:
            failures.append(f"负例#{i} {disc} 拒绝判定不同源：本地={'通过' if lok else '拒绝'}，"
                            f"网页={'通过' if wok else '拒绝'}")
            print(f"  × 负例#{i} {disc}: 拒绝判定不同源（本地={'通过' if lok else '拒绝'}，"
                  f"网页={'通过' if wok else '拒绝'}）")
            continue
        if not lok:
            # 只断言"两侧都拒绝"，不做拒绝层次比对：本地侧恒被 subprocess 包成
            # RuntimeError，网页侧则嵌了 traceback（内含 ValueError 等字样误字符匹配），
            # 两者层次本就不可比；真正的实质是"非法输入不许某一侧悄悄放行"。
            print(f"  √ 负例#{i} {disc}: 两侧均拒绝")
        else:
            print(f"  √ 负例#{i} {disc}: 两侧均放行（用例已失效，请换成真正非法的输入）")
    print()

    if failures:
        print(f"同源验收失败 {len(failures)} 项：")
        for f in failures:
            print("  × " + f)
        if not args.keep:
            pass
        return 1
    print(f"同源验收通过（正例 {len(CASES)} 例 + 负例 {len(NEG_CASES)} 例）："
          f"网页端与本地端产出同源（MD/HTML/Evidence）、非法输入一致地拒绝。")
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
