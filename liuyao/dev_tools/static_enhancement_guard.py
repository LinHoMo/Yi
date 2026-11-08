# -*- coding: utf-8 -*-
"""537 回归守卫（六爻）：536 根治的「静卦（无动爻）advanced_analysis 被 except 静默吞成 {}」
缺陷的常驻齿。

机制：536 前，`enhance_reading` 对静卦（changed_hexagram 为 None）抛 AttributeError，
被 `run_thinking_chain` 的 `except Exception` 静默折成 `advanced_analysis={}`，导致 86 个
静卦案例的经典增强段（伏藏/暗动/月破/三合…）整段缺失而无人知晓。536 在
`effects.analyze_repetition` 与 `classical_analysis.enhance_reading` 做优雅降级根治。

判据（538 批收紧）：逐静卦跑 `run_case(full=True)`，要求 `advanced_analysis` 含**全部**
`CLASSICAL_SIGNATURE` 经典增强键。不能只判「非空」——`thinking_chain` 事后仍会追加
`shi_yao_relation`／`desperate_relief` 等键（536 缺陷态实测仍「含 2 键」）；也不能只判
「任一签名键命中」，否则某个增强段被删（8/9）会漏过。86 静卦实测均 9/9 全覆盖，
收紧不误伤，且能同时抓「整段静默缺失」与「部分增强退化」。

守 528 约定：挂 CI root-gates，不新增 check.py 门号（仿 244 批「raise 回归守卫：修过的病
必须带齿常驻」、C1/G12/G13 挂 CI 而非 check.py）。

用法：
  python liuyao/dev_tools/static_enhancement_guard.py            # 扫描全部静卦
  python liuyao/dev_tools/static_enhancement_guard.py --selftest # 齿自证（5 类夹具）
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent          # liuyao/dev_tools
LIUYAO = HERE.parent                            # liuyao
for _p in (str(LIUYAO), str(LIUYAO / "scripts"), str(LIUYAO / "eval")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from case_runner import load_cases, hex2yao, run_case  # noqa: E402

# 中文 CLI 编码红线（check_cli_encoding 守）：cp936 控制台下也必须交出可读的 UTF-8。
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

# enhance_reading（classical_analysis.py）无条件写入的经典增强签名键。
# 536 缺陷态＝enhance_reading 被静默吞异常、根本没跑 → 这些键全部缺失；
# 而 thinking_chain 事后仍会追加 shi_yao_relation / luandong / desperate 等键，
# 故不能只判「非空」，必须判「enhance_reading 的签名键全部在场」。
CLASSICAL_SIGNATURE = frozenset({
    "hidden_spirit_analysis", "soul_hexagram", "monthly_break", "triple_combo",
    "repetition", "shen_yao_activation", "transformation_pattern",
    "six_spirit_analysis", "nayin",
})


def _is_static(case: dict) -> bool:
    hx = case.get("hexagram") or {}
    ho, hc = hx.get("original"), hx.get("changed")
    if not ho:
        return False
    yao = hex2yao(ho, hc)
    return bool(yao) and not any(v in (6, 9) for v in yao)


def static_cases() -> list:
    return [c for c in load_cases() if _is_static(c)]


def advanced_analysis_of(case: dict) -> dict:
    """复现评分器拿到的形状：run_case(full=True) 把思维链全量产物挂在 _full。"""
    r = run_case(case, full=True)
    aa = (r.get("_full") or {}).get("advanced_analysis") or {}
    return aa if isinstance(aa, dict) else {}


def verdict(aa) -> tuple[bool, str]:
    """纯判据（与 IO 分离，供 --selftest 直接喂夹具）。

    ok=True 当且仅当 9 个经典增强签名键**全部**在场；缺任一即判红，
    并区分「整段静默缺失（全缺）」与「部分增强退化（缺一部分）」。
    """
    if not isinstance(aa, dict) or len(aa) == 0:
        return False, "advanced_analysis 为空（536 缺陷态：静默吞成 {}）"
    missing = CLASSICAL_SIGNATURE - set(aa.keys())
    if missing:
        state = ("enhance_reading 未运行" if len(missing) == len(CLASSICAL_SIGNATURE)
                 else "部分增强退化")
        return False, (f"缺 {len(missing)}/{len(CLASSICAL_SIGNATURE)} 个经典增强签名键 "
                       f"{sorted(missing)}——{state}；现有键 {sorted(aa.keys())}")
    return True, (f"含 {len(aa)} 键，经典增强签名 "
                  f"{len(CLASSICAL_SIGNATURE)}/{len(CLASSICAL_SIGNATURE)} 全在场")


def check_one(case: dict):
    """返回 (ok, msg)。ok=False 即 536 类静默缺失或部分退化复现。"""
    try:
        aa = advanced_analysis_of(case)
    except Exception as exc:  # 管线抛错 → 增强段未产出，同样视为缺失信号
        return False, f"run_case 抛错：{type(exc).__name__}: {exc}"
    return verdict(aa)


def main() -> int:
    cases = static_cases()
    failures = []
    for c in cases:
        ok, msg = check_one(c)
        if not ok:
            failures.append((c["id"], msg))
    if failures:
        print(f"✗ 静卦增强回归守卫失败：{len(failures)}/{len(cases)} 静卦 advanced_analysis 异常")
        for cid, m in failures:
            print(f"  {cid}: {m}")
        return 1
    print(f"√ 静卦增强回归守卫通过：{len(cases)} 静卦经典增强签名键 "
          f"{len(CLASSICAL_SIGNATURE)}/{len(CLASSICAL_SIGNATURE)} 全在场"
          f"（536 缺陷与部分退化均未复现）")
    return 0


def selftest() -> int:
    """齿自证：5 类夹具——空／仅非经典键／部分退化 必判红，全签名 必判绿，
    再以真实管线注入空增强与删一键，确认端到端判红（防纯函数与 IO 分家）。
    """
    import classical_analysis  # noqa: E402
    real = classical_analysis.enhance_reading

    # ①–④ 纯判据夹具
    full = {k: "<ok>" for k in CLASSICAL_SIGNATURE}
    fixtures = [
        ("空字典（536 静默吞成 {}）", {}, False),
        ("仅非经典键（thinking_chain 事后追加）",
         {"shi_yao_relation": 1, "desperate_relief": 1}, False),
        ("部分退化（8/9，某个增强段被删）",
         {k: v for k, v in full.items() if k != "nayin"}, False),
        ("健康（9/9 全在场）", full, True),
    ]
    problems = []
    for label, aa, expect_ok in fixtures:
        ok, msg = verdict(aa)
        if ok != expect_ok:
            problems.append(f"夹具[{label}] 期望 {'绿' if expect_ok else '红'}，实得 {'绿' if ok else '红'}：{msg}")
    if problems:
        for p in problems:
            print("× " + p)
        return 1
    print(f"√ selftest 纯判据 4 夹具：3 红 1 绿 全对（含「部分退化 8/9」齿）")

    cases = static_cases()
    if not cases:
        print("× selftest：无静卦案例可用，无法做端到端自证")
        return 1

    # ⑤ 真实管线：注入空增强
    def _stub_empty(ctx):
        ctx["advanced_analysis"] = {}
        return ctx

    # ⑥ 真实管线：删掉一个增强段（部分退化）
    def _stub_partial(ctx):
        real(ctx)
        aa = ctx.get("advanced_analysis")
        if isinstance(aa, dict):
            aa.pop("nayin", None)
        return ctx

    try:
        for label, stub in (("空增强", _stub_empty), ("删一键（部分退化）", _stub_partial)):
            classical_analysis.enhance_reading = stub
            ok, msg = check_one(cases[0])
            if ok:
                print(f"× selftest 端到端[{label}] 未判红（无齿）：{msg}")
                return 1
            print(f"√ selftest 端到端[{label}] 判红：{msg[:110]}")
    finally:
        classical_analysis.enhance_reading = real
    return 0


if __name__ == "__main__":
    force_utf8_stdio()
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    sys.exit(main())
