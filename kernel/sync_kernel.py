# -*- coding: utf-8 -*-
"""内核同步器（C2·第三百一十六批）：`kernel/` 是唯一真源，两科 `core/yishu_core/` 是产物。

为什么要有它（截至 316 批的事实）：两科内核 17 个同名文件里 13 个逐字节相同、4 个分叉。
"各自演进"的说法掩盖了一件事——**同一份代码在手抄两遍**，改一次要写两遍，
写漏一遍没有任何门看得见（312 批之前 `narrative_utils` 被删而 10 个模块仍 import，就是同族）。

本器把关系倒过来：
  kernel/yishu_core/common/*.py          两科共用（单一真源）
  kernel/yishu_core/variants/<名>.<科>.py 登记在册的分叉（4 个）
  <科>/core/yishu_core/*.py               **产物**，由本器写；手改即被判红

    python kernel/sync_kernel.py --check    # 只比对（check.py 的 [35] 调它）
    python kernel/sync_kernel.py --write    # 重生成两科内核（会删掉产物里的多余 .py）
    python kernel/sync_kernel.py --selftest # 负例：证明"改了产物"与"多了野文件"都抓得住
    python kernel/sync_kernel.py --standalone liuyao --out <目录>
                                            # 产出可独立拷走的目录（D1=C 的显式命令）

**这不是跨科写**：AGENTS §二 禁的是"某一科的脚本往另一科目录里写"。本器在 `kernel/` 下，
不属于任何一科，且产物本来就分属两科——它是构建器，不是学科脚本。

**539 批补子包**：`common/report/` 自 316 批起在两科产物里各存一份（render 段与 check.py
都 import 它），却既无 kernel 真源、也不在本器的 `glob("*.py")` 视野内——等于「手抄两遍、
无人比对」。本批改以**产物相对路径**为键（平铺模块 + 子包递归），`rglob` 收集产物，
`MANIFEST.json` 的 `packages` 登记子包名；[35] 由此覆盖整个 `yishu_core/` 而不只是顶层。
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KERNEL = ROOT / "kernel"
MANIFEST = KERNEL / "MANIFEST.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _rel_py_files(target_dir: Path) -> set[str]:
    """产物目录下所有 .py 的**相对路径**（POSIX 分隔），跳过 __pycache__。

    539 批前用 `glob("*.py")` 只看顶层，`report/` 子包整个隐身；改用 rglob 后
    子包里的手改与野文件同样进 [35] 的判红面。
    """
    return {
        p.relative_to(target_dir).as_posix()
        for p in target_dir.rglob("*.py")
        if "__pycache__" not in p.parts
    }


def expected_files(manifest: dict, disc: str) -> dict[str, Path]:
    """某科应有的 {产物相对路径: 真源路径}。

    平铺模块（`common` / `<科>_only` / `variants`）的键就是文件名；`packages` 登记的
    子包按 `common/<pkg>/**/*.py` 递归展开，键为 `report/html.py` 这类相对路径。
    统一相对路径后，比对、写入、standalone 三处共用同一套键。
    """
    src = KERNEL / "yishu_core"
    common = src / "common"
    files = manifest["files"]
    out: dict[str, Path] = {}
    for name in files["common"]:
        out[name] = common / name
    for name in files.get(f"{disc}_only", []):
        out[name] = common / name
    for name in manifest.get("variants", []):
        out[name] = src / "variants" / name.replace(".py", f".{disc}.py")
    for pkg in manifest.get("packages", []):
        pkg_src = common / pkg
        for p in sorted(pkg_src.rglob("*.py")):
            if "__pycache__" not in p.parts:
                out[p.relative_to(common).as_posix()] = p
    return out


def drift(manifest: dict, disc: str, target_dir: Path) -> list[str]:
    """返回该科内核与真源的差异（空列表＝同源）。"""
    problems: list[str] = []
    # 子包真源缺目录时 expected_files 会静默返回空集——必须显式判红，
    # 否则「真源整个被删」会被读成「该科不需要这个包」。
    for pkg in manifest.get("packages", []):
        if not (KERNEL / "yishu_core" / "common" / pkg).is_dir():
            problems.append(f"{disc}：packages 登记的子包真源缺目录 kernel/yishu_core/common/{pkg}")
    want = expected_files(manifest, disc)
    for rel, src in want.items():
        if not src.exists():
            problems.append(f"{disc}：真源缺 {src.relative_to(ROOT)}")
            continue
        dst = target_dir / rel
        if not dst.exists():
            problems.append(f"{disc}：产物缺 {rel}")
        elif dst.read_bytes() != src.read_bytes():
            problems.append(f"{disc}：{rel} 与 kernel/ 不一致（产物被手改？）")
    extra = sorted(_rel_py_files(target_dir) - set(want))
    for rel in extra:
        problems.append(f"{disc}：产物里多出未登记文件 {rel}（该删或该进 manifest）")
    return problems


def write_target(manifest: dict, disc: str, target_dir: Path) -> list[str]:
    """按 manifest 重生成；删除未登记的 .py（含子包）。返回动作清单。"""
    actions: list[str] = []
    want = expected_files(manifest, disc)
    target_dir.mkdir(parents=True, exist_ok=True)
    for rel, src in sorted(want.items()):
        data = src.read_bytes()
        dst = target_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)
            actions.append(f"写入 {dst.relative_to(ROOT)}")
    for rel in sorted(_rel_py_files(target_dir) - set(want)):
        (target_dir / rel).unlink()
        actions.append(f"删除 {(target_dir / rel).relative_to(ROOT)}（未登记/该科不收）")
    # 清掉因删文件留下的空子目录（不递归删非空目录，避免误伤）
    for d in sorted((p for p in target_dir.rglob("*") if p.is_dir() and "__pycache__" not in p.parts),
                    key=lambda p: len(p.parts), reverse=True):
        try:
            d.rmdir()
            actions.append(f"移除空目录 {d.relative_to(ROOT)}")
        except OSError:
            pass
    return actions


def standalone(disc: str, out: Path) -> int:
    """产出一份可独立拷走的学科目录（D1=C）：core ＋ scripts ＋ 运行必需 data。

    为什么不带 `data/cases/` 与 `data/sources/`：那是语料/古籍底本（八字侧 49MB），
    拷贝它们会把"单目录可运行"变成"单目录 65MB"；chart/analyze/narrate/render 的
    运行只需 `data/rules`、`data/golden` 与顶层 `data/*.json`。

    539 批补 `engine/` 与 `rules/`：508 批把推演链从 `scripts/engine` 升格到
    `<学科根>/engine/` 后，本器仍只拷 core+scripts，拷走后 `chart.py` 的
    `import engine` 直接 ModuleNotFoundError（`_bootstrap.setup` 还要 `<学科根>/rules/`
    做 L2 规则层 flat import）。D1=C 的「单目录拷走并 --help rc=0」自此才重新成立。
    """
    src = ROOT / disc
    if not src.is_dir():
        print(f"  × 学科不存在：{src}")
        return 1
    if out.exists():
        print(f"  × 输出目录已存在，拒绝覆盖：{out}（请换一个空路径）")
        return 1
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(src / "core" / "yishu_core", out / "core" / "yishu_core", ignore=ignore)
    shutil.copytree(src / "scripts", out / "scripts", ignore=ignore)
    # 508 批升格后推演链与 L2 规则层都在学科根下，缺任一份都跑不起 chart.py
    for sub in ("engine", "rules", "assets"):
        d = src / sub
        if d.is_dir():
            shutil.copytree(d, out / sub, ignore=ignore)
    for sub in ("rules", "golden"):
        d = src / "data" / sub
        if d.is_dir():
            shutil.copytree(d, out / "data" / sub, ignore=ignore)
    for p in sorted((src / "data").glob("*.json")):
        (out / "data").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, out / "data" / p.name)
    files = sum(1 for p in (out / "core" / "yishu_core").rglob("*.py")
                if "__pycache__" not in p.parts)
    print(f"  √ standalone：{out}（{disc}：core {files} 文件〔含子包〕＋scripts＋data/rules/golden/*.json）")
    print(f"    试跑：python \"{out / 'scripts' / 'chart.py'}\" --help")
    return 0


def selftest() -> int:
    manifest = load_manifest()
    fails = []
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        for disc in manifest["targets"]:
            d = t / disc
            d.mkdir()
            want = expected_files(manifest, disc)
            for rel, src in want.items():
                (d / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, d / rel)
            if drift(manifest, disc, d):
                fails.append(f"{disc}：干净副本被误判")
            # 负例 1：改一个顶层文件的一个字节
            victim = sorted(want)[0]
            (d / victim).write_bytes((d / victim).read_bytes() + b"\n# tamper\n")
            if not drift(manifest, disc, d):
                fails.append(f"{disc}：顶层产物被改没抓到")
            (d / victim).write_bytes(want[victim].read_bytes())
            # 负例 2：塞一个顶层野文件
            (d / "_stray_probe.py").write_text("# probe\n", encoding="utf-8")
            if not drift(manifest, disc, d):
                fails.append(f"{disc}：顶层野文件没抓到")
            (d / "_stray_probe.py").unlink()
            # 负例 3/4（539 批新增）：子包内的字节漂移与野文件必须同样判红。
            # 这两类在 539 批前的 glob("*.py") 下会全绿——正是本次补洞的对象。
            subs = sorted(rel for rel in want if "/" in rel)
            if not subs:
                fails.append(f"{disc}：manifest 未登记任何子包，负例 3/4 无从验证")
            else:
                sub_victim = subs[0]
                (d / sub_victim).write_bytes((d / sub_victim).read_bytes() + b"\n# tamper\n")
                if not drift(manifest, disc, d):
                    fails.append(f"{disc}：子包产物被改没抓到（rglob 未生效？）")
                (d / sub_victim).write_bytes(want[sub_victim].read_bytes())
                (d / sub_victim).parent.mkdir(parents=True, exist_ok=True)
                (d / sub_victim).parent.joinpath("_stray_probe.py").write_text("# probe\n", encoding="utf-8")
                if not drift(manifest, disc, d):
                    fails.append(f"{disc}：子包野文件没抓到（rglob 未生效？）")
        if fails:
            for f in fails:
                print(f"  × selftest：{f}")
            return 1
        print("  √ selftest：顶层/子包各两类负例（改字节·塞野文件）全部抓到；干净副本放行（两科各试一次）")
        return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="内核单一真源同步器")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--standalone", choices=["liuyao", "bazi"],
                    help="产出可独立拷走的学科目录（core＋scripts＋运行必需 data）")
    ap.add_argument("--out", type=Path, help="--standalone 的输出目录（须为空/不存在）")
    args = ap.parse_args()
    if args.standalone:
        if not args.out:
            print("  × --standalone 必须同时给 --out <目录>")
            return 2
        return standalone(args.standalone, args.out.resolve())
    if not (args.check or args.write or args.selftest):
        ap.print_help()
        return 2
    manifest = load_manifest()
    if args.selftest:
        if selftest() != 0:
            return 1
        # 负例之后必须再跑一次**真盘**：只证"器是活的"不证"盘是对的"，
        # 那正是 §四.8 反复抓到的"全绿的新门先怀疑"。
        problems = []
        for disc, rel in manifest["targets"].items():
            problems += drift(manifest, disc, ROOT / rel)
        if problems:
            for p in problems:
                print(f"  × {p}")
            return 1
        counts = {d: len(expected_files(manifest, d)) for d in manifest["targets"]}
        print("  √ 真盘同源：" + "／".join(f"{d} {n} 文件" for d, n in counts.items())
              + f"（变体 {len(manifest.get('variants', []))} 个在册）")
        return 0

    if args.write:
        for disc, rel in manifest["targets"].items():
            for a in write_target(manifest, disc, ROOT / rel):
                print(f"  · {a}")
        print("  · 已重生成两科内核（产物入库，手改会被 [35] 判红）")

    problems = []
    for disc, rel in manifest["targets"].items():
        problems += drift(manifest, disc, ROOT / rel)
    if problems:
        for p in problems:
            print(f"  × {p}")
        print("  → 修法：改 kernel/ 后跑 `python kernel/sync_kernel.py --write`；"
              "**不要直接改 <科>/core/**")
        return 1
    counts = {d: len(expected_files(manifest, d)) for d in manifest["targets"]}
    print("  √ 内核同源：" + "／".join(f"{d} {n} 文件" for d, n in counts.items())
          + f"，与 kernel/ 逐字节一致（变体 {len(manifest.get('variants', []))} 个在册）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
