# -*- coding: utf-8 -*-
"""判词 ↔ 分数 同档门：报告里不许出现「判词吉 · 得分 −5.33」这种自相矛盾读数。

背景（2026-10-10 实测）：5.7 覆写链多处（行人「用神生世必归」、兄弟持世求名未绝望、
久病尚可调……皆书上有据）把 verdict 抬高一档，却**不带动 final_score**，
金标准 288 例输入集里有 **15 例** 判词比自家分数更乐观，最极端一例
「家人 · 占伯何日回」判 平吉 而得分 −5.33（差 3 档）。
step5 的收口已把这类抬升的分数一并托到所在档下界（沿用同函数内
三刑合战「保底 0.5」的既有先例；只上抬、压档类覆写一律保留）。

本门守的是**改回去**：分数被后续改动压下去而判词没跟着动时，立刻显形。

    python dev_tools/check_verdict_coherence.py
    python dev_tools/check_verdict_coherence.py --selftest   # 负例：假矛盾必须被抓到
"""
from __future__ import annotations

import sys
import argparse
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
for p in (str(DISC / "scripts"), str(DISC / "dev_tools"), str(DISC / "core")):
    if p not in sys.path:
        sys.path.insert(0, p)

# 六档序与 5.7 的阈值同源（step5.py 5.7 定性判断），不另立口径
RANK = {"大吉": 5, "吉": 4, "平吉": 3, "平凶": 2, "凶": 1, "大凶": 0}
def band_of(score: float) -> str:
    """与 step5 5.7 完全同源的分数→判词（>4.0 大吉｜≥1.0 吉｜≥−0.5 平吉｜≥−2.0 凶｜其余大凶）。
    「平凶」不由分数产生，只由覆写产生，故不出现在此表——它只会以压档形式出现，本门放行。"""
    if score > 4.0:
        return "大吉"
    if score >= 1.0:
        return "吉"
    if score >= -0.5:
        return "平吉"
    if score >= -2.0:
        return "凶"
    return "大凶"


def incoherent(rows: list[dict]) -> list[str]:
    out = []
    for r in rows:
        v, s = r.get("verdict"), r.get("score")
        if v not in RANK or not isinstance(s, (int, float)):
            continue                     # 域内专判词（下跌 / 平/不利）不属六档，放行
        want = band_of(float(s))
        if RANK[v] > RANK.get(want, 5):   # 只禁「判词比自己的分数更乐观」
            out.append(f"{r.get('case', '?')}: 判词{v}({RANK[v]}) 但得分 {s:+.2f} 属{want}"
                       f"档（差 {RANK[v] - RANK.get(want, 5)} 档）")
    return out


def selftest() -> list[str]:
    """负例：注入一条矛盾行必须被抓；两条一致行（含压档）必须放行。"""
    bad = incoherent([{"case": "T1", "verdict": "平吉", "score": -5.33}])
    ok = incoherent([{"case": "T2", "verdict": "平凶", "score": 0.5},    # 压档：判词更悲观，允许
                     {"case": "T3", "verdict": "吉", "score": 2.4},
                     {"case": "T4", "verdict": "下跌", "score": -9.0}])   # 域内专判词，放行
    problems = []
    if len(bad) != 1:
        problems.append("负例失效：注入的「平吉 @ −5.33」没被抓到")
    if ok:
        problems.append(f"假阳性：一致/压档/域内专判词被误判 → {ok[:2]}")
    return problems


def main() -> int:
    import golden
    rows = golden.fingerprint()
    n_bad = incoherent(rows)
    measured = sum(1 for r in rows if r.get("verdict") in RANK
                   and isinstance(r.get("score"), (int, float)))
    print(f"输入集 {len(rows)} 例（其中可判档 {measured} 例）→ "
          f"判词比自家分数更乐观 {len(n_bad)} 例")
    if measured == 0:
        print("× 0 例可判档——本门等于没跑，不判通过")
        return 1
    _ap = argparse.ArgumentParser(description="check_verdict_coherence：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        sp = selftest()
        for x in sp:
            print(f"  × {x}")
        print(f"  [selftest] 负例{'全部抓到' if not sp else '失效'}")
        if sp:
            return 1
    for x in n_bad[:12]:
        print(f"  × {x}")
    if not n_bad:
        print("  √ 判词与得分同档（压档类覆写按设计放行）")
    return 1 if n_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
