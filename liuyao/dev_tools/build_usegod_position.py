# -*- coding: utf-8 -*-
"""use_god_position 基准例补全器（一次性数据构建，产物入库、脚本留档可复跑）。

口径：expected.use_god_position 只在**纳甲唯一可定**时填写——
  书面已明写 用神六亲（expected.use_god）与 用神地支（expected.use_god_branch），
  而该（六亲, 地支）组合在本卦爻线中**恰出现一处**，则爻位由纳甲唯一确定，
  属卦表机械事实（对表回归性质），不涉解读分歧；多处出现（用神多现）一律跳过。
数据源：卦面爻线由引擎 build_hexagram_result 按 core 纳甲真值表排出
（与 case_runner 同一入口），本脚本不做任何手工指定。
"""
from __future__ import annotations
# eval/ 上 path（相对 __file__ 定位；禁止硬编码本机绝对路径）
import sys as _sys
from pathlib import Path as _P
_ed = str(_P(__file__).resolve().parents[1] / "eval")
if _ed not in _sys.path:
    _sys.path.insert(0, _ed)

import argparse
import json
import sys

# 控制台编码守卫：GBK/cp936 控制台下本器的中文输出会退化成乱码甚至 UnicodeEncodeError
# （rc 仍为 0、金标准看不见，只有这条守卫管得住）。判据见 dev_tools/check.py 的编码不变式。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
# 第五百零八批升格：学科根入路径，`import engine` 才解析到 <学科根>/engine
for _p in (str(DISC / "scripts"), str(DISC / "core"), str(DISC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine import build_hexagram_result  # noqa: E402
import case_runner as cr  # noqa: E402

CASES = DISC / "data" / "cases" / "classical_cases.json"


def compute_position(case: dict) -> tuple[str, str]:
    """由引擎 build_hexagram_result 按 core 纳甲真值表派生用神爻位。

    返回 (爻位, 出处)；六亲+地支本卦仅一处出现时唯一可定，多现/无基准/装卦失败返回空串（不猜）。
    """
    try:
        exp = case.get("expected") or {}
        god, branch = exp.get("use_god"), exp.get("use_god_branch")
        if not god or not branch:
            return "", ""
        hx = case.get("hexagram") or {}
        yao_vals = cr.hex2yao(hx.get("original"), hx.get("changed"))
        if yao_vals is None:
            return "", ""
        resolved = cr.resolve_case_time(case)
        dt = resolved["dt"]
        h = build_hexagram_result(yao_vals, case.get("question", ""), "manual",
                                  dt.year, dt.month, dt.day, dt.hour)
        lines = h["original_hexagram"]["yao_lines"]
        # 世爻/应爻：由引擎 is_world/is_ying 唯一确定（纳甲宫位机械事实，非六亲）
        if god in ("世爻", "应爻"):
            flag = "is_world" if god == "世爻" else "is_ying"
            matched = [y["position"] for y in lines if y.get(flag)]
            if len(matched) == 1:
                return matched[0], f"{god}唯一可定：引擎本卦第 {matched[0]} 爻 {flag}=True"
            return "", ""
        # 六亲+地支：本卦仅一处出现时唯一可定
        matches = [y["position"] for y in lines
                   if y.get("six_relation") == god and y.get("earthly_branch") == branch]
        if len(matches) == 1:
            return matches[0], f"纳甲唯一可定：{god}({branch})在本卦仅{matches[0]}爻一处"
    except Exception:
        pass
    return "", ""


def _check_sync() -> int:
    """同源复验：已落盘的 use_god_position 须与引擎当前派生一致（引擎升版后须重跑）。"""
    if not CASES.exists():
        print("× 落盘集不存在：%s" % CASES.relative_to(DISC))
        return 1
    store = json.loads(CASES.read_text(encoding="utf-8"))
    fails = []
    checked = 0
    for case in store.get("cases", []):
        exp = case.get("expected") or {}
        if not exp.get("use_god_position"):
            continue
        pos, _ = compute_position(case)
        if str(pos) != str(exp["use_god_position"]):
            fails.append("%s 的 use_god_position=%s 与引擎当前派生 %s 不一致"
                         % (case.get("id"), exp["use_god_position"], pos or "∅(多现/无基准)"))
            continue
        checked += 1
    ok = "全部一致" if not fails else "%d 处失效" % len(fails)
    print("同源复验：%d 条 use_god_position 与引擎一致；%s" % (checked, ok))
    for f in fails:
        print("  ×", f)
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="use_god_position 基准例补全器")
    ap.add_argument("--check", action="store_true",
                    help="只复验已生成的 use_god_position 与引擎一致，不写文件（[46] 同步门挂此）")
    args = ap.parse_args()
    if args.check:
        return _check_sync()
    store = json.loads(CASES.read_text(encoding="utf-8"))
    filled = skipped_multi = skipped_no_base = 0
    for case in store.get("cases", []):
        exp = case.get("expected") or {}
        god, branch = exp.get("use_god"), exp.get("use_god_branch")
        if not god or not branch or exp.get("use_god_position"):
            if exp.get("use_god_position"):
                filled += 1
            else:
                skipped_no_base += 1
            continue
        pos, basis = compute_position(case)
        if pos:
            exp["use_god_position"] = pos
            exp.setdefault("use_god_position_basis", basis)
            filled += 1
        else:
            skipped_multi += 1

    CASES.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"已填 {filled}（含原有）｜用神多现等跳过 {skipped_multi}｜无基准 {skipped_no_base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
