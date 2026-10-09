#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""文档死链精确检查（v2，修正 v1 的三类误报）。

v1（临时版）按 basename 全仓匹配且不区分引用类型，产生三类误报：
  ① 各科 docs/EVAL-AUDIT.md、CASE-LIBRARY-AUDIT.md 是**学科内相对引用**，文件存在；
  ② CHANGELOG / archive/ 是**历史记录**，提到已删文件是必需的历史留痕，不是死链；
  ③ 「禁止这样命名」「描述外部生态」句中的文件名是**反例/外部物**，不是引用。
本版只检查「活跃文档 → 仓库内路径」这一类真引用，且按引用所在目录做相对解析。

2026-10-09 两处补强（都是"实跑复现后才动手"）：
  · **扫描面**：`llms.txt`（被 `.txt` 一刀切排除，永不入扫）、`disciplines/*/SKILL.md`、
    `skills/*/SKILL.md` 三类此前不在清单里——它们恰是任务 AI 的入口、路径引用最密处；
  · **判据**：原门只判"文件系统上存在"，于是本机未跟踪的 `docs/audits/*.md`
    让门**本地绿、干净 clone 红**（`ci.yml` 正是在干净 checkout 上跑 `--full`）。
    现增加"引用目标必须已被 git 追踪"的判据，报「引用目标未入库」。
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # tools/ 下为仓库根；放 tools/scratch/ 时需 parents[2]

# 活跃文档：会被新人当现状读的文档。排除 CHANGELOG（历史流水）与 archive/（归档）。
# 2026-10-08：`docs/*.md` 只扫单层，于是 docs/source-readings（57 份）、docs/audits、
# docs/references 全是盲区——恰恰是本轮新增、逐份点名脚本与数据路径最多的一批。
# 改成 `docs/**/*.md` 递归；CHANGELOG/archive 的排除走 CHANGELOG_NAMES/EXCLUDE_PARTS，
# 不是靠收窄 glob。
# 2026-10-09（扫描面补三处，都是"任务 AI 的入口、路径引用最密"的位置）：
#   · `disciplines/*/SKILL.md`——各科四段契约入口，原来不在清单里；
#   · `skills/*/SKILL.md`——仓库根的 skill 壳（与各科 SKILL.md 同族）；
#   · `llms.txt`——被 EXCLUDE_SUFFIX 里的 `.txt` 一刀切排除，**永不入扫**；
#     它恰恰是给网页端 AI 的第一入口。走 ALWAYS_SCAN_NAMES 例外，不改 .txt 的泛排除
#     （data/sources/*.txt 书源一旦入扫会刷出成千上万条假引用）。
ACTIVE_GLOBS = [
    "AGENTS.md",
    "README.md",
    "SKILL.md",
    "PROMPTS.md",
    "llms.txt",
    "docs/**/*.md",
    "disciplines/*/README.md",
    "disciplines/*/SKILL.md",
    "disciplines/*/docs/*.md",
    "skills/*/SKILL.md",
    "synthesis/README.md",
]
# 只扫文档：.py 里的 "report.md" / "narrate.md" 是运行时产物名与 path 拼接片段，
# 不是文档引用，扫它们只会刷出无意义噪声。
EXCLUDE_SUFFIX = {".py", ".json", ".js", ".css", ".html", ".txt", ".wikitext.txt"}
# 例外名单（即便后缀被排除也照扫）：只列**入口文档**，逐个点名，不放后缀/目录级例外。
ALWAYS_SCAN_NAMES = {"llms.txt"}
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
    # 「拟新建」家族（2026-10-08 补）：source-readings 的 OPT 表有一行的**路径约定**
    # 明文写着「下表『建议』列中带『新建』二字者…不属于六节验收范围」，即这些路径是
    # **待建目标**、不是"存在性声明"。按窗口判定（须贴着引用出现），与「已删/仓库外」
    # 同族；负例见 --selftest 的「裸引用必咬」一条，防止这层豁免把真死链顺走。
    r"新建|待建|拟建|下建|应建|"
    # 同族补一条（2026-10-08）：文档里点名一个**不存在**的文件多为「历史死链留痕」
    # 或「本处曾有此指」，不是存在性声明。窗口判定不变（须贴着引用）。
    # 曾一并加过「真死链」，被 --selftest 否证：任何描述性散文（「真死链示例：`x.md`」）
    # 都会把负例吞掉。**拿不准的语义词不进 NEG_CTX**。
    r"不存在|"
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
    if set(p.parts) & EXCLUDE_PARTS or p.name in CHANGELOG_NAMES:
        return False
    if p.name in ALWAYS_SCAN_NAMES:      # 入口文档例外（llms.txt 是 .txt）
        return True
    return p.suffix not in EXCLUDE_SUFFIX


# ── 引用目标必须"在库里"，不只是"在这台机器上" ────────────────────────────
# 实测（2026-10-09）：docs/audits/*.md 只在**本机**存在（未跟踪、也没进 .gitignore），
# 死链门按文件系统判活 ⇒ 本地绿、干净 clone 红（`ci.yml` 正是在干净 checkout 跑 --full）。
# "存在"用文件系统判、"在库"必须用 git 判——两者不等价时，门说的是另一台机器。
# git 可用性三态（由 tracked_index() 首查写定）。`unavailable` 时"未入库"判据**没有执行**，
# run_scan 会显式打印这条，而不是把"没判"说成"判过且没问题"。
GIT_STATE = "unknown"
# 整库索引一次取全（`git ls-files`），而不是每个引用目标起一次
# `ls-files --error-unmatch`——后者在几百条引用下把门拖成分钟级，也更容易被中断。
_TRACKED_SET: set[str] | None = None


def tracked_index() -> set[str] | None:
    """git 索引里的全部路径（posix、相对 ROOT）；git 不可用返回 None。"""
    global GIT_STATE, _TRACKED_SET
    if _TRACKED_SET is not None:
        return _TRACKED_SET
    if not (ROOT / ".git").exists():
        GIT_STATE = "unavailable"
        return None
    try:
        # -c core.quotePath=false + -z：否则非 ASCII 路径（本仓有 3 个中文名跟踪文件，
        # 如 docs/samples/财运卦.html）在默认输出里是 `"docs/samples/\350\264…"` 这种
        # 八进制转义串——真实 unicode 路径不在集合内，任何指向它们的引用都会被误判成
        # "本机存在但未入库"。-z 再顺带解决带空格/换行的路径。
        p = subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotePath=false",
                            "ls-files", "-z"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        GIT_STATE = "unavailable"
        return None
    merged = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0 or "not a git repository" in merged:
        GIT_STATE = "unavailable"
        return None
    GIT_STATE = "ok"
    _TRACKED_SET = {x.strip() for x in merged.split("\0") if x.strip()}
    return _TRACKED_SET


def _check_ignored(rel_paths: list[str]) -> set[str]:
    """一次 `git check-ignore --stdin` 判定哪些目标在 gitignore 里（返回被忽略的子集）。

    ⚠️ 用**字节**管道而不是 text=True：Windows 下 text 模式会把 `\\n` 翻译成 `\\r\\n`，
    git 收到带 `\\r` 的路径后一条都不匹配——实测"明明在 .gitignore 里却报成未忽略"。
    """
    if not rel_paths or GIT_STATE != "ok":
        return set()
    try:
        p = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--stdin"],
                           input=("\n".join(rel_paths) + "\n").encode("utf-8"),
                           capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return set()
    txt = (p.stdout or b"").decode("utf-8", "replace")
    return {line.strip() for line in txt.splitlines() if line.strip()}


def is_tracked(path: Path) -> bool | None:
    """True=已被 git 追踪；False=本机存在但未入库；None=无法判定（非 git 仓库/无 git）。"""
    idx = tracked_index()
    if idx is None:
        return None
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        return None
    if rel in idx:
        return True
    # 目录：索引里有它下面的任何文件就算在库
    prefix = rel.rstrip("/") + "/"
    return any(f.startswith(prefix) for f in idx)


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


def _judge_tracked(hit: Path, src: Path, lineno: int, ref: str,
                   bucket: list, _root: Path) -> bool:
    """存在性已通过的引用再过一道"在库"判据。返回 True＝已记入未入库桶。

    未判定（is_tracked 返回 None，例如自证树不是 git 仓库）时**不记**，
    由 run_scan 里的 GIT_STATE 披露行说明"这条判据本轮没执行"。
    """
    try:
        rel = hit.relative_to(ROOT)
    except ValueError:
        return False
    if is_tracked(hit) is False:
        bucket.append((src, lineno, ref, rel.as_posix()))
        return True
    return False


def run_scan(root: Path) -> tuple[int, list, int, list]:
    """扫一棵树并打印结果；root 通过模块级 ROOT 生效（resolve/is_active 都读它）。"""
    global ROOT, _TRACKED_SET, GIT_STATE
    ROOT = root
    _TRACKED_SET = None          # 换树必须重取 git 索引（自证树是另一座仓库）
    GIT_STATE = "unknown"
    files: list[Path] = []
    for g in ACTIVE_GLOBS:
        for p in sorted(ROOT.glob(g)):
            if p.is_file() and is_active(p):
                files.append(p)

    dead: list[tuple[Path, int, str, str]] = []
    untracked: list[tuple[Path, int, str, str]] = []
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
                    hit = next((c for c in cands if c.exists()), None)
                    if hit is not None:
                        # 存在 ≠ 在库：本机存在但 git 未追踪的目标会让门"本地绿、干净 clone 红"
                        # （实测：docs/audits/*.md 未入库时被 5 份已提交文档点名引用）。
                        _judge_tracked(hit, f, i, one, untracked, ROOT)
                        continue
                    # 「学科/裸文件名」简写：`**liuren/`build_course_cases.py**`、
                    # `ming/`build_tiaohou.py`` —— 这是文档常用的省路径写法，
                    # 按 `<科>/<文件名>` 解析（2026-10-06 实踩误报）。
                    # 注意：Path.glob 返回 generator，真值**恒为 True**——
                    # 必须 list() 之后再判，否则空结果也会被当成命中（负例自证时踩到）。
                    if "/" in one and list(ROOT.glob("disciplines/*/" + Path(one).name)):
                        hits = list(ROOT.glob("disciplines/*/" + Path(one).name))
                        _judge_tracked(hits[0], f, i, one, untracked, ROOT)
                        continue
                    # 全仓按 basename 找一次：仓库级文档写 `references/case_library.md`
                    # 这类未限定学科的相对路径时，文件实存于某学科下，不算死链，
                    # 只记「未限定学科」提示（读者需自己拼学科前缀）。
                    if "/" in one:
                        hits = list(ROOT.glob("disciplines/*/" + one))
                        if hits:
                            _judge_tracked(hits[0], f, i, one, untracked, ROOT)
                            continue
                    dead.append((f, i, one, line.strip()[:90]))

    print(f"扫描活跃文档 {len(files)} 份（已排除全部 CHANGELOG 与 archive/）"
          f"；入口文档 {'、'.join(sorted(ALWAYS_SCAN_NAMES))} 走例外入扫")
    # 扫描数为 0 一定是路径解析错了（ROOT 层级漂移），不是"仓库没文档"。
    # 假绿比报错更坏——本轮就踩过一次（tools/ 与 tools/scratch/ 深度不同）。
    if not files:
        print("! 扫描 0 份文档：ROOT 层级有误，本结果无效", file=sys.stderr)
        return 2, [], 0, []
    print(f"反例/外部物语境命中 {len(hist)} 处（不计死链）")
    if GIT_STATE == "unavailable":
        print("! git 不可用：**「引用目标未入库」这一判据本轮没有执行**"
              "（不静默当成通过；见 is_tracked 的三态返回）")
    if dead:
        print(f"\n真死链 {len(dead)} 处：")
        for f, i, ref, txt in dead:
            print(f"  × {f.relative_to(ROOT)}:{i} → {ref}")
            print(f"      {txt}")
    else:
        print("\n真死链：0 处。活跃文档内的仓库内路径引用全部可解析。")
    if untracked:
        # 分两小类报，修法不同：gitignore 内的产物（tools/scratch/…）该**改掉引用**，
        # 未跟踪又未忽略的（docs/audits/…）该**入库**。混在一起报容易被一句"加进
        # .gitignore 让它闭嘴"处理掉，而那正是本判据要防的形态。
        ignored = _check_ignored([rel for _f, _i, _r, rel in untracked])
        print(f"\n引用目标未入库 {len(untracked)} 处（本机存在但 git 未追踪——"
              f"本地绿、干净 clone 必红）：")
        for f, i, ref, rel in untracked:
            tag = "（在 gitignore 内：该改掉引用，而不是把产物入库）" if rel in ignored else \
                  "（未跟踪也未忽略：应 git add 入库，或改掉引用）"
            print(f"  × {f.relative_to(ROOT)}:{i} → {ref}（{rel} 未被 git 追踪）{tag}")
        print("      处理：把目标 `git add` 入库，或改掉引用；"
              "**不要**为了让门变绿而删掉判据。")
    rc = 1 if (dead or untracked) else 0
    return (rc,
            [(f"{f.relative_to(ROOT)}", i, ref) for f, i, ref, _ in dead],
            len(files),
            [(f"{f.relative_to(ROOT)}", i, ref, rel) for f, i, ref, rel in untracked])


def selftest() -> int:
    """负例自证（AGENTS.md §四.8）。

    2026-10-09 这一轮加了三种新能力，每一项都配一条"该抓的必须抓到"的负例：
      ① 扫描面扩到 `disciplines/*/SKILL.md`、`skills/*/SKILL.md` 与 `llms.txt`
         （`.txt` 例外）——扩面前这三类**永不入扫**，写多少死链都不报警；
      ② 新增"引用目标必须已入库"判据（本机存在但 git 未追踪 ⇒ 判红），
         并配一条"已入库不误报"的正例，防止把判据做成只会咬人的噪声；
      ③ 既有语义不动：裸引用必咬、语境豁免精准、`docs/**/*.md` 递归生效、
         `__` 双下划线假路径豁免（单下划线仍是真死链）。
    """
    import subprocess
    import tempfile

    cases = [
        # (相对路径, 文档内容, 期望该引用被判死链)
        ("docs/top_dead.md", "真死链示例（应判红）：`docs/_no_such_probe.md`\n", True),
        ("docs/sub/deep_dead.md",
         "子目录递归探针（应判红）：`docs/sub/_no_such_deep.md`\n", True),
        ("docs/planned.md",
         "拟落地项 | 新建 `docs/_planned_target.md` 登记逐字出处\n", False),
        ("docs/leftover.md",
         "- **真死链修正**：原指 `docs/_was_dead.md`，该文件不存在，已改指别处\n", False),
        ("docs/fake.md", "举例写法：`docs/__fake_example.md`\n", False),
        ("docs/ok.md", "指向实存文件：`AGENTS.md`\n", False),
        # ① 扩面探针：入口文档 / 学科 SKILL.md / skills SKILL.md 里的死链必须咬到
        ("llms.txt",
         "任务 AI 入口：详见 `docs/_from_llms_txt.md`\n", True),
        ("disciplines/ming/SKILL.md",
         "学科入口：流程见 `docs/_from_disc_skill_md.md`\n", True),
        ("skills/liuyao/SKILL.md",
         "skill 壳：口径见 `docs/_from_skill_shell.md`\n", True),
    ]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "AGENTS.md").write_text("# 探针树\n", encoding="utf-8")
        for rel, body, _ in cases:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        # ② 未入库探针的靶子：文件**存在**，但不 `git add`
        (root / "docs" / "audits").mkdir(parents=True, exist_ok=True)
        (root / "docs" / "audits" / "_present_but_untracked.md").write_text(
            "# 本机有、库里没有\n", encoding="utf-8")
        (root / "docs" / "ok_target.md").write_text("# 已入库的靶子\n", encoding="utf-8")
        (root / "docs" / "cite_untracked.md").write_text(
            "现状引用：`docs/audits/_present_but_untracked.md`\n", encoding="utf-8")
        (root / "docs" / "cite_tracked.md").write_text(
            "现状引用：`docs/ok_target.md`\n", encoding="utf-8")

        have_git = False
        try:
            r = subprocess.run(["git", "--version"], capture_output=True, timeout=20)
            have_git = r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            have_git = False
        if have_git:
            for cmd in (["init", "--quiet"], ["add", "AGENTS.md", "docs/ok_target.md",
                                              "docs/cite_tracked.md", "docs/cite_untracked.md"]):
                subprocess.run(["git", "-C", str(root), *cmd],
                               capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=60)

        _rc, dead_found, n_files, untracked_found = run_scan(root)

    bad = []
    if n_files < len(cases):
        bad.append(f"只扫到 {n_files} 份探针文档（应 ≥{len(cases)}）——递归 glob 失效")
    for rel, body, expect_dead in cases:
        ref = re.search(r"`([^`]+)`", body)
        key_ref = ref.group(1) if ref else ""
        hit = any(key_ref in r for _f, _i, r in dead_found)
        if hit != expect_dead:
            bad.append(f"{rel}：期望 {'判红' if expect_dead else '放过'}，"
                       f"实际 {'判红' if hit else '放过'}")
    # ② 未入库判据
    if not have_git:
        print("  ! git 不可用：跳过「引用目标未入库」两条探针（不当作通过）")
    else:
        got_untracked = [u for u in untracked_found if "_present_but_untracked" in u[2]]
        if not got_untracked:
            bad.append("本机存在但未入库的引用目标没有判红（untracked 判据空转）："
                       f"{untracked_found}")
        if any("ok_target" in u[2] for u in untracked_found):
            bad.append("已入库的引用目标被误报成未入库——判据会刷出噪声，等于没有")
    # 恢复指向真仓库，避免同进程后续用到探针树
    global ROOT
    ROOT = Path(__file__).resolve().parents[1]

    ok_bits = ["裸引用判红", "语境豁免精准", "子目录递归生效",
               "llms.txt/学科 SKILL.md/skills SKILL.md 入扫且咬人"]
    if have_git:
        ok_bits.append("未入库目标判红、已入库目标不误报")
    for line in (bad or ["负例全按预期：" + "、".join(ok_bits)]):
        print(f"  {'× ' if bad else '√ '}{line}")
    print("SELFTEST FAIL" if bad else "SELFTEST PASS")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="文档死链机械门：活跃文档点名的仓库内路径必须存在且已入库")
    ap.add_argument("--root", type=Path, default=ROOT,
                    help="仓库根（默认按本文件位置解析；自证/证伪可指向另一棵树）")
    ap.add_argument("--selftest", action="store_true",
                    help="负例自证：裸引用必须判红、语境豁免必须精准、递归必须生效、"
                         "未入库目标必须判红")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    rc, _dead, _n, _untracked = run_scan(args.root.resolve())
    return rc


if __name__ == "__main__":
    sys.exit(main())