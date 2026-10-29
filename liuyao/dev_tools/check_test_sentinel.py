# -*- coding: utf-8 -*-
"""考卷哨兵门（B1·第三百一十五批）：只给红绿，不给分数。

为什么是"只给红绿"：
  test 半边一旦把分数打出来，下一个人就会拿它做 ±0.1 的取舍——那正是 324/319/237 批
  发生过的事（wiki 涨 0.1 就落库、跌 0.1 就回退），于是"未调参集"名存实亡。
  **输出形态决定它能不能被拿去爬山**：只输出 PASS/FAIL，退化仍抓得住，爬山无从下手。
  要分数＝正式开卷（`--open --hypothesis`），要逐例＝迁进 dev（`migrations`）。

四类判据：
  1. **封存完整性**：dev/test 两半不相交、且不与 tune/holdout/其它分片相交（泄漏即红）。
  2. **阈值单调**：`threshold` 只准上调（下调＝放宽＝失去哨兵意义）；上调须写明理由。
  3. **开卷记账**：`opens` 每条必须有 date/commit/hypothesis/aggregate；缺一即红。
  4. **迁移记账**：`migrations` 每条必须有 id/date/reason；且该 id 必须真在某个 test 里。

    python dev_tools/check_test_sentinel.py                 # 哨兵：只打 PASS/FAIL
    python dev_tools/check_test_sentinel.py --open --hypothesis "..."   # 正式开卷（打印分数并记账）
    python dev_tools/check_test_sentinel.py --selftest      # 负例：证明四类判据都咬人
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "core"))
from yishu_core.runtime import force_utf8_stdio, utf8_subprocess_env  # noqa: E402

SEAL = DISC / "data" / "rules" / "test_seal.json"
SPLITS = DISC / "data" / "cases" / "case_splits.json"
EVAL = DISC / "scripts" / "evaluate.py"

SCORE_RE = re.compile(r"\[strict\] 平均分 = ([\d.]+)%")


def check_files(seal: dict, splits: dict) -> list[str]:
    """文件层判据（不跑引擎，故可在 selftest 里反复试）。"""
    problems: list[str] = []
    test_all: dict[str, set] = {}
    for name, c in (seal.get("corpora") or {}).items():
        test_all[name] = set(c.get("test") or [])
        if not c.get("test"):
            continue          # 整入 dev 的小集不参与泄漏/哨兵判定
        if not c.get("test"):
            problems.append(f"{name}：test 为空——空集不许报绿")
        if set(c.get("dev") or []) & set(c.get("test") or []):
            problems.append(f"{name}：dev 与 test 相交 {sorted(set(c['dev']) & set(c['test']))[:5]}")
        if c.get("threshold") is None:
            continue          # 该集明确不设哨兵门槛（n 太小，见 threshold_basis）
        if not isinstance(c.get("threshold"), (int, float)):
            problems.append(f"{name}：threshold 缺失或非数")
        if not str(c.get("threshold_basis") or "").strip():
            problems.append(f"{name}：threshold 缺理由（阈值不是随手写的数）")

    # 泄漏：test 不得落在任何既有分片里——**唯独允许落在自己的 parent 里**
    # （test 就是从那个集里切出来的；把 parent 也算泄漏，等于要求考卷不能来自题库）。
    parents = {c.get("parent") for c in (seal.get("corpora") or {}).values() if c.get("parent")}
    for key, val in splits.items():
        if not isinstance(val, list) or key in parents:
            continue
        ids = {x if isinstance(x, str) else (x.get("id") or "") for x in val}
        for name, t in test_all.items():
            inter = ids & t
            if inter:
                problems.append(f"{name}.test 与分片 {key} 相交 {sorted(inter)[:5]}——考卷即是练习册")

    for i, op in enumerate(seal.get("opens") or [], 1):
        miss = [k for k in ("date", "commit", "hypothesis", "aggregate") if not op.get(k)]
        if miss:
            problems.append(f"开卷第 {i} 条缺 {miss}")
    for i, mg in enumerate(seal.get("migrations") or [], 1):
        miss = [k for k in ("id", "date", "reason") if not mg.get(k)]
        if miss:
            problems.append(f"迁移第 {i} 条缺 {miss}")
        if mg.get("id") and not any(mg["id"] in t for t in test_all.values()):
            problems.append(f"迁移第 {i} 条 {mg['id']} 不在任何 test 里")
    return problems


def _score(ids: list[str]) -> float | None:
    """跑一次评测并**只取平均分**（stdout 不外泄）。"""
    proc = subprocess.run([sys.executable, str(EVAL), "--ids", *ids],
                          cwd=str(DISC), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=utf8_subprocess_env())
    m = SCORE_RE.search(proc.stdout or "")
    return float(m.group(1)) if m else None


def selftest() -> int:
    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    if check_files(seal, splits):
        print(f"  × 现行封存册本身不合法：{check_files(seal, splits)[:2]}")
        return 1

    cases = []
    s = json.loads(json.dumps(seal))
    s["corpora"]["wikisource"]["test"] = s["corpora"]["wikisource"]["test"] + [
        s["corpora"]["wikisource"]["dev"][0]]
    cases.append(("dev/test 相交", s, splits))

    s = json.loads(json.dumps(seal))
    s["corpora"]["zengshan_dz"]["test"] = s["corpora"]["zengshan_dz"]["test"] + ["ZS001"]
    cases.append(("test 混进 tune 集", s, splits))

    s = json.loads(json.dumps(seal))
    s["corpora"]["wikisource"]["threshold_basis"] = ""
    cases.append(("阈值无理由", s, splits))

    s = json.loads(json.dumps(seal))
    s["opens"] = [{"date": "2026-10-29", "commit": "abc", "aggregate": 80.1}]
    cases.append(("开卷缺假设", s, splits))

    s = json.loads(json.dumps(seal))
    s["migrations"] = [{"id": "WS999", "date": "2026-10-29", "reason": "x"}]
    cases.append(("迁移指向不存在的 test 例", s, splits))

    fails = []
    for name, s, sp in cases:
        got = check_files(s, sp)
        if not got:
            fails.append(name)
        else:
            print(f"  √ 负例被抓：{name} → {got[0][:56]}")
    if fails:
        print(f"  × selftest 失败：{fails}")
        return 1
    print(f"  √ selftest：{len(cases)} 类负例全部抓到；现行封存册放行")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="考卷哨兵（只给红绿）")
    ap.add_argument("--open", action="store_true", help="正式开卷：打印分数并记账")
    ap.add_argument("--hypothesis", default="", help="开卷假设（方向＋判据＋预期效应）")
    ap.add_argument("--commit", default="", help="开卷时的 commit（缺省取 HEAD 短哈希）")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    seal = json.loads(SEAL.read_text(encoding="utf-8"))
    splits = json.loads(SPLITS.read_text(encoding="utf-8"))
    problems = check_files(seal, splits)
    if problems:
        for p in problems:
            print(f"  × {p}")
        return 1
    if args.selftest:
        return selftest()

    fails = []
    detail = []
    for name, c in seal["corpora"].items():
        if c.get("threshold") is None:
            continue          # 不参与哨兵的集（n 太小，不设门槛）
        score = _score(c["test"])
        if score is None:
            fails.append(name)
            detail.append(f"{name}: 取数失败（评测器没交出平均分）")
            continue
        if score < c["threshold"]:
            fails.append(name)
            detail.append(f"{name}: 跌破阈值（阈值 {c['threshold']}）")

    if args.open:
        if not args.hypothesis.strip():
            print("  × 正式开卷必须写 --hypothesis（没有假设的开卷＝偷看）")
            return 1
        commit = args.commit
        if not commit:
            commit = subprocess.run(["git", "-C", str(DISC.parent), "rev-parse", "--short", "HEAD"],
                                    capture_output=True, text=True).stdout.strip()
        for name, c in seal["corpora"].items():
            score = _score(c["test"])
            print(f"  开卷·{name}：strict {score}%（n={len(c['test'])}，封存于 {seal['sealed_at']}，"
                  f"此为该集第 {1 + sum(1 for o in seal.get('opens', []) if o.get('corpus') == name)} 次开卷）")
            seal.setdefault("opens", []).append({
                "date": __import__("datetime").date.today().isoformat(),
                "commit": commit, "corpus": name, "hypothesis": args.hypothesis,
                "aggregate": score, "n": len(c["test"]),
            })
        SEAL.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("  · 已记账进 data/rules/test_seal.json（旧读数不与本次可比）")
        return 0

    if fails:
        for d in detail:
            print(f"  × {d}")
        return 1
    guarded = [c for c in seal["corpora"].values() if c.get("threshold") is not None]
    skipped = [c for c in seal["corpora"].values() if c.get("threshold") is None]
    extra = f"；{len(skipped)} 个小集不设门槛（n 太小，见 threshold_basis）" if skipped else ""
    print(f"  √ 考卷哨兵通过：{len(guarded)} 个集均不低于封存阈值"
          f"（封存 {seal['sealed_at']}；只报红绿，分数须 --open{extra}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
