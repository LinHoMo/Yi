# -*- coding: utf-8 -*-
"""从《卜筮正宗》殆知阁转录本（data/sources/bushi_zhengzong_dz.dz.txt）抽取带
日期/卦面/验支的占验案例，建 `bushi_zhengzong_holdout`（永不调参的外部集）。

    python dev_tools/build_bushi_zhengzong_cases.py [--dry-run] [--selftest]

底本形态（表格式，与增删 dz 的 `′/″` 行不同）：
    占事  自己终身成败
    卦名  火山旅之山风蛊
    卦宫  ...
    六兽 世应 卦
    ...
    龙  应    巳 兄        丙 丙 戊
    武      未 孙        辰 辰 辰
    ...
    彼时祖业丰裕…果得长子．甲戌年生次子…

日期解码（408 批实测）：表头末三列是 日／月建／太岁，第一数据行放三柱天干、
第二数据行放三柱地支；同一本书里既有单栏也有双栏，尾随空列个数还不一致
（BZ035 尾 1 空、BZ038 尾 2 空），故不用固定切片，改由「row1 最后一个非空列」
向前试 e-2/e-1/e 三档，取第一个「row1 是干、row2 是支、月支可读」的档位。
例：`丙 丙 戊` / `辰 辰 辰` → 日丙辰、月辰、年戊辰，与原文「戊辰年辰月丙辰日」一致。

门（任一门不过即 excluded，写明原因）：
  1. 表块能切出左右栏，且 `占事`/`卦名` 对齐（表头模板/缺表直接排除）；
  2. 日柱天干+地支齐全、月支可读，且日期三列按上述结构锚位唯一可解；
  3. 卦名可解析（转录讹字按 NAME_ALIAS 登记表归一）、hex2yao 可装卦；
  4. 表内动标 ≡ 本卦⊕变卦差集（动标字形有 Ｏ/Ｘ/ｘ/O/０ 五种，row1=上爻）；
  5. 验语有结果标记＋应期令牌（400 批 YING_PAT 口径）；无直接结果句时按 409 批
     通用确认句回溯（果验/果应/果符/果如 → 最近前置日期令牌，须非占测日/月、
     非连写日「巳午日」、距确认句 ≤30 字）；单点门：同单位不得出现
     两个以上已应日期（终身卦/多事件一律剔除），月序范围（「三四月」）不可判；
  6. 锚句归属：验语里又起他卦（「又一人…得…卦」）时锚句只认前半段；
  7. 验语自述「X是月建」与表月冲突 → 底本自相矛盾，剔除；
  8. 不与全库在册案例同案（同日期+卦变，或同卦变+应期支）。
本集只抽书载应期与断语原文；用神/吉凶字面未抽（评测时 N/A 不进分母，见 CHANGELOG）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# 控制台编码守卫（AGENTS.md §四.9）：cp936 控制台下中文输出会退化成乱码，rc 仍为 0。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(DISC / "core"))
sys.path.insert(0, str(HERE))
from stable_write import write_stable  # noqa: E402
from case_runner import hex2yao  # noqa: E402
from graduate_verifications import (  # noqa: E402
    YING_PAT, MONTH_ORDER_BRANCH, _ying_branch, _ying_unit,
)
from build_zengshan_dz_cases import (  # noqa: E402
    BRANCHES, STEMS, STEMS_SRC, resolve_hex_name, strip_tail_gua,
)

SRC = DISC / "data" / "sources" / "bushi_zhengzong_dz.dz.txt"
OUT = DISC / "data" / "cases" / "bushi_zhengzong_cases.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"
LIUSHU = "龙武虎蛇陈雀"
DATE_RE = re.compile(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS_SRC, BRANCHES))
# 验语自述月建：「亥水虽是月建」（现时断言）。未来月建写法（「明示辰月建可见」＝次年辰月）
# 不算——连接词「是/为/即/乃」必须显式出现。BZ0421 表巳月而称亥为月建且「不谓月破」
# 只在亥月成立 → 底本自相矛盾，不猜，剔除。
SELF_MONTH_RE = re.compile(
    r"([%s])[水木火土金]?(?:虽)?(?:是|为|即|乃)月建" % BRANCHES)
# 408 批实测：本书动标有五种字形——Ｏ(U+FF2F 89)、Ｘ(U+FF38 71)、ｘ(U+FF58 20)、
# O(U+004F 14)、０(U+FF10 1)。只认 ASCII O/ｘ 会漏掉 89+71+14 个动爻（同一本书内
# 两种转录习惯混排），BZ045/BZ046 即因此被判「表无动标」。
YANG_MARK = set("OoＯｏ0０")
YIN_MARK = set("XxＸｘ")
# 409 批：通用确认句回溯取期。底本大量验语写作「甲子日必回．后果验」「许巳年脱厄．果验」，
# 结果标记（果验/果应/果符/果如）后不带日期——400 批 YING_PAT 只认「标记后 12 字内日期」，
# 这批会整批落空。回溯规则：取确认句**最近的前置**日期令牌，且
#   ① 不是占测日/占测月自身（同单位才比；dz 建器门 6「占测日自重不计」同口径）；
#   ② 不是连写日（「巳午日」「丑未日」是两日/范围，单点不可判）；
#   ③ 距确认句 ≤30 字（再远就无法证明是同一断言；BZ0791 的 49 字即按此拒）。
# 只用显式确认词，不拿「果于/果至」当兜底——那是 YING_PAT 自己的句式。
GENERIC_VERIFY_RE = re.compile(r"果验|果應|果应|后果验|竟验|果符|果如")
GENERIC_MAX_BACK = 30
# 转录讹字登记（408 批逐条实测）：底本用「干」代「乾」、个别卦名有讹字/衍字。
# 每条都由门 4（表动标 ≡ 本卦⊕变卦差集）反证——别名错则装卦差集必不符而剔除。
NAME_ALIAS = {
    "干为天": "乾为天",      # 全书「干」＝「乾」（卦宫同写「干金」）
    "兑为金": "兑为泽",      # 八纯卦名当作「兑为泽」，金为宫行
    "风泽中乎孚": "风泽中孚",  # 衍「乎」
    "艮天大畜": "山天大畜",    # 首字讹「艮」
    "天火同火": "天火同人",    # 末字讹「火」
}
# 验语内另起他卦的形态：「又一人申月甲午日父为子择媳，得复之噬嗑卦」（BZ034 实测——
# 该表本卦的断语后紧跟下一案的题面，YING 会把下一案的「后至巳年」记到本案头上）。
OTHER_CASE_RE = re.compile(
    r"又[一有]?[人友]?[^\n。；]{0,12}?[%s]月[%s][%s]日[^\n。；]{0,12}?得[^\n。；]{2,8}卦" % (
        BRANCHES, STEMS_SRC, BRANCHES))


def _multi_point(text: str, date: dict) -> bool:
    """同一单位（日/月/年）出现 ≥2 个不同支＝多事件验语，单点应期无从取。

    扣除占测日支（「辰日克之」）与占测月支（「午月克之」）——它们不是应期。
    月序（六月/七月/三月）按标准月建映射后同样计入（BZ0392「六月病…八月失财」实测：
    只数「X月」支令牌会漏掉月序形态）。
    """
    groups = {"日": set(), "月": set(), "年": set()}
    for br, unit in re.findall(r"([%s])(日|月|年)" % BRANCHES, text):
        if unit == "日" and br == date["day"][-1:]:
            continue
        if unit == "月" and br == date["month"]:
            continue
        groups[unit].add(br)
    for ch in re.findall(r"([正一二三四五六七八九十冬腊])月", text):
        groups["月"].add(MONTH_ORDER_BRANCH[ch])
    return any(len(v) >= 2 for v in groups.values())


def _month_range_ambiguous(m, text: str) -> bool:
    """月序命中若紧跟在另一个月序字前（「后三四月」＝三月或四月），单点不可判。

    BZ097 实测：真验语是「五月方归」，YING 却从「后三四月乃父在湖广生理」截出
    「四月」→巳月，与书载应验（午月）不符。范围写法一律不收。
    """
    if not m or not m.group(5):
        return False
    i = m.start(5)
    return i > 0 and text[i - 1] in MONTH_ORDER_BRANCH


def _generic_yingqi(text: str, date: dict):
    """通用确认句（果验/果应/果符/果如）→ 最近前置日期令牌（409 批回溯规则）。

    返回 (branch, unit, marker_match, reason)；失败时 branch=None，reason 写明哪一种拒绝。
    只认**最近**的前置令牌：若最近那个本身是连写日/占测日/占测月，直接拒——不跳过它
    去更早的令牌（那等于在多个候选里挑一个对得上的）。
    """
    gm = GENERIC_VERIFY_RE.search(text)
    if not gm:
        return None, None, None, "无通用确认句"
    toks = [m for m in re.finditer(r"([%s])(日|月|年)" % BRANCHES, text) if m.start() < gm.start()]
    if not toks:
        return None, None, gm, "确认句前无日期令牌"
    m = toks[-1]
    br, unit = m.group(1), m.group(2)
    prev = text[m.start() - 1] if m.start() > 0 else ""
    if prev in BRANCHES:
        return None, None, gm, "最近令牌是连写日「%s」" % text[m.start() - 1:m.end()]
    if unit == "日" and br == date["day"][-1]:
        return None, None, gm, "最近令牌是占测日「%s」" % m.group(0)
    if unit == "月" and br == date["month"]:
        return None, None, gm, "最近令牌是占测月「%s」" % m.group(0)
    if gm.start() - m.start() > GENERIC_MAX_BACK:
        return None, None, gm, "最近令牌距确认句 %d 字（下限 %d）" % (
            gm.start() - m.start(), GENERIC_MAX_BACK)
    return br, unit, gm, ""


def _tokens(line: str) -> list[str]:
    return line.split("\t")


def _half_tokens(toks: list[str]) -> list[list[str]]:
    """按第二个六兽切成左右半；单栏返回 [toks]。"""
    idx = [i for i, t in enumerate(toks) if t.strip() and t.strip()[0] in LIUSHU]
    if len(idx) >= 2:
        k = idx[1]
        return [toks[:k], toks[k:]]
    return [toks]


def _date_from_rows(row1: list[str], row2: list[str], mode: str = "") -> dict | None:
    """日期三列定位（408 批实测，取代固定 [-3:] / [-4:-1] 切片）。

    版面：表头「日／月建／太岁」三列，第一数据行是日干（及月/年干），第二行是日支
    （及月/年支）；同一本书里既有单栏也有双栏，尾随空列个数还不一致（BZ035 尾 1 空、
    BZ038 尾 2 空），固定切片会把日干读成「申」这类非干字。
    改用结构锚：取 row1 **最后一个非空列** e，日期三列必以 e 或 e-1 或 e-2 起头
    （年列常空，故 e 可能落在月列或日列）；按 e-2→e-1→e 顺序取**第一个**同时满足
    「row1[start] 是干、row2[start] 是支、月支可读」的档位。年列完整时 e-2 即日干，
    年列空时 e-1 才是日干（BZ033 与 BZ035 两种版面实测）。
    """
    filled = [i for i, t in enumerate(row1) if t.strip()]
    if not filled:
        return None
    e = filled[-1]
    hits = []
    for start in (e - 2, e - 1, e):
        if start < 0 or start >= len(row2):
            continue
        stem, branch = row1[start].strip(), row2[start].strip()
        # 空串是任意字符串的子串（'' in STEMS_SRC 为 True）——必须显式非空，
        # 否则空列会被当成日干支（本轮实测把日干读成空的 start_col=8）。
        if not stem or stem not in STEMS_SRC or not branch or branch not in BRANCHES:
            continue
        month = ""
        if start + 1 < len(row1) and row1[start + 1].strip() in BRANCHES:
            month = row1[start + 1].strip()
        elif start + 1 < len(row2) and row2[start + 1].strip() in BRANCHES:
            month = row2[start + 1].strip()
        if not month:
            continue
        year = ""
        if start + 2 < len(row1) and start + 2 < len(row2):
            ys, yb = row1[start + 2].strip(), row2[start + 2].strip()
            if ys and ys in STEMS_SRC and yb and yb in BRANCHES:
                year = ys + yb
        hits.append({"day": ("己" if stem == "已" else stem) + branch,
                     "month": month, "year": year,
                     "day_stem_normalized": stem == "已",
                     "start_col": start})
    return hits[0] if hits else None


def _split_names(line: str, prefix: str) -> list[str]:
    parts = [p for p in line.split("\t\t") if prefix in p]
    out = []
    for p in parts:
        p = p.strip()
        if p.startswith(prefix):
            p = p[len(prefix):].strip()
        out.append(p)
    if not out:
        p = line.strip()
        if p.startswith(prefix):
            p = p[len(prefix):].strip()
        out = [p]
    return out


def _moving_from_table(rows: list[list[str]]) -> list[tuple[int, int]]:
    """表行是**上爻→初爻**（row1=line6…row6=line1）；Ｏ=老阳(9)、Ｘ=老阴(6)。"""
    out = []
    for i, toks in enumerate(rows, 1):
        mark = toks[2].strip() if len(toks) > 2 else ""
        line = 7 - i
        if any(ch in YANG_MARK for ch in mark):
            out.append((line, 9))
        elif any(ch in YIN_MARK for ch in mark):
            out.append((line, 6))
    return sorted(out)


def _verdicts(post_lines: list[str], n: int) -> list[str]:
    """把表后断语按左右栏切开；单栏全给 case0。"""
    if n == 1:
        return ["\n".join(x.strip() for x in post_lines if x.strip())]
    left, right = [], []
    last_both = False
    for line in post_lines:
        if not line.strip():
            continue
        toks = _tokens(line)
        nonempty = [t.strip() for t in toks if t.strip()]
        if len(nonempty) >= 2:
            left.append(nonempty[0])
            right.append(nonempty[-1])
            last_both = True
            continue
        text = nonempty[0] if nonempty else ""
        if not text:
            continue
        if last_both:
            # 双栏后单行：给还没有结果标记的一侧；两侧都有则给右（右常续行）
            lh = bool(YING_PAT.search("。".join(left)))
            rh = bool(YING_PAT.search("。".join(right)))
            if lh and not rh:
                right.append(text)
            elif not lh and rh:
                left.append(text)
            else:
                right.append(text)
        else:
            # 首个单行通常是左栏断语
            left.append(text)
    return ["\n".join(left), "\n".join(right)]


def _case_from_block(lines: list[str], start: int, end: int, cid: str, sha: str) -> tuple[dict | None, dict]:
    block = lines[start:end]
    header = block[0]
    questions = _split_names(header, "占事")
    hex_line = next((x for x in block if x.startswith("卦名")), "")
    names = _split_names(hex_line, "卦名") if hex_line else []
    n = 2 if (len(questions) >= 2 and len(names) >= 2) else 1
    if n == 1:
        questions, names = questions[:1], names[:1]
    data_rows = [x for x in block
                 if x.split("\t")[0].strip() and x.split("\t")[0].strip()[0] in LIUSHU]
    if len(data_rows) < 6:
        return [], [{"id": cid, "reason": "数据行不足 6 行（表头模板或缺表）", "offset": start}]
    table = data_rows[:6]
    halves = [_half_tokens(_tokens(r)) for r in table]
    if n == 2 and any(len(h) < 2 for h in halves):
        return [], [{"id": cid, "reason": "双栏表块切不出左右半", "offset": start}]
    last_data_idx = max(i for i, x in enumerate(block) if x in table)
    # 表后断语只取**紧邻的连续段落**：本书占事块之间常隔着大段辨谬/问答正文
    # （BZ035 与下一占事相隔千余行，把整段当断语会把「子日」「十月」等无关令牌算进应期）。
    post = []
    for x in block[last_data_idx + 1:]:
        if not x.strip() or re.match(r"第[一二三四五六七八九十百]+问", x.strip()):
            break
        post.append(x)
    verdicts = _verdicts(post, n)
    cases = []
    for side in range(n):
        q = questions[side].strip() if side < len(questions) else ""
        hx = names[side].strip() if side < len(names) else ""
        raw_orig, raw_chg = _split_hex(hx)
        raw_orig = NAME_ALIAS.get(raw_orig, raw_orig)
        raw_chg = NAME_ALIAS.get(raw_chg, raw_chg) if raw_chg else ""
        orig, note = resolve_hex_name(raw_orig)
        chg, note2 = resolve_hex_name(raw_chg) if raw_chg else (None, "")
        if note and "不符" in note:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "卦名前缀与卦体不符：%r（%s）" % (hx, note)})
            continue
        if note2 and "不符" in note2:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "变卦名前缀与卦体不符：%r（%s）" % (hx, note2)})
            continue
        if not orig or (raw_chg and not chg):
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "卦名不可解析：%r" % hx})
            continue
        row1 = halves[0][side] if n == 2 else halves[0][0]
        row2 = halves[1][side] if n == 2 else halves[1][0]
        date = _date_from_rows(row1, row2)
        if not date:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "表末三列读不出日柱/月支：%r / %r" % (row1, row2)})
            continue
        yao = hex2yao(orig, chg)
        if yao is None:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "hex2yao 装卦失败：%s→%s" % (orig, chg)})
            continue
        moving_pairs = sorted((i, v) for i, v in enumerate(yao, 1) if v in (6, 9))
        moving = [i for i, _ in moving_pairs]
        table_moving = _moving_from_table([h[side] if n == 2 else h[0] for h in halves])
        if moving_pairs != table_moving:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "动标不符：表 %r ≠ 卦 %r" % (table_moving, moving)})
            continue
        text = verdicts[side] if side < len(verdicts) else ""
        # 换题线：断语后若接「第X问／答曰」等问答正文，锚句不可能属于本表（BZ0461 实测）
        mq = re.search(r"(?m)^第[一二三四五六七八九十百]+问", text)
        if mq:
            text = text[:mq.start()]
        # 非单点门（401 批 L1165 同口径）：终身卦是多点应验，抽单点＝在多结果里挑一个；
        # 验语里同一单位出现两个以上不同支也一样（BZ033 辛未/甲戌/丁丑/庚辰…；
        # BZ0452 巳年起用＋申年生子）。占测月/日自身不计。
        if "终身" in q:
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "终身叙述（多点应验，不可作单点应期）"})
            continue
        if _multi_point(text, date):
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "验语多事件（同单位 ≥2 个已应日期）"})
            continue
        sm = SELF_MONTH_RE.search(text)
        if sm:
            claimed = sm.group(1)
            if claimed and claimed != date["month"]:
                cases.append({"id": cid if n == 1 else cid + str(side + 1),
                              "reason": "验语自述月建%s与表月%s冲突" % (claimed, date["month"])})
                continue
        ym = YING_PAT.search(text)
        yb, yu = _ying_branch(ym), _ying_unit(ym)
        gm = None
        yingqi_src = "ying_pat"
        if not yb:
            yb, yu, gm, why = _generic_yingqi(text, date)
            if not yb:
                reason = "验语无结果标记＋应期令牌"
                if gm:
                    reason += "（通用确认句回溯：%s）" % why
                cases.append({"id": cid if n == 1 else cid + str(side + 1),
                              "reason": reason})
                continue
            yingqi_src = "generic_verify_backref"
        if ym and _month_range_ambiguous(ym, text):
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "月序范围（如三四月）不可作单点：%r" % ym.group(0)})
            continue
        # 锚句归属：验语若又起他卦（「又一人X月Y日…得…卦」），锚句只能在前半段
        anchor = ym or gm
        other = OTHER_CASE_RE.search(text)
        if other and anchor.start() > other.start():
            cases.append({"id": cid if n == 1 else cid + str(side + 1),
                          "reason": "锚句属于验语内另起的他卦（%s…）" % text[other.start():other.start() + 18]})
            continue
        topic = re.sub(r"^占", "", q).strip().strip("？?")
        cases.append({
            "id": cid if n == 1 else cid + str(side + 1),
            "source": "《卜筮正宗》（殆知阁转录本）",
            "topic": topic,
            "question": topic,
            "input": {"date": "%s月%s日" % (date["month"], date["day"]), "question": topic},
            "hexagram": {"original": orig, "changed": chg, "moving": moving},
            "expected": {
                # 408 批只从书载验语取应期；用神/吉凶字面未抽（不拿引擎输出回填，见 CHANGELOG）
                "verdict": None, "use_god": "", "use_god_branch": "",
                "use_god_position": "", "yingqi": yb + (yu or "日"),
                "yingqi_branches": [yb], "detail": text[:300],
                "same_as_day_branch": yb == date["day"][1:2],
            },
            "provenance": {
                "source_file": "data/sources/bushi_zhengzong_dz.dz.txt",
                "sha256": sha, "offset": start, "line_no": start + 1,
                "text_head": hex_line[:120],
                "table_date": [date["day"], date["month"], date["year"]],
                "date_source": "table_day_month_columns",
                "day_stem_normalized": date["day_stem_normalized"],
                "question_source": "占事行",
                "yingqi_source": yingqi_src,
                "generic_marker": gm.group(0) if gm else None,
            },
            "notes": "dev_tools/build_bushi_zhengzong_cases.py 抽取（408/409 批），过表栏/日期/"
                     "卦名/装卦/动标/验支/单点/锚句/同案 门；应期取书载实录（YING_PAT 或通用"
                     "确认句回溯）；用神与吉凶未抽（N/A 不进分母）；永不参与调参。",
        })
    good = [c for c in cases if "input" in c]
    bad = [c for c in cases if "input" not in c]
    return good, bad


def _split_hex(hx: str) -> tuple[str, str]:
    hx = hx.strip().strip("。；，, ．")
    for conn in ("之", "变"):
        if conn in hx:
            a, b = hx.split(conn, 1)
            return strip_tail_gua(a.strip()), strip_tail_gua(b.strip())
    return strip_tail_gua(hx), ""


def _existing_keys() -> tuple[set, set]:
    k1, k2 = set(), set()
    for p in (DISC / "data" / "cases").glob("*.json"):
        if p.name == OUT.name:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        for c in (d.get("cases") or []):
            hx = c.get("hexagram") or {}
            dtx = (c.get("input") or {}).get("date") or ""
            md = re.search(r"([%s])月([%s])([%s])日" % (BRANCHES, STEMS, BRANCHES), dtx)
            if not md:
                continue
            k1.add((md.group(1), md.group(2) + md.group(3), hx.get("original"), hx.get("changed"))) 
            for b in ((c.get("expected") or {}).get("yingqi_branches") or []):
                k2.add((hx.get("original"), hx.get("changed"), b))
    return k1, k2


def selftest() -> int:
    fails = []
    # 表日期解码：单栏（1159/1160）
    r1 = _tokens("龙\t\t\t巳\t兄\t\t\t\t\t丙\t丙\t戊")
    r2 = _tokens("武\t\t\t未\t孙\t\t\t\t\t辰\t辰\t辰")
    d = _date_from_rows(r1, r2)
    if not d or (d["day"], d["month"], d["year"]) != ("丙辰", "辰", "戊辰"):
        fails.append("单栏日期解码错：%r" % d)
    # 双栏左/右（2378/2379）
    row = _tokens("龙\t应\t\t子\t兄\t\t\t\t\t丙\t辰\t\t\t龙\t\t\t未\t父\t\t\t\t\t丁\t午\t辰")
    row2 = _tokens("武\t\t\t戌\t官\t\t\t\t\t申\t\t\t\t武\t\tO\t酉\t兄\t申\t兄\t\t\t未\t\t")
    halves = _half_tokens(row)
    if len(halves) != 2:
        fails.append("双栏切分失败")
    else:
        dl = _date_from_rows(halves[0], _half_tokens(row2)[0])
        dr = _date_from_rows(halves[1], _half_tokens(row2)[1])
        if not dl or dl["day"] != "丙申" or dl["month"] != "辰":
            fails.append("双栏左日期错：%r" % dl)
        if not dr or dr["day"] != "丁未" or dr["month"] != "午":
            fails.append("双栏右日期错：%r" % dr)
    # 尾随空列个数不同（BZ038 实测：单栏尾 2 空，日干在倒数第 4 列）
    r3 = _tokens("雀\t\t\t寅\t财\t\t\t伏\t\t戊\t申\t\t")
    r4 = _tokens("龙\t世\t\t子\t孙\t\t\t申兄\t\t子\t\t\t")
    d2 = _date_from_rows(r3, r4)
    if not d2 or d2["day"] != "戊子" or d2["month"] != "申":
        fails.append("尾空列日期解码错：%r" % d2)
    # 空串不得当干/支（'' in STEMS_SRC 恒真）
    r5 = _tokens("雀\t\t\t寅\t财\t\t\t\t\t\t申")
    if _date_from_rows(r5, r4) is not None:
        fails.append("空日干未被拒")
    # 卦名切分/别名
    a, b = _split_hex("火山旅之山风蛊")
    if (a, b) != ("火山旅", "山风蛊"):
        fails.append("卦名切分错：%r/%r" % (a, b))
    a2, b2 = _split_hex("水天需之干为天")
    if NAME_ALIAS.get(a2, a2) != "水天需" or resolve_hex_name(NAME_ALIAS.get(b2, b2))[0] != "乾":
        fails.append("干→乾别名错：%r/%r" % (a2, b2))
    # 动标五字形：Ｏ/Ｘ/ｘ/O/０（row1=上爻…）
    rows = [["雀", "世", "Ｏ"], ["龙", "", "Ｘ"], ["武", "", "ｘ"], ["虎", "", "O"], ["蛇", "", "０"]]
    mv = _moving_from_table(rows)
    if mv != [(2, 9), (3, 9), (4, 6), (5, 6), (6, 9)]:
        fails.append("动标字形解码错：%r" % mv)
    # 非单点：同单位 ≥2 支；占测日/月自身不计
    d3 = {"day": "丙申", "month": "辰", "year": ""}
    if not _multi_point("果至六月病，至八月店中财物被盗尽", {"day": "戊辰", "month": "寅", "year": ""}):
        fails.append("月序多事件漏判")
    if _multi_point("辰月克之，申日生之，果于本日酉时，亥日痊愈", d3):
        fails.append("单一事件误判为多事件")
    # 月序范围「三四月」不可作单点
    txt = "第四爻午火独静，五月必归也．后三四月乃父在湖广生理"
    m = YING_PAT.search(txt)
    if not _month_range_ambiguous(m, txt):
        fails.append("月序范围未判歧义")
    m2 = YING_PAT.search("果于次年二月拿问．应卯者")
    if _month_range_ambiguous(m2, "果于次年二月拿问．应卯者"):
        fails.append("单点月序误判歧义")
    # 自述月建与表月冲突（现时断言）；未来月建不算
    if not SELF_MONTH_RE.search("亥水虽是月建，不谓月破") or \
            SELF_MONTH_RE.search("明示辰月建可见"):
        fails.append("自述月建识别错")
    # 409 通用确认句回溯：正例 + 五类负例（连写日/占测日/占测月/超距/无令牌）
    d4 = {"day": "甲子", "month": "亥", "year": ""}
    if _generic_yingqi("世空者迟至，己巳日必回，后果验．", d4)[:2] != ("巳", "日"):
        fails.append("通用确认句正例未取到巳日")
    if _generic_yingqi("惟巳午日好卖…果验．", d4)[0] is not None:
        fails.append("连写日（巳午日）未拒")
    if _generic_yingqi("戌日冲之，本日即果验．", {"day": "戊戌", "month": "巳", "year": ""})[0] is not None:
        fails.append("占测日自重未拒")
    if _generic_yingqi("未月持财，月内必有．果验．", {"day": "庚子", "month": "未", "year": ""})[0] is not None:
        fails.append("占测月自重未拒")
    far = "断曰：" + "甲" * 20 + "申日．" + "乙" * 30 + "果验"
    if _generic_yingqi(far, d4)[0] is not None:
        fails.append("超距令牌未拒")
    if _generic_yingqi("其事即散．果验．", d4)[0] is not None:
        fails.append("无前置令牌未拒")
    if _generic_yingqi("果至其日而死．", d4)[2] is not None:
        fails.append("果至被误当通用确认词")
    if not YING_PAT.search("果于本日酉时，得名医救活，亥日痊愈"):
        fails.append("验支正例未命中")
    if YING_PAT.search("此卦亥水兄弟为用神，辰月克之，申日生之"):
        fails.append("验支负例（无结果标记）误命中")
    print("√ selftest：单/双栏/尾空列日期解码、空串拒绝、卦名别名、动标五字形、"
          "非单点/月序范围/自述月建、通用确认句回溯五负例、验支正负例 全过"
          if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="《卜筮正宗》dz 表格式占验案例抽取器")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    text = SRC.read_text(encoding="utf-8")
    lines = text.splitlines()
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
    k1, k2 = _existing_keys()
    cases, excluded = [], []
    starts = [i for i, l in enumerate(lines) if l.startswith("占事")]
    for bi, s in enumerate(starts):
        e = starts[bi + 1] if bi + 1 < len(starts) else len(lines)
        cid = "BZ%03d" % (bi + 1)
        keep, bad = _case_from_block(lines, s, e, cid, sha)
        excluded.extend(bad)
        for c in keep:
            hx = c["hexagram"]
            md = DATE_RE.search(c["input"]["date"])
            day = ("己" if md.group(2) == "已" else md.group(2)) + md.group(3)
            key1 = (md.group(1), day, hx["original"], hx["changed"])
            key2 = (hx["original"], hx["changed"], c["expected"]["yingqi_branches"][0])
            if key1 in k1 or key2 in k2:
                excluded.append({"id": c["id"], "reason": "与全库在册案例同案", "date": c["input"]["date"]})
                continue
            cases.append(c)
            k1.add(key1)
            k2.add(key2)
    print("可评分 %d 例｜剔除 %d 例｜%s" % (len(cases), len(excluded), SRC.name))
    for c in cases:
        print("  √ %s %s %s→%s 应%s ｜%s" % (
            c["id"], c["input"]["date"], c["hexagram"]["original"],
            c["hexagram"]["changed"] or "—", c["expected"]["yingqi"], c["question"][:40]))
    for r in excluded[:20]:
        print("  × %s %s" % (r.get("id"), r.get("reason")))
    if args.dry_run:
        print("（dry-run，不写盘）")
        return 0
    doc = {
        "schema": "yi-liuyao-cases/1",
        "_meta": {
            "description": "《卜筮正宗》dz 表格式段落抽取的应期外部集；八道门＋同案去重；"
                           "409 批增通用确认句回溯取期；永不参与调参",
            "source": "《卜筮正宗》（殆知阁转录本）",
            "source_file": "data/sources/bushi_zhengzong_dz.dz.txt",
            "source_sha256": sha,
            "built_by": "dev_tools/build_bushi_zhengzong_cases.py",
            "n": len(cases),
            "excluded": excluded,
        },
        "cases": cases,
    }
    write_stable(OUT, doc, indent=2)   # 与在册 *_cases.json 的 indent=2 一致
    sp = json.loads(SPLITS.read_text(encoding="utf-8"))
    sp["bushi_zhengzong_holdout"] = [c["id"] for c in cases]
    sp["note_bushi_zhengzong_holdout"] = (
        "第408批前本集为空：《卜筮正宗》在 classical_cases.json 的 30 例 ZS* 中占 20 例，"
        "而 ZS001-020 正是 tune 集，不能充当外部集。第408批改由 "
        "dev_tools/build_bushi_zhengzong_cases.py 从 dz 表格式段落（十八问答附占验等）"
        "另抽 %d 例（BZ*，书源 data/sources/bushi_zhengzong_dz.dz.txt），"
        "与 ZS/ZD/WS 在册案例同案去重后零重叠，故可作永不调参的外部集。"
        "应期取书载实录：400 批 YING_PAT，或 409 批通用确认句回溯"
        "（果验/果应 → 最近前置日期令牌，须非占测日/月、非连写日、≤30 字），"
        "逐例 provenance.yingqi_source 留痕。detail 为断语原文（供格局维比对）；"
        "用神/吉凶字面未抽（N/A 不进分母）。" % len(cases))
    write_stable(SPLITS, sp, indent=2)  # 原文件 indent=2：默认 indent=1 会把全文重排（408 实踩）
    print("√ 落盘 %s｜%d 例；case_splits.bushi_zhengzong_holdout=%d"
          % (OUT.name, len(cases), len(cases)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
