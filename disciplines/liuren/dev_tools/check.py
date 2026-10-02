# -*- coding: utf-8 -*-
"""大六壬·质量门：契约文件 + 四段冒烟 + 九宗门全枚举守门 + 引文逐字门 + 金标准。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parents[1]
CORE = ROOT / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.gate_kit import run_step as _run_step  # noqa: E402

_CN = re.compile(r"[\u4e00-\u9fff]")


def _hanzi(s: str) -> str:
    return "".join(_CN.findall(s))

from yishu_core.ganzhi_calendar import EARTHLY_BRANCHES  # noqa: E402
from yishu_core.symbols import xunkong_of  # noqa: E402

from jiuzongmen import (  # noqa: E402
    MEN_ORDER,
    classify_tianpan,
    san_chuan_full,
)
from analyze import _richen  # noqa: E402
from kemu import IMPLEMENTED as KEMU_IMPLEMENTED  # noqa: E402
from yishu_core.liuren_tables import TIAN_JIANG_ORDER, tianjiang_layout  # noqa: E402

# 判据名单（日辰关系标签）唯一真值源：data/verdicts.json#richen
_VERDICTS_FOR_GATE = json.loads(
    (DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、300s 超时、argv 前补解释器（实现在内核 gate_kit）。"""
    return _run_step(cmd, cwd=DISC, timeout=300, python=True)


def build_tianpan(jiang: str, hour: str) -> dict[str, str]:
    ji = EARTHLY_BRANCHES.index(jiang)
    hi = EARTHLY_BRANCHES.index(hour)
    return {g: EARTHLY_BRANCHES[(ji - hi + i) % 12] for i, g in enumerate(EARTHLY_BRANCHES)}


def enumerate_gate() -> tuple[list[str], dict]:
    """六十甲子 × 12 时辰（月将固定一支）的全枚举守门断言；例数由循环实算。

    月将×时辰只以「月将−时」的差值进判据，故固定月将取遍 12 时辰已覆盖全部相对关系，
    无需再乘 12 月将（另 12 倍是同一批构型）。"""
    fails: list[str] = []
    from yishu_core.ganzhi_calendar import ganzhi_pair

    # 六十甲子：与 core ganzhi_calendar 的 %60 同口径（不另立表）
    days = [ganzhi_pair(i) for i in range(60)]
    stats: dict[str, int] = {}
    bieze_days: dict[str, int] = {}
    bazhuan_days: dict[str, int] = {}
    fuyin = fanyin = jinglanshe = 0
    kemu_counts: dict[str, int] = {}
    richen_counts: dict[str, int] = {}
    n_cases = 0
    # 中末传沿天盘连传的四门（其余五门各有特法）——名单须落在 MEN_ORDER 内
    chain_mens = {"贼克", "比用", "涉害", "遥克"}
    assert chain_mens <= set(MEN_ORDER), "链式取用门不在 MEN_ORDER 内"
    for day in days:
        # 月将固定取「子」作代表：delta = 月将-时辰 随 12 时辰取遍 0..11，
        # 门类结构只依赖 (日, delta)，与月将取哪个支无关
        for hour in EARTHLY_BRANCHES:
            tianpan = build_tianpan("子", hour)
            n_cases += 1
            res = san_chuan_full(day[0], day[1], tianpan)
            men = res["men"]
            if men not in MEN_ORDER:
                fails.append(f"{day}{hour}：门类 {men} 越界")
            stats[men] = stats.get(men, 0) + 1
            chuan = res["san_chuan"]
            if len(chuan) != 3 or any(b not in EARTHLY_BRANCHES for b in chuan):
                fails.append(f"{day}{hour}：三传非法 {chuan}")
            if men in chain_mens:
                if chuan[1] != tianpan[chuan[0]] or chuan[2] != tianpan[chuan[1]]:
                    fails.append(f"{day}{hour}：中末链断裂 {chuan}")
            kind = classify_tianpan(day[0], day[1], tianpan)
            if kind == "伏吟":
                fuyin += 1
            elif kind == "返吟":
                fanyin += 1
                if res["ke_name"] == "井栏射":
                    jinglanshe += 1
            if men == "别责":
                bieze_days[day] = bieze_days.get(day, 0) + 1
            if men == "八专":
                bazhuan_days[day] = bazhuan_days.get(day, 0) + 1
            from kemu import recognize as _kemu_rec
            chart_like = {
                "moment": {"day_ganzhi": day, "hour_branch": hour,
                           "xunkong": xunkong_of(day)},
                "san_chuan": res["san_chuan"],
                "tianpan": tianpan,
                "men": res["men"],
                "ke_name": res["ke_name"],
            }
            for h in _kemu_rec(chart_like):
                kemu_counts[h["name"]] = kemu_counts.get(h["name"], 0) + 1
            for r in _richen(chart_like, _VERDICTS_FOR_GATE):
                richen_counts[r["name"]] = richen_counts.get(r["name"], 0) + 1
    # 诀文锚定断言（《六壬大全·入手法》逐字，每日 12 课口径）
    if fuyin != len(days):
        fails.append(f"伏吟数 {fuyin} ≠ 六十甲子数 {len(days)}（诀：伏吟每旦各一课）")
    if fanyin != len(days):
        fails.append(f"返吟数 {fanyin} ≠ 六十甲子数 {len(days)}")
    if jinglanshe != 6:
        fails.append(f"井栏射 {jinglanshe} ≠ 6（诀：六日该无克，丑未同干丁己辛）")
    expect_bieze = {"戊辰": 1, "戊午": 1, "丙辰": 1, "辛未": 2, "辛丑": 2, "丁酉": 1, "辛酉": 1}
    if bieze_days != expect_bieze:
        fails.append(f"别责课分布 {bieze_days} ≠ 诀注（刚三柔六共九课：{expect_bieze}）")
    expect_bazhuan_days = {"甲寅", "庚申", "丁未", "己未", "癸丑"}
    if set(bazhuan_days) != expect_bazhuan_days:
        fails.append(f"八专日 {sorted(bazhuan_days)} ≠ 五日（两课无克号八专）")
    if stats.get("昴星", 0) <= 0 or stats.get("遥克", 0) <= 0 or stats.get("涉害", 0) <= 0:
        fails.append(f"九宗门覆盖不全：{stats}")
    # 课目识别守门：IMPLEMENTED 里每条判据必须在全枚举课式中至少触发一次。
    # 60 日 × 12 时辰（月将固定一支）已穷尽六壬天地盘的相对关系，
    # 故「零触发」只可能是判据写错或枚举不全，不是样本不够。
    for name in KEMU_IMPLEMENTED:
        if kemu_counts.get(name, 0) <= 0:
            fails.append(f"课目「{name}」{n_cases} 课式零触发——判据或枚举有误")
    # 日辰关系守门（卷三「日辰」歌）：判据名单取 verdicts.json#richen（唯一真值源），
    # 每条判据同样必须在全枚举中至少触发一次——零触发即判据写错或枚举不全。
    for name in ((_VERDICTS_FOR_GATE.get("richen") or {})):
        if name.startswith("_") or name == "出处":
            continue
        if richen_counts.get(name, 0) <= 0:
            fails.append(f"日辰关系「{name}」{n_cases} 课式零触发——判据或枚举有误")
    return fails, stats, kemu_counts, n_cases


def _nospace(s: str) -> str:
    """去所有空白（含换行），**保留标点与书名号**——逐字断言用。

    与 _hanzi() 的区别是本门的关键：_hanzi 只留汉字，会把「《玉厯》」的书名号、
    「，」的句读一并滤掉，故「去夹注/去书名号」在 _hanzi 口径下不可见（漏检来源）。
    """
    return "".join(s.split())


def _cn_num(n: int) -> str:
    """1..99 的本书序数写法：十/二十/三十…（整十），二一/二二/五九（非整十，十位不带「十」）。

    仅用于把实算缺号转成人可读的汉字（如 58 → 五八）；不作任何取数用途。
    """
    if n <= 10:
        return "一二三四五六七八九十"[n - 1]
    if n < 20:
        return "十" + "一二三四五六七八九"[n - 11]
    tens, ones = divmod(n, 10)
    if ones == 0:
        return "一二三四五六七八九"[tens - 1] + "十"
    return "一二三四五六七八九"[tens - 1] + "一二三四五六七八九"[ones - 1]


# 书源卷一「课目」段**自编号缺号**登记：该段用序数 一…六五 逐条编号，实测缺第 58 条
# （五八）——如实登记，不臆补、不造诀文。若将来重抓后缺号集与登记不符（补全或新增缺号），
# 门 [1c] 立即判败，强制重新核对语料条数（防「书源已变而数据仍按旧差 1」静默漂移）。
KEMU_NUMBERING_GAP: tuple[int, ...] = (58,)


def kemu_section_parse() -> dict:
    """解析书源卷一「课目」段：返回 {n_lines, numbers, missing, bad_lines}。

    段落结构：段名一行 + 每课一行（「…诀文<序数><卦名>[ 附注]」）。按**自编号逐行进位**
    解析（容忍跳号，从而暴露缺号），故实收条数、自编号跨度、缺号三者出自同一次解析。
    """
    src1 = (ROOT / "data" / "sources"
            / "liu-ren-da-quan.wikitext.txt").read_text(encoding="utf-8")
    i = src1.index("课目")
    seg = src1[i:src1.index("补论", i)]
    lines = [x.strip() for x in seg.splitlines() if x.strip()][1:]
    numbers: list[int] = []
    bad_lines: list[int] = []
    expected = 1
    for k, x in enumerate(lines, 1):
        tail = x[-18:]
        hit = next((c for c in range(expected, min(expected + 4, 100))
                    if _cn_num(c) in tail), None)
        if hit is None:
            bad_lines.append(k)
            continue
        numbers.append(hit)
        expected = hit + 1
    missing = ([n for n in range(numbers[0], numbers[-1] + 1) if n not in numbers]
               if numbers else [])
    return {"n_lines": len(lines), "numbers": numbers,
            "missing": missing, "bad_lines": bad_lines}


def book_kemu_count() -> int:
    """书源卷一「课目」段**实收**课目条数（唯一权威源，别处不得另写数字）。

    条数取自 `kemu_section_parse()` 的同一次解析（不另按行数估算）。该段自编号为
    一…六五，但缺第 58 条（见 `KEMU_NUMBERING_GAP`），故实收 = 跨度 − 缺号数。
    门 [1c] 以它为准比对 data/kemu.json 的条数；语料一变，门即报出实算差异。
    """
    p = kemu_section_parse()
    return len(p["numbers"])


def verbatim_inventory(verdicts: dict | None = None) -> dict:
    """全例外置引文的逐字清单（**唯一计算处**：门 [1d] 与本目录订正器共用）。

    返回 {items, n_verdicts, n_kemu, non_verbatim, registered, stale}，
    条数一律实算，不落任何常量——语料增长后各处只引用本函数的输出。
    `verdicts` 传入时用它替代磁盘上的 data/verdicts.json（供订正器落盘前自检）。
    """
    vd = verdicts if verdicts is not None else json.loads(
        (DISC / "data" / "verdicts.json").read_text(encoding="utf-8"))
    src_paths = sorted((ROOT / "data" / "sources").glob("liu-ren-da-quan*.wikitext.txt"))
    texts = {p.name: p.read_text(encoding="utf-8") for p in src_paths}
    whole = _nospace("".join(texts.values()))
    src1 = texts.get("liu-ren-da-quan.wikitext.txt", "")
    kemu_seg = _nospace(src1[src1.index("课目"):src1.index("补论")]) if (
        "课目" in src1 and "补论" in src1) else ""
    juan_blob = _nospace("".join(texts.get(f"liu-ren-da-quan-juan{n}.wikitext.txt", "")
                                for n in (7, 8, 9, 10)))

    men = vd.get("men") or {}
    tj = vd.get("tianjiang") or {}
    items = [(f"men.{n}.basis", e["basis"], whole) for n, e in men.items()
             if (e or {}).get("basis")]
    items += [(f"tianjiang.{n}.verse", e["verse"], whole) for n, e in tj.items()
              if isinstance(e, dict) and e.get("verse")]
    # 日辰关系（卷三「日辰」歌）诀文——同样逐字对全文核验
    items += [(f"richen.{n}.句", e["句"], whole) for n, e in (vd.get("richen") or {}).items()
              if isinstance(e, dict) and e.get("句")]
    n_verdicts = len(items)

    kemu = json.loads((DISC / "data" / "kemu.json").read_text(encoding="utf-8"))
    entries = kemu.get("entries") or []
    items += [(f"kemu.{e['name']}.verse", e["verse"], kemu_seg) for e in entries
              if e.get("verse")]
    items += [(f"kemu.{e['name']}.note", e["note"], juan_blob) for e in entries
              if e.get("note")]

    policy = vd.get("verbatim_policy")
    registered = {e.get("key"): e for e in ((policy or {}).get("normalized") or [])
                  if isinstance(e, dict)}
    non_verbatim = [k for k, t, c in items if not (c and _nospace(t) in c)]
    # 期望条数实算：门数（MEN_ORDER）+ 天将数（core TIAN_JIANG_ORDER）+ 日辰关系条数
    # （verdicts.json#richen 的标签数，唯一真值源在数据侧，不在此另抄名单）
    n_expected = len(MEN_ORDER) + len(TIAN_JIANG_ORDER) + len(
        [k for k, e in (vd.get("richen") or {}).items()
         if isinstance(e, dict) and e.get("句")])
    return {
        "items": items,
        "n_verdicts": n_verdicts,
        "n_kemu": len(items) - n_verdicts,
        "n_expected_verdicts": n_expected,
        "non_verbatim": non_verbatim,
        "registered": registered,
        "stale": sorted(set(registered) - set(non_verbatim)),
        "men_keys": list(men),
        "no_basis": [n for n, e in men.items() if not (e or {}).get("basis")],
    }


def check_verbatim() -> tuple[list[str], str]:
    """[1d] 引文逐字门：本科全部外置引文须为书源去空白后的**逐字子串**（字符级）。

    覆盖 verdicts（men[*].basis、tianjiang[*].verse）与 kemu（课目 verse、课目 note）
    全部引文；条数由 verbatim_inventory() 实算，本门不写死任何条数。
    期望条数亦实算：门数取 `jiuzongmen.MEN_ORDER`、天将数取 core `TIAN_JIANG_ORDER`
    （不另抄一份名单/条数）；课目 verse 对卷一「课目」段，课目 note 对卷七~十「课经集」。
    允许归化（去夹注/去书名号/正字），但**必须**登记在 verdicts.json#verbatim_policy.normalized
    （每条带 rule + reason），否则判败；登记与实际不符（含陈旧登记）同样判败——
    防「声称逐字而实际归化」的口径不实，也防登记表腐烂。
    本门用字符级口径（保留标点与书名号），与 [1c] 的「只留汉字」口径互补。
    """
    fails: list[str] = []
    if not sorted((ROOT / "data" / "sources").glob("liu-ren-da-quan*.wikitext.txt")):
        return [f"找不到六壬书源：{ROOT / 'data' / 'sources'}"], "书源缺失"
    if not isinstance(json.loads((DISC / "data" / "verdicts.json")
                                 .read_text(encoding="utf-8")).get("verbatim_policy"), dict):
        return ["verdicts.json 缺 verbatim_policy 登记块"], "无登记块"

    inv = verbatim_inventory()
    if inv["no_basis"]:
        fails.append(f"门类诀文缺 basis：{inv['no_basis']}")
    if set(inv["men_keys"]) != set(MEN_ORDER):
        fails.append(f"verdicts 门类键 {sorted(inv['men_keys'])} ≠ MEN_ORDER "
                     f"{sorted(MEN_ORDER)}（名单应只有一份）")
    if inv["n_verdicts"] != inv["n_expected_verdicts"]:
        fails.append(f"verdicts 引文 {inv['n_verdicts']} 条 ≠ MEN_ORDER+TIAN_JIANG_ORDER "
                     f"= {inv['n_expected_verdicts']} 条（防静默缩水）")
    for key in inv["non_verbatim"]:
        ent = inv["registered"].get(key)
        if ent is None:
            fails.append(f"引文非逐字且未登记归化：{key}")
        elif not (ent.get("rule") and ent.get("reason")):
            fails.append(f"归化登记缺 rule/reason：{key}")
    if inv["stale"]:
        fails.append(f"归化登记与实测不符（已逐字却仍登记）：{inv['stale']}")

    n_reg = len(set(inv["registered"]) & set(inv["non_verbatim"]))
    detail = (f"{len(inv['items'])} 条（verdicts {inv['n_verdicts']} + 课目 {inv['n_kemu']}）"
              f"去空白后逐字命中书源；非逐字 {len(inv['non_verbatim'])} 条"
              + (f"（其中已登记归化 {n_reg} 条）：{'、'.join(inv['non_verbatim'])}"
                 if inv["non_verbatim"] else "（归化登记表为空）"))
    return fails, detail


def main() -> int:
    fails: list[str] = []

    required = ["SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                "scripts/narrate.py", "scripts/render.py",
                "scripts/jiuzongmen.py", "data/verdicts.json",
                "dev_tools/check.py", "dev_tools/golden.py"]
    missing = [r for r in required if not (DISC / r).exists()]
    if missing:
        fails.append(f"缺 {missing}")
    print("[0] 契约文件", "√" if not missing else "×")

    fails2, stats, kemu_counts, n_cases = enumerate_gate()
    if fails2:
        fails.extend(fails2)
        print("[1] 九宗门全枚举守门 ×", *fails2[:6], sep="\n    ")
    else:
        print(f"[1] 九宗门全枚举守门 √ {n_cases} 例"
              f"（{n_cases // len(EARTHLY_BRANCHES)} 日×{len(EARTHLY_BRANCHES)} 时辰）"
              f"门类分布 {stats}; 课目触发 {kemu_counts}")

    # 骨架完整度不变式（SYS-REVIEW #9）：天将布法=十二将全排列、乘临/遁干字段合法、
    # 十二天将歌诀在 verdicts 全覆盖——防「骨架」旁路支线静默腐烂。
    try:
        sys.path.insert(0, str(DISC / "scripts"))
        from chart import chart as _chart
        from yishu_core.liuren_tables import TIAN_JIANG_ORDER
        from yishu_core.symbols import HEAVENLY_STEMS
        c0 = _chart("2024-02-20 10:30", "占求财")
        layout = c0.get("tianjiang_layout") or {}
        if sorted(layout.values()) != sorted(TIAN_JIANG_ORDER):
            fails.append(f"天将布法非十二将全排列：{sorted(layout.values())}")
        for _pair in c0.get("chuan_tianjiang") or []:
            if _pair.get("jiang") not in TIAN_JIANG_ORDER:
                fails.append(f"乘临字段非法：{_pair.get('jiang')}")
                break
        dg0 = c0.get("dun_gan") or []
        if len(dg0) != 3 or any(x not in HEAVENLY_STEMS for x in dg0):
            fails.append(f"遁干字段非法：{dg0}")
        tj_verdicts = json.loads((DISC / "data" / "verdicts.json")
                                 .read_text(encoding="utf-8")).get("tianjiang") or {}
        missing_tj = [t for t in TIAN_JIANG_ORDER
                      if not (tj_verdicts.get(t) or {}).get("verse")]
        if missing_tj:
            fails.append(f"天将歌诀缺乘临诀文：{missing_tj}")
        print("[1b] 骨架完整度（布法排列/乘临字段/诀文覆盖）"
              + ("√" if not any("布法" in f or "乘临" in f or "遁干" in f or "歌诀" in f for f in fails) else "×"))
    except Exception as exc:
        fails.append(f"骨架完整度自检异常：{type(exc).__name__}: {exc}")
        print("[1b] 骨架完整度 ×")

    # [1c] 课目引文可回指门（铁律三）：verse 逐字在卷一「课目」歌诀段，
    # note 逐字在卷七~卷十「课经集」——防「自洽但无出处」的生成文本混入。
    try:
        kemu_json = json.loads((DISC / "data" / "kemu.json").read_text(encoding="utf-8"))
        entries = kemu_json.get("entries") or []
        src1 = (ROOT / "data" / "sources"
                / "liu-ren-da-quan.wikitext.txt").read_text(encoding="utf-8")
        seg1 = _hanzi(src1[src1.index("课目"):src1.index("补论")])
        blob = "".join(
            _hanzi((ROOT / "data" / "sources"
                    / f"liu-ren-da-quan-juan{n}.wikitext.txt").read_text(encoding="utf-8"))
            for n in (7, 8, 9, 10))
        bad_v = [e["name"] for e in entries
                 if _hanzi(e.get("verse") or "") not in seg1]
        bad_n = [e["name"] for e in entries
                 if (e.get("note") or "") and _hanzi(e["note"]) not in blob]
        no_note = [e["name"] for e in entries if not e.get("note")]
        n_impl = sum(1 for e in entries if e.get("implemented"))
        extra = sorted(set(KEMU_IMPLEMENTED) - {e["name"] for e in entries})
        gate_fail = []
        if bad_v:
            gate_fail.append(f"课目诀文不可回指卷一歌诀：{bad_v}")
        if bad_n:
            gate_fail.append(f"课经释义不可回指课经集：{bad_n}")
        if len(entries) != book_kemu_count():
            gate_fail.append(f"课目表 {len(entries)} 条 ≠ 书源卷一「课目」段实算 "
                             f"{book_kemu_count()} 条")
        sec = kemu_section_parse()
        if sec["bad_lines"]:
            gate_fail.append(f"书源「课目」段有未按序行（第 {sec['bad_lines']} 行）"
                             "——解析规则或源文格式已变，须重新核对")
        elif sec["missing"] != sorted(KEMU_NUMBERING_GAP):
            gate_fail.append(
                f"书源「课目」段缺号 {[_cn_num(n) for n in sec['missing']]} "
                f"≠ 登记 {[_cn_num(n) for n in KEMU_NUMBERING_GAP]}"
                "（补全或新增缺号须重新核对语料条数与 [1c] 期望）")
        if extra:
            gate_fail.append(f"IMPLEMENTED 含表外课名：{extra}")
        fails.extend(gate_fail)
        mark = "×" if gate_fail else "√"
        _sec = kemu_section_parse()
        _gap = "、".join(_cn_num(n) for n in _sec["missing"]) or "无"
        print(f"[1c] 课目引文可回指 {mark} {len(entries)} 条"
              f"（书源段实收 {book_kemu_count()} 条，自编号缺号：{_gap}）"
              f"（课经释义 {len(entries) - len(no_note)} 条"
              + (f"，无释义：{'、'.join(no_note)}" if no_note else "")
              + f"）｜已落判据 {n_impl} 条")
    except Exception as exc:
        fails.append(f"课目引文可回指门异常：{type(exc).__name__}: {exc}")
        print("[1c] 课目引文可回指 ×")

    # [1d] 引文逐字门（字符级，保留标点与书名号）：防「声称逐字而实际去夹注/去书名号」。
    try:
        v_fails, v_detail = check_verbatim()
        fails.extend(v_fails)
        print("[1d] 引文逐字门 " + ("×" if v_fails else "√") + " " + v_detail)
    except Exception as exc:
        fails.append(f"引文逐字门异常：{type(exc).__name__}: {exc}")
        print("[1d] 引文逐字门 ×")

    code, out = run(["scripts/chart.py", "--datetime", "2024-02-20 10:30",
                     "--question", "占求财", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out[-800:])
    else:
        print("[2] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out[-800:])
    else:
        print("[3] analyze 冒烟 √")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是吉凶断语" not in out:
        fails.append("narrate 应声明非吉凶断语")
        print(out[-800:])
    else:
        print("[4] narrate 口径声明 √")

    code, out = run(["scripts/render.py", "scratch/analyze.json", "-o", "scratch/report.md"])
    if code != 0 or not (DISC / "scratch" / "report.md").exists():
        fails.append("render 冒烟失败")
        print(out[-800:])
    else:
        print("[5] render 冒烟 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out[-800:])
    else:
        print("[6] 金标准 √", out.strip())

    if fails:
        print("\n质量门未通过：", *fails, sep="\n  · ")
        return 1
    print("\n大六壬质量门全部通过。")
    print("口径：本课输出为机械结构标签，非吉凶断语；一切分数是古籍案例对齐分，"
          "不是现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
