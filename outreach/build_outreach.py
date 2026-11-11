# -*- coding: utf-8 -*-
"""对外可发现层构建器（第五百四十九批）：把「代码 + 代码产出的结论」变成静态可读物。

为什么有这一层：网页端大模型联网检索时只能读**静态文本**，不会执行 Python。
本仓此前结论只在运行时产生、当场交付、从不落盘（.gitignore 排掉 outputs/*.html），
外部 AI 即使搜到仓库也读不到任何成品。本器把三样东西从真源**现场生成**并入库：

  1. `llms.txt` / `KNOWLEDGE.md` / `kb/INDEX.md` —— 面向 AI 读者的自包含导览与 raw 直链；
  2. `examples/liuyao-example.md` / `examples/bazi-example.md` —— **由两科四段流水线实跑生成**
     的完整术数结论（固定输入、逐字节可复现，非手写）；
  3. `site/**` —— 不入库（gitignore），供 GitHub Pages Actions 现场生成后部署。
     每篇判据/示例除 `.md` 原文外另出**HTML 可读版**：Pages 对 `.md` 给 `text/markdown`，
     浏览器不保证内联渲染，且标题/表格都是原始标记；HTML 版由内置转换器生成（零第三方依赖），
     转换不完整即判红（代码块未闭合）或按普通段落兜底（绝不丢内容）。

真源：`outreach/KNOWLEDGE-BODY.md`（人写知识正文）、`plugins/scripts/kb-docs.mjs`
（判据篇目登记表，与 `plugins/scripts/build.mjs` 同一份，不新增第二登记表）、
两科 `references/*.md`（判据全文）、两科 `scripts/`（引擎）。

**双登记表对账（552 批加固）**：`kb/INDEX.md`（对外导览，入库）与随包
`skills/yi-divination/references/INDEX.md`（构建产物）同源于 `kb-docs.mjs`，此前只有
「登记了就得在盘」单向检查，解析用宽松正则——认不出的行会被**静默跳过**，
磁盘新增篇目没登记也不会红。本批改为 fail-closed 解析＋四向核对：
① Python 解析 ↔ 直接 import 的 JS `KB_DOC`（node 在 PATH 时逐条比 keys 与描述）；
② 登记表 ↔ 磁盘 `references/*.md`（有文件未登记即红，不再静默缺席）；
③ 登记表 ↔ 随包 `INDEX.md`（已构建时逐篇比，多一篇/少一篇都红）；
④ 每篇 ↔ `llms.txt`／`KNOWLEDGE.md`／`kb/INDEX.md`／`site/kb/INDEX.md` 逐篇可见
（少渲染一篇即红——`kb/INDEX.md` 按科分节，新增第三个科时最容易静默漏）。

    python outreach/build_outreach.py --write       # 生成入库产物 + site/
    python outreach/build_outreach.py --check       # 同源复验 + 双登记表四向对账（CI 挂此）
    python outreach/build_outreach.py --registry    # 只跑双登记表对账（不跑引擎，秒级）
    python outreach/build_outreach.py --selftest    # 内存负例自证，真盘零写入

铁律：示例结论只能由代码生成（§一.1）；示例输入为**新造中性问句**、不触达
`data/cases/` 与 `case_library.md`（§一.2）；所有对外文本带口径脚注（§一.3）。
"""
from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

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
    "examples/liuyao-time-example.md",
    "examples/bazi-example.md",
)

ROW_LINE_RE = re.compile(r"^\['([^']+\.md)',\s*'([^']*)'\],?$")
REGISTRY_BLOCK_OPEN = "new Map(["
REGISTRY_BLOCK_CLOSE = "\n])"
DISCIPLINES = ("liuyao", "bazi")
# 案例库物理隔离（§一.2）与随包索引自身都不是「判据篇目」
NOT_A_ROW = ("INDEX.md", "case_library.md")
FORBIDDEN = ("预测准确率", "断事如神", "命中率 99", "准确率 99")
# 与 plugins 自检 [7] 同口径：口径声明里的否定语境（「不是预测准确率」「不得说断事如神」）
# 是**合规文本**，逐行豁免；只在肯定语境出现禁句才判红。
NEGATION = ("不是", "不得", "禁止", "不可", "不许", "严禁", "不能", "未声称")

# 示例输入：新造中性问句，不来自任何古籍案例集（§一.2）
LY_QUESTION = "示例：某合作项目下月能否顺利推进"
LY_DATETIME = "2026-01-15 10:30"
LY_SEED = 42
LY_TIME_QUESTION = "示例：某岗位竞聘在本季度是否值得投入"
LY_TIME_DATETIME = "2026-03-18 14:00"
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


def parse_registry_text(txt: str) -> list[tuple[str, str]]:
    """fail-closed 解析登记表：认不出的行直接判红，**不静默跳过**。

    552 批之前用全文件宽松正则（`\\['…',\\s*'…'\\]`）——只要某条写成双引号、
    换行或被注释掉，它就被悄悄漏掉，对外层少一篇而四门全绿。现在先把 `new Map([`
    到 `])` 之间的块切出来，块内每一非空、非注释行都必须是单行单引号字面量；
    任一行不合式即抛错并指出行号（新增条目格式不符 = 立刻红，而不是延迟到读者发现）。
    """
    open_at = txt.find(REGISTRY_BLOCK_OPEN)
    if open_at < 0:
        raise ValueError(f"kb-docs.mjs 找不到登记表块 {REGISTRY_BLOCK_OPEN}")
    close_at = txt.find(REGISTRY_BLOCK_CLOSE, open_at)
    if close_at < 0:
        raise ValueError(f"kb-docs.mjs 登记表块未闭合（缺 {REGISTRY_BLOCK_CLOSE!r}）")
    block = txt[open_at + len(REGISTRY_BLOCK_OPEN):close_at]
    rows: list[tuple[str, str]] = []
    bad: list[str] = []
    for lineno, raw in enumerate(block.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("//") or line.startswith("*"):
            continue
        m = ROW_LINE_RE.match(line)
        if not m:
            bad.append(f"第 {lineno} 行 {line[:60]}")
            continue
        rows.append((m.group(1).strip(), m.group(2).strip()))
    if bad:
        raise ValueError(
            "登记表出现无法解析的条目（拒绝静默跳过，必须是单行 ['<科>/<篇>.md', '<描述>']）："
            + "；".join(bad[:3])
        )
    if not rows:
        raise ValueError("kb-docs.mjs 未解析到任何篇目，登记表格式已变")
    return rows


def kb_rows() -> list[tuple[str, str]]:
    """从 kb-docs.mjs 抽篇目登记表——与 build.mjs 共用同一真源。"""
    return parse_registry_text(_read(REGISTRY))


def unregistered_references(rows: list[tuple[str, str]], ref_files: list[str] | None = None) -> list[str]:
    """反向覆盖：磁盘上有判据文件但登记表没登记 → 对外层会静默缺席。

    `ref_files` 可注入（自检用内存夹具，真盘零写入）；缺省时扫两科 `references/`。
    案例库 `case_library.md` 与随包 `INDEX.md` 按设计不进登记表，显式排除。
    """
    if ref_files is None:
        ref_files = []
        for disc in DISCIPLINES:
            for p in sorted((ROOT / disc / "references").glob("*.md")):
                ref_files.append(f"{disc}/{p.name}")
    registered = {key for key, _ in rows}
    return [
        f for f in ref_files
        if Path(f).name not in NOT_A_ROW and f not in registered
    ]


def validate_rows(rows: list[tuple[str, str]]) -> None:
    """登记表面完整性：路径合法、文件在盘、案例库永不进对外层、双向无遗漏。"""
    if not rows:
        raise ValueError("登记表为空：对外知识层不得无篇目")
    seen: set[str] = set()
    basenames: dict[str, str] = {}
    for key, desc in rows:
        if key in seen:
            raise ValueError(f"登记表重复篇目：{key}")
        seen.add(key)
        parts = key.split("/")
        if len(parts) != 2 or parts[0] not in DISCIPLINES or not parts[1].endswith(".md"):
            raise ValueError(f"登记表篇目路径不合法：{key}")
        if parts[1] in NOT_A_ROW:
            raise ValueError(f"该文件不得进入对外知识层（§一.2）：{key}")
        if not desc:
            raise ValueError(f"篇目缺「什么时候读」描述：{key}")
        # 描述会原样进 Markdown 表格：竖线与换行都会把表撑坏，且不会报错
        if "|" in desc or "\n" in desc or "\r" in desc:
            raise ValueError(f"篇目描述含表格分隔符或换行：{key}")
        if parts[1] in basenames:
            raise ValueError(f"两科篇目同名（对外层按 basename 展示会串味）：{key} 与 {basenames[parts[1]]}")
        basenames[parts[1]] = key
        if not (ROOT / parts[0] / "references" / parts[1]).is_file():
            raise ValueError(f"登记表指向不存在的判据文件：{key}")
    missing = unregistered_references(rows)
    if missing:
        raise ValueError(
            "判据文件未登记（对外层会静默少一篇，请补进 kb-docs.mjs）：" + "、".join(missing)
        )


def raw_link(key: str) -> str:
    disc, name = key.split("/")
    return f"{RAW}/{disc}/references/{name}"


def blob_link(key: str) -> str:
    disc, name = key.split("/")
    return f"{BLOB}/{disc}/references/{name}"


PKG_INDEX = ROOT / "plugins" / "skills" / "yi-divination" / "references" / "INDEX.md"
PKG_ROW_RE = re.compile(r"^\| `([^`]+\.md)`", re.M)


def registry_rows_from_node() -> list[tuple[str, str]] | None:
    """直接 import JS 的 `KB_DOC`——登记表的**运行时真值**，与 Python 解析逐条对账。

    Python 侧的 fail-closed 只能保证「没有静默跳过」，保证不了「和 JS 读到的是同一份」：
    JS 的 Map 会静默去重、注释里的 `['a.md','b']` 也不进 Map。故 node 在 PATH 时
    以真实模块为准做逐条比对；node 不在则跳过并打印原因（不静默、也不假绿）。
    """
    node = shutil.which("node")
    if not node:
        return None
    code = (
        "import(" + json.dumps(REGISTRY.as_uri()) + ")"
        ".then(m => process.stdout.write(JSON.stringify([...m.KB_DOC])))"
    )
    proc = subprocess.run(
        [node, "--input-type=module", "-e", code],
        cwd=str(ROOT), capture_output=True, timeout=90,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace")[-600:]
        raise RuntimeError(f"node 读取 KB_DOC 失败（rc={proc.returncode}）：{err}")
    raw = proc.stdout.decode("utf-8", errors="replace").strip()
    if not raw:
        raise RuntimeError("node 读取 KB_DOC 返回空——登记表模块可能已损坏")
    return [(str(k), str(v)) for k, v in json.loads(raw)]


def check_registry_consistency(rows: list[tuple[str, str]]) -> tuple[list[str], bool]:
    """双登记表四向核对的 ①③：JS 真值 ↔ Python 解析、登记表 ↔ 随包 INDEX.md。

    返回 (问题列表, 随包索引是否实际参与核对)——成功文案按**实际核对过的方数**措辞，
    干净树上包里没有 `references/INDEX.md` 时不许自称「四方一致」（那是假全称）。
    """
    problems: list[str] = []

    node_rows = registry_rows_from_node()
    if node_rows is None:
        print("  · node 不在 PATH：跳过 JS 侧逐条对账（fail-closed 解析仍保证零静默跳过）")
    elif node_rows != rows:
        py = dict(rows)
        js = dict(node_rows)
        only_py = [k for k in py if k not in js]
        only_js = [k for k in js if k not in py]
        desc = [k for k in py if k in js and py[k] != js[k]]
        if only_py or only_js or desc:
            problems.append(
                "Python 解析与 JS KB_DOC 不一致："
                f"仅 Py 有 {only_py}；仅 JS 有 {only_js}；描述不同 {desc}"
            )
        else:
            problems.append(
                "Python 解析与 JS KB_DOC 顺序不一致（两份导览的阅读顺序会分家）："
                f"Py {[k for k, _ in rows][:3]}… / JS {[k for k, _ in node_rows][:3]}…"
            )

    if not PKG_INDEX.is_file():
        print("  · 随包 INDEX.md 未构建：跳过包内对账（node plugins/scripts/build.mjs 后自动启用）")
        return problems, False
    txt = _read(PKG_INDEX)
    listed = PKG_ROW_RE.findall(txt)
    want = [key.split("/")[1] for key, _ in rows]
    if listed != want:
        extra = [n for n in listed if n not in want]
        lost = [n for n in want if n not in listed]
        problems.append(
            f"随包 INDEX.md 与登记表不同步：多出 {extra}；缺少 {lost}"
            "（跑 node plugins/scripts/build.mjs 重建）"
        )
    for key, desc in rows:
        if desc not in txt:
            problems.append(f"随包 INDEX.md 的描述与登记表不同源：{key}")
    return problems, True


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
    # Windows 的 print 会把 \n 转成 \r\n；若不在源头归一，rstrip("\n") 遇到 \r 会提前
    # 停止，报告末尾比 Linux 多留一个换行——549 批首轮 Pages 门实测正好差 1 字节。
    text = proc.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
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
    ly_time_code = f"""
import sys
sys.path.insert(0, {str(ly)!r})
from chart import chart
from analyze import analyze
from render import render
a = analyze(chart("time", {LY_TIME_QUESTION!r}, datetime_str={LY_TIME_DATETIME!r}))
print(render(a, fmt="md"), end="")
"""
    return {
        "liuyao": _engine_report(ly, ly_code),
        "liuyao_time": _engine_report(ly, ly_time_code),
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


def _site_index_md(rows: list[tuple[str, str]], mirrors: dict[str, str]) -> str:
    """`kb/INDEX.md` 的 Pages 镜像：篇目/顺序/「什么时候读」同源，链接改站内相对路径。

    与 `kb/INDEX.md` 的差别只有链接形态：那边给绝对 raw 直链（服务联网检索的 AI），
    这边给站内相对路径（服务断网/离线下载后的完整阅读）。两者都由登记表现场生成，
    不互为真源，也不许手改。

    **为什么落在 `site/kb/` 而不是 `site/` 根**：Windows 文件系统大小写不敏感，
    `site/INDEX.md` 与 `site/index.md`、`site/INDEX.html` 与 `site/index.html` 是同一个文件
    （552 批实测：`Path('site/INDEX.md').resolve()` 指回 `site\\index.md`），写在根上会
    互相覆盖、把 Pages 首页顶掉。放在 `kb/` 子目录后与仓库 `kb/INDEX.md` 路径一一对应，
    且与根上的 `index.*` 不再同名。
    """
    lines = [
        "# 判据知识库索引 · 离线镜像（Pages 版）",
        "",
        "> 本页是仓库 `kb/INDEX.md` 的镜像：篇目、顺序与「什么时候读」逐条同源于",
        "> `plugins/scripts/kb-docs.mjs`，但链接指向**本站内的离线副本**——不依赖网络、",
        "> raw 直链或 JS。由 `outreach/build_outreach.py --write` 现场生成，勿手改。",
        "",
        "## 怎么离线读",
        "",
        "- 整站是纯静态文件：离线解压后直接打开本页或同目录的 `INDEX.html`（无 JS、无外链、无 CDN）。",
        "- 每篇判据在 `../knowledge/`（相对本页）有**可读 HTML 全文**，示例在 `../examples/`；点开即网页。",
        "- 每篇另有同名 `.md` 原文（同目录），适合直接抓取、diff 或喂给工具；内容与 HTML 逐字同源。",
        "- 需要确认真源时再用仓库 `kb/INDEX.md` 的 raw 直链（需联网）。",
        "",
    ]
    for disc, title in (("liuyao", "六爻"), ("bazi", "八字")):
        lines += [f"## {title}", "", "| 篇目 | 什么时候读 | 离线副本 | 字节 |", "|---|---|---|---|"]
        for key, desc in rows:
            if not key.startswith(disc + "/"):
                continue
            mirror = key.replace('/', '__')[:-3]
            rel = f"../knowledge/{mirror}.html"
            size = len(mirrors[f"knowledge/{key.replace('/', '__')}"].encode("utf-8"))
            lines.append(f"| `{key.split('/')[1]}` | {desc} | [{mirror}.html]({rel}) | {size} |")
        lines.append("")
    lines += [
        "## 示例结论（引擎实跑）",
        "",
        "- [六爻纳甲占报告](../examples/liuyao-example.html)",
        "- [六爻时间起卦报告](../examples/liuyao-time-example.html)",
        "- [八字命局因子说明](../examples/bazi-example.html)",
        "",
        "## 其它入口",
        "",
        "- [首页](../index.html) · [知识速读全文](../KNOWLEDGE.md) · [llms.txt](../llms.txt)",
        "",
        "## ⛔ 不在本站的内容",
        "",
        "古籍案例库 `case_library.md` 刻意不进入对外层与发布包（AGENTS.md §一.2）：",
        "它在仓库中公开只为测试与审计，**解读时不得引用、联想或类比**。",
        "",
    ]
    return "\n".join(lines)


def _site_index_html(rows: list[tuple[str, str]], mirrors: dict[str, str]) -> str:
    """`INDEX.md` 的可点版本：Pages 不做 Jekyll 渲染，`.md` 只能当纯文本看；
    这份 HTML 让「离线也能一页点到底」，与 INDEX.md 同源于同一份 rows。"""
    esc = html.escape

    def table(disc: str) -> str:
        out = [
            "<table>",
            "<thead><tr><th>篇目</th><th>什么时候读</th><th>离线副本</th><th>字节</th></tr></thead>",
            "<tbody>",
        ]
        for key, desc in rows:
            if not key.startswith(disc + "/"):
                continue
            name = key.split("/")[1]
            mirror = key.replace("/", "__")[:-3]
            rel = f"../knowledge/{mirror}.html"
            size = len(mirrors[f"knowledge/{key.replace('/', '__')}"].encode("utf-8"))
            out.append(
                f'<tr><td><code>{esc(name)}</code></td><td>{esc(desc)}</td>'
                f'<td><a href="{rel}">{esc(name)}</a></td><td class="n">{size}</td></tr>'
            )
        out += ["</tbody>", "</table>"]
        return "\n".join(out)

    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>判据知识库索引 · 易（Yi）</title>\n"
        "<meta name=\"description\" content=\"判据篇目离线索引：每篇的用途、站内全文副本与字节数，无需联网。\">\n"
        "<style>\n"
        "body{max-width:60rem;margin:2rem auto;padding:0 1rem;font:16px/1.7 -apple-system,"
        "\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif;color:#1f2328;background:#fff}\n"
        "h1{font-size:1.6rem}h2{margin-top:2rem;border-bottom:1px solid #d8dee4;padding-bottom:.3rem}\n"
        "table{border-collapse:collapse;width:100%;margin:.5rem 0;font-size:.94rem}\n"
        "th,td{border:1px solid #d8dee4;padding:.45rem .6rem;text-align:left;vertical-align:top}\n"
        "th{background:#f6f8fa}code{background:#f6f8fa;padding:.1rem .3rem;border-radius:3px}\n"
        "td.n{text-align:right;white-space:nowrap;color:#57606a}\n"
        "blockquote{margin:1rem 0;padding:.5rem 1rem;border-left:3px solid #d0d7de;color:#57606a}\n"
        "</style>\n</head>\n<body>\n"
        "<h1>判据知识库索引 · 离线镜像</h1>\n"
        "<blockquote><p>本页是仓库 <code>kb/INDEX.md</code> 的镜像：篇目、顺序与「什么时候读」"
        "逐条同源于 <code>plugins/scripts/kb-docs.mjs</code>，链接指向本站内的全文副本，"
        "<strong>断网也可完整阅读</strong>。由 <code>outreach/build_outreach.py --write</code> 生成。</p></blockquote>\n"
        "<h2>六爻</h2>\n" + table("liuyao") + "\n"
        "<h2>八字</h2>\n" + table("bazi") + "\n"
        "<h2>示例结论（引擎实跑）</h2>\n<ul>\n"
        '<li><a href="../examples/liuyao-example.html">六爻纳甲占报告</a></li>\n'
        '<li><a href="../examples/liuyao-time-example.html">六爻时间起卦报告</a></li>\n'
        '<li><a href="../examples/bazi-example.html">八字命局因子说明</a></li>\n'
        "</ul>\n"
        "<h2>其它入口</h2>\n<ul>\n"
        '<li><a href="../index.html">首页</a> · <a href="../KNOWLEDGE.md">知识速读全文</a> · '
        '<a href="../llms.txt">llms.txt</a> · <a href="INDEX.md">本页 Markdown 版</a></li>\n'
        "</ul>\n"
        "<h2>⛔ 不在本站的内容</h2>\n"
        "<p>古籍案例库 <code>case_library.md</code> 刻意不进入对外层与发布包（AGENTS.md §一.2）："
        "它在仓库中公开只为测试与审计，<strong>解读时不得引用、联想或类比</strong>。</p>\n"
        "<hr>\n<p>源码：<a href=\"" + REPO + "\">github.com/LinHoMo/Yi</a> · MIT License</p>\n"
        "</body>\n</html>\n"
    )


def _relative_links(text: str) -> list[str]:
    """抽出站内相对链接（Markdown 与 href 两种写法），跳过外链与锚点。"""
    found = re.findall(r"\]\(([^)\s]+)\)", text) + re.findall(r'href="([^"]+)"', text)
    return [l for l in found if not l.startswith(("http://", "https://", "mailto:", "#"))]


def check_site_links(site: dict[str, str], from_key: str) -> list[str]:
    """站内相对链接必须都能落到 site/ 里真实存在的文件——「离线可完整阅读」不能只是口号。

    552 批把 INDEX 放在 `site/kb/` 下，链接写成 `../knowledge/…`；一旦镜像命名规则
    变了而链接没跟，Pages 上就是一串 404 而构建照样绿（549/551 两次踩过示例 404）。
    """
    if from_key not in site:
        return [f"{from_key} 不在 site 产物中（覆盖检查应同时报出）"]
    problems: list[str] = []
    base = PurePosixPath(from_key).parent
    for tgt in _relative_links(site[from_key]):
        resolved = posixpath.normpath(str(base / tgt))
        if resolved not in site:
            problems.append(f"{from_key} 的相对链接指向不存在的站内文件：{tgt}")
    return problems


# 552 批：Pages 离线可读版——保守的 Markdown→HTML 转换器（零第三方依赖）
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s+(.*)$")
HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
HR_RE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
FENCE_RE = re.compile(r"^```(\w*)\s*$")
SEP_RE = re.compile(r"^[|]?[\s:|-]+[|]?$")


def _is_cjk(ch: str) -> bool:
    return ("\u4e00" <= ch <= "\u9fff") or ch in "，。！？；：、（）《》“”‘’…—"


def _join_lines(lines: list[str]) -> str:
    """段内换行折叠：中文之间不插空格（硬折行的中文文档否则会满屏空格）。"""
    out = ""
    for ln in lines:
        ln = ln.strip()
        if not ln:
            continue
        if not out:
            out = ln
        elif _is_cjk(out[-1]) and _is_cjk(ln[0]):
            out += ln
        else:
            out += " " + ln
    return out


def _inline(text: str, resolve) -> str:
    """行内语法：优先切出行内代码（其中 ** 与 [] 不得被继续处理），其余先转义再加标记。"""
    out = []
    for part in re.split(r"(`[^`]+`)", text):
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            out.append("<code>" + html.escape(part[1:-1], quote=False) + "</code>")
            continue
        seg = html.escape(part, quote=False)
        seg = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", seg)
        seg = re.sub(
            r"\[([^\]]+)\]\(([^)\s]+)\)",
            lambda m: _anchor(m.group(1), m.group(2), resolve),
            seg,
        )
        out.append(seg)
    return "".join(out)


def _anchor(label: str, href: str, resolve) -> str:
    target = resolve(href)
    if target is None:  # 案例库等按 §一.2 不得出现在对外层：只留文字，不做链接
        return label
    return f'<a href="{html.escape(target, quote=True)}">{label}</a>'


def _split_cells(row: str) -> list[str]:
    row = row.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    cells, cur, in_code = [], "", False
    for ch in row:
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append(cur)
            cur = ""
        else:
            cur += ch
    cells.append(cur)
    return [c.strip() for c in cells]


def _aligns(sep: str) -> list[str]:
    out = []
    for c in _split_cells(sep):
        left, right = c.startswith(":"), c.endswith(":")
        out.append("center" if left and right else "right" if right else "")
    return out


def _table_html(header: list[str], aligns: list[str], rows: list[list[str]], resolve) -> str:
    def cell(tag: str, text: str, i: int) -> str:
        style = f' style="text-align:{aligns[i]}"' if i < len(aligns) and aligns[i] else ""
        return f"<{tag}{style}>{_inline(text, resolve)}</{tag}>"

    out = ["<table>", "<thead><tr>"]
    out += [cell("th", h, i) for i, h in enumerate(header)]
    out += ["</tr></thead>", "<tbody>"]
    for row in rows:
        row = (row + [""] * len(header))[: len(header)]
        out.append("<tr>" + "".join(cell("td", c, i) for i, c in enumerate(row)) + "</tr>")
    out += ["</tbody>", "</table>"]
    return "\n".join(out)


def _render_list(lines: list[str], resolve) -> str:
    items = []
    for ln in lines:
        m = LIST_RE.match(ln)
        items.append((len(m.group(1)), m.group(2)[0].isdigit(), m.group(3)))

    def build(seq):
        tag = "ol" if seq[0][1] else "ul"
        out, i = [f"<{tag}>"], 0
        while i < len(seq):
            indent, _ordered, text = seq[i]
            j = i + 1
            while j < len(seq) and seq[j][0] > indent:
                j += 1
            li = "<li>" + _inline(text, resolve)
            if j > i + 1:
                li += build(seq[i + 1:j])
            out.append(li + "</li>")
            i = j
        out.append(f"</{tag}>")
        return "\n".join(out)

    return build(items)


def _starts_block(lines: list[str], i: int) -> bool:
    line = lines[i]
    if FENCE_RE.match(line) or HEAD_RE.match(line) or HR_RE.match(line.strip()):
        return True
    if line.startswith(">") or LIST_RE.match(line):
        return True
    return (
        line.lstrip().startswith("|")
        and i + 1 < len(lines)
        and SEP_RE.match(lines[i + 1].strip()) is not None
        and "-" in lines[i + 1]
    )


def md_to_html(md: str, resolve) -> str:
    """把判据/示例的 Markdown 转成可读 HTML。只覆盖仓内实际用到的语法；
    认不出的行按普通段落输出（**绝不丢内容**），代码块未闭合则直接判红。"""
    lines = md.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    # 生成器注释（`<!-- … -->`）是给 diff/构建看的，不该出现在读者页上
    lines = ["" if re.match(r"^\s*<!--.*-->\s*$", ln) else ln for ln in lines]
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = FENCE_RE.match(line)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < len(lines) and not re.match(r"^```\s*$", lines[i]):
                buf.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("Markdown 代码块未闭合（渲染会截断后文）")
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            blocks.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf), quote=False)}</code></pre>")
            continue
        m = HEAD_RE.match(line)
        if m:
            n = len(m.group(1))
            blocks.append(f"<h{n}>{_inline(m.group(2), resolve)}</h{n}>")
            i += 1
            continue
        if HR_RE.match(line.strip()):
            blocks.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and SEP_RE.match(lines[i + 1].strip()) and "-" in lines[i + 1]:
            header = _split_cells(line)
            aligns = _aligns(lines[i + 1])
            i += 2
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(_split_cells(lines[i]))
                i += 1
            blocks.append(_table_html(header, aligns, rows, resolve))
            continue
        if line.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append("<blockquote><p>" + "<br>".join(_inline(b, resolve) for b in buf) + "</p></blockquote>")
            continue
        if LIST_RE.match(line):
            buf = []
            while i < len(lines):
                if LIST_RE.match(lines[i]):
                    buf.append(lines[i])
                    i += 1
                elif not lines[i].strip() and i + 1 < len(lines) and LIST_RE.match(lines[i + 1]):
                    i += 1
                else:
                    break
            blocks.append(_render_list(buf, resolve))
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not _starts_block(lines, i):
            buf.append(lines[i])
            i += 1
        blocks.append("<p>" + _inline(_join_lines(buf), resolve) + "</p>")
    return "\n".join(blocks)



PAGE_CSS = (
    "body{max-width:52rem;margin:0 auto;padding:1.5rem 1rem 3rem;"
    "font:17px/1.85 -apple-system,\"Segoe UI\",\"Noto Sans CJK SC\",sans-serif;"
    "color:#1f2328;background:#fff}"
    "nav{font-size:.9rem;padding:.4rem 0 1rem;border-bottom:1px solid #d8dee4;margin-bottom:1.2rem}"
    "nav a{color:#0969da;text-decoration:none;margin-right:.4rem}"
    "h1,h2,h3,h4{line-height:1.4;margin:1.6em 0 .6em}h1{font-size:1.55rem}"
    "h2{font-size:1.3rem;border-bottom:1px solid #eaeef2;padding-bottom:.25rem}h3{font-size:1.12rem}"
    "table{border-collapse:collapse;width:100%;margin:.8rem 0;font-size:.93rem;display:block;overflow-x:auto}"
    "th,td{border:1px solid #d8dee4;padding:.4rem .55rem;vertical-align:top}"
    "th{background:#f6f8fa;white-space:nowrap}"
    "code{background:#f6f8fa;padding:.1rem .3rem;border-radius:3px;font-size:.92em}"
    "pre{background:#f6f8fa;padding:.8rem 1rem;border-radius:6px;overflow-x:auto;line-height:1.55}"
    "pre code{background:none;padding:0}"
    "blockquote{margin:1rem 0;padding:.4rem 1rem;border-left:3px solid #d0d7de;color:#57606a}"
    "hr{border:0;border-top:1px solid #d8dee4;margin:2rem 0}"
    "footer{margin-top:3rem;padding-top:1rem;border-top:1px solid #d8dee4;"
    "font-size:.85rem;color:#57606a}"
)


def _page_html(title: str, body: str, page_dir: str, md_mirror: str) -> str:
    """单篇离线页外壳：顶部回索引、右上给 Markdown 原文，底部带口径脚注。"""
    back = posixpath.relpath("kb/INDEX.html", page_dir or ".")
    md_rel = posixpath.relpath(md_mirror, page_dir or ".")
    return (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n<style>\n{PAGE_CSS}\n</style>\n</head>\n<body>\n"
        f'<nav><a href="{back}">← 判据索引</a> · <a href="{md_rel}">Markdown 原文</a></nav>\n'
        f"<main>\n{body}\n</main>\n"
        "<footer>本页是仓库判据/示例的离线镜像，由 <code>outreach/build_outreach.py</code> 生成。"
        "仓库内一切分数都是<strong>古籍案例对齐分</strong>（回归审计用），<strong>不是现实命中率</strong>；"
        "现实侧样本为零。本工具不是预言；医疗、法律、投资、重大决策请以专业意见为准。</footer>\n"
        "</body>\n</html>\n"
    )


def _resolver(base_dir: str, page_dir: str, repo_map: dict[str, str]):
    """把文档里的链接解析成站内相对路径：镜像内的跳镜像、未镜像的仓内文件跳 GitHub、外链原样。"""

    def resolve(href: str):
        if href.startswith(("http://", "https://", "mailto:", "#")):
            return href
        path, _, frag = href.partition("#")
        tail = ("#" + frag) if frag else ""
        repo = posixpath.normpath(posixpath.join(base_dir, path) if base_dir else path)
        if "case_library" in repo:
            return None  # §一.2：案例库不得以链接形式出现在对外层
        if repo in repo_map:
            return posixpath.relpath(repo_map[repo], page_dir or ".") + tail
        if (ROOT / repo).exists():
            return f"{BLOB}/{repo}{tail}"
        return href + tail

    return resolve


def check_artifact_coverage(
    rows: list[tuple[str, str]],
    tracked: dict[str, str],
    site: dict[str, str],
) -> list[str]:
    """④ 逐篇覆盖：每篇在四份对外产物里都必须恰好出现一次、且站内有全文镜像。

    `kb/INDEX.md` 与 `site/kb/INDEX.md` 都是按科分节拼的——新增第三个科、或改
    `startswith` 分支时最容易「少渲染一节但全门皆绿」。这条断言把它变成红。
    """
    problems: list[str] = []
    llms = tracked["llms.txt"]
    kidx = tracked["kb/INDEX.md"]
    kbody = tracked["KNOWLEDGE.md"]
    sindex_md = site["site/kb/INDEX.md"]
    sindex_html = site["site/kb/INDEX.html"]
    for key, _ in rows:
        name = key.split("/")[1]
        if llms.count(key) != 1:
            problems.append(f"llms.txt 未恰好列出一次：{key}（实 {llms.count(key)}）")
        # 两份索引表都只展示 basename（表头是「篇目」），按表格行首判是否渲染过
        if kidx.count(f"| `{name}` |") != 1:
            problems.append(f"kb/INDEX.md 未恰好列出一次：{key}（实 {kidx.count(f'| `{name}` |')}）")
        if sindex_md.count(f"| `{name}` |") != 1:
            problems.append(f"site/kb/INDEX.md 未恰好列出一次：{key}")
        if name not in kbody:
            problems.append(f"KNOWLEDGE.md 未列出：{key}")
        if f"site/knowledge/{key.replace('/', '__')}" not in site:
            problems.append(f"site/ 缺判据镜像：{key}")
        if f"site/knowledge/{key.replace('/', '__')[:-3]}.html" not in site:
            problems.append(f"site/ 缺判据可读版：{key}")
    if sindex_md.count("](../knowledge/") != len(rows):
        problems.append("site/kb/INDEX.md 的离线副本行数与登记表不符")
    if sindex_html.count('href="../knowledge/') != len(rows):
        problems.append("site/kb/INDEX.html 的离线副本行数与登记表不符")
    # 首页与每篇可读版同样只放相对链接：镜像命名一变就 404 而构建照样绿（549/551 两次踩过）
    for rel in ("site/index.html", "site/index.md", "site/kb/INDEX.md", "site/kb/INDEX.html", "site/KNOWLEDGE.html"):
        problems += check_site_links(site, rel)
    for key, _ in rows:
        problems += check_site_links(site, f"site/knowledge/{key.replace('/', '__')[:-3]}.html")
    for rel in ("examples/liuyao-example.html", "examples/liuyao-time-example.html", "examples/bazi-example.html"):
        if f"site/{rel}" in site:
            problems += check_site_links(site, f"site/{rel}")
    return problems

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
        f"- [判据索引离线镜像]({PAGES}kb/INDEX.md)：同一批篇目的站内全文副本，断网也能逐篇读完",
        f"- [GitHub Pages 站点]({PAGES})：无需登录的静态知识镜像",
        "",
        "## 代码产出的实际结论（引擎实跑示例报告）",
        "",
        f"- [六爻纳甲占报告示例]({RAW}/examples/liuyao-example.md)：固定输入下的完整六爻结论与应期窗口",
        f"- [六爻时间起卦报告示例]({RAW}/examples/liuyao-time-example.md)：time 模式确定性起卦、同一时刻必得同卦",
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
        f"- 六爻·时间起卦：[examples/liuyao-time-example.md]({RAW}/examples/liuyao-time-example.md)",
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
        f"- 离线镜像（Pages，可点）：{PAGES}kb/INDEX.html · Markdown 版 {PAGES}kb/INDEX.md",
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
        f"- [六爻时间起卦示例]({RAW}/examples/liuyao-time-example.md)",
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
    ly_time_input = (
        f"mode=time, question=「{LY_TIME_QUESTION}」, datetime={LY_TIME_DATETIME}（确定性起卦，不接 seed）"
    )
    ly_repro = (
        "python -c \"import sys;sys.path.insert(0,'liuyao/scripts');"
        "from chart import chart;from analyze import analyze;from render import render;"
        f"print(render(analyze(chart('coin','{LY_QUESTION}',datetime_str='{LY_DATETIME}',seed={LY_SEED})),fmt='md'))\""
    )
    ly_time_repro = (
        "python -c \"import sys;sys.path.insert(0,'liuyao/scripts');"
        "from chart import chart;from analyze import analyze;from render import render;"
        f"print(render(analyze(chart('time','{LY_TIME_QUESTION}',datetime_str='{LY_TIME_DATETIME}')),fmt='md'))\""
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
        "examples/liuyao-time-example.md": _example(
            "示例报告 · 六爻时间起卦（引擎实跑）", ly_time_repro, ly_time_input, reports["liuyao_time"]
        ),
        "examples/bazi-example.md": _example(
            "示例报告 · 八字四柱（引擎实跑）", bz_repro, bz_input, reports["bazi"]
        ),
    }

    # 4) site/ —— 不入库，Pages Actions 现场生成
    # Pages 首页必须是 index.html：upload-pages-artifact 不做 Jekyll 渲染，
    # 只放 index.md 时 `/` 会落到 GitHub 错误页（549 批首轮实测），而 `/llms.txt` 正常。
    # 同一原因：`.md` 在 Pages 上是纯文本，没法点，故 552 批另出 INDEX.html 做可点版。
    # 纯静态、无 JS；首页仍给绝对 raw 直链（联网检索的 AI 直接跟进），
    # INDEX 页改给站内相对路径（断网/离线下载后仍能一页读全）。
    mirrors: dict[str, str] = {}
    for key, _ in rows:
        disc, name = key.split("/")
        mirrors[f"knowledge/{key.replace('/', '__')}"] = (
            f"<!-- 判据全文镜像，真源：{blob_link(key)} -->\n\n"
            + _read(ROOT / disc / "references" / name)
        )
    # 判据/示例的离线可读版：Pages 对 .md 给 text/markdown，浏览器不一定内联，
    # 且表格/标题都是原始标记；同一内容再出一份 HTML，断网也能当网页读。
    repo_map: dict[str, str] = {"kb/INDEX.md": "kb/INDEX.html", "KNOWLEDGE.md": "KNOWLEDGE.html"}
    for key, _ in rows:
        disc, name = key.split("/")
        repo_map[f"{disc}/references/{name}"] = f"knowledge/{key.replace('/', '__')[:-3]}.html"
    for rel in tracked:
        if rel.startswith("examples/"):
            repo_map[rel] = rel[:-3] + ".html"
    pages: dict[str, str] = {}
    for key, _ in rows:
        disc, name = key.split("/")
        stem = key.replace("/", "__")[:-3]
        pages[f"knowledge/{stem}.html"] = _page_html(
            f"{name} · 易（Yi）",
            md_to_html(_read(ROOT / disc / "references" / name), _resolver(f"{disc}/references", "knowledge", repo_map)),
            "knowledge",
            f"knowledge/{stem}.md",
        )
    for rel in [r for r in tracked if r.startswith("examples/")]:
        pages[rel[:-3] + ".html"] = _page_html(
            f"{Path(rel).stem} · 易（Yi）",
            md_to_html(tracked[rel], _resolver("examples", "examples", repo_map)),
            "examples",
            rel,
        )
    pages["KNOWLEDGE.html"] = _page_html(
        "知识速读 · 易（Yi）",
        md_to_html(knowledge, _resolver("", ".", repo_map)),
        ".",
        "KNOWLEDGE.md",
    )

    index_md = _site_index_md(rows, mirrors)
    index_html_offline = _site_index_html(rows, mirrors)

    nav_rows = "\n".join(
        f'<li><a href="knowledge/{key.replace("/", "__")[:-3]}.html">{key}</a> — {desc}</li>'
        for key, desc in rows
    )
    index_html = (
        "<!doctype html>\n<html lang=\"zh-CN\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>易（Yi）· 术数知识与引擎示例</title>\n"
        "<meta name=\"description\" content=\"六爻纳甲与八字四柱的确定性排盘引擎："
        "判据知识库、代码实跑产出的完整结论报告、能力边界与安装入口。\">\n"
        "</head>\n<body>\n"
        "<h1>易（Yi）· 术数知识与引擎示例</h1>\n"
        "<p>本仓库同时提供<strong>代码</strong>与<strong>代码实跑产出的术数结论</strong>。"
        "机械运算归 Python 代码，象数解读归语言模型。</p>\n"
        "<blockquote><p>仓库内一切分数都是<strong>古籍案例对齐分</strong>（回归审计用），"
        "<strong>不是现实命中率</strong>；现实侧样本为零。本工具不是预言；"
        "医疗、法律、投资、重大决策请以专业意见为准。</p></blockquote>\n"
        "<h2>离线也能读全（站内镜像，不依赖网络）</h2>\n<ul>\n"
        '<li><a href="kb/INDEX.html">判据知识库总索引</a> — 每篇的用途与站内全文副本，可点</li>\n'
        '<li><a href="kb/INDEX.md">同一索引的 Markdown 版</a> · '
        '<a href="KNOWLEDGE.html">知识速读（可读版）</a> · <a href="KNOWLEDGE.md">Markdown 原文</a> · '
        '<a href="llms.txt">llms.txt</a></li>\n'
        "</ul>\n"
        "<h2>给 AI 读者的入口（绝对 raw 直链）</h2>\n<ul>\n"
        f'<li><a href="{RAW}/llms.txt">llms.txt</a> — 机器可读的全部入口清单</li>\n'
        f'<li><a href="{RAW}/KNOWLEDGE.md">KNOWLEDGE.md</a> — 自包含知识速读、术语表、铁律与 FAQ</li>\n'
        f'<li><a href="{RAW}/kb/INDEX.md">kb/INDEX.md</a> — 判据篇目路由表</li>\n'
        f'<li><a href="{RAW}/CAPABILITY.md">CAPABILITY.md</a> — 能力读数与边界</li>\n'
        f'<li><a href="{RAW}/README.md">README.md</a> — 安装与 clone／skills／插件使用</li>\n'
        "</ul>\n"
        "<h2>代码产出的实际结论</h2>\n<ul>\n"
        f'<li><a href="{RAW}/examples/liuyao-example.md">六爻纳甲占报告（引擎实跑）</a></li>\n'
        f'<li><a href="{RAW}/examples/liuyao-time-example.md">六爻时间起卦报告（引擎实跑）</a></li>\n'
        f'<li><a href="{RAW}/examples/bazi-example.md">八字命局因子说明（引擎实跑）</a></li>\n'
        "</ul>\n"
        "<p>三份示例均由固定输入下的四段流水线 <code>chart → analyze → narrate → render</code> "
        "现场生成，逐字节同源复验；静态示例不能代替现场起卦。</p>\n"
        "<h2>判据知识库（站内可读版，按需读、勿整本读）</h2>\n<ul>\n" + nav_rows + "\n</ul>\n"
        "<h2>不用于解读</h2>\n"
        "<p><code>case_library.md</code> 虽在仓库公开，按 AGENTS.md §一.2 与解读物理隔离："
        "断卦时不得打开、不得提及案例名、不得以案例类比佐证。</p>\n"
        "<hr>\n<p>源码：<a href=\"" + REPO + "\">github.com/LinHoMo/Yi</a> · MIT License</p>\n"
        "</body>\n</html>\n"
    )
    site: dict[str, str] = {
        "site/index.html": index_html,
        "site/kb/INDEX.md": index_md,
        "site/kb/INDEX.html": index_html_offline,
        "site/KNOWLEDGE.md": knowledge,
        "site/index.md": (
            "# Yi · 术数知识与引擎示例（静态镜像）\n\n"
            f"> 本页是 [{PAGES}]({PAGES}) 的入口；仓库真源见 "
            f"[{REPO}]({REPO})。本页内容由 `outreach/build_outreach.py` 生成，不依赖 JS 即可阅读。\n\n"
            "- [判据总索引（离线可读）](kb/INDEX.html) · [Markdown 版](kb/INDEX.md)\n"
            "- [知识速读（本页全文）](#) ← 下方正文\n"
            "- [llms.txt](llms.txt)（机器可读索引）\n"
            "- 判据全文（可读版）：" + "、".join(
                f"[{key.split('/')[1]}](knowledge/{key.replace('/', '__')[:-3]}.html)" for key, _ in rows
            ) + "\n"
            "- 同名 `.md` 原文仍在同目录，供抓取与 diff。\n"
            "- 示例结论：[六爻报告](examples/liuyao-example.md)、[六爻时间起卦](examples/liuyao-time-example.md)、[八字报告](examples/bazi-example.md)\n\n"
            "---\n\n" + knowledge
        ),
        "site/llms.txt": "\n".join(llms),
        "site/examples/liuyao-example.md": tracked["examples/liuyao-example.md"],
        "site/examples/liuyao-time-example.md": tracked["examples/liuyao-time-example.md"],
        "site/examples/bazi-example.md": tracked["examples/bazi-example.md"],
    }
    for rel, text in mirrors.items():
        site[f"site/{rel}"] = text
    for rel, text in pages.items():
        site[f"site/{rel}"] = text
    # 守卫：每个入库示例必须在 site/ 有镜像，否则 Pages 会 404（549/551 两次踩过）
    for rel in tracked:
        if rel.startswith("examples/"):
            assert f"site/{rel}" in site, f"site/ 缺少示例镜像：{rel}"
    # 守卫：双登记表的每一篇在四份对外产物＋站内镜像里都要恰好出现一次
    problems = check_artifact_coverage(rows, tracked, site)
    if problems:
        raise ValueError("对外层逐篇覆盖不全：" + "；".join(problems[:6]))
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
    for rel in (k for k in tracked if k.startswith("examples/")):
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
    tracked, site = build(rows)
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
    check("正例：逐篇覆盖无缺口", lambda: check_artifact_coverage(rows, tracked, site) == [])
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
    # ---- 552 批新增：双登记表对账的每条规则都要有负例（否则规则是摆设）
    check("登记表用双引号写条目 → 解析判红（不静默跳过）", lambda: rejects(
        lambda: parse_registry_text("export const KB_DOC = new Map([\n"
                                    "  ['liuyao/a.md', 'x'],\n"
                                    "  [\"liuyao/b.md\", \"y\"],\n"
                                    "])\n")
    ))
    check("登记表块未闭合 → 解析判红", lambda: rejects(
        lambda: parse_registry_text("new Map([\n  ['liuyao/a.md', 'x'],\n")
    ))
    check("磁盘有判据未登记 → 校验判红（反向覆盖）", lambda: rejects(
        lambda: validate_rows([r for r in rows if not r[0].endswith("najia_rules.md")])
    ))
    check("篇目描述含竖线（撑坏表格）→ 校验判红", lambda: rejects(
        lambda: validate_rows([(rows[0][0], rows[0][1] + "|x")] + rows[1:])
    ))
    check("两科篇目同名 → 校验判红", lambda: rejects(
        lambda: validate_rows(rows + [("bazi/" + rows[0][0].split("/")[1], "x")])
    ))
    check("kb/INDEX.md 漏渲染一篇 → 覆盖判红", lambda: bool(check_artifact_coverage(
        rows,
        {**tracked, "kb/INDEX.md": "\n".join(
            l for l in tracked["kb/INDEX.md"].splitlines()
            if f"| `{rows[0][0].split('/')[1]}` |" not in l
        )},
        site,
    )))
    check("site/ 缺判据镜像 → 覆盖判红", lambda: bool(check_artifact_coverage(
        rows, tracked, {k: v for k, v in site.items() if not k.endswith("najia_rules.md")}
    )))
    check("Markdown 代码块未闭合 → 转换判红（不静默截断后文）", lambda: rejects(
        lambda: md_to_html("前文\n```\n乾纳甲壬\n", lambda h: h)
    ))
    check("表格行不被当成普通段落（渲染完整）", lambda: (
        "<p>|" not in md_to_html("| a | b |\n|---|---|\n| 1 | 2 |\n", lambda h: h)
        and md_to_html("| a | b |\n|---|---|\n| 1 | 2 |\n", lambda h: h).count("<tr>") == 2
    ))
    check("生成器注释不进读者页", lambda: "<!--" not in md_to_html(
        "<!-- 由构建器生成 -->\n# 标题\n", lambda h: h
    ))
    check("案例库链接只留文字、不生成 <a>（§一.2）", lambda: "<a" not in md_to_html(
        "见 [案例库](../../liuyao/references/case_library.md)。", lambda h: None
    ))
    check("缺判据可读版 → 覆盖判红", lambda: bool(check_artifact_coverage(
        rows, tracked, {k: v for k, v in site.items() if not k.endswith("najia_rules.html")}
    )))
    check("首页站内链接指空 → 链接门判红", lambda: bool(check_site_links(
        {**site, "site/index.html": site["site/index.html"].replace(
            'href="kb/INDEX.html"', 'href="kb/NOPE.html"')},
        "site/index.html",
    )))
    check("INDEX 站内链接指空 → 链接门判红", lambda: bool(check_site_links(
        {**site, "site/kb/INDEX.md": site["site/kb/INDEX.md"].replace(
            "../examples/liuyao-example.html", "../examples/nope.html")},
        "site/kb/INDEX.md",
    )))
    check("site/kb/INDEX.md 漏一篇 → 覆盖判红", lambda: bool(check_artifact_coverage(
        rows,
        tracked,
        {**site, "site/kb/INDEX.md": "\n".join(
            l for l in site["site/kb/INDEX.md"].splitlines() if rows[0][0].split("/")[1] not in l
        )},
    )))

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
    ap.add_argument("--check", action="store_true", help="同源复验 + 双登记表四向对账")
    ap.add_argument("--registry", action="store_true", help="只跑双登记表对账（不跑引擎，秒级）")
    ap.add_argument("--selftest", action="store_true", help="内存负例自证")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.registry:
        try:
            rows = kb_rows()
            validate_rows(rows)
        except ValueError as exc:
            print(f"  × {exc}")
            print("[outreach] 双登记表对账判红：两侧条目不一致或有遗漏")
            return 1
        problems, pkg_checked = check_registry_consistency(rows)
        if problems:
            for p in problems:
                print("  × " + p)
            print("[outreach] 双登记表对账判红：两侧条目不一致或有遗漏")
            return 1
        ways = ("Python 解析／JS KB_DOC／磁盘 references／随包 INDEX 四方一致" if pkg_checked
                else "Python 解析／JS KB_DOC／磁盘 references 三方一致（随包 INDEX 未构建，已跳过）")
        print(f"[outreach] 双登记表对账全绿：{len(rows)} 篇——{ways}")
        return 0
    try:
        rows = kb_rows()
        tracked, site = build(rows)
        validate(tracked)
    except ValueError as exc:
        print(f"  × {exc}")
        print("[outreach] 对外层校验判红：产物与登记表/口径约束不符")
        return 1
    if args.write:
        write_all(tracked, site)
        print(f"[outreach] 已写入 {len(tracked)} 份入库产物 + {len(site)} 份 site/ 产物")
        return 0
    problems = check_registry_consistency(rows)[0] + compare(tracked)
    if problems:
        for p in problems:
            print("  × " + p)
        print("[outreach] 同源复验判红：对外产物与真源/引擎输出不一致，请跑 --write 后提交")
        return 1
    print(f"[outreach] 同源复验全绿：{len(TRACKED)} 份入库产物与真源逐字节一致；判据篇目 {len(rows)} 篇；"
          f"site/ 产物 {len(site)} 份（含 INDEX 离线镜像）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
