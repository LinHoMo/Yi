# -*- coding: utf-8 -*-
"""门禁同步器（A0-1·第三百三十一批）：`devkit/` 是门禁内核的唯一真源。

与 `kernel/sync_kernel.py` 同机制、同范式（D2 决策：复制分发，不用 import）：

  devkit/shared/*.py        两科共用门／器的单一真源
  <科>/dev_tools/<同名>.py  **产物**，由本器写；手改即被 [37] 判红

    python devkit/sync_devkit.py --check    # 只比对（两科 check.py 的 [37] 调它）
    python devkit/sync_devkit.py --write    # 重生成两科 dev_tools/ 里的共享件
    python devkit/sync_devkit.py --selftest # 负例：改产物／缺产物／塞野文件／改门号都抓得住

528 批扩面：`--check` 与 `--selftest` 同时对拍 MANIFEST `gate_ids` 与两科 check.py 的
实际门号。此前这两份清单靠手工同步（518 批重排门号即手工改），改了 check.py 忘了改
MANIFEST 全仓照样全绿。两科门表结构不同——六爻是规整三元组、八字多数是
「`# [N]` 注释 + run([...])」顺序块，故用 AST 双路解析，不靠正则在附近抓编号
（528 批首轮正则探查即因此误报 9 处）。

**这不是跨科写**：AGENTS §二 禁的是"某一科的脚本往另一科目录里写"。本器在 `devkit/`
下，不属于任何一科，且产物本来就分属两科——它是构建器，不是学科脚本。
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEVKIT = ROOT / "devkit"
MANIFEST = DEVKIT / "MANIFEST.json"
SHARED = "shared"
ROOT_GATES = "root"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def variant_path(devkit: Path, name: str, disc: str) -> Path:
    """登记为变体的共享件：`shared/variants/<名去 .py>.<科>.py`（照 kernel 变体范式）。"""
    return devkit / SHARED / "variants" / f"{name[:-3]}.{disc}.py"


def expected_shared(manifest: dict, devkit: Path, disc: str) -> dict[str, Path]:
    """{共享件名: 该科真源路径}。变体按科取，其余取 shared/ 根。"""
    variants = manifest.get("variants", {})
    out: dict[str, Path] = {}
    for name in manifest["files"]["shared"]:
        if disc in (variants.get(name) or []):
            out[name] = variant_path(devkit, name, disc)
        else:
            out[name] = devkit / SHARED / name
    return out


def source_hygiene(manifest: dict, devkit: Path) -> list[str]:
    """真源目录里只准有在册的 `.py`——野文件即红（否则它会被当成"没分发"而隐形）。"""
    problems: list[str] = []
    for sub, key in ((SHARED, "shared"), (ROOT_GATES, "root")):
        registered = set(manifest["files"].get(key, []))
        d = devkit / sub
        if not d.exists():
            if key == "root" and not registered:
                continue  # 557 批：根级门已删除，不再要求该目录
            problems.append(f"真源目录缺 {sub}/")
            continue
        if key == "shared":
            # 共享根只放非变体项；变体项在 shared/variants/ 下按科登记
            variants = manifest.get("variants", {})
            plain = {n for n in registered if not variants.get(n)}
            for p in sorted(d.glob("*.py")):
                if p.name not in plain:
                    problems.append(f"{sub}/ 里多出未登记文件 {p.name}（该删或该进 MANIFEST）")
            for name in sorted(plain):
                if not (d / name).exists():
                    problems.append(f"{sub}/ 缺已登记真源 {name}")
            vd = d / "variants"
            registered_v = {variant_path(devkit, n, disc).name
                            for n, discs in variants.items() for disc in discs}
            if vd.exists():
                for p in sorted(vd.glob("*.py")):
                    if p.name not in registered_v:
                        problems.append(f"{sub}/variants/ 里多出未登记文件 {p.name}")
            for n, discs in variants.items():
                for disc in discs:
                    if not variant_path(devkit, n, disc).exists():
                        problems.append(f"{sub}/variants/ 缺登记变体 {n}（{disc}）")
        else:
            for p in sorted(d.glob("*.py")):
                if p.name not in registered:
                    problems.append(f"{sub}/ 里多出未登记文件 {p.name}（该删或该进 MANIFEST）")
    return problems


def drift(manifest: dict, devkit: Path, disc: str, target_dir: Path) -> list[str]:
    """返回某科共享件与真源的差异（空列表＝同源）。"""
    problems: list[str] = []
    want = expected_shared(manifest, devkit, disc)
    for name, src in want.items():
        if not src.exists():
            try:
                shown = src.relative_to(devkit)
            except ValueError:
                shown = src
            problems.append(f"{disc}：真源缺 {shown}")
            continue
        dst = target_dir / name
        if not dst.exists():
            problems.append(f"{disc}：产物缺 {name}")
        elif dst.read_bytes() != src.read_bytes():
            problems.append(f"{disc}：{name} 与 devkit/shared/ 不一致（产物被手改？）")
    # 野文件两类（A1-2 负例口径）：
    #  ① 以 `_` 开头的 .py（除 `__init__.py`）＝一次性脚本/探针，该进 scratch/；
    #  ② 与任一共享源逐字节相同的**异名**文件＝第二份手抄拷贝。
    src_bytes = {}
    for name, src in want.items():
        if src.exists():
            src_bytes[src.read_bytes()] = name
    for p in sorted(target_dir.glob("*.py")):
        if p.name in want or p.name == "__init__.py":
            continue
        if p.name.startswith("_"):
            problems.append(f"{disc}：dev_tools/ 里多出野文件 {p.name}（一次性脚本该进 scratch/）")
            continue
        try:
            data = p.read_bytes()
        except Exception:
            continue
        if data in src_bytes:
            problems.append(f"{disc}：{p.name} 是 {src_bytes[data]} 的第二份拷贝"
                            "（共享件只准有分发产物这一个名字）")
    return problems


def write_target(manifest: dict, devkit: Path, disc: str, target_dir: Path) -> list[str]:
    """按 MANIFEST 重生成共享件；**不删**学科自有的其他门（那不是产物）。"""
    actions: list[str] = []
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, src in sorted(expected_shared(manifest, devkit, disc).items()):
        if not src.exists():
            continue
        data = src.read_bytes()
        dst = target_dir / name
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)
            try:
                shown = dst.relative_to(ROOT)
            except ValueError:          # selftest 的临时目录不在仓库内
                shown = dst
            actions.append(f"写入 {shown}")
    return actions


def gate_id_map(src: str) -> dict[str, int]:
    """从 check.py 门表字面量抽 `{脚本名: [N] 编号}`。

    两科结构不同（六爻 `(key, title, script)` 三元组、八字 `(title, script)` 二元组），
    且 title 里常引用别的门号（「本科由 [14] 覆盖」之类），**只能用 AST 按元组配对**，
    正则在附近几行抓 `[N]` 会串到相邻门——528 批首轮探查就是这样误报了 9 处。
    """
    out: dict[str, int] = {}
    lines = src.splitlines()
    tree = ast.parse(src)
    # A) 规整门表：六爻 (key, title, script) 三元组／八字 (title, script) 二元组
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Tuple, ast.List)):
            continue
        for elt in node.elts:
            if not isinstance(elt, ast.Tuple):
                continue
            strs = [e.value for e in elt.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            gate, script = None, None
            for s in strs:
                m = re.match(r"^\[(\d+)\]", s)
                if m and gate is None:
                    gate = int(m.group(1))
                if s.endswith(".py") and "/" in s:
                    script = Path(s).name
            if gate is not None and script:
                out[script] = gate
    # B) 顺序式门块（八字多数门）：门号在 `# [N]` 注释或 `print("\n[N] …")` 行，
    #    脚本在紧随其后的 run([...]) 里。向上回溯，遇上一个 run 即止，避免串到别的门。
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "run" and node.args):
            continue
        arg0 = node.args[0]
        if not isinstance(arg0, (ast.List, ast.Tuple)):
            continue
        scripts = [Path(e.value).name for e in arg0.elts
                   if isinstance(e, ast.Constant) and isinstance(e.value, str)
                   and e.value.endswith(".py") and "/" in e.value]
        if not scripts:
            continue
        gate = None
        for i in range(node.lineno - 2, max(-1, node.lineno - 16), -1):
            line = lines[i]
            if "run([" in line:
                break
            m = (re.match(r"^\s*#\s*\[(\d+)\]", line)
                 or re.match(r'^\s*print\("[^"]*?\[(\d+)\]', line))
            if m:
                gate = int(m.group(1))
                break
        if gate is not None:
            for s in scripts:
                out.setdefault(s, gate)   # A) 的规整门表优先
    return out


def gate_id_problems(manifest: dict, root: Path = ROOT,
                     texts: dict[str, str] | None = None) -> list[str]:
    """MANIFEST `gate_ids`（登记值）↔ 两科 check.py 门表（实盘）逐项对拍。

    528 批此前这两份清单靠手工同步（518 批重排门号即手工改），没有门看着；
    改了 check.py 编号忘了改 MANIFEST，全仓门禁照样全绿。texts 只用于负例注入。
    """
    problems: list[str] = []
    ids = manifest.get("gate_ids") or {}
    maps: dict[str, dict[str, int]] = {}
    discs = {d for per in ids.values() for d in per}
    for disc in sorted(discs):
        rel = (manifest.get("targets") or {}).get(disc)
        if not rel:
            problems.append(f"gate_ids 登记了科 {disc}，targets 里却没有")
            continue
        p = root / rel / "check.py"
        try:
            src = texts[disc] if texts and disc in texts else p.read_text(encoding="utf-8")
            maps[disc] = gate_id_map(src)
        except (OSError, SyntaxError, UnicodeError) as e:
            problems.append(f"{disc} 的 {rel}/check.py 读不动／解析失败：{e}")
    for name, per_disc in ids.items():
        for disc, want in per_disc.items():
            got = maps.get(disc, {}).get(name)
            if got is None:
                problems.append(f"{disc}/{name}：MANIFEST 登记 [{want}]，"
                                f"但 check.py 门表里找不到该脚本（漏挂线或改了名）")
            elif got != want:
                problems.append(f"{disc}/{name} 门号分家：MANIFEST 登记 [{want}]，"
                                f"check.py 实为 [{got}]（改门号须同批改 MANIFEST）")
    return problems


def selftest() -> int:
    """负例走临时目录（AGENTS.md §四.8）：干净副本放行、改产物／缺产物／野文件都判红。"""
    manifest = {
        "files": {"shared": ["probe_shared.py", "probe_variant.py"],
                  "root": ["probe_root.py"]},
        "variants": {"probe_variant.py": ["alpha", "beta"]},
        "targets": {"alpha": "alpha/dev_tools", "beta": "beta/dev_tools"},
    }
    fails: list[str] = []
    with tempfile.TemporaryDirectory(prefix="devkit_selftest_") as td:
        t = Path(td)
        dk = t / "devkit"
        (dk / SHARED).mkdir(parents=True)
        (dk / SHARED / "variants").mkdir(parents=True)
        (dk / ROOT_GATES).mkdir(parents=True)
        src = dk / SHARED / "probe_shared.py"
        src.write_text("# shared probe\n", encoding="utf-8")
        for disc in manifest["targets"]:
            (dk / SHARED / "variants" / f"probe_variant.{disc}.py").write_text(
                f"# variant for {disc}\n", encoding="utf-8")
        (dk / ROOT_GATES / "probe_root.py").write_text("# root probe\n", encoding="utf-8")
        for disc in manifest["targets"]:
            target = t / manifest["targets"][disc]
            target.mkdir(parents=True)
            write_target(manifest, dk, disc, target)
            if drift(manifest, dk, disc, target):
                fails.append(f"{disc}：干净副本被误判")
        # 负例 1：手改产物
        victim = t / manifest["targets"]["alpha"] / "probe_shared.py"
        victim.write_bytes(victim.read_bytes() + b"\n# tamper\n")
        if not drift(manifest, dk, "alpha", victim.parent):
            fails.append("产物被手改没抓到")
        victim.write_bytes(src.read_bytes())
        # 负例 2：产物缺失
        victim.unlink()
        if not drift(manifest, dk, "alpha", victim.parent):
            fails.append("产物缺失没抓到")
        write_target(manifest, dk, "alpha", victim.parent)
        # 负例 3：真源塞野文件
        (dk / SHARED / "_stray_probe.py").write_text("# probe\n", encoding="utf-8")
        if not source_hygiene(manifest, dk):
            fails.append("真源野文件没抓到")
        (dk / SHARED / "_stray_probe.py").unlink()
        # 负例 4：真源缺已登记文件
        src.unlink()
        if not source_hygiene(manifest, dk):
            fails.append("真源缺文件没抓到")
        src.write_text("# shared probe\n", encoding="utf-8")
        # 负例 5：dev_tools 野文件（_ 前缀）
        alpha = t / manifest["targets"]["alpha"]
        (alpha / "_stray_probe.py").write_text("# probe\n", encoding="utf-8")
        if not drift(manifest, dk, "alpha", alpha):
            fails.append("dev_tools 野文件没抓到")
        (alpha / "_stray_probe.py").unlink()
        # 负例 6：第二份拷贝（异名、逐字节同源）
        (alpha / "probe_copy.py").write_bytes(src.read_bytes())
        if not drift(manifest, dk, "alpha", alpha):
            fails.append("共享件第二份拷贝没抓到")
        (alpha / "probe_copy.py").unlink()
    # 528 批：门号登记同源负例（内存注入，不碰仓库）。真仓先证干净，再改一个门号看是否判红。
    real_manifest = load_manifest()
    if gate_id_problems(real_manifest, ROOT):
        fails.append("真仓门号登记本就分家（负例前提失效，先修真仓）")
    ly_src = (ROOT / "liuyao" / "dev_tools" / "check.py").read_text(encoding="utf-8")
    anchor = '"[11] 文档活引用可达性'
    if anchor not in ly_src:
        fails.append("门号负例锚失效（[11] 标题串找不到）")
    elif not any("门号分家" in x for x in gate_id_problems(
            real_manifest, ROOT, {"liuyao": ly_src.replace(anchor, '"[99] 文档活引用可达性', 1)})):
        fails.append("check.py 门号被改没抓到")
    if fails:
        for f in fails:
            print(f"  × selftest：{f}")
        return 1
    print("  √ selftest：改产物／缺产物／真源野文件／真源缺文件／dev_tools 野文件／"
          "第二份拷贝／门号被改，七类负例全部抓到；干净副本与真仓门号登记放行")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="门禁单一真源同步器")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.write or args.selftest):
        ap.print_help()
        return 2

    manifest = load_manifest()
    if args.selftest:
        if selftest() != 0:
            return 1
        # 负例之后必须再跑一次**真盘**：只证"器是活的"不证"盘是对的"。
        problems = source_hygiene(manifest, DEVKIT)
        for disc, rel in manifest["targets"].items():
            problems += drift(manifest, DEVKIT, disc, ROOT / rel)
        problems += gate_id_problems(manifest, ROOT)
        if problems:
            for p in problems:
                print(f"  × {p}")
            return 1
        n = len(manifest["files"]["shared"])
        print(f"  √ 真盘同源：{n} 个共享件在册，分发到 "
              + "／".join(manifest["targets"]) + " 逐字节一致")
        return 0

    if args.write:
        for disc, rel in manifest["targets"].items():
            for a in write_target(manifest, DEVKIT, disc, ROOT / rel):
                print(f"  · {a}")
        print(f"  · 已重生成 {len(manifest['files']['shared'])} 个共享件"
              "（产物入库，手改会被 [37] 判红）")

    problems = source_hygiene(manifest, DEVKIT)
    for disc, rel in manifest["targets"].items():
        problems += drift(manifest, DEVKIT, disc, ROOT / rel)
    problems += gate_id_problems(manifest, ROOT)
    if problems:
        for p in problems:
            print(f"  × {p}")
        print("  → 修法：改 devkit/shared/ 后跑 `python devkit/sync_devkit.py --write`；"
              "**不要直接改 <科>/dev_tools/ 里的共享件**")
        return 1
    n = len(manifest["files"]["shared"])
    print(f"  √ 门禁同源：{n} 个共享件与 devkit/shared/ 逐字节一致"
          f"（分发目标 {len(manifest['targets'])} 科）"
          f"；gate_ids 门号登记与两科 check.py 逐项同源")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
