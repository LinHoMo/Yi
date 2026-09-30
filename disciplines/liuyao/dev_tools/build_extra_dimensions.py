# -*- coding: utf-8 -*-
"""附加评测维度基准补全器（一次性数据构建，产物入库、脚本留档可复跑）。

补六维度（只在机械可定时填，与 build_usegod_position 同一口径）：
  - expected.use_god_wangshuai（月令旺衰 旺/相/休/囚/死）：
    书面已明写用神地支（expected.use_god_branch），其五行对月建的旺衰为机械派生
    （classical_enhancements.element_strength_in_month），对表回归性质。
  - expected.use_god_muku（入日墓 / 入月墓 / 不入墓）：
    用神五行墓支（内核 TOMB_MAP）恰临日辰/月建即入墓，机械判定。
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
只填主案例集，**不填外部集**——外部集（wikisource 等）是永不调参的真检验，
不能被必然满分的自洽维度抬高（口径诚实，见 CHANGELOG 30r）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC.parents[1] / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from liuyao_engine import build_hexagram_result  # noqa: E402
from engine_chart import get_six_spirit  # noqa: E402
from classical_enhancements import element_strength_in_month  # noqa: E402
from effects import analyze_hexagram_body  # noqa: E402
from yishu_core.symbols import BRANCH_ELEMENTS, TOMB_MAP, SAN_HE_GROUPS  # noqa: E402
import case_runner as cr  # noqa: E402

CASES = DISC / "data" / "cases" / "classical_cases.json"


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

        hx = case.get("hexagram") or {}
        yao_vals = cr.hex2yao(hx.get("original"), hx.get("changed"))
        if yao_vals is None:
            counters[3] += 1
            continue
        resolved = cr.resolve_case_time(case)
        dt = resolved["dt"]
        h = build_hexagram_result(yao_vals, case.get("question", ""), "manual",
                                  dt.year, dt.month, dt.day, dt.hour)
        dtime = h.get("divination_time") or {}
        month_sb, day_sb = dtime.get("month_stem_branch", ""), dtime.get("day_stem_branch", "")
        month_br, day_br, day_stem = month_sb[1:], day_sb[1:], day_sb[:1]

        # 月令旺衰 + 墓库：依赖书面用神地支
        ug_elem = BRANCH_ELEMENTS.get(branch or "", "")
        if branch and ug_elem and month_br:
            month_elem = BRANCH_ELEMENTS.get(month_br, "")
            if month_elem and not exp.get("use_god_wangshuai"):
                exp["use_god_wangshuai"] = element_strength_in_month(ug_elem, month_elem)
                exp.setdefault("use_god_wangshuai_basis",
                               f"机械派生：用神{branch}({ug_elem})临{month_br}({month_elem})月")
                counters[0] += 1
                changed = True
            if month_elem and not exp.get("use_god_muku"):
                tomb_of = TOMB_MAP.get(ug_elem, "")
                hits = [tag for tag, br in (("入日墓", day_br), ("入月墓", month_br))
                        if tomb_of and tomb_of == br]
                exp["use_god_muku"] = "、".join(hits) if hits else "不入墓"
                exp.setdefault("use_god_muku_basis",
                               f"机械判定：{ug_elem}墓在{tomb_of}，日{day_br}/月{month_br}")
                counters[1] += 1
                changed = True

        # 六神临用：依赖纳甲唯一爻位 + 日干
        if position and day_stem and not exp.get("use_god_six_spirit"):
            exp["use_god_six_spirit"] = get_six_spirit(day_stem, int(position))
            exp.setdefault("use_god_six_spirit_basis",
                           f"机械派生：{day_stem}日{position}爻按六神起例")
            counters[2] += 1
            changed = True

        # ── 卦身/三合：仅主案例集（无古籍案例锚点，对通则对表；外部集不填防口径膨胀）──
        if self_consistent:
            if not exp.get("gua_shen_branch"):
                body = analyze_hexagram_body(h)
                gsb = body.get("body_branch")
                if gsb:
                    exp["gua_shen_branch"] = gsb
                    exp.setdefault(
                        "gua_shen_branch_basis",
                        f"机械派生：{h['original_hexagram'].get('generation','')}"
                        f"→卦身{gsb}支")
                    counters[4] += 1
                    changed = True
            if not exp.get("sanhe_full_combo"):
                hex_branches = {y.get("earthly_branch")
                                for y in h["original_hexagram"]["yao_lines"]}
                full_combo = god_combo = ""
                for _elem, grp in SAN_HE_GROUPS.items():
                    if set(grp) <= hex_branches:
                        full_combo = "".join(grp)
                        if branch in grp:
                            god_combo = "".join(grp)
                        break
                exp["sanhe_full_combo"] = full_combo or "无"
                exp.setdefault("sanhe_full_combo_basis", "机械判定：本卦纳甲支集合")
                exp["use_god_in_sanhe"] = god_combo or "无"
                exp.setdefault("use_god_in_sanhe_basis",
                               f"机械判定：书面用神{branch or '?'}是否入三合")
                counters[5] += 1
                counters[6] += 1
                changed = True

    # 保留各文件原有缩进（主案例集 indent=1，外部集 indent=2）与末尾换行；无改动不写回
    if changed:
        path.write_text(json.dumps(store, ensure_ascii=False, indent=indent) + "\n",
                        encoding="utf-8")
    return changed


def main() -> int:
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
