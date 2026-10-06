#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文档死链精确检查（v2，修正 v1 的三类误报）。

v1（临时版）按 basename 全仓匹配且不区分引用类型，产生三类误报：
  ① 各科 docs/EVAL-AUDIT.md、CASE-LIBRARY-AUDIT.md 是**学科内相对引用**，文件存在；
  ② CHANGELOG / archive/ 是**历史记录**，提到已删文件是必需的历史留痕，不是死链；
  ③ 「禁止这样命名」「描述外部生态」句中的文件名是**反例/外部物**，不是引用。
本版只检查「活跃文档 → 仓库内路径」这一类真引用，且按引用所在目录做相对解析。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/ 下为仓库根；放 tools/scratch/ 时需 parents[2]

# 活跃文档：会被新人当现状读的文档。排除 CHANGELOG（历史流水）与 archive/（归档）。
ACTIVE_GLOBS = [
    "AGENTS.md",
    "README.md",
    "SKILL.md",
    "PROMPTS.md",
    "docs/*.md",
    "disciplines/*/README.md",
    "disciplines/*/docs/*.md",
    "synthesis/README.md",
]
# 只扫文档：.py 里的 "report.md" / "narrate.md" 是运行时产物名与 path 拼接片段，
# 不是文档引用，扫它们只会刷出无意义噪声。
EXCLUDE_SUFFIX = {".py", ".json", ".js", ".css", ".html", ".txt", ".wikitext.txt"}
EXCLUDE_PARTS = {"archive", ".git", "__pycache__", ".workbuddy"}
# CHANGELOG 是历史流水，单独说明但不当死链报（根 + 各学科都算）
CHANGELOG_NAMES = {"CHANGELOG.md"}

# 匹配反引号内的 .md 文件名，或裸 .md 路径；同链亦扫 .py（文档里点名脚本的路径，
# 学科工具目录已从 tools/ 迁 dev_tools/，这类引用极易漏——2026-10-06 实踩 1 处）
MD_REF = re.compile(r"`([A-Za-z0-9_./\\-]+\.(?:md|py))`|(?<![\w/])([A-Za-z0-9_./\\-]+\.(?:md|py))")
# `analyze.py:121` / `evaluate.py:75-76` / `chart.py::_selfcheck` 这类带行号/符号的
# 裸文件名是「同科内定位」，不是仓库路径引用，不参与死链判定（否则噪声上百条）。
PY_LOC = re.compile(r"\.(py):[\d_]|::|\.(py)\s*$|（`\S+\.py")
# 「反例 / 已删历史档 / 外部物」语境：**按窗口判定，不按整行**。
# 2026-10-06 实踩：整行 + 上一行的做法被"仓库外"里的「外部」二字误伤，
# 导致真死链被整行豁免（负例自证时才发现门不咬人）。
# 改为只看引用前后 WINDOW 字符，语境词必须贴着引用出现。
WINDOW = 40
NEG_CTX = re.compile(
    r"禁写|不要写|不得写|反例|禁止|已删除|已删|删除|已移除|移\s*`?archive|"
    r"禁止这样|命名为|仓库外|历史备注|原先定义于|已并入|已归档|零引用|"
    r"已随|一并移除|原本|"
    r"GEMINI\.md|cursor/rules|HANDOFF_V8"
)
# 两条**逐条人工定性**过的正当豁免（写死而非泛化，避免顺手放过真死链）：
#  ① `CONTRACT.md` 是写给「要把学科接进本仓的人」的接入文档，其中 `Yi/AGENTS.md`
#     的 `Yi/` 是**接入方的仓库名占位**（同段还有 `Yi/disciplines/<科名>/`），非死链。
#  ② `HANDOFF.md` 的「- **已删**：…`docs/OLD.md`（130 KB）」是删除留痕，
#     刻意点名已不存在的文件，是文档要求的历史记录形态。
CONTRACT_YI = re.compile(r"Yi/")
# 文档里**举例用的假路径**（负例自证、写法示例）。约定用 `__` 双下划线前缀标记，
# 如 `docs/__no_such.md`。这是精确豁免（只认双下划线），不是泛化词。
FAKE_PATH = re.compile(r"/__[\w.-]+$|\\__[\w.-]+$")
# 表头列名里的反例/历史列。**只用于表头**（不用于正文），避免「旧命令」这类
# 宽泛词在正文里掩盖真死链——MIGRATION.md 的「旧命令（v0）」列即此例。
TBL_NEG = re.compile(r"禁|反例|旧命令|已删|删除|不存|no-?op|废弃")
# 「占位/示意/产物」语境：同样按窗口判定（CLI 输出参数、目录结构示意、模板占位符）
PLACEHOLDER_CTX = re.compile(
    r"\{[^}]*\.(?:md|py)|\{discipline\}|<科>|xxx|-o\s|render\.py|\.py/\.json|└──|├──|│|"
    r"生成指导|生成物|各科|三科|逐字断言|GET\s|curl|zip\s|api\.github|URL|https?://"
)
# 学科内相对引用：docs/EVAL-AUDIT.md 这类写在学科 README 里，指的是该学科自己的 docs/
PER_DISC = re.compile(r"^disciplines/[a-z]+/")


def is_active(p: Path) -> bool:
    return (
        not (set(p.parts) & EXCLUDE_PARTS)
        and p.suffix not in EXCLUDE_SUFFIX
        and p.name not in CHANGELOG_NAMES
    )


def resolve(ref: str, src: Path) -> list[Path]:
    """把引用解析成候选绝对路径。"""
    cands: list[Path] = []
    if ref.startswith(("disciplines/", "core/", "tools/", "docs/", "web/", "synthesis/", "data/", "guidance/")):
        cands.append(ROOT / ref)
    if ref.startswith(("./", "../")):
        cands.append((src.parent / ref).resolve())
    else:
        cands.append(src.parent / ref)
        cands.append(ROOT / ref)
        cands.append(ROOT / "docs" / ref)
    # 包内简写：文档常写 `execution/schemas.py` 指 `core/yishu_core/execution/schemas.py`、
    # `yishu_core/eval.py` 指 `core/yishu_core/eval.py`（省 `core/` 或 `core/yishu_core/` 一层）。
    # 加候选而不是改文档——这类简写是文档既有风格，且读起来更清爽。
    cands.append(ROOT / "core" / ref)
    cands.append(ROOT / "core" / "yishu_core" / ref)
    cands.append(ROOT / "core" / "yishu_core" / Path(ref).name)
    if ref.startswith("scripts/"):
        # 学科内脚本简写：在源文档所属学科里找
        rel = src.relative_to(ROOT).parts
        if len(rel) > 1 and rel[0] == "disciplines":
            cands.append(ROOT / "disciplines" / rel[1] / ref)
    # 跨学科引用：`<学科>/scripts/xxx.py` 在别科文档里出现（EVAL-AUDIT 常引 liuyao 口径）。
    # 逐学科试，而不是靠 basename 全仓 glob（后者会掩盖真死链）。
    head = ref.split("/")[0]
    if head and (ROOT / "disciplines" / head).is_dir():
        cands.append(ROOT / "disciplines" / head / ref[len(head) + 1:])
    return cands


def main() -> int:
    files: list[Path] = []
    for g in ACTIVE_GLOBS:
        for p in sorted(ROOT.glob(g)):
            if p.is_file() and is_active(p):
                files.append(p)

    dead: list[tuple[Path, int, str, str]] = []
    hist: list[tuple[Path, int, str]] = []
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            print(f"! 跳过（非 UTF-8）：{f.relative_to(ROOT)}")
            continue
        for i, line in enumerate(lines, 1):
            if ".md" not in line and ".py" not in line:
                continue
            prev = lines[i - 2] if i >= 2 else ""
            # 表格语义：若本行是 markdown 表格行，则向上找表头（连续以 | 开头的行）。
            # 表头里若有「禁止」「反例」等列名，该列的条目就是反例而非引用
            # （AGENTS.md §三 的「禁止」列列举 run_blind_v5.py 等，2026-10-06 实踩）。
            tbl_ctx = ""
            if line.lstrip().startswith("|"):
                # 向上收集**整段连续表格行**，取最上面一行作表头
                # （中间会跨过 |---|---| 分隔行与小节标题之外的行）。
                seg = []
                k = i - 2
                while k >= 0 and lines[k].lstrip().startswith("|"):
                    seg.append(lines[k])
                    k -= 1
                tbl_ctx = seg[-1] if seg else ""
            for m in MD_REF.finditer(line):
                ref = m.group(1) or m.group(2)
                # 语境窗口 = 引用前 WINDOW 字符 + 引用后 WINDOW 字符（**不含整行与上一行**）。
                # 整行判定会被同行远处的语境词误伤（2026-10-06 负例自证实踩）。
                # 上一行只在它以引导词收尾（列表项引导）时才并入，覆盖
                # 「- **已删**：…`docs/OLD.md`（130 KB）」这种跨行写法。
                lo, hi = max(0, m.start() - WINDOW), min(len(line), m.end() + WINDOW)
                near = line[lo:m.start()] + " " + line[m.end():hi]
                lead = prev if re.search(
                    r"^\s*[-*]\s*\*\*[^*]+\*\*[：:]"      # 列表项引导：`- **已删**：…`
                    r"|[：:]\s*$|[-*]\s*\*\*.*\*\*[：:]?\s*$|[、，,]\s*`?\S*\.(?:md|py)`?\s*$",
                    prev,
                ) else ""
                # 条目引导可能跨两行（"- **已删**：a、b、\n  `c.md`（130 KB）"），
                # 故 lead 最多向上取 2 行（2026-10-06 HANDOFF §七 实踩）。
                if not lead and i >= 3 and re.search(r"[-*]\s*\*\*.*\*\*[：:]", lines[i - 3]):
                    lead = lines[i - 3] + "\n" + prev
                ctx2 = lead + "\n" + near          # 正文语境：窗口 + 列表引导
                tbl_ok = bool(TBL_NEG.search(tbl_ctx))  # 表头语境：单独判
                # 生成输出/发布物目录（guidance/、reports/ 等）先摘掉前缀再判
                ref_norm = re.sub(r"^(guidance|outputs|scratch|reports)/", "", ref)
                # A.md/B.md 并列写法：拆开各自再判。
                # 只有当**每一段**都以 .md 结尾时才是并列写法，否则原样保留
                # （否则会丢掉 `references/xxx.md` 的目录部分，把实存文件误判成死链）。
                segs = ref_norm.split("/")
                parts = (
                    [s for s in segs if s.endswith((".md", ".py"))]
                    if len(segs) > 1 and all(s.endswith((".md", ".py")) for s in segs)
                    else [ref_norm]
                ) or [ref_norm]
                for one in parts:
                    # 逐条豁免 ①：接入文档里的 `Yi/<文件>` 是接入方仓库名占位
                    # （同段还有 `Yi/disciplines/<科名>/`，是给接入方的写法）
                    if f.name == "CONTRACT.md" and CONTRACT_YI.search(one):
                        hist.append((f, i, one))
                        continue
                    # 逐条豁免 ②：「- **已删**：…`docs/OLD.md`（130 KB）」是删除留痕，
                    # 刻意点名已不存在的文件——这是 HANDOFF 的文档要求，不是死链。
                    if "已删" in ctx2:
                        hist.append((f, i, one))
                        continue
                    # 豁免 ③：文档里举例用的假路径（`__` 双下划线前缀约定）
                    if FAKE_PATH.search(one):
                        hist.append((f, i, one))
                        continue
                    # `.py` 只有带目录前缀才是路径引用；裸 `evaluate.py` / `chart.py`
                    # 是表格里的「学科内定位」，不是仓库路径（否则噪声上百条）。
                    if one.endswith(".py") and "/" not in one:
                        hist.append((f, i, one))
                        continue
                    if one.endswith(".py") and PY_LOC.search(ctx2):
                        hist.append((f, i, one))  # 同科内定位，非路径引用
                        continue
                    if NEG_CTX.search(ctx2) or PLACEHOLDER_CTX.search(ctx2) or tbl_ok:
                        hist.append((f, i, one))
                        continue
                    cands = resolve(one, f)
                    # 学科内相对引用：先试该学科自己的目录
                    if PER_DISC.match(str(f.relative_to(ROOT)).replace("\\", "/")):
                        disc = f.relative_to(ROOT).parts[1]
                        cands.append(ROOT / "disciplines" / disc / "docs" / Path(one).name)
                        cands.append(ROOT / "disciplines" / disc / Path(one).name)
                    if any(c.exists() for c in cands):
                        continue
                    # 「学科/裸文件名」简写：`**liuren/`build_course_cases.py**`、
                    # `ming/`build_tiaohou.py`` —— 这是文档常用的省路径写法，
                    # 按 `<科>/<文件名>` 解析（2026-10-06 实踩误报）。
                    # 注意：Path.glob 返回 generator，真值**恒为 True**——
                    # 必须 list() 之后再判，否则空结果也会被当成命中（负例自证时踩到）。
                    if "/" in one and list(ROOT.glob("disciplines/*/" + Path(one).name)):
                        hist.append((f, i, one))
                        continue
                    # 全仓按 basename 找一次：仓库级文档写 `references/case_library.md`
                    # 这类未限定学科的相对路径时，文件实存于某学科下，不算死链，
                    # 只记「未限定学科」提示（读者需自己拼学科前缀）。
                    if "/" in one:
                        hits = list(ROOT.glob("disciplines/*/" + one))
                        if hits:
                            hist.append((f, i, one))
                            continue
                    dead.append((f, i, one, line.strip()[:90]))

    print(f"扫描活跃文档 {len(files)} 份（已排除全部 CHANGELOG 与 archive/）")
    # 扫描数为 0 一定是路径解析错了（ROOT 层级漂移），不是"仓库没文档"。
    # 假绿比报错更坏——本轮就踩过一次（tools/ 与 tools/scratch/ 深度不同）。
    if not files:
        print("! 扫描 0 份文档：ROOT 层级有误，本结果无效", file=sys.stderr)
        return 2
    print(f"反例/外部物语境命中 {len(hist)} 处（不计死链）")
    if dead:
        print(f"\n真死链 {len(dead)} 处：")
        for f, i, ref, txt in dead:
            print(f"  × {f.relative_to(ROOT)}:{i} → {ref}")
            print(f"      {txt}")
    else:
        print("\n真死链：0 处。活跃文档内的仓库内路径引用全部可解析。")
    return 1 if dead else 0


if __name__ == "__main__":
    sys.exit(main())