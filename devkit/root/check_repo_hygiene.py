# -*- coding: utf-8 -*-
"""仓库卫生门（第五百五十批）：让 `REPO-HYGIENE.md` 的三条硬纪律常驻有牙。

本仓反复踩过三类「本地全绿、线上/新人全红」的退化，全都没有门看着：

  1. 生成物被误提交进 git（engine/、skills/、site/、data/cache/、__pycache__）；
     `.gitignore` 只能挡「忘记 add」，挡不住 `git add -f` 或改了忽略规则。
  2. 硬编码本机绝对路径：549 批实证 33 个 .py 被批量注入
     `C:\\Users\\...\\Yi\\<科>\\eval`，本地能跑、fresh checkout 直接 import 失败。
  3. 活文档里钉死会变的数（篇目数／包体体积／版本快照）：517／539／549 批
     各清过一轮，但没有任何门阻止下一轮写回去。

只读、不写盘。历史 CHANGELOG 按登记时点保留，扫描时豁免（见 SCAN_EXEMPT）。

    python devkit/root/check_repo_hygiene.py
    python devkit/root/check_repo_hygiene.py --selftest
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
SELF = "devkit/root/check_repo_hygiene.py"

# ── 判据 1：生成物零入库 ────────────────────────────────────────────────
FORBIDDEN_PREFIXES = (
    "site/", "plugins/engine/", "plugins/skills/",
    "dsh-plugin/engine/", "dsh-plugin/skills/",
)
FORBIDDEN_EXACT = {
    "dsh-plugin/SKILL.md", "dsh-plugin/package-lock.json",
}
# dsh-plugin/src 下唯一入库的源码是 index.mjs（.gitignore 显式 negated）
SRC_ALLOW = {"dsh-plugin/src/index.mjs"}
FORBIDDEN_RE = (
    re.compile(r"(^|/)data/cache/"),
    re.compile(r"(^|/)data/collation/"),
    re.compile(r"(^|/)data/feedback/"),
    re.compile(r"(^|/)scratch/"),
    re.compile(r"(^|/)outputs/"),
    re.compile(r"(^|/)logs/"),
    re.compile(r"__pycache__/"),
    re.compile(r"\.pyc$"),
    re.compile(r"\.tgz$"),
    re.compile(r"^dsh-plugin/src/[^/]+\.(mjs|json)$"),
)

# ── 判据 2：零硬编码本机绝对路径 ───────────────────────────────────────
ABS_RE = re.compile(
    r"(?:[A-Za-z]:[\\/]{1,2}Users[\\/]"
    r"|/home/runner/work/"
    r"|/Users/[A-Za-z0-9_.-]+/Desktop/)", re.I
)
CODE_EXT = (".py", ".mjs", ".js", ".json", ".yml", ".yaml", ".toml")

# ── 判据 3：活文档不钉会变的数 ─────────────────────────────────────────
STALE_MARKERS = (
    (re.compile(r"\b2\.6\s*MB\b"), "包体体积快照（以 npm pack --dry-run 实跑为准）"),
    (re.compile(r"\b0\.77\s*MB\b"), "tgz 体积快照"),
    (re.compile(r"\b163\s*文件\b"), "发布包文件数快照"),
    (re.compile(r"\b1[39]\s*篇判据|\b9\s*篇判据"), "知识库篇目数手钉（以 kb-docs.mjs 登记表为准）"),
    (re.compile(r"package\.json\s*已到\s*1\.0\.\d+"), "版本快照（版本真源是 package.json 本身）"),
    (re.compile(r"1\.0\.0\.tgz"), "固定发布包文件名（版本会漂移）"),
)
SCAN_EXEMPT = (
    "CHANGELOG", "HISTORY-INDEX", "ARCHIVE",
    "ARCHITECTURE-PLAN.md", "REARCHITECT-PROPOSAL.md",
    "RULE-ENGINE-REFACTOR-PLAN.md", "SANMING-SIKU-COLLATION.md",
    # 这个门的职责就是抓硬编码绝对路径，其 selftest 夹具**必须**含
    # `C:\Users\bob\x` 一类假路径；整体豁免，避免把负例当缺陷（550 批实证）。
    "check_house_conventions.py",
)
DOC_EXT = (".md", ".yml", ".yaml")


def tracked_files() -> list[str]:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return sorted(x.strip() for x in r.stdout.splitlines() if x.strip())


def scan(tracked: list[str], texts: dict[str, str]) -> list[str]:
    """纯判据：tracked 为入库路径清单，texts 为待扫文本 {相对路径: 内容}。"""
    problems: list[str] = []

    # 1) 生成物零入库
    for p in tracked:
        if p in SRC_ALLOW:
            continue
        if p.startswith(FORBIDDEN_PREFIXES) or p in FORBIDDEN_EXACT or any(r.search(p) for r in FORBIDDEN_RE):
            problems.append(f"生成物误入库：{p}（应按 REPO-HYGIENE.md §二 由脚本再生）")

    # 2) 零硬编码本机绝对路径
    for rel, txt in sorted(texts.items()):
        if rel == SELF or rel.endswith(CODE_EXT) is False:
            continue
        if any(s in rel for s in SCAN_EXEMPT):
            continue
        for n, line in enumerate(txt.splitlines(), 1):
            if ABS_RE.search(line):
                problems.append(f"硬编码本机绝对路径：{rel}:{n}（按 __file__ 相对定位）")

    # 3) 活文档不钉过期数
    for rel, txt in sorted(texts.items()):
        if rel == SELF or not rel.endswith(DOC_EXT):
            continue
        if any(s in rel for s in SCAN_EXEMPT):
            continue
        for n, line in enumerate(txt.splitlines(), 1):
            for pat, why in STALE_MARKERS:
                if pat.search(line):
                    problems.append(f"活文档钉过期数：{rel}:{n} — {why}")
    return problems


def real_texts(tracked: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in tracked:
        if not (rel.endswith(CODE_EXT) or rel.endswith(DOC_EXT)):
            continue
        if rel == SELF or any(s in rel for s in SCAN_EXEMPT):
            continue
        p = ROOT / rel
        if not p.is_file() or p.stat().st_size > 2_000_000:
            continue
        try:
            out[rel] = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
    return out


def selftest() -> int:
    base_files = ["README.md", "DOCS.md", "AGENTS.md", "liuyao/scripts/chart.py",
                  "dsh-plugin/src/index.mjs", ".github/workflows/ci.yml"]
    base_texts = {
        "README.md": "# 易（Yi）\n",
        "DOCS.md": "# 文档索引\n",
        "AGENTS.md": "# 铁律\n",
        "liuyao/scripts/chart.py": "from pathlib import Path\n",
        "dsh-plugin/src/index.mjs": "export const name = 'yi'\n",
        ".github/workflows/ci.yml": "name: quality-gates\n",
    }
    cases: list[tuple[str, bool]] = []

    def check(name: str, fn) -> None:
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        cases.append((name, ok))

    check("正例：干净清单零问题", lambda: scan(base_files, base_texts) == [])
    check("生成物误入库判红", lambda: any(
        "生成物误入库" in p for p in scan(base_files + ["site/index.html"], base_texts)
    ))
    check("data/cache 误入库判红", lambda: any(
        "生成物误入库" in p for p in scan(base_files + ["liuyao/data/cache/eval_x.json"], base_texts)
    ))
    check("src 产物误入库判红（index.mjs 例外仍绿）", lambda: (
        scan(base_files, base_texts) == []
        and any("生成物误入库" in p for p in scan(base_files + ["dsh-plugin/src/tools.mjs"], base_texts))
    ))
    check("硬编码绝对路径判红", lambda: any(
        "硬编码" in p for p in scan(base_files, {
            **base_texts, "liuyao/scripts/chart.py": "_ed = 'C:\\Users\\someone\\Yi\\liuyao\\eval'\n"
        })
    ))
    check("CI runner 绝对路径判红", lambda: any(
        "硬编码" in p for p in scan(base_files, {
            **base_texts, "liuyao/scripts/chart.py": "ROOT = '/home/runner/work/Yi/Yi'\n"
        })
    ))
    check("活文档包体快照判红", lambda: any(
        "钉过期数" in p for p in scan(base_files, {
            **base_texts, "README.md": "解包 2.6 MB\n"
        })
    ))
    check("活文档版本快照判红", lambda: any(
        "钉过期数" in p for p in scan(base_files, {
            **base_texts, ".github/workflows/ci.yml": "# package.json 已到 1.0.24\n"
        })
    ))
    check("CHANGELOG 历史按登记时点豁免", lambda: scan(
        base_files + ["liuyao/docs/CHANGELOG.md"],
        {**base_texts, "liuyao/docs/CHANGELOG.md": "163 文件 / 2.6 MB / 1.0.0.tgz（历史快照）\n"}
    ) == [])
    check("负例夹具文件豁免，但普通文件仍判红", lambda: (
        scan(base_files + ["liuyao/dev_tools/check_house_conventions.py"], {
            **base_texts, "liuyao/dev_tools/check_house_conventions.py": "if ABS_RE.search('C:\\Users\\bob\\x'):\n"
        }) == []
        and any("硬编码" in p for p in scan(base_files, {
            **base_texts, "liuyao/scripts/chart.py": "_ed = 'C:\\Users\\someone\\Yi'\n"
        }))
    ))
    check("门自身模式字面量不自伤", lambda: scan(
        base_files + [SELF], {**base_texts, SELF: "ABS_RE = r'C:\\Users\\'\n"}
    ) == [])

    for name, ok in cases:
        print(f"  {'√' if ok else '×'} {name}")
    bad = [n for n, ok in cases if not ok]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(cases)} 类正/负例全过（真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="仓库卫生门")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证，真盘零写入")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    tracked = tracked_files()
    if not tracked:
        print("  × git ls-files 为空（路径解析失败不许报绿）")
        return 1
    problems = scan(tracked, real_texts(tracked))
    if problems:
        for p in problems:
            print("  × " + p)
        print(f"[仓库卫生] 判红 {len(problems)} 项——按 REPO-HYGIENE.md 修后复跑")
        return 1
    print(f"[仓库卫生] 全绿：{len(tracked)} 份入库文件，生成物零入库／零硬编码绝对路径／活文档零过期钉数")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
