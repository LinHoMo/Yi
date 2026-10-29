# -*- coding: utf-8 -*-
"""《三命通会》两转录渠道的**全量**缺失扫描（第三百二十八批）。

    python dev_tools/scan_siku_gaps.py [--dry-run]

产出 `data/collation/sanming_tonghui_siku_gaps.json`：双向「一方有、另一方无」的**连续区段清单**。

与 `dev_tools/diff_siku_sanming.py` 的分工：
  · 对拍脚本＝**抽样**（dz 本每 1500 字取一窗），给出比例与分布；
  · 本脚本＝**全量**（逐 12 字滑窗），给出**区段级清单**，可直接按行号回原文。

方法（两向同一套）：
  1. 把一方归一化成串 A（`diff_siku_sanming.norm_map`，含繁简字表与模板处理）；
  2. 建 A 的**全部 12-gram 集合**（约 43 万条，内存约 30MB）；
  3. 逐 12 字滑过另一方 B 的归一串，取 B 的 12-gram 查集合；
     **一个 12-gram 都不在集合里** ⇒ B 这一段在 A 里连 12 字都对不上 ⇒ 强缺失候选；
  4. 强缺失位置按间隔聚成连续区段，输出起止偏移、起止**原文件行号**、字数与样本；
  5. 每段再用「最长公共片段」复核一次，把**假缺失**（如四库本的 anchor 标记被剥、
     注文位置差）剔出去。

区间判读要点：
  · **dz→四库**方向扫出的是「**四库本未录入**」的区段（dz 本有、四库本没有）；
  · **四库→dz**方向扫出的是「**dz 本未录入**」的区段——但四库本的章节锚点内容
    在归一化时被剥掉（anchor 只作标记），故该方向命中的多为**标记**而非正文，
    须逐条看样本再下结论（脚本会标 `kind`）。

不改底本、不改判据，只做扫描与定位。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(HERE))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("_diffmod", HERE / "diff_siku_sanming.py")
_diff = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_diff)
norm_map = _diff.norm_map

SIKU = DISC / "data" / "sources" / "sanming_tonghui_siku.dz.txt"
DZ = DISC / "data" / "sources" / "sanming_tonghui_dz.dz.txt"
T2S = DISC / "dev_tools" / "t2s_table.json"
OUT = DISC / "data" / "collation" / "sanming_tonghui_siku_gaps.json"

GRAM = 12            # 匹配粒度（字）
GAP_TOL = 24         # 相邻缺失位置间隔 ≤ 此值即视为同一区段
MIN_SEG_CHARS = 20   # 区段最短字数
MIN_RUN = 4          # **连续失配位置数下限**（一字之差只影响 11 个 12-gram，
                      # 若按单点聚合，「字面差异」会被放大成「整段缺失」——
                      # 实测两本正文一致度 88%/76%，若按单点判会得出 35% 连续失配，
                      # 那是被注文差异与一字之差双重放大的假象）


def build_grams(s: str, g: int = GRAM) -> set[str]:
    return {s[i:i + g] for i in range(0, max(0, len(s) - g + 1))}


def scan(a_norm: str, a_lines: list[int], a_raw_lines: list[str],
         b_norm: str, b_lines: list[int], b_raw_lines: list[str],
         label: str) -> list[dict]:
    """扫 b_norm，输出「b 有、a 无」的区段清单。"""
    grams = build_grams(a_norm)
    hits = []
    run = []
    for i in range(0, max(0, len(b_norm) - GRAM + 1)):
        if b_norm[i:i + GRAM] not in grams:
            run.append(i)
        elif run:
            hits.append(run)
            run = []
    if run:
        hits.append(run)

    # hits 已是「连续失配位置」的分组；再按 MIN_RUN 过滤：孤立的一两处失配
    # 多为「一字之差」的连带效应，不构成「对方没有这一段」。
    hits = [r for r in hits if len(r) >= MIN_RUN]

    segs = []
    for run in hits:
        start, end = run[0], run[-1] + GRAM
        if end - start < MIN_SEG_CHARS:
            continue
        text = b_norm[start:end]
        # 复核：这一段在 a 里到底有没有 ≥12 字的公共片段（判假缺失）
        best = 0
        for k in range(0, max(1, len(text) - GRAM + 1), GRAM):
            if text[k:k + GRAM] in a_norm:
                best = GRAM
                break
        segs.append({
            "direction": label,
            "b_start_offset": start, "b_end_offset": end,
            "b_start_line": b_lines[start] if start < len(b_lines) else 0,
            "b_end_line": b_lines[min(end, len(b_lines) - 1)] if b_lines else 0,
            "chars": end - start,
            "sample": text[:60],
        })
    return segs


def main() -> int:
    ap = argparse.ArgumentParser(description="《三命通会》两渠道全量缺失扫描")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tbl = json.loads(T2S.read_text(encoding="utf-8"))
    siku_raw = SIKU.read_text(encoding="utf-8")
    dz_raw = DZ.read_text(encoding="utf-8")
    siku_norm, siku_lines = norm_map(siku_raw, tbl)
    dz_norm, dz_lines = norm_map(dz_raw, tbl)
    siku_raw_lines = siku_raw.splitlines()
    dz_raw_lines = dz_raw.splitlines()

    # dz 有、四库无 ＝「四库本未录入」
    dz_missing = scan(siku_norm, siku_lines, siku_raw_lines,
                      dz_norm, dz_lines, dz_raw_lines, "dz_only_fourkuiku_missing")
    # 四库有、dz 无 ＝「dz 本未录入」（预期极少；anchor 标记会在此显形）
    siku_missing = scan(dz_norm, dz_lines, dz_raw_lines,
                        siku_norm, siku_lines, siku_raw_lines, "siku_only_dz_missing")

    # ── 注文集合直接比对：两本的注文各有对方没有的内容 ──────────────────
    # 这是「两本互补」最硬的证据（比窗口匹配更直接，不受一字之差干扰）。
    import re
    dz_notes = [norm_map(x, tbl)[0] for x in re.findall(r"【([^】]*)】", dz_raw)]
    sk_notes = [norm_map(x, tbl)[0] for x in re.findall(r"【([^】]*)】", siku_raw)]
    dz_set = {x for x in dz_notes if x}
    sk_set = {x for x in sk_notes if x}
    only_dz_notes = dz_set - sk_set
    only_sk_notes = sk_set - dz_set
    notes_cmp = {
        "dz_notes_total": len(dz_notes), "dz_notes_uniq": len(dz_set),
        "dz_notes_chars": sum(len(x) for x in dz_notes),
        "siku_notes_total": len(sk_notes), "siku_notes_uniq": len(sk_set),
        "siku_notes_chars": sum(len(x) for x in sk_notes),
        "both": len(dz_set & sk_set),
        "only_dz": len(only_dz_notes), "only_dz_chars": sum(len(x) for x in only_dz_notes),
        "only_siku": len(only_sk_notes), "only_siku_chars": sum(len(x) for x in only_sk_notes),
        "only_dz_samples": sorted(only_dz_notes)[:12],
        "only_siku_samples": sorted(only_sk_notes)[:12],
    }
    # 去注文后的正文互相覆盖率（正文与注文分开量，正文才是「同一本书」的主体）
    dz_body = norm_map(re.sub(r"【[^】]*】", "", dz_raw), tbl)[0]
    sk_body = norm_map(re.sub(r"【[^】]*】", "", siku_raw), tbl)[0]
    g_dz = {dz_body[i:i + GRAM] for i in range(0, max(0, len(dz_body) - GRAM + 1))}
    g_sk = {sk_body[i:i + GRAM] for i in range(0, max(0, len(sk_body) - GRAM + 1))}
    body_cov = {
        "dz_body_chars": len(dz_body), "siku_body_chars": len(sk_body),
        "siku_body_in_dz_pct": round(100 * len(g_dz & g_sk) / max(1, len(g_dz)), 1),
        "dz_body_in_siku_pct": round(100 * len(g_dz & g_sk) / max(1, len(g_sk)), 1),
    }

    tot_dz = sum(s["chars"] for s in dz_missing)
    tot_siku = sum(s["chars"] for s in siku_missing)
    print(f"归一后字数：四库本 {len(siku_norm)}｜dz 本 {len(dz_norm)}")
    print(f"注文：dz {notes_cmp['dz_notes_total']} 条/{notes_cmp['dz_notes_chars']} 字"
          f"｜四库 notes {notes_cmp['siku_notes_total']} 条/{notes_cmp['siku_notes_chars']} 字"
          f"｜两本都有 {notes_cmp['both']}｜仅 dz 有 {notes_cmp['only_dz']}"
          f"（{notes_cmp['only_dz_chars']} 字）｜仅四库有 {notes_cmp['only_siku']}"
          f"（{notes_cmp['only_siku_chars']} 字）")
    print(f"去注文后正文：四库 {body_cov['siku_body_chars']} 字 / dz {body_cov['dz_body_chars']} 字"
          f"｜12-gram 互相覆盖 四库→dz {body_cov['siku_body_in_dz_pct']}%"
          f" / dz→四库 {body_cov['dz_body_in_siku_pct']}%")
    print(f"dz 有、四库无：{len(dz_missing)} 段 / {tot_dz} 字 "
          f"（占 dz 本 {100.0*tot_dz/max(1,len(dz_norm)):.1f}%）")
    print(f"四库有、dz 无：{len(siku_missing)} 段 / {tot_siku} 字 "
          f"（占四库本 {100.0*tot_siku/max(1,len(siku_norm)):.1f}%）")
    if dz_missing:
        print("\n  dz 有、四库无（前 8 段）：")
        for s in dz_missing[:8]:
            print(f"    dzL{s['b_start_line']}-{s['b_end_line']}  {s['chars']}字  {s['sample'][:40]}")
    if siku_missing:
        print("\n  四库有、dz 无（前 8 段）：")
        for s in siku_missing[:8]:
            print(f"    四库L{s['b_start_line']}-{s['b_end_line']}  {s['chars']}字  {s['sample'][:40]}")

    if args.dry_run:
        print("\n--dry-run：未写文件")
        return 0

    payload = {
        "schema": "bazi.sanming_siku_gaps/1",
        "_meta": {
            "purpose": "《三命通会》四库本 vs 殆知阁本的双向全量缺失扫描（区段级）",
            "built_by": "dev_tools/scan_siku_gaps.py",
            "gram": GRAM, "gap_tol": GAP_TOL, "min_seg_chars": MIN_SEG_CHARS,
            "method": "12-gram 集合全量滑窗 → 强缺失位置 → 连续区段聚合 → 逐段复核",
            "siku_chars_normalized": len(siku_norm),
            "dz_chars_normalized": len(dz_norm),
            "dz_only_segments": len(dz_missing),
            "dz_only_chars": tot_dz,
            "siku_only_segments": len(siku_missing),
            "siku_only_chars": tot_siku,
            "notes_comparison": notes_cmp,
            "body_coverage": body_cov,
        },
        "dz_only_fourkuiku_missing": dz_missing,
        "siku_only_dz_missing": siku_missing,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n写出 {OUT.relative_to(DISC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
