# -*- coding: utf-8 -*-
"""课经集释义抽取/合并：给 data/kemu.json 的每条课目补「定义句 + 卷篇出处」。

判据源（只读原料）：data/sources/liu-ren-da-quan-juan{7,8,9,10}.wikitext.txt
= 《六壬大全》卷七~卷十「课经集一~四」（维基文库四库本，provenance 同目录）。

做法与纪律：
  * 课目名以**卷一「课目」歌诀**（data/kemu.json 现有条目 + 前六门）为准；
    课经集标题多为「X课」，故默认对应 name+"课"，不规整者走显式 ALIAS 表——
    **不做模糊匹配**，找不到就打印出来，不静默（铁律三：引文必须可回指）。
  * 定义句取该课标题后第一个以「凡」起头的段落（课经体例：凡…为X课）。
  * 合并前逐条断言：`note` 抽汉字后必须是课经集原文的连续子串，否则拒绝写入。
  * 默认只报告（dry-run）；`--write` 才落盘。

    python dev_tools/build_kemu_notes.py            # 只报告
    python dev_tools/build_kemu_notes.py --write    # 合并进 data/kemu.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parents[1]
SRC = ROOT / "data" / "sources"
OUT = DISC / "data" / "kemu.json"

sys.path.insert(0, str(ROOT / "core"))
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对

# kemu.json 的 `_comment`（`--write` 与 `--check` 共用同一份，避免两处各写一遍）
COMMENT_LINES = [
    "六壬大全 卷一「课目」诀表（书源自编号 一…六五，缺「五八」一条，故实收 64 条；"
    "缺号登记在 dev_tools/check.py 的 KEMU_NUMBERING_GAP，本仓不臆补。"
    "1–6 即九宗门前六门，判据见 "
    "scripts/jiuzongmen.py + scripts/kemu.py）。verse 逐字（铁律三：引文可回指）。",
    "note = 卷七~卷十「课经集」该课定义句（凡…为X课），note_src 记卷篇出处；",
    "note 由 dev_tools/build_kemu_notes.py 从书源抽取并断言可回指，勿手改。",
    "implemented=true 为已落机械判据（scripts/kemu.py 的 IMPLEMENTED）；",
    "未落者只登记诀文与释义，不得在 analyze 中输出该课目名（不写占位识别）。",
    "rules = 课目机械判据参数（旬奇/日奇），出处见其 _meta。",
]

CN = re.compile(r"[\u4e00-\u9fff]")
JUANS = {7: "课经集一", 8: "课经集二", 9: "课经集三", 10: "课经集四"}

# 卷一「课目」歌诀里的前六门（原表缺自编号 1~6 条，此处按书源逐字补齐；诀文照录书源，
# 含四库本讹字「昂星」「旡」——正字说明另见 kemu.json 的 variant 字段）
FRONT_SIX = [
    {"name": "元首", "verse": "元首一上克其下，天地得位品亨通"},
    {"name": "重审", "verse": "重审一下贼乎上，以臣诤君详审行"},
    {"name": "知一", "verse": "知一上下有二克，择比而用先执中"},
    {"name": "涉害", "verse": "涉害俱比俱不比，度难归家分深浅"},
    {"name": "遥克", "verse": "遥克神日互相克，蒿矢弹射势为轻"},
    {"name": "昴星", "verse": "昂星四课旡克遥，阴伏掩相阳转逢",
     "variant": "书源作「昂星」（讹字）"},
]

# 卷一歌诀名 → 课经集标题（只列不规整者；其余按 name+"课" 直配）
ALIAS = {
    "时太": "时泰课",
    "繁华": "荣华课",
    "玄胎": "元胎课",
    "联珠": "连珠课",
    "赘胥": "赘婿课",
    "无禄": "无禄绝嗣课",
    "昂星": "昴星课",
    "昴星": "昴星课",
    "斲轮": "斫轮课",       # 卷一作「斲轮」，卷八标题作「斫轮」（同课异写）
    "涉害": "",             # 课经集未收涉害课，释义在 verdicts.json「men」条
    "乱首": "",             # 课经集未收（卷一歌诀有诀无释）
    "孤寡": "",             # 课经集未收
    "地盘": "",             # 「地盘为孤天盘寡」与孤寡同条，非独立课
}

# 课目判据参数（不是断语）。逐字出自《六壬大全》卷七「三奇课」「六仪课」定义句：
#   「如甲子、甲戌旬用丑，甲申、甲午旬用子；甲辰、甲寅旬用亥，此为旬三奇。
#     甲日用午、丙奇辰、乙巳、丁卯、戊奇寅、己丑、庚未、辛申位、壬奇取酉、癸戌」
RULES = {
    "_meta": "课目机械判据参数（非断语）。出处《六壬大全》卷七「三奇课」「六仪课」。",
    "xun_qi": {"子": "丑", "戌": "丑", "申": "子", "午": "子",
               "辰": "亥", "寅": "亥"},
    "stem_qi": {"甲": "午", "乙": "巳", "丙": "辰", "丁": "卯", "戊": "寅",
                "己": "丑", "庚": "未", "辛": "申", "壬": "酉", "癸": "戌"},
}


def _hanzi(s: str) -> str:
    return "".join(CN.findall(s))


def _implemented() -> set[str]:
    """已落判据的课目名——唯一真值源是 scripts/kemu.py 的 IMPLEMENTED。"""
    sys.path[:0] = [str(DISC / "scripts"), str(ROOT / "core")]
    from kemu import IMPLEMENTED
    return set(IMPLEMENTED)


def juan_text() -> dict[str, str]:
    parts = {}
    for n in JUANS:
        p = SRC / f"liu-ren-da-quan-juan{n}.wikitext.txt"
        parts[n] = p.read_text(encoding="utf-8")
    return parts


def juan_defs(text: str) -> dict[str, str]:
    """卷内 {课标题: 定义句}。定义句 = 标题行后第一个以「凡」起头的段落。"""
    lines = [l.strip() for l in text.splitlines()]
    heads = [i for i, l in enumerate(lines)
             if re.fullmatch(r"[\u4e00-\u9fff]{2,8}课", l)]
    out: dict[str, str] = {}
    for idx, i in enumerate(heads):
        end = heads[idx + 1] if idx + 1 < len(heads) else len(lines)
        for l in lines[i + 1:end]:
            if l.startswith("凡"):
                out.setdefault(lines[i], l)
                break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="课经集释义抽取/合并")
    ap.add_argument("--write", action="store_true", help="写回 data/kemu.json")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对「就地合并后应落盘的那份」是否与入库 data/kemu.json 一致")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    data = json.loads(OUT.read_text(encoding="utf-8"))
    entries = data["entries"]
    have = {e["name"] for e in entries}
    added = [e for e in FRONT_SIX if e["name"] not in have]
    entries[:0] = [dict(e) for e in added]

    juan = juan_text()
    defs: dict[str, tuple[str, str]] = {}
    for n, text in juan.items():
        for title, defn in juan_defs(text).items():
            key = title[:-1]                       # 去「课」字
            defs[key] = (defn, f"《六壬大全》卷{n}·{JUANS[n]}")
            defs[title] = (defn, f"《六壬大全》卷{n}·{JUANS[n]}")

    miss, ok = [], 0
    for e in entries:
        title = ALIAS.get(e["name"], e["name"] + "课")
        hit = defs.get(title) or defs.get(e["name"])
        if not hit:
            miss.append(e["name"])
            continue
        defn, src = hit
        e["note"] = defn
        e["note_src"] = src
        ok += 1

    # 断言：note 逐字可回指（抽汉字后为课经集原文连续子串）
    blob = _hanzi("".join(juan.values()))
    bad = [e["name"] for e in entries
           if e.get("note") and _hanzi(e["note"]) not in blob]
    # 断言：三奇判据参数确有书源依据（定义句里逐字写着这两段映射）
    qi_def = defs.get("三奇课", ("", ""))[0] or defs.get("三奇", ("", ""))[0]
    for _frag in ("如甲子甲戌旬用丑", "甲日用午"):
        if _frag not in _hanzi(qi_def):
            bad.append(f"三奇课定义缺「{_frag}」→ RULES 无书源依据")
    # implemented 旗标从 scripts/kemu.py 的 IMPLEMENTED 派生（不在此另立真值）
    implemented = _implemented()
    unknown = sorted(implemented - {e["name"] for e in entries})
    if unknown:
        bad.append(f"IMPLEMENTED 含表外课名：{'、'.join(unknown)}")
    for e in entries:
        e["implemented"] = e["name"] in implemented

    # 断言：verse 逐字可回指卷一「课目」歌诀段
    j1 = (SRC / "liu-ren-da-quan.wikitext.txt").read_text(encoding="utf-8")
    seg = _hanzi(j1[j1.index("课目"):j1.index("补论")])
    bad_v = [e["name"] for e in entries if _hanzi(e["verse"]) not in seg]

    print(f"课目 {len(entries)} 条｜新增前六门 {len(added)} 条"
          f"｜有释义 {ok} 条｜无释义 {len(miss)} 条")
    if miss:
        print("  无释义（课经集未收或标题不规整，不静默）：", "、".join(miss))
    if bad:
        print("  × note 非课经集原文：", "、".join(bad))
    if bad_v:
        print("  × verse 非卷一歌诀原文：", "、".join(bad_v))
    if bad or bad_v:
        return 1
    # 要落盘的整份数据（`--write` 与 `--check` 共用同一构造，避免两份实现）
    data["rules"] = dict(RULES)
    data["_comment"] = list(COMMENT_LINES)

    if args.check:
        # 本建器是「**就地合并**」：先读入库 kemu.json，再补前六门/note/implemented/rules。
        # 故比对口径 = 「把要落盘的那份（已含上述补写）与入库文件比」——一致即证明
        # **重跑不会改变入库文件**，无需另立第二套真值。
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, data))
    if args.write:
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
        print(f"√ 已写回 {OUT.relative_to(ROOT).as_posix()}")
    else:
        print("（dry-run，未落盘；加 --write 写回）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
