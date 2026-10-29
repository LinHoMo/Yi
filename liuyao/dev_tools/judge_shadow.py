# -*- coding: utf-8 -*-
"""判定器影子对拍（A3·第三百一十七批）：判定器 vs 现行 verdict vs 书载方向。

**为什么是影子**：把 27 处覆写换成 9 格是改判，改判要按 AGENTS §四 出两集读数并逐格对拍。
在看清"换掉之后会往哪边动"之前就动手，等于用一次提交赌 300 批的积累。
所以本器只做一件事：**把三方的方向摆在一张表上**——

  · `现行`：`step5` 的 verdict 经 `verdict_map` 折成三态（成/滞/不成）
  · `判定器`：`scripts/judge.py` 的 9 格产出
  · `书载`：案例 `expected.verdict` 折成三态（没有书载答案的例不参与这一列）

读法：`一致率`只说明"换掉会动多少"，**不说明谁更对**；谁更对看"与书载同向"那两列。
口径：全部是**古籍案例对齐**，不是现实命中率（AGENTS §一.3）。

    python dev_tools/judge_shadow.py                 # 四个集全跑
    python dev_tools/judge_shadow.py --split tune    # 单集
    python dev_tools/judge_shadow.py --diff          # 只列分歧例
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(DISC / "core"))
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

import case_runner  # noqa: E402
from judge import judge_with_overlay as judge  # noqa: E402  九格 + 题类覆盖

TABLE = DISC / "data" / "rules" / "judgment_table.json"
SEAL = DISC / "data" / "rules" / "test_seal.json"
# 分片 → 封存册里的集名（只有这两集有考卷；其余集本身就是开发/回归集）
SEAL_CORPUS = {"wikisource_holdout": "wikisource", "zengshan_dz_holdout": "zengshan_dz",
               "wikisource_direction": "wikisource_direction",
               "zengshan_dz_prose_holdout": "zengshan_dz_prose",
               "zengshan_dz_prose_direction": "zengshan_dz_prose"}
SPLITS = ("tune", "holdout", "wikisource_holdout", "zengshan_dz_holdout", "wikisource_direction",
          "zengshan_dz_prose_holdout", "zengshan_dz_prose_direction")
DIRS = ("成", "滞", "不成")


def _dir_of(label: str, vmap: dict) -> str | None:
    v = vmap.get(str(label or "").strip())
    return v.get("direction") if v else None


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="判定器影子对拍（不改判）")
    ap.add_argument("--split", choices=SPLITS, action="append")
    ap.add_argument("--diff", action="store_true", help="只列分歧例")
    ap.add_argument("--dev-only", action="store_true",
                    help="只跑封存册的 dev 半边（判据开发必须在 dev 上做，test 不许看）")
    ap.add_argument("--half", choices=("dev", "test"), default="dev",
                    help="跑哪一半（默认 dev；test 半边须凭 --open 一次性开封）")
    ap.add_argument("--open", action="store_true",
                    help="正式开封：跑 test 半边并把结果记账进封存册（须先预注册）")
    args = ap.parse_args()
    vmap = json.loads(TABLE.read_text(encoding="utf-8"))["verdict_map"]
    splits = args.split or list(SPLITS)

    for split in splits:
        ids = case_runner.load_ids(split)
        if split in SEAL_CORPUS:
            seal = json.loads(SEAL.read_text(encoding="utf-8"))
            half = "test" if (args.half == "test" or args.open) else "dev"
            pool = set(seal["corpora"][SEAL_CORPUS[split]][half]) or set(seal["corpora"][SEAL_CORPUS[split]]["dev"])
            ids = [i for i in ids if i in pool]
        by_id = {c["id"]: c for c in case_runner.load_cases()}
        agree = n = 0
        ov_hit = 0
        skipped = 0
        cur_hit = judge_hit = exp_n = 0
        conf = Counter()
        diffs = []
        errs = 0
        for cid in ids:
            case = by_id.get(cid)
            if not case:
                continue
            try:
                row = case_runner.run_case(case, full=True)
            except Exception:
                errs += 1
                continue
            j = judge(row["_full"])
            ov_hit += int(bool(j.get("overlay")))
            cur = _dir_of(row.get("verdict"), vmap)
            exp = _dir_of((case.get("expected") or {}).get("verdict"), vmap)
            n += 1
            conf[(cur, j["direction"])] += 1
            if cur == j["direction"]:
                agree += 1
            else:
                diffs.append((cid, row.get("verdict"), j["cell"], j["why"]))
            if exp and j.get("direction") is not None:
                exp_n += 1
                cur_hit += int(cur == exp)
                judge_hit += int(j["direction"] == exp)
            elif exp:
                skipped += 1

        if args.diff:
            print(f"\n═ {split}：{len(diffs)} 例分歧 ═")
            for d in diffs:
                print(f"  {d[0]}  现行={d[1]:6s} → 判定器={d[2]:5s}  {d[3]}")
            continue

        print(f"\n═ {split}（n={n}，引擎错 {errs}）═")
        print(f"  题类覆盖命中：{ov_hit}/{n} 例（其余走九格）")
        print(f"  现行 vs 判定器 方向一致：{agree}/{n} = {agree * 100 / max(n, 1):.1f}%"
              f"（不一致即「换掉会动」的规模）")
        if exp_n:
            print(f"  与书载方向同向：现行 {cur_hit}/{exp_n} = {cur_hit * 100 / exp_n:.1f}%"
                  f" ｜ 判定器 {judge_hit}/{exp_n} = {judge_hit * 100 / exp_n:.1f}%")
        if skipped:
            print(f"  轴不适用（时间/价势题，不参与吉凶轴）：{skipped} 例（现行与判定器同口径排除）")
        print("  迁移矩阵（行=现行，列=判定器）：")
        print("        " + "".join(f"{d:>8s}" for d in DIRS))
        for a in DIRS:
            row = "".join(f"{conf.get((a, b), 0):>8d}" for b in DIRS)
            print(f"    {a:>4s}" + row)
        if diffs:
            print(f"  分歧 {len(diffs)} 例（--diff 看逐例）：" + "、".join(d[0] for d in diffs[:8])
                  + ("…" if len(diffs) > 8 else ""))

    if args.dev_only:
        print("\n（--dev-only：wiki/dz 只跑 dev 半边；test 半边未参与，见 data/rules/test_seal.json）")
    # ── 正式开封：一次性跑封存的 test 半边并记账 ──
    if args.open:
        seal = json.loads(SEAL.read_text(encoding="utf-8"))
        pre = seal.get("judge_preregistration") or {}
        if not pre:
            print("  × 没有预注册：开封前须先在 test_seal.json 的 judge_preregistration 写明假设与判据")
            return 1
        if seal.get("judge_opens"):
            print(f"  × 已经开过卷了（{len(seal['judge_opens'])} 次）：考卷不重复开封")
            return 1
        tot_j = tot_c = tot_n = 0
        per = {}
        for split in ("wikisource_holdout", "zengshan_dz_holdout", "wikisource_direction"):
            ids = case_runner.load_ids(split)
            sc = seal["corpora"][SEAL_CORPUS[split]]
            ids = [i for i in ids if i in set(sc["test"])]
            by = {c["id"]: c for c in case_runner.load_cases()}
            j_hits = c_hits = n = 0
            for cid in ids:
                case = by.get(cid)
                if not case:
                    continue
                exp = (case.get("expected") or {}).get("verdict")
                if not exp:
                    continue
                row = case_runner.run_case(case, full=True)
                jj = judge(row["_full"])
                if jj.get("direction") is None:
                    continue
                cur = _dir_of(row.get("verdict"), vmap)
                gd = _dir_of(exp, vmap)
                if gd is None:
                    continue
                n += 1
                j_hits += int(jj["direction"] == gd)
                c_hits += int(cur == gd)
            per[split] = {"judge": j_hits, "current": c_hits, "n": n}
            tot_j += j_hits
            tot_c += c_hits
            tot_n += n
        rec = {"date": __import__("datetime").date.today().isoformat(),
               "hypothesis": pre.get("hypothesis"), "judge_version": pre.get("judge_version"),
               "per_corpus": per, "judge": f"{tot_j}/{tot_n}", "current": f"{tot_c}/{tot_n}"}
        seal.setdefault("judge_opens", []).append(rec)
        SEAL.write_text(json.dumps(seal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\n══ 一次性开封（test 半边 · 预注册假设已记）══")
        for k, v in per.items():
            print(f"  {k:26s} 判定器 {v['judge']}/{v['n']} ｜ 现行 {v['current']}/{v['n']}")
        print(f"  合计：判定器 {tot_j}/{tot_n} = {tot_j * 100 / max(tot_n, 1):.1f}%"
              f" ｜ 现行 {tot_c}/{tot_n} = {tot_c * 100 / max(tot_n, 1):.1f}%")
        print(f"  决策规则：{pre.get('decision_rule')}")
        print("  · 已记账进 data/rules/test_seal.json（judge_opens）")
        return 0

    print("\n注：以上为**古籍案例对齐**口径，不是现实预测命中率；判定器仍处影子模式，"
          "未参与 verdict 计算（放行须另批走 §四）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
