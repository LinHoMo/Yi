# -*- coding: utf-8 -*-
"""底本完整性门（[42]，第四百三十三批）：provenance 登记值必须与在盘底本逐项相等。

为什么需要它（433 批实测）：`data/sources/*.provenance.json` 的 note 普遍写着
「sha256 与 stats 由本次对在盘文件实测得出，可用于后续核对文件是否被改动」，
但全仓没有任何门真的核对过。433 批首跑即抓到 1 份失配：
`liuyao/data/sources/huozhulin.provenance.json` 记 sha256 `2cc29b1e…`、67945 字节，
在盘文件却是 sha256 `b3bed441…`、66666 字节——差 1279 字节/字，恰等于文件换行数，
即 CRLF 版被规范成 LF 版后 provenance 未重测。底本是全部「逐字回验」的根，
根上的一字节漂移会让上面所有门失去意义，故设本门。

核对口径（四项都是机械可复算，不做启发式）：
  sha256 —— 原始字节的 SHA-256；
  bytes  —— 原始字节数（UTF-8 未解码）；
  chars  —— `len(text)`（UTF-8 解码后，含换行符）；
  lines  —— **非空行数**（`sum(1 for ln in text.splitlines() if ln.strip())`）。
            ⚠ 不是 `len(text.splitlines())`：早期 provenance 脚本按非空行统计
            （433 批实测 36/37 份按此口径全相符；用含空行口径会误报 22+14 份）。

不核 `stats.ganzhi_pairs／tables／headings`：它们的抽取口径散在多个历史脚本里，
没有单一可复算定义；本门宁可显式说「不核」，也不拿半定义去判红（§六.5）。

    python dev_tools/check_source_provenance.py
    python dev_tools/check_source_provenance.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
SRC = DISC / "data" / "sources"

# 底本份数下限（0 结果 ≠ 通过；份数增减必须同批改这里并登记）：
# bazi 23 / liuyao 16（433 批实测；六爻原 14 份因两份旧册缺 source_file 未核，
# 433 批补齐后 16 份全核）。
MIN_FILES = {"bazi": 23, "liuyao": 16}


def measure(source: Path) -> dict:
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return {
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "chars": len(text),
        "lines": sum(1 for ln in text.splitlines() if ln.strip()),
    }


def audit(prov_dir: Path, base: Path) -> tuple[list[str], dict]:
    """逐份核对 provenance ↔ 底本。`base` 是学科根（source_file 相对它解析）。"""
    problems: list[str] = []
    stats = {"files": 0, "checked": 0, "fields": 0}
    for pv in sorted(prov_dir.glob("*.provenance.json")):
        stats["files"] += 1
        try:
            d = json.loads(pv.read_text(encoding="utf-8"))
        except Exception as exc:
            problems.append(f"{pv.name}：JSON 解析失败（{exc}）")
            continue
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
    if stats["files"] == 0:
        problems.append("扫描到 0 份 provenance——0 结果 ≠ 通过，先确认路径没挪动")
    return problems, stats


def _fixture(root: Path, source_text: str = "甲子\n\n乙丑\n", **overrides) -> Path:
    """临时夹具：一份底本 + 一份 provenance（只走临时目录，铁律二）。"""
    src_dir = root / "data" / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    # 夹具源文件放在临时根下、源名不带 `/`：避免死链门把「data/sources/…」当成仓库真路径。
    src = root / "jubu.txt"
    src.write_text(source_text, encoding="utf-8")
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
    (src_dir / "jubu.provenance.json").write_text(
        json.dumps(prov, ensure_ascii=False), encoding="utf-8")
    return src_dir


def selftest() -> int:
    def tamper(root: Path) -> Path:
        src_dir = _fixture(root)
        (root / "jubu.txt").write_text("甲子\n\n乙丑\n丙\n", encoding="utf-8")
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
    if bad:
        print(f"  × selftest 失败 {bad} 例——测量口径/判据漂移，先修器")
        return 1
    print(f"  √ selftest：{len(cases)} 件（正例/哈希失配/底本漂移/缺文件/缺键/行数口径/0 结果）全过")
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
    print(f"[42] 底本完整性：{stats['files']} 份 provenance（核到 {stats['checked']} 份底本、"
          f"{stats['fields']} 项统计）")
    st_fail = selftest() if args.selftest else 0
    if problems:
        print(f"\n失败 {len(problems)} 项：")
        for p in problems:
            print(f"  × {p}")
        return 1
    if st_fail:
        return 1
    print("  √ sha256/bytes/chars/lines 与在盘底本逐项相符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
