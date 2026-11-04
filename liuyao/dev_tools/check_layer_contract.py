# -*- coding: utf-8 -*-
"""分层契约门（CONTRACT.md §三／§四）：键白名单 + 层间禁边 + 文档摘要同步。

  · 键面：实跑全部夹具，chart/analyze 顶层键与嵌套子键须落在各科 JSON 白名单内；
    多一个键即红（越界新增），少一个必填键即红（静默丢字段）。
  · 禁边：AST 扫 scripts/、core/、engine/ 的 import 图；在册欠账出现不红、
    欠账消失而条目未删判红（AGENTS.md §六.2）。
  · 文档同步：CONTRACT.md §四 的键数表须与两科 JSON 逐项相符，防摘要成假事实。

真值源是各科 `layer_contract.json`；改契约 = 改 JSON + CONTRACT.md + CHANGELOG。

    python dev_tools/check_layer_contract.py [--selftest]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "CONTRACT.md"
sys.path.insert(0, str(DISC / "core"))
from yishu_core.runtime import force_utf8_stdio, utf8_subprocess_env  # noqa: E402
from yishu_core.gate_kit import (  # noqa: E402
    contract_edge_problems,
    contract_stage_problems,
    py_imports,
    rel_files,
)

# D2 分区：六爻 data/rules 分 domain/（在用领域表）与 legacy/（v1 旧台账）；八字仍扁平。
# 按在盘实际位置自适应，两科同一份代码（AGENTS.md §二 复制分发，不用 import）。
_RULES_FLAT = DISC / "data" / "rules"
_RULES_DOMAIN = _RULES_FLAT / "domain"
CONTRACT_PATH = (_RULES_DOMAIN / "layer_contract.json"
                  if (_RULES_DOMAIN / "layer_contract.json").exists()
                  else _RULES_FLAT / "layer_contract.json")
# 353 批：跨科共用信封 schema（root 单一真源；两科 dev_tools 副本按 parents[2] 定位）
SCHEMA_PATH = Path(__file__).resolve().parents[2] / "devkit" / "layer_contract.schema.json"

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
    # D4 收编后 scripts/ 下有子目录（classical/）——名单必须递归，否则收编文件悄悄退出禁边扫描面
    # 第五百零八批升格：engine/ 与 engine/classical/ 已在 <学科根> 下，同样必须入扫描面。
    for rel in (rel_files(DISC, "scripts/**/*.py") + rel_files(DISC, "core/**/*.py")
                + rel_files(DISC, "engine/**/*.py")):
        edges[rel] = py_imports(DISC / rel)
    rules = (schema.get("edges") or {}).get("forbidden") or []
    problems, notes = contract_edge_problems(edges, rules)
    notes.insert(0, f"扫 {len(edges)} 个模块，检查 {len(rules)} 条禁边规则")
    return problems, notes


def validate_contract_envelope(data: dict, schema_def: dict) -> list[str]:
    """353 批：按 `devkit/layer_contract.schema.json` 的required/properties 校验信封。

    零外部依赖：只实现本仓用到的 JSON Schema 子集（required/type/items/minLength/
    minItems/minProperties）。各科 stage 键名不在信封层，仍由 contract_stage_problems 判。
    """
    problems: list[str] = []
    if not isinstance(data, dict):
        return ["契约不是 JSON object"]
    for key in schema_def.get("required", []):
        if key not in data:
            problems.append(f"信封缺顶级键 {key}")
    props = schema_def.get("properties", {})

    def _typed(name: str, value, spec: dict) -> None:
        t = spec.get("type")
        if t == "integer" and not isinstance(value, int):
            problems.append(f"信封 {name} 应为 integer，实得 {type(value).__name__}")
        elif t == "string" and not isinstance(value, str):
            problems.append(f"信封 {name} 应为 string，实得 {type(value).__name__}")
        elif t == "array" and not isinstance(value, list):
            problems.append(f"信封 {name} 应为 array，实得 {type(value).__name__}")
        elif t == "object" and not isinstance(value, dict):
            problems.append(f"信封 {name} 应为 object，实得 {type(value).__name__}")
        elif t == "boolean" and not isinstance(value, bool):
            problems.append(f"信封 {name} 应为 boolean，实得 {type(value).__name__}")
        if isinstance(value, (str, list, dict)) and spec.get("minLength") and len(value) < spec["minLength"]:
            problems.append(f"信封 {name} 长度 < {spec['minLength']}")
        if isinstance(value, (str, list, dict)) and spec.get("minItems") and len(value) < spec["minItems"]:
            problems.append(f"信封 {name} 项数 < {spec['minItems']}")

    for key, spec in props.items():
        if key in data:
            _typed(key, data[key], spec)

    fixtures = data.get("fixtures")
    if isinstance(fixtures, list):
        for i, fx in enumerate(fixtures):
            if not isinstance(fx, dict):
                problems.append(f"信封 fixtures[{i}] 不是 object")
                continue
            for key in ("name", "args"):
                if key not in fx:
                    problems.append(f"信封 fixtures[{i}] 缺 {key}")
            if "name" in fx and (not isinstance(fx["name"], str) or not fx["name"].strip()):
                problems.append(f"信封 fixtures[{i}].name 非空 string")
            if "args" in fx and not isinstance(fx["args"], list):
                problems.append(f"信封 fixtures[{i}].args 应为 array")

    stages = data.get("stages")
    if isinstance(stages, dict) and not stages:
        problems.append("信封 stages 为空（没有段就没有契约）")

    edges = data.get("edges")
    if isinstance(edges, dict):
        forbidden = edges.get("forbidden")
        if not isinstance(forbidden, list):
            problems.append("信封 edges.forbidden 应为 array")
        else:
            for i, rule in enumerate(forbidden):
                if not isinstance(rule, dict):
                    problems.append(f"信封 edges.forbidden[{i}] 不是 object")
                    continue
                for key in ("from", "to", "known", "why"):
                    if key not in rule:
                        problems.append(f"信封 edges.forbidden[{i}] 缺 {key}")
                for key in ("from", "to", "why"):
                    if key in rule and (not isinstance(rule[key], str) or not rule[key].strip()):
                        problems.append(f"信封 edges.forbidden[{i}].{key} 非空 string")
                if "known" in rule and not isinstance(rule["known"], bool):
                    problems.append(f"信封 edges.forbidden[{i}].known 应为 boolean")
    return problems


DOC_ROW = re.compile(r"^\|\s*(六爻|八字)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|(.+)$", re.M)
DOC_NESTED = re.compile(r"`([a-z_]+)`\s*(\d+)\s*键")
DISC_BY_LABEL = {"六爻": "liuyao", "八字": "bazi"}


def load_contracts(root: Path = ROOT) -> dict:
    """按在盘位置读两科契约（六爻有 domain/、八字扁平）。"""
    out = {}
    for name in ("liuyao", "bazi"):
        domain = root / name / "data" / "rules" / "domain" / "layer_contract.json"
        path = domain if domain.is_file() else root / name / "data" / "rules" / "layer_contract.json"
        out[name] = json.loads(path.read_text(encoding="utf-8"))
    return out


def doc_sync_problems(text: str, contracts: dict) -> list[str]:
    """CONTRACT.md §四 摘要 vs 两科 JSON；缺段、0 行、漏登记均判红。"""
    if "## §四" not in text:
        return ["CONTRACT.md 缺 §四 输出键白名单"]
    body = text.split("## §四", 1)[1].split("\n## ", 1)[0]
    rows = DOC_ROW.findall(body)
    if len(rows) != 2:
        return [f"§四 应有六爻/八字两行键数表，实得 {len(rows)} 行（0 行不许当通过）"]
    problems = []
    for label, chart_n, ana_n, rest in rows:
        stages = contracts[DISC_BY_LABEL[label]]["stages"]
        for kind, got in (("chart", int(chart_n)), ("analyze", int(ana_n))):
            expected = len(stages[kind]["allowed"])
            if got != expected:
                problems.append(f"§四 {label} {kind} 键数 {got} ≠ JSON {expected}")
        nested = {k: len(v["allowed"]) for k, v in stages["analyze"].get("nested", {}).items()}
        declared = {k: int(v) for k, v in DOC_NESTED.findall(rest)}
        for name, n in declared.items():
            if name not in nested or nested[name] != n:
                problems.append(f"§四 {label} 嵌套表 `{name}` {n} 键 ≠ JSON {nested.get(name, '缺表')}")
        for name in nested:
            if name not in declared:
                problems.append(f"§四 {label} 漏登记嵌套表 `{name}`（JSON {nested[name]} 键）")
    return problems


def doc_problems_now() -> list[str]:
    if not DOC_PATH.is_file():
        return [f"缺根级契约文档：{DOC_PATH}"]
    return doc_sync_problems(DOC_PATH.read_text(encoding="utf-8"), load_contracts())


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

    # 353 批：信封 schema 负例——真契约放行；缺 stages／禁边 why 为空必须判红
    try:
        schema_def = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        schema_def = None
    if schema_def is not None:
        if validate_contract_envelope(schema, schema_def):
            problems.append("信封 schema 自证失败：真契约被误判")
        broken = json.loads(json.dumps(schema))
        broken.pop("stages", None)
        if not validate_contract_envelope(broken, schema_def):
            problems.append("信封 schema 自证失败：缺 stages 没被抓到")
        broken = json.loads(json.dumps(schema))
        if (broken.get("edges") or {}).get("forbidden"):
            broken["edges"]["forbidden"][0]["why"] = ""
            if not validate_contract_envelope(broken, schema_def):
                problems.append("信封 schema 自证失败：禁边 why 为空没被抓到")

    if doc_problems_now():
        problems.append("CONTRACT.md §四 与两科 JSON 不同步")
    if not doc_sync_problems("", load_contracts()):
        problems.append("文档同步自证失败：缺 §四 没被抓到")
    if DOC_PATH.is_file():
        tampered, n = re.subn(r"(\|\s*六爻\s*\|\s*)\d+", r"\g<1>999",
                              DOC_PATH.read_text(encoding="utf-8"), count=1)
        if n != 1 or not doc_sync_problems(tampered, load_contracts()):
            problems.append("文档同步自证失败：键数被改没被抓到")
    return problems


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="分层契约门（四段键白名单 + 禁边表）")
    ap.add_argument("--selftest", action="store_true",
                    help="先跑负例自证（8 类），再照常跑实测——与本科其它门的约定一致")
    args = ap.parse_args()

    problems: list[str] = []
    schema = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if not schema.get("fixtures"):
        problems.append("契约自身不合规：fixtures 为空——没有夹具就没有键面证据")
    try:
        schema_def = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        schema_def = None
        problems.append(f"信封 schema 缺失：{SCHEMA_PATH}（跨科共用契约无 schema）")
    if schema_def is not None:
        env_problems = validate_contract_envelope(schema, schema_def)
        for p in env_problems:
            print(f"  × {p}")
        problems.extend(env_problems)
        if not env_problems:
            print("  √ 信封 schema 通过（devkit/layer_contract.schema.json）")

    if args.selftest:
        own = selftest()
        for p in own:
            print(f"  × {p}")
        if not own:
            print("  √ selftest：键面／禁边／信封 schema／文档摘要同步负例全部抓到")
        problems.extend(own)

    doc_problems = doc_problems_now()
    for p in doc_problems:
        print(f"  × {p}")
    problems.extend(doc_problems)
    if not doc_problems:
        print("  √ CONTRACT.md §四 摘要与两科契约 JSON 逐项同步")

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
