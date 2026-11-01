# -*- coding: utf-8 -*-
"""底本完整性门（[42]，第四百三十三批）：provenance 登记值必须与在盘底本逐项相等。

为什么需要它（433 批实测）：`data/sources/*.provenance.json` 的 note 普遍写着
「sha256 与 stats 由本次对在盘文件实测得出，可用于后续核对文件是否被改动」，
但全仓没有任何门真的核对过。433 批首跑即抓到 1 份失配：
`liuyao/data/sources/huozhulin.provenance.json` 记 sha256 `2cc29b1e…`、67945 字节，
在盘文件却是 sha256 `b3bed441…`、66666 字节——差 1279 字节/字，恰等于文件换行数，
即 CRLF 版被规范成 LF 版后 provenance 未重测。底本是全部「逐字回验」的根，
根上的一字节漂移会让上面所有门失去意义，故设本门。

核对口径（下列各项都是机械可复算，不做启发式）：
  sha256 —— 原始字节的 SHA-256；
  bytes  —— 原始字节数（UTF-8 未解码）；
  chars  —— `len(text)`（UTF-8 解码后，含换行符）；
  lines  —— **非空行数**（`sum(1 for ln in text.splitlines() if ln.strip())`）。
            ⚠ 不是 `len(text.splitlines())`：早期 provenance 脚本按非空行统计
            （433 批实测 36/37 份按此口径全相符；用含空行口径会误报 22+14 份）。
  443 批补核三项（帮助登记注记里的「统计由 [42] 核对」成为字面事实）：
  ganzhi_pairs —— 相邻「一字干＋一字支」的出现数，`re.findall("[十干][十二支]", text)`；
            **不要求六十甲子配对合法**（实测按合法配对计数只有 8/36 相符，按全组合
            36/36 逐格相符，故历史口径就是全组合）。
  tables   —— 维基表格开标签数 `text.count("{|")`（dz 本与 wikitext 本同口径）。
  headings —— 行首为 `=` 的行数（维基标题行；dz 本无此形态，登记值均为 0）。
            三项均由 443 批对全仓 36 份**登记了该字段**的 provenance 逐格重算验证：
            0 处改值、0 处变空，定义由「36/36 命中」反推并固定下来，不是猜的。

444 批补核三项**登记元数据**（同样只在登记时才核）：
  page_count  —— 必须等于 `pages` 列表长度（36 份登记，实测 36/36 相符）；
  eol_on_disk —— 在盘换行形态：全 LF→"LF"、全 CRLF→"CRLF"、两者兼有→"mixed"、
                 无换行→"none"（3 份登记，实测全符；这是 433 批 CRLF/LF 事故的常设哨）；
  sha256_lf_text —— 把原始字节里的 `\r\n` 折成 `\n` 后取 SHA-256（1 份登记，实测相符）。

445 批补齐台账表：六爻 `source_ledger.md` 的「干支对」「标题」两列是 provenance
统计的第二份抄本，435 批只核了字节/哈希/行数。现对**数值格**逐格复算（六爻 6 行×2
列＝12 格；456 批把《易冒》《易隐》两行的「未测」按同一 `measure()` 实测补入后，
下限由 8 抬到 12，数值格少于 12 即判红——防整列退化为占位而门空转）。八字当前无此表，跳过。

435 批追加：`references/` 下的「在库书源」台账表是 provenance 的第二份抄本，
433 批刚发现它六行里有四行陈旧（字节/哈希/行数）——本门把该表一并核对
（字节、sha256 前 16 位、非空行、provenance 存在性）。表不存在则跳过（八字当前无此表）。

442 批追加：**可选双口径行数**。`huangji_jingshi_shu_dz.provenance.json` 在 2026-10-07
澄清时登记 `lines_nonempty=5358 / lines_physical=5496`，并声明后者「与 cat -n 行号口径
一致，供 check_source_readings.py 逐字核验使用」——但 433 批的 [42] 只核
bytes/chars/lines，这两个字段从未被复算。442 批首跑即抓到 `lines_physical` 登记值
**多一行**：在盘底本换行符 5495 个、末尾带换行，`cat -n`／`splitlines()`／文件迭代器
三种口径均为 **5495**；5496 是「换行符数 +1」的常见多算（该笔记把该值当作行号口径
交给人用，错一位就会让「源L」整体错行）。故本门对**已登记**的 `lines_nonempty`
（非空行，同 `lines` 定义）与 `lines_physical`（`len(text.splitlines())`）一并复算；
未登记的不强制补（保留历史登记形态，避免为过门批量改数据）。

    python dev_tools/check_source_provenance.py
    python dev_tools/check_source_provenance.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
SRC = DISC / "data" / "sources"
LEDGER = DISC / "references" / "source_ledger.md"

# 底本份数下限（0 结果 ≠ 通过；份数增减必须同批改这里并登记）：
# bazi 23 / liuyao 16（433 批实测；六爻原 14 份因两份旧册缺 source_file 未核，
# 433 批补齐后 16 份全核）。
MIN_FILES = {"bazi": 23, "liuyao": 16}
# 台账表行数下限（表不存在时按 0：八字当前无 ledger）。
MIN_LEDGER_ROWS = {"bazi": 0, "liuyao": 6}
# 台账「干支对／标题」数值格下限（445 批立；456 批 8→12）：六爻 6 行全部 6×2 有值——
# 《易冒》《易隐》两行的「未测」已由 456 批实测补入（314/0、1334/0）。八字无台账，按 0。
MIN_LEDGER_STAT_CELLS = {"bazi": 0, "liuyao": 12}


# 六十干支的构成元件：只用于「相邻干支组合」统计，不参与任何判读，故不引内核表。
STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
STEM_BRANCH = re.compile(f"[{STEMS}][{BRANCHES}]")


def _eol(raw: bytes) -> str:
    """在盘换行形态（供 eol_on_disk 复核；mixed/none 也是合法实测值）。"""
    crlf = raw.count(b"\r\n")
    cr = raw.count(b"\r") - crlf
    lf = raw.count(b"\n") - crlf
    if crlf == 0 and cr == 0:
        return "LF" if lf else "none"
    if lf == 0 and cr == 0:
        return "CRLF"
    return "mixed"


def measure(source: Path) -> dict:
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "chars": len(text),
        "lines": sum(1 for ln in text.splitlines() if ln.strip()),
        # 443 批：三项可复算扩展统计（定义与 36/36 验证见模块 docstring）
        "ganzhi_pairs": len(STEM_BRANCH.findall(text)),
        "tables": text.count("{|"),
        "headings": sum(1 for ln in text.splitlines() if ln.startswith("=")),
        # 444 批：登记元数据的可复算值（有登记才核，见 audit）
        "eol": _eol(raw),
        "sha256_lf_text": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
        # 442 批：双口径行数（仅在 provenance 登记时才核，见 audit）。
        # lines_nonempty 与 lines 同义（非空行）；lines_physical 是 `cat -n`／
        # 文件迭代器口径的物理行数 = len(splitlines())，**不是**换行符数 +1
        # （末尾有换行时 +1 会多算一行，皇极经世书 provenance 原登记即此错）。
        "lines_nonempty": sum(1 for ln in text.splitlines() if ln.strip()),
        "lines_physical": len(text.splitlines()),
    }


def audit(prov_dir: Path, base: Path) -> tuple[list[str], dict]:
    """逐份核对 provenance ↔ 底本。`base` 是学科根（source_file 相对它解析）。"""
    problems: list[str] = []
    stats = {"files": 0, "checked": 0, "fields": 0, "ext": 0, "dual": 0, "meta": 0}
    for pv in sorted(prov_dir.glob("*.provenance.json")):
        stats["files"] += 1
        try:
            d = json.loads(pv.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{pv.name}：JSON 解析失败（{exc}）")
            continue
        note = str(d.get("note") or "")
        # 只抓已删除的裸 `tools/`；`dev_tools/` 是现行目录，不能误伤。
        if "tools/" in note.replace("dev_tools/", ""):
            problems.append(f"{pv.name}：note 仍指向已删除的 tools/ 路径（扁平化后该目录不存在）")
        sf = str(d.get("source_file") or "")
        if not sf:
            problems.append(f"{pv.name}：缺 source_file")
            continue
        src = base / sf
        if not src.is_file():
            problems.append(f"{pv.name}：source_file 不存在 → {sf}")
            continue
        stats["checked"] += 1
        got = measure(src)
        reg_sha = str(d.get("sha256") or "")
        if not reg_sha:
            problems.append(f"{pv.name}：缺 sha256")
        elif reg_sha != got["sha256"]:
            problems.append(f"{pv.name}：sha256 失配（登记 {reg_sha[:12]}… ≠ "
                            f"在盘 {got['sha256'][:12]}…）")
        for key in ("bytes", "chars", "lines"):
            stats["fields"] += 1
            reg = (d.get("stats") or {}).get(key)
            if reg is None:
                problems.append(f"{pv.name}：stats.{key} 未登记")
            elif int(reg) != got[key]:
                problems.append(f"{pv.name}：stats.{key} {reg} ≠ 在盘 {got[key]}")
        # 443 批：已登记的扩展示性统计逐项复算（未登记的不强制补：如《三命通会》四库本
        # 与两份 wikitext 原始件本就没有这三项）。定义见 measure()；36/36 实测相符。
        for key in ("ganzhi_pairs", "tables", "headings"):
            if key not in (d.get("stats") or {}):
                continue
            stats["ext"] += 1
            reg = d["stats"][key]
            if int(reg) != got[key]:
                problems.append(f"{pv.name}：stats.{key} {reg} ≠ 在盘 {got[key]}"
                                f"（口径见 check_source_provenance.measure）")
        # 444 批：登记元数据自洽（有登记才核；定义见 measure/_eol）。
        pages, pc = d.get("pages"), d.get("page_count")
        if isinstance(pages, list) and isinstance(pc, int):
            stats["meta"] += 1
            if pc != len(pages):
                problems.append(f"{pv.name}：page_count {pc} ≠ pages 长度 {len(pages)}")
        if "eol_on_disk" in d:
            stats["meta"] += 1
            if str(d["eol_on_disk"]) != got["eol"]:
                problems.append(f"{pv.name}：eol_on_disk 登记 {d['eol_on_disk']} ≠ "
                                f"在盘 {got['eol']}（口径见 check_source_provenance._eol）")
        if "sha256_lf_text" in d:
            stats["meta"] += 1
            reg_lf = str(d["sha256_lf_text"] or "")
            if reg_lf != got["sha256_lf_text"]:
                problems.append(f"{pv.name}：sha256_lf_text 失配（登记 {reg_lf[:12]}… ≠ "
                                f"LF 折行实测 {got['sha256_lf_text'][:12]}…）")
        # 442 批：可选双口径行数一旦登记就必须复算相符——它们被逐字回验按行号引用，
        # 登记值错一位就会把「源L」指向另一行，而 sha/bytes/chars 全绿时无人发现。
        # 定义见 measure()；未登记的 provenance 不强制补（保留历史登记形态）。
        for key in ("lines_nonempty", "lines_physical"):
            if key not in (d.get("stats") or {}):
                continue
            stats["dual"] += 1
            reg = d["stats"][key]
            if int(reg) != got[key]:
                problems.append(f"{pv.name}：stats.{key} {reg} ≠ 在盘 {got[key]}"
                                f"（口径见 check_source_provenance.measure）")
    if stats["files"] == 0:
        problems.append("扫描到 0 份 provenance——0 结果 ≠ 通过，先确认路径没挪动")
    return problems, stats


def _as_int(cell: str) -> int | None:
    s = cell.replace(",", "").strip()
    return int(s) if s.isdigit() else None


def audit_ledger(path: Path, base: Path) -> tuple[list[str], int, int]:
    """核对 `references/` 下的「在库书源」台账表（provenance 的第二份抄本）。

    返回 (问题, 行数, 已核统计格数)。445 批起把「干支对」「标题」两列一并复算——
    它们是 provenance 统计的第二份抄本，此前只核字节/哈希/行数。
    """
    if not path.is_file():
        return [], 0, 0
    text = path.read_text(encoding="utf-8")
    m = re.search(r"## 一、在库书源.*?\n(.*?)(?=\n### |\n## |\Z)", text, re.S)
    if not m:
        return [f"{path.name}：找不到「## 一、在库书源」表"], 0, 0
    prov_by_source: dict[str, str] = {}
    for pv in sorted((base / "data" / "sources").glob("*.provenance.json")):
        try:
            d = json.loads(pv.read_text(encoding="utf-8"))
        except Exception:
            continue
        sf = str(d.get("source_file") or "")
        if sf:
            prov_by_source[sf] = pv.name
    problems: list[str] = []
    rows = 0
    stat_cells = 0
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or "`" not in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        fm = re.search(r"`([^`]+\.txt)`", cells[1])
        if not fm:
            continue
        rows += 1
        rel = f"data/sources/{fm.group(1)}"
        src = base / rel
        name = f"台账行「{fm.group(1)}」"
        if not src.is_file():
            problems.append(f"{path.name}：{name} 底本不存在 → {rel}")
            continue
        got = measure(src)
        b, sha_cell, ln = _as_int(cells[2]), cells[3].strip("`").strip(), _as_int(cells[4])
        if b is None or b != got["bytes"]:
            problems.append(f"{path.name}：{name} 字节 {cells[2]} ≠ 在盘 {got['bytes']}")
        if not re.fullmatch(r"[0-9a-f]{16}", sha_cell) or not got["sha256"].startswith(sha_cell):
            problems.append(f"{path.name}：{name} sha256 {sha_cell}… ≠ 在盘 {got['sha256'][:16]}…")
        if ln is None or ln != got["lines"]:
            problems.append(f"{path.name}：{name} 行 {cells[4]} ≠ 在盘非空行 {got['lines']}")
        # 445 批：台账的「干支对」「标题」列 = provenance 统计的第二份抄本。
        # 数值格必须复算相符；「未测」等非数字占位是合法形态（六爻《易冒》《易隐》两行），
        # 只跳过、不判红（0 结果由 main 里的最小格数上限兜底）。
        for idx, key, label in ((5, "ganzhi_pairs", "干支对"), (6, "headings", "标题")):
            if len(cells) <= idx:
                continue
            v = _as_int(cells[idx])
            if v is None:
                continue
            stat_cells += 1
            if v != got[key]:
                problems.append(f"{path.name}：{name} {label} {cells[idx]} ≠ 在盘 {got[key]}")
        if cells[-1].startswith("有") and rel not in prov_by_source:
            problems.append(f"{path.name}：{name} 声称有 provenance，但无 source_file 指向它")
    if rows == 0:
        problems.append(f"{path.name}：在库书源表 0 行——0 结果 ≠ 通过，先确认表结构没改")
    return problems, rows, stat_cells


def _fixture(root: Path, source_text: str = "甲子\n\n乙丑\n", **overrides) -> Path:
    """临时夹具：一份底本 + 一份 provenance（只走临时目录，铁律二）。"""
    src_dir = root / "data" / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    # 夹具源文件放在临时根下、源名不带 `/`：避免死链门把「data/sources/…」当成仓库真路径。
    # 用 write_bytes 而非 write_text：Windows 文本模式会把 \n 转成 \r\n，
    # 会让 eol_on_disk 的正例变成 CRLF（444 批自测实踩）。
    src = root / "jubu.txt"
    src.write_bytes(source_text.encode("utf-8"))
    m = measure(src)
    prov = {
        "sha256": overrides.get("sha256", m["sha256"]),
        "stats": {
            "bytes": overrides.get("bytes", m["bytes"]),
            "chars": overrides.get("chars", m["chars"]),
            "lines": overrides.get("lines", m["lines"]),
        },
        "source_file": overrides.get("source_file", "jubu.txt"),
    }
    if overrides.get("drop_sha"):
        prov.pop("sha256")
    if "note" in overrides:
        prov["note"] = overrides["note"]
    # 442 批：可选双口径字段（`extra` 里的键直接并入 stats；不传即保持历史形态）
    for k, v in (overrides.get("extra") or {}).items():
        prov["stats"][k] = v
    # 444 批：登记元数据（page_count/pages/eol_on_disk/sha256_lf_text）；
    # 哨兵 "__LF__" 让正例不必在夹具外重算 LF 折行哈希。
    for k, v in (overrides.get("top") or {}).items():
        if v == "__LF__":
            v = m["sha256_lf_text"]
        prov[k] = v
    (src_dir / "jubu.provenance.json").write_text(
        json.dumps(prov, ensure_ascii=False), encoding="utf-8")
    return src_dir


def _ledger_fixture(root: Path, *, bytes_cell=None, lines_cell=None,
                    ganzhi_cell=None, headings_cell=None,
                    drop_source=False, drop_prov=False, no_rows=False,
                    missing_section=False) -> Path:
    """临时夹具：一份底本＋provenance＋「在库书源」台账表。"""
    src_dir = root / "data" / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    # 夹具名带 `_selftest_`：死链门把该类串登记为负例样本，不会当成仓库真路径。
    src = src_dir / "_selftest_ledger.txt"
    src.write_bytes("甲子\n\n乙丑\n".encode("utf-8"))
    m = measure(src)
    if not drop_prov:
        (src_dir / "_selftest_ledger.provenance.json").write_text(json.dumps({
            "sha256": m["sha256"],
            "stats": {"bytes": m["bytes"], "chars": m["chars"], "lines": m["lines"]},
            "source_file": "data/sources/_selftest_ledger.txt",
        }, ensure_ascii=False), encoding="utf-8")
    if drop_source:
        src.unlink()
    ref = root / "references"
    ref.mkdir(parents=True, exist_ok=True)
    ledger = ref / "source_ledger.md"
    if missing_section:
        ledger.write_text("# 台账\n\n（无表）\n", encoding="utf-8")
        return ledger
    body = ""
    if not no_rows:
        b = m["bytes"] if bytes_cell is None else bytes_cell
        ln = m["lines"] if lines_cell is None else lines_cell
        gz = m["ganzhi_pairs"] if ganzhi_cell is None else ganzhi_cell
        hd = m["headings"] if headings_cell is None else headings_cell
        body = (f"| 《夹具》 | `_selftest_ledger.txt` | {b:,} | `{m['sha256'][:16]}` | {ln} "
                f"| {gz} | {hd} | 有 |\n")
    ledger.write_text(
        "# 台账\n\n## 一、在库书源（实测）\n\n"
        "| 书 | 本地文件（`data/sources/`） | 字节 | 本地 sha256（前 16 位） | 行（非空） "
        "| 干支对 | 标题 | provenance |\n"
        "|---|---|---|---|---|---|---|---|\n" + body + "\n### 抽取状态\n",
        encoding="utf-8")
    return ledger


def selftest() -> int:
    def tamper(root: Path) -> Path:
        src_dir = _fixture(root)
        (root / "jubu.txt").write_bytes("甲子\n\n乙丑\n丙\n".encode("utf-8"))
        return src_dir

    def empty(root: Path) -> Path:
        d = root / "data" / "sources"
        d.mkdir(parents=True, exist_ok=True)
        return d

    cases = [
        ("正例：四项与在盘一致", None, lambda r: _fixture(r)),
        ("负例：sha256 失配", "sha256 失配", lambda r: _fixture(r, sha256="0" * 64)),
        ("负例：底本被追加一字节", "sha256 失配", tamper),
        ("负例：source_file 不存在", "source_file 不存在",
         lambda r: _fixture(r, source_file="nope.txt")),
        ("负例：缺 sha256", "缺 sha256", lambda r: _fixture(r, drop_sha=True)),
        ("负例：lines 用含空行口径", "stats.lines", lambda r: _fixture(r, lines=3)),
        ("负例：0 份 provenance", "0 份", empty),
        ("负例：note 仍指向已删除 tools/", "tools/",
         lambda r: _fixture(r, note="须跑 tools/crosscheck_source.py 对勘留痕")),
        # 442 批：可选双口径（夹具底本 "甲子\n\n乙丑\n" = 非空 2 行 / 物理 3 行）
        ("正例：双口径登记值与底本一致", None,
         lambda r: _fixture(r, extra={"lines_nonempty": 2, "lines_physical": 3})),
        ("负例：lines_physical 按「换行符+1」多算一行", "stats.lines_physical",
         lambda r: _fixture(r, extra={"lines_nonempty": 2, "lines_physical": 4})),
        ("负例：lines_nonempty 登记错", "stats.lines_nonempty",
         lambda r: _fixture(r, extra={"lines_nonempty": 3, "lines_physical": 3})),
        ("正例：未登记双口径不强制补", None, lambda r: _fixture(r)),
        # 443 批：三项扩展统计（夹具底本 "甲子\n\n乙丑\n" = 干支相邻 2、无表、无标题行）
        ("正例：三项扩展统计与底本一致", None,
         lambda r: _fixture(r, extra={"ganzhi_pairs": 2, "tables": 0, "headings": 0})),
        ("负例：ganzhi_pairs 登记错", "stats.ganzhi_pairs",
         lambda r: _fixture(r, extra={"ganzhi_pairs": 3})),
        ("负例：tables 按表格行数而非 `{|` 计", "stats.tables",
         lambda r: _fixture(r, source_text="== 标题 ==\n{|\n|}\n",
                            extra={"tables": 2, "headings": 1})),
        ("负例：headings 未按行首 `=` 计", "stats.headings",
         lambda r: _fixture(r, source_text="== 标题 ==\n", extra={"headings": 2})),
        # 444 批：登记元数据（夹具底本为 LF）
        ("正例：page_count/eol/LF 折行哈希全符", None,
         lambda r: _fixture(r, top={"pages": ["p1"], "page_count": 1,
                                    "eol_on_disk": "LF", "sha256_lf_text": "__LF__"})),
        ("负例：page_count 与 pages 长度不符", "page_count",
         lambda r: _fixture(r, top={"pages": ["p1"], "page_count": 2})),
        ("负例：eol_on_disk 登记 CRLF 但在盘为 LF", "eol_on_disk",
         lambda r: _fixture(r, top={"eol_on_disk": "CRLF"})),
        ("负例：sha256_lf_text 失配", "sha256_lf_text",
         lambda r: _fixture(r, top={"sha256_lf_text": "0" * 64})),
    ]
    ledger_cases = [
        ("台账正例：行值与底本一致", None, lambda r: _ledger_fixture(r)),
        ("台账负例：字节失配", "字节", lambda r: _ledger_fixture(r, bytes_cell=1)),
        ("台账负例：行数失配", "在盘非空行", lambda r: _ledger_fixture(r, lines_cell=3)),
        ("台账负例：底本不存在", "底本不存在", lambda r: _ledger_fixture(r, drop_source=True)),
        ("台账负例：缺 provenance", "声称有 provenance",
         lambda r: _ledger_fixture(r, drop_prov=True)),
        ("台账负例：0 行", "0 行", lambda r: _ledger_fixture(r, no_rows=True)),
        ("台账负例：缺表", "找不到", lambda r: _ledger_fixture(r, missing_section=True)),
        # 445 批：台账「干支对／标题」列（夹具底本 = 干支 2 / 标题 0）
        ("台账负例：干支对失配", "干支对", lambda r: _ledger_fixture(r, ganzhi_cell=3)),
        ("台账负例：标题失配", "标题", lambda r: _ledger_fixture(r, headings_cell=1)),
        ("台账正例：未测占位跳过不判红", None,
         lambda r: _ledger_fixture(r, ganzhi_cell="未测", headings_cell="未测")),
    ]
    bad = 0
    for label, expect, setup in cases:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            prov_dir = setup(root)
            problems, _ = audit(prov_dir, root)
            if expect is None:
                ok = not problems
            else:
                ok = any(expect in p for p in problems)
            if not ok:
                bad += 1
            print(f"  {'√' if ok else '×'} {label}"
                  + ("" if ok else f"（未报出「{expect}」：{problems[:2]}）"))
    for label, expect, setup in ledger_cases:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ledger = setup(root)
            problems, rows, _cells = audit_ledger(ledger, root)
            if expect is None:
                ok = not problems and rows == 1
            else:
                ok = any(expect in p for p in problems)
            if not ok:
                bad += 1
            print(f"  {'√' if ok else '×'} {label}"
                  + ("" if ok else f"（未报出「{expect}」：{problems[:2]}）"))
    if bad:
        print(f"  × selftest 失败 {bad} 例——测量口径/判据漂移，先修器")
        return 1
    print(f"  √ selftest：{len(cases) + len(ledger_cases)} 件"
          f"（provenance {len(cases)}＋台账 {len(ledger_cases)}）全过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="底本完整性门（[42]）：provenance ↔ 在盘底本")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    problems, stats = audit(SRC, DISC)
    floor = MIN_FILES.get(DISC.name)
    if floor is None:
        problems.append(f"未登记的学科 {DISC.name}：先在 MIN_FILES 登记底本份数下限")
    elif stats["files"] < floor:
        problems.append(f"只扫到 {stats['files']} 份 provenance（下限 {floor}）"
                        "——路径挪动/文件被删？")
    ledger_problems, ledger_rows, ledger_cells = audit_ledger(LEDGER, DISC)
    problems.extend(ledger_problems)
    ledger_floor = MIN_LEDGER_ROWS.get(DISC.name)
    if ledger_floor is None:
        problems.append(f"未登记的学科 {DISC.name}：先在 MIN_LEDGER_ROWS 登记台账行数下限")
    elif LEDGER.is_file() and ledger_rows < ledger_floor:
        problems.append(f"台账只核到 {ledger_rows} 行（下限 {ledger_floor}）——表被删/改？")
    elif not LEDGER.is_file() and ledger_floor:
        problems.append(f"references/source_ledger.md 不存在（台账下限 {ledger_floor} 行）")
    cell_floor = MIN_LEDGER_STAT_CELLS.get(DISC.name, 0)
    if LEDGER.is_file() and ledger_cells < cell_floor:
        problems.append(f"台账「干支对／标题」只核到 {ledger_cells} 个数值格（下限 {cell_floor}）"
                        "——列被删/改成非数字占位？")
    ledger_desc = f"台账 {ledger_rows} 行" if LEDGER.is_file() else "台账 —（无此表）"
    if LEDGER.is_file():
        ledger_desc += f"（干支对/标题 {ledger_cells} 格）"
    ext_desc = f"、扩展 {stats['ext']} 项" if stats["ext"] else ""
    meta_desc = f"、元数据 {stats['meta']} 项" if stats["meta"] else ""
    dual_desc = f"、双口径 {stats['dual']} 项" if stats["dual"] else ""
    print(f"[42] 底本完整性：{stats['files']} 份 provenance（核到 {stats['checked']} 份底本、"
          f"{stats['fields']} 项基础统计{ext_desc}{meta_desc}{dual_desc}）；{ledger_desc}")
    st_fail = selftest() if args.selftest else 0
    if problems:
        print(f"\n失败 {len(problems)} 项：")
        for p in problems:
            print(f"  × {p}")
        return 1
    if st_fail:
        return 1
    print("  √ sha256/bytes/chars/lines 与已登记扩展统计（含双口径）逐项相符（台账表同源）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
