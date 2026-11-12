# -*- coding: utf-8 -*-
"""《滴天髓闡微》人工认定版候选池（569 批）——12 案逐条签判准。

背景：565 批的机器认定池已按 568 批更正（只认主语明确锚），但其中 **12 案的"旺／衰"主语不明**
（命例里的"旺极矣""太旺"多指忌神、官杀或某一五行，不是日主），机器无法判，故 `category` 留 null。
568 批开卷后这 12 案全部记「不适用」，可判样本仅 3 案。

本器做**人工认定**：把 12 条判语逐条读过，给出日主强弱档（偏弱／偏旺／中和）与理由，
所引**原话片段必须逐字出现在该案判语中**（复验器逐条核）。本池是**新池**，不是重开已开卷的池——
565 池的一次性开封效力不受影响。

    python dev_tools/build_dts_manual_candidates.py --write
    python dev_tools/build_dts_manual_candidates.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mine_dts_candidates as M_  # noqa: E402

SRC_POOL = DISC / "data" / "cases" / "dts_candidates.json"
OUT = DISC / "data" / "cases" / "dts_manual_candidates.json"
ID_PREFIX = "DTM"

# ── 人工认定表：案 id →（日主强弱档, 原话片段（逐字）, 理由）──────────────────────
# 认定的对象是**日主**的旺衰；命例中"太旺／衰极"常指忌神或官杀，理由栏写明为何不取该词。
MANUAL: tuple[tuple[str, str, str, str], ...] = (
    ("DTC001", "偏弱", "天衰极矣", "原书言天干（壬水）衰极，并断为「合从」——日主从火，故偏弱"),
    ("DTC002", "偏弱", "天衰极矣", "原书言天干丁火衰极，且断为「从官」——日主偏弱"),
    ("DTC003", "中和", "日主之气不薄", "原书只言日主之气不薄，未言衰旺——取中和"),
    ("DTC004", "偏旺", "官杀太旺亦伤残，秘须身财并旺", "所称太旺者为劫刃（比劫），非日主；原书谓须身旺方能任官杀——日主偏旺"),
    ("DTC005", "偏旺", "日元得地", "所称太旺者为财官；原书谓日元得地、壬水可用——日主偏旺"),
    ("DTC008", "偏旺", "日主根元亦固", "所称太旺者为水势；原书谓日主根元亦固——日主偏旺"),
    ("DTC009", "中和", "虽日坐禄支，不致浮泛", "所称太旺者为水势；原书谓日坐禄支而不浮泛，未言衰旺——取中和"),
    ("DTC010", "偏旺", "财虽旺，不能破印", "所称太旺者为财势；原书谓坐下戌燥土、印护身——日主偏旺"),
    ("DTC011", "偏旺", "满局皆木", "日主甲木生于仲春、满局皆木——日主偏旺（所称衰极者为时支子水）"),
    ("DTC013", "偏弱", "伤官太旺，过于泄气", "所称太旺者为伤官；庚金泄气太过——日主偏弱"),
    ("DTC014", "偏旺", "金水太旺", "所称太旺者为金水，日主壬水得党——日主偏旺"),
    ("DTC015", "偏弱", "日元反弱", "原文明言「日元反弱」——日主偏弱（所称太旺者为金气）"),
)


def build() -> dict:
    src = json.loads(SRC_POOL.read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in src.get("cases") or []}
    cases = []
    for cid, strength, phrase, reason in MANUAL:
        case = by_id.get(cid)
        if case is None:
            raise ValueError(f"源池已无 {cid}（重挖后 id 变动？）")
        if phrase not in (case.get("source_quote") or ""):
            raise ValueError(f"{cid} 所引原话片段不是判语中的逐字子串：{phrase}")
        cases.append({
            "id": f"{ID_PREFIX}{len(cases) + 1:03d}",
            "source_quote": case["source_quote"],
            "source_line": case["source_line"],
            "head_line": case["head_line"],
            "pillars": case["pillars"],
            "real_datetime": case["real_datetime"],
            "phrase": phrase,
            "manual_strength": strength,
            "reason": reason,
            "verdict": None,
            "case_kind": "人工认定（逐条读判语，原话逐字可回查）",
            "enroll_status": "未开卷·不入册·不出分",
            "block": "未授权入册；人工认定只到日主强弱档，不含吉凶方向与用神判定",
            "dedup": "与在册案例及另两个候选池按四柱去重（沿用 565 批口径）",
            "notes": f"源池案 {cid}；原话「{phrase}」逐字在判语中；理由：{reason}",
        })

    return {
        "schema": "yi-case-pool/2",
        "batch": 569,
        "discipline": "bazi",
        "_comment": ("《滴天髓闡微》**人工认定版**候选池（569 批）：对 565 批机器池中 12 条"
                     "「主语不明」的旺衰逐条读判语后人工认定日主强弱档，所引原话逐字可回查。"
                     "本池为**新池**，565 批机器池的一次性开封效力不受影响；本池同样**未开卷**。"),
        "source": {
            "file": "data/sources/di-tian-sui-chan-wei.wikitext.txt",
            "sha256": hashlib.sha256(M_.B_.SRC.read_bytes()).hexdigest(),
            "segment": "与 565 批机器池同源，12 案逐条人工认定",
        },
        "policy": {
            "照录": "source_quote 为底本判语行逐字子串（程序化截取）；所引原话片段逐字在判语中，复验器逐条核。",
            "人工认定": "日主强弱档由人读判语后给出，理由必写；「太旺／衰极」若指忌神或官杀，理由中写明为何不取该词。",
            "expected": "整池不写 expected／吉凶方向／用神——反推属重罪（AGENTS.md §三.4）。",
            "去重": "四柱与在册案例及另两个候选池互斥（沿用 565 批口径）。",
            "开卷": "一次性：须用户显式授权；开卷前状态与哈希须与登记一致；n<30 不出率值。",
        },
        "preregistration": {
            "frozen_at": "569 批（未开卷）",
            "判卷规则": "逐例判红绿：引擎 strength.strength（偏弱／偏旺／中和）与本池人工认定档比对；只出逐例红绿，n<30 不出率值。",
            "禁止": "不得事后改判；改判须登记新记录（§六.3）。不得把本池内容反推为 expected。",
            "开卷条件": "用户显式授权；开卷前状态与哈希须与本记录一致。",
        },
        "cases": cases,
        "excluded": [],
        "open_result": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="滴天髓人工认定候选池")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pool = build()
    text = json.dumps(pool, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"[dts-manual] 已写入 {OUT.name}：人工认定 {len(pool['cases'])} 案")
        return 0
    if args.check:
        if not OUT.is_file():
            print("  × 缺候选池文件（跑 --write）")
            return 1
        if OUT.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            print("  × 候选池与源池/人工表不一致（重跑 --write）")
            return 1
        print(f"  √ 人工认定池与源池逐字节一致：{len(pool['cases'])} 案")
        return 0
    print(f"人工认定 {len(pool['cases'])} 案（--write 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
