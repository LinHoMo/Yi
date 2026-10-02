# -*- coding: utf-8 -*-
"""案例库隔离门（AGENTS.md 铁律二 · 架构评审 A1 的机械化落地）。

  python tools/case_isolation_check.py             # 静态层 + 运行层（默认，仍 <1s）
  python tools/case_isolation_check.py --fast      # 只跑静态层（与仓库其他门同名约定）
  python tools/case_isolation_check.py --trace     # 额外打印解读路径 import 闭包
  python tools/case_isolation_check.py --root DIR  # 扫另一棵同布局的树（证伪测试用）

失败退出码 1，全绿退出码 0。

`--fast` 既是"只跑静态层"的快捷方式，也是**防误伤**：`tools/check.py` 的
`gate_sub()` 会对以 `check.py` 结尾的命令自动注入 `--fast`（本门文件名正好命中），
本门接受它，免得未来有人把它当普通 check 挂上去时被注入打挂。

铁律二（AGENTS.md §一.2）：`**/cases/` 与 `references/case_library.md` 只允许三种访问
场景——测试运行器读取、用户明确要求事后校验、用户主动询问有无类似案例；解读交付前
禁止打开案例库。架构评审 A1 指出：这是三条铁律里**唯一完全没有机械支撑**的一条，
风险不是"已经违规"，而是"无法证明没有违规"。本门把它变成机械可达。

========================= 覆盖边界（诚实标注，勿误读为全覆盖） =========================
静态层（始终执行）
  1) 解读路径的 import 闭包：`disciplines/<科>/scripts/{chart,analyze,narrate,render}.py`
     及其在本科可解析到的本地 import 的传递闭包（同目录模块 + 学科根下的包）；
  2) core 层：`core/yishu_core/**/*.py`（内核不该知道案例库的存在）。
  判据（AST 级，注释不计入）：
    · 字符串字面量命中案例资源路径模式（CASE_PATH_PATTERNS）；
    · 标识符命中案例读取符号名（CASE_SYMBOL_NAMES）；
    · 裸 "cases" 被当作路径分量使用（`Path(...) / "cases"`、`rglob("cases")` 等）；
    · 闭包内某模块 import 到了白名单里的案例读取器。
运行层（默认执行；`--fast` 可关）
  借 Python 3.8+ 的 `sys.addaudithook` 记录真实 `open` 事件，在**受控子进程**里同进程
  runpy 跑一份正常解读请求（chart→analyze→render），断言没有任何一次打开落在
  `data/cases/**` 或 `references/case_library.md`。这一层不看源码形状，抓真实行为；
  与 `tools/check.py` 的黑箱取证哲学（verdict_audit）一致。
  （默认探针学科：ming、liuyao——两者都有真实案例库，liuyao 另带 case_library.md。）

**未覆盖（已知边界，不要当成本门守住了）**：
  · 只扫"解读路径"这一条链：`tools/report.py`、`cli/`、`synthesis/`、`web/` 的源码不扫
    （本轮把范围限定为学科 scripts 闭包 + core；这些入口当前对案例库是干净的）；
  · 非四段入口的解读脚本（如六爻 `scripts/yi_liuyao.py` 一键闭环）不在闭包内 → 不扫；
  · 案例库内容是否被**抄进**断语/语料：那是 [1c] verdict_audit 的职责，不是本门；
  · 运行层只跑固定几例请求，覆盖"这份报告读过什么"，不覆盖任意分支；
  · 运行层是同进程 runpy 跑学科三段（chart→analyze→render），审计 hook 只看得到
    **本进程**的 open；学科脚本若自己起子进程读文件，hook 看不到；
  · 经非 Python 途径（子进程调外部脚本）读案例：静态层抓不到，运行层也抓不到。

例外白名单（最小集，依据写在这里，不放宽判据本身）：
  · `scripts/case_runner.py`、`scripts/evaluate.py`：铁律明文允许的"测试/评测运行器"，
    它们就是为读案例做回归审计而存在；
  · `dev_tools/`、`tests/`：同类，开发工具与测试目录。
  白名单只作用于**被扫的落点**：闭包 BFS 不进入这些文件内部（它们内部对案例库的引用
  是允许的）。但若解读路径**import 到了** `case_runner.py`/`evaluate.py`，仍判失败——
  那意味着案例库在解读期变为可达。
=========================================================================================
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# 默认仓库根：本文件在 <root>/tools/ 下，按仓库根相对解析（不硬编码绝对路径）
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

# 四段契约的解读入口（解读路径的起点）
CONTRACT_ENTRIES = ("chart.py", "analyze.py", "narrate.py", "render.py")

# 铁律二允许的"测试/评测运行器"落点（白名单，最小集）
ALLOWED_READER_BASENAMES = {"case_runner.py", "evaluate.py"}
ALLOWED_TOOL_DIRS = {"dev_tools", "tests"}

# 案例资源路径模式（作用于**字符串字面量**，注释天然不计入）
CASE_PATH_PATTERNS = tuple(re.compile(p) for p in (
    r"case_library",           # references/case_library.md
    r"data[/\\]cases",         # 案例库目录
    r"(?<![\w.])cases[/\\]",   # "…/cases/…" 路径片段
    r"[/\\]cases(?![\\/\w.-])",  # "…/cases" 结尾
    r"[\w-]+_cases\.json",     # huozhulin_cases.json / ming_cases.json …
    r"case_splits\.json",
    r"eval_(?:tune|holdout|[a-z0-9_]*holdout)\.json",
    r"course_examples\.json",
    r"huozhulin",              # 古籍案例来源名（火珠林）
    r"wikisource",             # 古籍案例来源名（维基文库）
))

# 案例读取器接口的符号名（比 "cases"/"CASES" 精确：后者在同仓被当"测试用例"用，误报率高）
CASE_SYMBOL_NAMES = frozenset({
    "case_runner", "case_library",
    "load_cases", "load_case", "load_ids", "run_cases", "run_ids",
    "DEFAULT_CASES", "CASES_PATH", "cases_file",
})

# 裸 "cases" 作为路径分量时的用法（Path(...) / "cases"、os.path.join(..., "cases")、rglob("cases")）
_PATH_COMPONENT_CALLS = {"join", "glob", "rglob", "iterdir"}
_CASE_COMPONENT_LITERALS = {"cases", "data/cases", "cases/"}


# ── 判定原语 ───────────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return text.replace("\\", "/")


def case_marker(text: str) -> str | None:
    """字符串里是否出现案例资源标记；返回命中的片段，否则 None。"""
    if not text:
        return None
    t = _norm(text)
    for pat in CASE_PATH_PATTERNS:
        m = pat.search(t)
        if m:
            return m.group(0)
    return None


def is_case_resource(path_str: object) -> bool:
    """一个**实际被打开的文件路径**是否属于案例库（运行层用）。"""
    try:
        t = _norm(str(path_str))
    except Exception:
        return False
    if "case_library" in t:
        return True
    parts = [x for x in t.split("/") if x]
    if "cases" in parts and "data" in parts:
        return True
    return case_marker(t) is not None


def _short(text: str, n: int = 60) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[:n] + "…"


def _parse(path: Path) -> ast.AST | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return None


def _rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root))
    except ValueError:
        return str(p)


# ── 单模块扫描（AST 级） ───────────────────────────────────────────────────

def scan_module(path: Path) -> list[dict]:
    """扫一个模块里的案例资源引用；返回 [{line, kind, detail}]。

    只认 AST 节点（常量字符串 / 标识符 / 路径分量），注释与文档说明中的散文不计入；
    docstring 属字符串常量，会计入——解读路径里出现案例字样本身就值得复核。
    """
    tree = _parse(path)
    if tree is None:
        return [{"line": 0, "kind": "解析失败",
                 "detail": "无法解析（SyntaxError）——解读路径的可解析性由 [1] 门另守"}]
    hits: list[dict] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            m = case_marker(node.value)
            if m:
                hits.append({"line": node.lineno, "kind": "字符串字面量",
                             "detail": f"「{_short(node.value)}」命中案例资源标记「{m}」"})
        elif isinstance(node, ast.Name) and node.id in CASE_SYMBOL_NAMES:
            hits.append({"line": node.lineno, "kind": "案例读取符号",
                         "detail": f"标识符 {node.id}（案例读取器接口）"})
        elif isinstance(node, ast.Attribute) and node.attr in CASE_SYMBOL_NAMES:
            hits.append({"line": node.lineno, "kind": "案例读取符号",
                         "detail": f"属性 .{node.attr}（案例读取器接口）"})
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            for side in (node.left, node.right):
                if isinstance(side, ast.Constant) and side.value == "cases":
                    hits.append({"line": node.lineno, "kind": "路径分量",
                                 "detail": "把字面量 “cases” 拼进路径（疑似案例库目录）"})
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else (
                fn.id if isinstance(fn, ast.Name) else None)
            if name in _PATH_COMPONENT_CALLS:
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                            and _norm(arg.value).strip("/") in _CASE_COMPONENT_LITERALS:
                        hits.append({"line": node.lineno, "kind": "路径分量",
                                     "detail": f"{name}(「{arg.value}」) 疑似遍历案例库目录"})
    hits.sort(key=lambda h: h["line"])
    return hits


# ── import 闭包 ───────────────────────────────────────────────────────────

def _import_targets(path: Path) -> list[tuple[str, int, int]]:
    """模块的 import 目标：(模块名, 行号, 相对层级)。"""
    tree = _parse(path)
    if tree is None:
        return []
    out: list[tuple[str, int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.append((a.name, node.lineno, 0))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                out.append((node.module, node.lineno, node.level))
            elif node.level:                      # from . import x
                for a in node.names:
                    out.append((a.name, node.lineno, node.level))
    return out


def _resolve_local(mod: str, level: int, scripts_dir: Path, disc_dir: Path) -> Path | None:
    """把 import 目标解析成本仓文件；非本科本地模块（core/stdlib/第三方）返回 None。"""
    parts = [p for p in mod.split(".") if p]
    if not parts:
        return None
    bases = [scripts_dir] if level else [scripts_dir, disc_dir]
    for base in bases:
        cand = base.joinpath(*parts)
        for probe in (cand.with_suffix(".py"), cand / "__init__.py"):
            if probe.is_file():
                return probe
    return None


def _reader_label(p: Path, disc_dir: Path) -> str | None:
    """p 是案例读取器 / 开发测试目录 → 返回类别说明（白名单依据），否则 None。

    判定只看**学科目录下的相对路径**：若拿绝对路径的任意一段去比 dev_tools/tests，
    仓库恰好装在含 "tests" 的路径下时会把整棵树误判成白名单。
    """
    if p.name in ALLOWED_READER_BASENAMES:
        return f"案例读取器 {p.name}"
    try:
        rel = p.relative_to(disc_dir)
    except ValueError:
        return None
    if rel.parts and rel.parts[0] in ALLOWED_TOOL_DIRS:
        return f"开发/测试工具目录（{rel.parts[0]}/）"
    return None


def import_closure(entries: list[Path], scripts_dir: Path, disc_dir: Path):
    """从四段入口出发的本地 import 传递闭包。

    返回 (闭包文件集合, 闭包内触达读取器的记录, 被跳过的开发/测试目录记录)。
    BFS 不进入读取器/开发工具目录内部——它们内部对案例库的引用是铁律允许的。
    """
    seen: dict[Path, Path | None] = {}
    stack: list[Path] = []
    for e in entries:
        if e.is_file() and e not in seen:
            seen[e] = None
            stack.append(e)
    reached_readers: list[tuple[Path, int, str, Path, str]] = []
    skipped_tools: list[tuple[Path, int, Path]] = []
    while stack:
        cur = stack.pop()
        for mod, lineno, level in _import_targets(cur):
            tgt = _resolve_local(mod, level, scripts_dir, disc_dir)
            if tgt is None or tgt in seen:
                continue
            label = _reader_label(tgt, disc_dir)
            if label:
                if tgt.name in ALLOWED_READER_BASENAMES:
                    reached_readers.append((cur, lineno, mod, tgt, label))
                else:
                    skipped_tools.append((cur, lineno, tgt))
                continue
            seen[tgt] = cur
            stack.append(tgt)
    return set(seen), reached_readers, skipped_tools


# ── 静态层 ────────────────────────────────────────────────────────────────

def static_scan(root: Path) -> tuple[list[str], dict]:
    fails: list[str] = []
    info: dict = {"closures": {}, "modules": 0, "core_modules": 0, "notes": []}

    disc_root = root / "disciplines"
    for disc_dir in sorted(p for p in disc_root.glob("*") if p.is_dir()):
        scripts = disc_dir / "scripts"
        if not scripts.is_dir():
            continue
        entries = [scripts / n for n in CONTRACT_ENTRIES]
        present = [e for e in entries if e.is_file()]
        if not present:
            continue
        closure, reached, skipped = import_closure(present, scripts, disc_dir)
        info["closures"][disc_dir.name] = sorted(_rel(root, p) for p in closure)
        for cur, lineno, mod, tgt, label in reached:
            fails.append(f"{_rel(root, cur)}:{lineno}: 解读路径 import 到{label}"
                         f"（{mod} → {_rel(root, tgt)}）——铁律二：解读期案例库不得可达")
        for cur, lineno, tgt in skipped:
            info["notes"].append(f"{_rel(root, cur)}:{lineno}: 解读路径引用开发工具 "
                                 f"{_rel(root, tgt)}（白名单放行，不进入其内部）")
        for p in sorted(closure):
            info["modules"] += 1
            for h in scan_module(p):
                fails.append(f"{_rel(root, p)}:{h['line']}: {h['kind']}——{h['detail']}")

    core = root / "core" / "yishu_core"
    if core.is_dir():
        for p in sorted(core.rglob("*.py")):
            if "__pycache__" in p.parts:
                continue
            info["core_modules"] += 1
            for h in scan_module(p):
                fails.append(f"{_rel(root, p)}:{h['line']}: {h['kind']}——{h['detail']}"
                             f"（内核不该知道案例库的存在）")
    return fails, info


# ── 运行层（审计 hook 实跑） ───────────────────────────────────────────────

# 运行层探针用的请求（与 verdict_audit / verify_web_parity 同源的正例形状）
PROBE_REQUESTS = {
    "liuyao": {"discipline": "liuyao", "question": "占本周面试能否通过",
               "mode": "time", "datetime": "2026-09-30 10:30"},
    "ming": {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
    "meihua": {"discipline": "meihua", "question": "占投资", "datetime": "2026-09-30 10:30"},
    "xiaoliuren": {"discipline": "xiaoliuren", "question": "占出行",
                   "datetime": "2026-09-30 10:30"},
    "zeji": {"discipline": "zeji", "date": "2026-09-30", "activity": "开市"},
    "liuren": {"discipline": "liuren", "question": "占合作",
               "datetime": "2026-09-30 10:30", "gender": "男"},
}
DEFAULT_PROBE = ("ming", "liuyao")


def probe_serve(root: Path, discipline: str) -> int:
    """[子进程入口] 装审计 hook，同进程 runpy 跑完一份解读请求，报告打开过的案例资源。"""
    import runpy

    for cand in (root / "core", DEFAULT_ROOT / "core"):
        if cand.is_dir() and str(cand) not in sys.path:
            sys.path.append(str(cand))
    from yishu_core.report import (analyze_argv, chart_argv, normalize_request,  # noqa: E402
                                   render_argv)

    opened: list[str] = []

    def _hook(event: str, args: tuple) -> None:
        if event == "open" and args:
            try:
                opened.append(os.fspath(args[0]))
            except Exception:
                pass

    sys.addaudithook(_hook)

    req = normalize_request(PROBE_REQUESTS[discipline])
    scripts = root / "disciplines" / discipline / "scripts"
    sys.path.insert(0, str(scripts))
    tmp = Path(tempfile.mkdtemp(prefix=f"case_probe_{discipline}_"))
    chart_p, analyze_p, md_p = tmp / "chart.json", tmp / "analyze.json", tmp / "report.md"

    stages = (
        ("chart", chart_argv(req, str(scripts / "chart.py"), str(chart_p))),
        ("analyze", analyze_argv(req, str(scripts / "analyze.py"), str(chart_p),
                                 str(analyze_p))),
        ("render", render_argv(req, str(scripts / "render.py"), str(analyze_p), str(md_p))),
    )
    status: dict[str, str] = {}
    for name, argv in stages:
        sys.argv = list(argv)
        try:
            runpy.run_path(argv[0], run_name="__main__")
            status[name] = "ok"
        except SystemExit as exc:
            code = exc.code
            status[name] = "ok" if code in (0, None) else f"exit {code}"
            if code not in (0, None):
                break
        except BaseException as exc:                       # noqa: BLE001 探针须报出任何炸法
            status[name] = f"{type(exc).__name__}: {exc}"
            break

    hits = sorted({p for p in opened if is_case_resource(p)})
    print("CASE_PROBE_JSON " + json.dumps(
        {"discipline": discipline, "status": status, "n_open": len(opened),
         "case_hits": hits}, ensure_ascii=False))
    return 1 if hits else 0


def runtime_scan(root: Path, disciplines: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """跑运行层探针；返回 (判败项, 说明行)。"""
    fails: list[str] = []
    lines: list[str] = []
    for d in disciplines:
        script = root / "disciplines" / d / "scripts" / "chart.py"
        if not script.is_file():
            # 换根扫（证伪测试）时该科可能不存在——跳过并说明，不得因此判败
            lines.append(f"  · {d}：该根下无此科（缺 {_rel(root, script)}），探针跳过")
            continue
        if d not in PROBE_REQUESTS:
            fails.append(f"运行层探针 {d}：未登记该科的探针请求（PROBE_REQUESTS），无法探")
            continue
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--root", str(root),
             "--probe-serve", d],
            cwd=str(root), capture_output=True, text=True, encoding="utf-8",
            errors="replace")
        out = (proc.stdout or "") + (proc.stderr or "")
        payload = None
        for line in out.splitlines():
            if line.startswith("CASE_PROBE_JSON "):
                try:
                    payload = json.loads(line[len("CASE_PROBE_JSON "):])
                except json.JSONDecodeError:
                    payload = None
        if payload is None:
            fails.append(f"运行层探针 {d}：未取到结果（退出码 {proc.returncode}）\n"
                         f"      …{_short(out.strip()[-200:], 200)}")
            continue
        bad_stage = {k: v for k, v in payload["status"].items() if v != "ok"}
        if payload["case_hits"]:
            for p in payload["case_hits"]:
                fails.append(f"运行层探针 {d}：解读过程打开过案例资源 {p}"
                             f"——铁律二：解读期不得打开案例库")
        elif bad_stage:
            fails.append(f"运行层探针 {d}：解读未跑完 {bad_stage}（探针无效，非隔离结论）")
        else:
            lines.append(f"  √ {d}：解读全链 {payload['n_open']} 次打开，"
                         f"无一落在案例库")
    return fails, lines


# ── CLI ───────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        from yishu_core.runtime import force_utf8_stdio
        force_utf8_stdio()
    except Exception:
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    ap = argparse.ArgumentParser(
        description="案例库隔离门（AGENTS.md 铁律二）：预测/解读路径不得触达案例库")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                    help="仓库根（默认按本文件位置解析；证伪测试可指向另一棵同布局的树）")
    ap.add_argument("--fast", action="store_true",
                    help="只跑静态层（不跑运行层探针）；默认两层都跑")
    ap.add_argument("--probe", nargs="*", default=None, metavar="学科",
                    help=f"运行层探针覆盖的学科（默认：{'、'.join(DEFAULT_PROBE)}）")
    ap.add_argument("--trace", action="store_true", help="打印解读路径 import 闭包")
    ap.add_argument("--probe-serve", metavar="学科", help=argparse.SUPPRESS)
    args = ap.parse_args()

    root = args.root.resolve()
    if args.probe_serve:                       # 子进程入口：只跑探针，不跑门
        return probe_serve(root, args.probe_serve)
    if not (root / "disciplines").is_dir():
        print(f"× 不是仓库根（缺 disciplines/）：{root}")
        return 1

    fails, info = static_scan(root)

    print(f"案例库隔离门（铁律二）：仓库根 {root}")
    print(f"  静态层：解读路径 {info['modules']} 个模块（{len(info['closures'])} 科闭包）"
          f" + core {info['core_modules']} 个模块")
    if args.trace:
        for disc, files in sorted(info["closures"].items()):
            print(f"    · {disc}：{len(files)} 模块")
            for f in files:
                print(f"        - {f}")
        for note in info["notes"]:
            print(f"    ↷ {note}")

    probe_disciplines = tuple(args.probe) if args.probe else DEFAULT_PROBE
    if not args.fast:
        rt_fails, rt_lines = runtime_scan(root, probe_disciplines)
        print("  运行层（审计 hook 实跑解读请求）：探针 " + "、".join(probe_disciplines))
        for line in rt_lines:
            print(line)
        fails.extend(rt_fails)
    else:
        print("  运行层：未执行（--fast；本次只覆盖静态层）")

    if fails:
        print(f"  × 发现 {len(fails)} 处案例库隔离违规：")
        for f in fails:
            print(f"      · {f}")
        print("  依据：AGENTS.md §一.2 铁律二——`**/cases/` 与 "
              "`references/case_library.md` 只许测试运行器/事后校验/用户主动询问三种访问。")
        return 1
    print("  √ 解读路径未触达案例库（静态层"
          + ("，运行层未跑" if args.fast else "+运行层") + "）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
