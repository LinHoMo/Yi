# -*- coding: utf-8 -*-
"""附加评测维度基准补全器（一次性数据构建，产物入库、脚本留档可复跑）。

补六维度（只在机械可定时填，与 build_usegod_position 同一口径）：
  - expected.use_god_wangshuai（月令旺衰 旺/相/休/囚/死）：
    书面已明写用神地支（expected.use_god_branch），其五行对月建的旺衰为机械派生
    （classical_enhancements.element_strength_in_month），对表回归性质。
  - expected.use_god_muku（入日墓 / 入月墓 / 动墓 / 化墓 任意组合，无则「不入墓」）：
    用神五行墓支（内核 TOMB_MAP）恰临日辰/月建即入墓；另有动爻地支即用神墓支
    为「动墓」，用神发动而化出墓支为「化墓」。判据唯一实现在
    classical_enhancements.use_god_tomb_tags（与 case_runner 同源，禁各写一份）。
  - expected.use_god_six_spirit（六神临用）：
    书面用神爻位已由纳甲唯一确定（expected.use_god_position，30o 批），
    六神由日干 + 爻位按起例表机械派生（engine_chart.get_six_spirit）。
  - expected.gua_shen_branch（卦身支，仅主案例集）：世爻阴阳 + 世爻位按
    《卜筮正宗》安月卦身诀机械派生（effects.analyze_hexagram_body 唯一实现）。
  - expected.sanhe_full_combo / expected.use_god_in_sanhe（三合局，仅主案例集）：
    本卦六爻纳甲支是否含完整三合组（内核 SAN_HE_GROUPS）；书面用神支是否入局。

数据源：月将/日辰由案例时间还原（case_runner.resolve_case_time）后经
build_hexagram_result 排出，与引擎跑同一案例同源——故本批为**对表回归**，
衡量「取用神 → 定爻位/旺衰/墓库/六神/卦身/三合」派生链路的自洽，非泛化证据。

卦身/三合无古籍案例锚点（案例原文不写卦身、几乎不写三合），属「对通则对表」；
只填主案例集，**不填外部集**——外部集（wikisource 等）已于 181–309 批参与调参，
不能被必然满分的自洽维度抬高（口径诚实，见 CHANGELOG 30r）。
"""
from __future__ import annotations

import argparse
import json
import sys

# 控制台编码守卫：GBK/cp936 控制台下本器的中文输出会退化成乱码甚至 UnicodeEncodeError
# （rc 仍为 0、金标准看不见，只有这条守卫管得住）。判据见 dev_tools/check.py 的编码不变式。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
# 第五百零八批升格：classical 族在 <学科根>/engine/classical/；学科根本身供 `import engine` 解析
for _p in (str(DISC / "engine" / "classical"), str(DISC / "scripts"), str(DISC / "core"), str(DISC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine import build_hexagram_result  # noqa: E402
from engine_chart import get_six_spirit  # noqa: E402
from classical_enhancements import element_strength_in_month, use_god_tomb_tags  # noqa: E402
from effects import analyze_hexagram_body  # noqa: E402
from yishu_core.symbols import BRANCH_ELEMENTS, SAN_HE_GROUPS  # noqa: E402
import case_runner as cr  # noqa: E402

CASES = DISC / "data" / "cases" / "classical_cases.json"


def _derive(case: dict) -> dict:
    """由案例重派生六维度（与落盘填充同一派生链），返回各字段规范值。

    无基准（无用神地支/爻位、装卦失败、时点不可还原）时返回空值，调用方据此跳过。
    """
    out = {"wang": None, "wang_basis": "", "muku_label": None, "muku_basis": "",
           "six": None, "six_basis": "", "gsb": None, "gsb_basis": "",
           "sanhe_full": None, "sanhe_god": None,
           "sanhe_full_basis": "机械判定：本卦纳甲支集合",
           "sanhe_god_basis": ""}
    exp = case.get("expected") or {}
    branch = exp.get("use_god_branch")
    position = exp.get("use_god_position")
    if not branch and not position:
        return out
    hx = case.get("hexagram") or {}
    yao_vals = cr.hex2yao(hx.get("original"), hx.get("changed"))
    if yao_vals is None:
        return out
    try:
        resolved = cr.resolve_case_time(case)
        dt = resolved["dt"]
        h = build_hexagram_result(yao_vals, case.get("question", ""), "manual",
                                  dt.year, dt.month, dt.day, dt.hour)
    except Exception:
        return out
    dtime = h.get("divination_time") or {}
    month_sb, day_sb = dtime.get("month_stem_branch", ""), dtime.get("day_stem_branch", "")
    month_br, day_br, day_stem = month_sb[1:], day_sb[1:], day_sb[:1]
    ug_elem = BRANCH_ELEMENTS.get(branch or "", "")
    if branch and ug_elem and month_br:
        month_elem = BRANCH_ELEMENTS.get(month_br, "")
        if month_elem:
            out["wang"] = element_strength_in_month(ug_elem, month_elem)
            out["wang_basis"] = f"机械派生：用神{branch}({ug_elem})临{month_br}({month_elem})月"
            muku = use_god_tomb_tags(
                h["original_hexagram"]["yao_lines"], branch, position, day_br, month_br)
            out["muku_label"] = muku["label"]
            out["muku_basis"] = (f"机械判定：{ug_elem}墓在{muku['tomb_branch']}，"
                                 f"日{day_br}/月{month_br}，动墓/化墓另核动爻")
    if position and day_stem:
        out["six"] = get_six_spirit(day_stem, int(position))
        out["six_basis"] = f"机械派生：{day_stem}日{position}爻按六神起例"
    body = analyze_hexagram_body(h)
    out["gsb"] = body.get("body_branch")
    if out["gsb"]:
        out["gsb_basis"] = (f"机械派生：{h['original_hexagram'].get('generation', '')}"
                            f"→卦身{out['gsb']}支")
    hex_branches = {y.get("earthly_branch") for y in h["original_hexagram"]["yao_lines"]}
    full_combo = god_combo = ""
    for _elem, grp in SAN_HE_GROUPS.items():
        if set(grp) <= hex_branches:
            full_combo = "".join(grp)
            if branch in grp:
                god_combo = "".join(grp)
            break
    out["sanhe_full"] = full_combo or "无"
    out["sanhe_god"] = god_combo or "无"
    out["sanhe_god_basis"] = f"机械判定：书面用神{branch or '?'}是否入三合"
    return out


def _build_file(path: Path, counters: list, indent: int, self_consistent: bool = False) -> bool:
    store = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for case in store.get("cases", []):
        exp = case.get("expected") or {}
        branch = exp.get("use_god_branch")
        position = exp.get("use_god_position")
        if not branch and not position:
            counters[3] += 1
            continue
        d = _derive(case)
        # 月令旺衰
        if d["wang"] and not exp.get("use_god_wangshuai"):
            exp["use_god_wangshuai"] = d["wang"]
            exp.setdefault("use_god_wangshuai_basis", d["wang_basis"])
            counters[0] += 1
            changed = True
        # 墓库：日墓/月墓/动墓/化墓四类，判据唯一实现在 classical_enhancements。
        # 每次重建（规则升级后旧值须刷新），故不用 setdefault。
        if d["muku_label"] is not None and (
                exp.get("use_god_muku") != d["muku_label"]
                or exp.get("use_god_muku_basis") != d["muku_basis"]):
            exp["use_god_muku"] = d["muku_label"]
            exp["use_god_muku_basis"] = d["muku_basis"]
            counters[1] += 1
            changed = True
        # 六神临用：依赖纳甲唯一爻位 + 日干
        if d["six"] and not exp.get("use_god_six_spirit"):
            exp["use_god_six_spirit"] = d["six"]
            exp.setdefault("use_god_six_spirit_basis", d["six_basis"])
            counters[2] += 1
            changed = True
        # 卦身/三合：仅主案例集（无古籍案例锚点，对通则对表；外部集不填防口径膨胀）
        if self_consistent:
            if d["gsb"] and not exp.get("gua_shen_branch"):
                exp["gua_shen_branch"] = d["gsb"]
                exp.setdefault("gua_shen_branch_basis", d["gsb_basis"])
                counters[4] += 1
                changed = True
            if d["sanhe_full"] is not None and not exp.get("sanhe_full_combo"):
                exp["sanhe_full_combo"] = d["sanhe_full"]
                exp.setdefault("sanhe_full_combo_basis", d["sanhe_full_basis"])
                exp["use_god_in_sanhe"] = d["sanhe_god"]
                exp.setdefault("use_god_in_sanhe_basis", d["sanhe_god_basis"])
                counters[5] += 1
                counters[6] += 1
                changed = True
    # 保留各文件原有缩进（主案例集 indent=1，外部集 indent=2）与末尾换行；无改动不写回
    if changed:
        path.write_text(json.dumps(store, ensure_ascii=False, indent=indent) + "\n",
                        encoding="utf-8")
    return changed


def _verify_file(path: Path) -> list:
    """逐案例重派生六维度，与已落盘字段比对；只标「有值但不一致」（引擎升版致陈旧），
    空字段（尚未填充）不计为失效。"""
    if not path.exists():
        return []
    store = json.loads(path.read_text(encoding="utf-8"))
    mm = []
    for case in store.get("cases", []):
        exp = case.get("expected") or {}
        if not exp.get("use_god_branch") and not exp.get("use_god_position"):
            continue
        d = _derive(case)
        cid = case.get("id", path.name)
        if d["wang"] is not None and exp.get("use_god_wangshuai") not in (None, ""):
            if exp.get("use_god_wangshuai") != d["wang"]:
                mm.append(f"{cid}: use_god_wangshuai={exp.get('use_god_wangshuai')} ≠ 引擎派生 {d['wang']}")
        if d["muku_label"] is not None and exp.get("use_god_muku") not in (None, ""):
            if exp.get("use_god_muku") != d["muku_label"] or exp.get("use_god_muku_basis") != d["muku_basis"]:
                mm.append(f"{cid}: use_god_muku 与引擎派生不一致")
        if d["six"] and exp.get("use_god_six_spirit") not in (None, ""):
            if exp.get("use_god_six_spirit") != d["six"]:
                mm.append(f"{cid}: use_god_six_spirit={exp.get('use_god_six_spirit')} ≠ 引擎派生 {d['six']}")
        if d["gsb"] and exp.get("gua_shen_branch") not in (None, ""):
            if exp.get("gua_shen_branch") != d["gsb"]:
                mm.append(f"{cid}: gua_shen_branch={exp.get('gua_shen_branch')} ≠ 引擎派生 {d['gsb']}")
        if d["sanhe_full"] is not None and exp.get("sanhe_full_combo") not in (None, ""):
            if exp.get("sanhe_full_combo") != d["sanhe_full"] or exp.get("use_god_in_sanhe") != d["sanhe_god"]:
                mm.append(f"{cid}: 三合维度与引擎派生不一致")
    return mm


def _check_sync() -> int:
    """同源复验：派生维度（旺衰/墓库/六神/卦身/三合）须与引擎当前派生一致。"""
    others = [p for p in sorted(CASES.parent.glob("*_cases.json")) if p.name != CASES.name]
    mm = []
    for path in [CASES] + others:
        mm.extend(_verify_file(path))
    print("派生维度同源复验：%d 处字段与引擎不一致" % len(mm))
    for m in mm:
        print("  ×", m)
    return 1 if mm else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="附加评测维度基准补全器")
    ap.add_argument("--check", action="store_true",
                    help="只复验已生成的派生维度与引擎一致，不写文件（[46] 同步门挂此）")
    args = ap.parse_args()
    if args.check:
        return _check_sync()
    # 主案例集 + 全部外部集（外部 split 永不调参，补入后即外部对表检验）
    others = [p for p in sorted(CASES.parent.glob("*_cases.json")) if p.name != CASES.name]
    counters = [0, 0, 0, 0, 0, 0, 0]  # 旺衰/墓库/六神/无基准/卦身/三合/用神入三合
    _build_file(CASES, counters, indent=1, self_consistent=True)
    for path in others:
        _build_file(path, counters, indent=2)
    print(f"旺衰 {counters[0]}｜墓库 {counters[1]}｜六神 {counters[2]}｜无基准跳过 {counters[3]}｜"
          f"卦身 {counters[4]}｜三合 {counters[5]}｜用神入三合 {counters[6]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
