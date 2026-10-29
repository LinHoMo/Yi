# -*- coding: utf-8 -*-
"""分层契约门：四段输出键白名单 + 层间禁边表（CONTRACT.md §三／§四）。

为什么需要它（第三百一十批体检）：
  段自述与实跑不符的现象在本科真实发生过：`chart` 段自称"纯机械排盘"，却在
  `trigram_interpretation` 里吐「体生用有所付出，待时收功」这类成句评价（六爻侧实见）；
  `analyze` 自称"无解读成分"却吐 `verdict="大吉"`。原有的 `[2.2] chart 纯净门` 只查
  「大凶/凶/吉/宜/忌」五个字，且只跑一个夹具——**判据是措辞黑名单，不是 schema 白名单**，
  所以门一直是绿的。本门把判据换成键面。

本门换判据：
  · 键面：实跑四个夹具，chart / analyze 的顶层键与 `trigram_interpretation` /
    `conclusion` 的子键必须落在 `data/rules/layer_contract.json` 的白名单内；
    多一个键即红（越界新增），必填键少一个即红（静默丢字段）。
  · 禁边：AST 扫 `scripts/` 与 `core/` 的 import 图，按契约禁边表判。
    语义是「只准减不准增」：在册欠账出现＝记一笔不红；在册欠账消失＝条目没删，判红
    （防台账变假事实，AGENTS.md §六.2）。

    python dev_tools/check_layer_contract.py
    python dev_tools/check_layer_contract.py --selftest   # 负例：证明本器抓得住

真值源是 `data/rules/layer_contract.json`，不是本文件的常量——改契约只改 JSON + CONTRACT.md。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "core"))
from yishu_core.runtime import force_utf8_stdio, utf8_subprocess_env  # noqa: E402
from yishu_core.gate_kit import (  # noqa: E402
    contract_edge_problems,
    contract_stage_problems,
    py_imports,
    rel_files,
)

CONTRACT_PATH = DISC / "data" / "rules" / "layer_contract.json"

# 夹具由契约文件声明（`fixtures`），不在代码里写死：两科共用同一份驱动，
# 差异只在各自的 layer_contract.json。只跑一种起卦方式会漏掉该方式特有字段。
def _fixtures(schema: dict) -> list[tuple[str, list[str]]]:
    items = schema.get("fixtures") or []
    if not items:
        raise RuntimeError("契约缺 fixtures：没有夹具就不许报绿（零夹具＝零证据）")
    return [(it["name"], list(it["args"])) for it in items]


def _run_json(script: str, args: list[str], *, stdin_json: dict | None = None) -> dict:
    """跑一个段脚本，返回其 JSON 输出；失败抛 RuntimeError（不静默降级）。"""
    argv = [sys.executable, str(DISC / "scripts" / script), *args]
    proc = subprocess.run(argv, cwd=str(DISC), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          env=utf8_subprocess_env())
    if proc.returncode != 0:
        raise RuntimeError(f"{script} 退出码 {proc.returncode}：{(proc.stdout + proc.stderr)[-400:]}")
    text = proc.stdout
    start = text.find("{")
    if start < 0:
        raise RuntimeError(f"{script} 输出不含 JSON：{text[:200]}")
    try:
        return json.loads(text[start:])
    except ValueError as exc:
        raise RuntimeError(f"{script} 输出不是合法 JSON：{exc}") from exc


def _analyze_fixture(chart_data: dict) -> dict:
    """把 chart JSON 落到临时文件再喂 analyze（走真实 CLI，不 import 内部函数）。"""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "chart.json"
        path.write_text(json.dumps(chart_data, ensure_ascii=False), encoding="utf-8")
        return _run_json("analyze.py", [str(path)])


def stage_problems(schema: dict) -> tuple[list[str], list[str]]:
    """跑全部夹具，返回 (problems, notes)。notes 是给人看的合规摘要。"""
    problems: list[str] = []
    notes: list[str] = []
    stages = schema.get("stages") or {}
    for name, args in _fixtures(schema):
        chart_data = _run_json("chart.py", args)
        if (spec := stages.get("chart")):
            found = contract_stage_problems(chart_data, spec, label=f"chart[{name}]")
            problems.extend(found)
        if (spec := stages.get("analyze")):
            found = contract_stage_problems(_analyze_fixture(chart_data), spec,
                                            label=f"analyze[{name}]")
            problems.extend(found)
    if not problems:
        n_chart = len(stages.get("chart", {}).get("allowed") or ())
        n_ana = len(stages.get("analyze", {}).get("allowed") or ())
        notes.append(f"{len(_fixtures(schema))} 个夹具 × 两段键面全部落在契约内"
                     f"（chart {n_chart} 键 / analyze {n_ana} 键）")
    return problems, notes


def edge_problems(schema: dict) -> tuple[list[str], list[str]]:
    """扫 import 图判禁边；返回 (problems, notes)。"""
    edges: dict[str, set[str]] = {}
    for rel in rel_files(DISC, "scripts/*.py") + rel_files(DISC, "core/**/*.py"):
        edges[rel] = py_imports(DISC / rel)
    rules = (schema.get("edges") or {}).get("forbidden") or []
    problems, notes = contract_edge_problems(edges, rules)
    notes.insert(0, f"扫 {len(edges)} 个模块，检查 {len(rules)} 条禁边规则")
    return problems, notes


def selftest() -> list[str]:
    """负例自证（AGENTS.md §四.8）：先证明判据抓得住，再谈它是不是绿的。"""
    problems: list[str] = []
    spec = {"allowed": ["a", "b"], "required": ["a"],
            "nested": {"n": {"allowed": ["x"], "required": ["x"]}}}
    if not contract_stage_problems({"a": 1, "b": 2, "n": {"x": 1}}, spec):
        problems.append("自证失败：合规输入被误判为违规")
    if not contract_stage_problems({"a": 1, "b": 2, "zzz": 3, "n": {"x": 1}}, spec):
        problems.append("自证失败：越界新增键没被抓到")
    if not contract_stage_problems({"b": 2, "n": {"x": 1}}, spec):
        problems.append("自证失败：必填键缺失没被抓到")
    if not contract_stage_problems({"a": 1, "b": 2, "n": {"x": 1, "y": 2}}, spec):
        problems.append("自证失败：嵌套白名单越界没被抓到")
    if not contract_stage_problems({"a": 1, "b": 2, "n": [1, 2]}, spec):
        problems.append("自证失败：嵌套类型不符没被抓到")

    # 夹具路径用 nope.py（[11] 的负例约定），免得死链门把 selftest 样本当真实声明
    rules = [{"from": "scripts/nope.py", "to": "bad", "known": True, "why": "t"},
             {"from": "dev_tools/nope.py", "to": "worse", "known": False, "why": "t"}]
    edges = {"scripts/nope.py": {"bad"}, "dev_tools/nope.py": {"ok"}}
    probs, notes = contract_edge_problems(edges, rules)
    if probs:
        problems.append("自证失败：在册欠账出现却被判红")
    if not any("欠账在册" in n for n in notes):
        problems.append("自证失败：在册欠账没有出声")
    probs, _ = contract_edge_problems({"scripts/nope.py": {"ok"}}, rules)
    if not any("欠账已还" in p for p in probs):
        problems.append("自证失败：欠账消失（条目未删）没被抓到")
    probs, _ = contract_edge_problems({"dev_tools/nope.py": {"worse"}}, rules)
    if not any("新增禁边" in p for p in probs):
        problems.append("自证失败：零容忍禁边被踩却没被抓到")

    schema = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not schema.get("fixtures"):
        problems.append("契约自身不合规：fixtures 为空——没有夹具就没有键面证据")
    for rule in (schema.get("edges") or {}).get("forbidden") or ():
        if not rule.get("why"):
            problems.append(f"契约自身不合规：禁边 {rule.get('from')}→{rule.get('to')} 缺 why")
    for name, spec_ in (schema.get("stages") or {}).items():
        if not set(spec_.get("required") or ()) <= set(spec_.get("allowed") or ()):
            problems.append(f"契约自身不合规：{name}.required 有键不在 allowed 内")
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="分层契约门（四段键白名单 + 禁边表）")
    ap.add_argument("--selftest", action="store_true",
                    help="先跑负例自证（8 类），再照常跑实测——与本科其它门的约定一致")
    args = ap.parse_args()

    schema = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not schema.get("fixtures"):
        problems.append("契约自身不合规：fixtures 为空——没有夹具就没有键面证据")
    problems: list[str] = []

    if args.selftest:
        own = selftest()
        for p in own:
            print(f"  × {p}")
        if not own:
            print("  √ selftest：键面（多键/缺键/嵌套/类型/夹具缺失）＋禁边（在册/已还/新增）负例全部抓到")
        problems.extend(own)

    st_problems, st_notes = stage_problems(schema)
    ed_problems, ed_notes = edge_problems(schema)
    for n in st_notes + ed_notes:
        print(f"  · {n}")
    for p in st_problems + ed_problems:
        print(f"  × {p}")
    problems.extend(st_problems + ed_problems)

    if not st_problems and not ed_problems:
        print(f"  √ 分层契约：键面与禁边均符合 CONTRACT.md（batch {schema.get('batch')}）")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
