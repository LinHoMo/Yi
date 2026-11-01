# -*- coding: utf-8 -*-
"""案例层源哈希门（[43]，第四百三十八批）：案例 JSON 登记的源文件/哈希须与在盘底本一致。

为什么需要它（438 批实测）：案例层还有一层“源哈希”登记，却从未被任何门核对——
  · `bushi_zhengzong_cases.json` 有 `_meta.source_sha256` + 每例 `provenance.sha256`；
  · `yiin_cases.json` 有 `_meta.sha256` + 每例 `provenance.sha256`；
  · `zengshan_dz_cases.json` 有每例 `provenance.sha256`（无 `_meta` 哈希）；
  · `huozhulin_cases.json` 有 `_meta.sha256`；
  · `wikisource_cases.json` 有 `_meta.sha256`，但**没写 source_file**，且 433 批后
    provenance 的 `sha256` 已从 LF 文本哈希改为在盘字节哈希——案例层仍停在旧值。
本门把 5 份案例文件的元哈希、LF 文本哈希、每例哈希逐项与在盘底本对拍；
声明了 `source_file`/`source` 的，同时核对声明路径本身。

    python dev_tools/check_case_source_hashes.py
    python dev_tools/check_case_source_hashes.py --selftest
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
CASES = DISC / "data" / "cases"

# 案例文件 → (源文件, 元哈希字段, 每例哈希字段, LF 文本哈希字段, 下限)
# 元/每例字段为 None 表示该文件没有这一层登记；LF 字段只有 wikisource 需要。
SPECS = {
    "bushi_zhengzong_cases.json": (
        "data/sources/bushi_zhengzong_dz.dz.txt", "source_sha256", "sha256", None, 38),
    "huozhulin_cases.json": (
        "data/sources/huozhulin.wikitext.txt", "sha256", None, None, 0),
    "wikisource_cases.json": (
        "data/sources/zengshan_buyi.wikitext.txt", "sha256", None, "sha256_lf_text", 0),
    "yiin_cases.json": (
        "data/sources/yiin_dz.dz.txt", "sha256", "sha256", None, 56),
    "zengshan_dz_cases.json": (
        "data/sources/zengshan_buyi_dz.dz.txt", None, "sha256", None, 29),
}
MIN_FILES = 5
MIN_META = 5   # bushi 1 + huozhulin 1 + wikisource 1 + yiin 1 + wikisource LF 1
MIN_CASE = 123  # bushi 38 + yiin 56 + zengshan 29


def hashes(source: Path) -> tuple[str, str]:
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    lf = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(raw).hexdigest(), hashlib.sha256(lf.encode("utf-8")).hexdigest()


def audit_file(case_path: Path, base: Path, src_rel: str, meta_field, case_field,
               lf_field, min_case: int) -> tuple[list[str], dict]:
    problems: list[str] = []
    stats = {"meta": 0, "case": 0, "cases": 0}
    try:
        d = json.loads(case_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"{case_path.name}：JSON 解析失败（{exc}）"], stats
    src = base / src_rel
    if not src.is_file():
        return [f"{case_path.name}：源文件不存在 → {src_rel}"], stats
    raw, lf = hashes(src)
    meta = d.get("_meta") or {}
    declared = meta.get("source_file") or meta.get("source")
    if declared and declared != src_rel:
        problems.append(f"{case_path.name}：声明的源文件 {declared} ≠ 登记表 {src_rel}")
    if meta_field:
        stats["meta"] += 1
        reg = str(meta.get(meta_field) or "")
        if not reg:
            problems.append(f"{case_path.name}：缺 _meta.{meta_field}")
        elif reg != raw:
            problems.append(f"{case_path.name}：_meta.{meta_field} {reg[:12]}… ≠ 在盘 {raw[:12]}…")
    if lf_field:
        stats["meta"] += 1
        reg = str(meta.get(lf_field) or "")
        if not reg:
            problems.append(f"{case_path.name}：缺 _meta.{lf_field}")
        elif reg != lf:
            problems.append(f"{case_path.name}：_meta.{lf_field} {reg[:12]}… ≠ LF 文本 {lf[:12]}…")
    cases = d.get("cases") or []
    stats["cases"] = len(cases)
    if case_field:
        for c in cases:
            pv = c.get("provenance") or {}
            cid = c.get("id") or "?"
            sf = str(pv.get("source_file") or "")
            if sf and sf != src_rel:
                problems.append(f"{case_path.name}：{cid} 的 source_file {sf} ≠ 登记表 {src_rel}")
            reg = str(pv.get(case_field) or "")
            stats["case"] += 1
            if not reg:
                problems.append(f"{case_path.name}：{cid} 缺 provenance.{case_field}")
            elif reg != raw:
                problems.append(f"{case_path.name}：{cid} provenance.{case_field} "
                                f"{reg[:12]}… ≠ 在盘 {raw[:12]}…")
        if stats["case"] < min_case:
            problems.append(f"{case_path.name}：每例哈希只核到 {stats['case']} 项"
                            f"（下限 {min_case}）——案例被删/字段被清？")
    return problems, stats


def audit_all(specs: dict, base: Path) -> tuple[list[str], dict]:
    problems: list[str] = []
    stats = {"files": 0, "meta": 0, "case": 0}
    for name, spec in specs.items():
        path = base / "data" / "cases" / name
        if not path.is_file():
            problems.append(f"{name}：案例文件不存在")
            continue
        stats["files"] += 1
        probs, st = audit_file(path, base, *spec)
        problems.extend(probs)
        stats["meta"] += st["meta"]
        stats["case"] += st["case"]
    if stats["files"] == 0:
        problems.append("扫描到 0 份案例文件——0 结果 ≠ 通过，先确认路径没挪动")
    if stats["meta"] < MIN_META:
        problems.append(f"元哈希只核到 {stats['meta']} 项（下限 {MIN_META}）")
    if stats["case"] < MIN_CASE:
        problems.append(f"每例哈希只核到 {stats['case']} 项（下限 {MIN_CASE}）")
    return problems, stats


def _fixture(root: Path, *, meta_wrong=False, case_wrong=False, drop_source=False,
             bad_lf=False, no_cases=False) -> tuple[Path, dict]:
    src_dir = root / "data" / "sources"
    src_dir.mkdir(parents=True, exist_ok=True)
    src = src_dir / "_selftest_src.txt"
    src.write_text("甲子\n\n乙丑\n", encoding="utf-8")
    raw, lf = hashes(src)
    if drop_source:
        src.unlink()
    meta = {
        "source_file": "data/sources/_selftest_src.txt",
        "sha256": ("0" * 64) if meta_wrong else raw,
        "sha256_lf_text": ("0" * 64) if bad_lf else lf,
    }
    cases = [] if no_cases else [
        {"id": "S1", "provenance": {"source_file": "data/sources/_selftest_src.txt",
                                    "sha256": ("0" * 64) if case_wrong else raw}},
        {"id": "S2", "provenance": {"source_file": "data/sources/_selftest_src.txt",
                                    "sha256": raw}},
    ]
    case_dir = root / "data" / "cases"
    case_dir.mkdir(parents=True, exist_ok=True)
    cp = case_dir / "_selftest_case.json"
    cp.write_text(json.dumps({"_meta": meta, "cases": cases}, ensure_ascii=False), encoding="utf-8")
    spec = ("data/sources/_selftest_src.txt", "sha256", "sha256", "sha256_lf_text", 2)
    return cp, spec


def selftest() -> int:
    cases = [
        ("正例：元哈希/每例哈希/LF 哈希全符", None,
         lambda r: _fixture(r)),
        ("负例：元哈希失配", "_meta.sha256", lambda r: _fixture(r, meta_wrong=True)),
        ("负例：每例哈希失配", "provenance.sha256", lambda r: _fixture(r, case_wrong=True)),
        ("负例：LF 文本哈希失配", "sha256_lf_text", lambda r: _fixture(r, bad_lf=True)),
        ("负例：源文件不存在", "源文件不存在", lambda r: _fixture(r, drop_source=True)),
        ("负例：0 例哈希", "下限 2", lambda r: _fixture(r, no_cases=True)),
    ]
    bad = 0
    for label, expect, setup in cases:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cp, spec = setup(root)
            probs, st = audit_file(cp, root, *spec)
            ok = (not probs) if expect is None else any(expect in p for p in probs)
            if not ok:
                bad += 1
            print(f"  {'√' if ok else '×'} {label}"
                  + ("" if ok else f"（未报出「{expect}」：{probs[:2]}）"))
    with tempfile.TemporaryDirectory() as td:
        probs, st = audit_all({}, Path(td))
        ok = any("0 份" in p for p in probs)
        print(f"  {'√' if ok else '×'} 负例：0 份案例文件")
        if not ok:
            bad += 1
    if bad:
        print(f"  × selftest 失败 {bad} 例——判据/路径漂移，先修器")
        return 1
    print(f"  √ selftest：{len(cases) + 1} 件（正例/元哈希/每例/LF/缺源/0 例/0 文件）全过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="案例层源哈希门（[43]）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    problems, stats = audit_all(SPECS, DISC)
    print(f"[43] 案例层源哈希：{stats['files']} 份案例文件，元哈希 {stats['meta']} 项、"
          f"每例哈希 {stats['case']} 项")
    st_fail = selftest() if args.selftest else 0
    if problems:
        print(f"\n失败 {len(problems)} 项：")
        for p in problems:
            print(f"  × {p}")
        return 1
    if st_fail:
        return 1
    print("  √ 案例层源哈希与在盘底本逐项相符（声明路径同源）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
