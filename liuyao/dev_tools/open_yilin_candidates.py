# -*- coding: utf-8 -*-
"""《易林補遺》L1279 候选池：机读重建 + 第 542 批冻结假设的一次性开卷（第 543 批）。

用户授权「扩构建器覆盖面／逐例签字复核／按冻结假设开卷一次」后落地。本器做两件事：

1. **机械重建**（不写盘）：把候选池的逐字文本转成引擎可跑的案例——底本原字
   「垢」归一化到内核卦表的「姤」（照录不改字、机读值另记）、月序「五月」按
   正月建寅转月支「午」、动爻由 `case_runner.hex2yao` 从本卦／变卦逐位比较反推
   （或由「上六爻动」这类明示转成变卦）。全部由代码完成，LLM 不心算任何结论。
2. **开卷一次**：按 542 批 `preregistration` 冻结的主指标「top-1 应期支一致」
   逐例判卷。`n=3 < 30`，按冻结的 decision_rule **只报逐例红绿**，`aggregate`
   恒 null、结构里不许出现率值字段、不作任何能力声称；判卷只追加、开封只此一次。

    python dev_tools/open_yilin_candidates.py --dry-run   # 只打印逐例，不写盘
    python dev_tools/open_yilin_candidates.py --open      # 冻结口径并追加 open_result（只此一次）
    python dev_tools/open_yilin_candidates.py --verify    # 只读校验（CI root-gates 挂这个）
    python dev_tools/open_yilin_candidates.py --selftest  # 内存负例自证
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
ROOT = DISC.parent
for p in ("eval", "scripts", "core", "engine", "rules", ""):
    sys.path.insert(0, str(DISC / p) if p else str(DISC))

POOL = DISC / "data" / "cases" / "yilin_buyi_candidates.json"

import prospective as P  # noqa: E402  轻量：只读校验只需 rule_sha()

ALIAS = {'垢': '姤'}          # 底本原字 → 内核卦表规范名（引文仍照录「垢」）

# 544 批性能修正：`import case_runner` 会连带拉起 thinking_chain／
# classical_enhancements／narrate_core／yishu_core.symbols 等 9 个重型模块，
# 而 `--verify`／`--selftest` 根本不碰引擎（实测顶层 import 使只读校验 0.568s，
# 纯基线 0.266s）。改为按需加载并缓存：只读路径不再付这笔开销，
# 只有 --dry-run／--open 的机读重建才加载。判据与输出键一律未动。
_ENGINE = None


def engine():
    global _ENGINE
    if _ENGINE is None:
        import case_runner as C
        from yishu_core.symbols import HEXAGRAM_TRIGRAMS, BAGUA_LINES, EARTHLY_BRANCHES
        branch_from_yin = EARTHLY_BRANCHES[2:] + EARTHLY_BRANCHES[:2]
        seq = {s: branch_from_yin[i - 1] for i, s in enumerate(
            ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '十一', '十二'], 1)}
        _ENGINE = {"C": C, "H": HEXAGRAM_TRIGRAMS, "B": BAGUA_LINES,
                   "E": EARTHLY_BRANCHES, "SEQ": seq}
    return _ENGINE
STATUS_OPEN = "已开卷一次·逐例红绿·无率值"
FORBIDDEN_RATE_KEYS = {"rate", "accuracy", "percent", "percentage", "hit_rate",
                       "命中率", "准确率", "对齐分", "aggregate_value", "mean"}


def lines_of(name):
    e = engine()
    tri = e["H"].get(name)
    if not tri:
        return None
    upper, lower = tri
    return e["B"][lower] + e["B"][upper]


def name_of(lines):
    for n in engine()["H"]:
        if lines_of(n) == lines:
            return n
    return None


def parse_case(c: dict) -> dict | None:
    """逐字文本 → 引擎案例（纯机械，无象数解读）。"""
    t = c["hexagram_text"]
    m = re.match(r'^(.+?)之(.+?)卦$', t)
    if m:
        orig, chg = m.group(1), ALIAS.get(m.group(2), m.group(2))
        rest = ""
    else:
        e = engine()
        orig = max((n for n in e["H"] if t.startswith(n)), key=len, default=None)
        if not orig:
            return None
        rest = t[len(orig):]
        chg = None
    moving: list[int] = []
    if "皆动" in rest or "爻动" in rest:
        nums = {'初': 1, '二': 2, '三': 3, '四': 4, '五': 5, '上': 6}
        if '初二三' in rest:
            moving = [1, 2, 3]
        else:
            moving = sorted({v for k, v in nums.items() if k in rest})
        base = lines_of(orig)
        if base:
            chg = name_of([1 - b if (i + 1) in moving else b for i, b in enumerate(base)])
    e = engine()
    if orig not in e["H"]:
        return None
    if e["C"].hex2yao(orig, chg if chg != orig else None) is None:
        return None

    d = c["date_text"]
    mm = re.search(r'([正二三四五六七八九十]+)月', d)
    branch = e["SEQ"].get(mm.group(1)) if mm else None
    _, day_gz = e["C"].parse_ganzhi_hint(d)
    date_str = f'{branch}月{day_gz}日' if branch and day_gz else d
    return {
        "id": c["id"],
        "question": "占病",
        "input": {"date": date_str, "question": "占病"},
        "hexagram": {"original": orig,
                     "changed": chg if chg != orig else None,
                     "moving": sorted(set(moving))},
        "_date_str": date_str, "_orig": orig, "_chg": chg,
    }


def book_branch(c: dict) -> str | None:
    """只从「单点应期·可回指」案的书载应期句机械取地支；跨月／非单点一律不取。"""
    if c["enroll_status"] != "单点应期·可回指":
        return None
    hits = [b for b in engine()["E"] if b + "日" in c["yingqi_text"]]
    return hits[-1] if hits else None


def judge(pool: dict) -> list[dict]:
    rows = []
    for c in pool["cases"]:
        built = parse_case(c)
        rec = {"id": c["id"], "enroll_status": c["enroll_status"],
               "book_branch": book_branch(c)}
        if built is None:
            rec.update({"engine_top1": None, "engine_candidates": [],
                        "in_candidate_pool": None, "result": "不适用·机读重建失败"})
            rows.append(rec)
            continue
        r = engine()["C"].run_case(built, full=False)
        cands = [re.sub(r'日$', '', str(x)) for x in (r.get("yingqi_branches") or [])]
        top1 = cands[0] if cands else None
        rec["engine_top1"] = top1
        rec["engine_candidates"] = cands[:6]
        rec["rebuilt"] = {"date": built["_date_str"], "original": built["_orig"],
                          "changed": built["_chg"]}
        b = rec["book_branch"]
        if b is None:
            rec["in_candidate_pool"] = None
            rec["result"] = "不适用·" + c["enroll_status"]
        else:
            rec["in_candidate_pool"] = b in cands      # 仅归因线索，不是冻结主指标
            rec["result"] = "命中" if top1 == b else "未命中"
        rows.append(rec)
    return rows


def result_sha(rows: list[dict]) -> str:
    canon = json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode("utf-8")).hexdigest()[:16]


def build_open_result(pool: dict, rows: list[dict]) -> dict:
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    return {
        "opened_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "commit_at_open": commit,
        "open_count": 1,
        "scoring_rule_sha": P.rule_sha(),
        "metric_frozen": "top-1 应期支一致（542 批 preregistration 冻结；开卷后不得改指标）",
        "aggregate": None,
        "_comment": "可判 n=3 < 30，按 542 批冻结的 decision_rule 只报逐例红绿："
                    "aggregate 恒 null、结构里不许出现率值字段、不作任何能力声称。"
                    "判卷只追加、开封只此一次；in_candidate_pool 仅作排序归因线索，"
                    "不是主指标，不得据此改冻结指标。",
        "cases": rows,
        "result_sha": result_sha(rows),
    }


def check_open(pool: dict) -> list[str]:
    """只读校验：开卷记录完整、无率值、判卷未被改写、指标未被偷换。"""
    bad: list[str] = []
    pre = pool.get("preregistration") or {}
    op = pool.get("open_result")
    if pre.get("status") == STATUS_OPEN:
        if not op:
            bad.append("状态为已开卷但缺 open_result")
            return bad
        if op.get("open_count") != 1:
            bad.append("open_count 不等于 1（开封只此一次）")
        if op.get("aggregate") is not None:
            bad.append("aggregate 非 null（n<30 不许出率值）")
        if not op.get("metric_frozen") or "top-1" not in str(op.get("metric_frozen")):
            bad.append("冻结指标被改写")
        if op.get("scoring_rule_sha") != P.rule_sha():
            bad.append("scoring_rule_sha 与现场口径不符")
        rows = op.get("cases") or []
        expect_ids = [c["id"] for c in pool.get("cases", [])]
        if [r.get("id") for r in rows] != expect_ids:
            bad.append("判卷逐例 ID/顺序与候选池不符")
        if op.get("result_sha") != result_sha(rows):
            bad.append("判卷结果被改写（result_sha 不符，判卷只追加）")
        for r in rows:
            for k in FORBIDDEN_RATE_KEYS:
                if k in r:
                    bad.append(f"{r.get('id')} 出现率值字段 {k}")
            if r.get("result") not in ("命中", "未命中") and not str(r.get("result", "")).startswith("不适用"):
                bad.append(f"{r.get('id')} result 非法：{r.get('result')}")
        for k in FORBIDDEN_RATE_KEYS:
            if k in op:
                bad.append(f"open_result 出现率值字段 {k}")
    else:
        if op:
            bad.append("未开卷状态却带 open_result")
    return bad


def selftest() -> int:
    import copy
    pool = json.loads(POOL.read_text(encoding="utf-8"))
    if not pool.get("open_result"):
        print("  × selftest：需先 --open 落盘开卷记录")
        return 1
    probes = []
    probes.append(("健康副本放行", not check_open(pool)))
    p = copy.deepcopy(pool); p["open_result"]["aggregate"] = 66.7
    probes.append(("出率值被抓", bool(check_open(p))))
    p = copy.deepcopy(pool); p["open_result"]["open_count"] = 2
    probes.append(("二次开卷被抓", bool(check_open(p))))
    p = copy.deepcopy(pool); p["open_result"]["cases"][0]["result"] = "命中"
    probes.append(("判卷被改写被抓", bool(check_open(p))))
    p = copy.deepcopy(pool); p["preregistration"]["status"] = "未开卷·不入册·不出分"
    probes.append(("状态回退被抓", bool(check_open(p))))
    p = copy.deepcopy(pool); p["open_result"]["metric_frozen"] = "loose 候选池命中"
    probes.append(("偷换冻结指标被抓", bool(check_open(p))))
    p = copy.deepcopy(pool); p["open_result"]["cases"][0]["准确率"] = 1.0
    probes.append(("逐例率值字段被抓", bool(check_open(p))))
    fails = [n for n, ok in probes if not ok]
    if fails:
        for f in fails:
            print("  × selftest：" + f)
        return 1
    print(f"  √ selftest：{len(probes)} 类负例全部抓到；健康副本放行（全程内存）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="易林補遺候选池机读重建与一次性开卷")
    ap.add_argument("--dry-run", action="store_true", help="只打印逐例，不写盘")
    ap.add_argument("--open", action="store_true", help="冻结口径并追加 open_result（只此一次）")
    ap.add_argument("--verify", action="store_true", help="只读校验开卷记录")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证")
    args = ap.parse_args()
    pool = json.loads(POOL.read_text(encoding="utf-8"))

    if args.selftest:
        if selftest() != 0:
            return 1
        bad = check_open(pool)
        for b in bad:
            print("  × " + b)
        return 1 if bad else 0
    if args.verify:
        bad = check_open(pool)
        for b in bad:
            print("  × " + b)
        if bad:
            return 1
        print("  √ 开卷记录校验：一次开封、逐例红绿、无率值、判卷未改写、指标未偷换")
        return 0
    if args.dry_run:
        for r in judge(pool):
            print(f"  {r['id']} | 书载{r['book_branch'] or '—'} | top1 {r['engine_top1']} "
                  f"| 候选池含书载支 {r['in_candidate_pool']} | {r['result']}")
        return 0
    if args.open:
        if pool.get("open_result"):
            print("  × 开封只此一次：open_result 已在册，拒绝二次开卷")
            return 1
        rows = judge(pool)
        pool["open_result"] = build_open_result(pool, rows)
        pool["preregistration"]["status"] = STATUS_OPEN
        raw = POOL.read_bytes()
        text = json.dumps(pool, ensure_ascii=False, indent=2) + "\n"
        POOL.write_bytes(text.replace("\n", "\r\n").encode("utf-8")
                         if b"\r\n" in raw else text.encode("utf-8"))
        n = sum(1 for r in rows if r["result"] in ("命中", "未命中"))
        print(f"  √ 已开卷一次：{len(rows)} 案逐例判卷（可判 {n} 案，n<30 只报红绿、不出率值）")
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
