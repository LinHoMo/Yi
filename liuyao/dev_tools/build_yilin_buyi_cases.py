# -*- coding: utf-8 -*-
"""从《易林補遺》候选池 (data/cases/yilin_buyi_candidates.json) 抽取可评分案例，
建成外部验证集 `yilin_buyi_holdout`（ID: YLB001–007）。

    python dev_tools/build_yilin_buyi_cases.py [--dry-run]

按 548 批 §四 入册授权（用户明确勾选「§四 入册候选池」＝ Form C 单独授权）：
  · 候选池本身零评分、零泄漏；此处为**首次正式入册**为评分集。
  · 严守 §三.4 禁反推：expected 只取书载（verdict 一律 null、use_god 空、
    单点应期 yingqi/yingqi_branches 取自书载应期句；跨月/非单点按 411 不换算，yingqi 空）。
  · 卦象 original/changed：书载「X之Y」直取；仅记动爻描述的案按书载动爻机械派生
    changed（定义型变换，非反推）。moving 由 original+changed 反推（与 case_runner.hex2yao 同义）。
  · 外部验证集，永不参与调参；与 yiin_holdout / zengshan_dz_holdout 同定位（应期语料通道）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import kernel_dir  # noqa: E402
sys.path.insert(0, str(kernel_dir(__file__)))
from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402

CAND = DISC / "data" / "cases" / "yilin_buyi_candidates.json"
OUT = DISC / "data" / "cases" / "yilin_buyi_cases.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

POS_MAP = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6}
MONTH_MAP = {"正": 1, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
             "七": 7, "八": 8, "九": 9, "十": 10, "冬": 11, "十一": 11, "腊": 12, "十二": 12}
BRANCH_BY_MONTH = {1: "寅", 2: "卯", 3: "辰", 4: "巳", 5: "午", 6: "未",
                   7: "申", 8: "酉", 9: "戌", 10: "亥", 11: "子", 12: "丑"}
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEMS = "甲乙丙丁戊己庚辛壬癸"


def hex_lines(name: str):
    tri = HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    up, lo = tri
    return BAGUA_LINES[lo] + BAGUA_LINES[up]  # 自下而上


NAME_BY_LINES = {tuple(BAGUA_LINES[lo] + BAGUA_LINES[up]): nm
                  for nm, (up, lo) in HEXAGRAM_TRIGRAMS.items()}


def name_from_lines(lines6: list[int]) -> str | None:
    return NAME_BY_LINES.get(tuple(lines6))


def derive_changed(orig: str, moving: list[int]) -> str | None:
    base = hex_lines(orig)
    if base is None:
        return None
    chg = [(1 - b) if (i + 1) in moving else b for i, b in enumerate(base)]
    return name_from_lines(chg)


def compute_moving(orig: str, chg) -> list[int]:
    base = hex_lines(orig)
    if base is None or not chg or chg == orig:
        return []
    chg_lines = hex_lines(chg)
    if chg_lines is None:
        return []
    return sorted(i + 1 for i, (a, b) in enumerate(zip(base, chg_lines)) if a != b)


def parse_hex(text: str):
    """返回 (original, changed_or_None, moving_or_None)。"""
    text = text.strip()
    if "之" in text:
        a, b = text.split("之", 1)
        orig = a.strip()
        chg = re.sub(r"卦$", "", b.strip())
        chg = {"垢": "姤"}.get(chg, chg)  # YLB002 底本「垢」＝「姤」，建器取内核名
        return orig, chg, None
    if "安静" in text:
        orig = text.replace("安静", "").rstrip("卦").strip()
        return orig, None, []
    m = re.search(r"[初二三四五上九六爻]", text)
    orig = text[:m.start()].rstrip("卦").strip() if m else text.rstrip("卦").strip()
    moving = [POS_MAP[w] for w in re.findall(r"初|二|三|四|五|上", text)]
    return orig, None, moving


def normalize_date(date_text: str) -> str:
    """候选 date_text（含「X月…旬Y日」）→ 月支＋日柱 形式 input.date。"""
    month_branch = None
    mm = re.search(r"([正一二三四五六七八九十冬腊]+)月", date_text)
    if mm:
        num = mm.group(1)
        midx = 11 if num in ("十一", "冬") else 12 if num == "十二" else MONTH_MAP.get(num)
        if midx:
            month_branch = BRANCH_BY_MONTH[midx]
    day = None
    if "旬" in date_text:
        after = date_text.split("旬", 1)[1]
        dm = re.search(r"([%s][%s])日" % (STEMS, BRANCHES), after)
        if dm:
            day = dm.group(1)
    if day is None:
        dm = re.search(r"([%s][%s])日" % (STEMS, BRANCHES), date_text)
        if dm:
            day = dm.group(1)
    if not month_branch or not day:
        return date_text  # 兜底：原样（缺月支的案不会走到这里，建器已过滤）
    return f"{month_branch}月{day}日"


def run_selftest() -> int:
    """确定性变换逻辑的自证（只读候选池，不写盘）。"""
    fails: list[str] = []

    # parse_hex 三形态：X之Y / 安静 / X初二三爻皆动；底本「垢」归一「姤」
    for text, want in (
        ("乾之坤", ("乾", "坤", None)),
        ("观之益", ("观", "益", None)),
        ("姤之大过", ("姤", "大过", None)),
        ("乾之垢", ("乾", "姤", None)),
        ("乾卦安静", ("乾", None, [])),
        ("观初二三爻皆动", ("观", None, [1, 2, 3])),
    ):
        got = parse_hex(text)
        if got != want:
            fails.append(f"parse_hex({text!r})={got!r} 应 {want!r}")

    # normalize_date：月序按正月建寅转月支；缺月支兜底原样
    for date_text, want in (
        ("子月戊午日", "子月戊午日"),
        ("亥月戊子日", "亥月戊子日"),
        ("五月庚申日", "午月庚申日"),
        ("十一月丙午日", "子月丙午日"),
        ("戊寅日", "戊寅日"),
    ):
        if normalize_date(date_text) != want:
            fails.append(f"normalize_date({date_text!r})={normalize_date(date_text)!r} 应 {want!r}")

    # 动爻派生可逆：任取本卦＋动爻列表，derive_changed 再 compute_moving 应回原动爻
    for orig in ("乾", "坤", "屯", "蒙", "剥", "萃", "师", "观", "姤", "小畜",
                 "蛊", "大畜", "否", "益", "大过", "颐", "复"):
        for moving in ([1], [6], [1, 2, 3], [2, 6]):
            chg = derive_changed(orig, moving)
            if chg is None:
                fails.append(f"derive_changed({orig},{moving}) 得 None"); continue
            back = compute_moving(orig, chg)
            if back != sorted(moving):
                fails.append(f"动爻可逆失败 {orig} {moving}→{chg}→{back}")
    if compute_moving("乾", "乾") != []:
        fails.append("compute_moving 静卦未返回 []")

    for f in fails:
        print("  × selftest：", f)
    if fails:
        return 1
    print("  √ selftest：parse_hex 三形态＋「垢→姤」归一／normalize_date 月序转月支／"
          "动爻派生可逆（17 卦×4 动爻组合全闭合）")
    return 0


def _check_sync() -> int:
    """同源复验：落盘集须由当前候选池逐字可复现（sha 不变且每条锚句仍逐字命中底本）。"""
    if not OUT.exists():
        print("× 落盘集不存在：%s" % OUT.relative_to(DISC))
        return 1
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    meta = doc.get("_meta") or {}
    cand = json.loads(CAND.read_text(encoding="utf-8"))
    sha = cand["source"]["sha256"]
    src_file = cand["source"]["file"]
    src_text = (DISC / src_file).read_text(encoding="utf-8", errors="replace")
    fails = []
    if meta.get("sha256") != sha:
        fails.append("底本 sha256 已变——须重跑本脚本重建 %s" % OUT.name)
    cases = doc.get("cases") or []
    if meta.get("n") != len(cases):
        fails.append("n=%s ≠ 实际 %d 条" % (meta.get("n"), len(cases)))
    checked = 0
    for c in cases:
        detail = (c.get("expected") or {}).get("detail") or ""
        if detail and detail not in src_text:
            fails.append("%s 的 expected.detail 已不在底本（%s…）" % (c.get("id"), detail[:24]))
            continue
        checked += 1
    ok = "全部一致" if not fails else "%d 处失效" % len(fails)
    print("同源复验：%d/%d 条锚句仍逐字命中底本；%s" % (checked, len(cases), ok))
    for f in fails:
        print("  ×", f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="从《易林補遺》候选池建 yilin_buyi_holdout")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true", help="确定性变换逻辑自证（不写盘）")
    ap.add_argument("--check", action="store_true",
                    help="只复验已生成 JSON 的锚句仍逐字命中底本，不写文件（[46] 同步门挂此）")
    args = ap.parse_args()
    if args.selftest:
        return run_selftest()
    if args.check:
        return _check_sync()

    cand = json.loads(CAND.read_text(encoding="utf-8"))
    src = cand["source"]
    sha = src["sha256"]
    src_file = src["file"]
    pool_cases = cand["cases"]

    cases = []
    for c in pool_cases:
        cid = c["id"]
        orig, chg, moving = parse_hex(c["hexagram_text"])
        if chg is None:
            chg = derive_changed(orig, moving) if moving else None
        moving = compute_moving(orig, chg)
        date_norm = normalize_date(c["date_text"])
        yingqi_text = c.get("yingqi_text") or ""
        verdict_text = c.get("verdict_text") or ""
        single = str(c.get("enroll_status", "")).startswith("单点")
        if single and yingqi_text:
            yq = yingqi_text
            brs = [b for b in yq if b in BRANCHES]
            detail = yingqi_text
        else:
            yq = ""
            brs = []
            detail = (verdict_text or yingqi_text) or c["source_quote"][:40]
        rec = {
            "id": cid,
            "source": "《易林補遺》（dz 转录本）",
            "topic": c.get("topic", ""),
            "question": c.get("relation", ""),
            "input": {"date": date_norm, "question": c.get("relation", "")},
            "hexagram": {
                "original": orig,
                "changed": chg,
                "moving": moving,
                "note": c["hexagram_text"],
            },
            "expected": {
                "verdict": None,
                "use_god": "",
                "yingqi": yq,
                "yingqi_branches": brs,
                "detail": detail,
            },
            "provenance": {
                "source_file": src_file,
                "sha256": sha,
                "line": c.get("source_line"),
                "day_line": c.get("source_line"),
                "table_line": c.get("source_line"),
                "quote": c["source_quote"],
                "speech_head": c["source_quote"][:40],
            },
        }
        cases.append(rec)

    n_yq = sum(1 for c in cases if c["expected"]["yingqi"])
    print(f"《易林補遺》候选 {len(pool_cases)} 案 → 入册 {len(cases)} 例；带单点应期 {n_yq} 例")
    for c in cases:
        chg = c["hexagram"]["changed"]
        print(f"  {c['id']} {c['hexagram']['original']}之{chg or '（静）'} "
              f"动{c['hexagram']['moving']} {c['input']['date']} 应期={c['expected']['yingqi'] or '—'}")

    if args.dry_run:
        print("\n--dry-run：未写文件")
        return 0

    payload = {
        "_meta": {
            "book": "易林補遺",
            "source": "dz 转录本",
            "source_file": src_file,
            "sha256": sha,
            "built_by": "dev_tools/build_yilin_buyi_cases.py",
            "split": "yilin_buyi_holdout",
            "n": len(cases),
            "with_yingqi": n_yq,
            "verdict_policy": "吉凶一律 null：书载断语为散文，映射吉/凶属解读，越铁律一；本集为应期语料通道。",
            "note": "外部验证集，永不参与调参；按 548 批 §四 入册授权由 yilin_buyi_candidates.json 转建。",
        },
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    splits["yilin_buyi_holdout"] = [c["id"] for c in cases]
    splits["note_yilin_buyi_holdout"] = (
        "《易林補遺》dz 转录本「占病何日见凶」段 7 案（L1279）经候选池（542 批）预注册、"
        "开卷一次、逐例红绿后，按 548 批 §四 入册授权转建。外部验证集，永不参与调参；"
        "吉凶记 null，只评应期；跨月/非单点应期按 411 不换算，yingqi 留空。"
    )
    ne = splits.get("note_externals", "")
    if "yilin_buyi_holdout" not in ne:
        splits["note_externals"] = (ne
            + "yilin_buyi_holdout/bushi_quanshu_holdout 为 548 批 §四 入册的《易林補遺》/"
              "《卜筮全书》候选池转建集（永不参与调参）。")
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n写出 {OUT.relative_to(DISC)}（{len(cases)} 例）")
    print(f"登记 {SPLITS.relative_to(DISC)} 键 yilin_buyi_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
