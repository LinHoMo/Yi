# -*- coding: utf-8 -*-
"""学科质量门共享壳（gate kit）—— 八字·六爻两科 `dev_tools/check.py` 共用，禁止各写一份。

SKILL.md 要求学科门复用共享件。此前 7 科各写一份 subprocess 壳，取值互相漂移：
argv 前缀（内置 `sys.executable` 与否）、超时（无/60/120/300）、子进程环境（无 / utf8）
各不相同 —— 同一语义多份实现，正是 `SKILL.md` §二「同类只存一份」要治的病。
本模块把实现收成一份，各科只**声明**自己的口径：

    run_step(cmd, *, cwd, timeout=None, python=False) -> (rc, 合并文本)
    measure(name, out, patterns)                      -> float | None
    eval_metrics(disc_root, split, *, model_key=None) -> dict

子进程环境一律带 `utf8_subprocess_env()`：不传则中文 Windows 上子进程按 GBK 出字节、
父进程按 UTF-8 解码，中文断言恒红（见 `yishu_core.runtime` 的说明）——那是假红，
不是被测行为有问题。口径要确定性，所以不继承调用方设置。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

from yishu_core.runtime import utf8_subprocess_env


def run_step(cmd: list[str], *, cwd, timeout: float | None = None,
             python: bool = False) -> tuple[int, str]:
    """跑一步子进程，返回 (退出码, stdout+stderr 合并文本)。

    python=True 时在 argv 前补 `sys.executable`（调用方给的是脚本相对路径）。
    """
    argv = [sys.executable, *cmd] if python else list(cmd)
    proc = subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          timeout=timeout, env=utf8_subprocess_env())
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def measure(name: str, out: str, patterns: dict) -> float | None:
    """按学科的 PATTERNS 正则从门输出里取一个数值指标；取不到返回 None。"""
    pat = patterns.get(name)
    if not pat:
        return None
    m = re.search(pat, out)
    return float(m.group(1)) if m else None


def eval_metrics(split: str, *, eval_file, cwd,
                 model_key: str | None = None) -> dict:
    """跑 `eval/evaluate.py --split <split> --save`，返回 {avg, n, rc, top1, rank}。

    `eval_file` 必须由调用方传入：内核不得知道评测落盘目录（铁律二
    「解读路径不得触达案例库」由 `dev_tools/check_case_isolation.py` 机械守，
    内核里出现该路径字面量会直接把门判红）。

    新鲜度守卫（P0 教训）：先删上一次的落盘文件，跑完若文件不在或 mtime 早于起跑时刻，
    说明评测没产出新结果（崩溃时旧文件会冒充本次分数）→ 返回 error，不拿旧值充数。

    model_key=None 用于只出一种计分模型的学科（其 `results` 即汇总本体）；
    给 "strict" 则取 `results[model_key]`，并顺带取 `results.yingqi_discrimination` 的
    主应期命中率与平均名次（无该键的学科为 None）。
    """
    path = Path(eval_file)
    started = time.time()
    if path.exists():
        path.unlink()
    rc, out = run_step(["eval/evaluate.py", "--split", split, "--save"],
                       cwd=cwd, python=True)
    if rc != 0:
        return {"error": "evaluate.py 退出码 %d：%s" % (rc, " ".join(out.split())[-400:])}
    if not path.exists() or path.stat().st_mtime < started:
        return {"error": "评测未产出新文件（未落盘或路径不对）"}
    results = (json.loads(path.read_text(encoding="utf-8")) or {}).get("results") or {}
    agg = results if model_key is None else (results.get(model_key) or {})
    disc = results.get("yingqi_discrimination") or {}
    return {"avg": agg.get("avg"), "n": agg.get("n"), "rc": rc,
            "top1": disc.get("top1_hit_rate"), "rank": disc.get("avg_rank_of_correct")}

# ── 四段契约判据（第三百一十批，CONTRACT.md §四／§三）────────────────────────
# 放在共享门壳而不是各科 dev_tools：两科若各写一份，键面比对与禁边扫描必然漂移，
# 正是本模块开头说的「同一语义多份实现」。学科侧只提供自己的 layer_contract.json。

def py_imports(path) -> set[str]:
    """一个 .py 的顶层 import 模块名集合（`ast.walk`，含函数内延迟 import）。"""
    import ast
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def rel_files(root, pattern: str) -> list[str]:
    """`root` 下匹配 glob 的相对路径（正斜杠），按字典序——与平台路径分隔符无关。"""
    root = Path(root)
    return sorted(p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file())


def contract_stage_problems(observed: dict, spec: dict, *, label: str = "") -> list[str]:
    """比对一次实跑输出与契约分节；返回问题串（空列表＝合规）。

    三条判据：**多键即红**（越界新增）、**必填键缺失即红**（静默丢字段）、
    nested 白名单同样只准减不准增。`debt` 不参与判定——它只是给人看的欠账清单。
    """
    tag = f"{label}." if label else ""
    problems: list[str] = []
    keys = set(observed or {})
    allowed = set(spec.get("allowed") or ())
    required = set(spec.get("required") or ())
    for k in sorted(keys - allowed):
        problems.append(f"{tag}{k} 不在契约白名单内（越界新增字段）")
    for k in sorted(required - keys):
        problems.append(f"{tag}{k} 必填键缺失（契约声明它必须出现）")
    for name, sub in (spec.get("nested") or {}).items():
        if name not in keys:
            continue
        value = observed.get(name)
        if not isinstance(value, dict):
            problems.append(f"{tag}{name} 应为对象，实为 {type(value).__name__}")
            continue
        sub_allowed = set(sub.get("allowed") or ())
        sub_required = set(sub.get("required") or ())
        for k in sorted(set(value) - sub_allowed):
            problems.append(f"{tag}{name}.{k} 不在契约白名单内（越界新增字段）")
        for k in sorted(sub_required - set(value)):
            problems.append(f"{tag}{name}.{k} 必填键缺失")
    return problems


def contract_edge_problems(edges: dict, rules: list, *, base: str = "") -> tuple[list[str], list[str]]:
    """按禁边表核对 import 图；返回 (problems, notes)。

    `edges` = {相对路径: {import 的模块名}}。`rules` 里的 `from` 支持 glob。
    语义是「只准减不准增」：known 的边出现＝记一笔欠账（note，不红）；
    known 的边消失＝欠账已还，条目必须删（红，防台账变假事实）。
    """
    import fnmatch
    problems: list[str] = []
    notes: list[str] = []
    for rule in rules or ():
        pattern, target, known = rule.get("from"), rule.get("to"), bool(rule.get("known"))
        hits = [f for f in edges
                if fnmatch.fnmatch(f, pattern) and target in edges[f]]
        if known and hits:
            notes.append(f"欠账在册：{hits[0] if len(hits) == 1 else pattern} → {target}"
                         f"（{len(hits)} 处；{rule.get('why', '')[:60]}）")
        elif known and not hits:
            problems.append(f"欠账已还但条目还在：{pattern} → {target}——请从 layer_contract.json 删除该条")
        elif not known and hits:
            problems.append(f"新增禁边：{', '.join(hits)} → {target}（CONTRACT 零容忍）")
    return problems, notes
