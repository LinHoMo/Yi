# -*- coding: utf-8 -*-
"""从《易隐》殆知阁转录本（data/sources/yiin_dz.dz.txt）抽取完整占例，
建成**永不参与调参**的外部验证集 `yiin_holdout`（ID: YI***）。

    python dev_tools/build_yiin_cases.py [--dry-run] [--selftest]

    --selftest：九道门逐门负例＋应期两式正负例（不写盘）；负例不过即 rc=1。

为什么另立这一集（第三百二十六批）：《易隐》（清·曹九锡）是本科在库书源里
**唯一"有规整六爻卦表、却零条正式案例"**的大部头——底本 151457 字、59 个六爻
渲染块，此前只在 `verifications.json` 留了 13 条 status=「仅验语」的台账
（有声无盘），从未进过任何 `*_cases.json`。同期的《增删卜易》已抽 246 条、
《卜筮正宗》已抽 90 条，本书的抽取率是 0，这不是"书里没有"，是"没人抽"。

dz 本案例形态（逐字示例，L1037-1046）：

    庚寅年，庚辰月，丁卯日，甲辰时，卜自己寿命，得颐之复。
    　　　　　　　　　巽宫：山雷颐（游魂）　　　　　　坤宫：地雷复（六合）
    六神 　伏　　神　【本　　卦】　　　　　　　　　　【变　　卦】
    　　　　　　　▅▅▅▅▅　兄弟丙寅木　　○→　▅▅　▅▅　官鬼癸酉金
    …（六爻，**上爻在前、初爻在后**）…
    世动化丑来刑，……故其人病起正月，至四月癸卯日故也。

与《增删卜易》的差别：本书卦表带「六神／伏神」两列（伏神在行首、无伏神处留空），
动爻以 `○→`（阳动）/`×→`（阴动）标在本爻与变爻之间，世应写在爻侧。

九道门（任一门不过即 excluded，写明原因，绝不放宽）：
  1. 块高恰为 6 行（六爻齐全；不足 6 行者不猜补）
  2. 表头可解析出「宫＋卦名（＋卦性）」，且卦名归一到内核 64 卦短名
     （「山雷颐」→颐、「乾为天」→乾；变卦同）
  3. **纳甲自洽**：六爻地支 ≡ 内核 `najia_branch(本卦, 位)` 逐位相符
  4. **阴阳自洽**：爻符号（▅▅▅▅▅/▅▅　▅▅）≡ 内核 BAGUA_LINES 推得的本卦爻性
     （BAGUA_LINES 的爻序是**初→上**，与卦表的上→初相反，此处按位索引，不做拼接）
  5. **动爻自洽**：`○→`/`×→` 标记的爻位集合 ≡ 本卦⊕变卦 的差集；
     无变卦时不得有动标记（静卦）
  6. 时点可还原：块上方 2–4 行内有含日柱的行，且能解析出月建＋日柱
     （年、旬、时可缺；缺月建者不收——月建是旺衰判据，缺了不可评）
  7. 占题可解析：日柱行「日」字之后、「得/遇/卜得」之前的主语短语非空
  8. 应期只取实录，两式：①结果锚词（果/故/竟/卒）在日期前 20 字内，或「X日故」后置；
     ②「果」在日期后 20 字内，取**最近的在前日期**（「果于X日」则取果后日期，
     「果于木日」这类符号日不收）。预测句（待/直至/次日/逢/至 之后的日）只记 claim，
     不进评分分母（与《增删卜易》门 6 同口径）。
  9. 不与在册案例同案：按（本卦, 变卦, 月建, 日柱）与全部 `*_cases.json` 比对

吉凶一律记 null（`N/A 不进分母`）：本书断语是散文（「决难免死」「理宜多寿」
「后果然」），把散文映射成吉/凶标签属解读，越 SKILL.md 铁律一。本集定位是
**应期语料通道**，与 `zengshan_dz_holdout` 同一定位。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# 控制台编码守卫：GBK/cp936 下中文输出会退化成乱码且 rc 仍为 0（判据见 check.py 编码不变式）
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import kernel_dir  # noqa: E402

sys.path.insert(0, str(kernel_dir(__file__)))

from yishu_core.najia import najia_branch  # noqa: E402
from yishu_core.symbols import BAGUA_LINES, HEXAGRAM_TRIGRAMS  # noqa: E402

SRC = DISC / "data" / "sources" / "yiin_dz.dz.txt"
OUT = DISC / "data" / "cases" / "yiin_cases.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"
REPORT = DISC / "docs" / "YIIN-CASE-AUDIT.md"

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
SHORT = list(HEXAGRAM_TRIGRAMS.keys())

YAO_SYM = re.compile(r"(▅{5}|▅{2}\u3000▅{2})")
PAL = re.compile(r"([乾坤震巽坎离艮兑])宫[：:]\s*([^\u3000（(]{2,8})(?:（([^）]*)）)?")
LIUQIN = re.compile(r"(兄弟|父母|子孙|妻财|官鬼)([%s])([%s])([金木水火土])" % (STEMS, BRANCHES))
DAY_LINE = re.compile(r"([%s])([%s])日" % (STEMS, BRANCHES))
MONTH_LINE = re.compile(r"([%s])([%s])月" % (STEMS, BRANCHES))
YEAR_LINE = re.compile(r"([%s])([%s])年" % (STEMS, BRANCHES))
HOUR_LINE = re.compile(r"([%s])([%s])时" % (STEMS, BRANCHES))
XUN = re.compile(r"([%s][%s])旬" % (STEMS, BRANCHES))

# 占题归类（只做**分类**，不做吉凶/用神判断——那属解读）
TOPICS = [
    ("寿命", ("寿命", "寿")),
    ("疾病", ("病", "疾")),
    ("婚姻", ("婚", "姻", "娶", "嫁")),
    ("功名", ("求官", "选官", "为官", "起官", "文书", "科")),
    ("求财", ("求财", "财", "脱货")),
    ("词讼", ("讼",)),
    ("行人", ("回", "远行", "行人", "归")),
    ("盗贼", ("盗", "贼", "拐", "捕")),
    ("迁移", ("迁移", "迁")),
    ("家宅", ("坟茔", "宅", "居")),
    ("六畜", ("六畜", "畜")),
]

# 应期分两档，口径与《增删卜易》门 6 一致（只把**实录**计入评分）：
#   VERIFIED＝果/故/竟/卒 之后的干支日，或「干支日故」这类**后置**锚词（书已验）；
#             423 批补第二式：「果」在日期之后（「后至辛卯日…果得财也」），
#             取最近的在前日期；「果于X日」取果后日期（符号日如「木日」不收）。
#   CLAIM＝待/直至/次日/逢/至 之后的干支日（书判预期，不进评分分母）
# 两档都不取占测日自重——日辰行在块上方，不在断语段内，天然隔离。
YQ = r"([%s]?[%s]{1,2})日" % (STEMS, BRANCHES)
VERIFIED_PRE = re.compile(r"[果故竟卒][^。；;]{0,20}?" + YQ)
VERIFIED_POST = re.compile(YQ + r"[故竟卒]")
CLAIM_YQ = re.compile(r"(?:直?待|直至|须待|必待|次日|翌日|逢|至)[^。；;]{0,20}?" + YQ)
GUO = "果"
RESULT_AFTER = re.compile(r"果\s*[于於]\s*([%s]?[%s]{1,2})日" % (STEMS, BRANCHES))


def verified_of(seg: str) -> tuple[str, str] | None:
    """单句实录应期 → (干支, 原句)／None。两式见模块 docstring 门 8。

    第二式必须取**最近的**在前日期：同一句里常有机制日期
    （「长生于亥日，后至辛卯日…果得财」），取首个会把机制日当验期。
    「果于X日」的结果日期写在果后；X 不是地支（「木日」「火日」）时不可评分。
    """
    m = VERIFIED_PRE.search(seg) or VERIFIED_POST.search(seg)
    if m:
        return m.group(1), seg.strip()
    g = seg.find(GUO)
    if g < 0:
        return None
    after = seg[g:]
    m2 = RESULT_AFTER.match(after)
    if m2:
        return m2.group(1), seg.strip()
    if re.match(r"果\s*[于於]", after):
        return None
    best = None
    for dm in re.finditer(YQ, seg):
        if dm.end() <= g and g - dm.end() <= 20:
            best = dm
    return (best.group(1), seg.strip()) if best else None



def full_to_short(name: str) -> str | None:
    """「山雷颐」→颐、「乾为天」→乾。取最长后缀匹配，防「大过」被「过」截断。"""
    name = name.strip()
    if "为" in name:
        i = name.index("为")
        if i > 0:
            return name[i - 1]
    best = None
    for s in SHORT:
        if name.endswith(s) and (best is None or len(s) > len(best)):
            best = s
    return best


def hex_lines(short: str) -> list[int]:
    """本卦六爻爻性，**初→上**（0=阴, 1=阳）。"""
    up, dn = HEXAGRAM_TRIGRAMS[short]
    return BAGUA_LINES[dn] + BAGUA_LINES[up]


def split_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks, cur = [], []
    for i, l in enumerate(lines):
        if "▅" in l:
            cur.append(i)
        else:
            if len(cur) >= 5:
                blocks.append((cur[0], cur[-1]))
            cur = []
    if len(cur) >= 5:
        blocks.append((cur[0], cur[-1]))
    return blocks


def case_window(lines: list[str], blocks: list[tuple[int, int]], line_no: int) -> str:
    """该案的书文窗口：日柱行 → 下一卦表块的日柱行。

    `expected.detail` 必须是这个窗口里的**逐字子串**（427 批：[16] 据此验证
    yiin 的断语没有在重生成/手改里被换成别案或凭空造句）。
    """
    a = int(line_no) - 1
    b = next((bb for aa, bb in blocks if aa == a), None)
    if b is None:
        return ""
    start = a
    for k in (2, 3, 4):
        if a - k >= 0 and DAY_LINE.search(lines[a - k]) and "▅" not in lines[a - k]:
            start = a - k
            break
    stop = len(lines)
    for aa, bb in blocks:
        if aa > b:
            for k in (2, 3, 4):
                if (aa - k >= 0 and aa - k > a and DAY_LINE.search(lines[aa - k])
                        and "▅" not in lines[aa - k]):
                    stop = aa - k
                    break
            else:
                stop = aa
            break
    return "\n".join(lines[start:stop])


def parse_yao(lines: list[str], a: int, b: int) -> tuple[list[dict] | None, str]:
    """解析六爻，行序为上爻→初爻；返回按**初→上**排列的列表。"""
    ys = lines[a:b + 1]
    if len(ys) != 6:
        return None, f"块高={len(ys)}（非 6 行，不猜补）"
    out = []
    for k, yl in enumerate(ys):
        parts = YAO_SYM.split(yl)
        idx = next((j for j, p in enumerate(parts) if YAO_SYM.fullmatch(p)), None)
        if idx is None:
            return None, f"第{k+1}行无爻符号"
        mid = parts[idx + 1]
        after = parts[idx + 3] if len(parts) > idx + 3 else ""
        m = LIUQIN.search(mid)
        if not m:
            return None, f"第{k+1}行六亲干支不可解析:{mid.strip()[:24]!r}"
        liuqin, stem, branch, wx = m.groups()
        out.append(dict(
            pos=6 - k,
            yin=("▅▅　▅▅" in parts[idx]),
            liuqin=liuqin, stem=stem, branch=branch, wx=wx,
            shi=("世" in mid), ying=("应" in mid),
            moving=("○→" in mid or "×→" in mid or "○→" in after or "×→" in after),
            fushen=parts[idx - 1].replace("\u3000", ""),
        ))
    out.reverse()  # 上→初 转为 初→上
    return out, ""


def parse_block(lines: list[str], a: int, b: int) -> dict:
    yao, err = parse_yao(lines, a, b)
    if err:
        return {"fail": err}

    head, head_k = None, None
    for k in (1, 2, 3):
        if a - k >= 0 and "宫" in lines[a - k]:
            head, head_k = lines[a - k], a - k
            break
    if head is None:
        return {"fail": "无宫位表头"}
    pals = PAL.findall(head)
    if not pals:
        return {"fail": "宫位行不可解析"}
    ben_pal, ben_full, ben_tag = pals[0]
    ben = full_to_short(ben_full)
    if not ben:
        return {"fail": f"本卦名不可解析:{ben_full}"}
    bian, bian_tag = None, ""
    if len(pals) >= 2:
        bian = full_to_short(pals[1][1])
        bian_tag = pals[1][2]
        if not bian:
            return {"fail": f"变卦名不可解析:{pals[1][1]}"}

    # 门 3：纳甲自洽
    for y in yao:
        exp = najia_branch(ben, y["pos"])
        if exp != y["branch"]:
            return {"fail": f"纳甲不符 位{y['pos']} 文本{y['branch']} 内核{exp}"}

    # 门 4：阴阳自洽
    bl = hex_lines(ben)
    for y in yao:
        if y["yin"] == bool(bl[y["pos"] - 1]):
            return {"fail": f"阴阳不符 位{y['pos']} 文本yin={y['yin']}"}

    # 门 5：动爻 ≡ 差集
    movers = sorted(y["pos"] for y in yao if y["moving"])
    if bian:
        b2 = hex_lines(bian)
        diff = sorted(p for p in range(1, 7) if b2[p - 1] != bl[p - 1])
        if movers != diff:
            return {"fail": f"动爻不符 标记{movers} 差集{diff}"}
    elif movers:
        return {"fail": "有动标记但无变卦（表头缺变卦列）"}

    # 门 6：时点
    day_k = None
    for k in (2, 3, 4):
        if a - k >= 0 and DAY_LINE.search(lines[a - k]) and "▅" not in lines[a - k]:
            day_k = a - k
            break
    if day_k is None:
        return {"fail": "块上方 2–4 行内无日柱行"}
    date_line = lines[day_k]
    d = DAY_LINE.search(date_line)
    mo = MONTH_LINE.search(date_line)
    if not mo:
        return {"fail": f"缺月建，不可评旺衰:{date_line.strip()[:30]}"}
    day_gz = d.group(0)[:-1]
    mon_gz = mo.group(0)[:-1]
    yr = YEAR_LINE.search(date_line)
    xun = XUN.search(date_line)
    hr = HOUR_LINE.search(date_line)

    # 门 7：占题。日柱之后先剥掉时柱（「己丑日庚午时，子占父寿」的时柱不属于占题）
    tail = date_line[d.end():]
    tail = re.sub(r"^\s*[，,]?\s*[%s][%s]时\s*[，,]?" % (STEMS, BRANCHES), "", tail)
    tail = re.split(r"[得遇]", tail)[0]
    tail = tail.strip("，。、；; ,")
    if not tail:
        return {"fail": "占题不可解析:日柱后为空"}
    q_clean = tail
    # 「用有虑火灾者，卜得萃之困」→ 取证前的背景语（原书以事由代占题）
    m3 = re.match(r"^(.*?[者])[，,]\s*([占卜问].*)$", tail)
    if m3:
        q_clean = re.sub(r"^(用有|有恐|有欲|有|因|为)+", "", m3.group(1)).rstrip("者").strip()
    # 「占六畜。得蒙之师卦」这类句号切分后只剩动词的，退回事由段
    if len(q_clean) <= 1 or q_clean in ("卜", "占", "问"):
        return {"fail": f"占题仅剩动词:{tail[:24]!r}"}

    # 门 8：应期（只认实录锚词）
    body = []
    for j in range(b + 1, min(len(lines), b + 4)):
        t = lines[j].strip()
        if not t or "▅" in t:
            break
        body.append(t)
    speech = body[0] if body else ""
    yq, yq_raw, yq_claim, yq_claim_raw = "", "", "", ""
    for seg in re.split(r"[。；;]", speech):
        v = verified_of(seg)
        if v:
            # 实录优先：同一句的「直待…果到」不再重复记为 claim
            if not yq:
                yq, yq_raw = v
            continue
        if not yq_claim:
            m3 = CLAIM_YQ.search(seg)
            if m3:
                yq_claim, yq_claim_raw = m3.group(1), seg.strip()
    branches = [c for c in yq if c in BRANCHES]

    # 世次：由「世」所在爻位推（游魂世在四、归魂世在三，与表头卦性互证）
    shi_pos = next((y["pos"] for y in yao if y["shi"]), None)
    gen = {1: "一世", 2: "二世", 3: "三世", 4: "四世", 5: "五世", 6: "六世"}.get(shi_pos, "")

    topic = next((t for t, kws in TOPICS if any(kw in q_clean for kw in kws)), "")

    return dict(
        ben=ben, bian=bian, ben_pal=ben_pal, generation=gen,
        ben_tag=ben_tag, bian_tag=bian_tag,
        moving=movers, yao=yao,
        date_line=date_line,
        date=(f"{yr.group(0) if yr else ''}{mon_gz}月"
              f"{xun.group(0) if xun else ''}{day_gz}日{hr.group(0) if hr else ''}"),
        day_gz=day_gz, mon_gz=mon_gz,
        question=q_clean, question_raw=tail, topic=topic,
        speech=speech, yingqi=yq, yingqi_raw=yq_raw,
        yingqi_claim=yq_claim, yingqi_claim_raw=yq_claim_raw,
        head_line=head_k + 1, day_line=day_k + 1,
    )


def drop_duplicates(parsed: list[dict], seen: dict[tuple, str]) -> tuple[list[tuple], list[dict]]:
    """门 9：先与在册案例比、再集内互比（都含**占题**）。返回 (剔除清单, 保留)。

    占题必须进键：326 批初版只按「本卦＋变卦＋月建＋日柱」，把《易隐》
    **同盘异题**的教学式复用（如睽之归妹·丙子月丁卯日分占坟茔/婚姻/求官）
    一次误杀 7 条。selftest 反向守两件：同盘异题不剔、同盘同题必剔。
    """
    dup, keep = [], []
    for p in parsed:
        clash = False
        for k, cid in seen.items():
            if (k[0] == p["ben"] and k[1] == p["bian"]
                    and p["mon_gz"] in k[2] and p["day_gz"] in k[2]
                    and k[3].strip() == p["question"].strip()):
                dup.append((p["line"], cid))
                clash = True
                break
        if not clash:
            keep.append(p)
    inner, uniq = {}, []
    for p in keep:
        key = (p["ben"], p["bian"], p["mon_gz"], p["day_gz"], p["question"].strip())
        if key in inner:
            dup.append((p["line"], inner[key]))
            continue
        inner[key] = f"L{p['line']}"
        uniq.append(p)
    return dup, uniq


def run_selftest() -> int:
    """九道门＋应期两式的负例自证（只读底本，不写盘）。"""
    fails: list[str] = []
    lines = SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    blocks = split_blocks(lines)
    good = None
    for a, b in blocks:
        r = parse_block(lines, a, b)
        if "fail" not in r and r["bian"] and r["moving"]:
            good = (a, b)
            break
    if good is None:
        print("  × selftest：找不到带变卦与动爻的健康块")
        return 1
    a, b = good
    base = parse_block(lines, a, b)
    if "fail" in base:
        fails.append(f"健康块被拒：{base['fail']}")

    def probe(label: str, mutate, expect: str) -> None:
        tmp = list(lines)
        mutate(tmp)
        r = parse_block(tmp, a, b)
        if "fail" not in r or expect not in r["fail"]:
            fails.append(f"{label}：未按预期判失败（{r.get('fail') or '通过'}）")

    def date_idx(t: list[str]) -> int:
        for k in (2, 3, 4):
            if a - k >= 0 and DAY_LINE.search(t[a - k]) and "▅" not in t[a - k]:
                return a - k
        return -1

    # 门 1：块高（5 行不猜补）
    _, err = parse_yao(lines, a, b - 1)
    if not err:
        fails.append("门 1 块高：5 行未被拒")

    def m2(t):
        for k in (1, 2, 3):
            if a - k >= 0 and "宫" in t[a - k]:
                t[a - k] = "表头缺失"
                return
    probe("门 2 表头", m2, "无宫位表头")

    def m3(t):
        for j in range(a, b + 1):
            mm = LIUQIN.search(t[j])
            if mm:
                new = "子" if mm.group(3) != "子" else "丑"
                t[j] = t[j][:mm.start(3)] + new + t[j][mm.end(3):]
                return
    probe("门 3 纳甲", m3, "纳甲不符")

    def m4(t):
        for j in range(a, b + 1):
            if "▅▅▅▅▅" in t[j]:
                t[j] = t[j].replace("▅▅▅▅▅", "▅▅　▅▅", 1)
                return
            if "▅▅　▅▅" in t[j]:
                t[j] = t[j].replace("▅▅　▅▅", "▅▅▅▅▅", 1)
                return
    probe("门 4 阴阳", m4, "阴阳不符")

    def m5(t):
        for j in range(a, b + 1):
            if "○→" in t[j] or "×→" in t[j]:
                t[j] = t[j].replace("○→", "   ").replace("×→", "   ")
                return
    probe("门 5 动爻", m5, "动爻不符")

    def m6(t):
        di = date_idx(t)
        if di >= 0:
            t[di] = MONTH_LINE.sub("月", t[di], count=1)
    probe("门 6 月建", m6, "缺月建")

    def m7(t):
        di = date_idx(t)
        if di >= 0:
            d = DAY_LINE.search(t[di])
            t[di] = t[di][:d.end()]
    probe("门 7 占题", m7, "占题不可解析")

    # 门 8：实录两式＋不取预测/机制/符号日
    yq_cases = [
        ("果于子日建功", "子"),
        ("后至辛卯日，财值巳辰，果得财也", "辛卯"),
        ("况投长生于亥日，后至辛卯日，财值巳辰，果得财也", "辛卯"),
        ("待丁未日冲破丑合，果回家也", "丁未"),
        ("果于辛卯日死", "辛卯"),
        ("更加卯日冲破，果于木日死也", None),
        ("故当日未得，次日甲辰，寅卯兄弟又空，内财帮比而得也", None),
        ("犹与辰日六合，故未到官者，可散也", None),
    ]
    for seg, want in yq_cases:
        got = verified_of(seg)
        if (got[0] if got else None) != want:
            fails.append(f"门 8 应期：{seg[:16]!r} → {got[0] if got else None!r}，应 {want!r}")
    m = CLAIM_YQ.search("直待癸酉日得")
    if not m or m.group(1) != "癸酉":
        fails.append("门 8 预期句未记 claim")

    # 门 9：判定键含占题——同盘异题不剔、同盘同题必剔、集内重复必剔
    demo = {"ben": "乾", "bian": "坤", "mon_gz": "子", "day_gz": "甲子",
            "question": "占甲", "line": 1}
    seen = {("乾", "坤", "子月甲子日", "占乙"): "ZD001"}
    dup, keep = drop_duplicates([dict(demo)], seen)
    if dup:
        fails.append("门 9 同案：同盘异题被误剔")
    dup2, _ = drop_duplicates([dict(demo, question="占乙", line=2)], seen)
    if dup2 != [(2, "ZD001")]:
        fails.append(f"门 9 同案：同盘同题未剔（{dup2!r}）")
    dup3, uniq3 = drop_duplicates([dict(demo, line=3), dict(demo, line=4)], {})
    if len(dup3) != 1 or len(uniq3) != 1:
        fails.append("门 9 同案：集内重复未剔")

    for f in fails:
        print(f"  × selftest：{f}")
    if fails:
        return 1
    print("  √ selftest：九道门负例全抓；应期取最近在前日期／「果于符号日」不收／"
          "预测句只记 claim；同盘异题不剔、同盘同题必剔")
    return 0


def _check_sync() -> int:
    """同源复验：落盘集须由当前底本逐字可复现（sha 不变且每条锚句仍在原处）。"""
    if not OUT.exists():
        print("× 落盘集不存在：%s" % OUT.relative_to(DISC))
        return 1
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    meta = doc.get("_meta") or {}
    text = SRC.read_text(encoding="utf-8")
    fails = []
    if meta.get("sha256") != hashlib.sha256(SRC.read_bytes()).hexdigest():
        fails.append("底本 sha256 已变——须重跑本脚本重建 %s" % OUT.name)
    cases = doc.get("cases") or []
    if meta.get("n") != len(cases):
        fails.append("n=%s ≠ 实际 %d 条" % (meta.get("n"), len(cases)))
    checked = 0
    for c in cases:
        detail = (c.get("expected") or {}).get("detail") or ""
        if detail and detail not in text:
            fails.append("%s 的 expected.detail 已不在底本（%s…）" % (c.get("id"), detail[:24]))
            continue
        checked += 1
    ok = "全部一致" if not fails else "%d 处失效" % len(fails)
    print("同源复验：%d/%d 条锚句仍逐字命中底本；%s" % (checked, len(cases), ok))
    for f in fails:
        print("  ×", f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="从《易隐》dz 底本抽建 yiin_holdout")
    ap.add_argument("--dry-run", action="store_true", help="只打印门禁结果，不写文件")
    ap.add_argument("--selftest", action="store_true", help="九道门＋应期负例自证（不写盘）")
    ap.add_argument("--check", action="store_true",
                    help="只复验已生成 JSON 的锚句仍逐字命中底本，不写文件（[46] 同步门挂此）")
    args = ap.parse_args()
    if args.selftest:
        return run_selftest()
    if args.check:
        return _check_sync()

    raw = SRC.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    lines = raw.decode("utf-8").splitlines()
    blocks = split_blocks(lines)

    parsed, excluded = [], []
    for a, b in blocks:
        r = parse_block(lines, a, b)
        r["line"] = a + 1
        if "fail" in r:
            excluded.append((a + 1, r["fail"]))
        else:
            parsed.append(r)

    # 门 9：与在册案例同案。判定键含**占题**——《易隐》有把同一盘（同卦同月日）
    # 分派给四五个不同占题的教学式复用（如「睽之归妹·丙子月丁卯日」分别占坟茔/
    # 婚姻/求官/求财），那是同盘异题、用神各不相同，不是重复占验，不能按盘面剔。
    seen: dict[tuple, str] = {}
    for p in sorted((DISC / "data" / "cases").glob("*_cases.json")):
        if p.name == OUT.name:
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for c in data.get("cases", []):
            h = c.get("hexagram") or {}
            inp = c.get("input") or {}
            key = (h.get("original"), h.get("changed"), str(inp.get("date", "")),
                   str(c.get("question") or inp.get("question", "")))
            seen[key] = c.get("id", "?")

    dup, uniq = drop_duplicates(parsed, seen)

    print(f"底本 {SRC.name}  {len(raw)} bytes  sha256={sha[:16]}…")
    print(f"卦表块 {len(blocks)}  过门 {len(parsed)}  排出门 {len(excluded)}  同案剔除 {len(dup)}  入库 {len(uniq)}")
    for L, why in excluded:
        print(f"  × L{L}: {why}")
    for L, cid in dup:
        print(f"  = L{L}: 与在册 {cid} 同案")

    cases = []
    for i, p in enumerate(uniq, 1):
        cases.append({
            "id": f"YI{i:03d}",
            "source": "《易隱》（殆知阁转录本）",
            "topic": p["topic"],
            "question": p["question"],
            "input": {"date": p["date"], "question": p["question"]},
            "hexagram": {
                "original": p["ben"], "changed": p["bian"],
                "moving": p["moving"],
                "palace": p["ben_pal"], "generation": p["generation"],
                "note": p["ben_tag"],
            },
            "expected": {
                "verdict": None,
                "use_god": "",
                "yingqi": (p["yingqi"] + "日") if p["yingqi"] else "",
                "yingqi_branches": [c for c in p["yingqi"] if c in BRANCHES],
                # 书判预期（待/直至/次日/逢 之后的日）：只作参考，**不进评分分母**，
                # 避免把"书说会在某日"当成"实际某日"（与 zengshan_dz 门 6 同口径）
                "yingqi_claim": (p["yingqi_claim"] + "日") if p["yingqi_claim"] else "",
                "detail": p["yingqi_raw"] or p["yingqi_claim_raw"] or p["speech"][:60],
            },
            "provenance": {
                "source_file": "data/sources/yiin_dz.dz.txt",
                "sha256": sha,
                "line": p["line"],
                "day_line": p["day_line"],
                "table_line": p["line"],
                "quote": p["date_line"].strip(),
                "speech_head": p["speech"][:40],
            },
        })

    n_yq = sum(1 for c in cases if c["expected"]["yingqi"])
    print(f"\n入库 {len(cases)} 例；带应期 {n_yq} 例（{100.0*n_yq/max(1,len(cases)):.0f}%）")
    for c in cases[:8]:
        print(f"  {c['id']} L{c['provenance']['line']:5d} {c['hexagram']['original']}"
              f"{'之'+c['hexagram']['changed'] if c['hexagram']['changed'] else '（静）'}"
              f"  {c['input']['date']:<22s} {c['question'][:16]:<18s} 应期={c['expected']['yingqi'] or '—'}")

    if args.dry_run:
        print("\n--dry-run：未写文件")
        return 0

    payload = {
        "_meta": {
            "book": "易隐",
            "author": "清·曹九锡（辑）",
            "source": "殆知阁转录本（github.com/garychowcmu/daizhigev20）",
            "source_file": "data/sources/yiin_dz.dz.txt",
            "sha256": sha,
            "built_by": "dev_tools/build_yiin_cases.py",
            "split": "yiin_holdout",
            "blocks": len(blocks),
            "passed": len(parsed),
            "excluded": len(excluded),
            "duplicates": len(dup),
            "n": len(cases),
            "with_yingqi": n_yq,
            "verdict_policy": "吉凶一律 null：本书断语为散文，映射吉/凶属解读，越铁律一。本集为应期语料通道。",
            "note": "外部验证集，永不参与调参；与 zengshan_dz_holdout 同定位。",
        },
        "cases": cases,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # 登记分片（保留既有键序，追加在末尾）
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    splits["yiin_holdout"] = [c["id"] for c in cases]
    splits["note_yiin_holdout"] = (
        "《易隐》dz 底本直抽（九道门：纳甲/阴阳/动爻三重自洽＋时点＋占题＋同案去重）。"
        "外部验证集，永不参与调参；吉凶记 null，只评应期。"
    )
    SPLITS.write_text(json.dumps(splits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\n写出 {OUT.relative_to(DISC)}（{len(cases)} 例）")
    print(f"登记 {SPLITS.relative_to(DISC)} 键 yiin_holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
