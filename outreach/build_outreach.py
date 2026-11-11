# -*- coding: utf-8 -*-
"""对外可发现层构建器（第五百四十九批）：把「代码 + 代码产出的结论」变成静态可读物。

为什么有这一层：网页端大模型联网检索时只能读**静态文本**，不会执行 Python。
本仓此前结论只在运行时产生、当场交付、从不落盘（.gitignore 排掉 outputs/*.html），
外部 AI 即使搜到仓库也读不到任何成品。本器把三样东西从真源**现场生成**并入库：

  1. `llms.txt` / `KNOWLEDGE.md` / `kb/INDEX.md` —— 面向 AI 读者的自包含导览与 raw 直链；
  2. `examples/liuyao-example.md` / `examples/bazi-example.md` —— **由两科四段流水线实跑生成**
     的完整术数结论（固定输入、逐字节可复现，非手写）；
  3. `site/**` —— 不入库（gitignore），供 GitHub Pages Actions 现场生成后部署。

真源：`outreach/KNOWLEDGE-BODY.md`（人写知识正文）、`plugins/scripts/kb-docs.mjs`
（判据篇目登记表，与 `plugins/scripts/build.mjs` 同一份，不新增第二登记表）、
两科 `references/*.md`（判据全文）、两科 `scripts/`（引擎）。

    python outreach/build_outreach.py --write       # 生成入库产物 + site/
    python outreach/build_outreach.py --check       # 入库产物逐字节同源复验（CI 挂此）
    python outreach/build_outreach.py --selftest    # 内存负例自证，真盘零写入

铁律：示例结论只能由代码生成（§一.1）；示例输入为**新造中性问句**、不触达
`data/cases/` 与 `case_library.md`（§一.2）；所有对外文本带口径脚注（§一.3）。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
OUTREACH = ROOT / "outreach"
REGISTRY = ROOT / "plugins" / "scripts" / "kb-docs.mjs"
KNOWLEDGE_BODY = OUTREACH / "KNOWLEDGE-BODY.md"

REPO = "https://github.com/LinHoMo/Yi"
RAW = "https://raw.githubusercontent.com/LinHoMo/Yi/main"
PAGES = "https://linhomo.github.io/Yi/"
BLOB = REPO + "/blob/main"

TRACKED = (
    "llms.txt",
    "KNOWLEDGE.md",
    "kb/INDEX.md",
    "examples/liuyao-example.md",
    "examples/bazi-example.md",
)

ROW_RE = re.compile(r"\['([^']+\.md)',\s*'([^']*)'\]")
FORBIDDEN = ("预测准确率", "断事如神", "命中率 99", "准确率 99")
# 与 plugins 自检 [7] 同口径：口径声明里的否定语境（「不是预测准确率」「不得说断事如神」）
# 是**合规文本**，逐行豁免；只在肯定语境出现禁句才判红。
NEGATION = ("不是", "不得", "禁止", "不可", "不许", "严禁", "不能", "未声称")

# 示例输入：新造中性问句，不来自任何古籍案例集（§一.2）
LY_QUESTION = "示例：某合作项目下月能否顺利推进"
LY_DATETIME = "2026-01-15 10:30"
LY_SEED = 42
BZ_DATETIME = "1990-05-20 10:30"
BZ_GENDER = "男"
BZ_QUESTION = "示例：命局结构说明"

CALIBER = (
    "> **口径说明**：本报告全部由 Python 引擎按四段契约 `chart → analyze → narrate → render`\n"
    "> 机械生成，未由语言模型改写任何排盘或判定结论。仓库内一切分数都是**古籍案例对齐分**\n"
    "> （回归审计用），**不是现实命中率**；现实侧样本为零。本内容是条件化倾向陈述，不是预言；\n"
    "> 医疗、法律、投资及重大决策请以专业意见为准。示例问句为演示用中性问句，不引用任何古籍案例。\n"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def kb_rows() -> list[tuple[str, str]]:
    """从 kb-docs.mjs 抽篇目登记表——与 build.mjs 共用同一真源。"""
    txt = _read(REGISTRY)
    rows = ROW_RE.findall(txt)
    if not rows:
        raise ValueError("kb-docs.mjs 未解析到任何篇目，登记表格式已变")
    return [(k.strip(), d.strip()) for k, d in rows]


def validate_rows(rows: list[tuple[str, str]]) -> None:
    """登记表面完整性：路径合法、文件在盘、案例库永不进对外层。"""
    if not rows:
        raise ValueError("登记表为空：对外知识层不得无篇目")
    seen: set[str] = set()
    for key, desc in rows:
        if key in seen:
            raise ValueError(f"登记表重复篇目：{key}")
        seen.add(key)
        parts = key.split("/")
        if len(parts) != 2 or parts[0] not in ("liuyao", "bazi") or not parts[1].endswith(".md"):
            raise ValueError(f"登记表篇目路径不合法：{key}")
        if "case_library" in key:
            raise ValueError("案例库不得进入对外知识层（§一.2）")
        if not desc:
            raise ValueError(f"篇目缺「什么时候读」描述：{key}")
        if not (ROOT / parts[0] / "references" / parts[1]).is_file():
            raise ValueError(f"登记表指向不存在的判据文件：{key}")


def raw_link(key: str) -> str:
    disc, name = key.split("/")
    return f"{RAW}/{disc}/references/{name}"


def blob_link(key: str) -> str:
    disc, name = key.split("/")
    return f"{BLOB}/{disc}/references/{name}"


def _engine_report(script_dir: Path, code: str) -> str:
    """子进程跑四段流水线，取 render 段 stdout（两科同名模块，必须分进程）。"""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(ROOT), capture_output=True, env=env, timeout=180,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")[-1200:]
        raise RuntimeError(f"引擎实跑失败（rc={proc.returncode}）：{err}")
    text = proc.stdout.decode("utf-8", errors="replace")
    if not text.strip():
        raise RuntimeError("引擎 stdout 为空，示例报告不得为空")
    return text.rstrip("\n") + "\n"


def engine_reports() -> dict[str, str]:
    ly = ROOT / "liuyao" / "scripts"
    bz = ROOT / "bazi" / "scripts"
    ly_code = f"""
import sys
sys.path.insert(0, {str(ly)!r})
from chart import chart
from analyze import analyze
from render import render
a = analyze(chart("coin", {LY_QUESTION!r}, datetime_str={LY_DATETIME!r}, seed={LY_SEED}))
print(render(a, fmt="md"), end="")
"""
    bz_code = f"""
import sys
sys.path.insert(0, {str(bz)!r})
from chart import chart
from analyze import analyze
from render import render
a = analyze(chart({BZ_QUESTION!r}, datetime_str={BZ_DATETIME!r}, gender={BZ_GENDER!r}))
print(render(a), end="")
"""
    return {
        "liuyao": _engine_report(ly, ly_code),
        "bazi": _engine_report(bz, bz_code),
    }


def _example(title: str, repro_cmd: str, input_desc: str, body: str) -> str:
    return (
        "<!-- 由 outreach/build_outreach.py --write 生成；结论由引擎实跑，请勿手改 -->\n"
        f"# {title}\n\n"
        "> 这是一份**代码产出的实际术数结论**：下方「引擎报告原文」逐字来自两科\n"
        "> `chart → analyze → narrate → render` 四段流水线的 `render` 输出，未作任何人工改写。\n\n"
        f"- 输入：{input_desc}\n"
        f"- 复现（仓库根）：`{repro_cmd}`\n"
        "- 同源复验：`python outreach/build_outreach.py --check`（逐字节比对，漂移即判红）\n"
        "- 用途：供网页端大模型读取并据此解释术语、示范解读骨架；**不是对新占问的现场起卦**。\n\n"
        "---\n\n"
        "## 引擎报告原文\n\n"
        + body + "\n---\n\n"
        + CALIBER
    )


def build(rows: list[tuple[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    """返回 (入库产物, site 产物)，值统一为 LF 文本。"""
    validate_rows(rows)
    reports = engine_reports()

    # 1) llms.txt —— 机器可读索引，全部给 raw 直链（网页端 AI 读 blob 常失败）
    llms = [
        "# 易（Yi）",
        "",
        "> 六爻纳甲与八字四柱的确定性排盘与解读引擎。机械运算归 Python 代码，象数解读归语言模型。",
        "> 仓库内所有分数是「古籍案例对齐分」（回归审计用），不是现实命中率；现实侧样本为零。",
        "> 本工具不是预言；医疗、法律、投资、重大决策请以专业意见为准。",
        "",
        "## 给 AI 读者的入口",
        "",
        f"- [KNOWLEDGE.md]({RAW}/KNOWLEDGE.md)：自包含术数知识速读、术语表、铁律与常见问题，可直接据此作答",
        f"- [CAPABILITY.md]({RAW}/CAPABILITY.md)：能力边界与全部读数（每行带集合名、n 与出处）",
        f"- [README.md]({RAW}/README.md)：安装、clone、插件与构建",
        f"- [知识库导览]({RAW}/kb/INDEX.md)：判据篇目路由表与 raw 直链",
        f"- [GitHub Pages 站点]({PAGES})：无需登录的静态知识镜像",
        "",
        "## 代码产出的实际结论（引擎实跑示例报告）",
        "",
        f"- [六爻纳甲占报告示例]({RAW}/examples/liuyao-example.md)：固定输入下的完整六爻结论与应期窗口",
        f"- [八字命局因子说明示例]({RAW}/examples/bazi-example.md)：固定输入下的四柱、强弱、格局、喜用、大运流年",
        "",
        "## 判据知识库（按需读，勿整本读）",
        "",
    ]
    for key, desc in rows:
        llms.append(f"- [{key}]({raw_link(key)})：{desc}")
    llms += [
        "",
        "## 安装 / 使用",
        "",
        f"- [README 安装节]({RAW}/README.md)：clone 即用、装 skills、装 DSH 插件",
        f"- [plugins/SKILL.md]({RAW}/plugins/SKILL.md)：技能正文（含 frontmatter，可放进通用 skills 目录）",
        f"- [MCP stdio 服务]({BLOB}/plugins/mcp/server.mjs)：零依赖，可直接暴露四工具",
        "",
        "## 不用于解读",
        "",
        f"- `liuyao/references/case_library.md` 虽在仓库公开，按 AGENTS.md §一.2 与解读物理隔离：",
        "  断卦时不得打开、不得提及案例名、不得以案例类比佐证，也不得当作解读知识引用。",
        "",
    ]

    # 2) KNOWLEDGE.md —— 人写正文 + 现场生成的篇目/示例索引
    body = _read(KNOWLEDGE_BODY).rstrip("\n")
    krows = [
        "",
        "## 八、判据篇目索引（raw 直链）",
        "",
        "下表由构建器从登记表现场生成。网页端 AI 请优先抓 `raw.githubusercontent.com` 直链，",
        "`github.com/.../blob/...` 在部分联网检索通道会因限流或渲染失败而读不到。",
        "",
        "| 篇目 | 什么时候读 | raw 直链 |",
        "|---|---|---|",
    ]
    for key, desc in rows:
        krows.append(f"| `{key.split('/')[1]}` | {desc} | {raw_link(key)} |")
    krows += [
        "",
        "## 九、代码产出的示例结论",
        "",
        f"- 六爻：[examples/liuyao-example.md]({RAW}/examples/liuyao-example.md)（{PAGES} 同步镜像）",
        f"- 八字：[examples/bazi-example.md]({RAW}/examples/bazi-example.md)",
        "",
        "两份报告均由固定输入下的四段流水线实跑生成，含完整结论、应期窗口、旺衰动变、",
        "格局喜用与判据所本，可用作解读范式。**静态示例不能代替现场起卦**：要为新占问出结论，",
        "须 clone 本体运行脚本，或安装 skills / DSH 插件调用四工具。",
        "",
        "---",
        "",
        "> 本文由 `outreach/build_outreach.py --write` 从 `outreach/KNOWLEDGE-BODY.md` 与登记表拼装，",
        "> 同器 `--check` 逐字节复验。引用能力读数请连 commit 一起引用 `CAPABILITY.md`。",
        "",
    ]
    knowledge = body + "\n" + "\n".join(krows)

    # 3) kb/INDEX.md —— 对外导览（与包内 build 生成的 INDEX.md 用途不同，不互为真源）
    idx = [
        "# Yi 知识库导览（GitHub / 网页端 AI 用）",
        "",
        "> 本文件服务**仓库读者与联网检索的 AI**：给出每篇判据的 raw 直链与「什么时候读」。",
        "> 随 DSH 插件发布的 `skills/yi-divination/references/INDEX.md` 是构建产物，",
        "> 由 `plugins/scripts/build.mjs` 按 `plugins/scripts/kb-docs.mjs` 生成，两者判据篇目同源但用途不同。",
        "",
        "按需读取：先看这张表挑篇，再按 raw 直链读全文；**不要整本读**。",
        "",
        "## 六爻",
        "",
        "| 篇目 | 什么时候读 | raw 直链 |",
        "|---|---|---|",
    ]
    for key, desc in rows:
        if key.startswith("liuyao/"):
            idx.append(f"| `{key.split('/')[1]}` | {desc} | {raw_link(key)} |")
    idx += ["", "## 八字", "", "| 篇目 | 什么时候读 | raw 直链 |", "|---|---|---|"]
    for key, desc in rows:
        if key.startswith("bazi/"):
            idx.append(f"| `{key.split('/')[1]}` | {desc} | {raw_link(key)} |")
    idx += [
        "",
        "## 示例结论",
        "",
        f"- [六爻报告示例]({RAW}/examples/liuyao-example.md)",
        f"- [八字报告示例]({RAW}/examples/bazi-example.md)",
        "",
        "## ⛔ 不在此目录的内容",
        "",
        "古籍案例库 `case_library.md` 刻意不进入对外知识层与发布包（AGENTS.md §一.2）。",
        "它在仓库中公开只为测试与审计，**解读时不得引用、联想或类比**。",
        "",
    ]

    ly_input = (
        f"mode=coin, question=「{LY_QUESTION}」, datetime={LY_DATETIME}, seed={LY_SEED}"
    )
    bz_input = (
        f"question=「{BZ_QUESTION}」, datetime={BZ_DATETIME}, gender={BZ_GENDER}"
    )
    ly_repro = (
        "python -c \"import sys;sys.path.insert(0,'liuyao/scripts');"
        "from chart import chart;from analyze import analyze;from render import render;"
        f"print(render(analyze(chart('coin','{LY_QUESTION}',datetime_str='{LY_DATETIME}',seed={LY_SEED})),fmt='md'))\""
    )
    bz_repro = (
        "python -c \"import sys;sys.path.insert(0,'bazi/scripts');"
        "from chart import chart;from analyze import analyze;from render import render;"
        f"print(render(analyze(chart('{BZ_QUESTION}',datetime_str='{BZ_DATETIME}',gender='{BZ_GENDER}'))))\""
    )

    tracked = {
        "llms.txt": "\n".join(llms),
        "KNOWLEDGE.md": knowledge,
        "kb/INDEX.md": "\n".join(idx),
        "examples/liuyao-example.md": _example(
            "示例报告 · 六爻纳甲（引擎实跑）", ly_repro, ly_input, reports["liuyao"]
        ),
        "examples/bazi-example.md": _example(
            "示例报告 · 八字四柱（引擎实跑）", bz_repro, bz_input, reports["bazi"]
        ),
    }

    # 4) site/ —— 不入库，Pages Actions 现场生成
    site: dict[str, str] = {
        "site/index.md": (
            "# Yi · 术数知识与引擎示例（静态镜像）\n\n"
            f"> 本页是 [{PAGES}]({PAGES}) 的入口；仓库真源见 "
            f"[{REPO}]({REPO})。本页内容由 `outreach/build_outreach.py` 生成，不依赖 JS 即可阅读。\n\n"
            "- [知识速读（本页全文）](#) ← 下方正文\n"
            "- [llms.txt](llms.txt)（机器可读索引）\n"
            "- 判据全文：" + "、".join(
                f"[{key.split('/')[1]}](knowledge/{key.replace('/', '__')})" for key, _ in rows
            ) + "\n"
            "- 示例结论：[六爻报告](examples/liuyao-example.md)、[八字报告](examples/bazi-example.md)\n\n"
            "---\n\n" + knowledge
        ),
        "site/llms.txt": "\n".join(llms),
        "site/examples/liuyao-example.md": tracked["examples/liuyao-example.md"],
        "site/examples/bazi-example.md": tracked["examples/bazi-example.md"],
    }
    for key, _ in rows:
        disc, name = key.split("/")
        site[f"site/knowledge/{key.replace('/', '__')}"] = (
            f"<!-- 判据全文镜像，真源：{blob_link(key)} -->\n\n"
            + _read(ROOT / disc / "references" / name)
        )
    return tracked, site


def validate(tracked: dict[str, str]) -> None:
    """对外文本硬约束：口径脚注、禁句、案例库隔离、非空。"""
    for rel in TRACKED:
        if rel not in tracked or not tracked[rel].strip():
            raise ValueError(f"产物缺失或为空：{rel}")
    for rel, text in tracked.items():
        for line in text.splitlines():
            if any(n in line for n in NEGATION):
                continue
            for bad in FORBIDDEN:
                if bad in line:
                    raise ValueError(f"对外文本出现禁句「{bad}」：{rel}")
    for rel in ("examples/liuyao-example.md", "examples/bazi-example.md"):
        text = tracked[rel]
        for must in ("古籍案例对齐分", "专业意见", "引擎报告原文", "不是现实命中率"):
            if must not in text:
                raise ValueError(f"示例缺口径/结构标记「{must}」：{rel}")
        if "case_library" in text:
            raise ValueError(f"示例不得引用案例库：{rel}")
    if "三条铁律" not in tracked["KNOWLEDGE.md"]:
        raise ValueError("KNOWLEDGE.md 缺铁律章节")
    if "raw.githubusercontent.com" not in tracked["llms.txt"]:
        raise ValueError("llms.txt 必须给 raw 直链")


def compare(tracked: dict[str, str]) -> list[str]:
    """入库产物逐字节同源复验，返回差异说明列表。"""
    problems: list[str] = []
    for rel in TRACKED:
        if rel not in tracked:
            problems.append(f"缺产物：{rel}")
            continue
        p = ROOT / rel
        if not p.is_file():
            problems.append(f"缺文件：{rel}（跑 --write 生成）")
            continue
        want = tracked[rel].replace("\r\n", "\n").encode("utf-8")
        got = p.read_bytes().replace(b"\r\n", b"\n")
        if want != got:
            problems.append(f"内容漂移：{rel}（在盘 {len(got)} B / 应 {len(want)} B）")
    return problems


def write_all(tracked: dict[str, str], site: dict[str, str]) -> None:
    for rel, text in {**tracked, **site}.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def selftest() -> int:
    """内存负例自证；真盘零写入。"""
    rows = kb_rows()
    tracked, _ = build(rows)
    cases: list[tuple[str, bool]] = []

    def check(name: str, fn) -> None:
        try:
            ok = bool(fn())
        except Exception:
            ok = False
        cases.append((name, ok))

    def rejects(fn) -> bool:
        """校验器必须判红（抛 ValueError/RuntimeError）才算这条负例有牙。"""
        try:
            fn()
            return False
        except (ValueError, RuntimeError):
            return True

    check("正例：真源生成的产物通过校验", lambda: validate(tracked) is None)
    check("改一个产物字节 → 同源复验判红", lambda: any(
        "KNOWLEDGE.md" in p for p in compare({**tracked, "KNOWLEDGE.md": tracked["KNOWLEDGE.md"] + "x"})
    ))
    check("删掉一个产物 → 同源复验判红", lambda: any(
        "缺产物" in p for p in compare({k: v for k, v in tracked.items() if k != "kb/INDEX.md"})
    ))
    check("示例删口径脚注 → 校验判红", lambda: rejects(lambda: validate({
        **tracked, "examples/liuyao-example.md": tracked["examples/liuyao-example.md"].replace("古籍案例对齐分", "")
    })))
    check("示例出现禁句 → 校验判红", lambda: rejects(lambda: validate({
        **tracked, "examples/bazi-example.md": tracked["examples/bazi-example.md"] + "预测准确率 99%"
    })))
    check("登记表注入案例库 → 校验判红", lambda: rejects(
        lambda: validate_rows(rows + [("liuyao/case_library.md", "x")])
    ))
    check("登记表指向不存在文件 → 校验判红", lambda: rejects(
        lambda: validate_rows(rows + [("liuyao/nope.md", "x")])
    ))
    check("登记表重复篇目 → 校验判红", lambda: rejects(lambda: validate_rows(rows + [rows[0]])))
    check("产物为空 → 校验判红", lambda: rejects(lambda: validate({**tracked, "llms.txt": ""})))
    check("KNOWLEDGE 丢铁律章节 → 校验判红", lambda: rejects(lambda: validate({
        **tracked, "KNOWLEDGE.md": tracked["KNOWLEDGE.md"].replace("三条铁律", "三条说明")
    })))
    check("登记表为空 → 校验判红", lambda: rejects(lambda: validate_rows([])))

    for name, ok in cases:
        print(f"  {'√' if ok else '×'} {name}")
    bad = [n for n, ok in cases if not ok]
    if bad:
        print(f"selftest 失败 {len(bad)} 项：{'; '.join(bad)}")
        return 1
    print(f"selftest：{len(cases)} 类正/负例全过（真盘零写入）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="对外可发现层构建器")
    ap.add_argument("--write", action="store_true", help="生成入库产物 + site/")
    ap.add_argument("--check", action="store_true", help="入库产物逐字节同源复验")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    rows = kb_rows()
    tracked, site = build(rows)
    validate(tracked)
    if args.write:
        write_all(tracked, site)
        print(f"[outreach] 已写入 {len(tracked)} 份入库产物 + {len(site)} 份 site/ 产物")
        return 0
    problems = compare(tracked)
    if problems:
        for p in problems:
            print("  × " + p)
        print("[outreach] 同源复验判红：对外产物与真源/引擎输出不一致，请跑 --write 后提交")
        return 1
    print(f"[outreach] 同源复验全绿：{len(TRACKED)} 份入库产物与真源逐字节一致；判据篇目 {len(rows)} 篇")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
