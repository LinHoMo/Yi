# -*- coding: utf-8 -*-
"""命·质量门：契约完整性 + 四段冒烟 + 金标准 + **对齐分下限** + **表同步门**。

    python dev_tools/check.py            # 全部检查
    python dev_tools/check.py --raise    # 把本次实测对齐分登记为新基线（确认改进后才用）
    python dev_tools/check.py --fast     # 跳过 [7] 案例评测（根门 dev_tools/check.py 默认这么调）

⚠ `--fast` 下 **[7] 分数下限门不生效**（照六爻同参数口径；根门 `dev_tools/check.py --full`
  才会不带 --fast 跑一遍）。合入前必须跑一次**不带 --fast** 的本门，否则 tune/holdout
  回退无人拦（SKILL.md）。跳过时本门会在输出里显式写明「未生效」，不假装通过。

分数口径（SKILL.md 铁律三，务必连同分数一起读）：
  [7] 的分数是**古籍案例对齐分**——引擎输出与《穷通宝鉴》《子平真诠》《滴天髓》等
  案例要点的加权一致性（strict 计分模型），用于回归审计，**衡量不了现实命中率**。
  tune n=30、holdout n=246（holdout 集合未参与本轮判据调参）。

门槛设计（SKILL.md）：
  · 基线取**实测值**，只准前进不准后退：低于 BASELINE 即判红（范式照六爻
    `liuyao/dev_tools/check.py`）。抬基线走 `--raise`，且必须在
    `docs/CHANGELOG.md` 登记理由；**下调**基线只能改本文件里的字面量（进 git diff、
    进评审），本地 `check_baseline.json` 覆盖文件一律**不得放宽**（见 `_effective_baseline`）。
  · §四.2「tune 均分无故跌破 95 即视为回归」落在**加权均分**口径上（当前 tune 100.0 /
    holdout 96.2，均 ≥95，AGENTS_TUNE_FLOOR 有机械断言兜着）。
  · 维度层不用百分比当门槛，改用**绝对命中数**（`DIM_HITS`）：当前 holdout 的
    pattern 77.8%／cong_ge 86.7% 是「满分例数/适用例数」的维度内比值（n=36／n=15，
    另有 210／231 例 N/A），不是 §四.2 说的「均分」；把它当 95 分线是口径错配。
    而百分比本身不能当回归门槛——新增案例只涨分母、必然压低百分比，拿它设线等于
    逼人调阈值或拒绝扩样。命中数则单调：引擎回归必压低它，扩案例不会。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
CORE = Path(__file__).resolve().parents[1] / "core"
for _p in (str(DISC / "scripts"), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.gate_kit import eval_metrics, run_step  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

BASELINE_FILE = DISC / "dev_tools" / "check_baseline.json"   # 本地覆盖（gitignore）
CASES_FILE = DISC / "data" / "cases" / "bazi_classical_cases.json"

# 古籍案例对齐分（加权均分 %，strict）——2026-10-09 实测登记，非预测命中率
BASELINE = {
    "tune": 100.0,        # n=30
    "holdout": 96.2,      # n=246（未参与本轮调参）
}
AGENTS_TUNE_FLOOR = 95.0  # SKILL.md 的均分硬下限；BASELINE 必须严于它

# 维度绝对命中数下限（= evaluate.py 明细里的「满分例数」；n/a 例不进分母故不影响本数）
DIM_HITS = {
    "tune": {"tiaohou": 30},
    "holdout": {"pillars": 189, "tiaohou": 19, "pattern": 28, "cong_ge": 13},
}
# 其余维度（ten_gods / hidden_stems / shensha / dayun）案例集 0 applicable，
# 如实登记在 rule_registry 的 mechanical_regression / _uncovered，不设假下限。

# 接线门比对的最小叶子长度。原取 12（只想比整句引文），代价是 nayin_quxiang.json
# 这类「性质名短语库」（227 条叶子全 <12 字、最长 8 字）被 `if not leaves: continue`
# 整份跳过——死语料反而看不见。取 4：四字名相（「从革之金」）已足够特异，不会撞进干支串里；
# 真出现「短串偶合」的假绿，宁可显式登记在 UNWIRED_CORPORA 也不靠拉长阈值来遮。
MIN_LEAF_LEN = 4


def run(cmd: list[str]) -> tuple[int, str]:
    """本门口径：cwd=学科根、60s 超时、argv 前补解释器（实现在内核 gate_kit）。"""
    return run_step(cmd, cwd=DISC, timeout=60, python=True)


def _effective_baseline() -> dict:
    """BASELINE 与本地覆盖文件合并——**覆盖文件只准抬，不准降**（防"调绿"）。"""
    merged = dict(BASELINE)
    if not BASELINE_FILE.exists():
        return merged
    local = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
    for key, value in local.items():
        floor = BASELINE.get(key)
        if isinstance(floor, (int, float)) and isinstance(value, (int, float)) \
                and value < floor:
            raise SystemExit(
                f"× {BASELINE_FILE.name} 把 {key} 基线从登记值 {floor} 降到 {value}——"
                f"本地覆盖文件不得放宽门槛。要下调基线：改本文件字面量（进 git diff）"
                f"并在 docs/CHANGELOG.md 登记理由。")
        merged[key] = value
    return merged


def _leaf_strings(obj) -> list[str]:
    """语料 JSON → 全部叶子字符串（跳过 _meta：元信息本就不进报告）。"""
    if isinstance(obj, dict):
        return [s for k, v in obj.items() if k != "_meta" for s in _leaf_strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _leaf_strings(v)]
    return [obj] if isinstance(obj, str) else []


# 已知「数据已入库、叙述层未接线」的语料：如实登记而不是静默跳过（SKILL.md
# 「任何 0 结果都要先确认不是路径解析错了」的反面——0 命中必须有名有姓地说出来）。
# 列在这里的文件一旦真的接上（命中 >0），本门**反而判红**并要求把它从表里摘掉，
# 于是这张表不会烂成「永久豁免清单」。
# ⚠️ 2026-10-09f 更新：nayin_quxiang.json 已在 narrate.py 接线（只作旁证展示、不计格不评分），
# 从 UNWIRED_CORPORA 摘除——若本门 [8] 再报它 0 命中，说明接线回归，必须立刻修。
UNWIRED_CORPORA = {
    # 当前无未接线语料（nayin_quxiang.json 已落地 2026-10-09f）。
    # 新缺口登记格式："文件名": "接线方案出处 / 待办事项",
}


def _alignment_floor(baseline: dict, fails: list[str], measured: dict,
                     fast: bool = False) -> None:
    """[7] 对齐分下限：加权均分 + 维度绝对命中数，两条各判一次（口径见模块 docstring）。"""
    print("\n[7] 古籍案例对齐分下限（strict 加权均分 + 维度命中数；非现实预测命中率）")
    if fast:
        # 不静默跳过：跳过必须写成「未生效」，否则 --fast 的门长得像全绿的门。
        print("  × 本次带 --fast：**分数下限未跑**，[7] 未生效——"
              "合入前请跑不带 --fast 的门（或 dev_tools/check.py --full）")
        return
    splits_ids: dict = {}
    if CASES_FILE.is_file():
        splits_ids = json.loads(CASES_FILE.read_text(encoding="utf-8")).get("splits") or {}
    for split in ("tune", "holdout"):
        ids = splits_ids.get(split) or []
        if not ids:
            # 空集合没有分数，也就无从证明「不低于基线」——如实判红而不是跳过：
            # 否则「删案例来凑绿」这条最省力的路永远是绿的。
            fails.append(f"{split} 分集合为空（n=0）：无分数可与基线比对，"
                         f"禁止用清空案例集的方式过门")
            print(f"  × {split} n=0 → 无法比对基线")
            continue
        eval_file = DISC / "data" / "cases" / f"eval_{split}.json"
        m = eval_metrics(split, eval_file=eval_file, cwd=DISC, model_key=None)
        if m.get("error"):
            fails.append(f"{split} 评测未跑成：{str(m['error'])[:200]}")
            print(f"  × {split} 评测失败：{str(m['error'])[:120]}")
            continue
        avg, n = m.get("avg"), m.get("n")
        floor = baseline[split]
        measured[split] = avg
        ok = avg is not None and avg >= floor - 1e-9
        print(f"  {'√' if ok else '×'} {split} 加权均分 {avg}%（n={n}，基线 ≥{floor:g}）")
        if not ok:
            fails.append(f"{split} 对齐分均分 {avg} 低于基线 {floor}（n={n}；"
                         f"分数是古籍案例对齐分，非预测率——铁律三）")
            continue
        dims = (json.loads(eval_file.read_text(encoding="utf-8")).get("results")
                or {}).get("dims") or {}
        want = DIM_HITS.get(split) or {}
        seen = {k for k, v in dims.items() if v.get("applicable")}
        for dim in sorted(set(want) | seen):
            cell = dims.get(dim) or {}
            full, applicable, rate = cell.get("full"), cell.get("applicable", 0), cell.get("rate")
            if dim in want:
                need = want[dim]
                hit_ok = full is not None and full >= need
                print(f"      · {dim:<13s} 满分 {full}/{applicable}（{rate}%）"
                      f"下限 ≥{need} {'√' if hit_ok else '×'}")
                if not hit_ok:
                    fails.append(f"{split}/{dim} 绝对命中数 {full} 低于下限 {need}"
                                 f"（适用 {applicable} 例）")
            else:
                print(f"      · {dim:<13s} 满分 {full}/{applicable}（{rate}%）"
                      f"—— 本次未设下限；扩样后请把实测命中数登记进 DIM_HITS")

def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="八字科质量门")
    ap.add_argument("--raise", dest="raise_baseline", action="store_true",
                    help="把本次实测 tune/holdout 均分写入本地基线文件（仅在确认改进后使用；"
                         "维度命中数下限 DIM_HITS 不在 --raise 范围内，改它要走代码字面量 + CHANGELOG 登记）")
    ap.add_argument("--fast", action="store_true",
                    help="跳过 [7] 案例评测（根门 dev_tools/check.py 非 --full 时自动带上；"
                         "分数下限本次不生效，输出里会明写）")
    args = ap.parse_args()
    fails: list[str] = []
    measured: dict[str, float] = {}

    # SKILL.md 的均分硬下限是「登记基线不得被调到 95 以下」的机械兜底：
    # 有人把 BASELINE["tune"] 改小凑绿时，这里先红，不用等分数跑出来。
    if BASELINE["tune"] < AGENTS_TUNE_FLOOR:
        fails.append(f"BASELINE['tune']={BASELINE['tune']} 低于 SKILL.md "
                     f"的 tune 均分硬下限 {AGENTS_TUNE_FLOOR}")

    required = [
        "SKILL.md",
        "scripts/chart.py",
        "scripts/analyze.py",
        "scripts/narrate.py",
        "scripts/render.py",
        "data/verdicts.json",
        "data/tiaohou_quotes.json",
        "data/ditian_sui.json",
        "dev_tools/check.py",
        "dev_tools/golden.py",
        "dev_tools/sync_tiaohou_engine.py",
        "dev_tools/diff_tiaohou_vs_head.py",
        "data/rules/rule_registry.json",
    ]
    for rel in required:
        if not (DISC / rel).exists():
            fails.append(f"缺 {rel}")
    print("[0] 契约文件", "√" if not fails else "×")

    code, out = run(["scripts/chart.py", "--datetime", "1990-05-20 10:30", "--gender", "男", "-o", "scratch/chart.json"])
    if code != 0:
        fails.append("chart 冒烟失败")
        print(out)
    else:
        print("[1] chart 冒烟 √")

    code, out = run(["scripts/analyze.py", "scratch/chart.json", "-o", "scratch/analyze.json"])
    if code != 0:
        fails.append("analyze 冒烟失败")
        print(out)
    else:
        a = json.loads((DISC / "scratch" / "analyze.json").read_text(encoding="utf-8"))
        con = a.get("conclusion") or {}
        # 机械标签允许；禁止「命运吉凶」总断
        if con.get("方向"):
            fails.append("analyze 不应给出命运方向总断")
        for v in con.get("verdicts") or []:
            if not isinstance(v, dict) or not v.get("basis"):
                fails.append("verdicts 须带 basis")
                break
        if not con.get("strength") or not con.get("pattern"):
            fails.append("缺 strength/pattern 机械推演")
        if not con.get("dayun"):
            fails.append("缺 dayun 大运表")
        print("[2] analyze 机械推演 √" if not any("analyze" in f or "verdicts" in f or "strength" in f or "dayun" in f or "方向" in f for f in fails) else "[2] analyze ×")

    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0 or "不是命运断言" not in out:
        fails.append("narrate 应声明非命运断言")
        print(out)
    else:
        print("[3] narrate 口径声明 √")

    code, out = run(["dev_tools/golden.py", "verify"])
    if code != 0:
        fails.append("金标准指纹漂移")
        print(out)
    else:
        print("[4] 金标准 √", out.strip())

    code, out = run(["dev_tools/regression.py"])
    if code != 0:
        fails.append("机械因子回归失败")
        print(out)
    else:
        print("[5] 机械回归 √", out.strip().splitlines()[-1] if out.strip() else "")

    # 评测器存在性 + 框架自检（八字科评测是新立的尺子，必须校准）；分数下限见 [7]
    if not (DISC / "scripts" / "evaluate.py").is_file():
        fails.append("缺 scripts/evaluate.py（八字科评测器）")
        print("[6] 评测器 ×")
    else:
        code, out = run(["dev_tools/eval_selftest.py"])
        if code != 0:
            fails.append("评测框架自检失败")
            print(out)
        else:
            print("[6] 评测框架自检 √", out.strip().splitlines()[-2]
                  if len(out.strip().splitlines()) > 1 else "")
        # tune / holdout：分数下限门（只准前进不准后退；口径见模块 docstring）
        _alignment_floor(_effective_baseline(), fails, measured, fast=args.fast)

    # [8] 语料接线：data/*.json 每个语料文件都必须真的被报告消费（否则是死语料）。
    # 叶子长度阈值曾取 12——nayin_quxiang.json 全库叶子 <12 字，整份文件被
    # `if not leaves: continue` 静默跳过，「死语料必判红」的门对它完全无感（2026-10-09 修）。
    # 现在：非空即判、0 命中即红，唯一例外是 UNWIRED_CORPORA 里**点名登记**的缺口，
    # 且登记表里的文件一旦接上反而判红（防豁免清单烂掉）。
    code, out = run(["scripts/narrate.py", "scratch/analyze.json"])
    if code != 0:
        fails.append("narrate 接线自检时跑不通")
        print("[8] 语料接线 ×")
    else:
        bad = []
        for path in sorted((DISC / "data").glob("*.json")):
            obj = json.loads(path.read_text(encoding="utf-8"))
            leaves = [s for s in _leaf_strings(obj) if len(s) >= MIN_LEAF_LEN]
            if not leaves:
                fails.append(f"{path.name}：过滤后 0 条叶子串（MIN_LEAF_LEN={MIN_LEAF_LEN} "
                             f"或整份是非文本表）——接线门看不见它，必须显式处理")
                print(f"[8] 语料接线 × {path.name}：无可比对叶子串")
                continue
            hit = sum(1 for s in leaves if s in out)
            declared = UNWIRED_CORPORA.get(path.name)
            if declared:
                if hit:
                    fails.append(f"{path.name}：已进报告 {hit}/{len(leaves)} 条，"
                                 f"却仍挂在 UNWIRED_CORPORA 豁免表里——请摘掉（登记理由：{declared}）")
                    print(f"[8] 语料接线 × {path.name}：豁免表条目已过期")
                else:
                    print(f"[8] 语料接线 · {path.name}：0/{len(leaves)} 条进报告"
                          f"——已登记缺口，不判红（{declared}）")
                continue
            if hit == 0:
                bad.append(f"{path.name}：{len(leaves)} 条语料一条未进报告（接线缺失）")
            else:
                print(f"[8] 语料接线 √ {path.name}：{hit}/{len(leaves)} 条进入报告")
        if bad:
            fails.extend(bad)
            for b in bad:
                print(f"[8] 语料接线 × {b}")

    # [9] 静态表 ↔ data 层同步（SKILL.md：不同源就必须有挂线的同步门，不靠自觉）
    code, out = run(["dev_tools/sync_tiaohou_engine.py", "--check"])
    if code != 0:
        fails.append("TIAO_HOU 引擎表与 data/tiaohou_quotes.json 不同源"
                     f"（跑 dev_tools/sync_tiaohou_engine.py 同步，不要手改表）：{out.strip()[:200]}")
        print("[9] 调候表同步 ×")
        print(out.strip()[-800:])
    else:
        print("[9] 调候表同步 √", out.strip())

    if fails:
        print("失败：", *fails, sep="\n  ")
        return 1

    if args.raise_baseline:
        if measured:
            new = dict(BASELINE)
            new.update(measured)
            BASELINE_FILE.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n",
                                     encoding="utf-8")
            print(f"基线已登记 → {BASELINE_FILE}")
            print(json.dumps(new, ensure_ascii=False))
            print("注：维度命中数下限（DIM_HITS）不在 --raise 范围，改它要走代码字面量 + "
                  "docs/CHANGELOG.md 登记（§四.4 口径变更必须写明）。")
        else:
            print("× 本次未取到任何对齐分，拒绝登记基线")
            return 1

    print("八字科质量门通过。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率（SKILL.md 铁律三）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
