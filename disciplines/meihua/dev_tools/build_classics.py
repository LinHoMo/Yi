# -*- coding: utf-8 -*-
"""梅花易数·古籍原文构建器（《梅花易数》逐字引文，产物入库、脚本留档可复跑）。

    python dev_tools/build_classics.py [--write]

为什么有这份数据：
  `data/verdicts.json` 里每条判据都标了卷篇出处（`basis_quotes` 等），但那些是
  **要点转述**；报告读者无法回指原书。本构建器把引擎实际执行的那几条规则、
  以及卷二《体用总诀》逐卦的「生体/克体」条，**逐字**摘出，落成
  `data/classics.json`，由 narrate 在报告末段附出（`references/classics.md` 是索引，
  不复抄原文，避免双份真值源）。

口径（不得含糊）：
  · 引文**逐字**取自书源（繁体照录，字符级保存，不做"模型转写"）；构建器逐条断言
    "是该行整行原文"（铁律三可回指）；
  · 引文只作**所本原文**，不参与评分、不改判据；判据唯一真值源仍是 `data/verdicts.json`；
  · **只收规则篇，不收占验/占例篇**（观梅占、牡丹占、邻夜扣门、西林寺、观物用易例、
    万物戏验…）——案例库与预测过程物理隔离（AGENTS.md 铁律二）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
SRC_DIR = DISC / "data" / "sources"
OUT = DISC / "data" / "classics.json"

# 内核（八卦名单唯一真值源）——构建期结构断言要用
sys.path.insert(0, str(DISC.parents[1] / "core"))
from yishu_core import corpus_kit  # noqa: E402  语料可复现性比对
sys.path.insert(0, str(DISC / "scripts"))

VOLS = {
    "卷一": SRC_DIR / "meihua_yishu_卷一.wikitext.txt",
    "卷二": SRC_DIR / "meihua_yishu_卷二.wikitext.txt",
    "卷三": SRC_DIR / "meihua_yishu_卷三.wikitext.txt",
}

# 键 → (卷, 篇名, [该篇内待摘行的前缀, …])；前缀必须在该篇内唯一命中，摘出整行原文。
RULES: dict[str, tuple[str, str, list[str]]] = {
    "起例_卦以八除": ("卷一", "卦以八除", ["凡起卦不問數多少"]),
    "起例_爻以六除": ("卷一", "爻以六除", ["凡起動爻"]),
    "起例_互卦": ("卷一", "互卦起例", ["互卦只用八卦", "又云：乾坤無互"]),
    "起例_年月日时": ("卷一", "年月日時起例", ["年月日為上卦"]),
    "起例_物数": ("卷一", "物數占例", ["凡見有可數之物"]),
    "八卦象例": ("卷一", "八卦象例", ["乾三連，坤六斷"]),
    "卦气旺": ("卷一", "卦氣旺", ["震、巽木旺於春"]),
    "卦气衰": ("卷一", "卦氣衰", ["春坤、艮"]),
    "占卜总决": ("卷二", "占卜總決", ["大抵占卜之法", "次看卦之體用", "複驗己身之動靜"]),
    "先天后天论": ("卷二", "先天後天論", ["先天卦斷吉凶"]),
    # 注：卷二《卦斷遺論》原文本身即以「西林寺額 / 今日動靜如何 / 牛哀鳴占」等占验例说理，
    #     逐字引入会把案例名带进语料与报告（违反 AGENTS.md 铁律二：案例库与预测过程物理隔离），
    #     故**故意不收**；该判据只保留规则名与要义转述（data/verdicts.json#hexagram_special）。
    "体用总诀": ("卷二", "體用總訣", ["體用之間，比和則吉"]),
    "体用总诀_体用者": ("卷二", "體用總訣", ["體用雲者"]),
    "体用总诀_受生受克": ("卷二", "體用總訣", ["宜受他卦之生"]),
    "体用互变之诀": ("卷三", "體用互變之訣", ["大凡占卜，以體為其主", "大凡占卦，變卦克體"]),
    "占卦诀": ("卷三", "占卦訣", ["又如占卦問吉事", "又如占不吉之事"]),
    "体用生克之诀": ("卷三", "體用生克之訣", ["占卦即以卦分體用互變"]),
    "体用衰旺之诀": ("卷三", "體用衰旺之訣", ["凡體卦宜乘旺"]),
    "体用动静之诀": ("卷三", "體用動靜之訣", ["占卦體用互變既分", "又若我坐，則事應之遲"]),
    "占卜克应之诀": ("卷三", "占卜克應之訣", ["克應者，所謂克期應驗也"]),
    "变卦式八则": ("卷三", "變卦式八則", ["體用於變爻，作動靜取之"]),
    "八卦定阴阳次序": ("卷三", "八卦定陰陽次序", ["乾為父，震長男"]),
    "诸卦反对性情": ("卷三", "諸卦反對性情", [
        "乾剛坤柔反其義", "大畜其卦福之生", "同人內親睽外疏", "革去舊故鼎從新",
        "要將字字考精詳"]),
}

# 卷二《体用总诀》逐卦「生体」「克体」条（引擎 sheng_ti/ke_ti 所本之原文）
PER_GUA = {
    "生体": ("卷二", "體用總訣", {
        "乾": "乾卦生體", "坤": "坤卦生體", "震": "震卦生體", "巽": "巽卦生體",
        "坎": "坎卦生體", "離": "離卦生體", "艮": "艮卦生體", "兌": "兌卦生體"}),
    "克体": ("卷二", "體用總訣", {
        "乾": "又看卦中有克體之卦者", "坤": "坤卦克體", "震": "震卦克體",
        "巽": "巽卦克體", "坎": "坎卦克體", "離": "離卦克體", "艮": "艮卦克體",
        "兌": "兌卦克體"}),
}

# 案例篇（占验/占例）：**不得**进 classics.json（铁律二：案例库与预测过程物理隔离）
CASE_SECTIONS = (
    "觀梅占", "牡丹占", "鄰夜扣門借物占", "今日動靜如何", "西林寺牌額占",
    "老人有憂色占", "少年有喜色占", "牛哀鳴占", "雞悲鳴占", "枯枝墜地占",
    "風覺鳥占", "風覺占", "鳥占", "聽聲音占", "形物占", "驗色占",
    "觀物用易例", "萬物戲驗",
)

# 卷一「象數易理篇之三·八卦萬物屬類」：逐卦分「天時／地理／人物／…／五味」诸类，
# 是梅花断事按事类取象的正表（引擎此前只消费「（並為上卦）」那一段简表）。
# 本书源小节用 `'''乾卦'''` 之类行分块，块内「键：值。」行为类象条目。
WANWU_SECTION = ("卷一", "八卦萬物屬類")
WANWU_MIN_CLASSES = 20          # 每卦至少这么多类（实测远多于此；低于即判书源结构变了）
WANWU_REQUIRED = ("天時", "地理", "人物")   # 每卦必须有的三类（缺即判书源结构变了）
# 书源（繁体）卦名 → 内核八卦名（`yishu_core.symbols.HEXAGRAM_TRIGRAMS` 的经卦名）。
# 归化只涉及两字（兌/離），且**只用于字典键**——`原文` 一律照录书源原样，不改一字。
WANWU_GUA_ALIAS = {"兌": "兑", "離": "离"}


def _blocks(lines: list[str]) -> dict[str, tuple[int, int]]:
    heads = [(i, l.strip()) for i, l in enumerate(lines) if l.strip().startswith("===")]
    heads = [(i, t) for i, t in heads if not t.startswith("====")]
    out: dict[str, tuple[int, int]] = {}
    for k, (i, raw) in enumerate(heads):
        title = raw.strip("=").strip()
        end = heads[k + 1][0] if k + 1 < len(heads) else len(lines)
        if title in out:                      # 同名篇（如两卷都有「八卦方位圖」）在本卷内必须唯一
            raise SystemExit(f"篇名重复：{title}")
        out[title] = (i, end)
    return out


def _pick(lines: list[str], blocks: dict, title: str, prefix: str) -> tuple[str, int]:
    if title not in blocks:
        raise SystemExit(f"篇名不存在：{title}")
    lo, hi = blocks[title]
    hits = [(j, lines[j].strip()) for j in range(lo + 1, hi)
            if lines[j].strip().startswith(prefix)]
    if len(hits) != 1:
        raise SystemExit(f"前缀在篇内命中 {len(hits)} 行（要求唯一）：{title} / {prefix}")
    return hits[0][1], hits[0][0] + 1


def _wanwu_table(lines_by_vol: dict, blocks_by_vol: dict,
                 problems: list[str]) -> dict:
    """卷一「八卦萬物屬類」逐卦类象表：{卦: {类: {原文, 行号, 出处}}}。

    只手摘「键：值。」整行（逐字），卦块由 `'''X卦'''` 行切分；结构性断言写进 problems：
    八经卦齐、每卦类数 ≥ WANWU_MIN_CLASSES、必含 WANWU_REQUIRED 三类——书源一变形即判败。
    """
    import re

    vol, title = WANWU_SECTION
    lines = lines_by_vol[vol]
    if title not in blocks_by_vol[vol]:
        problems.append(f"篇名不存在：{vol}·{title}")
        return {}
    lo, hi = blocks_by_vol[vol][title]
    table: dict[str, dict] = {}
    cur: str | None = None
    raw_names: dict[str, str] = {}
    for j in range(lo + 1, hi):
        raw = lines[j].strip()
        head = re.fullmatch(r"'''(.+?)卦'''", raw)
        if head:
            src_name = head.group(1)
            cur = WANWU_GUA_ALIAS.get(src_name, src_name)
            raw_names[cur] = src_name
            table.setdefault(cur, {})
            continue
        if cur is None:
            continue
        item = re.match(r"^([^：\s]+)：(.+)$", raw)
        if not item:
            continue
        key, text = item.group(1), raw
        if key in table[cur]:                     # 同卦同类重复：书源结构变了
            problems.append(f"{vol}·{title}·{cur}：类「{key}」重复出现")
            continue
        table[cur][key] = {
            "原文": text, "行号": j + 1,
            "出处": f"《梅花易数》{vol}·{title}（源文件第 {j + 1} 行）",
        }
    table = {g: v for g, v in table.items() if v}

    from yishu_core.symbols import HEXAGRAM_TRIGRAMS as _TRI
    eight = {n for n, t in _TRI.items() if t[0] == t[1]}
    if set(table) != eight:
        problems.append(f"{vol}·{title} 卦集不齐：{sorted(table)} ≠ 八经卦 {sorted(eight)}")
    for gua, items in table.items():
        if raw_names.get(gua) and raw_names[gua] != gua:
            items["_书源卦名"] = raw_names[gua]
        if len(items) < WANWU_MIN_CLASSES:
            problems.append(f"{gua} 类数 {len(items)} < {WANWU_MIN_CLASSES}（书源结构变了？）")
        for need in WANWU_REQUIRED:
            if need not in items:
                problems.append(f"{gua} 缺必备类「{need}」")
    return table


def build() -> tuple[dict, list[str]]:
    lines_by_vol = {v: p.read_text(encoding="utf-8").splitlines() for v, p in VOLS.items()}
    blocks_by_vol = {v: _blocks(ls) for v, ls in lines_by_vol.items()}
    problems: list[str] = []
    long_lines: list[str] = []

    def one(vol: str, title: str, prefix: str) -> dict:
        text, ln = _pick(lines_by_vol[vol], blocks_by_vol[vol], title, prefix)
        # 逐字回指（真断言）：记录的行号必须**就是**该行原样——原实现写的是
        # `text in "".join(lines)`，那对「从该行摘出的文本」恒真（等于没断言），
        # 行号漂移也不会被发现；改为按行号回读比对。
        if text != lines_by_vol[vol][ln - 1].strip():
            problems.append(f"引文与记录行号不符：{vol}·{title} 第 {ln} 行 / {text[:24]}")
        if len(text) > 420:
            long_lines.append(f"{vol}·{title}（{len(text)} 字）")
        return {"卷": vol, "篇": title, "原文": text,
                "出处": f"《梅花易数》{vol}·{title}（源文件第 {ln} 行）"}

    rules: dict[str, dict] = {}
    for key, (vol, title, prefixes) in RULES.items():
        parts = [one(vol, title, p) for p in prefixes]
        rules[key] = {
            "卷": vol, "篇": title,
            "原文": [p["原文"] for p in parts],
            "出处": parts[0]["出处"],
        }

    per_gua: dict[str, dict] = {}
    for kind, (vol, title, gua_prefix) in PER_GUA.items():
        items = {}
        for gua, prefix in gua_prefix.items():
            items[gua] = one(vol, title, prefix)
        per_gua[kind] = items

    # 逐卦类象正表（卷一·象數易理篇之三·八卦萬物屬類）：按事类取象的书源依据
    wanwu = _wanwu_table(lines_by_vol, blocks_by_vol, problems)

    # 案例篇不得入库（铁律二）：逐条断言未出现在任何入库字符串里
    body = json.dumps({"rules": rules, "per_gua": per_gua, "wanwu": wanwu},
                      ensure_ascii=False)
    for sec in CASE_SECTIONS:
        if sec in body:
            problems.append(f"案例篇混入（违反铁律二）：{sec}")

    doc = {
        "schema": "meihua-classics-v1",
        "_comment": [
            "梅花易数古籍原文（《梅花易数》卷一/卷二/卷三逐字引文，繁体照录，带篇名与源文件行号）。",
            "口径：引文只作**所本原文**（narrate 末段附出），不参与评分、不改判据；判据唯一真值源是 data/verdicts.json。",
            "只收**规则篇**，不收占验/占例篇（观梅占、牡丹占、观物用易例…）——案例库与预测过程物理隔离（AGENTS.md 铁律二）。",
            "wanwu = 卷一「八卦萬物屬類」逐卦类象正表（天時/地理/人物/家宅/婚姻/求名/求利/官訟…诸类），"
            "供断事按事类取象；每类记原文、行号与出处，门 [1c] 按行号逐字回读核对。",
            "构建器 dev_tools/build_classics.py 逐条断言引文为该篇整行原文；references/classics.md 是索引，不复抄原文。",
        ],
        "source": {
            "book": "《梅花易数》",
            "volumes": {v: f"data/sources/{p.name}" for v, p in VOLS.items()},
            "site": "维基文库 zh.wikisource.org（字符级保存，无模型转写）",
        },
        "rules": rules,
        "per_gua": per_gua,
        "wanwu": wanwu,
    }
    if long_lines:
        print("超长原文（>420 字，照录不截断）：" + "；".join(long_lines))
    return doc, problems


def main() -> int:
    ap = argparse.ArgumentParser(description="梅花易数古籍原文构建（默认 dry-run）")
    ap.add_argument("--write", action="store_true", help="落盘 data/classics.json")
    ap.add_argument("--check", action="store_true",
                    help="不落盘，只比对已入库 data/classics.json 是否与重算一致")
    args = ap.parse_args()

    doc, problems = build()
    n = sum(len(v["原文"]) for v in doc["rules"].values())
    n += sum(len(v) for v in doc["per_gua"].values())
    wanwu = doc.get("wanwu") or {}
    print(f"规则 {len(doc['rules'])} 条 / 原文段 {n} 段"
          f"（逐卦生体 {len(doc['per_gua']['生体'])} + 克体 {len(doc['per_gua']['克体'])}）")
    print(f"逐卦类象 {len(wanwu)} 卦 / 类目 {sum(len(v) for v in wanwu.values())} 条"
          f"（每卦 ≥ {WANWU_MIN_CLASSES} 类，必含 {'/'.join(WANWU_REQUIRED)}）")
    print(f"卷次覆盖：" + "、".join(f"{v}×{sum(1 for r in doc['rules'].values() if r['卷'] == v)}"
                                    for v in VOLS))
    print(f"案例篇隔离：断言 {len(CASE_SECTIONS)} 个案例篇名未入库")
    print(f"问题 {len(problems)} 项：{problems or '无'}")
    if problems:
        print("有断言未过，拒绝写盘。")
        return 1
    if args.check:
        return corpus_kit.report(OUT.name, corpus_kit.check(OUT, doc))
    if not args.write:
        print("dry-run（未写盘）；加 --write 落盘。")
        return 0
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已写出 → {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
