# -*- coding: utf-8 -*-
"""合绊极性门：**同一条「用神/忌神 × 日/月」合，两层不得反号**。

为什么需要它（第三百六十四批·六爻欠账，实测抓到的真缺陷）：
`effects.analyze_day_month_bonding`（step5 的"日月合"）对**用神**无条件套
《卜筮正宗》「用神合日切近有力、合月事必成就」记 +0.5／+0.4，而同一条合在
`step4` 贪合忘生克里被判「用神被合绊，暂受阻滞」−0.2。两层反号、两边都进总分，
一条**合绊**净成 +0.3 的加分项。reg_02（占升官·官鬼亥水动而逢日辰寅合、
古典断凶）就是这样被抬到 +0.18「平吉」的——而用神旺衰 0.50「弱」、
动变净效应 −0.35，其余各项合计也是负的，唯独这一项是正。

书证（底本逐字，《增删卜易》源L738，动静两式并列在同一句里）：
  「静而逢合，谓之合起。动而逢合，合谓之合绊。」
  「爻静或与日月动爻合者得合而起。即使爻值休囚亦有旺相之意。」
  「爻动或与日月动爻合者谓之动逢合而绊住，反不能动之意。」
即"切近有力"是**静爻合起**的说法，用神自己动的时候根本不适用。
本函数早已对**忌神**做了动静分计（第两百八十四批，源L1480/L738/L3152），
却漏了用神那一半——本门守的就是"漏掉的那一半不许长回来"。

同源先例：`step4.py` 4.3c 一节（进退神曾在两层重复计分且符号反向，
忌神越化进分数越高、方向判词随之翻吉）就是同一类病，修法同为「数值只走一条通道」。

    python dev_tools/check_bond_polarity.py               # 全量对账（128 路探针）
    python dev_tools/check_bond_polarity.py --selftest    # 负例：反号必须被抓到
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
# 第五百零八批升格：engine/ 在学科根下（不在 scripts/），`import engine` 需学科根入路径。
sys.path[:0] = [str(DISC / "engine" / "pipeline"), str(DISC), str(DISC / "scripts"),
                str(DISC / "dev_tools"), str(DISC / "core")]

# 探针集：64 卦 ×（静卦／双动）× 1 个时刻。双动那一路专门制造"用神自己也动"的盘面，
# 静卦那一路制造"用神静而逢日月合"的盘面——两式都要跑到，门才有意义。
TIMES = ["2024-02-05 10:30", "2026-09-22 23:40"]
QUESTIONS = ["占求财", "占病", "占行人", "占婚姻", "占讼", "占失物",
             "占父病", "占夫外出", "占妻胎安否", "占伯何日回", "占子久病",
             "占升遷", "占候文書"]

# step4 贪合忘生克的形态 → 它对用神/忌神那一支的符号含义
_GREEDY_SIGN = {
    "用神被合": -1,        # 合绊：阻滞，为负
    "忌神贪合忘克": +1,    # 忌被合住不克用，为正
    "原神贪合忘生": -1,    # 原神被合住不生用，为负
}
# step5 日月合的 bond 文本 → 说的是谁（用神／忌神）
_SUBJECT_OF = (("忌神", "忌神"), ("用神", "用神"))


def _subject(bond: str) -> str:
    for key, subj in _SUBJECT_OF:
        if key in str(bond):
            return subj
    return ""


def violations(ug_moving: bool, s4_issues: list, dmb_findings: list) -> list[str]:
    """返回违规说明；空列表＝本例合规。

    三条判据（都只判"符号"，不判"大小"——量级归各层自己，本门不替它们定价）：
      A 用神动而逢日月合＝合绊，step5 的用神项不得为正（书证源L738「动逢合而绊住」）；
      B 用神静而逢日月合＝合起，step5 的用神项不得为负（同句「静而逢合，谓之合起」）；
      C 跨层同号：step4 对某支判了符号 s，step5 对同一支的项不得取 −s。
    """
    out: list[str] = []
    dmb = [f for f in (dmb_findings or []) if isinstance(f, dict)]
    s4 = [i for i in (s4_issues or []) if isinstance(i, dict)]

    for f in dmb:
        bond = str(f.get("bond") or "")
        subj = _subject(bond)
        if subj != "用神":
            continue
        score = f.get("score", 0.0)
        if not isinstance(score, (int, float)):
            continue
        if ug_moving and score > 0:
            out.append(f"用神**动**而逢合＝合绊（源L738「动而逢合，合谓之合绊」），"
                       f"step5 却记 {score:+.2f}（{bond}）——合绊不得加分")
        if (not ug_moving) and score < 0:
            out.append(f"用神**静**而逢合＝合起（源L738「静而逢合，谓之合起」），"
                       f"step5 却记 {score:+.2f}（{bond}）——合起不得减分")

    # 跨层同号：只看 step4 给了明确符号的那些，符号为 0 的不构成声明
    for i in s4:
        want = _GREEDY_SIGN.get(str(i.get("type") or ""))
        if want is None:
            continue
        se = i.get("score_effect", 0)
        if not isinstance(se, (int, float)) or se == 0:
            continue
        subj = "用神" if str(i.get("type")) == "用神被合" else \
               ("忌神" if i.get("type") == "忌神贪合忘克" else "原神")
        if subj == "原神":
            continue          # 原神项不在 step5 日月合的 bond 词表里，跳过
        for f in dmb:
            if _subject(str(f.get("bond") or "")) != subj:
                continue
            sc = f.get("score", 0.0)
            if not isinstance(sc, (int, float)) or sc == 0:
                continue
            if (sc > 0) != (se > 0):
                out.append(f"同一条合两层反号：step4「{i.get('type')}」{se:+.2f} "
                           f"vs step5「{f.get('bond')}」{sc:+.2f}")
    return out


def selftest(problems: list[str]) -> None:
    """负例三式：动用神加分 / 静用神减分 / 两层反号，都必须被抓；合规输入必须放行。"""
    bad_a = violations(True, [], [{"bond": "日合用神", "score": 0.5}])
    if not bad_a:
        problems.append("负例失效：用神**动**逢日合仍记 +0.5（合绊当合起）没被抓到")
    bad_b = violations(False, [], [{"bond": "日合用神", "score": -0.3}])
    if not bad_b:
        problems.append("负例失效：用神**静**逢日合记 −0.3（合起当合绊）没被抓到")
    bad_c = violations(True, [{"type": "用神被合", "score_effect": -0.2}],
                       [{"bond": "日合用神", "score": 0.5}])
    if not bad_c:
        problems.append("负例失效：step4 判 −0.2 合绊、step5 判 +0.5 切近有力（反号）没被抓到")
    ok = violations(True, [{"type": "用神被合", "score_effect": -0.2}],
                    [{"bond": "用神动逢日合（合绊）", "score": 0.0}])
    if ok:
        problems.append(f"假阳性：修后的合规形态（动用神记 0、减分归 step4）被误判 → {ok}")
    ok2 = violations(False, [], [{"bond": "日合用神", "score": 0.5}])
    if ok2:
        problems.append(f"假阳性：静用神合起记 +0.5 被误判 → {ok2}")


def main() -> int:
    from engine import build_hexagram_result
    from thinking_chain import run_thinking_chain
    from effects import analyze_day_month_bonding
    import case_runner as cr

    problems: list[str] = []
    examined = 0
    hit_ug_moving = 0
    names = sorted(cr.HEXAGRAM_TRIGRAMS)
    for i, name in enumerate(names):
        base = cr.hex2yao(name)
        for moving in ([], [i % 6, (i + 3) % 6]):
            yao = [9 if (v == 7 and idx in moving) else (6 if (v == 8 and idx in moving) else v)
                   for idx, v in enumerate(base)]
            dt = datetime.strptime(TIMES[i % len(TIMES)], "%Y-%m-%d %H:%M")
            q = QUESTIONS[i % len(QUESTIONS)]
            try:
                r = build_hexagram_result(yao, q, "manual", dt.year, dt.month, dt.day, dt.hour)
                chain = run_thinking_chain(r).get("thinking_chain", {})
            except Exception as exc:                       # 单路跑挂不该静默成"通过"
                problems.append(f"{name}|{moving} 探针跑挂：{type(exc).__name__}: {exc}")
                continue
            s2 = chain.get("step2_use_god_identification", {}) or {}
            s4 = chain.get("step4_change_analysis", {}) or {}
            sel = s2.get("selected_use_god") or {}
            ug_moving = bool(isinstance(sel, dict) and sel.get("is_moving"))
            if ug_moving:
                hit_ug_moving += 1
            try:
                dmb = analyze_day_month_bonding({"thinking_chain": chain} | r).get("findings", [])
            except Exception as exc:
                problems.append(f"{name}|{moving} 日月合重算跑挂：{type(exc).__name__}: {exc}")
                continue
            examined += 1
            for v in violations(ug_moving, s4.get("greedy_harmony_issues") or [], dmb):
                problems.append(f"{name}|{moving}|{q}：{v}")

    _ap = argparse.ArgumentParser(description="check_bond_polarity：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    if _ap.parse_args().selftest:
        selftest(problems)
        print("  [selftest] 负例已跑（动用神加分／静用神减分／两层反号必被抓；"
              "修后合规形态与静用神合起不误伤）")

    print(f"合绊极性对账：{examined} 路探针（其中用神自动 {hit_ug_moving} 路）"
          f"→ 违规 {len([p for p in problems if '：' in p])} 条")
    if examined == 0:
        print("× 0 路被检视——本门等于没跑，不判通过")
        return 1
    if hit_ug_moving == 0:
        print("× 0 路用神自动——探针集覆盖不到本门要守的那一式，不判通过")
        return 1
    for x in problems[:20]:
        print(f"  × {x}")
    if not problems:
        print("  √ 同一条合在 step4／step5 同号，动用神逢合不计正分（源L738 动静两式）")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
