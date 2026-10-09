# -*- coding: utf-8 -*-
"""命科评测框架自检：证明打分器能区分「答对 / 答错 / 未记录 / 不可跑」。

    python dev_tools/eval_selftest.py

为什么需要它：命科的评测是**新立的尺子**（此前 `evaluate.py` 根本不存在）。
一把没校准过的尺子比没有尺子更危险——它会给人"已经量过了"的错觉。
本脚本用**临时**案例（不写进案例集）逐项验证打分器的行为边界：

  1. 四柱全对 → 100
  2. 四柱错一柱 → 恰好 75（权重 24 能被 4 整除，不留取整残差）
  3. expected 未记录的维度 → 记 N/A 且**不进分母**（"只评书上明写的量"）
  4. 案例只给四柱、没给公历 → 走四柱直填起盘（chart_from_pillars），不反推公历
     （书源命例《子平真诠评注》多只有四柱；2026-09-30t 行为变更）
  5. 期望的神煞引擎没有 → 0 分（不给面子分）
  6. 期望记了调候但引擎还没这能力 → 0 分，而不是 N/A（不能把"没实现"算成"不适用"）
  7. `--verbose` 能逐例打印

口径（`AGENTS.md` 铁律三）：一切分数是古籍案例对齐分，不是现实预测命中率。
本脚本**只校验打分器行为**，不产生任何"精度"结论。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[3] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.runtime import utf8_subprocess_env  # noqa: E402

CASES = DISC / "data" / "cases" / "ming_classical_cases.json"
DT = "1990-05-20 10:30"
# 历法真值（年界立春、月界节气、儒略日日柱）：仅用于自检，不是命理判据
PILLARS = {"year": "庚午", "month": "辛巳", "day": "乙酉", "hour": "辛巳"}


def _run_eval(extra: list[str] | None = None) -> str:
    argv = [sys.executable, "scripts/evaluate.py", "--split", "tune"]
    if extra:
        argv += extra
    p = subprocess.run(argv, cwd=DISC, capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env=utf8_subprocess_env(), timeout=120)
    return (p.stdout or "") + (p.stderr or "")


def _case(cid: str, expected: dict, *, with_dt: bool = True) -> dict:
    pillars = dict(PILLARS)
    if with_dt:
        pillars["datetime"] = DT
    return {"id": cid, "book": "（框架自检，非古籍）", "location": "（框架自检）",
            "source_quote": "（框架自检用，不入库）", "pillars": pillars,
            "gender": "男", "expected": expected}


SCENARIOS = (
    ("四柱全对 → 满分 100",
     [_case("S-OK", {"pillars": PILLARS})],
     ["pillars", "1/1", "平均分 = 100.0%"], None),
    ("四柱错一柱 → 恰好 75（不留取整残差）",
     [_case("S-HALF", {"pillars": dict(PILLARS, hour="甲子")})],
     ["3/4", "平均分 = 75.0%"], None),
    ("未记录的维度记 N/A 且不进分母",
     [_case("S-GODS", {"ten_gods": {"year": "正官", "month": "七杀",
                                    "day": "比肩", "hour": "七杀"}})],
     ["ten_gods", "1/1", "n/a=1", "平均分 = 100.0%"], None),
    ("只给四柱不给公历 → 四柱直填起盘可跑（不反推公历）",
     [_case("S-NODT", {"pillars": PILLARS}, with_dt=False)],
     ["平均分 = 100.0%", "1/1"], None),
    ("期望神煞而引擎没有 → 0 分（不给面子分）",
     [_case("S-SS", {"shensha": ["不存在的贵人"]})],
     ["shensha", "平均分 = 0.0%"], None),
    ("期望调候而引擎未实现 → 0 分而非 N/A",
     [_case("S-TH", {"tiaohou": {"main": "丙", "assist": "癸"}})],
     ["tiaohou", "平均分 = 0.0%"], None),
    ("--verbose 逐例打印",
     [_case("S-V", {"pillars": PILLARS})],
     ["[tune] S-V"], ["--verbose"]),
)


def main() -> int:
    force_utf8_stdio()
    if not CASES.is_file():
        print(f"× 缺案例文件 {CASES.relative_to(DISC.parent.parent)}")
        return 2
    backup = CASES.read_text(encoding="utf-8")
    fails: list[str] = []
    try:
        for name, cases, expect, extra in SCENARIOS:
            CASES.write_text(json.dumps(
                {"schema": "yi-ming-cases/1",
                 "splits": {"tune": [c["id"] for c in cases], "holdout": []},
                 "cases": cases}, ensure_ascii=False, indent=2), encoding="utf-8")
            out = _run_eval(extra)
            missing = [s for s in expect if s not in out]
            if missing:
                fails.append(f"{name}（缺 {missing}）")
                print(f"  × {name}")
                for line in out.splitlines()[:24]:
                    print("      " + line)
            else:
                print(f"  √ {name}")
    finally:
        CASES.write_text(backup, encoding="utf-8")

    if fails:
        print(f"\n评测框架自检失败 {len(fails)}/{len(SCENARIOS)} 项：")
        for f in fails:
            print("  · " + f)
        return 1
    print(f"\n命科评测框架自检通过（{len(SCENARIOS)} 个场景）。")
    print("口径：本自检只校验打分器行为，不产生任何精度结论。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
