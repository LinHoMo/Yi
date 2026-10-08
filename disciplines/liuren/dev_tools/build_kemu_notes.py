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

# 《六壬指南》日辰加临课目的旁证键（与课经集 entries 并列、不合并）
JIALIN_KEY = "zhinan_dz_jialin"

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
    # 课目**别名**（OPT-liuren_zhinan_dz-05，2026-10-07）：书源一课多名者在此登记
    # 别名 → 本仓课名。**只走别名，不另立课目**——同「赘婿／赘胥」的处理
    # （书源多作赘婿，本仓课名取卷一歌诀的「赘胥」）。消费方：
    # scripts/kemu.py::KE_NAME_VARIANTS 与 dev_tools/check.py 门 [1e]。
    "aliases": {
        "_meta": "别名 → 本仓课名/课名键。别名不作独立课目，不占卷一「课目」段的 64 条。",
        "无依": "井栏射",
        "无亲": "井栏射",
        "赘婿": "赘胥",
        "_三合四局": "OPT-liuren_cuiyan_dz-05：三合四局（曲直/炎上/从革/润下）别名与顺逆字段；"
                     "指向同一课目「全局」，以 ju_name 字段区分；"
                     "core 唯一真值源 KE_CYCLE/SAN_HE_GROUPS 不另立表",
        "曲直": "全局",
        "炎上": "全局",
        "从革": "全局",
        "润下": "全局",
    },
    # 三合四局（曲直/炎上/从革/润下）的**结构参数**（OPT-liuren_cuiyan_dz-05）：
    # 支局/顺逆合次序取自《萃言》各局总论段；branches 与 core 的 SAN_HE_GROUPS 同集，
    # 此处只登记**顺序**（顺合/逆合是课目判据，core 表不含顺序），不另立五行生克表。
    # `note` 是书源**摘要**（含跨行缀合），不是逐字引文——逐字要求约束的是
    # 课目 note/verse 与 data/cases/*/source_quote；这里刻意用 note 而非 verbatim 命名。
    "san_he_ju_extension": {
        "曲直": {
            "element": "木", "branches": ["亥", "卯", "未"],
            "顺合": ["亥卯未", "未亥卯"],
            "逆合": ["未卯亥", "卯亥未", "亥未卯"],
            "source": "data/sources/liuren_cuiyan_dz.dz.txt:127-129",
            "note": "木性本直，又复曲折也。顺合者理势自然，逆者事有曲折。春占取利于求财，诸事皆吉。",
        },
        "炎上": {
            "element": "火", "branches": ["寅", "午", "戌"],
            "顺合": ["寅午戌"],
            "逆合": ["戌午寅", "午寅戌", "寅戌午"],
            "source": "data/sources/liuren_cuiyan_dz.dz.txt:131-133",
            "note": "火之性也。顺合者凡事光明，逆合者凡事猛烈，主事成急速，虚多实少。",
        },
        "从革": {
            "element": "金", "branches": ["巳", "酉", "丑"],
            "顺合": ["酉丑巳"],
            "逆合": ["酉巳丑", "巳丑酉"],
            "source": "data/sources/liuren_cuiyan_dz.dz.txt:135-137",
            "note": "金须煅炼而成，有改革之意也。顺则有鼎新之象，逆则有肃杀之威。此课占婚大忌。",
        },
        "润下": {
            "element": "水", "branches": ["申", "子", "辰"],
            "顺合": ["申子辰", "子辰申", "辰申子"],
            "逆合": ["子申辰", "申辰子"],
            "source": "data/sources/liuren_cuiyan_dz.dz.txt:139-141",
            "note": "就下者水之性也。主悠游长久，事不迫促，然终不能静也。",
        },
    },
    # 九宗门枚举细则的**书源旁证**（OPT-liuren_xinjing_dz-01，2026-10-07）：
    # 只登记书源自述的枚举名单，作为 scripts/kemu.py 既有判据的第二书源，
    # **不新增判据**（别责／八专／返吟的判定仍走 jiuzongmen 判据树）。
    "xinjing_旁证": {
        "_meta": "《六壬星纪》九宗门枚举旁证。verbatim 为书源逐字，"
                 "「本仓判据」列记与既有判据的一致性；只作旁证，不引入断语。",
        "别责": {
            "verbatim": "刚三柔六共九课辛丑、辛未各有两课，丙辰、戊午、戊辰、丁酉、辛酉各有一课",
            "源": "《六壬星纪》L198",
            "本仓判据": "jiuzongmen 门「别责」＋全枚举守门 expect_bieze="
                        "{戊辰:1, 戊午:1, 丙辰:1, 辛未:2, 辛丑:2, 丁酉:1, 辛酉:1}"
                        "（刚日 3 柔日 6 共九课，与书源逐日相合）",
            "结论": "已落，与书源旁证一致（零新增）",
        },
        "八专": {
            "verbatim": "八专之课号芜淫丁未、癸丑、甲寅、己未、庚申，皆两课也",
            "源": "《六壬星纪》L216",
            "本仓判据": "jiuzongmen 门「八专」＋全枚举守门 expect_bazhuan_days="
                        "{甲寅, 庚申, 丁未, 己未, 癸丑}（五日，与书源逐日相合）",
            "结论": "已落，与书源旁证一致（零新增）",
        },
        "返吟无克六日": {
            "verbatim": "若夫丁未、己未、辛未、丁丑、己丑、辛丑六课无克，乃名无依",
            "源": "《六壬指南》L28（**重新定位**：星纪 L28 不含「无依」，"
                   "该句在指南 L28；指南 L148-L149 另有「反吟无依则复旧」"
                   "「反吟来去不定，故曰无依，无依倚也」两处）",
            "本仓判据": "jiuzongmen 返吟门 ke_name=井栏射（别名 无依／无亲），"
                        "全枚举守门 jinglanshe==6（丑未同干丁己辛）",
            "结论": "已落，别名走 aliases（不另立课目）",
        },
    },
    # 昼夜乘临生克分途的口径注记（OPT-liuren_zhizhi_yuding_dz-05）：
    # 该书源句**不是**「昼夜两套将」，而是「同一位支昼夜所乘之将不同 → 生克分途」。
    "day_night_route_口径": "同神昼夜乘临不同将则生克分途（非「昼夜两套将」）："
                           "十二天将名与其五行神昼夜同一，变的是同一位支昼夜所乘之将"
                           "（贵人昼夜取支不同故顺逆异、乘临亦异）。源《六壬直指御定》L679。",
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
    # 课名合法来源 = 《六壬大全》课经集 entries ∪ 《六壬指南》日辰加临旁证键。
    # 旁证走**独立书名键**是刻意设计：并入 entries 会污染「大全 64 条」计数门（§四.5 对拍口径）。
    # 但旁证条目必须自带 `_book` + `_note`，否则这个键就成了"无出处名字的收容所"。
    jialin = data.get(JIALIN_KEY) or []
    for e in jialin:
        if not (e.get("name") and e.get("_book") and e.get("_note")):
            bad.append(f"旁证课目缺 _book/_note 出处：{e.get('name', e)}")
        if e.get("name") in {x["name"] for x in entries}:
            bad.append(f"旁证课目与课经集 entries 重名：{e['name']}")
    jialin_names = {e.get("name") for e in jialin}
    implemented = _implemented()
    unknown = sorted(implemented - ({e["name"] for e in entries} | jialin_names))
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
