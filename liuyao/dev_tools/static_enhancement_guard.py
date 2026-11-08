# -*- coding: utf-8 -*-
"""537 回归守卫（六爻）：536 根治的「静卦（无动爻）advanced_analysis 被 except 静默吞成 {}」
缺陷的常驻齿。

机制：536 前，`enhance_reading` 对静卦（changed_hexagram 为 None）抛 AttributeError，
被 `run_thinking_chain` 的 `except Exception` 静默折成 `advanced_analysis={}`，导致 86 个
静卦案例的经典增强段（伏藏/暗动/月破/三合…）整段缺失而无人知晓。536 在
`effects.analyze_repetition` 与 `classical_analysis.enhance_reading` 做优雅降级根治。

本守卫逐静卦跑 `run_case(full=True)`，断言其 `advanced_analysis` 非空（精确的 536 缺陷
逆判据：缺陷态即 `{}`）。任何静卦 advanced_analysis 为空即判红——复现静默缺失立即报错，
杜绝该缺陷类回归。

守 528 约定：挂 CI root-gates，不新增 check.py 门号（仿 244 批「raise 回归守卫：修过的病
必须带齿常驻」、C1/G12/G13 挂 CI 而非 check.py）。

用法：
  python liuyao/dev_tools/static_enhancement_guard.py            # 扫描全部静卦
  python liuyao/dev_tools/static_enhancement_guard.py --selftest # 齿自证（注入空增强判红）
"""
import os
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
# 故不能只判「非空」，必须判「enhance_reading 的签名键在场」。
CLASSICAL_SIGNATURE = {
    "hidden_spirit_analysis", "soul_hexagram", "monthly_break", "triple_combo",
    "repetition", "shen_yao_activation", "transformation_pattern",
    "six_spirit_analysis", "nayin",
}


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


def check_one(case: dict):
    """返回 (ok, msg)。ok=False 即 536 类静默缺失复现（enhance_reading 未跑）。"""
    try:
        aa = advanced_analysis_of(case)
    except Exception as exc:  # 管线抛错 → 增强段未产出，同样视为缺失信号
        return False, f"run_case 抛错：{type(exc).__name__}: {exc}"
    if not isinstance(aa, dict) or len(aa) == 0:
        return False, "advanced_analysis 为空（静默缺失复现，536 缺陷态）"
    present = CLASSICAL_SIGNATURE & set(aa.keys())
    if not present:
        return False, (f"advanced_analysis 仅含非经典键 {sorted(aa.keys())}——"
                       f"enhance_reading 未运行（536 缺陷态）")
    return True, f"非空，含 {len(aa)} 键（经典增强签名 {len(present)}/{len(CLASSICAL_SIGNATURE)}）"


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
    print(f"√ 静卦增强回归守卫通过：{len(cases)} 静卦 advanced_analysis 全部非空"
          f"（536 缺陷未复现，经典增强段均正常产出）")
    return 0


def selftest() -> int:
    """齿自证：注入空 advanced_analysis（复现 536 前静默缺失），确认守卫判红。"""
    import classical_analysis  # noqa: E402
    real = classical_analysis.enhance_reading

    def _stub(ctx):
        ctx["advanced_analysis"] = {}
        return ctx

    classical_analysis.enhance_reading = _stub
    try:
        cases = static_cases()
        if not cases:
            print("✗ selftest：无静卦案例可用，无法自证")
            return 1
        ok, msg = check_one(cases[0])
        if ok:
            print(f"✗ selftest：注入空 advanced_analysis 后守卫未判红（无齿）—— {msg}")
            return 1
        print("√ selftest：注入空 advanced_analysis 后守卫判红（有齿，可抓 536 类静默缺失回归）")
        return 0
    finally:
        classical_analysis.enhance_reading = real


if __name__ == "__main__":
    force_utf8_stdio()
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(selftest())
    sys.exit(main())
