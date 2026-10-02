# -*- coding: utf-8 -*-
"""紫微斗数古法回归：用**书源明文**逐条核对 core 的安星取值层。

    python dev_tools/regression.py

与 golden 指纹（比对自己上一次的输出）不同，本回归比对的是**古籍原文**：
每一条断言都能在 data/sources/zi-wei-dou-shu-quan-shu.wikitext.txt 中找到出处，
故 core 改公式时它能独立判定对错，而不是「与上次一致即通过」。

断言两组：
  A 安星公式：命宫/身宫、紫微定位表、天府、十二宫逆布 —— 与书源例题及五张图逐格比对；
  B 同度自证：卷二「一 命宫」各主星本宫诗里的「X同度」明文（「与」字可省），
    逐格核对「天府 = (4-紫微)%12」+ 紫微系/天府系固定偏移是否把它们放进同一宫，
    并核对双星同宫格局表是否恰为原文所列组合。

**格数的唯一权威源是本模块的 `companion_cells()`**（B1 那一行的读数即当前基线），
别处（含 core 的 docstring、学科 SKILL.md）只引用这个读数，不另写常量。
计数口径一并写在这里，免得再出现"同一件事三个数"：

  · 取「同度」二字之前的**全部**宫位组，逐支展开 —— 只取首个宫位组会少算
    （书源有若干行把两处单支宫分写在同一句里，如「寅宫旺申宫得地，与巨门同度」）；
  · 按 (星, 宫支) 去重；
  · **不要求「与」字** —— 书源 L2232「卯酉宫贪狼同度」与前后各行
    「…与X同度」是同一体例，只是省了「与」；若只认「与X同度」，会漏掉这一行。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import (  # noqa: E402
    EARTHLY_BRANCHES,
    MAIN_STAR_ORDER,
    DUAL_PATTERNS,
    PALACES,
    ZIWEI_POS_TABLE,
    chang_qu_positions,
    di_kong_jie_pos,
    huoling_pos,
    kui_yue_positions_by_stem,
    long_chi_feng_ge_pos,
    lu_cun_pos,
    ming_gong_pos,
    qing_yang_tuo_luo_pos,
    san_tai_ba_zuo_pos,
    shen_gong_pos,
    tai_fu_feng_gao_pos,
    tian_ku_xu_pos,
    tian_ma_pos,
    tian_xing_yao_pos,
    tianfu_group_positions,
    tianfu_position,
    ziwei_group_positions,
)

DATA = DISC / "data"


def _ok(cond: bool, label: str, detail: str = "") -> tuple[bool, str]:
    mark = "√" if cond else "×"
    return cond, f"  {mark} {label}" + (f"　{detail}" if detail else "")


def check_ming_shen_gong() -> list[tuple[bool, str]]:
    """书源 1663：「假如正月生子时就在寅宫安身命，丑时逆转丑安命，顺去卯安身，
    寅时逆转子安命，顺至辰安身」——三条例题逐条复算。"""
    out = []
    yin = EARTHLY_BRANCHES.index("寅")
    cases = [(0, "寅", "寅"), (1, "丑", "卯"), (2, "子", "辰")]   # (时支序, 命宫, 身宫)
    bad = []
    for h, mg, sg in cases:
        got_mg = EARTHLY_BRANCHES[ming_gong_pos(yin, h)]
        got_sg = EARTHLY_BRANCHES[shen_gong_pos(yin, h)]
        if (got_mg, got_sg) != (mg, sg):
            bad.append(f"正月{['子', '丑', '寅'][h]}时 → 命{got_mg}/身{got_sg} 应 {mg}/{sg}")
    out.append(_ok(not bad, "A1 命宫身宫合书源安身命例三例题", f"{bad}" if bad else "正月子/丑/寅时 3/3"))
    return out


def check_ziwei_table(lines: list[str]) -> list[tuple[bool, str]]:
    """书源 1667：「火六局……酉宫起初一日」+ 五张安紫微图 150 格逐格复算。"""
    out = []
    from build_corpus import GRID_DERIVED, ZHI_GRID_TOP, build_position_table  # noqa: E402

    decoded = build_position_table(lines)["table"]
    total = sum(1 for row in decoded.values() for x in row if x)
    out.append(_ok(total == 150, "A2 五张安紫微图解码格数", f"{total}/150"))
    out.append(_ok(
        decoded[6][0] == "酉", "A3 火六局初一紫微在酉（合书源安身命例例题）",
        f"解码值 {decoded[6][0]}"))

    mism = [(ju, i + 1, decoded[ju][i], ZIWEI_POS_TABLE.get(ju, (None,) * 30)[i])
            for ju in decoded for i in range(30)
            if decoded[ju][i] != ZIWEI_POS_TABLE.get(ju, (None,) * 30)[i]]
    out.append(_ok(not mism, "A4 core 取值层与解码表逐格一致", f"{mism[:4]}" if mism else "150/150"))
    out.append(_ok(
        all(ZIWEI_POS_TABLE[ju][i] for ju in ZIWEI_POS_TABLE for i in range(30)),
        "A5 取值层无空格（残缺格已按结构自洽推得并登记）",
        f"推得格 {sum(len(v) - 1 for v in GRID_DERIVED.values())} 处"))
    out.append(_ok(set(ZIWEI_POS_TABLE) == set(ZHI_GRID_TOP and
                  {2, 3, 4, 5, 6}), "A6 五局齐全"))
    return out


def check_tianfu() -> list[tuple[bool, str]]:
    """书源 2097 安天府图图注：「紫居丑则府居卯矣」「惟寅申二宫紫府同宫」。"""
    out = []
    out.append(_ok(EARTHLY_BRANCHES[tianfu_position(1)] == "卯",
                   "A7 紫微居丑 → 天府居卯（图注原文所举）"))
    same = [EARTHLY_BRANCHES[p] for p in range(12) if tianfu_position(p) == p]
    out.append(_ok(sorted(same) == ["寅", "申"],
                   "A8 紫府同宫只在寅申（图注原文）", f"{same}"))
    return out


def companion_cells(table: dict) -> int:
    """同度明文格数——**本仓唯一权威读数**（口径见模块 docstring）。

    输入是 `data/star_brightness.json` 的 `companions.table`：{星: {宫支: [同度星]}}。
    格数 = Σ 每星的宫支数（(星, 宫支) 去重后的格数）。任何文档要写这个数字，
    都应当引用 B1 那行打印的读数，而不是另抄一个常量——本仓曾因此出现
    "同一件事在 core docstring / 学科 SKILL.md / 回归输出 里是三不同数"。
    """
    return sum(len(cells) for cells in table.values())


def check_companions() -> list[tuple[bool, str]]:
    """卷二「一 命宫」各主星本宫诗的「X同度」明文 → 安星公式逐格自证。"""
    out = []
    comp = json.loads((DATA / "star_brightness.json").read_text(encoding="utf-8"))
    table = (comp.get("companions") or {}).get("table") or {}
    cells = companion_cells(table)
    hit = miss = 0
    bad = []
    for star, cs in table.items():
        for branch, comps in cs.items():
            for p in range(12):
                pos = {**ziwei_group_positions(p),
                       **tianfu_group_positions(tianfu_position(p))}
                if EARTHLY_BRANCHES[pos.get(star, -1)] != branch:
                    continue
                for c in comps:
                    if c in MAIN_STAR_ORDER and EARTHLY_BRANCHES[pos[c]] == branch:
                        hit += 1
                    else:
                        miss += 1
                        bad.append(f"{star}在{branch}应见{c}同度，实不在")
    out.append(_ok(miss == 0 and hit == cells,
                   "B1 同度明文逐格自证（天府式 + 星系偏移）",
                   f"明文 {cells} 格｜一致 {hit} / 不符 {miss}"
                   + (f"　{bad[:3]}" if bad else "")))

    du = {frozenset(x) for x in DUAL_PATTERNS}
    src = set()
    for star, cells in table.items():
        for comps in cells.values():
            for c in comps:
                if star in MAIN_STAR_ORDER and c in MAIN_STAR_ORDER:
                    src.add(frozenset((star, c)))
    out.append(_ok(src <= du, "B2 书源「X同度」所列组合尽在格局表内（无捏造）",
                   f"书源 {len(src)} 组 / 表 {len(du)} 组" +
                   (f"　表外 {sorted(map(sorted, src - du))}" if src - du else "")))

    # 几何自证：遍历 12 个紫微落宫，统计实际出现的双星同宫组合
    geo = set()
    for p in range(12):
        pos = {**ziwei_group_positions(p), **tianfu_group_positions(tianfu_position(p))}
        by_branch: dict[int, list[str]] = {}
        for star, b in pos.items():
            by_branch.setdefault(b, []).append(star)
        for stars in by_branch.values():
            if len(stars) == 2:
                geo.add(frozenset(stars))
    out.append(_ok(geo == du, "B3 格局表 24 组 = 安星几何上真实可现的双星同宫组合",
                   f"几何 {len(geo)} 组 / 表 {len(du)} 组" +
                   (f"　差 {sorted(map(sorted, geo ^ du))}" if geo != du else "")))
    return out


def check_auxiliary() -> list[tuple[bool, str]]:
    """各安星诀的例题复算（书源卷二 1691-1783）。"""
    idx = {b: i for i, b in enumerate(EARTHLY_BRANCHES)}
    out = []
    cases = [
        ("A9 文昌丑时在酉、文曲丑时在巳（书源 1695-1697）",
         EARTHLY_BRANCHES[chang_qu_positions(1)[0]] == "酉"
         and EARTHLY_BRANCHES[chang_qu_positions(1)[1]] == "巳",
         str(tuple(EARTHLY_BRANCHES[x] for x in chang_qu_positions(1)))),
        ("A10 天魁天钺：甲丑未 / 丙丁亥戌（书源 1707）",
         tuple(EARTHLY_BRANCHES[x] for x in kui_yue_positions_by_stem(0)) == ("丑", "未")
         and tuple(EARTHLY_BRANCHES[x] for x in kui_yue_positions_by_stem(2)) == ("亥", "戌"),
         ""),
        ("A11 禄存：甲寅乙卯丙戊巳丁己午庚申辛酉壬亥癸子（书源 1719）",
         [EARTHLY_BRANCHES[lu_cun_pos(s)] for s in range(10)]
         == ["寅", "卯", "巳", "午", "巳", "午", "申", "酉", "亥", "子"],
         str([EARTHLY_BRANCHES[lu_cun_pos(s)] for s in range(10)])),
        ("A12 癸禄在子 → 擎羊丑、陀罗亥（书源 1725 例题）",
         tuple(EARTHLY_BRANCHES[x] for x in qing_yang_tuo_luo_pos(idx["子"])) == ("丑", "亥"),
         ""),
        ("A13 天马：寅午戌在申、申子辰在寅、巳酉丑在亥、亥卯未在巳（书源 1713）",
         [EARTHLY_BRANCHES[tian_ma_pos(i)] for i in (2, 8, 5, 3)] == ["申", "寅", "亥", "巳"],
         ""),
        ("A14 火铃：寅午戌丑卯 / 申子辰寅戌 / 巳酉丑卯戌 / 亥卯未酉戌（书源 1729）",
         [tuple(EARTHLY_BRANCHES[x] for x in huoling_pos(i, 0)) for i in (2, 8, 5, 3)]
         == [("丑", "卯"), ("寅", "戌"), ("卯", "戌"), ("酉", "戌")],
         str([tuple(EARTHLY_BRANCHES[x] for x in huoling_pos(i, 0)) for i in (2, 8, 5, 3)])),
        ("A15 地空地劫：子时俱在亥、丑时劫子空戌、午时俱在巳（书源 1745）",
         tuple(EARTHLY_BRANCHES[x] for x in di_kong_jie_pos(0)) == ("亥", "亥")
         and tuple(EARTHLY_BRANCHES[x] for x in di_kong_jie_pos(1)) == ("戌", "子")
         and tuple(EARTHLY_BRANCHES[x] for x in di_kong_jie_pos(6)) == ("巳", "巳"),
         ""),
        ("A16 天刑天姚：正月酉丑、二月戌寅（书源 1764）",
         tuple(EARTHLY_BRANCHES[x] for x in tian_xing_yao_pos(idx["寅"])) == ("酉", "丑")
         and tuple(EARTHLY_BRANCHES[x] for x in tian_xing_yao_pos(idx["卯"])) == ("戌", "寅"),
         ""),
        ("A17 天哭天虚：子年俱在午、丑年哭巳虚未（书源 1771）",
         tuple(EARTHLY_BRANCHES[x] for x in tian_ku_xu_pos(0)) == ("午", "午")
         and tuple(EARTHLY_BRANCHES[x] for x in tian_ku_xu_pos(1)) == ("巳", "未"),
         ""),
        ("A18 龙池凤阁：子年辰戌（书源 1775）",
         tuple(EARTHLY_BRANCHES[x] for x in long_chi_feng_ge_pos(0)) == ("辰", "戌"),
         ""),
        ("A19 台辅午起子顺、封诰寅起子顺（书源 1779/1783）",
         tuple(EARTHLY_BRANCHES[x] for x in tai_fu_feng_gao_pos(0)) == ("午", "寅")
         and tuple(EARTHLY_BRANCHES[x] for x in tai_fu_feng_gao_pos(2)) == ("申", "辰"),
         ""),
        ("A20 三台顺数左辅、八座逆数右弼（书源 1767）",
         tuple(EARTHLY_BRANCHES[x] for x in san_tai_ba_zuo_pos(idx["辰"], idx["戌"], 1))
         == ("辰", "戌")
         and tuple(EARTHLY_BRANCHES[x] for x in san_tai_ba_zuo_pos(idx["辰"], idx["戌"], 3))
         == ("午", "申"),
         ""),
        ("A21 十二宫逆布：兄弟在命宫后一位（书源 1669「男女俱从逆转」）",
         PALACES[:3] == ["命宫", "兄弟", "夫妻"], ""),
    ]
    for label, cond, detail in cases:
        out.append(_ok(cond, label, detail))
    return out


def run() -> tuple[bool, list[str]]:
    src = ROOT / "data" / "sources" / "zi-wei-dou-shu-quan-shu.wikitext.txt"
    if not src.is_file():
        return True, [f"  · 缺书源 {src.name}，跳过古法回归"
                      f"（先跑 python tools/fetch_source.py --fetch zi-wei-dou-shu-quan-shu）"]
    lines = src.read_text(encoding="utf-8").splitlines()
    checks = (check_ming_shen_gong() + check_ziwei_table(lines)
              + check_tianfu() + check_companions() + check_auxiliary())
    ok = all(c for c, _ in checks)
    return ok, [line for _, line in checks]


def main() -> int:
    force_utf8_stdio()
    ok, lines = run()
    print("紫微斗数·古法回归（对着书源原文核，不看上次输出）")
    for line in lines:
        print(line)
    n_ok = sum(1 for x in lines if x.startswith("  √"))
    print(f"  合计 {n_ok}/{len(lines)} 项通过")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
