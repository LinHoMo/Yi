# -*- coding: utf-8 -*-
"""《增刪卜易》**dz 底本**占例采集器（B3·第三百二十九批）。

为什么要有第二个采集器：313–328 批那一路的外部案例池全部来自
`zengshan_buyi.wikitext.txt`（维基文库本）。该本已榨干——实跑
`fetch_wikisource_cases.py`：爻图块 253 个，可入外部集 50 例、方向集 31 例，
剔除计数里「无应期」107、「无占题头」79，**机器可读的六爻占例在维基文库上只有这一本**
（用 `insource:/○/` 全库搜过，命中的六爻书只有《增删卜易》各卷）。

而仓里的 `zengshan_buyi_dz.dz.txt`（另一底本，散文排印）用的是**另一套卦画记法**：
`妻财戌土″应              妻财戌土″` —— 六亲＋地支＋动爻标记（′/″）＋世应，
两列并排时左为本卦、右为变卦。本器把它解析成同一套案例结构。

**三方校验与既采集器完全同源**（V1 纳甲／V2 卦变／V3 世应），直接复用
`fetch_wikisource_cases` 的 `resolve_hex/hex_lines/palace_of/najia_branch/response_position`，
**不另造第二套口径**——基准错比基准缺更坏，宁可弃例。

产出：`data/cases/zengshan_dz_cases.json`（结构与 wikisource_cases.json 一致），
并登记分片 `zengshan_dz_prose_holdout`（有应期）与 `zengshan_dz_prose_direction`（仅方向）。

    python dev_tools/fetch_zengshan_dz_cases.py            # 采集并写盘
    python dev_tools/fetch_zengshan_dz_cases.py --report   # 只报不写（含剔除明细）
    python dev_tools/fetch_zengshan_dz_cases.py --selftest # 负例：错卦名/错动爻必须被拒
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402

ensure_kernel_on_path(__file__)
from yishu_core import symbols as sym  # noqa: E402
import fetch_wikisource_cases as W  # noqa: E402  三方校验与断语抽取全部复用它
from yishu_core.runtime import force_utf8_stdio  # noqa: E402  [20] CLI 编码红线：中文入口必须有守卫

BRANCHES = "".join(sym.EARTHLY_BRANCHES)
SRC = DISC / "data" / "sources" / "zengshan_buyi_dz.dz.txt"
# **独立文件名**：仓里已有 zengshan_dz_cases.json（维基版 21 例，ZD*）。
# 本器产出的 dz 底本案例是另一批（ZDP*），必须另起文件名——
# 首版误用了同名文件，把原 21 例覆盖掉了（329 批自曝，哨兵取数失败时才发现）。
OUT = DISC / "data" / "cases" / "zengshan_dz_prose_cases.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"

HEADER_DATE = re.compile(r"([子丑寅卯辰巳午未申酉戌亥])月\s*([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日?")
# dz 底本的变卦记法是「得X卦变Y」（Y 可不带"卦"字），维基本才是「得X之Y卦」——
# 只认"之"会把变卦列整列当成静卦，于是每个案例都撞上"无變卦却标动爻"。
HEX_PAIR = re.compile(r"得([一-龥]{1,4}?)卦?(?:之|变)([一-龥]{1,4}?)卦?(?=[，。；、\s]|$)")
HEX_ONE = re.compile(r"得([一-龥]{1,4}?)卦(?![变之])")
# 爻行 token：六亲 + 地支 + 动标(′/″) + 世/应
# 六亲必须写成**非捕获的择一**（写成字符类只会匹配到最后一个字：父母→母、兄弟→弟）——
# 这条与 core 常量 list 插值是同一类坑：字符类里放多字串必错。
YAO_TOKEN = re.compile(rf"((?:父母|兄弟|子孙|官鬼|妻财))([{BRANCHES}])([木火土金水])([′″]?)([世应]?)")
QUESTION = re.compile(r"占([^，。；]{1,18}?)得")


def parse_yao_line(line: str) -> list[dict] | None:
    """一行可能是一爻或两爻（本卦｜变卦）。解析不出 token 返回 None。"""
    toks = list(YAO_TOKEN.finditer(line))
    if not toks:
        return None
    # 「动」跟在 token 后面：本行里 token 之后的第一个「动」归该 token
    cols = []
    for t in toks:
        seg = line[t.start():t.end() + 2]
        cols.append({"six_relation": W.norm_rel(t.group(1)), "branch": t.group(2),
                     "element": t.group(3) or "", "mark": t.group(4) or "",
                     "shiyao": t.group(5) or "", "moving": "动" in seg})
    # 一行只允许一爻或两爻；更多说明这行是正文
    if len(cols) > 2:
        return None
    return cols


def find_blocks(lines: list[str]) -> list[dict]:
    """头行（含月日 + 占/得 + 卦名）后紧跟 6 行爻图的块。"""
    blocks = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if "卦" not in line or ("占" not in line and "得" not in line):
            i += 1
            continue
        md = HEADER_DATE.search(line)
        if not md:
            i += 1
            continue
        month_branch, day_gz = md.group(1), md.group(2)
        mp = HEX_PAIR.search(line)
        orig_raw = chg_raw = ""
        if mp:
            orig_raw, chg_raw = mp.group(1), mp.group(2) or ""
        else:
            mo = HEX_ONE.search(line)
            if not mo:
                i += 1
                continue
            orig_raw = mo.group(1)
        rows = []
        j = i + 1
        while j < n and len(rows) < 6:
            txt = lines[j]
            if not txt.strip():
                j += 1
                continue
            r = parse_yao_line(txt)
            # **遇到解析不了的非空行即止**：早先版本在这里 `continue`（跳过），
            # 结果把下一例的爻行当成本例——V1 只失配 6/486 就能混过去，
            # 但那 6 例的"基准"是别的卦的卦画。基准错比基准缺更坏。
            if r is None:
                break
            if rows and len(r) != len(rows[0]):
                break
            rows.append(r)
            j += 1
        if len(rows) == 6:
            blocks.append({"head": i, "end": j - 1, "rows": rows, "cols": len(rows[0]),
                           "orig_raw": orig_raw, "chg_raw": chg_raw,
                           "month_branch": month_branch, "day_gz": day_gz, "head_text": line})
        i = max(j, i + 1)
    return blocks


def _question(head_text: str) -> str:
    m = QUESTION.search(head_text)
    return ("占" + m.group(1)) if m else ""


def build(blk: dict, lines: list[str], stats: dict, dropped: list) -> dict | None:
    orig = W.resolve_hex(blk["orig_raw"])
    changed = W.resolve_hex(blk["chg_raw"]) if blk["chg_raw"] else None
    if not orig:
        stats["bad_hex_name"] += 1
        dropped.append((blk["head"], "bad_hex_name", blk["orig_raw"]))
        return None
    if blk["chg_raw"] and not changed:
        stats["bad_hex_name"] += 1
        dropped.append((blk["head"], "bad_hex_name", f"{blk['orig_raw']}之{blk['chg_raw']}"))
        return None
    if len(blk["day_gz"]) < 2:
        stats["no_day"] += 1
        return None
    if not blk["month_branch"]:
        stats["no_month"] += 1
        return None

    base = W.hex_lines(orig)
    diagram = []
    for idx, r in enumerate(blk["rows"], start=1):
        diagram.append({"position": idx, **r[0]})
    diagram.reverse()          # 底本自上爻往下 → 自下而上
    for i, it in enumerate(diagram, start=1):
        it["position"] = i
    if len(diagram) != 6 or not base:
        stats["few_lines"] += 1
        return None

    problems = []
    for it in diagram:
        want = W.najia_branch(orig, it["position"])
        if want:
            stats["v1_cmp"] += 1
            if it["branch"] != want:
                problems.append(f"V1 纳甲 {it['position']}爻 原文{it['branch']} 内核{want}")
                stats["v1_fail"] += 1
    # 动爻的取法（324 批踩坑后定案）：**字面的「動」**才是动爻标记；
    # ′/″ 是阴阳（老爻）标记，每爻都有，不能当动爻用——早先版本把 ′/″ 当动爻，
    # 于是每个案例都是"6 爻皆动"，V2 全红。
    # 两列并排时，右列是变卦列：**支不同即动**，与「動」字互校。
    txt_moving = {it["position"] for it in diagram if it.get("moving")}
    col_moving: set = set()
    if blk["cols"] >= 2:
        for idx, r in enumerate(blk["rows"], start=1):
            if len(r) >= 2 and r[0]["branch"] != r[1]["branch"]:
                col_moving.add(7 - idx)      # 底本自上而下 → 位次自下而上
    # 動字与两列支差必须**互证一致**，不一致即弃（底本自身不自洽的案例不收）——
    # 早先用并集，两边有一边错时会互相掩盖，负例都抓不住。
    if txt_moving and col_moving and txt_moving != col_moving:
        problems.append(f"V2 動字{sorted(txt_moving)} ≠ 两列支差{sorted(col_moving)}")
        stats["v2_fail"] += 1
    marks = txt_moving or col_moving
    info: dict = {}
    if changed:
        chg = W.hex_lines(changed)
        diff = {i + 1 for i, (a, b) in enumerate(zip(base, chg)) if a != b}
        stats["v2_cmp"] += 1
        if marks and marks != diff:
            problems.append(f"V2 卦变 動爻{sorted(marks)} ≠ 纳甲差集{sorted(diff)}")
            stats["v2_fail"] += 1
        info["moving"] = sorted(marks or diff)
    else:
        info["moving"] = sorted(marks)
    pal = W.palace_of(orig)
    if pal:
        palace, gen, world = pal
        info["palace"], info["generation"] = palace, gen
        tw = {it["position"] for it in diagram if it["shiyao"] == "世"}
        tr = {it["position"] for it in diagram if it["shiyao"] == "应"}
        if world:
            want_resp = W.response_position(world)
            if tw:
                stats["v3_cmp"] += 1
                if world not in tw:
                    problems.append(f"V3 世位 原文{sorted(tw)} 内核{world}")
                    stats["v3_fail"] += 1
            if tr:
                stats["v3_cmp"] += 1
                if want_resp not in tr:
                    problems.append(f"V3 应位 原文{sorted(tr)} 内核{want_resp}")
                    stats["v3_fail"] += 1
    if problems:
        stats["validate_fail"] += 1
        dropped.append((blk["head"], "validate_fail", "；".join(problems)))
        return None

    after = "".join(lines[blk["end"] + 1: blk["end"] + 24])
    after = W._clip(after)
    verdict, yq, _ig, clause = W.outcome_of(blk["head_text"] + after)
    stats["with_verdict"] += int(bool(verdict))
    stats["with_yingqi"] += int(bool(yq))
    return {"input": {"date": f"{blk['month_branch']}月{blk['day_gz']}日",
                       "question": _question(blk["head_text"])},
            "hexagram": {"original": orig, "changed": changed or "", **info},
            "expected": {"verdict": verdict or "", "use_god": "", "use_god_branch": "",
                         "use_god_position": "", "yingqi": yq or "",
                         "yingqi_branches": [], "detail": clause or ""},
            "_src": f"zengshan_buyi_dz.dz.txt L{blk['head'] + 1}"}



def run_selftest() -> int:
    """负例自证：错卦名、错動爻必须被拒，健康块必须留下。"""
    fails = []
    lines = SRC.read_text(encoding="utf-8", errors="replace").split("\n")
    blocks = find_blocks(lines)
    if not blocks:
        print("  × 采不到块，自检无从谈起")
        return 1
    # 取一个**真能成例**的块当底（不是每个块都过得了三方校验）
    def _stats():
        return {"blocks": 0, "v1_cmp": 0, "v1_fail": 0, "v2_cmp": 0, "v2_fail": 0, "v3_cmp": 0,
                "v3_fail": 0, "validate_fail": 0, "bad_hex_name": 0, "no_day": 0, "no_month": 0,
                "few_lines": 0, "with_verdict": 0, "with_yingqi": 0}

    blk = None
    blk_static = None
    for cand in blocks:
        if build(cand, lines, _stats(), []) is None:
            continue
        if cand["chg_raw"] and blk is None:
            blk = cand          # 有变卦名的块：用来做"改错必须被拒"的负例
        elif not cand["chg_raw"] and blk_static is None:
            blk_static = cand   # 静卦块：正例
    if blk is None or blk_static is None:
        print("  × 没有能成例的块（需各一个静卦与一个变卦），自检无从谈起")
        return 1

    stats = {"blocks": 0, "v1_cmp": 0, "v1_fail": 0, "v2_cmp": 0, "v2_fail": 0, "v3_cmp": 0,
             "v3_fail": 0, "validate_fail": 0, "bad_hex_name": 0, "no_day": 0, "no_month": 0,
             "few_lines": 0, "with_verdict": 0, "with_yingqi": 0}
    dropped: list = []
    # ① 健康块应留下
    got = build(blk_static, lines, stats, dropped)
    if not got:
        fails.append("健康块被拒")
    # ② 卦名换掉 → 纳甲/卦变必不合 → 必须弃
    bad = dict(blk)
    bad["orig_raw"] = "乾" if blk["orig_raw"] != "乾" else "坤"
    if build(bad, lines, stats, dropped) is not None:
        fails.append("错卦名未被拒")
    # ③ 变卦名换掉 → 纳甲差集必与動爻不符 → 必须弃（V2）
    bad2 = dict(blk)
    bad2["chg_raw"] = "乾" if blk["chg_raw"] != "乾" else "坤"
    if build(bad2, lines, stats, dropped) is not None:
        fails.append("错变卦名未被拒")
    # ④ 動字与两列支差互证：单列块无此校验，两列块上把首行的動字翻掉 → 必须弃
    if blk["cols"] >= 2:
        bad3 = dict(blk)
        bad3["rows"] = [list(r) for r in blk["rows"]]
        r0 = list(bad3["rows"][0])
        first = dict(r0[0])
        first["moving"] = not first.get("moving")
        r0[0] = first
        bad3["rows"][0] = r0
        if build(bad3, lines, stats, dropped) is not None:
            fails.append("错動爻未被拒")
    for f in fails:
        print(f"  × selftest：{f}")
    if fails:
        return 1
    print("  √ selftest：健康块留下／错卦名、错变卦名、错動爻都被拒")
    return 0

def main() -> int:
    force_utf8_stdio()          # [20]：cp936 下 argparse 的中文产物必须仍是可读 UTF-8
    ap = argparse.ArgumentParser(description="《增删卜易》dz 底本占例采集器")
    ap.add_argument("--report", action="store_true", help="只报不写")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()
    if args.selftest:
        return run_selftest()

    lines = SRC.read_text(encoding="utf-8", errors="replace").split("\n")
    blocks = find_blocks(lines)
    stats = {"blocks": len(blocks), "v1_cmp": 0, "v1_fail": 0, "v2_cmp": 0, "v2_fail": 0,
             "v3_cmp": 0, "v3_fail": 0, "validate_fail": 0, "bad_hex_name": 0,
             "no_day": 0, "no_month": 0, "few_lines": 0, "with_verdict": 0, "with_yingqi": 0}
    dropped: list = []
    cases = []
    for blk in blocks:
        c = build(blk, lines, stats, dropped)
        if c:
            cases.append(c)
    for i, c in enumerate(cases, 1):
        c["id"] = f"ZDP{i:03d}"
    print(f"块 {stats['blocks']}｜成例 {len(cases)}｜有吉凶 {stats['with_verdict']}｜有应期 {stats['with_yingqi']}")
    print(f"校验：V1 纳甲 {stats['v1_fail']}/{stats['v1_cmp']} 不合｜V2 卦变 {stats['v2_fail']}/{stats['v2_cmp']} 不合"
          f"｜V3 世应 {stats['v3_fail']}/{stats['v3_cmp']} 不合｜validate_fail {stats['validate_fail']}")
    print(f"剔除：bad_hex {stats['bad_hex_name']}｜no_day {stats['no_day']}｜no_month {stats['no_month']}｜few {stats['few_lines']}")
    if args.report:
        for d in dropped[:20]:
            print("  ·", d)
        return 0

    payload = {"_meta": {"source": "zengshan_buyi_dz.dz.txt",
                          "source_kind": "dz 底本散文排印（六亲+地支+′″+世应 两列式）",
                          "generated_by": "dev_tools/fetch_zengshan_dz_cases.py",
                          "date": date.today().isoformat(),
                          "note": "与 wikisource_cases.json 同结构；三方校验同源，不另造口径"},
               "cases": cases}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sp = json.loads(SPLITS.read_text(encoding="utf-8"))
    ids = [c["id"] for c in cases]
    sp["zengshan_dz_prose_holdout"] = [c["id"] for c in cases if c["expected"]["yingqi"]]
    sp["zengshan_dz_prose_direction"] = [c["id"] for c in cases if not c["expected"]["yingqi"]
                                         and c["expected"]["verdict"]]
    SPLITS.write_text(json.dumps(sp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"写入 {OUT.name}（{len(ids)} 例）｜有应期 {len(sp['zengshan_dz_prose_holdout'])}"
          f"｜仅方向 {len(sp['zengshan_dz_prose_direction'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
