# -*- coding: utf-8 -*-
"""《滴天髓闡微》命造块机器认定 → 未开卷候选池（565 批）。

背景：`build_dts_cases.py` 能从底本扫出**全部 513 个**竖排四柱命造块，但当年只**人工认定 12 条**
入评分集（`APPROVED` 表），其余 500 余块从未被认领——瓶颈是人工认定，不是机器能力。
本器把"选哪些块"这一步机械化：凡**判语里出现自指日主的强度表述**（身弱／身旺／财多身弱／
中和纯粹／衰极／太旺……），且通过与建器同一套机械校验者，即认定入池。

四条机械校验（与 `build_dts_cases.py` 同一口径，判据不靠人眼）：
  ① 四柱：块内四柱须与登记一致（登记由块本身程序化提取，不手抄）；
  ② 原话：所取判语片段须**逐字出现在**该案判语中；
  ③ 自洽：判语提到的日干／月支须与日柱／月柱相符（不符即弃）；
  ④ 去重：四柱与**在册案例**相同者不入池（同源书承袭同案，545 批口径）。

**本池未开卷**：不写 expected／吉凶判定／用神等任何"引擎侧答案"，只登记书证、四柱、
原话、归类与真实时刻重建值。开卷须另获用户授权（预注册见池内 `preregistration`）。
归类只做**强度档**（偏弱／偏旺／中和），由判语里的关键词机械映射，不含吉凶方向。

    python dev_tools/mine_dts_candidates.py --write
    python dev_tools/mine_dts_candidates.py --check
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
for _p in (str(DISC / "scripts"), str(DISC / "core")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, str(HERE))

import build_dts_cases as B_  # noqa: E402  复用底本解析与历法重建（唯一真源）

OUT = DISC / "data" / "cases" / "dts_candidates.json"
SPLITS_DIR = DISC / "data" / "cases"
ID_PREFIX = "DTC"

# 机器认定的关键词锚：只收**自指日主**的表述。
# 不收「君／君杀／臣盛」等需上下文判断的词（人工表里那类由人认定，见 build_dts_cases.APPROVED）。
ANCHORS: tuple[tuple[str, str], ...] = (
    ("日主本衰", "偏弱"), ("此衰极从弱之理", "偏弱"), ("财多身弱", "偏弱"),
    ("中和纯粹", "中和"), ("中和之象", "中和"), ("中和之气", "中和"),
    ("强旺极矣", "偏旺"), ("旺极矣", "偏旺"), ("太旺", "偏旺"), ("身旺", "偏旺"),
    ("身弱", "偏弱"), ("身衰", "偏弱"), ("衰弱", "偏弱"), ("衰极", "偏弱"),
    ("从弱", "偏弱"),
)


def enrolled_pillars() -> set[tuple]:
    """在册案例的四柱集合（去重门）。"""
    used: set[tuple] = set()
    for path in sorted(SPLITS_DIR.glob("*.json")):
        if path.name == OUT.name:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for case in data.get("cases", []) or []:
            pil = case.get("pillars") or {}
            if pil.get("year") and pil.get("day"):
                used.add((pil.get("year"), pil.get("month"), pil.get("day"), pil.get("hour")))
    return used


def mine() -> dict:
    src_text = B_.SRC.read_text(encoding="utf-8")
    lines = src_text.splitlines()
    blocks = B_.parse_blocks(lines)
    manual = {row[0] for row in B_.APPROVED}
    used = enrolled_pillars()

    picked, rejected = [], []
    for block in blocks:
        head = block["head_line"]
        if head in manual:
            rejected.append({"source_line": head, "reason": "已由人工认定并入评分集（build_dts_cases.APPROVED），不再重复入池"})
            continue
        speech = block["speech"]
        hit = next(((kw, cat) for kw, cat in ANCHORS if kw in speech), None)
        if not hit:
            continue
        pillars = block["pillars"]
        day_ref, month_ref = B_.DAY_REF.search(speech), B_.MON_REF.search(speech)
        if day_ref and day_ref.group(1) != pillars[2][0]:
            rejected.append({"source_line": head, "reason": f"判语日主 {day_ref.group(1)} ≠ 日柱 {pillars[2]}"})
            continue
        if month_ref and month_ref.group(1) != pillars[1][1]:
            rejected.append({"source_line": head, "reason": f"判语月支 {month_ref.group(1)} ≠ 月柱 {pillars[1]}"})
            continue
        key = tuple(pillars)
        if key in used:
            rejected.append({"source_line": head, "reason": "与在册案例同四柱（同源书承袭同案，545 批口径）"})
            continue
        used.add(key)
        picked.append(dict(block, phrase=hit[0], category=hit[1]))

    # 真实时刻重建：穷举 1900–2100 逐日反查四柱全同者（确定性，非猜）
    dt_index = B_.build_datetime_index({tuple(b["pillars"]) for b in picked})

    cases = []
    for block in picked:
        pillars = block["pillars"]
        key = tuple(pillars)
        cases.append({
            "id": f"{ID_PREFIX}{len(cases) + 1:03d}",
            "source_quote": block["speech"],
            "source_line": block["speech_line"],
            "head_line": block["head_line"],
            "pillars": {"year": pillars[0], "month": pillars[1], "day": pillars[2], "hour": pillars[3]},
            "real_datetime": dt_index.get(key),
            "phrase": block["phrase"],
            "category": block["category"],
            "verdict": None,
            "case_kind": "机器认定（关键词锚定＋四柱机械校验）",
            "enroll_status": "未开卷·不入册·不出分",
            "block": "未授权入册；归类只是强度档，不含吉凶方向与用神判定",
            "dedup": "已与在册案例按四柱去重（无同四柱）",
            "notes": "引文为底本判语行逐字截取；四柱由程序化解析所得，非手抄",
        })

    return {
        "schema": "yi-case-pool/2",
        "batch": 565,
        "discipline": "bazi",
        "_comment": ("《滴天髓闡微》命造块机器认定候选池（565 批新建，未开卷）。与既有 "
                     "`bazi_external_cases.json`（人工 12 条的评分集）**分池**：本池只登记书证、四柱、"
                     "原话、强度档与真实时刻重建值，不写 expected／吉凶／用神。"),
        "source": {
            "file": "data/sources/di-tian-sui-chan-wei.wikitext.txt",
            "sha256": hashlib.sha256(B_.SRC.read_bytes()).hexdigest(),
            "segment": "全书 513 个竖排四柱命造块",
        },
        "policy": {
            "照录": "source_quote 必须是底本判语行的逐字子串（程序化截取，不手抄）；四柱由 parse_blocks 解析，非手抄。",
            "expected": "整池不写 expected／吉凶方向／用神——反推属重罪（AGENTS.md §三.4）。",
            "归类": "只做强度档（偏弱／偏旺／中和），由判语关键词机械映射；不表达吉凶。",
            "去重": "四柱与在册案例相同者不入池（545 批口径）；人工已认定的 12 条不重复入池。",
            "开卷": "一次性：须用户显式授权；开卷前本池状态与哈希须与登记一致；n<30 不出率值。",
        },
        "preregistration": {
            "frozen_at": "565 批（未开卷）",
            "判卷规则": "逐例判红绿：引擎对每案给出强弱判定与书载强度档比对；只出逐例红绿，n<30 不出率值。",
            "禁止": "不得事后改判；改判须登记新记录（§六.3）。不得把本池内容反推为 expected。",
            "开卷条件": "用户显式授权；开卷前状态与哈希须与本记录一致。",
        },
        "cases": cases,
        "excluded": rejected,
        "open_result": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="《滴天髓闡微》机器认定候选池")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pool = mine()
    text = json.dumps(pool, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"[dts] 已写入 {OUT.name}：候选 {len(pool['cases'])} 案，excluded {len(pool['excluded'])} 项")
        return 0
    if args.check:
        if not OUT.is_file():
            print("  × 缺候选池文件（跑 --write）")
            return 1
        if OUT.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            print("  × 候选池与底本/规则不一致（重跑 --write）")
            return 1
        print(f"  √ 候选池与底本逐字节一致：{len(pool['cases'])} 案")
        return 0
    print(f"候选 {len(pool['cases'])} 案；excluded {len(pool['excluded'])} 项（--write 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
