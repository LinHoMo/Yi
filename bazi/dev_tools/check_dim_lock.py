# -*- coding: utf-8 -*-
"""维度适用数锁：受控空档维度的「带期望例数」必须与登记表逐格相等（第一百六十九批）。

    python dev_tools/check_dim_lock.py             # 实测（对拍案例文件与登记表）
    python dev_tools/check_dim_lock.py --selftest  # 加负例：证明本门抓得住

为什么需要它：`shensha`／`dayun` 的「带期望例数」是**登记过的事实**
（`data/rules/rule_registry.json` 的 ming.shensha／ming.dayun：shensha 第一百六十九批
由书证回填 5 例、其余 333 例书文 0 处提及神煞名而维持空档；dayun 仍 0 例——
书文明写顺逆／起运实测 0/338），但此前没有任何机械物守住这些数字——
于是两个方向都会静默出事：

  · 多了：有人（或某个 agent）按 §三.4 禁止的口径把 expected 由**引擎输出反推**回填，
    读数当场变成自证，而分数只会变好看，没人会红；
  · 少了：回填在一次 git 还原里静默丢失，回到空档，读数变化 0.00（第一百六十八批
    实证过这一类——214 例回填丢失而均分四舍五入后纹丝不动）。

双向都判红，解锁必须改本文件的 LOCK 字面量（进 git diff）+ `docs/CHANGELOG.md` 逐批登记
书证，这就是「空档 → 回填」唯一合法的通道（AGENTS.md §六.2 改实现必须回头改登记）。

口径：只数 `expected` 里**有没有该维的键**（数的是书写的期望，不跑引擎、不看分数），
故本门确定性、与评测产物新旧无关。锁的是「适用例数」，不是命中数——
命中数下限归 `check.py` 的 `DIM_HITS` 管。
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
for p in (str(DISC / "scripts"), str(DISC / "core")):
    if p not in sys.path:
        sys.path.insert(0, p)

import evaluate as ev  # noqa: E402

CASES = DISC / "data" / "cases" / "bazi_classical_cases.json"

# dim → {split: 必须恰好等于的「expected 带该维键的案例数」}
# 改这一行 = 解锁。改之前先在 docs/CHANGELOG.md 写清书证（哪本书哪段逐字、怎么派生），
# 并同步 rule_registry 的对应 note——三处不一致即为文实不符。
LOCK: dict[str, dict[str, int]] = {
    "shensha": {"tune": 0, "holdout": 5},
    "dayun":   {"tune": 0, "holdout": 0},
}

# dim → expected 里算「带该维键」的键名（dayun 两子项分列存放）
DIM_KEYS: dict[str, tuple[str, ...]] = {
    "shensha": ("shensha",),
    "dayun": ("dayun_direction", "dayun_start_age"),
}


def case_ids(store: dict, split: str, dim: str) -> list[str]:
    """该分片里 expected 带该维键的案例 ID（按文件内顺序）。"""
    ids: list[str] = []
    want = set(DIM_KEYS.get(dim, (dim,)))
    split_ids = set((store.get("splits") or {}).get(split) or [])
    for c in store.get("cases") or []:
        if c.get("id") not in split_ids:
            continue
        if want & set((c.get("expected") or {}).keys()):
            ids.append(c.get("id") or "?")
    return ids


def check(store: dict, lock: dict[str, dict[str, int]] | None = None) -> list[str]:
    """返回问题清单；空表 = 实测与登记逐格一致。"""
    lock = LOCK if lock is None else lock
    problems: list[str] = []
    for dim in lock:
        if dim not in ev.WEIGHTS:
            problems.append(
                f"登记维度「{dim}」不在评测维度表 {sorted(ev.WEIGHTS)} 里——"
                f"拼写错误会让本门拿 0 对 0 恒绿，必须修正 LOCK")
    for dim, per_split in lock.items():
        for split, want in per_split.items():
            if split not in (store.get("splits") or {}):
                problems.append(f"登记分片「{split}」在案例文件里不存在（splits={sorted((store.get('splits') or {}))}）")
                continue
            got = case_ids(store, split, dim)
            if len(got) > want:
                problems.append(
                    f"{dim}·{split}: 实测 {len(got)} 例带期望（{', '.join(got)}），登记为 {want}"
                    f"——超出登记的回填未经书证核对；若确有书载真值，"
                    f"改 check_dim_lock.py 的 LOCK + docs/CHANGELOG.md 登记后才准绿"
                    f"（§三.4 禁止由引擎输出反推 expected）")
            elif len(got) < want:
                problems.append(
                    f"{dim}·{split}: 实测 {len(got)} 例带期望，登记为 {want}"
                    f"——回填静默丢失（第一百六十八批同类事故：少 214 例而均分四舍五入不动）")
    return problems


def summary(store: dict) -> str:
    parts = []
    for dim, per_split in LOCK.items():
        parts.append(dim + "＝" + "、".join(
            f"{s}:{len(case_ids(store, s, dim))}/{w}"
            for s, w in per_split.items()))
    return "  ".join(parts)


def selftest() -> list[str]:
    """负例（铁律二：夹具只走临时目录，不落案例库）：
    ①登记外的回填必须点名判红；②回填丢失必须判红；③真实 LOCK 下少 1 例也要判红；
    ④维度名拼错必须判红（0 对 0 恒绿的病）。

    **夹具用等格小登记表，不用真实 LOCK**（第一百七十批修的正是这一点）：
    夹具 holdout 只放 1 例 shensha，真实 LOCK 是 5 例——拿真实 LOCK 比夹具，
    「正例不误伤」恒不可能成立（1≠5 必红），整个 selftest 会**永远失败**。
    这不是理论顾虑：169 批本门首次挂进 check.py 时就是这样，bazi 全门因它 rc=1。
    """
    fails: list[str] = []
    base = {
        "schema": "yi-bazi-cases/1",
        "splits": {"tune": ["T1"], "holdout": ["H1"]},
        "cases": [
            {"id": "T1", "split": "tune", "expected": {}},
            {"id": "H1", "split": "holdout", "expected": {"shensha": ["羊刃"]}},
        ],
    }
    with tempfile.TemporaryDirectory() as td:  # 铁律二：夹具不进 data/cases
        tmp = Path(td) / "cases.json"
        tmp.write_text(json.dumps(base, ensure_ascii=False, indent=1), encoding="utf-8")
        store = json.loads(tmp.read_text(encoding="utf-8"))

        # 夹具的 holdout 只有 1 例 shensha，与登记 5 例**不同格**——若照 LOCK 全量对拍，
        # 「正例不误伤」这一句永远不可能通过（1≠5 必判红），整个 selftest 会恒失败。
        # 故夹具另配一份等格的小登记表（1/1），只测判据行为、不测真实盘上的数。
        # ⚠ 这正是本门自己的教训形态：**夹具与登记表必须是同一套格子**，
        # 否则「全绿」是因为没比、不是因为比得过（§四.8）。
        fixture_lock = {"shensha": {"tune": 0, "holdout": 1},
                        "dayun":   {"tune": 0, "holdout": 0}}
        if check(store, fixture_lock):
            fails.append("负例失效：与登记一致的夹具被误判红（" + "; ".join(check(store, fixture_lock)) + ")")

        more = json.loads(json.dumps(base))
        more["cases"][0]["expected"]["dayun_direction"] = "forward"
        probs = check(more, fixture_lock)
        if not any("dayun·tune" in p and "T1" in p for p in probs):
            fails.append("负例失效：登记外的 dayun 回填没被点名判红")

        lost = json.loads(json.dumps(base))
        lost["cases"][1]["expected"] = {}
        probs = check(lost, fixture_lock)
        if not any("shensha·holdout" in p and "丢失" in p for p in probs):
            fails.append("负例失效：shensha 回填静默丢失没被判红")

        # 负例 D（第一百七十批补）：真实登记 LOCK 下，**少 1 例也要点名**——
        # 防「full 掉一格」这种小漂移被四舍五入/阈值吞掉（与 168 批 214 例同形、只是量小）。
        short = json.loads(json.dumps(base))
        short["cases"][1]["expected"] = {"pattern_cheng_bai": "成格"}
        probs = check(short, LOCK)
        if not any("shensha·holdout" in p and "丢失" in p for p in probs):
            fails.append("负例失效：真实 LOCK 下少 1 例（5→4）没被判红")

        typo = check(base, lock={"shenshaaa": {"tune": 0, "holdout": 1}})
        if not any("不在评测维度表" in p for p in typo):
            fails.append("负例失效：LOCK 维度名拼错没被判红（0 对 0 恒绿的病没堵住）")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description="维度适用数锁：受控空档维度的带期望例数与登记逐格相等")
    ap.add_argument("--selftest", action="store_true", help="加跑负例（证明本门抓得住）")
    args = ap.parse_args()

    if not CASES.is_file():
        print(f"× 案例文件缺失：{CASES}")
        return 2
    store = json.loads(CASES.read_text(encoding="utf-8"))
    problems = check(store)
    print(f"受控维度 {len(LOCK)} 个：{summary(store)}（实测/登记）")
    for p in problems:
        print("  ×", p)
    if not problems:
        print("  √ 实测带期望例数与登记逐格相等（多了＝未登记回填，少了＝回填静默丢失）")

    st_fail: list[str] = []
    if args.selftest:
        st_fail = selftest()
        for p in st_fail:
            print("  ×", p)
        print(f"  [selftest] 负例{'全部抓到' if not st_fail else '失效'}（4 类：登记外回填／回填丢失／真实 LOCK 少 1 例／维度名拼错）")

    if problems or st_fail:
        return 1
    print("维度适用数锁通过。解锁＝改 LOCK 字面量 + docs/CHANGELOG.md 登记书证。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
