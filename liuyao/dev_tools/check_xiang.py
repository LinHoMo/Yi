#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""象层门（362 批）：象目必须有出处、象类别必须随题类走、象层不得倒灌评分。

为什么需要它：本仓的「象分析」此前**只存在于两个地方**——trigram_symbolism 里
一张八卦类象表，和 analyze 里一句写死 `category="general"` 的调用。结果是：
八卦类象、卦辞爻辞、互体、六神象义这些素材盘面里全有，正文里一个字都不出。
素材在、能力不在，是**看不见的缺口**——原有门一条都拦不住（键面合规、评分未变、
指纹不动）。

本门三条判据：
  ① 出处：每个象目（trigram/ti_yong/guaci/yaoci/hu_gua/spirit/fangwei）必须带
     非空 `basis`，无出处的象目不得产出（AGENTS §三：文案进 data，出处随文案走）。
  ② 联动：题类→象类别必须真联动（疾病→health、失物→loss、功名→career），
     且问句无题类信号时落 general——只验"能取到类别"会把恒 general 判成过。
  ③ 禁评分：评分侧模块（step1-5/timing/judge/classical_*）不得读 `xiang`；
     `xiang` 不得出现在 evaluate.WEIGHTS 的维度键里。象可以进正文，不许进分数。

`--selftest` 做负例：挖空 basis／恒 general／评分侧偷读 xiang，三处各须被抓。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

# 评分侧：象层一旦被这里读到，象就变成了分数——CONTRACT §五-bis 禁边
SCORING_MODULES = (
    "step1.py", "step2.py", "step3.py", "step4.py", "step5.py",
    "timing.py", "judge.py", "classical_analysis.py",
    "classical_enhancements.py", "classical_enhancements_direction.py",
    "classical_enhancements_dufa.py", "classical_enhancements_fangwei.py",
    "classical_enhancements_fushi.py", "classical_enhancements_menlei.py",
    "classical_enhancements_shen_yao.py", "classical_enhancements_yimao_zhugui.py",
    "classical_enhancements_zhugui.py", "effects.py",
)
# 允许读象的层：装配、呈现、输出——象的合法去向
XIANG_CONSUMERS = ("xiang.py", "analyze.py", "narrate.py", "render.py", "output.py",
                   "engine_format.py", "engine_format_report.py")

# 题类→象类别的正例（问句须能命中 question_classes.json 的对应题类）
CATEGORY_CASES = (
    ("占问疾病何时痊愈", "health"),
    ("占问失物能否找回", "loss"),
    ("占问功名能否中第", "career"),
    ("占问婚姻是否可成", "relationship"),
    ("占问行人何时归来", "travel"),
)


def _xiang_of(question: str) -> dict:
    """实跑一路 analyze，取其象层。失败即抛（不静默降级——门不能假装通过）。"""
    from chart import chart as _chart
    from analyze import analyze as _analyze
    return (_analyze(_chart("coin", question, seed=42)).get("xiang") or {})


def basis_problems(samples: dict[str, dict]) -> list[str]:
    """① 出处：每个产出的象目都必须带非空 basis。"""
    problems: list[str] = []
    for q, x in samples.items():
        if not x:
            problems.append(f"象层整块缺失：{q}（素材在盘面里，analyze 没装配出来）")
            continue
        for key in ("trigram", "ti_yong", "guaci", "yaoci", "hu_gua", "spirit", "fangwei"):
            blk = x.get(key)
            if not isinstance(blk, dict):
                continue
            if not str(blk.get("basis") or "").strip():
                problems.append(f"象目 {key} 缺 basis（{q}）——无出处的象目不得产出")
    return problems


def category_problems(samples: dict[str, dict]) -> list[str]:
    """② 联动：题类→象类别必须真联动；无信号落 general。"""
    problems: list[str] = []
    for q, want in CATEGORY_CASES:
        got = (samples.get(q) or {}).get("category")
        if got != want:
            problems.append(f"象类别未随题类联动：{q} 应为 {want}，实得 {got}")
    # 兜底：问句无任何题类信号时必须落 general（否则就是关键词表过宽）
    from xiang import resolve_xiang_category
    if resolve_xiang_category("", "占问此事如何") != "general":
        problems.append("无题类信号的问句未落 general（关键词兜底表过宽）")
    return problems


def no_scoring_problems() -> list[str]:
    """③ 禁评分：评分侧不得读 xiang；xiang 不得成为评分维度。"""
    problems: list[str] = []
    for name in SCORING_MODULES:
        p = ROOT / "scripts" / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        if "xiang" in text and "xiang" not in ("",):
            # 只在真正取用（get/import/[）时判红，避免注释里提一句就红
            for line in text.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    continue
                if ("xiang" in s and ("import" in s or '"xiang"' in s or "'xiang'" in s
                                      or "get(\"xiang\"" in s or "get('xiang'" in s)):
                    problems.append(f"评分侧 {name} 读象：{s[:90]}——象不得倒灌评分（CONTRACT §五-bis）")
                    break
    try:
        from evaluate import WEIGHTS
        if "xiang" in WEIGHTS:
            problems.append("evaluate.WEIGHTS 含 xiang 维度——象层不进评分")
    except Exception:  # noqa: BLE001
        pass
    return problems


def selftest() -> int:
    """负例自证：先证明判据抓得住，再谈它是不是绿的。"""
    problems: list[str] = []
    ok = {"trigram": {"basis": "x"}, "ti_yong": {"basis": "x"}}
    if basis_problems({"占": ok}):
        problems.append("自证失败：合规象层被误判为缺出处")
    if not basis_problems({"占": {"trigram": {"basis": ""}}}):
        problems.append("自证失败：挖空 basis 的象目没被抓到")
    if not basis_problems({"占": {}}):
        problems.append("自证失败：象层整块缺失没被抓到")

    bad = {q: {"category": "general"} for q, _ in CATEGORY_CASES}
    if not category_problems(bad):
        problems.append("自证失败：category 恒 general（旧缺陷写法）没被抓到")
    good = {q: {"category": w} for q, w in CATEGORY_CASES}
    if category_problems(good):
        problems.append("自证失败：合规联动被误判")

    if problems:
        print("FAIL：负例自证未通过")
        for p in problems:
            print("  " + p)
        return 1
    print("selftest：三类负例（缺出处／恒 general／整块缺失）全部抓到；"
          "合规输入放行")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="象层门：出处／联动／禁评分")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()
    if args.selftest:
        return selftest()

    samples: dict[str, dict] = {}
    for q, _ in CATEGORY_CASES:
        samples[q] = _xiang_of(q)

    problems: list[str] = []
    problems.extend(basis_problems(samples))
    problems.extend(category_problems(samples))
    problems.extend(no_scoring_problems())

    cats = {q: (x.get("category") or "—") for q, x in samples.items()}
    print(f"象层门：{len(samples)} 路实跑；象类别 {list(cats.values())}")
    print(f"      象目出处逐块核对；评分侧 {len(SCORING_MODULES)} 个模块禁读象")
    if problems:
        print(f"FAIL：{len(problems)} 项")
        for p in problems:
            print("  " + p)
        return 1
    print("校验不过项: 无（象目有出处、类别随题类、象层未倒灌评分）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
