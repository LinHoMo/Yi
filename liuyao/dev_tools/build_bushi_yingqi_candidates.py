# -*- coding: utf-8 -*-
"""《易冒》＋《易林補遺》带**单点应期**命例 → 六爻候选池（573 批，未开卷）。

起因：六爻侧现成的判卷指标是 546 批冻结的「顶-1 应期支一致」；但仓内带单点应期书证的占例
几乎被挖尽——扫全部 12 部六爻底本，"含两个干支日＋卦名＋应期标记"的行只有 17 行，其中
《卜筮全书》可判的 2 行正是 BQS 已开卷用掉的。本批改从**体例最规整**的《易冒》下手：
该书通篇用「X建Y日占…得A之B卦…应Z日」的写法，逐条读完可析出**起卦日＋月支＋卦名＋
单点应期支**四要素齐备的占例 17 条（该书此前**零案例**被提取）。

口径（冻结）：
  · 引文一律由构建器从底本**程序化截取**（按句界切分、定位到含起卦句与应期句的那一段），不手抄；
  · **不写 expected／吉凶方向**：只登记书载的起卦四要素与**书载应期支**；
  · 应期支必须**逐字出现在引文里**，否则构建即失败；
  · 与在册案例、其余候选池按「起卦日＋卦名」去重。

    python dev_tools/build_bushi_yingqi_candidates.py --write
    python dev_tools/build_bushi_yingqi_candidates.py --check
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

SRC = {
    "yimao": DISC / "data" / "sources" / "yimao_dz.dz.txt",
    "yilin_buyi": DISC / "data" / "sources" / "yilin_buyi_dz.dz.txt",
}
OUT = DISC / "data" / "cases" / "bushi_yingqi_candidates.json"
ID_PREFIX = "BYQ"

# ── 人工认定表（573 批逐条读完《易冒》《易林補遺》相应段落后签定）──────────────
# (书, 行号, 月支, 起卦日干支, 本卦, 变卦, 书载应期支, 备注)
MANUAL: tuple[tuple, ...] = (
    ("yimao", 427, "寅", "辛亥", "节", "中孚", "丁巳", "摇会，应丁巳日得会"),
    ("yimao", 435, "午", "己巳", "大畜", "小畜", "丙子", "占妻病，应在当日即亡，后待丙子日而死"),
    ("yimao", 435, "未", "戊午", "乾", "小畜", "甲午", "占家宅，至甲午日而回禄"),
    ("yimao", 435, "酉", "甲子", "夬", "大过", "丁卯", "卜子归期，宜在丁卯日到"),
    ("yimao", 437, "未", "丙午", "遁", "节", "壬申", "占访友，应爻在壬申，是以壬申日遇"),
    ("yimao", 437, "巳", "乙丑", "睽", "咸", "丁卯", "占子归，应丁卯日至"),
    ("yimao", 769, "午", "辛卯", "睽", "未济", "己酉", "占晴，雨至己酉日方霁"),
    ("yimao", 779, "午", "甲申", "渐", "涣", "丙申", "占晴，及丙申日子孙当见而后大晴"),
    ("yimao", 982, "午", "甲寅", "大过", "", "庚午", "自筮身孕，后庚午日产"),
    ("yimao", 1021, "未", "甲辰", "屯", "革", "戊申", "占子痘，于戊申日乃变脾病而不治"),
    ("yimao", 1049, "亥", "甲申", "姤", "升", "壬辰", "占妻身，后交子月壬辰日病势渐解（含月限定）"),
    ("yimao", 1051, "寅", "庚子", "夬", "革", "壬寅", "占子病，后壬寅日症变"),
    ("yimao", 1304, "酉", "丁酉", "比", "", "庚子", "占庚子日摇会，果获之"),
    ("yimao", 1459, "辰", "甲辰", "大有", "", "乙卯", "占弟兄，后应乙卯日到"),
    ("yimao", 1459, "巳", "己酉", "剥", "旅", "甲寅", "占仆来，后及甲寅日乃至"),
    ("yilin_buyi", 217, "亥", "甲辰", "家人", "益", "己酉", "十月甲辰日卜得家人之益，果应己酉日到"),
)

BOOK_CN = {"yimao": "《易冒》", "yilin_buyi": "《易林補遺》"}
# 月支 → 月序（古法「X建」即月建；引擎解析用月序）
MONTH_ORDER = {"寅": "正", "卯": "二", "辰": "三", "巳": "四", "午": "五", "未": "六",
               "申": "七", "酉": "八", "戌": "九", "亥": "十", "子": "冬", "丑": "腊"}


def _segments(line: str) -> list[str]:
    """按句界切分（保留原文，不改字）。"""
    parts = re.split(r"(?<=。)|(?<=．)", line)
    return [p for p in (x.strip() for x in parts) if p]


def build() -> dict:
    texts = {k: p.read_text(encoding="utf-8").splitlines() for k, p in SRC.items()}
    cases, problems = [], []
    for book, line_no, month, day_gz, orig, changed, yingqi, note in MANUAL:
        lines = texts[book]
        if not (1 <= line_no <= len(lines)):
            problems.append(f"{book} L{line_no} 行号越界")
            continue
        seg = None
        for cand in _segments(lines[line_no - 1]):
            if day_gz + "日" in cand and yingqi + "日" in cand:
                seg = cand
                break
        if seg is None:
            problems.append(f"{book} L{line_no}：未找到同时含起卦日「{day_gz}日」与应期「{yingqi}日」的句段")
            continue
        # 月建写法两式：《易冒》作「X建」，《易林補遺》作「十月」等月序
        if f"{month}建" not in seg and f"{MONTH_ORDER[month]}月" not in seg:
            problems.append(f"{book} L{line_no}：句段未见月建「{month}建」或「{MONTH_ORDER[month]}月」（可能跨句）")
            continue
        cases.append({
            "id": f"{ID_PREFIX}{len(cases) + 1:03d}",
            "book": BOOK_CN[book],
            "source_quote": seg,
            "source_line": line_no,
            "month_branch": month,
            "month_order": MONTH_ORDER[month],
            "day_ganzhi": day_gz,
            "hexagram_text": orig,
            "changed_text": changed,
            "book_yingqi_ganzhi": yingqi,
            "book_yingqi_branch": yingqi[-1],
            "book_yingqi_text": f"{yingqi}日",
            "note": note,
            "verdict": None,
            "case_kind": "占验实例（带单点应期书证）",
            "enroll_status": "未开卷·不入册·不出分",
            "block": "未授权入册；本池只登记书载起卦四要素与书载应期支，不含吉凶方向",
            "dedup": "与在册案例及其余候选池按「起卦日＋卦名」去重",
            "notes": "引文为底本该行句段的逐字截取（程序化，不手抄）",
        })
    if problems:
        raise ValueError("；".join(problems))

    return {
        "schema": "yi-case-pool/2",
        "batch": 573,
        "discipline": "liuyao",
        "_comment": ("六爻「带单点应期书证」候选池（573 批新建，未开卷）。语料来自《易冒》"
                     "「X建Y日占…得A之B卦…应Z日」体例（该书此前零案例被提取）与《易林補遺》一条。"
                     "主指标沿用 546 批冻结的「顶-1 应期支一致」；n<30 只报逐例红绿。"),
        "source": {
            "yimao": {"file": "data/sources/yimao_dz.dz.txt",
                       "sha256": hashlib.sha256(SRC["yimao"].read_bytes()).hexdigest()},
            "yilin_buyi": {"file": "data/sources/yilin_buyi_dz.dz.txt",
                           "sha256": hashlib.sha256(SRC["yilin_buyi"].read_bytes()).hexdigest()},
        },
        "policy": {
            "照录": "source_quote 为底本该行句段的逐字截取（程序化切句定位，不手抄）。",
            "expected": "整池不写 expected／吉凶方向／用神——反推属重罪（AGENTS.md §三.4）。",
            "应期": "book_yingqi_branch 必须是书载**单点**应期支，逐字出现在引文中；含月限定者在 note 注明。",
            "去重": "起卦日＋卦名与在册案例、其余候选池互斥。",
            "开卷": "一次性：须用户显式授权；主指标沿用 546 批冻结的「顶-1 应期支一致」；n<30 不出率值。",
        },
        "preregistration": {
            "frozen_at": "573 批（未开卷）",
            "判卷规则": "逐例判红绿：引擎对该案给出应期支候选，判顶-1 是否命中书载单点应期支；只出逐例红绿，n<30 不出率值。",
            "禁止": "不得事后改判；改判须登记新记录（§六.3）。不得把本池内容反推为 expected。",
            "开卷条件": "用户显式授权；开卷前状态与哈希须与本记录一致。",
        },
        "cases": cases,
        "excluded": [],
        "open_result": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="六爻单点应期候选池")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        pool = build()
    except ValueError as exc:
        print(f"  × 构建失败：{exc}")
        return 1
    text = json.dumps(pool, ensure_ascii=False, indent=2) + "\n"
    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print(f"[byq] 已写入 {OUT.name}：候选 {len(pool['cases'])} 案")
        return 0
    if args.check:
        if not OUT.is_file():
            print("  × 缺候选池文件（跑 --write）")
            return 1
        if OUT.read_text(encoding="utf-8").replace("\r\n", "\n") != text:
            print("  × 候选池与底本/人工表不一致（重跑 --write）")
            return 1
        print(f"  √ 候选池与底本逐字节一致：{len(pool['cases'])} 案")
        return 0
    print(f"候选 {len(pool['cases'])} 案（--write 落盘）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
