# -*- coding: utf-8 -*-
"""紫微斗数因子推演（analyze 段）—— 机械格局/四化/大限，不写命运断语。

推演规则（全部机械可执行，lookup 表）：
  - 命宫主星 → 格局（PATTERNS 表 lookup）
  - 四化入宫 → 吉凶方向（data/verdicts.json#方向说明 查表 + 命宫三方四正判定）
  - 大限 → 起运年龄 = 局数，每十年一宫；起宫与方向依卷二「安大限诀」
  - 古法格局 → 卷二定富/贵/贫贱/杂局中机械可判者（data/geju_rules.json 判据）
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(CORE), str(Path(__file__).resolve().parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.ziwei_tables import (  # noqa: E402
    EARTHLY_BRANCHES,
    PALACES,
    PATTERNS,
    dayun_start_age,
    dayun_step_years,
)

_VERDICTS_CACHE: dict | None = None
_CORPUS_CACHE: dict[str, dict] = {}


def _load_verdicts() -> dict:
    """读 data/verdicts.json（结论措辞唯一真值源）；缓存避免每局重读。"""
    global _VERDICTS_CACHE
    if _VERDICTS_CACHE is None:
        with open(Path(__file__).resolve().parent.parent / "data" / "verdicts.json",
                  encoding="utf-8") as fh:
            _VERDICTS_CACHE = json.load(fh)
    return _VERDICTS_CACHE


def _load_corpus(name: str) -> dict:
    """读 data/<name>（build_corpus.py 从《紫微斗數全書》机械提取的引文层）。"""
    if name not in _CORPUS_CACHE:
        path = Path(__file__).resolve().parent.parent / "data" / name
        _CORPUS_CACHE[name] = (json.loads(path.read_text(encoding="utf-8"))
                              if path.is_file() else {})
    return _CORPUS_CACHE[name]


def _stem_yinyang(stem: str) -> str:
    """天干阴阳：甲丙戊庚壬 = 阳，乙丁己辛癸 = 阴。"""
    yang = "甲丙戊庚壬"
    return "阳" if stem in yang else "阴"


def identify_pattern(ming_stars: list[str]) -> tuple[str, str]:
    """命宫主星 → 格局名（lookup）。

    匹配优先级：两颗同宫组合 > 单星名称 > '命宫无主星'。
    返回 (格局名, basis 说明)。
    """
    if not ming_stars:
        return "命宫无主星", "命宫无主星，借对宫星曜"
    # 尝试两两组合
    for i in range(len(ming_stars)):
        for j in range(i + 1, len(ming_stars)):
            combo = ming_stars[i] + ming_stars[j]
            if combo in PATTERNS:
                return PATTERNS[combo], f"命宫主星 {ming_stars[i]}、{ming_stars[j]}"
    # 单星
    for s in ming_stars:
        if s in PATTERNS:
            return PATTERNS[s], f"命宫主星 {s}"
    return "未入榜格局", f"命宫主星 {'、'.join(ming_stars)}"


def sihua_impact(sihua_list: list[dict]) -> list[str]:
    """四化星 → 影响标签列表（机械：星+四化+入宫 → 描述）。"""
    impacts = []
    for item in sihua_list:
        dtype = item.get("type", "")
        star = item.get("star", "")
        palace = item.get("palace", "?")
        direction = item.get("direction", "平")
        if dtype and star and palace:
            impacts.append(f"{direction}：{star}{dtype}入{palace}")
    return impacts


def dayun_table(ju: int, ming_gong_idx: int, gender: str, year_stem: str) -> list[dict]:
    """大限排法（机械）。

    起运年龄 = 五行局；每步跨一宫、共十年。
    方向与**起宫**依卷二「安大限诀」原文：
      「阳男阴女从命前一宫起顺行 是父母宫。阴男阳女从命后一宫起逆行 是兄弟宫」
    → 顺行第一限在父母宫（宫位序 = 命宫前一宫），逆行第一限在兄弟宫。
    """
    start = dayun_start_age(ju)
    step = dayun_step_years()
    male = gender == "男"
    stem_yy = _stem_yinyang(year_stem)
    forward = (male and stem_yy == "阳") or (not male and stem_yy == "阴")

    # 十二宫自命宫起**逆行**铺在十二支上：兄弟 = 命宫 -1，父母 = 命宫 +1
    first = (ming_gong_idx + 1) % 12 if forward else (ming_gong_idx - 1) % 12

    table = []
    for i in range(12):
        age_start = start + i * step
        age_end = age_start + step - 1
        palace_off = (first + i) % 12 if forward else (first - i) % 12
        table.append({
            "step": i + 1,
            "start_age": age_start,
            "end_age": age_end,
            "palace_idx": palace_off,
            "palace": PALACES[(ming_gong_idx - palace_off) % 12],
            "direction": "顺行" if forward else "逆行",
        })
    return table


def _star_branch_map(palaces: dict) -> dict[int, set[str]]:
    """宫支序 → 该宫全部星（主星 + 辅星）；供「夹拱」类格局机械判定。"""
    out: dict[int, set[str]] = {}
    for p in palaces.values():
        br = p.get("branch")
        if not br or br not in EARTHLY_BRANCHES:
            continue
        idx = EARTHLY_BRANCHES.index(br)
        out.setdefault(idx, set()).update(p.get("main_stars") or [])
        out.setdefault(idx, set()).update(p.get("aux_stars") or [])
    return out


def _jiao(by_branch: dict[int, set[str]], idx: int, s1: str, s2: str) -> bool:
    """idx 宫的前后邻宫是否**分别**坐着 s1 与 s2（次序不论）——「来夹」。"""
    a = by_branch.get((idx + 1) % 12, set())
    b = by_branch.get((idx - 1) % 12, set())
    return (s1 in a and s2 in b) or (s2 in a and s1 in b)


def judge_classical_patterns(chart_json: dict) -> list[dict]:
    """卷一「定富局/定贵局」里**机械可判**者逐条判定（14 条）。

    只判原文给出**单一可执行结构条件**、且本引擎安星结果足以判定的条目；
    其余（判据作「见前批注」者、倚赖小限/流年/四化特殊结构者）不判，也不臆测——宁缺勿滥。
    判据原文逐条取自 data/geju_rules.json（书源逐字），此处只写判定式。

    **只收富局/贵局，不收贫贱局/杂局**：命科不作命运断语（`AGENTS.md` §一.3），
    把「贫贱/孤贫/困顿」类标签打进用户报告属命定论，与本仓口径冲突。
    """
    rules = (_load_corpus("geju_rules.json").get("rules") or {})
    palaces = chart_json.get("palaces") or {}
    by_branch = _star_branch_map(palaces)
    mg_idx = (chart_json.get("ming_gong") or {}).get("palace_idx")
    sg_idx = (chart_json.get("shen_gong") or {}).get("palace_idx")

    def _stars(name: str) -> tuple[set, set, str]:
        """宫名 → (主星集合, 辅星集合, 宫支)。"""
        p = palaces.get(name) or {}
        return set(p.get("main_stars") or []), set(p.get("aux_stars") or []), (p.get("branch") or "")

    def _sanfang_has(star: str) -> str:
        """命宫三方四正（财帛/官禄/迁移，含对宫）中含该星者，返回宫名（无则空）。"""
        for n in ("财帛", "官禄", "迁移"):
            m, a, _ = _stars(n)
            if star in m or star in a:
                return n
        return ""

    mg_m, mg_a, mg_b = _stars("命宫")
    ty_m, _, ty_b = _stars("田宅")
    gl_m, _, gl_b = _stars("官禄")
    sf_zuo, sf_you = _sanfang_has("左辅"), _sanfang_has("右弼")

    hits: list[tuple[str, bool]] = [
        # —— 富局 ——
        ("财荫夹印", mg_idx is not None and "天相" in mg_m
         and _jiao(by_branch, mg_idx, "武曲", "天梁")),
        ("日月夹财", mg_idx is not None and "武曲" in mg_m
         and _jiao(by_branch, mg_idx, "太阳", "太阴")),
        ("财禄夹马", mg_idx is not None and "天马" in by_branch.get(mg_idx, set())
         and _jiao(by_branch, mg_idx, "武曲", "禄存")),
        ("荫印拱身", sg_idx is not None and sg_idx == (mg_idx - 6) % 12
         and _jiao(by_branch, sg_idx, "天梁", "天相")),
        ("日月照璧", ty_m >= {"太阳", "太阴"}),
        # 「太阳单守，命在午宫」：单守 = 命宫主星恰为太阳一颗
        ("金灿光辉", mg_b == "午" and mg_m == {"太阳"}),
        # —— 贵局（原文给出单一结构条件者）——
        # 「日在卯守命是也，守官禄宫亦然」
        ("日出扶桑", (mg_b == "卯" and "太阳" in mg_m)
         or (gl_b == "卯" and "太阳" in gl_m)),
        ("月落亥宫", mg_b == "亥" and "太阴" in mg_m),
        # 「月在子宫守田宅是也」
        ("月生沧海", ty_b == "子" and "太阴" in ty_m),
        # 「武守命卯宫是也，余不是」
        ("武曲守垣", mg_b == "卯" and "武曲" in mg_m),
        # 「紫微左右同守命是也」——紫微与左辅右弼同宫
        ("君臣庆会", "紫微" in mg_m and "左辅" in mg_a and "右弼" in mg_a),
        # 「紫微守命二星来拱是也，夹之亦然」——拱=左辅右弼分居命宫三方四正；夹=分居前后邻宫
        ("辅弼拱主", "紫微" in mg_m and (
            (mg_idx is not None and _jiao(by_branch, mg_idx, "左辅", "右弼"))
            or bool(sf_zuo and sf_you and sf_zuo != sf_you))),
        # 「禄守命梁相来夹是也，入财亦然」——本判据取「禄存守命 + 天梁天相来夹」一面
        ("财印夹禄", "禄存" in mg_a and mg_idx is not None
         and _jiao(by_branch, mg_idx, "天梁", "天相")),
        # 「紫微守命前后有日月来夹是也」
        ("金舆扶驾", "紫微" in mg_m and mg_idx is not None
         and _jiao(by_branch, mg_idx, "太阳", "太阴")),
    ]
    out = []
    for name, hit in hits:
        rule = rules.get(name) or {}
        out.append({
            "名": name,
            "成立": bool(hit),
            "判据": rule.get("rule", ""),
            "类别": rule.get("kind", ""),
            "所本": rule.get("location", ""),
        })
    return out


def ziwei_analyze(chart_json: dict) -> dict:
    """chart JSON → analyze JSON。产出机械标签，不产出命运吉凶。"""
    result = dict(chart_json)
    palaces = chart_json.get("palaces", {})
    sihua_list = chart_json.get("sihua_list", [])
    pillars = chart_json.get("pillars", {})
    ming_gong = chart_json.get("ming_gong", {})
    ju = chart_json.get("wuxing_ju", 5)
    birth = chart_json.get("birth", {})
    gender = birth.get("gender")
    year_stem = (pillars.get("year") or "")[0:1] if pillars.get("year") else ""

    # 命宫主星
    mg_data = palaces.get("命宫", {})
    mg_stars = mg_data.get("main_stars", [])

    # 格局
    pattern, pattern_basis = identify_pattern(mg_stars)

    # 四化影响
    si_impact = sihua_impact(sihua_list)

    # 方向判定：命宫的「三方四正」（命宫 + 财帛 + 官禄 + 迁移 = 本宫/对宫/三合二宫）
    # 有忌入 → 有凶信号；只有禄权科落此四宫 → 偏吉。仅此，不外推。
    has_ji_in_critical = False
    has_lu_in_critical = False
    ming_sanfang = {"命宫", "迁移", "官禄", "财帛"}
    for item in sihua_list:
        if item.get("type") == "忌" and item.get("palace") in ming_sanfang:
            has_ji_in_critical = True
        if item.get("type") == "禄" and item.get("palace") in ming_sanfang:
            has_lu_in_critical = True
    # 结论措辞唯一真值源在 data/verdicts.json#方向说明，此处只做查表
    direction_note = _load_verdicts()["方向说明"]
    if has_ji_in_critical:
        direction = direction_note["忌入三方四正"]
    elif has_lu_in_critical:
        direction = direction_note["禄入三方四正"]
    else:
        direction = "平"

    # 大限
    mg_idx = ming_gong.get("palace_idx", -1)
    dy_table = []
    if mg_idx >= 0:
        dy_table = dayun_table(ju, mg_idx, gender or "男", year_stem)

    # 古法格局（卷二 定富/贵/贫贱/杂局 中机械可判者）
    classical = judge_classical_patterns(chart_json)
    hits = [c["名"] for c in classical if c["成立"]]

    # 推论总结
    mg_stars_str = "、".join(mg_stars) if mg_stars else "无主星"

    summary = {
        "命宫主星": mg_stars_str,
        "格局": pattern,
        "格局依据": pattern_basis,
        "五行局": chart_json.get("ju_name", ""),
        "命宫地支": mg_data.get("branch", ""),
        "紫微所在": f"{chart_json.get('ziwei', {}).get('branch', '')}宫",
        "天府所在": f"{chart_json.get('tianfu', {}).get('branch', '')}宫",
        "四化": chart_json.get("sihua", {}),
        "四化影响": si_impact,
        "古法格局": hits,
        "大限起宫": (dy_table[0].get("palace") if dy_table else ""),
        "大限位序": f"{'顺行' if dy_table and dy_table[0]['direction']=='顺行' else '逆行'}（{'阳男阴女顺' if dy_table and dy_table[0]['direction']=='顺行' else '阴男阳女逆'}）",
    }

    return {
        **result,
        "chart_summary": summary,
        "conclusion": {
            "命宫主星": mg_stars_str,
            "格局": pattern,
            "格局依据": pattern_basis,
            "四化影响": si_impact,
            "古法格局": classical,
            "方向": direction,
            "说明": (
                f"机械推演：命宫在{mg_data.get('branch', '')}，主星{mg_stars_str}，{pattern}。"
                f"四化：{'；'.join(si_impact) if si_impact else '无四化入三方'}。"
                "不含命运吉凶断言。"
            ),
            "所本": (
                "格局 lookup table（core.ziwei_tables.PATTERNS）+ "
                "四化表（SIHUA_TABLE）+ 大限起法（卷二安大限诀；dayun_start_age=局数）+ "
                "格局判据（data/geju_rules.json，书源逐字）"
            ),
            "timing": [],
            "dayun": dy_table,
        },
    }


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="紫微斗数因子推演（analyze 段）")
    ap.add_argument("chart_json", nargs="?", help="chart 段输出")
    ap.add_argument("-o", "--out", type=Path)
    args = ap.parse_args()

    if args.chart_json:
        data = json.loads(Path(args.chart_json).read_text(encoding="utf-8"))
    else:
        from chart import ziwei_chart as _chart

        data = _chart(datetime_str="1990-05-20 10:30", gender="男")

    out = ziwei_analyze(data)
    text = json.dumps(out, ensure_ascii=False, indent=2, default=str)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
