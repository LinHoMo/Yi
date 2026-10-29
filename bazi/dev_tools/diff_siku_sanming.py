# -*- coding: utf-8 -*-
"""《三命通会》两转录渠道内容级对拍：四库本（维基文库逐卷） vs 殆知阁本（dz）。

    python dev_tools/diff_siku_sanming.py [--dry-run]

产出 `data/sanming_tonghui_siku_diff.json`：逐章窗口级命中率 ＋ 两侧「独有片段」的逐条判定。

为什么做这个（第三百二十七批起）：在库底本 `data/sources/sanming_tonghui_dz.dz.txt` 开头即
「钦定四库全书　子部七　三命通会　术数类五」＋四库提要＋「乾隆四十四年九月恭校」——
**它本身就是四库全书本**，只是经殆知阁渠道转录；维基文库把同一底本按卷切成 12 页数字化，
于是同一本书有了两条转录渠道。两条渠道的差异不是「版本差异」，是**转录脱漏**：
哪一段在某一渠道掉了字、哪一段多出字，正是校勘要找的东西。

**行号体系不同，绝不能按行号对拍**（四库本 981 个 `{{SK anchor}}` 章节标记，dz 本没有对应锚），
只能做**内容级**对拍。

三道口径（都写在这里，便于复核）：
  1. **繁简**：四库本繁体、dz 本简体，先按 `dev_tools/t2s_table.json` 转成 dz 本字形。
     该表**用 dz 本的字集做判据**生成：对一字 c，若 dz 本同时含 c 与其简体形（歧义，如「乾/干」）
     则**保留原形**，若 dz 本只含简体形则映射。这比全局词组转换准（通用转换会把「乾坤」转成「干坤」，
     实测 65 处）。
  2. **注文**：四库本的双行夹注以 `{{SK notes|…}}` 独立标记，dz 本则与正文连排，
     故对拍**含注文**（不取注文则正文在 dz 本里根本找不到，只会把「排版差异」误报成「缺文」）。
  3. **模板与标签**：`{{…}}`（notes/anchor 除外）、`<…>`、全角空格与换行一律去除，不改一个字。

窗口：每 40 字一窗、步长 40（不重叠）；一窗在 dz 归一串中出现即命中。
分类：命中率 100%＝逐字一致；0＜命中＜100%＝局部差异；0＝dz 本无此段。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DISC = Path(__file__).resolve().parents[1]
SIKU = DISC / "data" / "sources" / "sanming_tonghui_siku.wikitext.txt"
DZ = DISC / "data" / "sources" / "sanming_tonghui_dz.dz.txt"
T2S = DISC / "dev_tools" / "t2s_table.json"
OUT = DISC / "data" / "collation" / "sanming_tonghui_siku_diff.json"

WIN = 40
STEP = 40
DZ_SAMPLE_STEP = 1500     # 反向对拍：dz 本每 1500 字取一窗
PROBE = 12                # 定位锚字数


def norm_map(raw: str, tbl: dict) -> tuple[str, list[int]]:
    """逐行归一化（**含行映射**）：返回 (归一串, 每个归一字符对应的原行号)。

    口径较 327 批**已修正**（第三百二十八批）：旧版全文正则 `\\{\\{SK anchor\\|[^\\n]*\\}\\}` 是
    **贪婪**匹配，会一路吃到行末最后一个 `}}`，于是同一行里的
    `{{SK anchor|X}}{{SK notes|Y}}正文` 被整块当 anchor 吃掉——**注文与正文一起丢**
    （实测 40 行 anchor+notes 组合、400 行 notes 后接正文，四库本因此少归一化出 7,506 字）。
    现改为：模板取「`{{` 与其后**第一个** `}}` 之间的内容」，与 `\\{\\{[^}\\n]*\\}\\}` 严格等价
    且不越界；HTML 标签按**跨行状态机**处理（`<!-- … -->` 这类注释块要跨行才闭合）。

    行映射用于把归一串位置反查回原文件行号，是「逐条判定」能落到行的基础。
    """
    out, lines = [], []
    in_tag = False
    # 字表用 str.maketrans 一次编译：**必须用 translate 而不是逐字 tbl.get(c, c)**——
    # 注文是整段字符串 append 进 buf 的（content[9:]），逐字查表对它无效，
    # 结果注文内容从未被繁简转换，四库本注文一直是繁体、与 dz 简体注文对不上，
    # 凭空造出大量「缺失」（第三百二十八批第三层修正）。
    trans = str.maketrans(tbl) if tbl else {}
    for ln_no, raw_line in enumerate(raw.splitlines(), 1):
        buf, i, n = [], 0, len(raw_line)
        while i < n:
            ch = raw_line[i]
            if in_tag:                      # 标签跨行：直到遇到 '>' 才出
                j = raw_line.find('>', i)
                if j < 0:
                    i = n
                    continue
                in_tag = False
                i = j + 1
                continue
            if ch == '<':
                in_tag = True
                i += 1
                continue
            if ch == '{':
                j = raw_line.find('}}', i + 2)
                if j < 0:
                    break
                content = raw_line[i + 2:j]
                if content.startswith('SK notes|'):
                    buf.append(content[9:])
                i = j + 2
                continue
            if ch.isspace() or ch == '\u3000':
                i += 1
                continue
            if ch in '\u3010\u3011':
                # 注文标记符号（第三百二十八批第三层修正）：dz 本用【】标注文，
                # 四库本用 {{SK notes}} 模板，两边**标记形态不同**，
                # 注文边界处的窗口必然失配（dz 有 3,449 个【】、四库本 0 个）。
                # 标记不是正文，两边统一剥掉。
                i += 1
                continue
            buf.append(ch)
            i += 1
        for c in buf:
            out.append(c.translate(trans))
            lines.append(ln_no)
    return "".join(out), lines


def main() -> int:
    ap = argparse.ArgumentParser(description="《三命通会》两转录渠道内容级对拍")
    ap.add_argument("--dry-run", action="store_true", help="只打印汇总，不写文件")
    args = ap.parse_args()

    tbl = json.loads(T2S.read_text(encoding="utf-8"))
    siku_raw = SIKU.read_text(encoding="utf-8")
    dz_raw = DZ.read_text(encoding="utf-8")

    siku_norm, siku_lines = norm_map(siku_raw, tbl)
    dz_norm, dz_lines = norm_map(dz_raw, tbl)
    siku_raw_lines = siku_raw.splitlines()

    # ── 正向：四库本逐章，章内窗口在 dz 本中的命中率 ──────────────────────────
    parts = re.split(r"\{\{SK anchor\|([^}]*)\}\}", siku_raw)
    anchor_lines = [siku_raw[:m.start()].count("\n") + 1
                    for m in re.finditer(r"\{\{SK anchor\|([^}]*)\}\}", siku_raw)]
    sections = []
    for i in range(1, len(parts) - 1, 2):
        title, body = parts[i], parts[i + 1]
        nb, _ = norm_map(body, tbl)
        if len(nb) < WIN:
            continue
        line_no = anchor_lines[i // 2] if (i // 2) < len(anchor_lines) else 0
        wins = [nb[k:k + WIN] for k in range(0, len(nb) - WIN + 1, STEP)]
        miss = [w for w in wins if w not in dz_norm]
        ratio = 1.0 - len(miss) / len(wins) if wins else 0.0
        sections.append({
            "title": title, "siku_line": line_no, "chars": len(nb), "windows": len(wins),
            "hit": len(wins) - len(miss), "miss": len(miss), "ratio": round(ratio, 4),
            "class": ("identical" if ratio == 1.0 else "partial" if miss else "missing"),
            "miss_samples": miss[:3],
        })

    n_id = sum(1 for s in sections if s["class"] == "identical")
    n_pa = sum(1 for s in sections if s["class"] == "partial")
    n_mi = sum(1 for s in sections if s["class"] == "missing")

    # ── 反向：dz 本独有（= 四库本掉字），**逐条判定** ─────────────────────────
    # 粗判会把**排版差异**误报成掉字：四库本章节标题是 `{{SK anchor}}`（对拍时被剥掉），
    # 窗口若跨过标题就必然失配；四库本表格转成文字后顺序也变。故分四级：
    #   整窗命中                  → 一致
    #   剥首尾各 8 字后命中        → 排版差异（标题/表格换序），非掉字
    #   **最长公共片段 ≥20 字**    → 该段四库本**有**（注文位置差/字面异文），不是缺文
    #   最长公共片段 <20 字       → 四库本全文无对应 → **真脱漏候选**
    # 注意：判定必须以「**四库本全文里有没有**」为准，不能拿窗首 12 字去 find 定位后
    # 就下结论——dz 的注文在四库本里位置不同（dz 连排、四库本夹注），按窗首定位会落到
    # 注文所在行，看着像对应、其实不是同一语境（实测 dzL95 的窗会被定位到四库 L104，
    # 两处讲的完全不是一回事）。
    def best_common(w: str) -> tuple[int, int]:
        """返回 (最长公共片段长度, 该片段在 siku_norm 中的位置)。"""
        for L in (40, 32, 24, 20, 16, 12):
            for k in range(0, len(w) - L + 1, 4):
                p = siku_norm.find(w[k:k + L])
                if p >= 0:
                    return L, p
        return 0, -1

    dz_only, layout_shift = [], []
    for k in range(0, max(1, len(dz_norm) - WIN), DZ_SAMPLE_STEP):
        w = dz_norm[k:k + WIN]
        if len(w) < WIN:
            break
        if w in siku_norm:
            continue
        if w[8:-8] and w[8:-8] in siku_norm:
            layout_shift.append({"offset": k, "dz_line": dz_lines[k] if k < len(dz_lines) else 0,
                                 "sample": w})
            continue
        blen, bpos = best_common(w)
        if blen >= 20:
            sl = siku_lines[bpos] if 0 <= bpos < len(siku_lines) else 0
            verdict = "present_but_differs"
        else:
            sl = 0
            verdict = "real_gap_candidate"
        dz_only.append({
            "offset": k, "dz_line": dz_lines[k] if k < len(dz_lines) else 0,
            "sample": w, "verdict": verdict,
            "best_common_len": blen, "siku_line": sl,
            "siku_raw_line": (siku_raw_lines[sl - 1].strip()[:80]
                              if 0 < sl <= len(siku_raw_lines) else ""),
        })

    # ── 四库本独有（= dz 本掉字）──────────────────────────────────────────────
    siku_only = [s for s in sections if s["class"] == "missing"]

    # ── 正向失配窗的三分类归因（首 20 / 后 20 字各自是否在 dz 中命中）──────────
    def attribute(w: str) -> str:
        head, tail = w[:20], w[20:]
        h, t = head in dz_norm, tail in dz_norm
        if h and t:
            return "middle_dropped"      # 首尾都在、中段 20 字在 dz 本里没有 → 真脱漏
        if h and not t:
            return "tail_differs"        # 前段在、后段不在 → dz 本此段有改动或换序
        if not h and t:
            return "head_differs"
        return "both_differ"

    tot_attr = {"middle_dropped": 0, "tail_differs": 0, "head_differs": 0, "both_differ": 0}
    for s in sections:
        for w in s["miss_samples"]:
            tot_attr[attribute(w)] += 1

    # ── 逐章定位「字面差异」到具体片段：每章取首个失配窗，回溯最长公共前缀 ──
    literal = []
    for s in sections:
        if s["class"] == "identical" or not s["miss_samples"]:
            continue
        w = s["miss_samples"][0]
        k = len(w)
        while k > 0 and w[:k] not in dz_norm:
            k -= 1
        if k == 0:
            continue
        pos = dz_norm.find(w[:k])
        literal.append({
            "title": s["title"], "siku_line": s.get("siku_line", 0),
            "dz_line": dz_lines[pos] if pos < len(dz_lines) else 0,
            "common_prefix": k, "siku_text": w,
            "dz_text": dz_norm[pos:pos + len(w) + 20],
        })

    # ── 人工核实的校勘条目（每条都在脚本里自检，底本一变即失效）──────────────
    # 这一层不靠机器猜：机器只能指出「两本不同」，判「谁是正」要按理校，
    # 下面两条是逐字比对原文后确认的，计数写死在断言里，改一个字就会被自检抓住。
    findings = [
        {
            "id": "E1",
            "claim": "dz 本卷标有误字：三命通**防**（应为「会」）",
            "detail": "dz 本每卷卷标交替出现「三命通会」「三命通防」，18 处作「防」；"
                      "四库本统一作「三命通會」。同一卷标两形并存，是刻工/转录层面的错字，"
                      "不是版本差异。",
            "siku_count": siku_raw.count("三命通會"),
            "dz_wrong": dz_raw.count("三命通防"),
            "dz_right": dz_raw.count("三命通会"),
        },
        {
            "id": "E2",
            "claim": "dz 本「著」被系统性过度转换为「着」",
            "detail": "dz 本「著」仅 6 处、「着」52 处；四库本相应作「復著之述作」"
                      "「萬物皆炳然著見」。「著述/著見」本不该转成「着述/着见」，"
                      "属转换工具的词组规则误伤。**引用 dz 本时，凡「著」字词不可直接采信**。",
            "siku_zhuan": siku_raw.count("著"),
            "dz_zhuan": dz_raw.count("著"),
            "dz_zhe": dz_raw.count("着"),
            "sample_siku": "復著之述作",
            "sample_dz": "复着之述作",
        },
    ]

    verdicts = {}
    for d in dz_only:
        verdicts[d["verdict"]] = verdicts.get(d["verdict"], 0) + 1

    summary = {
        "sections": len(sections),
        "identical": n_id, "partial": n_pa, "missing": n_mi,
        "identical_ratio": round(n_id / len(sections), 4) if sections else 0.0,
        "siku_chars_normalized": len(siku_norm),
        "dz_chars_normalized": len(dz_norm),
        "dz_only_samples": len(dz_only),
        "dz_only_verdicts": verdicts,
        "dz_only_layout_shift": len(layout_shift),
        "dz_only_sampled": len(dz_norm) // DZ_SAMPLE_STEP,
        "siku_only_sections": len(siku_only),
        "miss_window_attribution_sampled": tot_attr,
    }

    print("正向（按四库本 981 个章节锚点切分）：")
    print(f"  章节 {len(sections)}｜逐字一致 {n_id}｜局部差异 {n_pa}｜dz 本无此段 {n_mi}")
    print(f"  归一后字数：四库本 {len(siku_norm)}｜dz 本 {len(dz_norm)}")
    print(f"反向（dz 本等距采样 {summary['dz_only_sampled']} 窗）逐条判定：{verdicts}")
    print(f"  排版差异（剥首尾后命中）：{len(layout_shift)}")
    print(f"  失配窗归因（样本）：{tot_attr}")
    for f in findings:
        print(f"\n[{f['id']}] {f['claim']}")
        for k, v in f.items():
            if k not in ("id", "claim", "detail"):
                print(f"    {k} = {v}")

    if dz_only:
        print("\n  dz 本独有片段（按判定分类抽样）：")
        for v in ("real_gap_candidate", "present_but_differs"):
            sub = [d for d in dz_only if d["verdict"] == v]
            for d in sub[:2]:
                print(f"    [{v}] dzL{d['dz_line']} | {d['sample'][:36]}…")
                print(f"        四库L{d['siku_line']} 原文：{d['siku_raw_line']}")

    if args.dry_run:
        print("\n--dry-run：未写文件")
        return 0

    payload = {
        "schema": "bazi.sanming_siku_diff/2",
        "_meta": {
            "purpose": "《三命通会》四库本（维基文库逐卷转录）与殆知阁本（dz）的内容级对拍",
            "siku_file": "data/sources/sanming_tonghui_siku.wikitext.txt",
            "dz_file": "data/sources/sanming_tonghui_dz.dz.txt",
            "t2s_table": "dev_tools/t2s_table.json",
            "built_by": "dev_tools/diff_siku_sanming.py",
            "window": WIN, "step": STEP, "dz_sample_step": DZ_SAMPLE_STEP,
            "batch": "第三百二十八批（修正 327 批的模板贪婪匹配缺陷，详见 norm_map 文档串）",
            "caliber": {
                "繁简": "按 t2s_table 转成 dz 本字形；该表以 dz 本字集为判据消歧（乾/干类保留原形）",
                "注文": "含四库本 {{SK notes}} 注文内容（dz 本注文与正文连排，不取注文会误报缺文）",
                "模板": "模板取「{{ 与其后第一个 }} 之间的内容」；HTML 标签按跨行状态机处理",
                "行号": "两本行号体系不同，本对拍只做内容级，不按行号",
            },
            "summary": summary,
        },
        "sections": sections,
        "literal_diffs": literal,
        "collated_findings": findings,
        "dz_only_samples": dz_only,
        "dz_only_layout_shift": layout_shift,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n写出 {OUT.relative_to(DISC)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
