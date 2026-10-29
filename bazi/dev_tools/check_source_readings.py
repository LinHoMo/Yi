# -*- coding: utf-8 -*-
"""八字参考文档「源L<行号> + 引文」的逐字回验器。

为什么需要它（2026-10-10）：`references/bazi_nayin_shiyi.md` 与
`references/bazi_yue_shi_ge.md` 都写着「引文可逐字回验：
`python tools/check_source_readings.py --doc docs/source-readings/…`」，
但 `tools/` 与 `docs/source-readings/` 已随仓库扁平化删除——照声明去跑必然失败，
而这些行号引文此后**再没有任何东西校验过**。本器按现有结构重建该能力：

    python dev_tools/check_source_readings.py            # 全部参考文档
    python dev_tools/check_source_readings.py --doc references/bazi_yue_shi_ge.md
    python dev_tools/check_source_readings.py --selftest  # 负例：证明本器抓得住错引

判定口径（SKILL.md 铁律：宁可显式说"没查到"，也不给假绿）：
  · 引文 ≥ SHORT_OK 字且归一化后在**所指行或相邻行**出现 → PASS
  · 引文 ≥ FAIL_MIN 字且明确不在所指行邻域 → MISMATCH（判红）
  · 介于其间/该处无引文可查 → NOTE（只报不判红，规则未核全时不冒充硬约束）
  · 某文档一条都验不了 → 显式 0 条自报，绝不当通过
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
REF_DIR = DISC / "references"
SRC_DIR = DISC / "data" / "sources"

LINE_REF = re.compile(r"源\s*L\s*(\d+)")

def _source_titles() -> dict:
    """底本文件名 → 书名（取 provenance 的 title 字段）。用于判「锚点属于哪本书」。"""
    m = {}
    for pf in SRC_DIR.glob("*.provenance.json"):
        try:
            title = json.loads(pf.read_text(encoding="utf-8")).get("title") or ""
        except Exception:
            continue
        if title:
            m[title] = pf.name.replace(".provenance.json", ".dz.txt")
    return m


# 书名归一（第三百一十七批）：provenance 的 title 有繁有简（滴天髓闡微／增刪卜易），
# 而文档正文写简体是常态。不归一的话，《滴天髓阐微》查不到 → 锚点回落主底本 →
# 一条逐字正确的引文被判成"引文与底本不符"。只归一书名用字，不动正文。
_TITLE_FOLD = str.maketrans({
    "闡": "阐", "刪": "删", "淵": "渊", "黃": "黄", "峯": "峰",
    "羣": "群", "裏": "里", "啓": "启", "寜": "宁", "蔵": "藏",
})


def _fold_title(s: str) -> str:
    return "".join(s.split()).translate(_TITLE_FOLD)


def _anchor_owner(pos: int, ln: str, titles: dict, declared: set[str],
                  home_file: str) -> tuple[str, bool]:
    """锚点归哪一本底本：返回 (底本文件名, 是否属于未声明底本)。

    第三百一十七批前，本器只认文档头声明的**一个**底本：锚点左边的《书名》若指向
    另一本书，整条锚被剔除并记「跨书锚点，按底本无从回验」——于是多书合写的读法
    文档（六亲、疾病这类天然跨书的题目）一半引文落在门的盲区里，NOTE 还把盲区
    说成"已尽力"。现在文档可用 `附底本：data/sources/….dz.txt` 显式声明多本，
    锚点按最近的《书名》绑到对应底本，逐字回验照跑；未声明的书仍只记不判
    （宁可显式说"没核"，不给假绿）。
    """
    tail = ln[max(0, pos - 16):pos]
    ms = re.findall(r"《([^》]{2,12})》", tail)
    if not ms:
        return home_file, False
    f = titles.get(_fold_title(ms[-1]))
    if not f:
        return home_file, False
    if f in declared:
        return f, False
    return home_file, True


# 范围式（「源 L261-L292」）与回指式（「引文在源L180 处本身截断」）都不是逐字声明：
# 前者应验"引文落在该区间内"，后者只是指回上一条 already-checked 的引文。
RANGE_REF = re.compile(r"源\s*L\s*\d+\s*[-–—~]\s*(?:L\s*)?\d+")
BACK_REF = re.compile(r"在源\s*L\s*\d+|上一条|前文|本条")
QUOTE_BACKTICK = re.compile(r"`([^`]{6,400})`")
QUOTE_CORNER = re.compile(r"「([^」]{6,200})」")
SOURCE_DECL = re.compile(r"data/sources/([\w\-\.]+\.dz\.txt)")

# 归一化：去空白，统一中西标点和已知繁简/异体对照（两桶对称施加）
_DROP = re.compile(r"[\s，。、；：「」『』“”\"'‘’（）()\[\]【》《〈〉·．\-—_<>=|]+")
_VARIANT = str.maketrans({
    "剋": "克", "峯": "峰", "粧": "妆", "裏": "里", "羣": "群",
    "徧": "遍", "啓": "启", "寜": "宁", "蔵": "藏", "亰": "京",
})

FAIL_MIN = 14      # 只有足够长的引文才有资格判红
SHORT_OK = 6
CJK = re.compile(r"[㐀-鿿一-龥]")


def norm(s: str) -> str:
    return _DROP.sub("", s).translate(_VARIANT)


def _is_classical_quote(q: str) -> bool:
    """只把「以汉字为主的引文」当作书证来验。

    参考文档里有大量反引号代码标识符（`symbols.NAYIN_TO_ELEMENT`、
    `ganzhi_calendar`、`h_stem_idx = (RAT_HOUR_STEM[day_stem] …`），
    把它们当古籍引文去比对底本，必然报出一堆假红——回验器一旦假红，
    整个门就失去可信度（也逼人把门拆掉）。
    """
    n = norm(q)
    if len(n) < SHORT_OK:
        return False
    return len(CJK.findall(n)) * 10 >= len(n) * 7  # ≥70% 汉字


def _same_line_quotes(txt: str) -> list[str]:
    """取**同一行**内的书证引文（先反引号整段，再「」），代码串已剔除。"""
    out: list[str] = []
    for pat in (QUOTE_BACKTICK, QUOTE_CORNER):
        for m in pat.finditer(txt):
            q = m.group(1).strip()
            if _is_classical_quote(q) and not LINE_REF.search(q):
                out.append(q)
    return out


def _line_pairs(ln: str, home_title: str = "", titles=None,
                declared: set[str] | None = None,
                home_file: str = "") -> tuple[list[tuple[str, int, str]], list[tuple[str, int, int]], int]:
    """本行的 **（底本, 锚行号, 该锚自己的引文）** 与 **没有引文的锚**。

    旧实现根本不做绑定：它取「本行最长的一条引文」去配本行**所有**锚
    （`for m in LINE_REF.finditer(ln): q = max(quotes, key=len)`）。
    于是一行多锚的写法 `源 L265／L267／L269／L299／L301 五句歌诀 + 源L303「戊癸何方发，壬子是真途。」`
    会把只属于 303 的引文也算到 265 账上，报出「源L265：短引文未命中」——
    实测该句在 `mingli_tanyuan_dz.dz.txt` L303 邻域命中、在 265 邻域不命中，
    而文档从未声明 265 上有这句。**门自己造出一条声明再把它判为可疑**，
    比漏检更坏：它教人去改本来正确的引文。绑法与六爻科同：
    距离最小者优先，同距取左锚（引文紧跟的那条）。

    第三百一十七批：锚点带底本归属（多底本文档），单底本文档 `declared`
    只有一本时与旧行为逐字等价。
    """
    refs = [(m.start(), int(m.group(1)), m.end()) for m in LINE_REF.finditer(ln)]
    _titles = titles or {}
    _declared = declared or {home_file}
    owned: list[tuple[int, int, int, str]] = []
    foreign = 0
    for pos, n, end in refs:
        f, is_foreign = _anchor_owner(pos, ln, _titles, _declared, home_file or "")
        if is_foreign:
            foreign += 1
        else:
            owned.append((pos, n, end, f))
    rng = [(m.start(), m.end()) for m in RANGE_REF.finditer(ln)]
    quotes = []
    for pat in (QUOTE_CORNER, QUOTE_BACKTICK):
        for m in pat.finditer(ln):
            q = m.group(1).strip()
            if _is_classical_quote(q) and not LINE_REF.search(q):
                quotes.append((m.start(), q))
    pairs: list[tuple[str, int, str]] = []
    used: set[int] = set()
    for qs, q in quotes:
        if not owned:
            break
        best = min(owned, key=lambda r: (abs(qs - r[2]), 0 if r[2] <= qs else 1))
        pairs.append((best[3], best[1], q))
        used.add(best[0])
    # 范围式锚（源L261-L292）不是"某一行的逐字声明"，不能算成"有锚无引文"
    bare = [(f, n, p) for p, n, _e, f in owned
            if p not in used and not any(a <= p < b for a, b in rng)]

    return pairs, bare, foreign


def verify_doc(md: Path, problems: list[str], notes: list[str]) -> tuple[int, int]:
    """返回 (可验条数, 命中条数)。"""
    text = md.read_text(encoding="utf-8")
    lines = text.splitlines()
    src_names = SOURCE_DECL.findall(text)
    if not src_names:
        # 「没声明底本」不等于「不是书证型文档」。只要文档里出现 源L 行号或「逐字」字样，
        # 本器就必须检视它，否则一条逐字声明就落在门的盲区里而 NOTE 还把它说成已豁免。
        # 实测（第五十四批）：bazi_shishen_terminology.md 被记为「非书证型文档」，
        # 而它 L13 写的是「源L54 逐字：一曰官，分之阴阳……」——可验 0 条＝门没跑。
        cited = sum(1 for ln in lines if LINE_REF.search(ln) or "逐字" in ln)
        if cited:
            problems.append(
                f"{md.name}：含 {cited} 处书证指针（源L／逐字）却未声明底本，"
                "本器无从回验 → 请在文档头部写明 `data/sources/<书名>_dz.dz.txt`")
            return 0, 0
        # 真正不引古籍的接口/规范文档才走这条显式跳过：不判红，也不冒充已验
        notes.append(f"{md.name}：不声明底本（非书证型文档），本器不检视它")
        return 0, 0
    src_path = SRC_DIR / src_names[0]
    if not src_path.exists():
        problems.append(f"{md.name}：底本不存在 {src_path.name}")
        return 0, 0
    # 第三百一十七批：文档可用「附底本：data/sources/….dz.txt」把多本书一起声明；
    # SOURCE_DECL 会把它们按出现顺序全抓出来，第一本即主底本（home）。
    declared: list[str] = []
    for name in src_names:
        p = SRC_DIR / name
        if not p.exists():
            problems.append(f"{md.name}：声明的底本不存在 {name}")
            continue
        if name not in declared:
            declared.append(name)
    if not declared:
        problems.append(f"{md.name}：没有任何可读底本，无法回验")
        return 0, 0
    home_file = declared[0]
    titles = {_fold_title(k): v for k, v in _source_titles().items()}
    home_title = next((k for k, v in titles.items() if v == home_file), "")
    corpus: dict[str, list[str]] = {
        f: (SRC_DIR / f).read_text(encoding="utf-8", errors="replace").splitlines()
        for f in declared}
    declared_set = set(declared)

    checked = passed = 0
    # ── 第一遍：凡"锚点＋同行引文"者逐一回验，并把**通过**的行号记下来 ──
    # 目的：同一行号在本文档里被反复指回时（表格、举例、按语），旧实现一律记成
    # 「该行无同行引文，未检视」，于是 56 条"其实已验过"的项与"真的没证据"的项混在
    # 同一个桶里，门只报总数不报因果。第八十五批把两者分开：回指＝已验可豁免，
    # 无同行引文且本文档从未验过该行＝**真欠账**。
    # 多底本后行号不再是唯一键（两本书都有 L54），键改成 (底本, 行号)。
    verified_lines: set[tuple[str, int]] = set()
    for i, ln in enumerate(lines):
        if RANGE_REF.search(ln) and not _same_line_quotes(ln):
            # 纯范围引用（如「推月法 L261-L292」的行号总述）不是逐字声明
            continue
        pairs, bare, n_foreign = _line_pairs(ln, home_title, titles, declared_set, home_file)
        if n_foreign:
            notes.append(f"{md.name} 第{i+1}行：{n_foreign} 处锚点属别书《书名》源L"
                         "（未在「附底本」声明），按本文已声明底本无从回验，只记不判")
        for f, lineno, q in pairs:
            nq = norm(q)
            checked += 1
            src_lines = corpus[f]
            if lineno < 1 or lineno > len(src_lines):
                problems.append(f"{md.name} 《{f}》源L{lineno}：超出底本行数（共 {len(src_lines)} 行）")
                continue
            # 底本一段常被排成多行，窗口取 L(n-1)..L(n+3)；两桶同样归一化
            window = "".join(norm(x) for x in src_lines[max(0, lineno - 2):lineno + 3])
            if nq in window:
                passed += 1
                verified_lines.add((f, lineno))
            elif len(nq) >= FAIL_MIN:
                problems.append(f"{md.name} 《{f}》源L{lineno}：引文与底本该行邻域不符 → {q[:38]}…")
            else:
                notes.append(f"{md.name} 《{f}》源L{lineno}：短引文未命中（{q[:24]}），只记不判")
    # ── 第二遍：只处理裸指针（无同行引文的锚点），按是否"已在他处验过该行"分流 ──
    for i, ln in enumerate(lines):
        if RANGE_REF.search(ln) and not _same_line_quotes(ln):
            continue
        pairs, bare, n_foreign = _line_pairs(ln, home_title, titles, declared_set, home_file)
        for f, lineno, at in bare:
            if BACK_REF.search(ln[:at + 24]):
                notes.append(f"{md.name} 《{f}》源L{lineno}：回指式引用（指回已验的引文），未检视")
            elif (f, lineno) in verified_lines:
                notes.append(f"{md.name} 《{f}》源L{lineno}：回指（本文档他处已逐字回验通过），不计欠账")
            else:
                notes.append(f"{md.name} 《{f}》源L{lineno}：该行无同行引文，未检视（真欠账：本文档从未验过该行）")
    return checked, passed


def selftest(problems: list[str]) -> None:
    """负例自证：把一段确实存在的引文换成不存在的字，本器必须报 MISMATCH。"""
    tmp = REF_DIR / "_selftest_fake_reference.md"
    # 自动挑一份「声明了底本」的参考文档来借它的语料文件（两科同一实现，不硬编文件名）
    src_names = []
    for cand in sorted(REF_DIR.glob("*.md")):
        src_names = SOURCE_DECL.findall(cand.read_text(encoding="utf-8"))
        if src_names:
            break
    if not src_names:
        problems.append("负例自证无法执行：找不到可借的底本声明")
        return
    real = SRC_DIR / src_names[0]
    line_no = 1
    for n, t in enumerate(real.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if len(norm(t)) >= FAIL_MIN:
            line_no = n
            break
    good = norm(real.read_text(encoding="utf-8", errors="replace").splitlines()[line_no - 1])
    # 多锚行负例：引文只属于右边那条锚。旧实现拿"本行最长引文"去配所有锚，
    # 会在左边那条从未做过逐字声明的锚上报出 MISMATCH——门自己造一条声明再判它可疑。
    # 谁把绑定改回去，这一行必然假红，本断言当场失败。
    other = line_no + 40
    tmp.write_text(
        f"书源：data/sources/{src_names[0]}\n\n"
        f"真引文（源L{line_no} 逐字）：`{good[:30]}`\n\n"
        "假引文（源L1 逐字）：`此串绝无可能出现在任何古籍里用来测试回验器`\n"
        f"多锚行（源L{other} 四句总述 + 源L{line_no} 逐字：`{good[:30]}`）\n",
        encoding="utf-8")
    try:
        sub_p: list[str] = []
        sub_n: list[str] = []
        checked, passed = verify_doc(tmp, sub_p, sub_n)
        fake_hit = any("绝无可能出现在任何古籍里" in x for x in sub_p)
        real_flagged = any(f"源L{line_no}" in x for x in sub_p)
        # 只看判红：左锚本就没有自己的引文，它落进 NOTE 是正确行为（"该行无同行引文"），
        # 把它也算进断言会让门自己变成假阳性的来源。
        misbound = any(f"源L{other}" in x for x in sub_p)
        if checked < 3:
            problems.append(f"负例自证：只验到 {checked} 条（应≥3 条：真/假/多锚各一条），样本无效")
        if not fake_hit:
            problems.append(f"负例自证失效：编造的错误引文没被判红 → {sub_p}")
        if real_flagged:
            problems.append(f"负例自证假阳性：逐字正确的引文（源L{line_no}）也被判错，"
                            "窗口/归一化过窄，本器不足以当硬门")
        if misbound:
            problems.append(f"负例自证失效：多锚行把只属于 源L{line_no} 的引文算到了 源L{other} 账上，"
                            f"锚-引文绑定又丢了 → {sub_p}｜{sub_n}")
        if passed != 2:
            problems.append(f"负例自证计数异常：正样本应命中 2 条（真引文 + 多锚行引文），"
                            f"实得 {passed}（可验 {checked}）")
    finally:
        tmp.unlink(missing_ok=True)

    # ── 多底本自证（第三百一十七批）──
    # 文档用「附底本」声明第二本书后，锚点按《书名》绑过去逐字回验。
    # 没有这条自证，"支持多底本"只是措辞：旧实现会把跨书锚点整条跳过，
    # 可验条数照样涨（来自 home 书的引文），假绿看不出来。
    titles = _source_titles()
    aux = ""
    for pf in sorted(SRC_DIR.glob("*.dz.txt")):
        if pf.name == real.name:
            continue
        if any(v == pf.name for v in titles.values()):
            aux = pf.name
            break
    if not aux:
        problems.append("多底本自证无法执行：找不到第二本带 provenance 的底本")
        return
    aux_book = next(k for k, v in titles.items() if v == aux)
    aux_lines = (SRC_DIR / aux).read_text(encoding="utf-8", errors="replace").splitlines()
    aux_no, aux_good = 1, ""
    for n, t in enumerate(aux_lines, 1):
        if len(norm(t)) >= FAIL_MIN:
            aux_no, aux_good = n, norm(t)
            break
    if not aux_good:
        problems.append(f"多底本自证无法执行：《{aux_book}》找不到够长的行")
        return
    tmp2 = REF_DIR / "_selftest_multi_source.md"
    fake_no = aux_no + 40 if aux_no + 40 <= len(aux_lines) else max(1, aux_no - 1)
    tmp2.write_text(
        f"书源：data/sources/{real.name}\n"
        f"附底本：data/sources/{aux}\n\n"
        f"真引文（《{aux_book}》源L{aux_no} 逐字）：`{aux_good[:30]}`\n\n"
        f"假引文（《{aux_book}》源L{fake_no} 逐字）：`此串绝无可能出现在任何古籍里用来测试多底本`\n",
        encoding="utf-8")
    try:
        sub_p2: list[str] = []
        sub_n2: list[str] = []
        checked2, passed2 = verify_doc(tmp2, sub_p2, sub_n2)
        real2_flagged = any(f"源L{aux_no}：" in x and "不符" in x for x in sub_p2)
        fake2_flagged = any("绝无可能出现在任何古籍里" in x for x in sub_p2)
        if passed2 < 1:
            problems.append(f"多底本自证失效：《{aux_book}》的真实引文没被回验命中"
                            f"（可验 {checked2}／命中 {passed2}）→ {sub_p2}｜{sub_n2}")
        if not fake2_flagged:
            problems.append(f"多底本自证失效：挂在《{aux_book}》名下的编造引文没被判红 → {sub_p2}")
        if real2_flagged:
            problems.append(f"多底本自证假阳性：真引文被判错 → {sub_p2}")
    finally:
        tmp2.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="八字参考文档源L行号引文逐字回验")
    ap.add_argument("--doc", default="", help="只验一个文档（相对学科根）")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    ap.add_argument("--notes", action="store_true",
                    help="全量列出 NOTE（默认只报构成与前 12 条）")
    args = ap.parse_args()

    # `args.doc` 是 str（argparse 未做 type=Path），旧代码取 `.name` 直接抛 AttributeError，即本器自述的 `--doc` 单文档模式从来没跑通过（第五十四批修）。
    docs = [REF_DIR / Path(args.doc).name] if args.doc else sorted(REF_DIR.glob("*.md"))
    problems: list[str] = []
    notes: list[str] = []
    total_checked = total_passed = 0
    for md in docs:
        if not md.exists():
            problems.append(f"文档不存在：{md}")
            continue
        c, p = verify_doc(md, problems, notes)
        total_checked += c
        total_passed += p
        print(f"  {md.name}: 可验 {c} 条，逐字命中 {p} 条")

    if args.selftest:
        selftest(problems)
        print("  [selftest] 负例已跑")

    print(f"合计：{total_checked} 条可验 / {total_passed} 条逐字命中 / "
          f"{len(problems)} 条判红 / {len(notes)} 条 NOTE")
    if total_checked == 0:
        print("× 0 条被真正检视——本器等于没跑，不判通过")
        return 1
    # NOTE 只报总数等于没报：不点名就无法判定哪条可闭（第八十五批补，六爻科早已如此）
    kinds: dict[str, int] = {}
    for n in notes:
        if "短引文未命中" in n:
            k = "短引文未命中"
        elif "回指式引用" in n:
            k = "回指式引用（指回已验引文）"
        elif "不计欠账" in n:
            k = "回指·该行本文档已逐字验过（豁免）"
        elif "真欠账" in n:
            k = "真欠账（该行本文档从未验过）"
        elif "属别书" in n:
            k = "跨书锚点（按底本无从回验）"
        elif "不声明底本" in n:
            k = "文档不声明底本（整篇不检视）"
        elif "无同行引文" in n:
            k = "该行无同行引文"
        else:
            k = "其它"
        kinds[k] = kinds.get(k, 0) + 1
    print("  NOTE 构成：" + ("、".join(f"{k} {v}" for k, v in
                                    sorted(kinds.items(), key=lambda kv: -kv[1]))
                             if kinds else "（无）"))
    for n in (notes if args.notes else notes[:12]):
        print(f"  · {n}")
    if not args.notes and len(notes) > 12:
        print(f"  （另有 {len(notes) - 12} 条 NOTE，`--notes` 全列）")
    for p in problems:
        print(f"  × {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())