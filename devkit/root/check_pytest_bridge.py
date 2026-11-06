# -*- coding: utf-8 -*-
"""pytest 桥接覆盖门（第五百二十二批）：清单 × 盘上文件 × CI 直跑，逐格对拍。

    python devkit/root/check_pytest_bridge.py
    python devkit/root/check_pytest_bridge.py --selftest

为什么需要它：520 批把 main() 式测试接进 pytest 时，同一份 5 条清单在
`conftest.py:collect_ignore` 与 `bridge_test.py:_MAIN_STYLE` 各抄了一遍，
CI 的 `min-python-smoke` 又硬编码了第三份（6 条）直跑命令，**没有任何门看得见**。
更隐蔽的是 `thinking_chain_tests.py` 不匹配 `python_files = *_test.py`：
新增同类文件若不同时补三处，pytest 不收集、桥接不跑、CI 不跑，而一切全绿。
522 批把清单收进 `pytest_manifest.py` 单一真源，本门守住四件事：

  1. 覆盖：盘上每个 main() 式测试都在清单里；清单里没有悬空路径、没有原生 pytest 文件；
  2. 单一真源：conftest / bridge 只能 import 真源，不得复辟本地字面量清单；
  3. 命名盲区：不匹配 `*_test.py` 的文件必须落在清单里（否则无人收集）；
  4. CI 直跑：`.github/workflows/ci.yml` 的 `python <科>/tests/*.py` 恰好覆盖盘上全部测试。

扫到 0 个测试文件即判红（AGENTS.md §四.8：路径解析失败不许伪装成「没有孤儿」）。
自检全部走临时目录与内存注入，不碰仓库文件。
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import shutil
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
TEST_DIRS = ("liuyao/tests", "bazi/tests")
CONFIG_FILES = (
    "pytest_manifest.py",
    "conftest.py",
    "bridge_test.py",
    "pyproject.toml",
    ".github/workflows/ci.yml",
)

IMPORT_RE = re.compile(r"from\s+pytest_manifest\s+import\s+MAIN_STYLE_TESTS")
LEGACY_LIST_RE = re.compile(r"_MAIN_STYLE\s*=\s*\[")
CI_RUN_RE = re.compile(r"^\s*python\s+([A-Za-z0-9_./-]+\.py)\s*$", re.M)
TEST_RE = re.compile(r"^(?:liuyao|bazi)/tests/[^/\s]+\.py$")


def load(root: Path, rel: str, overrides: dict[str, str] | None) -> str:
    if overrides and rel in overrides:
        return overrides[rel]
    p = root / rel
    if not p.is_file():
        raise SystemExit(f"读不到 {rel}（路径解析失败，不静默放行）")
    return p.read_text(encoding="utf-8")


def manifest_list(txt: str) -> list[str]:
    """从真源 AST 抽 MAIN_STYLE_TESTS 字面量（不 import，避免依赖 pytest 环境）。"""
    tree = ast.parse(txt)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and node.target.id == "MAIN_STYLE_TESTS":
            val = node.value
        elif isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "MAIN_STYLE_TESTS" for t in node.targets):
            val = node.value
        else:
            continue
        if val is None:
            return []
        out = ast.literal_eval(val)
        if not isinstance(out, (list, tuple)) or not all(isinstance(x, str) for x in out):
            raise SystemExit("MAIN_STYLE_TESTS 必须是字符串列表/元组")
        return list(out)
    raise SystemExit("pytest_manifest.py 里找不到 MAIN_STYLE_TESTS（真源被删？）")


def is_native_pytest(txt: str) -> bool:
    """顶层存在 `def test_*` 即为原生 pytest 文件。"""
    tree = ast.parse(txt)
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
               for n in tree.body)


def discover(root: Path) -> dict[str, bool]:
    """盘上两科 tests/ 的测试文件 → 是否原生 pytest。"""
    out: dict[str, bool] = {}
    for d in TEST_DIRS:
        p = root / d
        if not p.is_dir():
            continue
        for f in sorted(p.glob("*.py")):
            if f.name.startswith("__"):
                continue
            rel = f.relative_to(root).as_posix()
            out[rel] = is_native_pytest(f.read_text(encoding="utf-8"))
    return out


def ci_test_runs(txt: str) -> set[str]:
    return {m for m in CI_RUN_RE.findall(txt) if TEST_RE.match(m)}


def check(root: Path = ROOT, overrides: dict[str, str] | None = None,
          discovered: dict[str, bool] | None = None) -> list[str]:
    problems: list[str] = []
    texts = {rel: load(root, rel, overrides) for rel in CONFIG_FILES}
    found = discover(root) if discovered is None else dict(discovered)

    # 0 文件判红：路径解析错了不许报「全绿」。
    if not found:
        problems.append("扫到 0 个测试文件（TEST_DIRS 路径解析失败，不静默放行）")

    try:
        listed = manifest_list(texts["pytest_manifest.py"])
    except SystemExit as e:
        return [str(e)]
    listed_set = set(listed)
    if len(listed) != len(listed_set):
        problems.append(f"MAIN_STYLE_TESTS 有重复项：{len(listed)} 条 / 去重 {len(listed_set)} 条")
    for rel in listed:
        if "/" not in rel or rel.startswith("/") or ".." in rel:
            problems.append(f"清单路径必须是相对仓库根的 posix 路径：`{rel}`")

    main_style = {rel for rel, native in found.items() if not native}
    # 1. 逐格对拍：漏登记 / 悬空 / 原生误入
    for rel in sorted(main_style - listed_set):
        problems.append(f"漏登记：`{rel}` 是 main() 式测试却不在清单里（pytest 不收集、桥接也不跑）")
    for rel in sorted(listed_set - set(found)):
        problems.append(f"悬空：清单里的 `{rel}` 在盘上不存在")
    for rel in sorted(listed_set & {r for r, n in found.items() if n}):
        problems.append(f"原生 pytest 文件 `{rel}` 被误列进桥接清单（会被 collect_ignore 排除）")

    # 2. 单一真源：两份消费方只能 import，不得再抄一份清单
    for rel in ("conftest.py", "bridge_test.py"):
        txt = texts[rel]
        if not IMPORT_RE.search(txt):
            problems.append(f"{rel} 没有 `from pytest_manifest import MAIN_STYLE_TESTS`（清单真源被绕开）")
        if LEGACY_LIST_RE.search(txt):
            problems.append(f"{rel} 复辟了本地 `_MAIN_STYLE = [...]` 清单（双份清单必漂移）")
    if "collect_ignore" not in texts["conftest.py"]:
        problems.append("conftest.py 缺 collect_ignore（两科 tests 同名包会撞车）")
    if "parametrize" not in texts["bridge_test.py"]:
        problems.append("bridge_test.py 缺 parametrize（桥接用例没了）")

    # 3. 命名盲区：不匹配 python_files 的文件必须靠桥接覆盖
    for rel in sorted(found):
        name = Path(rel).name
        if not fnmatch.fnmatch(name, "*_test.py") and rel not in listed_set:
            problems.append(f"命名盲区：`{rel}` 不匹配 python_files 且不在桥接清单里（无人收集）")

    # 4. pytest / CI 配置：根 bridge_test.py 必须被收集，CI 直跑必须覆盖全部测试
    if not re.search(r'^\s*testpaths\s*=\s*\[\s*"\."\s*\]', texts["pyproject.toml"], re.M):
        problems.append('pyproject.toml 的 testpaths 不含仓库根 "."（根 bridge_test.py 不会被收集）')
    runs = ci_test_runs(texts[".github/workflows/ci.yml"])
    if not runs:
        problems.append("CI 里扫到 0 条 `python <科>/tests/*.py` 直跑命令（路径解析失败？）")
    for rel in sorted(set(found) - runs):
        problems.append(f"CI 直跑漏了 `{rel}`（min-python-smoke 硬编码清单没跟上）")
    for rel in sorted(runs - set(found)):
        problems.append(f"CI 直跑了盘上不存在的 `{rel}`")

    return problems


def _probe_root(tmp: Path) -> Path:
    """造一个与真仓同形的临时仓（测试文件内容照抄，配置文件照抄）。"""
    for d in TEST_DIRS:
        (tmp / d).mkdir(parents=True, exist_ok=True)
        for f in (ROOT / d).glob("*.py"):
            shutil.copy2(f, tmp / d / f.name)
    for rel in CONFIG_FILES:
        dst = tmp / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text((ROOT / rel).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp


def selftest() -> int:
    """负例自证：全绿的新门先怀疑、再证明。"""
    base = check()
    if base:
        print("  [selftest] 真仓自身就判红，先修真仓：")
        for p in base:
            print("    - " + p)
        return 1
    print(f"  [selftest] 真仓基线：{len(discover(ROOT))} 个测试文件、"
          f"{len(manifest_list(load(ROOT, 'pytest_manifest.py', None)))} 条桥接清单、0 问题")

    cfg = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in CONFIG_FILES}
    ov = lambda **kw: {**cfg, **kw}  # noqa: E731
    cases: list[tuple[str, dict[str, str] | None, dict[str, bool] | None]] = []

    lst = manifest_list(cfg["pytest_manifest.py"])
    # 真删一行：判红必须来自「漏登记」分支本身，不能被路径格式断言顺手挡下。
    cases.append(("清单漏一项", ov(**{"pytest_manifest.py": cfg["pytest_manifest.py"].replace(
        f'    "{lst[0]}",\n', '')}), None))
    cases.append(("清单塞悬空路径", ov(**{"pytest_manifest.py": cfg["pytest_manifest.py"].replace(
        "MAIN_STYLE_TESTS: tuple[str, ...] = (",
        'MAIN_STYLE_TESTS: tuple[str, ...] = (\n    "liuyao/tests/__no_such_probe.py",')}), None))
    native = next(r for r, n in discover(ROOT).items() if n)
    cases.append(("原生 pytest 误入清单", ov(**{"pytest_manifest.py": cfg["pytest_manifest.py"].replace(
        "MAIN_STYLE_TESTS: tuple[str, ...] = (",
        f'MAIN_STYLE_TESTS: tuple[str, ...] = (\n    "{native}",')}), None))
    cases.append(("conftest 复辟本地清单", ov(**{"conftest.py": cfg["conftest.py"] + "\n_MAIN_STYLE = []\n"}), None))
    cases.append(("bridge 复辟本地清单", ov(**{"bridge_test.py": cfg["bridge_test.py"] + "\n_MAIN_STYLE = []\n"}), None))
    cases.append(("conftest 绕开真源", ov(**{"conftest.py": cfg["conftest.py"].replace(
        "from pytest_manifest import MAIN_STYLE_TESTS", "MAIN_STYLE_TESTS = ()")}), None))
    cases.append(("CI 直跑漏一项", ov(**{".github/workflows/ci.yml": cfg[".github/workflows/ci.yml"].replace(
        f"          python {native}\n", "")}), None))
    cases.append(("testpaths 不再含根", ov(**{"pyproject.toml": cfg["pyproject.toml"].replace(
        'testpaths = ["."]', 'testpaths = ["liuyao"]')}), None))
    cases.append(("盘上新增 main() 式文件却没补清单", None,
                  {**discover(ROOT), "liuyao/tests/new_probe_tests.py": False}))
    cases.append(("扫到 0 个测试文件", None, {}))

    bad = 0
    for name, overrides, found in cases:
        got = check(overrides=overrides, discovered=found)
        ok = bool(got)
        print(f"  [selftest] {name}：{'判红 √' if ok else '**没判红（门是假绿）**'}"
              + (f" → {got[0]}" if got else ""))
        bad += 0 if ok else 1

    # 真探针：临时盘上真加一个文件 / 真删一个文件，门必须判红；原样必须判绿。
    with tempfile.TemporaryDirectory() as td:
        tmp = _probe_root(Path(td))
        if check(root=tmp):
            print("  [selftest] 临时仓同形副本应判绿却判红（门误报）")
            bad += 1
        else:
            print("  [selftest] 临时仓同形副本：判绿 √")
        (tmp / "liuyao/tests" / "extra_probe_tests.py").write_text(
            "# main() 式探针\nerrs = []\nprint('ok')\n", encoding="utf-8")
        got = check(root=tmp)
        print(f"  [selftest] 真探针·临时盘新增未登记测试：{'判红 √' if got else '**没判红**'}")
        bad += 0 if got else 1

    if bad:
        print(f"[selftest] 失败 {bad} 项")
        return 1
    print("[selftest] 10 类负例 + 临时盘同形判绿 / 真探针判红各 1 项，全部通过")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="pytest 桥接清单覆盖门")
    ap.add_argument("--selftest", action="store_true", help="跑负例自证")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    problems = check()
    found = discover(ROOT)
    print(f"pytest 桥接覆盖：测试文件 {len(found)} 个"
          f"（原生 {sum(found.values())} / main() 式 {sum(not v for v in found.values())}）、"
          f"CI 直跑 {len(ci_test_runs(load(ROOT, '.github/workflows/ci.yml', None)))} 条")
    if problems:
        for p in problems:
            print("  × " + p)
        print(f"覆盖门判红：{len(problems)} 条")
        return 1
    print("√ 清单单一真源、覆盖、命名盲区与 CI 直跑全部对拍一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
