# -*- coding: utf-8 -*-
"""构建 GitHub Pages 站点：把仓库源码镜像成**纯静态、可离线取用**的目录树。

    python tools/build_web.py --outdir site

产出（site/ 为可上传的站点根）：

    index.html              单页应用（纯前端出报告，见 web/index.html）
    manifest.json           站点清单：学科元数据 + 文件清单（含 sha256 与字节数）
    engine/...              仓库源码镜像：engine/core/… engine/disciplines/… engine/tools/report.py
    .nojekyll               关闭 Jekyll，保证 `_` 开头路径与 .py 原样发布

为什么要镜像源码，而不是让前端 clone：
  网页端**不需要任何凭证**就要能出报告，唯一不依赖 Token 的形态是
  "浏览器里跑 Python"。本脚本把 Python 引擎镜像到静态站点，前端在 Pyodide 里
  取回这些文件、按仓库原有相对布局写入虚拟文件系统，于是
  `disciplines/<科>/scripts/chart.py` 里的 `Path(__file__).parents[3] / "core"`
  等路径**原样成立**，与本地/CI 跑的是同一份代码、同一条管线。

零第三方依赖（只用标准库），可在干净 runner 上直接运行。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core import __version__  # noqa: E402
from yishu_core.runtime import force_utf8_stdio  # noqa: E402

CST = timezone(timedelta(hours=8))

# 进入站点镜像的顶层目录（相对仓库根）
MIRROR_DIRS = ("core", "synthesis", "cli")
MIRROR_FILES = ("tools/report.py",)

# 学科元数据：字段名与 tools/ci_request.py / docs/AI-SOP.md 的请求契约保持一致
#
# ⚠️ 有意排除 liuren / lingqi（大六壬、灵棋经）：这两科为本地 CLI/MCP-only，
#    站点通道 A 未挂载（见 PROMPTS.md）。新增学科时必须同步：
#    ① core/yishu_core/report/request.py 的 DISCIPLINES（全部学科）；
#    ② 此处 DISCIPLINE_META（进 web 的学科子集）；
#    ③ web/engine_runtime.py 的 WEB_DISCIPLINES + DEMO。
#    构建期断言（build() 前）会校验 ② ⊆ ①，清单漂移直接 fail-fast。
DISCIPLINE_META = (
    {
        "id": "liuyao", "name": "六爻纳甲", "kind": "卜",
        "summary": "装卦纳甲，以用神旺衰、动变、月日定一事成败与应期",
        "fields": [
            {"key": "question", "label": "所问之事", "type": "text", "required": True,
             "placeholder": "例：占本周面试能否通过"},
            {"key": "datetime", "label": "起卦时刻（留空则随机摇钱）", "type": "datetime"},
            {"key": "mode", "label": "起卦方式", "type": "select",
             "options": [["coin", "摇钱（随机）"], ["time", "时间起卦"],
                         ["number", "数字起卦"], ["manual", "手摇录入"]]},
            {"key": "numbers", "label": "数字起卦（逗号分隔）", "type": "text"},
        ],
    },
    {
        "id": "ming", "name": "四柱八字", "kind": "命",
        "summary": "排四柱藏干十神，机械推演强弱、月令格局、扶抑喜用、大运流年",
        "fields": [
            {"key": "datetime", "label": "出生公历时间", "type": "datetime", "required": True},
            {"key": "gender", "label": "性别", "type": "select", "required": True,
             "options": [["男", "男"], ["女", "女"]]},
            {"key": "question", "label": "想问的方向（可选）", "type": "text"},
        ],
    },
    {
        "id": "ziwei", "name": "紫微斗数", "kind": "命",
        "summary": "安星四化，推格局与大限",
        "fields": [
            {"key": "datetime", "label": "出生公历时间", "type": "datetime", "required": True},
            {"key": "gender", "label": "性别", "type": "select", "required": True,
             "options": [["男", "男"], ["女", "女"]]},
        ],
    },
    {
        "id": "meihua", "name": "梅花易数", "kind": "卜",
        "summary": "体用生克、互变卦与卦气旺衰",
        "fields": [
            {"key": "question", "label": "所问之事", "type": "text", "required": True},
            {"key": "datetime", "label": "起卦时刻（留空用当前时间）", "type": "datetime"},
            {"key": "way", "label": "起卦方式", "type": "select",
             "options": [["datetime", "时间起卦"], ["numbers", "数字起卦"]]},
            {"key": "numbers", "label": "数字（逗号分隔）", "type": "text"},
        ],
    },
    {
        "id": "xiaoliuren", "name": "小六壬", "kind": "卜",
        "summary": "六宫掌诀断事，含邻宫速断与方位五行",
        "fields": [
            {"key": "question", "label": "所问之事", "type": "text", "required": True},
            {"key": "datetime", "label": "起课时刻（留空用当前时间）", "type": "datetime"},
            {"key": "activity", "label": "事类（可选）", "type": "text"},
            {"key": "numbers", "label": "数字（逗号分隔）", "type": "text"},
        ],
    },
    {
        "id": "zeji", "name": "择吉", "kind": "卜",
        "summary": "建除十二神 / 黄黑道 / 二十八宿三因子综合裁决",
        "fields": [
            {"key": "date", "label": "用事日期", "type": "date", "required": True},
            {"key": "activity", "label": "事类", "type": "text",
             "placeholder": "例：开市 / 嫁娶 / 出行"},
            {"key": "hour_branch", "label": "时支（可选）", "type": "text"},
            {"key": "question", "label": "所问之事（可选）", "type": "text"},
        ],
    },
)

# 镜像时跳过的目录名（生成物、缓存、开发工具、评测与文档——运行期都用不到）
SKIP_DIRS = {
    "__pycache__", "scratch", "outputs", "logs", "guard", "node_modules",
    ".git", ".pytest_cache", ".preview", "archive", "_site", "site",
    "cases", "sources", "references", "assets", "docs", "tests", "dev_tools",
}
# 镜像时跳过的文件名/前缀（大体积评测集、本地反馈、仓库自身的门户页）
SKIP_FILE_PREFIX = ("eval_",)
SKIP_FILE_NAMES = {
    "case_library.md", "classical_synthesis.md", "eval_tune.json", "eval_holdout.json",
    "index.html", "README.md",
}
# 超出此字节数的单个文件不进镜像（当前镜像内无此类文件；超限即闸）
MAX_FILE_BYTES = 512 * 1024

WEB_FILES = ("index.html", "web.css", "web.js", "engine_runtime.py", "favicon.svg")


def _profile_of(rel: str) -> str:
    """文件在清单里的用途：code=解释器要 import 的；doc=随镜像发布的说明。"""
    return "code" if rel.endswith(".py") else "doc"


def _with_scope(entry: dict, rel: str) -> dict:
    """标注文件归属学科与是否运行期必需（前端据此算出"跑这一科要取哪些文件"）。"""
    if rel.startswith("engine/disciplines/"):
        parts = rel[len("engine/disciplines/"):].split("/")
        if parts and parts[0]:
            entry["discipline"] = parts[0]
            entry["runtime"] = len(parts) > 2 and parts[1] == "scripts"
    elif rel.startswith("engine/core/"):
        entry["discipline"] = "*"
        entry["runtime"] = True
    return entry


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_mirror_files(index: dict | None = None) -> list[tuple[Path, str]]:
    """产出 (源文件绝对路径, 站点内相对路径) 列表，站点内路径以 engine/ 开头。

    index 为 path→sha256 表；给了就只收表里有的（保证清单与镜像逐条对齐）。
    """
    out: list[tuple[Path, str]] = []

    def keep(p: Path) -> bool:
        if p.name in SKIP_FILE_NAMES:
            return False
        if any(p.name.startswith(pre) for pre in SKIP_FILE_PREFIX):
            return False
        if p.stat().st_size > MAX_FILE_BYTES:
            return False
        return True

    def walk(base: Path, prefix: str) -> None:
        for p in sorted(base.rglob("*")):
            rel = p.relative_to(base)
            if any(seg in SKIP_DIRS for seg in rel.parts):
                continue
            if not p.is_file():
                continue
            if p.suffix not in (".py", ".json", ".css", ".md", ".txt", ".html"):
                continue
            if not keep(p):
                continue
            rel_str = f"{prefix}/{rel.as_posix()}"
            if index is not None and rel_str not in index:
                continue
            out.append((p, rel_str))

    for d in MIRROR_DIRS:
        base = ROOT / d
        if base.is_dir():
            walk(base, f"engine/{d}")
    for disc in [m["id"] for m in DISCIPLINE_META]:
        base = ROOT / "disciplines" / disc
        if base.is_dir():
            walk(base, f"engine/disciplines/{disc}")
    for f in MIRROR_FILES:
        p = ROOT / f
        if p.is_file():
            out.append((p, f"engine/{f}"))
    return out


def build_manifest(*, site_base: str = "", engine_root: str = "engine") -> dict:
    """只构建清单（不落盘）——预览服务器与站点构建共用。"""
    files = iter_mirror_files()
    entry = {}
    for src, rel in files:
        entry[rel] = {"path": rel, "bytes": src.stat().st_size,
                      "sha256": sha256_of(src), "profile": _profile_of(rel)}
        _with_scope(entry[rel], rel)
    manifest_files = [entry[rel] for _src, rel in files]
    total = sum(f["bytes"] for f in manifest_files)

    # 逐科汇总：前端据此显示"跑这一科要取多少文件/多大"，
    # 也是 docs 里"网页端一次推演的网络开销"这句话的依据。
    per_disc = {}
    for f in manifest_files:
        d = f.get("discipline")
        if not d:
            continue
        slot = per_disc.setdefault(d, {"files": 0, "bytes": 0, "runtime_files": 0})
        slot["files"] += 1
        slot["bytes"] += f["bytes"]
        if f.get("runtime"):
            slot["runtime_files"] += 1

    return {
        "schema": "yi-web-manifest/1",
        "yishu_core_version": __version__,
        "generated": datetime.now(CST).strftime("%Y-%m-%d %H:%M:%S%z"),
        "base": site_base,
        "engine_root": engine_root,
        "entry": f"{engine_root}/tools/report.py",
        "disciplines": list(DISCIPLINE_META),
        "per_discipline": per_disc,
        "files": manifest_files,
        "totals": {"files": len(manifest_files), "bytes": total},
        "notice": (
            "本页在浏览器内（Pyodide）运行与本地/CI 完全相同的 Python 排盘引擎；"
            "报告中的分数为古籍案例对齐分（非现实命中率）。"
        ),
    }


def _assert_discipline_lists_consistent() -> None:
    """fail-fast：DISCIPLINE_META 必须是 request.DISCIPLINES 的子集（清单漂移即拒绝构建）。"""
    from yishu_core.report.request import DISCIPLINES as ALL_DISCIPLINES
    web_ids = [m["id"] for m in DISCIPLINE_META]
    unknown = [d for d in web_ids if d not in ALL_DISCIPLINES]
    if unknown:
        raise SystemExit(
            f"DISCIPLINE_META 含未知学科 {unknown}——"
            f"request.DISCIPLINES = {list(ALL_DISCIPLINES)}，先同步两份清单")


def build(outdir: Path, *, site_base: str = "") -> dict:
    """生成站点。site_base 为空表示站点在域名根，否则形如 '/Yi'。"""
    _assert_discipline_lists_consistent()
    web_src = ROOT / "web"
    if not (web_src / "index.html").is_file():
        raise SystemExit("缺少 web/index.html（前端页面源）")

    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)

    # 1) 前端静态资源
    for name in WEB_FILES:
        src = web_src / name
        if src.is_file():
            shutil.copy2(src, outdir / name)

    # 2) 引擎镜像
    manifest = build_manifest(site_base=site_base)
    index = {f["path"]: f["sha256"] for f in manifest["files"]}
    files = iter_mirror_files(index)
    for src, rel in files:
        dst = outdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    # 3) .nojekyll：保证 .py 与 _ 开头路径原样发布
    (outdir / ".nojekyll").write_text("", encoding="utf-8")

    # 4) 清单
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5) 目录索引（人类可读；也是"AI 只需链接"时的入口说明）
    (outdir / "engine" / "README.txt").write_text(
        "本目录是 Yi 仓库的源码镜像，供网页端在浏览器内运行推演引擎。\n"
        "入口：tools/report.py；四段契约：disciplines/<科>/scripts/{chart,analyze,narrate,render}.py\n"
        "取用说明见站点根 manifest.json 与仓库 docs/AI-SOP.md。\n",
        encoding="utf-8")

    return {"outdir": str(outdir), "files": manifest["totals"]["files"],
            "bytes": manifest["totals"]["bytes"]}


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="构建 Yi 纯前端站点（GitHub Pages）")
    ap.add_argument("--outdir", type=Path, default=ROOT / "site", help="输出目录")
    ap.add_argument("--base", default="", help="站点子路径（用户/组织页留空；项目页填 /仓库名）")
    args = ap.parse_args()

    result = build(args.outdir, site_base=args.base)
    print(f"站点已生成：{result['outdir']}")
    print(f"  镜像文件 {result['files']} 个，{result['bytes'] / 1024:.1f} KB")
    print("  入口 index.html；清单 manifest.json")
    print("RESULT_JSON " + json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
