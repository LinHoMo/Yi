# -*- coding: utf-8 -*-
"""案例库自洽门：一条案例的「日辰 / 应期」必须与它**自己引用的那段书文**一致。

为什么需要它（2026-10-10 校勘）：`huozhulin_holdout` 只有 2 例，实测两例都是坏的——
  · HZL001 把《火珠林》源L458（癸亥日占坎之蒙、断**晴**）与源L459（甲辰日占乾之大壮、
    **申时**雷雨）拼成一条：date/topic 来自前一条，卦与应期来自后一条；
  · HZL002 的 expected.yingqi「甲寅日」取自「九二甲寅财动」——那是**动爻**不是验期，
    书上唯一验期在源L581「直待午火官，辰土印绶年可求」，还是**双列**（午或辰）。
抓取器在段落归属失败时标 `section="__trailing__"`，上下文窗口于是串到邻条。
**串档不会被任何现有门发现**，只表现为"外部落分很低"，然后逼人去看引擎——
本门把"基准自身是否自洽"变成红线：基准坏了先修基准，不动引擎去凑分。

    python dev_tools/check_case_selfconsistency.py            # 全量对账
    python dev_tools/check_case_selfconsistency.py --selftest # 负例：串档必须被抓到
    python dev_tools/check_case_selfconsistency.py --verbose  # 看信息性 NOTE

判定口径（为什么这样判，第一版的假红都在这儿）：
  · 只判"案例自己引用了书文片段"的条目（`provenance.context_head` / `wikitext_head` /
    `quote`）；没有自引书文的（classical_cases、yingqi_cases）不计入已验，并报出条数；
    `quote` 是 YIIN 集的书证（日柱行，不含断语），该集只跑日辰/应期两条判据，
    卦名不在日柱行里是常态，不记 NOTE（425 批扩围）。
  · YIIN 另跑「断语逐字」：`expected.detail` 必须是本案书文窗口（日柱行→下一卦表块）
    的逐字子串（427 批）；窗口口径与建器 `build_yiin_cases.case_window` 同源。
  · 卦变自洽（428 批）：本卦 + `moving` 的差集必须等于 `changed`，所有带 `moving`
    列表的案例都查（classical 用 moving_count，不适用）；手工重建后的盘面由此受控。
  · 应期词表（429 批）：`expected.yingqi` 只准空、干支应期、或 `timing.REL_RULES`
    登记的相对窗词；判词（「不安」「难成」）混进应期即红。
  · **判据只用干支，不用整句**：底本多作繁体（大壯／離／粵東帶貨），而片段是抓取时
    把 `<br>` 归一成换行的产物，拿整句回底本找必然假红——本器第一版就是这样
    一口气报出 8 条"片段在底本里找不到"。干支与地支繁简同形，"日辰""应期支"
    两类判据因此是**字符安全**的；
  · 片段里写明日辰而 `input.date` 是另一个日子 → 判红（串档的直接特征）；
  · `expected.yingqi` 的支在片段与断语里都不出现 → 判红（把动爻/别条的字当验期）；
  · 卦名与"片段可定位性" → 只记不判（繁简与标记差异不足以支撑硬约束，如实降级）；
  · 双列验期的正确处置是 expected 置空（评测按 N/A 剔除），不硬选一个当基准。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(DISC / "scripts"))
import build_yiin_cases as YB  # noqa: E402  卦表块/日柱行定位与建器同一口径
from timing import REL_RULES  # noqa: E402  相对窗词表单一真源（不在本器里另抄一份）

CASE_DIR = DISC / "data" / "cases"
YIIN_SRC = DISC / "data" / "sources" / "yiin_dz.dz.txt"
SETS = ("wikisource_cases.json", "huozhulin_cases.json", "yingqi_cases.json",
        "classical_cases.json", "yiin_cases.json")
# 该集的 provenance.quote 只是日柱行（不是整段书文）：①日辰、②应期照判，
# ③卦名不在日柱行里是常态，跳过。
DATE_LINE_SETS = {"yiin_cases.json"}
GZ = "甲乙丙丁戊己庚辛壬癸"
BRS = "子丑寅卯辰巳午未申酉戌亥"
DAY_RE = re.compile(f"[{GZ}][{BRS}]日")
BR_RE = re.compile(f"[{BRS}]")
YQ_TOKEN = re.compile(r"[%s]?[%s]{1,2}(?:年|月|日|时)" % (GZ, BRS))
REL_WORDS = tuple(k for keys, *_ in REL_RULES for k in keys)
NOTE: list[str] = []


def book_text(case: dict) -> str:
    """该案例**自己引用**的书文片段；没有就返回空串（→ 不计入已验）。"""
    pv = case.get("provenance") or {}
    return str(pv.get("context_head") or pv.get("wikitext_head") or pv.get("quote") or "")


def check_case(case: dict, name: str = "") -> tuple[int, list[str]]:
    """返回 (本例命中的判据数, 判红清单)。纯函数：负例可以直接喂构造数据。"""
    frag = book_text(case)
    if not frag:
        return 0, []
    cid = case.get("id", "?")
    problems: list[str] = []
    checked = 1                                   # 有自引书文，本身算一条
    inp = case.get("input") or {}
    cited_days = DAY_RE.findall(frag)
    dm = DAY_RE.search(str(inp.get("date") or ""))

    if dm and cited_days:                         # ① 日辰必须与自引片段一致
        checked += 1
        if len(set(cited_days)) > 1:
            NOTE.append(f"{cid}：自引片段里有 {len(set(cited_days))} 个不同日辰"
                        f"{sorted(set(cited_days))}，出处窗口不唯一——只记不判")
        elif dm.group(0) not in cited_days:
            problems.append(f"{cid}：自引书文片段里写的是「{cited_days[0]}」，"
                            f"而 input.date 是「{dm.group(0)}」——两条占验被拼成一条")

    yq = (case.get("expected") or {}).get("yingqi")
    if yq:                                        # ② 应期支必须出现在片段或断语里
        checked += 1
        brs = BR_RE.findall(str(yq))
        detail = str((case.get("expected") or {}).get("detail") or "")
        # YIIN 的 fragment 是日柱行，本身含年/月/日支；应期支只认断语（detail），
        # 否则月支会冒充应期支（425 批探针实测）。
        hay = detail if name in DATE_LINE_SETS else frag + detail
        if brs and not any(b in hay for b in brs):
            problems.append(f"{cid}：应期「{yq}」的支{brs}在自引片段与断语里都不出现"
                            f"——多半是把动爻或别条的字当成了验期")

    hx = case.get("hexagram") or {}               # ③ 卦名：繁简差异不足以硬判
    if name not in DATE_LINE_SETS:
        for label, nm in (("本卦", str(hx.get("original") or "")),
                          ("变卦", str(hx.get("changed") or ""))):
            if nm and nm not in frag:
                NOTE.append(f"{cid}：{label}「{nm}」未以简体形出现在片段里（底本多繁体，只记不判）")
    return checked, problems


def check_detail_verbatim(case: dict, lines: list[str], blocks: list[tuple[int, int]]) -> list[str]:
    """YIIN：`expected.detail` 必须是本案书文窗口里的逐字子串（427 批）。

    423 的建器写盘前验过引文，但没有常设门——重生成或手改把断语换成别案/凭空句，
    [38] 只数非空、[16] 只查应期支，都发现不了。窗口口径与建器 `case_window` 同源。
    """
    cid = str(case.get("id") or "?")
    pv = case.get("provenance") or {}
    ln = pv.get("line")
    det = str((case.get("expected") or {}).get("detail") or "")
    if not det:
        return [f"{cid}：expected.detail 为空，无可回指的断语"]
    if not ln:
        return [f"{cid}：缺 provenance.line，无法定位书文窗口"]
    win = YB.case_window(lines, blocks, int(ln))
    if not win:
        return [f"{cid}：provenance.line={ln} 定位不到书文窗口"]
    if det not in win:
        return [f"{cid}：expected.detail 不在本案书文窗口里（不是逐字引文）"]
    return []


def check_hexagram_transform(case: dict) -> list[str]:
    """卦变自洽：本卦 + `moving` 的差集必须等于 `changed`（428 批）。

    案例文件里有手工重建的条目（如 HZL001 原 moving=[5] 而 changed=大壮，
    后者需要 5、6 两爻动），构建器的三方校验管不到手改后的盘面。本判据对所有
    带 `moving` 列表的案例生效（classical 用 moving_count，不适用）。
    """
    cid = str(case.get("id") or "?")
    hx = case.get("hexagram") or {}
    orig = str(hx.get("original") or "")
    chg = str(hx.get("changed") or "")
    mov = hx.get("moving")
    if orig not in YB.HEXAGRAM_TRIGRAMS or not isinstance(mov, list):
        return []
    mov = sorted(int(x) for x in mov)
    if not chg:
        return [f"{cid}：有动爻 {mov} 却无变卦名"] if mov else []
    if chg not in YB.HEXAGRAM_TRIGRAMS:
        return [f"{cid}：变卦名「{chg}」不在内核 64 卦表"]
    ol = YB.BAGUA_LINES[YB.HEXAGRAM_TRIGRAMS[orig][1]] + YB.BAGUA_LINES[YB.HEXAGRAM_TRIGRAMS[orig][0]]
    cl = YB.BAGUA_LINES[YB.HEXAGRAM_TRIGRAMS[chg][1]] + YB.BAGUA_LINES[YB.HEXAGRAM_TRIGRAMS[chg][0]]
    diff = [i + 1 for i, (a, b) in enumerate(zip(ol, cl)) if a != b]
    if mov != diff:
        return [f"{cid}：动爻 {mov} ≠ 卦变差集 {diff}（{orig} → {chg}）"]
    return []


def check_yingqi_vocabulary(case: dict) -> list[str]:
    """`expected.yingqi` 必须是空（N/A）、干支应期，或 timing 登记的相对窗词（429 批）。

    判词（「不安」「难成」）混进应期会让该维静默变 N/A，还会被后续相对窗规则误读；
    本判据把「应期」这个词位的取值面钉死。
    """
    cid = str(case.get("id") or "?")
    v = str((case.get("expected") or {}).get("yingqi") or "")
    if not v:
        return []
    if YQ_TOKEN.search(v) or any(k in v for k in REL_WORDS):
        return []
    return [f"{cid}：expected.yingqi「{v}」既非干支应期也非登记相对窗（像是判词误填）"]


def load_sets() -> list[tuple[str, dict]]:
    out: list[tuple[str, dict]] = []
    for name in SETS:
        p = CASE_DIR / name
        if not p.exists():
            NOTE.append(f"{name}：文件不存在，本门未检视该集")
            continue
        for c in (json.loads(p.read_text(encoding="utf-8")).get("cases") or []):
            out.append((name, c))
    return out


def selftest(problems: list[str], examined: int, yiin_lines, yiin_blocks) -> None:
    """负例＝HZL001 校勘**前**的真实状态；正例＝校勘后；再加"无书文不算已验"。"""
    head = ("又问：壬癸动雨要言克日定时取验，何如?曰：如六月甲辰日占雨得乾之大壮，"
            "当日申时雷雨骤至，此壬癸克日定时")

    def mk(day: str) -> dict:
        return {"id": f"NEG_{day}", "input": {"date": day},
                "hexagram": {"original": "乾", "changed": "大壮"},
                "expected": {"yingqi": "申时", "detail": head},
                "provenance": {"context_head": head}}

    if not check_case(mk("癸亥日"))[1]:
        problems.append("负例失效：把日辰换成邻条的「癸亥日」没被判红")
    if check_case(mk("甲辰日"))[1]:
        problems.append("负例假阳性：日辰与自引片段一致的条目也被判红，判据不成立")
    ghost = {"id": "NEG_无书文", "input": {"date": "甲子日"},
             "hexagram": {"original": "乾"}, "expected": {"yingqi": "午日"}}
    if check_case(ghost)[0] != 0:
        problems.append("没有自引书文的条目被算成了已检视")

    # 425 批：YIIN 的 quote 只是日柱行——应期支仍须在 quote+detail 里；
    # 该集跳过卦名 NOTE（日柱行不含卦名是常态）。
    yq_head = "庚寅年己卯月丁亥日，占求财，得谦之小过。"

    def mk_yiin(yq: str, detail: str) -> dict:
        return {"id": "NEG_YIIN", "input": {"date": "庚寅年己卯月丁亥日"},
                "hexagram": {"original": "谦", "changed": "小过"},
                "expected": {"yingqi": yq, "detail": detail},
                "provenance": {"quote": yq_head}}

    if not check_case(mk_yiin("甲子日", "后至乙丑日，果得财也"), "yiin_cases.json")[1]:
        problems.append("负例失效：YIIN 应期支不在 quote/detail 里没被判红")
    if check_case(mk_yiin("辛卯日", "后至辛卯日，财值巳辰，果得财也"),
                  "yiin_cases.json")[1]:
        problems.append("负例假阳性：YIIN 应期支在 detail 里却被判红")
    note0 = len(NOTE)
    check_case(mk_yiin("辛卯日", "后至辛卯日，财值巳辰，果得财也"), "yiin_cases.json")
    if len(NOTE) != note0:
        problems.append("YIIN 日柱片段被误判为卦名缺失（③ 未跳过）")

    # 427 批：YIIN 的 expected.detail 必须是本案书文窗口的逐字子串
    if yiin_lines and yiin_blocks:
        ln = yiin_blocks[0][0] + 1
        win = YB.case_window(yiin_lines, yiin_blocks, ln)
        if win:
            pos = {"id": "POS_YIIN_DETAIL", "provenance": {"line": ln},
                   "expected": {"detail": win[:20]}}
            if check_detail_verbatim(pos, yiin_lines, yiin_blocks):
                problems.append("YIIN detail 正例被误伤")
            neg = {"id": "NEG_YIIN_DETAIL", "provenance": {"line": ln},
                   "expected": {"detail": "本书没有这句话"}}
            if not check_detail_verbatim(neg, yiin_lines, yiin_blocks):
                problems.append("负例失效：YIIN detail 不在本案窗口没被判红")
            empty = {"id": "NEG_YIIN_EMPTY", "provenance": {"line": ln},
                     "expected": {"detail": ""}}
            if not check_detail_verbatim(empty, yiin_lines, yiin_blocks):
                problems.append("负例失效：YIIN detail 为空没被判红")
        else:
            problems.append("YIIN 窗口为空，detail 负例无从构造")

    # 428 批：卦变自洽——本卦+moving 的差集必须等于 changed
    def hx(orig: str, chg: str, mov: list[int]) -> dict:
        return {"id": "HX_PROBE", "hexagram": {"original": orig, "changed": chg,
                                                "moving": mov}}

    if check_hexagram_transform(hx("乾", "大壮", [5, 6])):
        problems.append("卦变自洽正例被误伤")
    if not check_hexagram_transform(hx("乾", "大壮", [5])):
        problems.append("负例失效：乾→大壮 动爻[5] 未判红")
    if not check_hexagram_transform(hx("乾", "", [5])):
        problems.append("负例失效：有动无变未判红")

    # 429 批：应期词表——判词不得混进 expected.yingqi
    def yq(v: str) -> dict:
        return {"id": "YQ_PROBE", "expected": {"yingqi": v}}

    if check_yingqi_vocabulary(yq("癸卯日")):
        problems.append("应期词表正例（癸卯日）被误伤")
    if check_yingqi_vocabulary(yq("次日")):
        problems.append("应期词表正例（相对窗「次日」）被误伤")
    if not check_yingqi_vocabulary(yq("不安")):
        problems.append("负例失效：判词「不安」混进应期未判红")
    if examined == 0:
        problems.append("全量 0 条被检视，本门等于没跑")
    print("  [selftest] 负例已跑（串档 / 一致 / 无书文 / YIIN 日柱片段 / YIIN 断语逐字 / 卦变自洽 / 应期词表 七件）")


def main() -> int:
    ap = argparse.ArgumentParser(description="案例库 日辰/应期 与自引书文的同源自洽门")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verbose", action="store_true", help="打印信息性 NOTE")
    args = ap.parse_args()

    problems: list[str] = []
    examined = skipped = 0
    yiin_lines = yiin_blocks = None
    if YIIN_SRC.exists():
        yiin_lines = YIIN_SRC.read_text(encoding="utf-8", errors="replace").splitlines()
        yiin_blocks = YB.split_blocks(yiin_lines)
    for name, c in load_sets():
        n, ps = check_case(c, name)
        ps = ps + check_hexagram_transform(c)
        ps = ps + check_yingqi_vocabulary(c)
        if name == "yiin_cases.json" and yiin_lines is not None:
            ps = ps + check_detail_verbatim(c, yiin_lines, yiin_blocks)
        examined += 1 if n else 0
        skipped += 0 if n else 1
        problems.extend(f"[{name}] {x}" for x in ps)
    print(f"  对账：{examined} 例有自引书文可判，{skipped} 例无书文（不计入已验）")
    if args.selftest:
        selftest(problems, examined, yiin_lines, yiin_blocks)
    if args.verbose:
        for x in NOTE[:20]:
            print(f"  · {x}")
    elif NOTE:
        print(f"  · 另有 {len(NOTE)} 条信息性提示（卦名繁简/片段多日辰等），--verbose 查看")
    for p in problems:
        print(f"  × {p}")
    if examined == 0:
        print("× 0 例可检视——本门等于没跑，不判通过")
        return 1
    if not problems:
        print("  √ 各例的日辰与应期支均出自其自引书文（基准自洽）")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
