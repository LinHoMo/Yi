# -*- coding: utf-8 -*-
"""按考点折叠的加权读数（#39 配套量尺）：同一考点只算一次，看分数会不会变。

`[22]` 查出全库 747 例其实只有 405 个考点（287 组重复）。重复本身是否**扭曲读数**，
不能靠嘴上说"权重变了 2–6 倍"，得把两份读数都算出来摆着比：

  · 原始口径：全部例进 `run_eval`（应与 `scripts/evaluate.py` 的门内读数一致——
    这一步是本器的自证：对不齐说明我这里复刻错了聚合，后面的折叠数一概不采信）；
  · 折叠口径：同考点只留第一例（按 id 序取，不改判准、不挑好看的）。

折叠只动**分母与权重**，不动任何一例的判词与期望值（§三.4：不许用引擎输出回填基准）。
两数若相同，说明重复组同判同分、只是行数虚胖；若不同，差值就是"重复计数的杠杆"实测值。
"""
from __future__ import annotations

import pathlib
import sys

DISC = pathlib.Path(__file__).resolve().parents[1]
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(DISC / "dev_tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import evaluate as ev  # noqa: E402
from build_tiaohou_cases import content_key  # noqa: E402  判重键唯一真值源


def fold_ids(ids: list[str], by_id: dict) -> list[str]:
    """同考点只留 id 序最小的一例（先到先得，不挑分）。"""
    seen: set[tuple] = set()
    keep: list[str] = []
    for cid in sorted(ids):
        c = by_id.get(cid)
        if c is None:
            continue
        k = content_key(c)
        if k in seen:
            continue
        seen.add(k)
        keep.append(cid)
    return keep


def score(ids: list[str], engine_out: dict, base: dict, label: str) -> dict:
    res = ev.run_eval(engine_out, base, ids, ev.WEIGHTS, ev.score_case, ev.MODEL, label, False)
    scored = [r for r in res.get("rows", []) if "dims" in r]
    for row in scored:
        for k in ev.WEIGHTS:
            if k not in row["dims"]:
                res["dims"][k]["na"] += 1
    return res


def show(res: dict, label: str) -> None:
    print(f"  [{label}] n={res.get('n')}｜加权均分 {res.get('avg')}（min {res.get('min')}／max {res.get('max')}）")
    for k, v in (res.get("dims") or {}).items():
        if v.get("applicable"):
            print(f"     {k:<14s} 满分 {v.get('full', 0)}/{v.get('applicable')}  比率 {v.get('rate')}")


def main() -> int:
    force_utf8_stdio()
    by_id = {c["id"]: c for c in ev.load_cases()}
    if not by_id:
        print("× 案例 0 条——本器等于没跑，不报任何数")
        return 1

    for split in ("tune", "holdout", "external_holdout"):
        if split == "external_holdout":
            ext = ev.load_external_store()
            ids = list((ext.get("splits") or {}).get("external_holdout") or [])
            base = {c["id"]: c for c in ext.get("cases", [])}
        else:
            ids = ev.load_ids(split)
            base = by_id
        if not ids:
            print(f"\n=== {split}：splits 里 0 例 ⇒ 无从折叠，不报数（这不是"
                  f"「无结果」，是这一片还没接进来）===")
            continue

        print(f"\n=== {split}：原始 {len(ids)} 例 ===")
        engine_out = ev.run_ids(ids, cases_by_id=base if base is not by_id else None)
        raw = score(ids, engine_out, base, f"{split}-raw")
        show(raw, "原始口径")

        kept = fold_ids(ids, base)
        print(f"  折叠后唯一考点 {len(kept)} 个（去掉 {len(ids) - len(kept)} 行重复计数）")
        fold = score(kept, engine_out, base, f"{split}-folded")
        show(fold, "折叠口径")

        if raw.get("avg") == fold.get("avg"):
            print(f"  → 均分不变（{raw.get('avg')}）：重复组同判同分，折叠只把虚胖的行数还原成考点数。")
        else:
            d = round((raw.get("avg") or 0) - (fold.get("avg") or 0), 2)
            way = "原始口径偏乐观（被重复的行恰是得分行）" if d > 0 \
                  else "原始口径偏严（被重复的行恰是失分行）"
            print(f"  → 差值 {d} 分＝重复计数的杠杆实测值，{way}；强弱以折叠数为准。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
