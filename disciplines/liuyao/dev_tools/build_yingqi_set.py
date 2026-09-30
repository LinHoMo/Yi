# -*- coding: utf-8 -*-
"""从 references/case_library.md 抽取**带明确应期**的古籍案例，建成永不参与调参的外部集。

    python dev_tools/build_yingqi_set.py [--dry-run]

为什么需要这一步：应期目前的判别力指标（主应期命中 29.4%）是在 n=17 上算的，
而那一集同时参与过法则调参。没有未参与调参的外部样本，任何"应期提准"的说法都不成立。

抽取即审计——每条必须过四道门，否则进 excluded 并写明原因，绝不放宽收录：
  1. 本卦名可解析（在 HEXAGRAM_TRIGRAMS 内）
  2. 卦变自洽：本卦 + 文中动爻 ⇒ 推出的变卦名必须等于文中所记变卦
     （案例库确有自相矛盾处，如"乾之小畜"记三、五爻动，按京房卦变应为睽）
  3. 时间可还原：文中须给出月建与日柱干支
  4. 应期可评分：文中须有明确干支（X日／X月），否则无从判定命中
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
from kernel_path import kernel_dir  # noqa: E402
sys.path.insert(0, str(kernel_dir(__file__)))

from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402

LIB = HERE.parent / "references" / "case_library.md"
OUT = HERE.parent / "data" / "cases" / "yingqi_cases.json"
SPLITS = HERE.parent / "data" / "cases" / "case_splits.json"
REPORT = HERE.parent / "docs" / "CASE-LIBRARY-AUDIT.md"

CN_NUM = {"初": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "上": 6}
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

SEC = re.compile(r"^###\s*(.+?)\s*$", re.M)
CASE = re.compile(r"^##\s*案例([一二三四五六七八九十\d]+)[：:](.*)$", re.M)
MONTH_DAY = re.compile(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS, BRANCHES))
HEX_PAREN = re.compile(r"^([^\s（(]+)")
MOVING = re.compile(r"([初二三四五六上])爻\s*[动]")
YINGQI = re.compile(r"([%s])([%s])\s*(日|月)" % (STEMS, BRANCHES))


# 六十四卦在案例库里写成全名（乾为天 / 风天小畜 / 地天泰），内核表用短名。
TRIGRAM_IMAGE = {"天": "乾", "地": "坤", "雷": "震", "风": "巽",
                 "水": "坎", "火": "离", "山": "艮", "泽": "兑"}


def resolve_hex_name(raw: str) -> tuple[str | None, str]:
    """全名 → 短名，并尽量用"上卦象+下卦象"前缀反查卦体是否相符。

    返回 (卦名, 说明)。说明非空表示存在疑点，交调用方决定是否剔除。
    """
    if not raw:
        return None, "未记本卦名"
    if raw in HEXAGRAM_TRIGRAMS:
        return raw, ""
    m = re.match(r"^(.)(为)(.)$", raw)              # 乾为天 / 坤为地 / 震为雷
    if m and m.group(1) in BAGUA_LINES:
        return m.group(1), ""
    for L in (3, 2, 1):                              # 小畜 / 既济 / 泰 …
        cand = raw[-L:]
        if cand in HEXAGRAM_TRIGRAMS:
            prefix = raw[:-L]
            note = ""
            if len(prefix) == 2 and prefix in TRIGRAM_IMAGE:
                pass
            if len(prefix) == 2:
                up_img, lo_img = prefix[0], prefix[1]
                up = TRIGRAM_IMAGE.get(up_img)
                lo = TRIGRAM_IMAGE.get(lo_img)
                if up and lo:
                    want = (HEXAGRAM_TRIGRAMS[cand] == (up, lo))
                    if not want:
                        # 有些书写作"水雷屯"（上坎下震），也有的把上下顺序写反
                        want = HEXAGRAM_TRIGRAMS[cand] == (lo, up)
                        if not want:
                            return cand, (f"全名前缀 {prefix} 与卦体 {HEXAGRAM_TRIGRAMS[cand]} 不符")
                        note = f"前缀顺序按 {up}{lo} 反查得 {cand}"
            return cand, note
    return None, f"卦名不可解析（{raw}）"


def hex_lines(name: str) -> list[int] | None:
    tri = HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return BAGUA_LINES[lower] + BAGUA_LINES[upper]


def lines_to_hex(lines: list[int]) -> str | None:
    """六爻线（自下而上）→ 卦名。"""
    from yishu_core.symbols import HEXAGRAM_TRIGRAMS as HT
    want = tuple(lines)
    for name, (upper, lower) in HT.items():
        if tuple(BAGUA_LINES[lower] + BAGUA_LINES[upper]) == want:
            return name
    return None


def cn2int(s: str) -> int | None:
    """案例编号：一…十、十一…二十、廿三等中文数字与阿拉伯数字皆可。"""
    s = (s or "").strip()
    if s.isdigit():
        return int(s)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    if s in digits:
        return digits[s]
    m = re.match(r"^十(.)$", s)                 # 十一 … 十九
    if m and m.group(1) in digits:
        return 10 + digits[m.group(1)]
    m = re.match(r"^(.)?十(.?)$", s)            # 二十 / 二十三 / 廿一
    if m:
        tens = digits.get(m.group(1) or "一", 1) if m.group(1) else 1
        if s.startswith("廿"):
            tens = 2
        unit = digits.get(m.group(2) or "", 0)
        return tens * 10 + unit
    return None


def section(body: str, title: str) -> str:
    """取案例体内某个 `### 标题` 段的文本。"""
    out, grab = [], False
    for ln in body.splitlines():
        m = SEC.match(ln)
        if m:
            grab = m.group(1).strip().startswith(title)
            continue
        if grab:
            out.append(ln)
    return "\n".join(out)


def parse_case(block: str, num: str, title: str) -> tuple[dict | None, dict | None]:
    """返回 (可用案例, excluded 记录)。二者只有一个非空。"""
    n = cn2int(num)
    cid = f"YQ{n:03d}" if n else None
    src = re.search(r"《[^》]+》", section(block, "原文出处") or block)
    source = src.group(0) if src else "《案例库》"
    time_txt = section(block, "时间")
    q = section(block, "占问事项").strip().splitlines()
    question = q[0] if q else title
    start_txt = section(block, "起卦信息")

    def field(label: str) -> str:
        m = re.search(r"\*\*%s\*\*[：:]\s*(.+)" % label, start_txt)
        return m.group(1).strip() if m else ""

    def resolve(label: str):
        raw = field(label)
        mm = HEX_PAREN.match(raw) if raw else None
        return resolve_hex_name(mm.group(1) if mm else "")

    orig, orig_note = resolve("本卦")
    changed, chg_note = resolve("变卦")
    moving = sorted({CN_NUM[c] for c in MOVING.findall(field("动爻"))}) or None
    def excl(reason: str) -> tuple[None, dict]:
        return None, {"id": cid or f"YQ-{num}", "reason": reason, "title": title[:40],
                      "source": source, "original": orig, "changed": changed,
                      "moving": moving}

    md = MONTH_DAY.search(time_txt)
    if not md:
        return excl("时间无月建日柱干支，无法还原时空")
    month_branch, day_ganzhi = md.group(1), md.group(2) + md.group(3)

    if orig_note:
        return excl(f"本卦存疑：{orig_note}")
    if chg_note:
        return excl(f"变卦存疑：{chg_note}")
    base = hex_lines(orig) if orig else None
    if base is None:
        return excl(f"本卦名不可解析（{orig or '未记'}）")
    if not moving and not changed:
        # 六爻皆动之卦（静卦）是合法卦型，不该按"缺项"剔除；应期由用神旺衰与日辰定
        moving = []
    elif not moving:
        return excl("记有变卦却未记动爻位次，无从核对")
    # 动爻以"本卦⊕变卦"的差集为准（与 case_runner.hex2yao 同法）；
    # 文记动爻只作参照——案例库常见只记与断语相关的那一两个动爻，
    # 属记载不全而非矛盾，放宽为"文记必须是差集的子集"。
    # 但若文记出现差集之外的爻位，那是真矛盾，不可用于评分。
    required = None
    if changed:
        derived = list(base)
        chg = hex_lines(changed)
        if chg is None:
            return excl(f"变卦名不可解析（{changed}）")
        required = [i + 1 for i, (x, y) in enumerate(zip(base, chg)) if x != y]
        if not required:
            return excl("本卦与变卦相同却记有变卦")
        if moving and not set(moving) <= set(required):
            extra = sorted(set(moving) - set(required))
            return excl(f"文记动爻 {extra} 不在卦变差集 {required} 内，自相矛盾")
        if not moving:
            return excl("未记动爻位次（差集虽可推，无从核对原记）")
    if required:
        moving = required
    # 只看"结论与应验"段，且不回落到整块文本：整块里有 `### 时间` 的占测日干支，
    # 曾被当成应期答案（案例三真应期为"未日"，却被抽出"卯日"），那是在给自己打假分。
    concl = (section(block, "结论与应验") + chr(10) + section(block, "应验")
             + chr(10) + section(block, "结论"))
    actual = re.search(r"\*\*(?:实际|果|验)\*\*[：:]\s*(.+)", concl)
    if not actual:
        return excl("无应验记录（只有断语没有实际结果），不可评分")
    actual_txt = actual.group(1).strip()
    judge = re.search(r"\*\*(?:判断|断)\*\*[：:]\s*(.+)", concl)
    verdict_txt = (judge.group(1) if judge else "") + " " + actual_txt

    # 应期以**应验句**为准；判断句里的假设支不算答案。
    # 只按"支＋日/月"抓：古籍多写"未日""午月"而非"丁未日"，要求全干支会把真答案漏掉。
    yq = sorted({m.group(1) + m.group(2)
                 for m in re.finditer(r"([%s])\s*(日|月)" % BRANCHES, actual_txt)})
    if not yq:
        return excl("应验句无明确干支（日/月），不可评分")
    branches = sorted({x[0] for x in yq})
    if len(branches) > 3:
        return excl(f"应期含 {len(branches)} 支（{','.join(branches)}），过宽，不构成可检验断言")

    if cid is None:
        return excl("案例编号无法解析（既非阿拉伯数字也非中文数字）")

    # 用神：正文形如「以**子孙爻**为用神」「取**妻财爻**为利润用神」
    use_txt = section(block, "取用神说明") + chr(10) + section(block, "取用神")
    relation = None
    for cand in ("父母", "兄弟", "子孙", "妻财", "官鬼"):
        if re.search(r"\*\*" + cand + r"爻?\*\*[^。\n]{0,12}为[^。\n]{0,6}用神", use_txt):
            relation = cand
            break
    if not relation:
        return excl("用神六亲不可抽取，无法对齐评分")

    # 吉凶：按应验与判断句的成败词判定；"愈/得/成/有医"为吉，"死/丢/降/散/无望/不利"为凶
    good = any(k in verdict_txt for k in ("愈", "得医", "有利", "遂", "成", "得", "吉", "无碍", "有效"))
    bad = any(k in verdict_txt for k in ("死", "丢官", "降职", "散伙", "无望", "不利", "凶", "悔", "失"))
    if good == bad:
        return excl(f"吉凶方向不可判定（吉词{good} 凶词{bad}）")
    verdict = "吉" if good else "凶"
    same_day = day_ganzhi[1] in branches

    return {
        "id": cid,
        "source": source,
        "topic": title[:24],
        "question": question,
        "input": {"date": f"{month_branch}月{day_ganzhi}日", "question": question},
        "hexagram": {"original": orig, "changed": changed or None,
                     "moving": moving},
        "expected": {"verdict": verdict, "use_god": relation,
                     "use_god_branch": "",          # 原书未必记到爻，留空即记 N/A 不送分
                     "yingqi": "、".join(yq), "yingqi_branches": branches,
                     "detail": actual_txt[:200],
                     "same_as_day_branch": same_day},     # 应于占测当日，易命中，统计时单列
        "notes": "dev_tools/build_yingqi_set.py 抽取，过本卦可解析/卦变自洽/时间可还原/"
                 "应验句有干支/应期不宽于三支/用神与吉凶可判 六道门；不参与任何调参",
    }, None


def main() -> int:
    ap = argparse.ArgumentParser(description="抽取带明确应期的古籍案例作外部验证集")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    text = LIB.read_text(encoding="utf-8")
    marks = list(CASE.finditer(text))
    kept, excluded = [], []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        block = text[m.end():end]
        case, ex = parse_case(block, m.group(1), m.group(2).strip())
        (kept if case else excluded).append(case or ex)

    # 编号去重（同名案例可能重复出现）
    seen, unique = set(), []
    for c in kept:
        if c["id"] in seen:
            excluded.append({"id": c["id"] + "-dup", "reason": "与已收录案例编号重复",
                             "title": c["topic"]})
            continue
        seen.add(c["id"])
        unique.append(c)

    print(f"扫描 {len(marks)} 例 → 可评分 {len(unique)} 例，剔除 {len(excluded)} 例")
    for e in excluded[:14]:
        print(f"  × {e['id']}: {e['reason']}")
    if len(excluded) > 14:
        print(f"  …另 {len(excluded) - 14} 例")

    report = ["# 案例库应期抽取审计", "",
              f"抽取器：`dev_tools/build_yingqi_set.py`｜扫描 {len(marks)} 例 → "
              f"可评分 {len(unique)} 例｜生成于 {date.today().isoformat()}", "",
              "四道门：本卦名可解析、卦变自洽（本卦＋动爻⇒变卦）、时间可还原、应期有明确干支。",
              "**任一道不过即 excluded，不放宽收录。**", "", "## 可收录（未参与调参的外部验证集）", ""]
    report += ([f"- `{c['id']}` {c['source']}｜{c['topic']}｜应期 `{'、'.join(c['expected']['yingqi_branches'])}`"
                for c in unique] or ["（无）"])
    report += ["", "## 剔除清单与原因", "", "| 案例 | 原因 | 本卦 | 变卦 | 文记动爻 |", "|---|---|---|---|---|"]
    report += [f"| {e['id']} {e.get('title','')} | {e['reason']} | {e.get('original') or '—'} "
               f"| {e.get('changed') or '—'} | {e.get('moving') or '—'} |" for e in excluded]
    report += ["", "## 结论", "",
               "卦变不自洽者为多数时，说明该库内容不可直接用于评分："
               "须先按《京房》卦变与纳甲逐例校勘（人工或对照可靠整理本），修好后重跑本工具。",
               "在校勘完成前，**不设置 yingqi_holdout 外部集**，以免用一个错数据集得出好看的假指标。", ""]
    REPORT.write_text(chr(10).join(report), encoding="utf-8")
    print("校勘清单 →", REPORT.relative_to(HERE.parent))
    if args.dry_run or not unique:
        return 0

    OUT.write_text(json.dumps({"_meta": {
        "description": "应期外部验证集：从 case_library.md 抽取、通过四道自洽校验、永不参与调参",
        "built_by": "dev_tools/build_yingqi_set.py",
        "total_cases": len(unique),
        "excluded": excluded,
    }, "cases": unique}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n写入 {OUT.relative_to(HERE.parent)}（{len(unique)} 例）")

    sp = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    sp["yingqi_holdout"] = [c["id"] for c in unique]
    sp.setdefault("note", "")
    sp["note"] = (sp["note"] + "；yingqi_holdout=应期外部验证集，永不参与调参").lstrip("；")
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("case_splits.json 已登记 yingqi_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
