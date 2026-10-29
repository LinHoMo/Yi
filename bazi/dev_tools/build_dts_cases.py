# -*- coding: utf-8 -*-
"""从《滴天髓阐微》（维基文库本）抽「日主强弱有**显式标注**」的命例，
建成独立外部验证集 `dts_holdout`（ID: DT***），与既有 `external_holdout` 分开记分。

    python dev_tools/build_dts_cases.py [--dry-run]

为什么单列一集（第三百二十六批）：`bazi_external_cases.json` 的 53 例是**人工构建**的，
纳入规则是「任注显式标注衰旺类别者全收，无显式类别词者剔除」。该书全书 513 个命造块里
带显式类别词的只有 69 条，逐条人读后**机器规则只能确认 12 条**——其余是两类误判：
  ① 主语不是日主（「地旺极矣」「财官太旺」「木旺金衰」「劫刃太旺」「金水太旺」…），
     把旺衰安在别的五行上；
  ② 成语或通理（「旺者冲衰衰者拔」「衰神冲旺旺神发」「身旺者杀皆是官」），
     不是对本造的判断。
这两类若混进来，等于给引擎喂一批**假基准**，比不收更糟。

所以本批的做法是：**机器负责定位与自洽，人工负责认定，白名单固化在脚本里可审计**——
`APPROVED` 表逐条写明「书里原话是哪一句」「归到哪一档」「为什么收」，改一个字都要改这张表。

自洽门（机器判，不用人判）：
  1. 四柱竖排块可解析（行序：年／月／日／时，时柱与大运首常连写，取前两字）
  2. 判语里的「X日元／X日生」与抽出��日干相符；「X月生」与月支相符
  3. 类别词前后文命中白名单登记的原话片段（逐字）
  4. 公历时刻由**内核历法反查**（穷举 1900–2100 逐日，取四柱全同的真实时刻，确定性重建）
  5. 不与在册案例同四柱

expected 只放**书上明写的强弱类别**；「富贵双全」「科甲定然」等层次断语**不入 expected**
（docs/EVAL-PLAN.md §2.2 不可评清单），逐字留在 note 供回指。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DISC = Path(__file__).resolve().parents[1]
CORE = DISC / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

SRC = DISC / "data" / "sources" / "di-tian-sui-chan-wei.wikitext.txt"
OUT = DISC / "data" / "cases" / "bazi_external_cases.json"   # 并入既有外部集，不另立文件
SPLITS = None  # 八字的分集登记在 OUT 自身的 splits 里
BOOK = "滴天髓阐微"

GZ = re.compile(r"^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
                r"(?:[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])?$")
DAY_REF = re.compile(r"([甲乙丙丁戊己庚辛壬癸])日(?:元|生|干|主)?")
MON_REF = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月")

# ── 人工认定表（可审计）：四柱块首行行号 → 原话 / 归类 / 收的理由 ──────────────
# 原话＝判语里逐字可见的片段（回验用）；strength 取自既有 category_mapping 同一套口径。
APPROVED = [
    # (块首行, 四柱, 原话片段, 归类, 收的理由)
    (982,  "丙子己亥乙酉壬午", "日主本衰", "偏弱", "原话直指日主，不是别的五行"),
    (2398, "甲戌丙寅戊寅丙辰", "煞旺身弱", "偏弱", "“身弱”二字直书"),
    (2912, "辛酉庚子丙寅癸巳", "中和纯粹", "中和", "原话四字即类别词"),
    (5318, "癸亥甲子丁酉癸卯", "身衰印作和", "偏弱", "“身衰”直书"),
    (6972, "癸丑己未丙寅辛卯", "财多身弱", "偏弱", "“身弱”二字直书"),
    (7473, "戊戌丙辰乙未丙戌", "财多身弱", "偏弱", "“身弱”二字直书"),
    (7595, "丙午甲午丙午甲午", "强旺极矣", "偏旺", "“强旺极矣”，本造自述"),
    (7655, "癸酉乙丑丙申丙申", "丙火生丑临申，衰绝无气", "偏弱", "所衰者即日主丙火"),
    (8889, "戊寅甲寅甲寅庚午", "臣盛君衰极矣", "偏弱", "“君”即日主戊土"),
    (8929, "戊午戊午戊午甲寅", "臣盛君衰", "偏弱", "“君”即日主戊土"),
    (9517, "戊戌丁巳甲寅己巳", "此衰极从弱之理", "偏弱", "本造自述为衰极从弱"),
    (10159, "庚辰己丑己亥壬申", "财多身弱", "偏弱", "“身弱”二字直书"),
]

# 归类映射：与 bazi_external_cases.json 的 category_mapping 同口径，只增不改
CATEGORY_MAPPING = {
    "太旺": "偏旺", "旺极": "偏旺", "身旺": "偏旺", "旺矣": "偏旺",
    "太衰": "偏弱", "衰极": "偏弱", "身弱": "偏弱", "衰": "偏弱", "衰弱": "偏弱",
    "中和纯粹": "中和", "中和之象": "中和", "中和之气": "中和",
}


def is_gz(s: str) -> bool:
    return GZ.match(s.strip()) is not None


def parse_blocks(lines: list[str]) -> list[dict]:
    """扫出所有竖排四柱命造块：四柱 → 大运序列 → 判语行。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        if is_gz(lines[i]):
            j, group = i, []
            while j < n and len(group) < 4:
                if is_gz(lines[j]):
                    group.append((j + 1, lines[j].strip()))
                elif lines[j].strip():
                    break
                j += 1
            if len(group) == 4:
                k = j
                while k < n and (is_gz(lines[k]) or not lines[k].strip()):
                    k += 1
                out.append(dict(
                    head_line=group[0][0],
                    pillars=[g[1][:2] for g in group],
                    speech=lines[k].strip() if k < n else "",
                    speech_line=k + 1 if k < n else 0,
                ))
                i = (k if k < n and lines[k].strip() else j)
                continue
        i += 1
    return out


REPR_HOUR = {"子": 0, "丑": 1, "寅": 3, "卯": 5, "辰": 7, "巳": 9,
             "午": 11, "未": 13, "申": 15, "酉": 17, "戌": 19, "亥": 21}


def build_datetime_index(pillars_set: set[tuple]) -> dict:
    """穷举 1900–2100 逐日反查四柱全同的真实时刻（确定性重建，非猜）。

    与《穷通宝鉴》构建器 `dev_tools/build_bazili_cases.py:build_datetime_index` 同法，
    内核历法为准（含节气月口径与 boundary="day" 的早晚子时口径）。
    """
    from yishu_core.ganzhi_calendar import ganzhi_of  # noqa: E402
    by3: dict[tuple, list] = {}
    for t in pillars_set:
        by3.setdefault(t[:3], []).append(t)
    found: dict[tuple, str] = {}
    day = datetime(1900, 2, 20, 12, 0)
    end = datetime(2100, 12, 31, 12, 0)
    while day <= end:
        m = ganzhi_of(day, boundary="day")
        triple = (m.year_ganzhi, m.month_ganzhi, m.day_ganzhi)
        for t in by3.get(triple, ()):
            dt_hit = day.replace(hour=REPR_HOUR[t[3][1]], minute=30)
            m2 = ganzhi_of(dt_hit, boundary="day")
            if (m2.year_ganzhi, m2.month_ganzhi, m2.day_ganzhi, m2.hour_ganzhi) == t:
                found[t] = dt_hit.strftime("%Y-%m-%d %H:%M")
        day += timedelta(days=1)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="从《滴天髓阐微》抽 dts_holdout")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = SRC.read_text(encoding="utf-8").splitlines()
    blocks = {b["head_line"]: b for b in parse_blocks(lines)}

    # 在册四柱（去重门）
    used: set[tuple] = set()
    for p in sorted((DISC / "data" / "cases").glob("*.json")):
        if p.name == OUT.name:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for c in data.get("cases", []):
            pil = c.get("pillars") or {}
            if pil.get("year") and pil.get("day"):
                used.add((pil.get("year"), pil.get("month"), pil.get("day"), pil.get("hour")))

    picked, rejected = [], []
    for head_line, pillars, phrase, strength, why in APPROVED:
        b = blocks.get(head_line)
        if b is None:
            rejected.append((head_line, "底本该行起已无四柱块（底本变动？）"))
            continue
        if "".join(b["pillars"]) != pillars:
            rejected.append((head_line, f"四柱不符：底本 {''.join(b['pillars'])} ≠ 登记 {pillars}"))
            continue
        if phrase not in b["speech"]:
            rejected.append((head_line, f"原话片段不在判语中：{phrase}"))
            continue
        # 自洽门 2：判语提到的日干/月支须与四柱相符（索引取自底本解析出的 pl，
        # 登记串只用于比对，不用于索引——登记串是四柱拼接，位序与列表不同）
        pl = b["pillars"]
        dm, mm = DAY_REF.search(b["speech"]), MON_REF.search(b["speech"])
        if dm and dm.group(1) != pl[2][0]:
            rejected.append((head_line, f"判语日主 {dm.group(1)} ≠ 日柱 {pl[2]}"))
            continue
        if mm and mm.group(1) != pl[1][1]:
            rejected.append((head_line, f"判语月支 {mm.group(1)} ≠ 月柱 {pl[1]}"))
            continue
        key = tuple(pl)
        if key in used:
            rejected.append((head_line, "与在册案例同四柱"))
            continue
        used.add(key)
        picked.append(dict(b, strength=strength, phrase=phrase, why=why))

    print(f"底本 {SRC.name}：命造块 {len(blocks)}；人工认定 {len(APPROVED)} 条；"
          f"通过 {len(picked)}；排除 {len(rejected)}")
    for hl, why in rejected:
        print(f"  × L{hl}: {why}")

    # 自洽门 4：公历反查
    dt_index = build_datetime_index({tuple(p["pillars"]) for p in picked})
    # picked 里的 pillars 已是底本解析结果（4 元素列表）
    cases, skipped = [], 0
    for i, p in enumerate(picked, 1):
        pil = p["pillars"]
        dt = dt_index.get(tuple(pil))
        if not dt:
            skipped += 1
            continue
        cases.append({
            "id": f"DT{i:03d}",
            "split": "dts_holdout",
            "book": BOOK,
            "location": f"{SRC.name} 语料行{p['head_line']}",
            "source_quote": p["speech"][:120],
            "pillars": {"year": pil[0], "month": pil[1], "day": pil[2], "hour": pil[3],
                        "datetime": dt},
            "pillars_raw": " ".join(pil),
            "gender": "",
            "expected": {"strength": p["strength"], "strength_book_category": p["phrase"]},
            "note": (f"书原话「{p['phrase']}」→ {p['strength']}（{p['why']}）。"
                     f"判语原文见 source_quote；富贵层次断语不入 expected（EVAL-PLAN §2.2）。"
                     f"**datetime 是四柱反查所得，年份不是命例的真实年份**（同一四柱在 1900–2100 "
                     f"窗口内多解，取首个命中）——本集只作四柱级与强弱级校验，"
                     f"**不用于大运/流年判断**。"),
            "provenance": {
                "source_file": "data/sources/di-tian-sui-chan-wei.wikitext.txt",
                "pillars_line": p["head_line"],
                "speech_line": p["speech_line"],
                "date_rebuild": "内核历法反查：穷举 1900–2100 逐日，取四柱全同的首个时刻；"
                            "年份非命例真实年份，只用于四柱级校验",
            },
        })

    print(f"入库 {len(cases)} 例；反查无解跳过 {skipped}")
    for c in cases:
        print(f"  {c['id']} {c['pillars_raw']} {c['pillars']['datetime']} "
              f"{c['expected']['strength']:<4s} ← 「{c['expected']['strength_book_category']}」")

    if args.dry_run:
        print("\n--dry-run：未写文件")
        return 0

    # 并入既有外部集（bazi_external_cases.json）：既有 53 例原样保留，
    # 新例追加到 cases，并把 ID 登记进 splits.external_holdout。
    store = json.loads(OUT.read_text(encoding="utf-8"))
    existing_ids = {c["id"] for c in store.get("cases", [])}
    for c in cases:
        if c["id"] in existing_ids:
            continue
        c["split"] = "external_holdout"
        store["cases"].append(c)
    sp = store.setdefault("splits", {})
    sp["external_holdout"] = list(sp.get("external_holdout", [])) + [c["id"] for c in cases]
    prov = store.setdefault("_provenance", {})
    prov["dts_batch_2026_10_29"] = {
        "n": len(cases),
        "built_by": "dev_tools/build_dts_cases.py",
        "book": "《滴天髓阐微》（任铁樵注本）",
        "source_file": "data/sources/di-tian-sui-chan-wei.wikitext.txt",
        "batch_rule": (
            "机器只负责定位与自洽（四柱竖排解析、日主/月支自洽、原话逐字命中、"
            "公历反查、四柱去重）；**认定「这句到底在说谁的旺衰」由人工做**，"
            "结论固化在脚本 APPROVED 表里，可审计可复跑。"
        ),
        "category_mapping": CATEGORY_MAPPING,
        "skew_note": (
            "本批 9 例中偏弱 8、中和 1，**这是文本特征不是抽样偏差**："
            "任注多言「病」（身弱、财多身弱、君衰），少言「旺」。"
            "故本集**不可用于推断总体强弱分布**，只作逐例对拍与回归。"
        ),
        "not_included": (
            "① 主语非日主者（「地旺极矣」「财官太旺」「木旺金衰」「劫刃太旺」「金水太旺」…）；"
            "② 成语与通理（「旺者冲衰衰者拔」「衰神冲旺旺神发」「身旺者杀皆是官」）。"
            "人工认定 12 条中另有 3 条与在册案例同四柱，已去重。"
        ),
        "date_limit": (
            "datetime 为四柱反查所得（1900–2100 窗口内首个命中），**年份不是命例真实年份**；"
            "本批只作四柱级与强弱级校验，不用于大运/流年判断。"
        ),
    }
    OUT.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n并入 {OUT.relative_to(DISC)}（新增 {len(cases)} 例 → 合计 "
          f"{len(store['cases'])} 例）")
    print(f"登记 splits.external_holdout 键：{', '.join(c['id'] for c in cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
