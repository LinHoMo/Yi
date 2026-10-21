# -*- coding: utf-8 -*-
"""一条命令跑完全部质量门：`python dev_tools/check.py [--only eval calendar]`

  python dev_tools/check.py            # 全部检查
  python dev_tools/check.py --fast     # 跳过耗时的两套案例评测
  python dev_tools/check.py --raise    # 把当前实测值写回基线（确认改进后才用）

  --only 逗号与空格等价（`--only eval,calendar` 同 `--only eval calendar`）；给的名字一个
  都对不上就报错、列出可用项并退出码 2——不会"零门执行却打印通过"。

门槛设计（见 SKILL.md）：
  · 历法自检、段落产出冒烟 —— 必须全绿，任何回退即失败
  · 思维链用例、古籍回归、tune/holdout 对齐分 —— **只准前进不准后退**：
    与 BASELINE 比较，低于基线即失败。基线是 2026-09-22 重建评分器后的实测值，
    不是"理想值"；M1/M2 修好后用 --raise 抬上去。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]          # 学科根：liuyao
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import kernel_dir as _kernel_dir, repo_root as _repo_root  # noqa: E402
REPO = _repo_root(__file__)                          # 学科根：core 的父目录
ROOT = DISC                                          # 兼容旧变量名：脚本与数据以学科根为基准
sys.path.insert(0, str(_kernel_dir(__file__)))
from yishu_core.gate_kit import (  # noqa: E402
    eval_metrics as _kit_eval_metrics,
    measure as _kit_measure,
    run_step as _run_step,
)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = ROOT / "dev_tools" / "check_baseline.json"


def _project_header(text: str) -> dict:
    """零依赖最小 TOML 读取：只取 [project] 段内的 name/version/dynamic。

    pyproject 只被此检查用，不值得引入 tomllib/tomli 依赖（Python 3.10 兼容）。
    """
    section = None
    out: dict = {}
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            section = stripped[1:stripped.rfind("]")].strip()
            continue
        if section != "project" or "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        key, raw = key.strip(), raw.strip()
        if key == "dynamic":
            m = re.search(r"\[([^\]]*)\]", raw)
            items = (m.group(1) if m else "").split(",")
            out[key] = [v.strip().strip('"').strip("'")
                        for v in items if v.strip()]
        elif key in ("name", "version"):
            out[key] = raw.strip('"').strip("'")
    return out

BASELINE = {
    "calendar": 16,        # 历法自检通过项数（共 16）
    "ordering": 23,        # 爻序断言通过项数（共 23）——P0 事故看门狗
    "smoke": 36,           # 有产出的分析段
    "chain_tests": 11,     # /12（2026-10-10 上抬，理由见下方归因块）
    "regression": 14,      # 例数以汇总行为准（现 19 例：第八十二批加 reg_19 全要素真例；
                            # 2026-10-10 第十四批：7 例 fixture 的日期/爻数组与自身书证
                            # 对不上，校勘后 reg_13 由"假基准下的蒙对"变为真通过，11→12；
                            # 第十五批：补「近病＋卦逢六冲即愈」（源L17/L19/L21/L23）
                            # 并把 reg_01 的判词依源L539「果于丑日起床」改正，12→13；
                            # 第十七批：补「泄用之神」定价（用神生动爻，源L1662
                            # 「如世去生助他爻，泄尽自己之气也」——第五态此前落闲神恒计 0），
                            # reg_14 的动变断言依其数组实情改记 N/A，13→14）
    # 退化 2 例（旧表"隔一支配对"把寅→卯误判为"化合"零分）逐条解释：
    #   reg_05（占求财·妻财伏藏·寅→卯 子孙原神化进）：旧表判化合 net_event≈0 → 平吉2.71→PASS；
    #     新书源同五行对 → 化进神 → net_effect+3.5 → 大吉5.16→ 方向 band ≠ expected(mixed)→FAIL。
    #     书源据：《增删卜易》L1120/L1122「寅化卯进也」五源同证（见 commit 3bf717f）。
    #   reg_13（占子病·伏神得出·旺衰）：因进神表修正关联的 step3 旺衰评分从3.5→3.8,
    #     越过 medium 区间上限(0.5≤score<3.5)→ 旺衰断言 FAIL。方向、区间均 OK（dir=band=OK）。
    # 三条不动保护：① ADVANCE_PAIRS 五源同证是书源被动过，不可回退；② 不为让这 2 例回去而开
    #    case-specific 分支（违 SKILL.md）；③ 退化代价已计入：tune 97.2/holdout 90.2
    #    均稳超基线 93.9/85.7，wikisource_direction 24/38→28/38 净+4，是净正改进。
    # ── 2026-10-10 基线上抬 8→11 / 9→11（只准前进，非凑绿）──
    # 两处判据修正各自的实测效果（同一批用例、同一份金标准输入集）：
    #   ① step4 4.3c 去进退神重复计分（旧块加的是**不含角色**的 ±2~3.5，
    #      把 4.3a/b 已按角色定好号的 忌神化进 −1.0 反盖成正）→ reg_05 回绿，
    #      正是上面那条「net_effect+3.5 → 大吉5.16 → band≠mixed」的老账，
    #      同时净效应量级从 7.15/−6.79 回到 ±3 带内；
    #   ② 原神化退只在休囚时减力（《增删卜易》L541 旺相即能生用，
    #      L551 第三款作无力的原话是「元神**休囚**动化退神」）→ reg_03/case_03 回绿。
    # 仍红的 6 例不再由这两处解释，逐条已登记 docs/CHANGELOG.md：reg_01/07/17 的
    # fixture 与自身书证的卦变差集不自洽（本库对转写本的立场见
    # docs/CASE-LIBRARY-AUDIT.md：未校勘前不据以定标准，故不在此改数组凑绿）；
    # reg_14/18 缺泄神、双用神的角色定价；reg_13/16 为 fixture 卦名与书文不符。
    # 外部集如实记：wikisource_holdout 66.9→63.1（verdict 19/21→17/21），
    # 新增 2 例失分的形态是「verdict=吉 而 final_score 为负」（−0.53/−0.64），
    # 即 step5 覆写链的判词与自家分数打架——此前被 ① 的虚高加分掩盖，
    # 现由 regression_test 的「判词/分数不一致」报警单独显形，不参与通过判定。
    "tune": 93.9,          # 古籍对齐分 strict，n=20
    "holdout": 85.7,       # 古籍对齐分 strict，n=12（未参与调参）
    "tune_top1": 58.8,     # 主应期命中率 %（此列的对照应是**单支断言零模型**：均匀 1/12=8.3%；
                            # 基线注里的 ~38 是「全池覆盖零」，属 loose 的对照——第一百八十一批
                            # 更正类别配对，数字基线不动、行为零改动）
    "holdout_top1": 50.0,
}
# 基准应支平均名次：越小越好，单独按上限把关
BASELINE_MAX = {"tune_rank": 2.0, "holdout_rank": 1.7}

PATTERNS = {
    "chain_tests": r"Passed:\s*(\d+)/(\d+)",
    "regression": r"总通过:\s*(\d+)/(\d+)",
    "smoke": r"有产出:\s*(\d+)",
}


ENC_WITNESS: list[str] = []


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、无超时、argv 自带解释器（实现在内核 gate_kit）。"""
    _rc, _out = _run_step(cmd, cwd=ROOT)
    try:
        import importlib.util as _iu
        _path = str(ROOT / "dev_tools" / "check_cli_encoding.py")
        _sp = _iu.spec_from_file_location("enc_witness", _path)
        if _sp is None or _sp.loader is None:
            raise RuntimeError("载不进门：『" + _path + "』")
        _mod = _iu.module_from_spec(_sp)
        _sp.loader.exec_module(_mod)
        witness = _mod.witness
    except Exception as _e:
        ENC_WITNESS.append("编码证人自身没跑成：" + type(_e).__name__ + ": " + str(_e)[:90])
    if witness is not None:
        _nm = next((a for a in cmd if str(a).endswith(".py")), str(cmd[-1]))
        _w = witness(_nm, _out or "")
        if _w:
            ENC_WITNESS.append(_w)
    return _rc, _out


def measure(name: str, out: str) -> float | None:
    return _kit_measure(name, out, PATTERNS)


def eval_metrics(split: str) -> dict:
    """跑一个集合，返回 {avg, top1, rank}（新鲜度守卫与落盘点在内核 gate_kit）。"""
    return _kit_eval_metrics(split, model_key="strict", cwd=ROOT,
                             eval_file=ROOT / "data" / "cases" / f"eval_{split}.json")


# 本地门户产物，gitignore 的构建物。新克隆里没有 → 版本门跳过并说明，
# 而不是 FileNotFoundError 把整个门判红。
PORTAL_ARTIFACTS = ("assets/portal_data.json", "index.html")

# ── chart 段纯净门（缺陷 A 回归看门狗，2026-10-09）──────────────────────────
# CONTRACT §一：chart 段禁一切吉凶措辞。chart JSON 允许出现的「吉/凶/宜/忌」
# 只有卦辞爻辞引文（排盘素材，SKILL.md 内核卦辞爻辞），字段名白名单外
# 任何字符串含判语字即红。负例自证：内存植一条明知违规的探针串，扫描器必须
# 抓到它——抓不到说明门是死的（§四.8），全绿不算通过。
CHART_VERDICT_WORDS = ("大凶", "凶", "吉", "宜", "忌")
CHART_QUOTED_FIELDS = {"judgment", "line_text"}   # 卦辞/爻辞引文字段（唯一豁免）


def _scan_chart_verdict_strings(node, path=""):
    """返回 JSON 中越界的断语级字符串 (path, text) 列表。

    豁免：字段名为 judgment/line_text 的卦辞爻辞**引文**（排盘素材，SKILL.md）。
    其余任何字符串含 大凶/凶/吉/宜/忌 即视为 chart 段泄露吉凶断语。
    """
    hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            sub = f"{path}.{k}"
            if isinstance(v, (dict, list)):
                hits.extend(_scan_chart_verdict_strings(v, sub))
            elif isinstance(v, str):
                if k not in CHART_QUOTED_FIELDS and any(w in v for w in CHART_VERDICT_WORDS):
                    hits.append((sub, v))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            hits.extend(_scan_chart_verdict_strings(v, f"{path}[{i}]"))
    return hits


def chart_purity_problems() -> list[str]:
    """跑一次固定输入 chart 段，验输出无断语级文本 + 扫描器负例自证。"""
    problems: list[str] = []
    # 负例自证（§四.8）：先证明扫描器能抓到植入了违规串的盘——抓不到就是死门。
    probe = {"original_hexagram": {"judgment": "亨，利涉大川",        # 豁免：卦辞引文
                                   "yao_lines": [{"line_text": "潜龙勿用"}],
                                   "leak": "三爻回头克（大凶）"},       # 植入违规
             "advanced_analysis": {"advance_retreat": {"summary": "凶象显著"}}}
    probe_hits = _scan_chart_verdict_strings(probe)
    if not probe_hits:
        problems.append("chart 纯净门负例自证失败：植入的探针违规串没被抓到，门是死的")
        return problems
    if any(p.endswith(".judgment") or ".line_text" in p for p, _ in probe_hits):
        problems.append("chart 纯净门负例自证失败：把豁免字段（卦辞/爻辞）误判为违规")
        return problems

    import json as _json
    cmd = [sys.executable, str(DISC / "scripts" / "chart.py"),
           "--mode", "manual", "--yao", "7,8,9,7,6,8", "--question", "占病"]
    rc, out = run(cmd)
    # run() 的 cwd 是学科根；chart.py 用绝对路径可跑
    if rc != 0:
        problems.append(f"chart 纯净门：chart.py 运行失败（退出码 {rc}）")
        return problems
    try:
        start = out.index("{")
        data = _json.loads(out[start:])
    except ValueError:
        problems.append("chart 纯净门：chart.py 输出不是可解析 JSON")
        return problems
    hits = _scan_chart_verdict_strings(data)
    for p, txt in hits:
        problems.append(f"chart 段含断语级文本：{p} = {txt[:60]!r}")
    # 同轮顺带校验：enhance_reading 不在 chart 段跑（换产地到 analyze 段的结构性证明）
    if "advanced_analysis" in data:
        problems.append("chart 段输出仍含 advanced_analysis——断语级增强段应在 analyze 段产出（缺陷 A）")
    return problems


def version_report() -> list[str]:
    """返回不一致项。版本唯一真值源是 yishu_core.__version__。"""
    import yishu_core

    problems = [f"版本号不合语义：{yishu_core.__version__}"] if not re.match(
        r"^\d+\.\d+\.\d+$", yishu_core.__version__) else []
    # 扁平化后仓库根不再有 pyproject（各学科自包含、内核唯一发版）；
    # 仅当该文件存在时才核对包名/version 口径，缺失则跳过（不崩溃）。
    pyproject = REPO / "pyproject.toml"
    if pyproject.exists():
        proj = _project_header(pyproject.read_bytes().decode("utf-8"))
        if proj.get("name") != "yishu-core":
            problems.append(f"仓库根 pyproject 包名是 {proj.get('name')}，应为 yishu-core")
        if "version" in proj:
            problems.append(f"pyproject [project] 里又写了字面 version={proj['version']}，"
                            f"应改走 dynamic 从 yishu_core 取")
        if "version" not in proj.get("dynamic", []):
            problems.append("pyproject [project].dynamic 未包含 version")
    if (DISC / "pyproject.toml").exists():
        problems.append("学科根不该再有一份 pyproject（内核唯一发版）")

    for rel in PORTAL_ARTIFACTS:
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        m = re.search(r'"version"\s*:\s*"([^"]+)"', text)
        if not m:
            problems.append(f"{rel} 找不到 version 字段")
        elif m.group(1) != yishu_core.__version__:
            problems.append(f"{rel} 版本是 {m.group(1)}，应为 {yishu_core.__version__}"
                            f"（跑 python scripts/build_portal_assets.py 重建）")
    return problems


def report_parity_problems() -> list[str]:
    """「算出来了但看不到」看门狗：analyze 产出的每一节都必须在 HTML 报告里出现。

    起因（2026-10-10 实测）：`section_advice`（趋避建议）在文本报告与 narrate 都有，
    HTML 却整节没有——`assets/report.css` 里 `.advice-list` 自定义好却无人引用即旁证。
    金标准指纹与对齐分都看不见这类回归（它们只量机械值与判词，不量"某一节有没有出口"）。

    本门自带**负例自证**：把真实产物里的那一节人为摘掉后，检查必须报错——
    否则「门通过」与「门什么都没查」在报告里长得一样。
    """
    sp = str(DISC / "scripts")
    if sp not in sys.path:
        sys.path.insert(0, sp)
    from kernel_path import ensure_kernel_on_path as _ks
    _ks(Path(sp) / "render.py")

    problems: list[str] = []
    from datetime import datetime

    from engine import build_hexagram_result
    from analyze import analyze as _analyze
    from render import render_html
    from yishu_core.report.html import escape

    dt = datetime(2024, 3, 5, 10, 30)
    h = build_hexagram_result([9, 8, 7, 8, 7, 7], "占父病", "manual",
                              dt.year, dt.month, dt.day, dt.hour)
    a = dict(_analyze(h))
    html = render_html(a)

    # 1) 逐节断言：凡 analyze 层有内容的主节，HTML 必须有对应节标题
    con = a.get("conclusion") or {}
    expect = []
    if a.get("section_advice"):
        expect.append(("趋避建议", "section_advice"))
    if con.get("应期"):
        expect.append(("应期", "conclusion.应期"))
    if con.get("所本"):
        expect.append(("判据所本", "conclusion.所本"))
    if not expect:
        problems.append("取到的样例没有任何可选节可断言（section_advice/应期/所本 全空）"
                        "——本门等于没跑，请换一例")
    for title, src in expect:
        if title not in html:
            problems.append(f"HTML 报告缺「{title}」节，而 {src} 有 "
                            f"{len(a.get('section_advice') or con.get('应期') or [''])} 项内容")

    # 1b) 方位层可见性探针（原门只盯上面三节，advanced_analysis 的子节掉出 HTML 查不到）
    h_fw = build_hexagram_result([9, 8, 7, 8, 7, 7], "占通乡避乱", "manual",
                                 dt.year, dt.month, dt.day, dt.hour)
    a_fw = dict(_analyze(h_fw))
    fw = (a_fw.get("advanced_analysis") or {}).get("fangwei") or {}
    if not fw.get("applicable"):
        problems.append("方位探针失效：「占通乡避乱」未触发 fangwei（语域关键词或取爻口径变了）"
                        "——本项等于没跑，请修探针而不是删门")
    else:
        html_fw = render_html(a_fw)
        if "方位参考" not in html_fw:
            problems.append(f"HTML 缺「方位参考」节，而 advanced_analysis.fangwei 有 "
                            f"{len(fw.get('candidates') or [])} 条候选、吉方 {fw.get('ji_fang')}")
        doctored_fw = html_fw.replace("方位参考", "已删节", 1)
        if "方位参考" in doctored_fw or "已删节" not in doctored_fw:
            problems.append("方位负例失效：摘掉一处后 HTML 仍含该节标题，探针无从证明本门有牙")

    # 2) 内容级断言：建议条目逐条出现在 HTML 里，不是只要有个标题
    for t in (a.get("section_advice") or []):
        if escape(str(t)) not in html:
            problems.append(f"趋避建议条目未进 HTML：{str(t)[:24]}")

    # 3) 负例自证：人为摘掉趋避节，检查必须抓到（否则本门是空跑）
    if "趋避建议" in html:
        doctored = html.replace("趋避建议", "已删节", 1)
        if "趋避建议" in doctored:
            problems.append("负例探针失效：摘掉一处后 HTML 仍含该节标题，"
                            "说明本节出现多次，探针无法证明本门有牙")
        if "趋避建议" in doctored or "已删节" not in doctored:
            problems.append("负例样本构造失败，本门未验证")
    else:
        problems.append("负例探针无法执行：正样本本身就不含趋避建议（见上）")

    # 4) 崩溃不得伪装成产物
    if "Traceback" in html:
        problems.append("HTML 里泄漏了 Python traceback")
    return problems


def feedback_selftest() -> list[str]:
    """六爻反馈闭环假例自检（架构评审 A2）——此前本通道「有实现、无测试、无数据」。

    只跑**纯假例**，且落盘目标改成临时目录（不碰 `data/feedback/`，那是真实用户
    回填数据的落点，铁律二）。断言：应期抽取、strict/loose 判定（口径取自内核
    `yishu_core.yingqi`）、读数汇总，以及审计报告确实带口径句。
    """
    import shutil
    import tempfile

    sys.path.insert(0, str(DISC / "dev_tools"))
    from feedback_store import FeedbackStore, _extract_yingqi_dates  # noqa: E402
    import feedback_report  # noqa: E402

    problems: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="fb_selftest_"))
    try:
        store = FeedbackStore("liuyao")
        store.dir = tmp
        analyze = {"conclusion": {"应期": ["2026-10-05（冲空填实）", "2026-10-17（出旬）"]}}
        dates = _extract_yingqi_dates(analyze)
        if dates != ["2026-10-05", "2026-10-17"]:
            problems.append(f"应期抽取结果 {dates} ≠ 期望的两条 YYYY-MM-DD 候选")
        store.save({"analyze_json": analyze, "actual_date": "2026-10-06"})   # ±1 天 → 严格命中
        store.save({"analyze_json": analyze, "actual_date": "2026-11-20"})   # 远距 → 双否
        recs = {r["actual_date"]: r for r in store.load_all()}
        if len(recs) != 2:
            problems.append(f"落盘记录数 {len(recs)} ≠ 2")
        near = recs.get("2026-10-06") or {}
        if not (near.get("hit_strict") and near.get("hit_loose")):
            problems.append(f"±1 天应记严格命中，实为 strict={near.get('hit_strict')}"
                            f" loose={near.get('hit_loose')}")
        far = recs.get("2026-11-20") or {}
        if far.get("hit_strict") or far.get("hit_loose"):
            problems.append(f"远距日期不得记命中，实为 strict={far.get('hit_strict')}"
                            f" loose={far.get('hit_loose')}")
        st = store.stats()
        if (st["strict_hits"], st["loose_hits"], st["with_actual_outcome"]) != (1, 1, 2):
            problems.append(f"汇总读数 {st} ≠ （严格 1、宽松 1、可评 2）")
        if "口径" not in feedback_report.summary(store):
            problems.append("审计报告未附口径句（WINDOW_CALIBER 未接线）")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="六爻质量门")
    ap.add_argument("--only", nargs="*", help="限定检查项（逗号与空格分隔等价；对不上即报错退出 2）")
    ap.add_argument("--fast", action="store_true", help="跳过案例评测（tune/holdout）")
    ap.add_argument("--raise", dest="raise_baseline", action="store_true",
                    help="以本次实测覆盖基线（仅在确认改进后使用）")
    args = ap.parse_args()

    baseline = dict(BASELINE)
    if BASELINE_FILE.exists():
        baseline.update(json.loads(BASELINE_FILE.read_text(encoding="utf-8")))

    measured: dict[str, float] = {}
    failures: list[str] = []

    def gate(name: str, value: float | None, *, minimum: float = 0.0, maximum: float | None = None,
             label: str, raw: str = ""):
        if value is None:
            failures.append(f"{label}: 未能从输出取到指标")
            print(f"  × {label:<34s} 取数失败")
            return
        ok = value >= minimum - 1e-9 if maximum is None else value <= maximum + 1e-9
        measured[name] = value
        mark = "√" if ok else "×"
        ref = f"基线 ≥{minimum:g}" if maximum is None else f"基线 ≤{maximum:g}"
        print(f"  {mark} {label:<34s} {value:g} ({ref})")
        if not ok:
            failures.append(f"{label} {value:g} 劣于基线")
            print(raw[-1500:])

    # 选择器（--only）语义：逗号与空格等价；「选了名字却一个都没匹配上」必须显式失败。
    # 历史坑：本文件 docstring 旧示例写 --only eval,calendar（逗号），而实现按空格切——整串
    # 被当成一个陌生名字，所有门被跳过却打印"全部通过"、退出码 0（假绿）。
    # 可用名字的唯一真值源 = 下面各门的调用点（want() 就地登记），不另维护清单。
    only: set[str] | None = None
    if args.only is not None:
        only = {tok.strip() for chunk in args.only for tok in chunk.split(",")}
        only = {tok for tok in only if tok}
    seen_gates: list[str] = []

    def want(name: str) -> bool:
        """段落守卫：登记可用名字（唯一真值源），并返回该段本次是否执行。"""
        if name not in seen_gates:
            seen_gates.append(name)
        return only is None or name in only

    if want("version"):
        import yishu_core
        print(f"\n[0] 版本一致性（唯一真值源 yishu_core.__version__ = {yishu_core.__version__}）")
        for rel in PORTAL_ARTIFACTS:
            if not (ROOT / rel).exists():
                print(f"  · {rel} 不存在（本地门户未构建）→ 跳过该版本门")
        vproblems = version_report()
        for v in vproblems:
            print(f"  × {v}")
        if not vproblems:
            print(f"  √ 全项目统一 v{yishu_core.__version__}，无第二处版本号")
        failures.extend(vproblems)

    if want("calendar"):
        print("\n[1] 干支历内核自检")
        rc, out = run([sys.executable, str(REPO / "core" / "yishu_core" / "calendar_check.py")])
        passed = re.search(r"自检：(\d+) 项通过，(\d+) 项失败", out)
        if passed:
            gate("calendar", float(passed.group(1)), minimum=baseline["calendar"],
                 label="自检通过项", raw=out)
        if rc != 0:
            failures.append("历法自检退出码非 0")

    if want("ordering"):
        print("\n[1.5] 爻序断言（自下而上唯一约定，P0 看门狗）")
        rc, out = run([sys.executable, "dev_tools/hexagram_check.py"])
        m = re.search(r"(\d+) 项通过，(\d+) 项失败", out)
        if m:
            gate("ordering", float(m.group(1)), minimum=baseline["ordering"],
                 label="爻序断言通过数", raw=out)
        if rc != 0:
            failures.append("爻序断言未通过")

    if want("golden"):
        # 金标准指纹：64 卦 × 3 爻型 × 时间的排盘＋思维链＋分析层逐字段快照。
        # 基线是 data/golden/digest.json（入库），所以换机器也拦得住行为漂移——
        # 以前它只活在 gitignore 的 scratch/ 里，等于只有我这台机器有看门狗。
        print("\n[1.6] 金标准指纹（行为漂移看门狗）")
        rc, out = run([sys.executable, "dev_tools/golden.py"])

        def _shape(s):
            return (re.search(r"用例 (\d+) 条", s),
                    re.search(r"机械 ([0-9a-f]{16})", s),
                    re.search(r"措辞 ([0-9a-f]{16})", s))
        n, d, w = _shape(out)
        # 形状判据的自证：正例必须三件齐，负例（argparse 用法错误那种空跑）必须不被认作通过。
        _good = "用例 288 条｜机械 f7eb04494ea54a3b｜措辞 7200af9a70d2df8f｜异常 0 条"
        _bad = "usage: golden.py [-h] [{capture,verify}] [reason]"
        if not all(_shape(_good)) or any(x for x in _shape(_bad)):
            print("  × [selftest] 形状判据失效（正例没认全／用法错误被当成通过）")
            failures.append("金标准形状判据自证不过——本节的一切结论都不可信")
        cnt = f"{n.group(1)} 例指纹" if n else "指纹（用例数未知）"
        if rc == 0 and not (n and d and w):
            # 壳退 0 却没交出可比对的形状（用例子集为 0、被改坏、或被别的报错吃掉）——
            # 这正是"空跑长得像测量"的那一类，绝不当作通过。
            print("  × 壳退出码 0 但输出形状不完整（用例／机械／措辞 三件不齐）＝不能当作通过")
            for line in out.splitlines()[:6]:
                if line.strip():
                    print("    " + line.strip())
            failures.append("金标准壳输出形状不完整（rc=0 但缺 机械/措辞 指纹行）")
        elif rc == 0:
            print(f"  √ {cnt} 机械 {d.group(1)}／措辞 {w.group(1)} 与基线一致")
        else:
            # 失败分支过去整段被 `if "指纹" in out` 挡掉——golden 壳的报红文案里没有"指纹"二字，
            # 于是本节在最需要说话的时候一声不出（只剩汇总行）。漂移摘要必须在这里逐行落地。
            print(f"  × {cnt} "
                  f"{('机械 ' + d.group(1) + ' 现在 ') if d else ''}"
                  f"{'措辞 ' + w.group(1) + ' ' if w else ''}行为已漂移，改的是不是你要改的？")
            for line in out.splitlines():
                s = line.strip()
                if s:
                    print("    " + s)
        if rc != 0:
            failures.append("金标准指纹与基线不一致")


    if want("feedback"):
        # 反馈闭环假例自检（架构评审 A2）：此前本通道「有实现、无测试、无数据」，
        # 任一处改坏（应期抽取、口径、读数、口径句接线）都不会有任何门发现。
        print("\n[1.7] 反馈闭环假例自检（落盘走临时目录，铁律二）")
        fproblems = feedback_selftest()
        for f in fproblems:
            print(f"  × {f}")
        if not fproblems:
            print("  √ 应期抽取 / 严格·宽松判定 / 读数汇总 / 口径句接线 全部通过（口径取自内核）")
        failures.extend(fproblems)
        # 第八十六批：反馈链的**两个命令行入口**此前没有任何门跑过，实测 `feedback_report.py
        # --summary` 在 cp936 控制台以 UnicodeEncodeError 崩溃（一个警示符号就退出 1）——
        # 假例自检走的是库内函数，替不了"消费者照着 README 敲的那条命令"。
        # 文档写过的命令必须按字面跑，这是本仓登记过的同一类失守（声明复核轮）。
        for cmd in (["dev_tools/feedback_report.py", "--summary"],
                    ["dev_tools/outcome.py", "list"]):
            rc, out = run([sys.executable] + cmd)
            tag = f"{cmd[0]} {' '.join(cmd[1:])}"
            if rc != 0:
                tail = (out or "").strip().splitlines()
                failures.append(f"反馈链命令 `python {tag}` 退出码 {rc}"
                                + (f"：{tail[-1][:90]}" if tail else "（无输出）"))
            else:
                print(f"  √ 反馈链命令 `python {tag}` 在当前控制台可跑（rc=0）")

    if want("coherence"):
        # 判词与自家分数同档（覆写链抬判词却不抬分数，曾产出「平吉 @ −5.33」15 例）
        print("\n[1.8] 判词↔分数同档（覆写抬档必须把分数也带进档）")
        rc, out = run([sys.executable, "dev_tools/check_verdict_coherence.py", "--selftest"])
        for line in out.splitlines():
            if line.strip():
                print("  " + line.strip())
        if rc != 0:
            failures.append("存在判词比自家得分更乐观的输出（读数自相矛盾）")

    if want("smoke"):
        print("\n[2] 分析段落产出冒烟（只验有无产出）")
        rc, out = run([sys.executable, "tests/smoke_test.py"])
        gate("smoke", measure("smoke", out), minimum=baseline["smoke"],
             label="段落有产出数", raw=out)

        # 编码不变式（第一百二十八批）：下列 CLI 实测曾在 GBK/cp936 控制台写出 **GBK 字节**
        # （narrate 首字节 0xbe、render 0xc1f9、event_logger 0xcac2、thinking_chain 0xc1f9、classical_analysis 0xa1be），
        # 而 rc 都是 0、分数与金标准指纹**全看不见**——只有"产物能否按 UTF-8 读出中文"这条行为断言拦得住退化。
        # 夹具自足（第一百七十六批）：本门此前把夹具写死在未入库的 scratch/analyze.json——第175批清理
        # gitignored 生成物后，干净工作树上实跑判红两处（rc=1，真因是**文件不存在**，不是编码），
        # 而第175批登记误归因为「既有环境问题（控制台代码页相关）」。实跑反证：按四段契约现做
        # chart→analyze 后同两条入口 rc=0、全绿。现依 §一 铁律二（自检夹具只走临时目录）由门内
        # tempfile 现做夹具——全新 clone 即可复现；构建失败即判红，**不得静默跳过**。
        import subprocess as _sp
        import tempfile as _tf

        def _utf8_with_cjk(argv):
            r = _sp.run([sys.executable] + argv, capture_output=True, cwd=str(ROOT))
            b = r.stdout or b""
            try:
                u = b.decode("utf-8")
            except UnicodeDecodeError:
                return False, r.returncode
            return any("\u4e00" <= ch <= "\u9fff" for ch in u[:400]), r.returncode

        _enc_bad = []
        with _tf.TemporaryDirectory(prefix="yi_enc_fixture_") as _td:
            _fx_chart = str(Path(_td) / "chart.json")
            _fx_analyze = str(Path(_td) / "analyze.json")
            for _fx_argv in (["scripts/chart.py", "--mode", "time", "--datetime",
                              "2026-09-18 14:30", "-o", _fx_chart],
                             ["scripts/analyze.py", _fx_chart, "-o", _fx_analyze]):
                _fx_rc, _fx_out = run([sys.executable] + _fx_argv)
                if _fx_rc != 0:
                    _enc_bad.append("临时夹具构建失败（%s rc=%s，本门拒绝在缺夹具时冒充绿）"
                                    % (_fx_argv[1], _fx_rc))
            for _nm, _argv in (("scripts/narrate.py", ["scripts/narrate.py", _fx_analyze]),
                               ("scripts/render.py", ["scripts/render.py", _fx_analyze]),
                               ("scripts/thinking_chain.py", ["scripts/thinking_chain.py"]),
                               ("scripts/classical_analysis.py", ["scripts/classical_analysis.py"]),
                               ("scripts/event_logger.py", ["scripts/event_logger.py", "list", "--limit", "1"])):
                _ok, _rc = _utf8_with_cjk(_argv)
                if _rc != 0 or not _ok:
                    _enc_bad.append(f"{_nm}（rc={_rc}，UTF-8 可解且含中文={_ok}）")
        # 判据自身的负例：GBK 字节必须被判不可解，否则这条不变式是摆设。
        try:
            "六爻纳甲".encode("gbk").decode("utf-8")
            _enc_bad.append("负例失效：GBK 字节竟能被 UTF-8 解码——判据不可信")
        except UnicodeDecodeError:
            pass
        for _e in _enc_bad:
            print(f"  × CLI 编码退化：{_e}")
        if _enc_bad:
            failures.append(f"CLI 编码退化（{len(_enc_bad)} 处：产物须为可读 UTF-8 中文）")
        else:
            print("  √ 编码不变式：5 个中文 CLI 的 stdout 均可按 UTF-8 读出中文（负例已确判不可解）")

    if want("chart_purity"):
        # 缺陷 A 回归看门狗（2026-10-09）：chart 段禁吉凶断语 + 扫描器负例自证。
        print("\n[2.2] chart 段纯净（无断语级文本；负例先自证）")
        cp = chart_purity_problems()
        for c in cp:
            print(f"  × {c}")
        if not cp:
            print("  √ chart JSON 仅卦辞/爻辞引文含吉凶字；无 advanced_analysis；负例探针可被抓到")
        failures.extend(cp)

    if want("style"):
        # 报告外观：用到的类名必须有定义。评分与金标准指纹看不见"内容对、外观散架"这一类回归。
        # （两套 CSS 合并时就散过一次：排盘报告的 .container/.cell-* 等 29 个类没了定义。）
        print("\n[2.5] 报告样式层覆盖（类名必须有定义）")
        rc, out = run([sys.executable, "dev_tools/style_check.py"])
        for line in out.splitlines():
            if line.strip():
                print("  " + line.strip())
        if rc != 0:
            failures.append("报告里有类名没定义（样式层缺规则）")

    if want("report_parity"):
        # 「算出来了但看不到」：HTML 是主交付面，某一节整节缺失时指纹与对齐分都不报警
        # （趋避建议就这么丢过一次：CSS 里 .advice-list 定义好了，无人引用）。
        print("\n[2.7] 报告面一致性（analyze 产出的节必须在 HTML 出现；负例先自证）")
        rp = report_parity_problems()
        for r in rp:
            print(f"  × {r}")
        if not rp:
            print("  √ 趋避建议/应期/判据所本 逐节逐条进入 HTML；负例探针可被抓到；无 traceback 泄漏")
        failures.extend(rp)

    if want("chain_tests"):
        rc, out = run([sys.executable, "tests/thinking_chain_tests.py"])
        _m = measure("chain_tests", out)
        _mc = re.search(PATTERNS["chain_tests"], out)
        print(f"\n[3] 思维链用例（{_mc.group(2) if _mc else '?'} 例，逐维度断言）")   # 例数不硬编，同上
        gate("chain_tests", _m, minimum=baseline["chain_tests"],
             label="用例通过数", raw=out)
        # 用例脚本「有失败」时本就 exit 1，那是报告不是崩溃；只有连汇总行都没
        # 解析出来 yet rc!=0，才是脚本挂了却被数数当成通过（旧实现完全不看 rc）。
        if rc != 0 and _m is None:
            failures.append(f"思维链用例脚本崩溃（rc={rc} 且汇总行未产出）")

    if want("regression"):
        rc, out = run([sys.executable, "tests/regression_test.py"])
        _m = measure("regression", out)
        _mt = re.search(PATTERNS["regression"], out)
        # 例数由汇总行取，绝不硬编：旧标题写死「18 例」，而实际 19 例、reg_07 独败，
        # 于是「18 例 / 通过 18」在门面上读起来像全通过——把唯一的诚实失败例抹平了。
        print(f"\n[4] 古籍回归（{_mt.group(2) if _mt else '?'} 例，用神/方向/区间三维）")
        gate("regression", _m, minimum=baseline["regression"],
             label="回归通过数", raw=out)
        _bad = re.search(r"方向不一致\(不可接受\):\s*(\[[^\]]*\])", out)
        if _bad and _bad.group(1) not in ("[]", ""):
            print(f"  注：不可接受项 {_bad.group(1)}（reg_07 系仿古自设前提，校勘记录见 regression_test 注释）")
        if rc != 0 and _m is None:
            failures.append(f"古籍回归脚本崩溃（rc={rc} 且汇总行未产出）")

    if want("eval") and not args.fast:
        print("\n[5] 古籍案例对齐分与应期判别力（非现实预测命中率）")
        for split in ("tune", "holdout"):
            m = eval_metrics(split)
            if m.get("error"):
                failures.append(f"{split} 评测未跑成")
                print(f"  × {split} 评测失败：{m['error'][:300]}")
                continue
            gate(split, m.get("avg"), minimum=baseline[split], label=f"{split} 对齐分 %")
            gate(f"{split}_top1", m.get("top1"), minimum=baseline.get(f"{split}_top1", 0.0),
                 label=f"{split} 主应期命中 %")
            if m.get("rank") is not None:
                gate(f"{split}_rank", m.get("rank"), maximum=BASELINE_MAX.get(f"{split}_rank", 99),
                     label=f"{split} 应支平均名次")

    if want("yingqi_external") or want("eval"):
        # 外部验证集：只报数、不设门槛。n 太小时设门槛只会逼人去过拟合它。
        print("\n[6] 外部验证集（未参与任何调参；只报数不设门槛）")
        _ext_notes = {
            "yingqi_holdout": "转写本，过六道自洽门",
            "wikisource_holdout": "维基文库原本，过纳甲/卦变/世应三方校验",
            "wikisource_direction": "同书有吉凶无验期（应期 N/A，只评方向）",
            # 「含時级」原为不实：evaluate._expected_unit() 把 時/时 一律
            # 归到**日池**近似判定，引擎与评分都没有时辰档（2026-10-10 核）。
            "huozhulin_holdout": "火珠林原本（验期只写到时辰，评测按日池近似）",
            "suigui_holdout": "增删卜易·随鬼入墓章真例（动墓/化墓结构）",
            "zengshan_dz_holdout": "增删卜易 dz 底本直抽（八道门＋同案去重，应期语料通道）",
        }
        # 过去这里是一张**写死的清单**：注册表里新增（或留空）一个外部集，本段一个字都不会提。
        # 实测漏报的形状：`case_splits.json` 登记着 `bushi_zhengzong_holdout`，但列表为空，
        # 既不在本段的循环里、也不在 `too_weak`（那里只记了 5 个别来源）——**空着且无人说为什么空**。
        # 改为按注册表驱动：凡 `*_holdout` / `*_direction` 一律过一遍，空集也要出声。
        try:
            import json as _json
            _reg = _json.loads((ROOT / "data/cases/case_splits.json").read_text(encoding="utf-8"))
            _ext_splits = sorted([k for k, v in _reg.items()
                                  if isinstance(v, list)
                                  and (k.endswith("_holdout") or k.endswith("_direction"))])
        except Exception as _exc:  # 读不到注册表就退回旧清单，但要把原因打出来
            print(f"  ! 读 case_splits.json 失败（退回写死清单）：{type(_exc).__name__}: {_exc}")
            _ext_splits = sorted(_ext_notes)
        for split in _ext_splits:
            note = _ext_notes.get(split, "（登记于 case_splits.json，无备注）")
            ext = eval_metrics(split)
            if ext.get("error"):
                # evaluate 对空集也走"退出码 1"这条错误路径 ⇒ 旧写法把**注册表里的空集**
                # 报成"未跑成"，读起来像坏了。本段下面本来就有 `n_case == 0` 的准确说法，
                # 只是永远进不去；这里先分清"空集"与"真跑挂"，两种都要出声但话要说对。
                try:
                    import case_runner
                    _n_reg = len(case_runner.load_ids(split))
                except Exception:
                    _n_reg = -1
                if _n_reg == 0:
                    print(f"  ! {split}：注册表内 **0 例**（空集／候选未毕业）——"
                          f"不是故障，也没有可解读的读数（成因见 case_splits.json 与采集侧 block_reason）")
                else:
                    print(f"  ! {split} 未跑成：{ext['error'][:200]}")
            elif not ext.get("avg"):
                # 分两种：真没案例，还是有案例但基准没有任何可评维度。
                # 后一种报"为空"会误导——读起来像语料没建，其实是基准缺字段。
                try:
                    import case_runner                      # scripts/ 已在 sys.path 上
                    n_case = len(case_runner.load_ids(split))
                except Exception as exc:
                    n_case = -1
                    print(f"  ! {split}：案例数取不到（{type(exc).__name__}: {exc}）"
                          f"——本行读数不可信，不能当作「集内无案例」")
                if n_case > 0:
                    print(f"  ! {split}：{n_case} 例在集，但基准无可评维度（全部 N/A，分母为 0）"
                          f"——见 [16] 案例基准自洽与 docs/CASE-LIBRARY-AUDIT.md")
                elif n_case == 0:
                    print(f"  ! {split} 集内无案例（见 docs/CASE-LIBRARY-AUDIT.md）")
            else:
                print(f"  · {split}（{note}）对齐分 {ext['avg']}% (n={ext.get('n') or 0})，"
                      f"主应期命中 {ext.get('top1') or '—'}%，应支平均名次 {ext.get('rank') or '—'}")
        print(f"    {len(_ext_splits)} 个集合都登记为**永不参与调参**的外部集；n 越小越只能当参照，"
              "别拿它当成绩，也别为过它写私有规则（扩样路线见 docs/CASE-LIBRARY-AUDIT.md「改走原本」一节与 references/source_ledger.md）")

    # [11]-[17] 引用完整性 / 书源指针 / 案例库隔离 / 引文逐字回验 / 应期信息量 / 基准与 fixture 自洽。
    # 这几道门前不存在：本轮清出来的活断链（HANDOFF、tools/*、tests/test_ming_*）
    # 全部是靠人读出来的，而不是被门拦的——写进散文的门等于没跑，故一律接进本门。
    for key, title, script in (
            ("doc_refs", "[11] 文档活引用可达性（指向不存在文件的指针）",
             "dev_tools/check_doc_refs.py"),
            ("rule_registry", "[12] 规则注册表书源指针回验（verified 不许自说自话）",
             "dev_tools/check_rule_registry.py"),
            ("case_isolation", "[13] 案例库隔离（解读路径不得触达 data/cases）",
             "dev_tools/check_case_isolation.py"),
            ("source_readings", "[14] 书证引文逐字回验（《书名》源L行号+引文，含代码注释）",
             "dev_tools/check_source_readings.py"),
            ("yingqi_info", "[15] 应期候选池信息量（铺量涨分必须被拦住）",
             "dev_tools/check_yingqi_information.py"),
            ("case_selfconsistency", "[16] 案例基准自洽（日辰/应期须出自该例自引书文）",
             "dev_tools/check_case_selfconsistency.py"),
            ("fixture_invariants", "[17] 回归 fixture 不变量（声明的干支/卦名须算得出来）",
             "dev_tools/check_fixture_invariants.py"),
            ("fangwei", "[18] 方位层回验（避乱取方／延医取方须还出书自断）",
             "dev_tools/check_fangwei.py"),
            ("split_ledger", "[19] 分片台账复核（排除理由须能被字面重跑：无卦名／同源／别源 0 锚点）",
             "dev_tools/check_split_ledger.py"),
            ("cli_encoding", "[20] CLI 编码红线（cp936 下 argparse 中文入口的产物须为可读 UTF-8）",
             "dev_tools/check_cli_encoding.py"),
            ("yingqi_scoring", "[26] 应期评分口径（无语支基准：答进日窗满分／答不进 N/A，双向都要有牙）",
             "dev_tools/check_yingqi_scoring.py"),
            ("bing_yao", "[27] 日辰并爻唯一性守卫（成并+0.5／同支≥2位退0且理由引源L125「不能成并」）",
             "dev_tools/check_bing_yao.py"),
            ("prospective", "[28] 前瞻封存判卷（事件定义/窗口先于结果冻结；哈希链拒绝事后改写；"
                            "删失/旧口径/小样本显形——现实效度通道，与古籍对齐分永不同源）",
             "dev_tools/prospective.py"),
             ("regex_lists", "[29] 正则字符类 list 展平审计（AGENTS §二 硬规矩核对版：10-13 静默全盲案首次有全库机器版）",
              "dev_tools/check_regex_lists.py")):
        if want(key):
            print(f"\n{title}")
            rc, out = run([sys.executable, script, "--selftest"])
            for line in out.splitlines():
                if line.strip():
                    print("  " + line.strip())
            if rc != 0:
                failures.append(f"{title} 未通过")

    print("\n" + "=" * 62)
    if failures:
        print("质量门未通过：")
        for f in failures:
            print(f"  · {f}")

    # 选择器自证：选了名字却没一个对上——"假绿"里最凶的一种（旧行为在此打印"全部通过"
    # 并退出 0）。一律显式失败并列出可用项；用法错误统一退出码 2。
    matched = [] if only is None else [n for n in seen_gates if n in only]
    unknown = [] if only is None else sorted(n for n in only if n not in seen_gates)
    if only is not None and (not matched or unknown):
        if not only:
            why = "`--only` 展开后为空，至少要给一个检查项"
        elif not matched:
            why = f"{sorted(only)} 里没有一个能对上的检查项"
        else:
            why = f"不认识这些检查项 {unknown}"
        print(f"\n--only 用法错误：{why}")
        if not matched:
            print("  （上面的 √ 不代表任何检查真的跑过——别把它当通过。）")
        print("  可用检查项（取自各门调用点；逗号与空格分隔等价）：")
        for i in range(0, len(seen_gates), 4):
            print("    " + "".join(f"{c:<18}" for c in seen_gates[i:i + 4]).rstrip())
        return 2

    if failures:
        return 1

    if args.raise_baseline:
        new = dict(BASELINE)
        new.update({k: v for k, v in measured.items()})
        BASELINE_FILE.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8")
        print(f"基线已抬升 → {BASELINE_FILE}")
        print(json.dumps(new, ensure_ascii=False))
        return 0

    print("质量门全部通过（或不低于基线）。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
