# -*- coding: utf-8 -*-
"""《神峰通考》命例 → 未开卷候选池（566 批）。

《神峰通考》的命例是**行首四柱 + 断语**的紧凑体例（如「辛巳 丁酉 丙寅 己丑    吾郡李志富公富命身旺任财」），
可与《滴天髓》的竖排四柱块一样**机械提取**：四柱由行首正则解析、断语取该行余文（逐字），
不靠人眼誊抄。

与 565 批《滴天髓》机器认定同一口径：
  ① 四柱由行首正则程序化解析；
  ② 断语逐字取自同一行（池内只存行锚 + 断语全文，不手抄）；
  ③ 与**在册案例**同四柱者剔除（545 批口径：同源书承袭同案）；
  ④ 与已建《滴天髓》候选池同四柱者亦剔除（避免两池重复计入）。

**本池未开卷**：只登记书证、四柱、断语、命例标签（从固定词表机械抽取的格局／强弱词）与
真实时刻重建值；**不写 expected／吉凶方向／用神**。开卷须另获用户授权。

    python dev_tools/mine_shenfeng_candidates.py --write
    python dev_tools/mine_shenfeng_candidates.py --check
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
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import mine_dts_candidates as M_  # noqa: E402  复用真实时刻重建与在册去重

SRC = DISC / "data" / "sources" / "shenfeng_tongkao_dz.dz.txt"
OUT = DISC / "data" / "cases" / "shenfeng_candidates.json"
DTS_POOL = DISC / "data" / "cases" / "dts_candidates.json"
ID_PREFIX = "SFC"

GZ = r"[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]"
LEAD = re.compile(rf"^({GZ})\s+({GZ})\s+({GZ})\s+({GZ})\s+(.*)$")

# 命例标签词表（固定、机械抽取；只描述格局／强弱形态，不含吉凶方向）
LABELS = (
    "制杀太过", "从财", "从官", "从杀", "从儿", "化官", "化杀", "化财", "化气",
    "身旺任财", "身旺用财", "财旺身弱", "身弱", "身旺", "中和", "太过", "不及",
    "用神", "专旺", "食神生财", "伤官生财", "伤官佩印", "官印", "财官",
)


def parse_cases() -> list[dict]:
    out = []
    for lineno, raw in enumerate(SRC.read_text(encoding="utf-8").splitlines(), 1):
        text = raw.strip()
        m = LEAD.match(text)
        if not m:
            continue
        pillars = [m.group(i) for i in (1, 2, 3, 4)]
        speech = m.group(5).strip()
        if not speech:
            continue
        labels = [w for w in LABELS if w in speech]
        # 格局名后缀：断语末尾的「…格」（如「生生活巳格」「去留官格」），机械截取；
        # 只作标签用，可能含人名等前后缀，故名之 suffix，不当作严格格局名
        pattern = ""
        m2 = re.search(r"([\u4e00-\u9fff]{1,8}格)(?:[。；;]|$)", speech)
        if m2:
            pattern = m2.group(1)
        # 性别：断语里的「女／男」自指（此书命例多女命，夫星／子星规则不同）
        gender = "女" if "女" in speech else ("男" if "男" in speech else "")
        out.append({
            "head_line": lineno,
            "pillars": pillars,
            "speech": speech,
            "labels": labels,
            "pattern_suffix": pattern,
            "gender": gender,
        })
    return out


def mine() -> dict:
    used = M_.enrolled_pillars()
    dts_pillars: set[tuple] = set()
    if DTS_POOL.is_file():
        dts = json.loads(DTS_POOL.read_text(encoding="utf-8"))
        for case in dts.get("cases", []) or []:
            p = case.get("pillars") or {}
            dts_pillars.add((p.get("year"), p.get("month"), p.get("day"), p.get("hour")))

    picked, rejected = [], []
    seen_speech: set[str] = set()
    for block in parse_cases():
        key = tuple(block["pillars"])
        if key in used:
            rejected.append({"source_line": block["head_line"], "reason": "与在册案例同四柱（同源书承袭同案，545 批口径）"})
            continue
        if key in dts_pillars:
            rejected.append({"source_line": block["head_line"], "reason": "与《滴天髓》候选池同四柱（两池不重复计入）"})
            continue
        norm = "".join(block["speech"].split())
        if norm in seen_speech:
            rejected.append({"source_line": block["head_line"], "reason": "断语与本池前案逐字相同（同一考点不重复计入）"})
            continue
        used.add(key)
        seen_speech.add(norm)
        picked.append(block)

    # 四柱可还原：穷举 1900–2100 找得出真实时刻者才收；找不到者疑底本讹字（五虎遁／五鼠遁违律）
    dt_index = M_.B_.build_datetime_index({tuple(b["pillars"]) for b in picked})
    keep = []
    for block in picked:
        key = tuple(block["pillars"])
        if key not in dt_index:
            rejected.append({"source_line": block["head_line"],
                             "reason": "四柱穷举 1900–2100 找不出真实时刻（五虎遁／五鼠遁违律，疑底本讹字）"})
            continue
        keep.append(block)
    picked = keep

    cases = []
    for block in picked:
        pillars = block["pillars"]
        key = tuple(pillars)
        cases.append({
            "id": f"{ID_PREFIX}{len(cases) + 1:03d}",
            "source_quote": block["speech"],
            "source_line": block["head_line"],
            "pillars": {"year": pillars[0], "month": pillars[1], "day": pillars[2], "hour": pillars[3]},
            "real_datetime": dt_index.get(key),
            "labels": block["labels"],
            "pattern_suffix": block["pattern_suffix"],
            "gender": block["gender"],
            "verdict": None,
            "case_kind": "命例（行首四柱＋断语，程序化提取）",
            "enroll_status": "未开卷·不入册·不出分",
            "block": "未授权入册；标签只是格局／强弱形态词，不含吉凶方向与用神判定",
            "dedup": "已与在册案例及《滴天髓》候选池按四柱去重",
            "notes": "断语为该行余文逐字截取；四柱由行首正则解析，非手抄",
        })

    return {
        "schema": "yi-case-pool/2",
        "batch": 566,
        "discipline": "bazi",
        "_comment": ("《神峰通考》命例候选池（566 批新建，未开卷）。行首四柱＋断语的紧凑体例，"
                     "机械可提取；只登记书证、四柱、断语、标签与真实时刻重建值，"
                     "不写 expected／吉凶／用神。"),
        "source": {
            "file": "data/sources/shenfeng_tongkao_dz.dz.txt",
            "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(),
            "segment": "行首四柱的命例行",
        },
        "policy": {
            "照录": "source_quote 必须是底本该行余文的逐字子串（程序化截取，不手抄）；四柱由行首正则解析。",
            "expected": "整池不写 expected／吉凶方向／用神——反推属重罪（AGENTS.md §三.4）。",
            "标签": "只从固定词表机械抽取格局／强弱形态词，不表达吉凶，也不作引擎侧判定。",
            "去重": "与在册案例、《滴天髓》候选池按四柱去重（三方互斥）。",
            "开卷": "一次性：须用户显式授权；开卷前状态与哈希须与登记一致；n<30 不出率值。",
        },
        "preregistration": {
            "frozen_at": "566 批（未开卷）",
            "判卷规则": "逐例判红绿：引擎对每案给出强弱与格局标签，与本案书载标签比对；只出逐例红绿，n<30 不出率值。",
            "禁止": "不得事后改判；改判须登记新记录（§六.3）。不得把本池内容反推为 expected。",
            "开卷条件": "用户显式授权；开卷前状态与哈希须与本记录一致。",
        },
        "cases": cases,
        "excluded": rejected,
        "open_result": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="《神峰通考》候选池")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    pool = mine()
    text = json.dumps(pool, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"[shenfeng] 已写入 {OUT.name}：候选 {len(pool['cases'])} 案，excluded {len(pool['excluded'])} 项")
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
