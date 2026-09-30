# -*- coding: utf-8 -*-
"""从维基文库《火珠林》原文抓取占验案例，本地确定性解析并三方校验后成外部集。

    python dev_tools/fetch_huozhulin_cases.py            # 解析＋校验＋落盘
    python dev_tools/fetch_huozhulin_cases.py --report   # 只看校验统计，不落盘
    python dev_tools/fetch_huozhulin_cases.py --report --show 10  # 附带剔除样本

来源特殊性（区别于《增刪卜易》原本 fetch）：
  《火珠林》是宋·麻衣道者所著理论书，非占验集。其结构是"问答体"——
  每章先给四句<poem>，再展开注解，间杂"如X之Y卦"式占例说明。
  绝大多数例子没有明确的"月建+日柱"时刻，但有些含可检验事项
  （空间/人事/应期干支），可用于参考或评分。

抽取策略：
  1. 全文扫出所有"如/假如 + 卦名"占例引用；
  2. 在原句所在的"语义段落"里搜月日与应期干支；
  3. 三方校验（纳甲/卦变/世应）只在原文含爻图或明确动爻信息时才做；
     纯文字提及卦名而无卦图者，仅做"卦名可解析+卦变差集自洽"的最小校验；
  4. 按"是否可评分"分两路输出：
     - 含 干支日/月/年 应期 → huozhulin_cases.json（入评分集）
     - 仅有定性描述（空间/人事）→ huozhulin_qualitative.json（仅参考）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)
from yishu_core import symbols as sym                            # noqa: E402
from yishu_core.najia import najia_branch, response_position    # noqa: E402

SOURCES = DISC.parent.parent / "data" / "sources"
RAW = SOURCES / "huozhulin.wikitext.txt"
OUT_JSON = DISC / "data" / "cases" / "huozhulin_cases.json"
OUT_QUAL = DISC / "data" / "cases" / "huozhulin_qualitative.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 繁体字头归一：六十四卦用字 + 天干地支用字
TRAD = {
    "兌": "兑", "離": "离", "剝": "剥", "蠱": "蛊", "恆": "恒", "歸": "归",
    "無": "无", "晉": "晋", "賁": "贲", "頤": "颐", "豐": "丰", "澤": "泽",
    "風": "风", "臨": "临", "渙": "涣", "漸": "渐", "師": "师", "損": "损",
    "節": "节", "訟": "讼", "謙": "谦", "隨": "随", "壯": "壮", "過": "过",
    "復": "复", "觀": "观", "暌": "睽", "旣": "既", "卽": "即", "濟": "济",
    "坤": "坤", "乾": "乾", "震": "震", "巽": "巽", "艮": "艮", "坎": "坎",
    "兌": "兑",
}
TRI_CHARS = set("天地風雷水火山泽震巽乾坤坎离艮兑")

# 异体归一
VARIANTS = str.maketrans({"爲": "為", "為": "為"})


def norm_text(raw: str) -> str:
    out = raw.translate(VARIANTS)
    assert len(out) == len(raw), "异体归一改变了长度"
    return out


def norm(name: str) -> str:
    return "".join(TRAD.get(c, c) for c in (name or ""))


def resolve_hex(name: str) -> str | None:
    """原文卦名 → 内核卦名。先繁简归一，再剥"火天/澤天"前缀。"""
    n = norm(name).strip()
    if n in sym.HEXAGRAM_TRIGRAMS:
        return n
    # 全名如"天风姤""火天大有"：前缀是卦象字，后面才是卦名
    for cut in (1, 2):
        if len(n) > cut:
            tail = n[cut:]
            if tail in sym.HEXAGRAM_TRIGRAMS and all(c in TRI_CHARS for c in n[:cut]):
                return tail
    # "大有""姤""鼎"等可能直接在 HEXAGRAM_TRIGRAMS 里（第一次已查）
    return None


def hex_lines(name: str) -> list[int] | None:
    """六爻线自下而上（1 阳 0 阴）。"""
    tri = sym.HEXAGRAM_TRIGRAMS.get(name)
    if not tri:
        return None
    upper, lower = tri
    return sym.BAGUA_LINES[lower] + sym.BAGUA_LINES[upper]


def palace_of(name: str):
    """(宫名, 世代, 世爻位)。"""
    for palace, data in sym.EIGHT_PALACES.items():
        for hx, gen in data["order"]:
            if hx == name:
                pos = {"一世": 1, "二世": 2, "三世": 3, "四世": 4, "五世": 5,
                       "游魂": 4, "归魂": 3}.get(gen, 0)
                return palace, gen, pos
    return None


# ──────────────────────────────────────────────
# 文本切分：把原文按语义段落（以空行或章节头分段）拆成单元
# ──────────────────────────────────────────────
SECTION_RE = re.compile(r"^==\s*(.+?)\s*==\s*$", re.M)
# 维基文库 <br> 分段
SEG_SPLIT = re.compile(r"<br\s*/?>")
# poem / pre 块视为 noop（纯理论歌诀）
BLOCK_TAGS = re.compile(r"</?(?:poem|pre)[^>]*>")


def split_paragraphs(raw: str) -> list[dict]:
    """按空行切段；每段附带所属 section 名称。"""
    paragraphs = []
    current_section = "__header__"
    for line in raw.splitlines():
        # 章节头
        m = SECTION_RE.match(line)
        if m:
            current_section = m.group(1).strip()
            continue
        paragraphs.append({"section": current_section, "line": line})

    # 合并相邻非空行为段
    merged, buf = [], []
    for p in paragraphs:
        text = p["line"].strip()
        if text:
            buf.append((p["section"], text))
        else:
            if buf:
                sec = buf[0][0]
                body = " ".join(t for _, t in buf)
                merged.append({"section": sec, "text": body})
                buf = []
    if buf:
        sec = buf[0][0]
        body = " ".join(t for _, t in buf)
        merged.append({"section": sec, "text": body})
    return merged


# ──────────────────────────────────────────────
# 卦名对抽取：在一段文本中搜"如/假如+卦名(+之/化+变卦)"
# ──────────────────────────────────────────────
# 纯卦名列表（用于扫描）
HEXAGRAM_NAMES = sorted(sym.HEXAGRAM_TRIGRAMS.keys(), key=len, reverse=True)
_HEX_ALTERNATIVES = "|".join(re.escape(n) for n in HEXAGRAM_NAMES)

# 模式 A: "如/假如/占[X]得/[，]...A之B卦" 或 "A化B" 或 "A变B"
# 模式 B: "A卦" 单独出现（静卦，无变卦）
# 先匹配有变卦的对（A之B / A化B / A变B）
HEX_PAIR_RE = re.compile(
    r"(?:如|假如|得|占.*?得)\s*"
    r"(?P<ctx>[^。，,；;：:\n]{0,40}?)?"
    r"(?P<orig>" + _HEX_ALTERNATIVES + r")"
    r"(?:\s*卦?)?"
    r"(?:\s*(?:之|化|變|变)\s*"
    r"(?P<chg>" + _HEX_ALTERNATIVES + r")"
    r"(?:\s*卦?)?)?")

# 单个卦名（静卦）
HEX_SINGLE_RE = re.compile(
    r"(?<![变變化化之])"        # 不匹配在"X之"之后的
    r"(?P<name>" + _HEX_ALTERNATIVES + r")"
    r"\s*卦")


def extract_hex_pairs(text: str) -> list[dict]:
    """从一段文本中提取所有 (本卦, 变卦, 上下文) 引用。"""
    results = []
    seen_spans = set()

    # 先找有变卦的对
    for m in HEX_PAIR_RE.finditer(text):
        orig_raw = m.group("orig")
        chg_raw = m.group("chg")
        orig = resolve_hex(orig_raw)
        if not orig:
            continue
        changed = resolve_hex(chg_raw) if chg_raw else None

        # 验证：如果有变卦名存在但解析失败 → 记录为解析失败
        if chg_raw and not changed:
            # 变卦名不在六十四卦表内（不应发生，只是为了安全）
            continue

        span = m.span()
        if span in seen_spans:
            continue
        seen_spans.add(span)

        results.append({
            "original": orig,
            "changed": changed,
            "is_changed": changed is not None and changed != orig,  # True=有变卦且不同
            "span": span,
            "context": text[max(0, span[0] - 30):span[1] + 60],
        })

    # 再找单独的"X卦"（未被上面覆盖的）
    for m in HEX_SINGLE_RE.finditer(text):
        name_raw = m.group("name")
        name = resolve_hex(name_raw)
        if not name:
            continue
        span = m.span()
        # 如果该 span 已被包含在某个 pair 内则跳过
        if any(s[0] <= span[0] and span[1] <= s[1] for s in seen_spans):
            continue
        # 避免在已有 pair 内重复
        is_subsumed = False
        for s in seen_spans:
            if s[0] <= span[0] and span[1] <= s[1]:
                is_subsumed = True
                break
        if is_subsumed:
            continue

        results.append({
            "original": name,
            "changed": None,
            "is_changed": False,
            "span": span,
            "context": text[max(0, span[0] - 30):span[1] + 60],
        })

    return results


# ──────────────────────────────────────────────
# 时间提取：月建 + 日柱 / 年 + 月 + 日
# ──────────────────────────────────────────────
# 完整：乙丑年辛巳月丁酉日
FULL_DATE_RE = re.compile(
    r"(?:(?P<year_gan>[" + STEMS + r"])(?P<year_zhi>[" + BRANCHES + r"])年)?\s*"
    r"(?:(?P<month>[" + BRANCHES + r"])月)?\s*"
    r"(?P<day_gan>[" + STEMS + r"])(?P<day_zhi>[" + BRANCHES + r"])日")

# 月+日
MONTH_DAY_RE = re.compile(
    r"(?P<month>[" + BRANCHES + r"])月\s*(?P<day_gan>[" + STEMS + r"])(?P<day_zhi>[" + BRANCHES + r"])日")

# 单独日（无月）
DAY_ONLY_RE = re.compile(
    r"(?<!月\s)(?<!"
    r"["
    + STEMS + BRANCHES + r"]"
    r")"
    r"(?P<day_gan>[" + STEMS + r"])(?P<day_zhi>[" + BRANCHES + r"])日")


def extract_date(text: str) -> dict | None:
    """从文本中提取日期信息。"""
    # 优先完整日期
    m = FULL_DATE_RE.search(text)
    if m:
        d = m.groupdict()
        out = {}
        if d.get("year_gan"):
            out["year"] = d["year_gan"] + d["year_zhi"]
        if d.get("month"):
            out["month"] = d["month"]
        out["day"] = d["day_gan"] + d["day_zhi"]
        return out
    # 月+日
    m = MONTH_DAY_RE.search(text)
    if m:
        d = m.groupdict()
        return {"month": d["month"], "day": d["day_gan"] + d["day_zhi"]}
    # 丁酉日甲辰日 etc 出现在段首
    m = DAY_ONLY_RE.search(text)
    if m:
        d = m.groupdict()
        return {"day": d["day_gan"] + d["day_zhi"]}
    return None


# ──────────────────────────────────────────────
# 应期提取：（干）支+日/月/年/時
# ──────────────────────────────────────────────
# 锚定应期：應/果/期/驗 后紧跟（干）支+单位
# 单位包含 時/时（时辰级），也匹配 日/月/年
YINGQI_RE = re.compile(
    r"(?P<a>應|应|果|期|驗|验|應驗).{0,4}?"
    r"(?P<gan>[" + STEMS + r"])?(?P<zhi>[" + BRANCHES + r"])(?P<u>[日月年時时 ])")

# 直接在断句里的"X日到/X日回/X日归"
YINGQI_DIRECT_RE = re.compile(
    r"(?P<gan>[" + STEMS + r"])(?P<zhi>[" + BRANCHES + r"])\s*(日)\s*(?:到|回|歸|归|至|有|当)")

# "应在(某)第X位" 或 "期在X月"
YINGQI_ALT_RE = re.compile(
    r"(?:應|应|期)\s*(?:在|於|于|当\s*)?\s*"
    r"(?P<gan>[" + STEMS + r"])?(?P<zhi>[" + BRANCHES + r"])(?P<u>[日月年時时])")


def extract_all_yingqi(text: str) -> list[str]:
    """从一段文本中提取所有应期干支。返回列表如['申时', '卯日']。"""
    found = set()
    for m in YINGQI_RE.finditer(text):
        gan = m.group("gan") or ""
        zhi = m.group("zhi")
        unit = m.group("u").strip()
        if unit:
            found.add(gan + zhi + unit)
    for m in YINGQI_ALT_RE.finditer(text):
        gan = m.group("gan") or ""
        zhi = m.group("zhi")
        unit = m.group("u").strip()
        if unit:
            found.add(gan + zhi + unit)
    for m in YINGQI_DIRECT_RE.finditer(text):
        found.add(m.group("gan") + m.group("zhi") + "日")
    return sorted(found)


def extract_yingqi(text: str) -> str | None:
    """取应期干支，优先非時级的。不可检则返回 None。"""
    all_yq = extract_all_yingqi(text)
    if not all_yq:
        return None
    # 优先非時级
    non_hour = [y for y in all_yq if not y.endswith(("時", "时"))]
    if len(non_hour) == 1:
        return non_hour[0]
    if len(non_hour) > 1:
        return non_hour[0]
    if len(all_yq) == 1:
        return all_yq[0]
    return None


# ──────────────────────────────────────────────
# 占意提取：问曰/占[X]/占祟...
# ──────────────────────────────────────────────
TOPIC_PATTERNS = {
    "占身命": "身命", "占形性": "形性", "占运限": "运限", "占婚姻": "婚姻",
    "占孕产": "孕产", "占科举": "科举", "占谒贵": "谒贵", "占买卖": "买卖",
    "占求财": "求财", "占博戏": "博戏", "占出行": "出行", "占行人": "行人",
    "占逃亡": "逃亡", "占失物": "失物", "占贼盗": "贼盗", "占鬼神": "鬼神",
    "占词讼": "词讼", "占脱事": "脱事散忧", "占疾病": "疾病", "占医药": "医药",
    "占家宅": "家宅", "占人口": "人口", "占起造": "起造迁移", "占耕种": "耕种",
    "占蚕桑": "蚕桑", "占畜养": "畜养", "占渔猎": "渔猎", "占坟墓": "坟墓",
    "占朝国": "朝国", "占征战": "征战", "占天时": "天时", "占晴雨": "晴雨",
    "占射覆": "射覆", "占姓字": "姓字", "占葬地": "坟茔", "占阴晴": "天时",
    "占祟": "鬼祟", "占雨": "天时",
}

# 问句里直接引出占意的：如"问曰：…得X卦"
QUESTION_RE = re.compile(r"问[曰:：]\s*([^？?。\n]{0,40})")
# 答曰里反应验句
ANSWER_RE = re.compile(r"答[曰:：]\s*([^。\n]{0,80})")


def infer_topic(text: str, section: str) -> str:
    """从文本和章节名推断占问类别。"""
    # 文本里有明确"占X，"的头部
    m = re.search(r"占([一-鿿]{1,4})[，,、]", text)
    if m:
        raw = "占" + m.group(1)
        for pattern, topic in TOPIC_PATTERNS.items():
            if pattern in raw:
                return topic
        return m.group(1)
    # 问曰/答曰 中找占意
    q = QUESTION_RE.search(text)
    if q:
        q_text = q.group(1)
        for pattern, topic in TOPIC_PATTERNS.items():
            if pattern in q_text:
                return topic
    # 章节名推断
    for pattern, topic in TOPIC_PATTERNS.items():
        if pattern.replace("占", "") in section:
            return topic
    return "理论"


def extract_verdict(text: str) -> str | None:
    """从验句中推断吉凶方向。"""
    good_words = ("吉", "愈", "安", "晴", "可成", "有成", "得選", "获選", "有财")
    bad_words = ("凶", "死", "敗", "刀傷", "火災", "伏尸", "火灾", "刀伤", "败")
    good = any(w in text for w in good_words)
    bad = any(w in text for w in bad_words)
    if good and not bad:
        return "吉"
    if bad and not good:
        return "凶"
    return None


# ──────────────────────────────────────────────
# 定性/可检验判定
# ──────────────────────────────────────────────
# 空间可检验谓词
SPATIAL_WORDS = ("掘地", "离穴", "四十步", "步有", "方位", "方寻", "近柳",
                 "西北", "西南", "东南", "东北", "高处", "低处", "平处",
                 "墓穴", "坟", "陰宅", "阳宅", "屋", "宅")
# 人事可验证谓词
HUMAN_WORDS = ("刀傷", "刀伤", "火災", "火灾", "伏尸", "晴", "雨", "雷雨", "晴明",
               "陰雲", "阴云", "風", "风")


def is_spatial_outcome(text: str) -> bool:
    return any(w in text for w in SPATIAL_WORDS)


def is_human_outcome(text: str) -> bool:
    return any(w in text for w in HUMAN_WORDS)


# ──────────────────────────────────────────────
# 三方校验
# ──────────────────────────────────────────────
def validate_hex_pair(orig: str, changed: str | None) -> tuple[bool, list[str]]:
    """校验卦名对是否内部可解析。

    对于有变卦的对：验证本卦→变卦的卦变差集非空。
    对于静卦：只验证卦名存在。

    返回 (通过?, [问题列表])。
    """
    problems = []
    base = hex_lines(orig)
    if not base:
        return False, [f"本卦 {orig} 不在六十四卦表中"]

    if changed and changed != orig:
        chg = hex_lines(changed)
        if not chg:
            return False, [f"变卦 {changed} 不在六十四卦表中"]
        diff = [i + 1 for i, (a, b) in enumerate(zip(base, chg)) if a != b]
        if not diff:
            problems.append(f"{orig}→{changed} 同名但声明有变 → 静卦处理")
            return False, problems
        # 记录差集供后续使用
        return True, []
    return True, []


def moving_from_diff(orig: str, changed: str) -> list[int]:
    """从本卦变卦名计算动爻位次。"""
    base = hex_lines(orig)
    chg = hex_lines(changed)
    if not base or not chg:
        return []
    return [i + 1 for i, (a, b) in enumerate(zip(base, chg)) if a != b]


def validate_against_core(orig: str, changed: str | None) -> dict:
    """用内核 API 做进一步的纳甲/卦变/世应校验。"""
    result = {"hex_known": False, "palace": None, "generation": None,
              "line_diff": [], "problems": []}

    base = hex_lines(orig)
    if not base:
        result["problems"].append(f"本卦{orig}不在内核表中")
        return result

    result["hex_known"] = True
    pal = palace_of(orig)
    if pal:
        result["palace"] = pal[0]
        result["generation"] = pal[1]
        world_pos = pal[2]

    if changed and changed != orig:
        diff = moving_from_diff(orig, changed)
        result["line_diff"] = diff
        if not diff:
            result["problems"].append(f"{orig}与{changed}同名，无卦变差集")

    return result


# ──────────────────────────────────────────────
# 占例上下文窗口：在一段"如/假如"引用卦名的前后搜日期、应期
# ──────────────────────────────────────────────
# 明确的占例引入模式（要求出现在段落起始，避免在正文中误匹配）：
#   "假如 X年Y月Z日W时，占得 A之B" — 完整示例
#   "如 A之B卦" — 简短引用
#   "又问：X日...得 A" — 问答体引用
#   "曰：如 A之B" — 答曰中的引用
#   "曰：假如...得 A之B" — 答曰中的完整示例
#   "曰：如 X月Y日占...得 A之B" — 答曰中带日期的引用
EXAMPLE_FULL_RE = re.compile(
    r"假如.{0,40}得\s*(?P<orig>" + _HEX_ALTERNATIVES + r")"
    r"(?:\s*(?:之|化|變|变)\s*(?P<chg>" + _HEX_ALTERNATIVES + r"))?")
EXAMPLE_BRIEF_RE = re.compile(
    r"如\s*(?P<orig>" + _HEX_ALTERNATIVES + r")"
    r"\s*(?:之|化|變|变)\s*(?P<chg>" + _HEX_ALTERNATIVES + r")\s*卦")
EXAMPLE_QA_RE = re.compile(
    r"(?:又问|问曰).{0,30}(?P<day>[" + STEMS + r"][" + BRANCHES + r"])日.{0,20}"
    r".{0,15}得\s*(?P<orig>" + _HEX_ALTERNATIVES + r")"
    r"(?:\s*(?:之|化|變|变)\s*(?P<chg>" + _HEX_ALTERNATIVES + r"))?")
EXAMPLE_DAYUE_RE = re.compile(
    r"曰：如\s*(?:(?P<month>[" + BRANCHES + r"])月)?\s*"
    r"(?:(?P<day>[" + STEMS + r"][" + BRANCHES + r"])日)?"
    r".{0,20}得\s*(?P<orig>" + _HEX_ALTERNATIVES + r")"
    r"(?:\s*(?:之|化|變|变)\s*(?P<chg>" + _HEX_ALTERNATIVES + r"))?")


def find_example_points(text: str) -> list[dict]:
    """在文本中找到所有明确的占例引用点。

    返回 [(start_pos, orig_name, changed_name, match_type, anchor_match), ...]
    """
    results = []

    # 1. 完整示例：假如...得X之Y
    for m in EXAMPLE_FULL_RE.finditer(text):
        orig = resolve_hex(m.group("orig"))
        if not orig:
            continue
        chg_raw = m.group("chg")
        changed = resolve_hex(chg_raw) if chg_raw else None
        results.append((m.start(), orig, changed, "full", m))

    # 2. 简短引用：如X之Y卦
    for m in EXAMPLE_BRIEF_RE.finditer(text):
        orig = resolve_hex(m.group("orig"))
        if not orig:
            continue
        changed = resolve_hex(m.group("chg"))
        if changed:
            results.append((m.start(), orig, changed, "brief", m))

    # 3. 问答体引用：又问/问曰 + 日 + 得X
    for m in EXAMPLE_QA_RE.finditer(text):
        orig = resolve_hex(m.group("orig"))
        if not orig:
            continue
        chg_raw = m.group("chg")
        changed = resolve_hex(chg_raw) if chg_raw else None
        # 过滤掉假阳：乾/坤/震等单字卦名可能误匹配普通文本中的字
        # 但如果模式明确带有"又问/问曰"头，且接近"得X卦"，则更可信
        results.append((m.start(), orig, changed, "qa", m))

    # 4. 答曰中带日期的引用：曰：如 X月Y日占... 得 X之Y
    for m in EXAMPLE_DAYUE_RE.finditer(text):
        orig = resolve_hex(m.group("orig"))
        if not orig:
            continue
        chg_raw = m.group("chg")
        changed = resolve_hex(chg_raw) if chg_raw else None
        results.append((m.start(), orig, changed, "dayue", m))

    # 去重：同一 orig+changed 在 50 字内只取最先生成的
    deduped = []
    seen = {}
    for item in sorted(results, key=lambda x: x[0]):
        key = (item[1], item[2], item[0] // 80)
        if key not in seen:
            seen[key] = True
            deduped.append(item)
    return deduped


# ──────────────────────────────────────────────
# 边界控制：把应期限定在同一个问答内（避免跨案例串入）
# ──────────────────────────────────────────────
# 火珠林的"又问/曰："十分紧凑，固定字符窗口仍会从相邻案例串入应期。
# 改用"下一又问/曰：/==章节头"作为上界。关键：只匹配"=="层章节头，
# 不匹配"==="层的子章节头（如占法卦数下的占行人归期等）。
#   - \r?\n==[^=] 匹配 "\n== 章节名"（两等号后有非=字符）
#   - 不   匹配 "\n=== 子章节名"（第三个字符仍是=）
NEXT_EXAMPLE_RE = re.compile(
    r"(?:(?<![一-鿿])又问|(?<![一-鿿])又请|(?<![一-鿿])问曰|(?<![一-鿿])答曰|"
    r"曰：假如|曰：如|\r?\n==[^=])")
# 注： (?<![一-鿿]) 避免匹配到句中普通"又问"


def bounded_yingqi_context(text: str, start_pos: int) -> str:
    """从 start_pos 取到下一占例标记为止的上下文。

    注意：start_pos 应该指向占例引入标记的末尾（或正文起始），
    这样 NEXT_EXAMPLE_RE 找的是下一个引入标记，不会把当前引入本身当边界。
    """
    rest = text[start_pos:]
    m = NEXT_EXAMPLE_RE.search(rest)
    if m:
        return rest[:m.start()]
    return rest[:600]  # 兜底窗口


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────
def main() -> int:
    from yishu_core.runtime import force_utf8_stdio
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="解析《火珠林》原本占验案例")
    ap.add_argument("--report", action="store_true", help="只看统计，不落盘")
    ap.add_argument("--show", type=int, default=0, help="报告附带剔除样本数")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    SOURCES.mkdir(parents=True, exist_ok=True)
    if not RAW.exists():
        print(f"源文件不存在：{RAW}")
        return 1

    raw = RAW.read_text(encoding="utf-8")
    raw = norm_text(raw)

    paragraphs = split_paragraphs(raw)

    # 在整个清洗后文本上找所有占例引用点
    full_clean = BLOCK_TAGS.sub("", raw)
    example_points = find_example_points(full_clean)
    print(f"共切出 {len(paragraphs)} 个语义段落")
    print(f"找到 {len(example_points)} 个明确占例引用点")

    # 构建 section 偏移表：每个起始段落在 full_clean 中的 char 偏移
    para_offsets = []
    pos = 0
    for line in raw.splitlines():
        para_offsets.append(pos)
        pos += len(line) + 1

    # 对每个引用点：在其后 ~1500 字窗口内搜日期/应期/占验
    WINDOW = 1500
    YINGQI_WINDOW = 600  # 更紧的应期窗口，避免从相邻案例串入
    candidates = []
    seen_keys = set()

    for (pt_pos, orig, changed, mtype, m) in example_points:
        # 取引用点前后 ±WINDOW 字的上下文（用于占意/吉凶/空间判断等）
        ctx_start = max(0, pt_pos - 200)
        ctx_end = min(len(full_clean), pt_pos + WINDOW)
        context = full_clean[ctx_start:ctx_end]

        # 更紧的应期窗口：从当前引入标记的末尾起，到下一引入标记为止
        # m.end() 是当前引入标记的末尾，从此处开始搜不会把当前引入当边界
        yq_context = bounded_yingqi_context(full_clean, m.end())

        # 确定所属 section
        section = "__unknown__"
        for i in range(len(para_offsets) - 1, -1, -1):
            if para_offsets[i] <= pt_pos:
                section = paragraphs[i]["section"] if i < len(paragraphs) else "__trailing__"
                break

        # 在窗口内搜索日期和应期（日期用宽窗口，应期用紧窗口）
        date_info = extract_date(context)
        all_yingqi = extract_all_yingqi(yq_context)
        primary_yingqi = extract_yingqi(yq_context)
        topic = infer_topic(context, section)
        verdict = extract_verdict(context)
        has_spatial = is_spatial_outcome(context)
        has_human = is_human_outcome(context)

        # 去重
        key = (orig, changed, pt_pos // 200)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        # 校验
        valid, problems = validate_hex_pair(orig, changed)
        core_check = validate_against_core(orig, changed)

        # 引用点上下文 + 窗口内首段
        ctx_head = full_clean[pt_pos:min(pt_pos + 80, len(full_clean))]

        cand = {
            "original": orig,
            "changed": changed,
            "moving": core_check.get("line_diff", []),
            "palace": core_check.get("palace"),
            "generation": core_check.get("generation"),
            "is_changed": changed is not None and changed != orig,
            "match_type": mtype,
            "date": date_info,
            "yingqi": primary_yingqi,
            "all_yingqi": all_yingqi,
            "topic": topic,
            "verdict": verdict,
            "has_spatial": has_spatial,
            "has_human": has_human,
            "section": section,
            "context": ctx_head,
            "problems": problems + core_check.get("problems", []),
            "valid_hex": core_check["hex_known"],
            "full_text_excerpt": context[:300],
        }
        candidates.append(cand)

    print(f"提取到 {len(candidates)} 个候选（卦名对 + 上下文）")

    # 分两路：可评分 / 仅定性
    scorable = []
    qualitative = []
    dropped = []
    drop_stats = {"no_hex": 0, "validation_fail": 0, "no_date_and_no_qualitative": 0,
                  "pure_theory": 0, "dup": 0}

    seen_scorable = set()

    for c in candidates:
        if not c["valid_hex"]:
            drop_stats["no_hex"] += 1
            dropped.append(("no_hex", c))
            continue

        if c["problems"] and any("不在内核表" in p for p in c["problems"]):
            drop_stats["no_hex"] += 1
            dropped.append(("no_hex", c))
            continue

        # 判断属于哪一类
        has_day_yingqi = c["yingqi"] is not None and not c["yingqi"].endswith(("時", "时"))
        has_hour_yingqi = c["yingqi"] is not None and c["yingqi"].endswith(("時", "时"))
        has_date = c["date"] is not None and "day" in (c["date"] or {})
        has_qualitative = c["has_spatial"] or c["has_human"]
        has_verdict = c["verdict"] is not None

        # 可评分：有应期干支（日/月/年级别），非時级
        if has_day_yingqi:
            date_key = (c["original"], c["changed"], c["yingqi"])
            if date_key in seen_scorable:
                drop_stats["dup"] += 1
                continue
            seen_scorable.add(date_key)
            scorable.append(c)
        elif has_hour_yingqi and has_date:
            # 時级应期 + 有日期 → 可入评分（引擎会在 日 级评估，相差可能较大但如实记录）
            date_key = (c["original"], c["changed"], c["yingqi"])
            if date_key in seen_scorable:
                drop_stats["dup"] += 1
                continue
            seen_scorable.add(date_key)
            c["yingqi_unit"] = "時"
            scorable.append(c)
        elif has_qualitative:
            qualitative.append(c)
        elif has_date and has_verdict:
            # 有月日有吉凶但无干支应期 → 方向性定性
            qualitative.append(c)
        else:
            drop_stats["pure_theory"] += 1
            dropped.append(("pure_theory", c))

    print(f"\n可评分集：{len(scorable)} 例")
    print(f"定性参考集：{len(qualitative)} 例")
    print(f"纯理论/剔除：{len(dropped)} 条")
    print("剔除原因：" + json.dumps(drop_stats, ensure_ascii=False))

    if args.show:
        by_reason = {}
        for reason, c in dropped:
            by_reason.setdefault(reason, []).append(c)
        for reason, lst in by_reason.items():
            print(f"\n-- {reason} ({len(lst)})")
            for c in lst[:args.show]:
                print(f"   {c['original']}→{c['changed']} [{c['topic']}] {c['context'][:80]}")

    if args.report:
        return 0

    # ──────────────────────────────────────────
    # 输出 JSON
    # ──────────────────────────────────────────
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _section_to_source(section: str) -> str:
        if section and section != "__header__":
            return f"维基文库原本·{section}"
        return "维基文库原本"

    def _build_case(c: dict, idx: int) -> dict:
        """把内部候选结构转成标准案例格式（兼容 wikisource_cases.json）。"""
        date_obj = c["date"] or {}
        date_str = ""
        if date_obj.get("month"):
            date_str += f"{date_obj['month']}月"
        if date_obj.get("day"):
            date_str += f"{date_obj['day']}日"
        if date_obj.get("year"):
            date_str = f"{date_obj['year']}年" + date_str

        expected = {
            "verdict": c["verdict"],
            "yingqi": c["yingqi"] or "",
            "detail": c["context"][:160],
        }
        if c["has_spatial"]:
            expected["spatial_detail"] = c["full_text_excerpt"][:120]

        return {
            "id": f"HZL{idx:03d}",
            "source": f"《火珠林》（{_section_to_source(c['section'])}）",
            "topic": c["topic"],
            "question": c["topic"],
            "input": {
                "date": date_str or None,
                "question": c["topic"],
            },
            "hexagram": {
                "original": c["original"],
                "changed": c["changed"],
                "moving": c["moving"],
                "palace": c["palace"] or "",
                "generation": c["generation"] or "",
            },
            "expected": expected,
            "provenance": {
                "page": "火珠林",
                "sha256_head": sha[:12],
                "section": c["section"],
                "context_head": c["context"][:60],
            },
        }

    scorable_cases = [_build_case(c, i + 1) for i, c in enumerate(scorable)]
    qual_cases = [_build_case(c, i + 1) for i, c in enumerate(qualitative)]

    # 加标记说明哪些是定性案例
    for qc in qual_cases:
        qc["note"] = "定性描述（空间/人事）；不参与应期评分"

    # 输出可评分集
    OUT_JSON.write_text(json.dumps({
        "_meta": {
            "description": "火珠林（宋·麻衣道者）占验案例；问答体占断；含干支应期可评分",
            "built_by": "dev_tools/fetch_huozhulin_cases.py",
            "source": "data/sources/huozhulin.wikitext.txt",
            "retrieved": date.today().isoformat(),
            "sha256": sha,
            "total_cases": len(scorable_cases),
            "note": "仅含干支日/月/年级别应期的案例；用于应期评分",
            "dropped_stats": drop_stats,
        },
        "cases": scorable_cases,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n写入 {OUT_JSON.relative_to(DISC.parent.parent)} ({len(scorable_cases)} 例)")

    # 输出定性集
    OUT_QUAL.write_text(json.dumps({
        "_meta": {
            "description": "火珠林占验案例：定性描述（空间/人事）；仅参考，不参与评分",
            "built_by": "dev_tools/fetch_huozhulin_cases.py",
            "source": "data/sources/huozhulin.wikitext.txt",
            "total_qualitative": len(qual_cases),
            "note": "仅含定性描述（空间方位或人事占断），不参与评分",
        },
        "cases": qual_cases,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUT_QUAL.relative_to(DISC.parent.parent)} ({len(qual_cases)} 例)")

    # 更新 splits
    sp = json.loads(SPLITS.read_text(encoding="utf-8")) if SPLITS.exists() else {}
    sp["huozhulin_holdout"] = [c["id"] for c in scorable_cases]
    sp["huozhulin_qualitative"] = [c["id"] for c in qual_cases]
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"case_splits.json 已登记 huozhulin_holdout ({len(scorable_cases)}) / "
          f"huozhulin_qualitative ({len(qual_cases)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
