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

**这不是跨科写**：AGENTS §二 禁的是"某一科的脚本往另一科目录里写"。本器在 `kernel/` 下，
不属于任何一科，且产物本来就分属两科——它是构建器，不是学科脚本。
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


def expected_files(manifest: dict, disc: str) -> dict[str, Path]:
    """某科应有的 {产物文件名: 真源路径}。"""
    src = KERNEL / "yishu_core"
    files = manifest["files"]
    out: dict[str, Path] = {}
    for name in files["common"]:
        out[name] = src / "common" / name
    for name in files.get(f"{disc}_only", []):
        out[name] = src / "common" / name
    for name in manifest.get("variants", []):
        out[name] = src / "variants" / name.replace(".py", f".{disc}.py")
    return out


def drift(manifest: dict, disc: str, target_dir: Path) -> list[str]:
    """返回该科内核与真源的差异（空列表＝同源）。"""
    problems: list[str] = []
    want = expected_files(manifest, disc)
    for name, src in want.items():
        if not src.exists():
            problems.append(f"{disc}：真源缺 {src.relative_to(ROOT)}")
            continue
        dst = target_dir / name
        if not dst.exists():
            problems.append(f"{disc}：产物缺 {name}")
        elif dst.read_bytes() != src.read_bytes():
            problems.append(f"{disc}：{name} 与 kernel/ 不一致（产物被手改？）")
    have = {p.name for p in target_dir.glob("*.py")}
    extra = sorted(have - set(want))
    for name in extra:
        problems.append(f"{disc}：产物里多出未登记文件 {name}（该删或该进 manifest）")
    return problems


def write_target(manifest: dict, disc: str, target_dir: Path) -> list[str]:
    """按 manifest 重生成；删除未登记的 .py。返回动作清单。"""
    actions: list[str] = []
    want = expected_files(manifest, disc)
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, src in sorted(want.items()):
        data = src.read_bytes()
        dst = target_dir / name
        if not dst.exists() or dst.read_bytes() != data:
            dst.write_bytes(data)
            actions.append(f"写入 {dst.relative_to(ROOT)}")
    for p in sorted(target_dir.glob("*.py")):
        if p.name not in want:
            p.unlink()
            actions.append(f"删除 {p.relative_to(ROOT)}（未登记/该科不收）")
    return actions


def selftest() -> int:
    manifest = load_manifest()
    fails = []
    with tempfile.TemporaryDirectory() as td:
        t = Path(td)
        for disc in manifest["targets"]:
            d = t / disc
            d.mkdir()
            for name, src in expected_files(manifest, disc).items():
                shutil.copyfile(src, d / name)
            if drift(manifest, disc, d):
                fails.append(f"{disc}：干净副本被误判")
            # 负例 1：改一个字节
            victim = sorted(expected_files(manifest, disc))[0]
            (d / victim).write_bytes((d / victim).read_bytes() + b"\n# tamper\n")
            if not drift(manifest, disc, d):
                fails.append(f"{disc}：产物被改没抓到")
            (d / victim).write_bytes(expected_files(manifest, disc)[victim].read_bytes())
            # 负例 2：塞一个野文件
            (d / "_stray_probe.py").write_text("# probe\n", encoding="utf-8")
            if not drift(manifest, disc, d):
                fails.append(f"{disc}：野文件没抓到")
    if fails:
        for f in fails:
            print(f"  × selftest：{f}")
        return 1
    print(f"  √ selftest：改产物/塞野文件两类负例全部抓到；干净副本放行（两科各试一次）")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="内核单一真源同步器")
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
