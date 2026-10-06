# -*- coding: utf-8 -*-
"""根级质量门：一条命令跑完全仓库检查。

  python tools/check.py          # 快速门（默认）：版本/结构契约/内核自检/命名与断语/ming 质量门/六爻冒烟/合参自检
  python tools/check.py --full   # 全量门：再加 ming tune/holdout 案例评测、六爻黑箱回归与 pytest tests（慢）
  python tools/check.py --only version,structure   # 只跑指定检查项（逗号与空格等价）

设计口径（与各科 dev_tools/check.py 一致）：
  - --only 的可用名字只有一份真值源：各门的调用点本身（gate/gate_sub/section 就地登记），
    不另维护一张清单；给的名字有对不上的即报错并列出可用项——「选了名字却全跳过」
    是本项目最难发现的一类假绿，不允许它打印"全部通过"再退出 0；
  - 分数都是古籍案例对齐分，只用于回归审计（AGENTS.md 铁律三）；
  - 版本号唯一真值源 core/yishu_core/__init__.py::__version__，此处负责抓第二份；
  - 依赖方向单向（disciplines → core，synthesis → disciplines 的 schema），违反即缺陷；
  - 文件名不携带版本（版本走 git 与 CHANGELOG）；
  - 断语/引文进 data/*.json 或 references/*.md，代码只留算法；
  - 铁律二（案例库与预测/解读过程物理隔离）由 [1g] 机械守：静态 import 闭包 +
    审计 hook 实跑解读请求（tools/case_isolation_check.py）；
  - 同类**语义**也须单一真值源（不只是同名表）：反馈/应期的判定口径只在
    core/yishu_core/yingqi.py 一份，由 [1i] 按「身份/内容/行为」三层锁（架构评审 A2）；
  - [0b] 只报"读数锚点"（工作树 vs HEAD 的偏离），报告制不阻断——见 A11 折中版。
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import sys
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
sys.path.insert(0, str(CORE))

from yishu_core import __version__  # noqa: E402
# 学科清单唯一真值源：与 build_web.py 同源，避免 check.py 再硬编码一份 8 科名字
from yishu_core.report.request import (  # noqa: E402
    DISCIPLINES as ALL_DISCIPLINES,
    REQUEST_FIELDS,
)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.runtime import utf8_subprocess_env  # noqa: E402

# 四段契约要求的文件（新学科 ming 严格核验；liuyao 为迁移前旧实现，另立检查项）
CONTRACT_FILES = ("SKILL.md", "scripts/chart.py", "scripts/analyze.py",
                  "scripts/narrate.py", "scripts/render.py",
                  "data/verdicts.json", "dev_tools/check.py", "dev_tools/golden.py")
# 四段契约里"查表直录类学科"豁免的条目：这类学科断语直接录自古籍课表
# （lingqi 的 124 课），不设 data/verdicts.json、也不分案例集，见 docs/CONTRACT.md §四。
CONTRACT_EXEMPT_FILES = ("data/verdicts.json",)
TABLE_LOOKUP_DISCIPLINES = ("lingqi",)

# 目录级预算（架构评审 A3）：单文件看门狗对「几十个文件合计上万行」的分布式巨石无感。
# 超过基础预算的科必须在 DECLARED_HEAVY 里显式申报上限，否则失败——
# 「重科」是显式声明，不是默认漂移。
SCRIPTS_BUDGET_BASE = 6000
DECLARED_HEAVY = {"liuyao": 22000}

# 快速冒烟门（跑 golden，成本高）只跑这两科；八科的"静态结构门"（文件齐全）由
# check_structure 用 request.DISCIPLINES 全覆盖，新科接入时不必改这里。
SMOKE_DISCIPLINES = ("ming", "ziwei")

# render 段内容指纹基线（架构评审 A6）：render 是四段里唯一无内容指纹的一段。
# 只锁 Markdown 逐字节（同源验收口径即「MD 逐字节一致」；HTML 页头 runtime 标签是有意差异）。
RENDER_GOLDEN = ROOT / "data" / "golden" / "render_digest.json"

# 内核唯一真值表名：学科内出现同名赋值即视为复制（AGENTS.md 内核唯一真值源）
# 含历史别名/拆分名（STEMS/NAYIN_TABLE/XUN_KONG/SAN_HE…），否则同义表仍会漏检。
CORE_TABLE_ASSIGN = re.compile(
    r"^\s*(EARTHLY_BRANCHES|HEAVENLY_STEMS|BAGUA_LINES|HEXAGRAM_TRIGRAMS|"
    r"EIGHT_PALACES|TRIGRAM_ELEMENTS|XIAN_TIAN_TRIGRAM_NUMBERS|NUMBER_TO_TRIGRAM|"
    r"SHENG_CYCLE|KE_CYCLE|TWELVE_CHANGES|NAJIA|LIU_QIN|LIU_SHEN|"
    r"ER_SHISI_XIU|JIAN_CHU|HUANG_HEI_DAO|"
    r"STEMS|BRANCHES|NAYIN|NAYIN_TABLE|NAYIN_COUPLETS|NAYIN_TO_ELEMENT|"
    r"XUN_KONG|SAN_HE|SAN_HE_GROUPS|THREE_PUNISHMENTS|THREE_PUNISHMENTS_CYCLIC|"
    r"THREE_PUNISHMENTS_MUTUAL|SELF_PUNISHMENTS|TWELVE_GROWTH|TWELVE_GROWTH_TABLES|"
    r"TWELVE_GROWTH_STAGES|SIX_RELATIONS|LIUQIN_NAMES)\s*=\s*[\[\{]", re.M)

# 学科间 import（违反 disciplines 禁止互相 import 的契约）
CROSS_DISC_IMPORT = re.compile(
    r"^\s*(from|import)\s+(liuyao|ming|ziwei|meihua|xiaoliuren|zeji|liuren|lingqi)\b", re.M)

# 报告禁用断言词（铁律三）：只拦"肯定式"断言——「命中率/准确率」后紧跟数字，或「断事如神」。
# 不拦"不宣称现实预测命中率"这类否定式免责句（其后不是数字）。
BANNED_CLAIM = re.compile(r"(?:命中率|准确率)\s*[:：]?\s*\d|断事如神")

# 报告契约·八科必达字段（analyze.chart_summary 的键 → 其值必须出现在 narrate 正文）。
# 取「实测确认会渲染」的结构化键，专抓「算出来了但报告没呈现」（AGENTS.md §四.6 报告层同步）。
REPORT_REQUIRED = {
    "liuyao": ("用神", "旺衰"),
    "ming": ("强弱", "格局", "胎元"),
    "ziwei": ("命宫主星", "格局", "五行局"),
    "meihua": ("体用规则",),
    "xiaoliuren": ("落宫",),
    "zeji": ("日值神", "值宿"),
    "liuren": ("日干支", "月将"),
    "lingqi": ("课名", "卦宫"),
}

# 文件名版本号标记（AGENTS.md §三：名字不携带版本；版本走 git 与 CHANGELOG）
# 排除 archive/ 目录和 .git/ 目录，匹配 _v2 / _V3 / _v10 等
VERSIONED_FILENAME = re.compile(
    r"_v\d+(?:\.[A-Za-z0-9_]+)?\.(?:py|md|json|txt|yaml|yml|toml)$", re.I)

# 中文断语字面量检测（AGENTS.md §三：断语/引文进 data/*.json，代码只留算法）
# 检测 .py 文件中 dict/List 值含连续 8+ 中文字符的字符串
CHINESE_VERDICT_LITERAL = re.compile(r"[\u4e00-\u9fff]{8,}")

# 干支序列唯一字面量（天干 / 地支的完整 10/12 位串）
GANZHI_SEQ_LITERAL = re.compile(r'["\'](?:甲乙丙丁戊己庚辛壬癸|子丑寅卯辰巳午未申酉戌亥)["\']')


def _run_py(cmd: list[str], *, label: str, cwd: Path = ROOT,
            exe: str | None = None) -> tuple[int, str]:
    """子进程跑一个质量门；返回 (退出码, 输出)。exe 缺省用 sys.executable。"""
    try:
        p = subprocess.run([exe or sys.executable, *cmd], cwd=cwd,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1200,
                           env=utf8_subprocess_env())
    except subprocess.TimeoutExpired:
        return 1, f"{label}: 超时（>1200s）"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def _resolve_pytest_exe() -> list[str]:
    """返回可跑 pytest 的 python 候选（按优先级）。
    优先当前解释器；若其未装 pytest，则回退到同运行时目录下的标准 venv
    （binary_context：脚本依赖应装进 <runtime>/envs/default）。如此即便用裸受管
    Python 跑 check.py，单测门也能自动找到 venv 里的 pytest，避免静默失效。
    """
    cands = [sys.executable]
    # <binaries>/python/versions/X.Y.Z/python.exe → <binaries>/python/envs/default/{Scripts/python.exe,bin/python}
    # 系统级 Python（如 C:\Python314\python.exe）祖先层级不够，parents[2] 会 IndexError——
    # 层级不足时退到最上层：venv 回退候选找不到而已，不影响当前解释器本身。
    _resolved = Path(sys.executable).resolve()
    _anc = list(_resolved.parents)
    py_root = _anc[2] if len(_anc) >= 3 else _anc[-1]
    for rel in ("envs/default/Scripts/python.exe", "envs/default/bin/python"):
        venv_py = py_root / rel
        if venv_py.is_file() and str(venv_py) != str(_resolved):
            cands.append(str(venv_py))
            break
    return cands


def check_version() -> list[str]:
    """版本唯一真值源：除 core/yishu_core/__init__.py 外，任何 .py 不得写死版本。"""
    fails = []
    pat = re.compile(r'(__version__\s*=\s*["\']|version\s*=\s*["\']\d)')
    for p in ROOT.rglob("*.py"):
        if any(seg in p.parts for seg in ("__pycache__", "scratch", ".worktrees",
                                          "site", "_site", "archive", "egg-info")):
            continue
        if p == CORE / "yishu_core" / "__init__.py":
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if pat.search(line):
                fails.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")
    return fails


def check_filenames() -> list[str]:
    """文件名规范（AGENTS.md §三）：禁止携带版本号；data/cases 外的 .json 进 cases/。"""
    fails = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        parts = rel.parts
        if any(seg in ("archive", ".git", "__pycache__", ".worktrees",
                       "egg-info", "site", "_site") for seg in parts):
            continue
        # 版本号文件名
        if VERSIONED_FILENAME.search(p.name):
            fails.append(f"{rel}: 文件名携带版本号（版本走 git 与 CHANGELOG）")
    return fails


def check_capability_matrix() -> list[str]:
    """能力矩阵锁（SYS-REVIEW #3）：llms.txt 的权威矩阵与 build_web 清单一致。"""
    import importlib.util
    fails: list[str] = []
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location("build_web", ROOT / "tools" / "build_web.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    web_ids = [m["id"] for m in mod.DISCIPLINE_META]
    all_ids = ["liuyao", "ming", "ziwei", "meihua", "xiaoliuren", "zeji", "liuren", "lingqi"]
    unknown = [d for d in web_ids if d not in all_ids]
    if unknown:
        fails.append(f"build_web 出现未知学科 id：{unknown}")
    for d in all_ids:
        row = f"{d} | ✓ | ✓ | ✓" if d in web_ids else f"{d} | ✓ | ✗ | ✓"
        if row not in llms:
            fails.append(f"llms.txt 能力矩阵缺行或缺通道标注：{row}")
    return fails


def check_verdict_literals() -> list[str]:
    """断语字面量检测（AGENTS.md §三）：.py 中不应堆砌中文断语表，应外置到 data/*.json。

    本检查仅针对明确的数据结构——Python 字典中连续多条「条件/含义/建议」三元组
    或多条 verdict reason 映射——不计 docstring、argparse help、异常消息、注释。

    **它是粗筛，不是判据。** 两个方向各自有漏：
      · 假阴性：硬编码在 .py 里的断语只要不写成"连续字典值"就抓不到
        （阶段4 就靠这个漏掉过小六壬 `事势偏顺，宫义为吉` 整句）；
      · 假阳性：把 docstring / 模块说明批量外置只会让代码读不懂。
    **主判据是 `tools/verdict_audit.py --strict`**（[1c] 门）：它跑真实报告，
    反查"用户到底读到了哪些没进 data/*.json 的中文结论句"，取证而不猜代码长相。
    在主判据的采样集之外，再扫一遍没被报告覆盖的分支。
    """
    fails = []
    KNOWN_DATA_DRIVERS = {"classical_tables"}  # 已走 json.load
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "__pycache__" in p.parts or "scratch" in p.parts:
            continue
        stem = p.stem
        if stem in KNOWN_DATA_DRIVERS:
            continue
        if "/tests/" in str(p.relative_to(ROOT)) or "\\tests\\" in str(p.relative_to(ROOT)):
            continue
        # 含 json.load(data 路径) 且仅做引用的模块也跳过（从 data 加载而非硬编码）
        txt = p.read_text(encoding="utf-8", errors="ignore")
        if re.search(r'json\.load\s*\(\s*open\s*\(.*(?:\.\./)?data/"', txt) or \
           re.search(r'json\.load\s*\(.*_cp\b', txt):
            continue

        lines = txt.splitlines()
        in_docstring = False
        docstring_marker = ""
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 追踪 docstring 块（跳过的内容）
            if not in_docstring:
                for m in ('"""', "'''"):
                    if stripped.count(m) % 2 == 1:
                        in_docstring = True
                        docstring_marker = m
                        break
                if in_docstring:
                    continue
            else:
                if docstring_marker in stripped:
                    in_docstring = False
                    continue
                continue  # 在 docstring 内部，跳过

            # 跳过 argparse help 字符串、错误消息行
            if 'help="' in stripped or "help='" in stripped:
                continue
            if stripped.startswith(("raise ", "return {")):
                continue
            if '"error"' in stripped or "'error'" in stripped:
                continue
            # 跳过纯注释行
            if stripped.startswith("#"):
                continue

            # 检测：字典值是多层嵌套 dict 且包含 verdict 关键字
            # 模式：SOME_NAME = { "key": { "condition"|"meaning"|"advice"|"reason"|"note": "中文..." } }
            if re.search(r'=\s*\{', stripped) and \
               any(kw in stripped for kw in ('"condition"', '"meaning"', '"advice"',
                                              '"reason"', '"note"', '"text"', '"description"')):
                # 检查本行或后续行是否有 verdict-text 模式的中文
                context_block = "\n".join(lines[i-1:min(i+10, len(lines))])
                cn_literals = CHINESE_VERDICT_LITERAL.findall(context_block)
                if len(cn_literals) >= 3:  # 3条以上才视为"堆砌"
                    fails.append(f"{p.relative_to(ROOT)}:{i}: "
                                 f"疑似字典式断语表（{len(cn_literals)} 条中文字段）→ 外置到 data/*.json")
                    break  # 每文件只报首处
    return fails


def check_deeplink_keys() -> list[str]:
    """深链短键锁（架构评审 A5）：web/web.js 的 DEEPLINK_KEYS 值必须是请求字段白名单成员。

    短键表只存在于 JS 侧、不受输入协议指纹覆盖（[1f] 只锁 normalize_request 的规范键）。
    短键一旦指向没有任何 argv 会读的死字段，本地与网页端行为会不一致而零报警——
    这里把它锁死在唯一真值源 `request.REQUEST_FIELDS` 上。
    """
    js = (ROOT / "web" / "web.js").read_text(encoding="utf-8", errors="ignore")
    block = re.search(r"DEEPLINK_KEYS\s*=\s*\{(.*?)\}", js, re.S)
    if not block:
        return ["web/web.js 找不到 DEEPLINK_KEYS 定义（深链协议被改写？）"]
    values = re.findall(r":\s*'([^']+)'", block.group(1))
    unknown = sorted(set(values) - set(REQUEST_FIELDS))
    if unknown:
        return [f"web/web.js DEEPLINK_KEYS 指向未知请求字段：{unknown}"
                f"（白名单唯一真值源 request.REQUEST_FIELDS）"]
    return []


def check_structure() -> list[str]:
    """学科目录契约：八科四段文件齐全；依赖方向单向。

    清单取 `request.DISCIPLINES`（唯一真值源），扩展新科时自动覆盖——此前
    `NEW_DISCIPLINES` 只放 ming/ziwei，其余 6 科靠各学科自己的 dev_tools/check.py，
    根门对新科是敞的。
    查表直录类学科（`TABLE_LOOKUP_DISCIPLINES`，如 lingqi 的 124 课本就直录古籍）
    豁免 `CONTRACT_EXEMPT_FILES`，见 `docs/CONTRACT.md` §四。
    """
    fails = []
    for disc in ALL_DISCIPLINES:
        d = ROOT / "disciplines" / disc
        exempt = TABLE_LOOKUP_DISCIPLINES
        files = [f for f in CONTRACT_FILES
                 if not (disc in exempt and f in CONTRACT_EXEMPT_FILES)]
        for f in files:
            if not (d / f).exists():
                fails.append(f"{disc}/ 缺 {f}（CONTRACT.md 四段契约）")
        # 案例分层：案例与评测产物一律放 <科>/data/cases/（散落别处由 check_filenames 挡）。
        # 这里不把"目录存在"当硬条件——空目录 git 带不走，拿它当"分层守住了"的证据只会
        # 在新克隆上假红（本机空目录过门，克隆后必红）。
        # 没有案例库的科在这里明说，不静默放过。
        cases = d / "data" / "cases"
        if disc not in exempt and not (cases.is_dir() and any(cases.glob("*.json"))):
            print(f"  · {disc} 尚无案例库（data/cases 下没有 *.json）")
    # 学科互相 import（8 科全扫：此前只扫 liuyao/ming，另 6 科的违规 import 是敞的）
    for disc in ALL_DISCIPLINES:
        scripts = ROOT / "disciplines" / disc / "scripts"
        if not scripts.is_dir():
            continue
        for p in scripts.rglob("*.py"):
            if "scratch" in p.parts:
                continue
            for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                m = CROSS_DISC_IMPORT.match(line)
                if m and m.group(2) != disc:
                    fails.append(f"{p.relative_to(ROOT)}:{i}: 学科间 import {m.group(2)}")
    # 巨石看门狗：单文件过长视为架构债（M1b；classical_rules 已按域拆分）
    max_lines = 2200
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts:
            continue
        n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
        if n > max_lines:
            fails.append(f"{p.relative_to(ROOT)} 过长（{n} 行 > {max_lines}）——按域拆分，勿再堆巨石")
    # 目录级预算：scripts/ 合计行数（分布式巨石；超过基础预算须在 DECLARED_HEAVY 显式申报）
    for disc in ALL_DISCIPLINES:
        sp = ROOT / "disciplines" / disc / "scripts"
        if not sp.is_dir():
            continue
        total = sum(sum(1 for _ in p.open(encoding="utf-8", errors="ignore"))
                    for p in sp.rglob("*.py")
                    if "scratch" not in p.parts and "__pycache__" not in p.parts)
        budget = DECLARED_HEAVY.get(disc, SCRIPTS_BUDGET_BASE)
        if total > budget:
            extra = "" if disc in DECLARED_HEAVY else \
                "（未申报重科：如需超预算，须在 check.py 的 DECLARED_HEAVY 显式申报上限）"
            fails.append(f"disciplines/{disc}/scripts 合计 {total} 行 > 预算 {budget}{extra}")
        else:
            print(f"  · {disc}/scripts 合计 {total} 行（预算 {budget}）")
    return fails


def check_modules_importable() -> list[str]:
    """八科每个 `scripts/*.py` 都能独立 import 成功。

    背景（本门的存在理由）：2026-10-02 修 `trigram_symbolism.py` 时把
    `import json` / `from pathlib import Path` 换成了别名导入，模块一进 import
    就 NameError，被上层 try/except 吞成"空类象表"，288 条六爻排盘静默漂移
    （偏弱/中和翻转），而当时根门里根本没有跑六爻 golden，谁也没报警。
    纯静态的门（结构/命名/内核表）抓不到这种"import 期炸、运行期装死"，
    只能真的 import 一遍。
    """
    fails = []
    env = utf8_subprocess_env()
    for disc in ALL_DISCIPLINES:
        sp = ROOT / "disciplines" / disc / "scripts"
        if not sp.is_dir():
            continue
        for f in sorted(sp.glob("*.py")):
            code, out = _run_py(
                ["-c", f"import sys; sys.path[:0] = [{str(sp)!r}, {str(CORE)!r}];"
                       f" import importlib; importlib.import_module({f.stem!r})"],
                label=f"{disc}/{f.name}", cwd=sp)
            if code != 0:
                tail = [l for l in out.strip().splitlines() if l.strip()]
                fails.append(f"{disc}/scripts/{f.name} 独立导入失败："
                             f"{tail[-1][:120] if tail else 'unknown'}")
    return fails


def check_core_tables() -> list[str]:
    """内核表唯一：学科内不得重新定义 core 已有规则表（同名 + 改名副本两层检测）。"""
    fails: list[str] = []
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if CORE_TABLE_ASSIGN.match(line):
                name = line.strip().split("=", 1)[0].strip()
                fails.append(f"{p.relative_to(ROOT)}:{i}: 复制内核表 {name}"
                             f"（唯一真值源在 core）")
    fails.extend(check_core_table_renames())
    fails.extend(check_core_tables_in_scope())
    fails.extend(check_core_string_tables())
    return fails


def _canonical_literal(node: ast.AST) -> str | None:
    """dict/list 字面量 → 归一化指纹（dict 键排序），不可字面求值则返回 None。

    空 dict/list 不参与指纹比对：`{}`/`[]` 常是"运行时从 core 派生填充"的合法形态
    （如 chain_tables 用 core HE_PAIRS 现算六合表），并非复制。
    """
    try:
        val = ast.literal_eval(node)
    except Exception:
        return None
    if not val:  # 空 dict / 空 list
        return None
    try:
        if isinstance(val, dict):
            return json.dumps(val, ensure_ascii=False, sort_keys=True)
        if isinstance(val, list):
            return json.dumps(val, ensure_ascii=False)
    except (TypeError, ValueError):
        return None
    return None


def _module_table_fingerprints(py_file: Path) -> dict[str, list[str]]:
    """收集一个 .py 模块级 dict/list 字面量赋值：指纹 → [变量名]。"""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return {}
    out: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value if isinstance(node, ast.Assign) else node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not isinstance(value, (ast.Dict, ast.List)):
                continue
            fp = _canonical_literal(value)
            if not fp:
                continue
            for t in targets:
                if isinstance(t, ast.Name):
                    out.setdefault(fp, []).append(t.id)
    return out


def _all_scope_literals(py_file: Path) -> dict[str, dict[str, list[str]]]:
    """全作用域 dict/list 字面量赋值：指纹 → {作用域名: [变量名]}（含函数内、任意嵌套）。

    `_module_table_fingerprints` 只看模块级，看不见函数内的 dict 赋值
    （如 `def f(): sheng_wo = {"木": "水", ...}`）。这类副本与模块级副本同样危险：
    同份数据的第二份，改 core 漏改即口径分叉。故单独开一路全作用域收集。
    """
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return {}
    out: dict[str, dict[str, list[str]]] = {}

    def walk(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, getattr(child, "name", "<scope>"))
                continue
            if isinstance(child, (ast.Assign, ast.AnnAssign)):
                value = child.value
                if isinstance(value, (ast.Dict, ast.List)):
                    fp = _canonical_literal(value)
                    if fp:
                        targets = (child.targets if isinstance(child, ast.Assign)
                                   else [child.target])
                        for t in targets:
                            if isinstance(t, ast.Name):
                                out.setdefault(fp, {}).setdefault(scope, []).append(t.id)
            walk(child, scope)

    walk(tree, "<module>")
    return out


def _core_module_values(py_file: Path) -> dict[str, str]:
    """import 一个 core 模块，收集其模块级 dict/list 变量的运行值指纹。

    目的见 `check_core_tables_in_scope`：推导式派生的表（SHENG_WO/KE_WO 等）不是
    ast 字面量，只靠静态扫描会漏，故实际 import 一次取运行值补进指纹库。
    core 仅依赖 stdlib，import 无副作用。
    """
    if str(ROOT / "core") not in sys.path:
        sys.path.insert(0, str(ROOT / "core"))
    try:
        mod = importlib.import_module(f"yishu_core.{py_file.stem}")
    except Exception:
        return {}
    out: dict[str, str] = {}
    for name, val in vars(mod).items():
        if name.startswith("_"):
            continue
        try:
            if isinstance(val, dict) and val:
                out[name] = json.dumps(val, ensure_ascii=False, sort_keys=True)
            elif isinstance(val, list) and val:
                out[name] = json.dumps(val, ensure_ascii=False)
        except (TypeError, ValueError):
            continue
    return out


def check_core_tables_in_scope() -> list[str]:
    """函数级 / 嵌套作用域的内核表副本检测（补 `check_core_table_renames` 盲区）。

    背景：模块级指纹门对 `def f(): sheng_wo = {...}` 这类**函数内**字面量 100% 失明，
    六爻 engine_chart.py 的五行生克 dict 即因此长期挂着（AGENTS.md §二 真值源清单
    里"五行生克"赫然在列）。本函数用 ast 遍历全部作用域补齐。
    """
    core_fps: dict[str, list[str]] = {}
    for p in sorted((ROOT / "core" / "yishu_core").glob("*.py")):
        for fp, scopes in _all_scope_literals(p).items():
            for names in scopes.values():
                core_fps.setdefault(fp, []).extend(
                    f"yishu_core.{p.stem}.{n}" for n in names)
        # 补盲：core 里由推导式派生的表（如 `SHENG_WO = {v: k for k, v in SHENG_CYCLE...}`）
        # 不是 dict 字面量，字面量指纹库收不到它，学科层对其反向复制就漏检。
        # core 只依赖 stdlib，import 安全；取其模块级 dict/list 变量的运行值入指纹库。
        for name, val in _core_module_values(p).items():
            core_fps.setdefault(val, []).append(f"yishu_core.{p.stem}.{name}")
    if not core_fps:
        return []
    fails: list[str] = []
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT)
        for fp, scopes in _all_scope_literals(p).items():
            if fp not in core_fps:
                continue  # core 里没有这份内容 → 不是内核表的副本，不算违规
            src = "、".join(core_fps[fp])
            for scope, names in scopes.items():
                if scope == "<module>":
                    continue  # 模块级由 check_core_table_renames 负责，避免重复报
                fails.append(f"{rel}: 作用域 {scope}() 内复制内核表 {'、'.join(names)}"
                             f"（内容与 core {src} 逐字节相同，唯一真值源在 core）")
    return fails


def check_core_string_tables() -> list[str]:
    """干支序列字符串字面量唯一性（core/yishu_core/ganzhi_calendar.py 为唯一真值源）。

    上两条门都只比对 dict/list 字面量：裸字符串 `stems = "甲乙丙丁戊己庚辛壬癸"`
    既不匹配 `CORE_TABLE_ASSIGN` 正则，也不是可指纹的 dict —— 两层门同时放行。
    且同一函数里常出现"一半用 core 一半手写串"（如 meihua/chart.py:327 手写 stems、
    :328 用 core EARTHLY_BRANCHES），是最容易漏改半截的形态。
    """
    fails: list[str] = []
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT)
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            m = GANZHI_SEQ_LITERAL.search(line)
            if m:
                fails.append(f"{rel}:{i}: 复制内核干支序列「{m.group(0).strip(chr(34)+chr(39))}」"
                             f"（唯一真值源在 core/yishu_core/ganzhi_calendar.py）")
    return fails


def check_core_table_renames() -> list[str]:
    """改名副本检测：学科层出现与 core 真值表内容逐字节相同的模块级字面量即视为复制。

    背景：历史事故形态之一是把 core 表换名复制（如 XUN_KONG → EMPTY_DEATH），
    同名检测（CORE_TABLE_ASSIGN）对此失明，故增加内容指纹比对。
    """
    core_fps: dict[str, list[str]] = {}
    for p in sorted((ROOT / "core" / "yishu_core").glob("*.py")):
        for fp, names in _module_table_fingerprints(p).items():
            core_fps.setdefault(fp, []).extend(f"yishu_core.{p.stem}.{n}" for n in names)
    if not core_fps:
        return []
    fails: list[str] = []
    for p in (ROOT / "disciplines").rglob("*.py"):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        rel = p.relative_to(ROOT)
        for fp, names in _module_table_fingerprints(p).items():
            if fp in core_fps:
                src = "、".join(core_fps[fp])
                fails.append(f"{rel}: 改名复制内核表 {', '.join(names)}"
                             f"（内容与 core {src} 逐字节相同，唯一真值源在 core）")
    return fails


def _tail(out: str, n: int = 3) -> str:
    return "\n".join(out.strip().splitlines()[-n:])


def check_feedback_caliber() -> list[str]:
    """反馈口径单一真值源（架构评审 A2）。

    同一语义「应期回填 → 命中判定」原有两个并行实现：合参层 `synthesis/outcome_eval.py`
    （名次制）与六爻 `disciplines/liuyao/dev_tools/feedback_store.py`（容差窗）。
    两种口径是**真实差别**（一个问候选排序、一个问日期接近），不允许合并；
    但两处**各写一份常量/支关系表**是缺陷——六爻侧本地支合表还多出「丑午」「未申」
    两条错项（既非六合亦非六冲），会造成虚假宽松命中。

    现两处只准调用 `yishu_core.yingqi`，本门三层锁：
      ① 身份：两处取到的评分表/窗口常量必须是内核里那一个对象（不是同名副本）；
      ② 内容：两处源文件不得再出现这些常量或支关系表的字面量赋值；
      ③ 行为：同一份假例经内核判定函数跑出表驱动期望值（含六合 / 六害 / 支同 / 容差边界），
         并断言名次制打分确实走通（得分取自内核表）。
    """
    fails: list[str] = []
    for p in (ROOT / "synthesis", ROOT / "disciplines" / "liuyao" / "dev_tools"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    try:
        import importlib as _il
        Y = _il.import_module("yishu_core.yingqi")
        OE = _il.import_module("outcome_eval")
        FS = _il.import_module("feedback_store")
    except Exception as exc:  # noqa: BLE001 —— 口径模块不可导入本身就是失败
        return [f"反馈口径模块不可导入：{type(exc).__name__}: {exc}"]

    # ① 身份：同一对象，不是同名副本
    if OE.YQ_SCORE is not Y.RANK_SCORE:
        fails.append("synthesis/outcome_eval.py 的 YQ_SCORE 不是 yishu_core.yingqi.RANK_SCORE"
                     "（应期得分表必须同源，不得各写一份）")
    for name in ("LOOSE_WINDOW_DAYS", "STRICT_WINDOW_DAYS", "BRANCH_WINDOW_DAYS"):
        if getattr(FS, name, None) != getattr(Y, name, None):
            fails.append(f"feedback_store.{name} 与 yishu_core.yingqi.{name} 不同值")

    # ② 内容：源文件里不得再出现常量/支关系表的字面量赋值
    dup = re.compile(r"^\s*(LOOSE_WINDOW_DAYS|STRICT_WINDOW_DAYS|BRANCH_WINDOW_DAYS|"
                     r"YQ_SCORE|RANK_SCORE|_HE|_CHONG|DAY_CHARS|_ANCHOR)\s*[:=]")
    for rel in ("synthesis/outcome_eval.py",
                "disciplines/liuyao/dev_tools/feedback_store.py"):
        for i, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            if dup.match(line):
                fails.append(f"{rel}:{i}: 本地又在写应期口径常量——唯一真值源在 core/yishu_core/yingqi.py")

    # ③ 行为：表驱动边界（真算，非恒真断言）
    from datetime import date, timedelta

    from yishu_core.symbols import HARM_PAIRS, HE_PAIRS
    he_set = {frozenset(p) for p in HE_PAIRS}
    harm_set = {frozenset(p) for p in HARM_PAIRS}
    base = date(2026, 10, 1)

    def _day(delta: int) -> str:
        return (base + timedelta(days=delta)).isoformat()

    def _find(pred) -> int | None:
        """在 8..21 天里找一个满足 pred 的偏移（避开 ±7 纯日期容差，才验得到支窗口）。"""
        return next((d for d in range(8, 22)
                     if pred(Y.branch_of(_day(0)), Y.branch_of(_day(d)))), None)

    strict = Y.judge_window([_day(0)], _day(1))
    if not (strict["hit_strict"] and strict["hit_loose"]):
        fails.append(f"容差窗：±1 天应为严格命中，实为 {strict}")
    tol = Y.judge_window([_day(0)], _day(7))
    if tol["hit_strict"] or not tol["hit_loose"]:
        fails.append(f"容差窗：±7 天应为宽松命中、非严格，实为 {tol}")
    he_d = _find(lambda a, b: frozenset((a, b)) in he_set)
    if he_d is None:
        fails.append("容差窗：8..21 天内找不到与基准日六合的日子（内核六合表疑有误）")
    elif not Y.judge_window([_day(0)], _day(he_d))["hit_loose"]:
        fails.append(f"容差窗：{he_d} 天前为六合，应记宽松命中却未记")
    harm_d = _find(lambda a, b: frozenset((a, b)) in harm_set)
    if harm_d is None:
        fails.append("容差窗：8..21 天内找不到与基准日相害的日子（内核六害表疑有误）")
    elif Y.judge_window([_day(0)], _day(harm_d))["hit_loose"]:
        fails.append(f"容差窗：{harm_d} 天前为六害（非六合六冲），不得记命中——"
                     "此处正是被删掉的错项（丑午/未申）")
    # 旧错项回归（点名）：丑午、未申 既非六合亦非六冲，原六爻侧本地支合表错收这两对
    for a, b in (("丑", "午"), ("未", "申")):
        if Y.branches_relate(a, b):
            fails.append(f"容差窗：{a}{b} 非六合非六冲，不得算命中——旧错项回归")
    if any(v for v in Y.judge_window([_day(0)], _day(30)).values()):
        fails.append("容差窗：超出 21 天支窗口不得记命中")

    # 名次制仍走通，且得分取自内核表
    res = OE.eval_outcomes([{
        "event_id": "FBCHK", "discipline": "liuyao", "direction": "吉", "asked": "口径门假例",
        "yingqi_offered": [{"date": _day(0), "rule": "r0"}, {"date": _day(30), "rule": "r1"}],
        "outcome": {"recorded": "假例", "occurred_at": _day(0), "judged": "应验"}}])
    yq = (res.get("cases") or [{}])[0].get("应期") or {}
    if not (yq.get("命中") and yq.get("名次") == 1
            and yq.get("得分") == Y.RANK_SCORE[1]):
        fails.append(f"名次制：首位候选命中应得第 1 名与内核全分，实为 {yq}")
    return fails


# ── 读数锚点：工作树领先 HEAD 时，别让"以 revision 为锚"的取证悄悄说谎 ──
# 背景（2026-10-01 时点评审 A11，件已删、结论转登记 TECH-DEBT §2.6）：当时实测工作树
# 领先 HEAD 132 个文件，而 archify 的 repository-evidence 门按 **pin 的 revision** 校验
# 文件与行号——于是"以 HEAD 之名断言工作树事实"不诚实，评审因此放弃了 pin revision。
# 本条是折中版：不解决取证失效，只让它**可见**（报告制，不阻断——开发期漂移是常态）。
DRIFT_THRESHOLD = 50


def worktree_drift() -> tuple[int, str] | None:
    """(相对 HEAD 的未提交变更数, HEAD 短 sha)；非 git 仓库 / git 不可用 → None。"""
    def _git(*argv: str) -> str | None:
        try:
            p = subprocess.run(["git", *argv], cwd=ROOT, capture_output=True,
                               text=True, encoding="utf-8", errors="replace", timeout=30)
        except (OSError, subprocess.SubprocessError):
            return None
        return p.stdout if p.returncode == 0 else None

    status = _git("status", "--porcelain")
    if status is None:
        return None
    n = len([line for line in status.splitlines() if line.strip()])
    sha = (_git("rev-parse", "--short", "HEAD") or "").strip()
    return n, sha


def print_worktree_drift() -> None:
    """[0b] 读数锚点：把"工作树领先 HEAD"从人眼发现变成门输出里的显式读数。"""
    info = worktree_drift()
    if info is None:
        print("  · 非 git 仓库或 git 不可用，跳过读数锚点")
        return
    n, sha = info
    anchor = f"HEAD {sha}" if sha else "HEAD（取不到 sha）"
    if n == 0:
        print(f"  √ 工作树相对 {anchor} 无未提交变更，下述读数可锚定到该 revision")
        return
    if n <= DRIFT_THRESHOLD:
        print(f"  · 工作树相对 {anchor} 有 {n} 处未提交变更（阈值 {DRIFT_THRESHOLD}）："
              f"下述读数取自工作树")
        return
    print(f"  ！工作树相对 {anchor} 偏离 {n} 处 > 阈值 {DRIFT_THRESHOLD}"
          f"（报告制，不阻断；这不是失败项）")
    print("      · 声明：下述所有门的读数一律取自**工作树**，不等于任何已提交 revision。")
    print("      · 以 revision 为锚的取证（如 archify repository-evidence 的文件/行号校验）")
    print("        在此状态下会失败或说谎——引用行号前先 commit，或显式声明描述的是工作树。")


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="易·仓库级质量门")
    ap.add_argument("--only", nargs="*", default=None,
                    help="限定检查项：逗号或空格分隔皆可（--only version,structure 与 "
                         "--only version structure 等价）；省略即跑全部门。"
                         "给的名字有对不上的，以退出码 2 报错并列出可用检查项。")
    ap.add_argument("--full", action="store_true",
                    help="全量：三科案例评测（tune/holdout）+ 六爻黑箱回归 + "
                         "网页/本地同源验收 + pytest tests（慢）")
    ap.add_argument("--raise-render", action="store_true",
                    help="以本次八科 render MD 指纹覆盖基线 data/golden/render_digest.json"
                         "（须配合 --reason；架构评审 A6）")
    ap.add_argument("--reason", default="",
                    help="--raise-render 必填：为何允许 render 段漂移（防掩盖退步）")
    args = ap.parse_args()

    if args.raise_render and not args.reason.strip():
        print('× --raise-render 必须给理由：python tools/check.py --only report_contract '
              '--raise-render --reason "为何允许 render 漂移"')
        return 2

    # 选择器（--only）语义：逗号与空格等价；「选了名字却一个都没匹配上」必须显式失败。
    # 历史坑：旧文档示例写 --only version,structure,filenames（逗号），而实现按空格切，
    # 整串被当成一个陌生名字 → 所有门被跳过 → 打印"全部通过"、退出码 0（假绿）。
    only: set[str] | None = None
    if args.only is not None:
        only = {tok.strip() for chunk in args.only for tok in chunk.split(",")}
        only = {tok for tok in only if tok}
    failures: list[str] = []
    run_all = only is None
    # 可用检查项的真值源：各门调用点就地登记（见文件头"设计口径"），不另维护清单。
    seen_gates: list[str] = []

    def _register(name: str) -> None:
        if name not in seen_gates:
            seen_gates.append(name)

    def gate(name: str, fails: list[str], label: str):
        _register(name)
        if only is not None and name not in only:
            return
        if fails:
            failures.extend(fails)
            print(f"  × {label}")
            for f in fails:
                print(f"      · {f}")
        else:
            print(f"  √ {label}")

    def gate_sub(name: str, cmd: list[str], label: str, *, fast: bool = True):
        _register(name)
        if only is not None and name not in only:
            return
        argv = list(cmd)
        if fast:
            argv.insert(1, "--fast") if cmd[0].endswith("check.py") else None
        code, out = _run_py(argv, label=label)
        if code == 0:
            print(f"  √ {label}")
        else:
            failures.append(f"{label} 退出码 {code}")
            print(f"  × {label}")
            print(f"      …{_tail(out)}")

    def section(*names: str) -> bool:
        """段落守卫：登记名字并返回该段是否执行（默认全跑时恒真）。"""
        for n in names:
            _register(n)
        return only is None or any(n in only for n in names)

    print(f"[0] 版本一致性（唯一真值源 yishu_core.__version__ = {__version__}）")
    gate("version", check_version(), "全仓库无第二处版本号")

    # 读数锚点（A11 折中版）：工作树领先 HEAD 时，所有门的读数都锚不住任何 revision。
    # 报告制，不进 failures（开发期漂移是常态），只让下一位不必再用肉眼发现这个坑。
    print("\n[0b] 读数锚点（工作树 vs HEAD；报告制，不阻断）")
    if section("drift"):
        print_worktree_drift()

    print("\n[1] 结构契约（CONTRACT.md 四段 + 依赖方向单向 + 内核表唯一）")
    gate("structure", check_structure(), "学科目录完整、无学科间 import")
    gate("tables", check_core_tables(), "内核规则表无学科复制")

    gate("structure", check_modules_importable(),
         "八科 scripts 模块均可独立导入（import 期不得炸、也不得静默降级）")

    print("\n[1b] 命名与断语规范（AGENTS.md §三: 文件名无版本号 + 断语进 data JSON）")
    gate("filenames", check_filenames(), "文件名无版本号标记")
    gate("verdict_literals", check_verdict_literals(), "断语/引文外置到 data JSON（文本粗筛）")

    # 黑箱取证门：不看代码长什么样，只看用户读到什么（verdict_audit.py 的说明）
    # 比上面的文本粗筛准——粗筛会把 docstring/help 当成断语，取证门不会漏真断语。
    # 要跑 10 份真实报告，故归到 --full 档。
    print("\n[1c] 断语外置取证（跑真实报告，反查未进 data/*.json 的结论句）")
    gate_sub("verdict_audit",
             ["tools/verdict_audit.py", "--strict"],
             "断语外置取证（白名单外的未外置句判失败）", fast=False)

    # 语料消费审计（verdict_audit 的反向，SYS-REVIEW #1）：跑报告统计语料池
    # 覆盖率，零消费键打印明细。抽样覆盖有限（主题键合法不触发），只报告不判败；
    # 发现整块死语料（如 ziwei 命宫格局事件）从手工排查变成机械可见。
    print("\n[1d] 语料消费审计（同一批报告反查语料池覆盖率；报告零消费键）")
    gate_sub("verdict_consumption",
             ["tools/verdict_consumption.py"],
             "语料消费审计（报告制，零消费键可见）", fast=False)

    # 能力矩阵锁（SYS-REVIEW #3）：llms.txt 的权威矩阵必须与
    # tools/build_web.py 的 DISCIPLINE_META 一致，防「文档说八科、网页只能六科」漂移。
    print("\n[1e] 能力矩阵锁（llms.txt 权威表 ↔ build_web 清单）")
    gate("capability_matrix", check_capability_matrix(), "llms.txt 能力矩阵与站点清单一致")

    # 输入协议指纹（SYS-REVIEW #4）：request.py 的参数映射/校验与引擎 golden 同价锁定。
    print("\n[1f] 输入协议指纹（request.py 正/负例归一化产出锁定）")
    gate_sub("request_protocol",
             ["tools/request_protocol_golden.py", "verify"],
             "输入协议指纹（协议漂移即报警）", fast=False)

    # 案例库隔离门（铁律二 · 架构评审 A1）：这是三条铁律里原本**唯一零机械支撑**的一条。
    # 静态层扫解读路径的 import 闭包（四段入口 + core），运行层用 sys.addaudithook 实跑
    # 一份解读请求、断言没打开过 data/cases/** 或 references/case_library.md。
    # 判败制（与 [1c] 同级）：铁律不容"报告制"。fast=False：门自己默认两层都跑。
    print("\n[1g] 案例库隔离（铁律二：预测/解读路径不得触达案例库）")
    gate_sub("case_isolation", ["tools/case_isolation_check.py"],
             "案例库隔离（解读路径 import 闭包 + 审计 hook 实跑解读）", fast=False)

    print("\n[1h] 深链短键锁（web 深链短键 ⊆ 请求字段白名单）")
    gate("deeplink_keys", check_deeplink_keys(), "深链短键均指向有效请求字段")

    # 反馈口径单一真值源（架构评审 A2）：同语义曾两处并行实现、常量各写一份，
    # 且六爻侧支合表多出「丑午/未申」两条错项 → 虚假宽松命中。现两处只读 core 一份。
    print("\n[1i] 反馈口径单一真值源（应期判定常量/支表只在 core/yishu_core/yingqi.py）")
    gate("feedback_caliber", check_feedback_caliber(),
         "合参层与六爻侧共用内核一份应期口径（含表驱动边界断言）")

    # 语料可复现：构建器重跑结果必须与已入库 data/*.json 一致——防「引文层手工补录后
    # 构建器与入库脱钩，重跑即静默删条目」（2026-10-02f 实测过 ming 的「通隔論」）。
    # 尚未提供 --check 的构建器在本段末尾如实列出（登记为待补，不假装覆盖）。
    print("\n[1j] 语料可复现（构建器 --check 与入库 data/*.json 语义比对）")
    CORPUS_BUILDERS = (
        ("ming", "disciplines/ming/dev_tools/build_dts_corpus.py"),
        ("ming", "disciplines/ming/dev_tools/build_tiaohou.py"),
        ("ziwei", "disciplines/ziwei/dev_tools/build_corpus.py"),
        ("meihua", "disciplines/meihua/dev_tools/build_classics.py"),
        ("zeji", "disciplines/zeji/dev_tools/build_citations.py"),
        ("lingqi", "disciplines/lingqi/dev_tools/build_ketable.py"),
        ("liuren", "disciplines/liuren/dev_tools/build_course_cases.py"),
        ("liuren", "disciplines/liuren/dev_tools/build_kemu_notes.py"),
    )
    if section("corpus_repro"):
        for disc, script in CORPUS_BUILDERS:
            tag = f"{disc}/{Path(script).stem}"
            code, out = _run_py([script, "--check"], label=f"{tag} 语料可复现")
            if code == 0:
                print(f"  √ {tag} 语料可复现"
                      f"（{sum(1 for ln in out.splitlines() if '与重算一致' in ln)} 个文件）")
            else:
                failures.append(f"{tag} 语料层与构建器不一致（重跑会改变入库文件）")
                print(f"  × {tag} 语料可复现")
                print(f"      …{_tail(out, 8)}")
        print("  （未纳入本段的构建器见 docs/TECH-DEBT.md §2.4：需先为其补 --check）")

    print("\n[2] 内核自检（干支历/农历/评分器）")
    if section("core"):
        code, out = _run_py(["core/yishu_core/calendar_check.py"], label="内核自检")
        if code == 0:
            print("  √ 干支历内核自检")
        else:
            failures.append("内核自检失败")
            print("  × 干支历内核自检")
            print(f"      …{_tail(out)}")
        code, out = _run_py(["tools/core_selftest.py"], label="内核 API 自测")
        if code == 0:
            print("  √ 内核 API 自测（旬空/三刑/长生/纳音/十神/节气）")
        else:
            failures.append("内核 API 自测失败")
            print("  × 内核 API 自测")
            print(f"      …{_tail(out)}")
        code, out = _run_py(["tools/text_keys_selftest.py"], label="断语库键一致性")
        if code == 0:
            print("  √ 断语库键一致性（JSON 与代码引用对齐）")
        else:
            failures.append("断语库键一致性失败")
            print("  × 断语库键一致性")
            print(f"      …{_tail(out)}")

    for disc in SMOKE_DISCIPLINES:
        print(f"\n[{SMOKE_DISCIPLINES.index(disc) + 3}] {disc} 质量门"
              f"{'（含案例评测）' if args.full else '（快速：指纹+冒烟）'}")
        gate_sub(disc, [f"disciplines/{disc}/dev_tools/check.py"], disc, fast=not args.full)

    print("\n[5] 八科行为指纹（golden 基线：重构只准改结构，不准改行为）")
    for disc in ALL_DISCIPLINES:
        g = ROOT / "disciplines" / disc / "dev_tools" / "golden.py"
        if not g.is_file():
            continue
        gate_sub(f"golden_{disc}", [str(g.relative_to(ROOT))], f"{disc} 行为指纹", fast=False)

    print("\n[6] 六爻（迁移前旧实现：冒烟 + 四段契约端到端；--full 加黑箱回归）")
    gate_sub("liuyao", ["disciplines/liuyao/tests/smoke_test.py"], "六爻冒烟", fast=False)
    # 报告忠实度审计：narrate 正文断言 vs 引擎结构化输出，出现 invented/contradicted 即失败。
    # A10 已落地：原只跑单例 --demo（证明不了换个起卦法/换类问事时叙述模板仍不越界），
    # 现跑内置语料 12 例（coin/time/number 三种起卦法 × 求财/病/考试/婚姻/出行/官司/失物/天气/行人）。
    gate_sub("faithfulness", ["tools/report_faithfulness.py", "--corpus"],
             "报告忠实度（12 例语料：narrate 断言 vs 引擎结构）", fast=False)
    # 六爻四段契约薄适配层（chart→analyze→render）端到端冒烟。
    # 归在 liuyao 名下（与本节其余两项、以及下面 --full 的回归判据同键）——否则
    # `--only <别门>` 会连带跑三个子进程，甚至在别门"过关"时把它判红。
    if section("liuyao"):
        scratch = ROOT / "tools" / "scratch" / "liuyao_pipeline"
        scratch.mkdir(parents=True, exist_ok=True)
        chart_json = scratch / "chart.json"
        analyze_json = scratch / "analyze.json"
        report_md = scratch / "report.md"
        pipe_steps = [
            (["disciplines/liuyao/scripts/chart.py", "--mode", "time",
              "--datetime", "2026-09-23 10:00", "--question", "占合同能否成交",
              "-o", str(chart_json)], "六爻 chart"),
            (["disciplines/liuyao/scripts/analyze.py", str(chart_json),
              "-o", str(analyze_json)], "六爻 analyze"),
            (["disciplines/liuyao/scripts/render.py", str(analyze_json),
              "-o", str(report_md)], "六爻 render"),
        ]
        pipe_ok = True
        for cmd, label in pipe_steps:
            code, out = _run_py(cmd, label=label)
            if code != 0:
                pipe_ok = False
                print(f"  × {label}")
                print(f"      …{_tail(out)}")
        if pipe_ok and report_md.is_file() and analyze_json.is_file():
            print("  √ 六爻四段契约端到端（chart→analyze→render）")
        elif pipe_ok:
            pipe_ok = False
            failures.append("六爻四段契约产物缺失")
            print("  × 六爻四段契约产物缺失")
        if not pipe_ok:
            failures.append("六爻四段契约端到端失败")
    if args.full and (only is None or "liuyao" in only):
        # 六爻自身质量门对回归用基线口径（11/18，2026-09-22 实测），
        # 残余案例待古籍重推（README/HANDOFF 已声明）——根门对齐该口径，不得要求全过。
        code, out = _run_py(["disciplines/liuyao/tests/regression_test.py"], label="六爻回归")
        m = re.search(r"总通过:\s*(\d+)/(\d+)", out)
        if code == 0 or (m and int(m.group(1)) >= 11):
            print(f"  √ 六爻黑箱回归（{m.group(0) if m else '通过'}，基线 11/18）")
        else:
            failures.append("六爻黑箱回归低于基线")
            print("  × 六爻黑箱回归（低于基线 11/18）")
            print(f"      …{_tail(out)}")

    # render 段是全库唯一无内容保护的段落（架构评审 A6）：八科 golden 均不含 render，
    # 根门原本只判"产物存在"。这里对**用户真正读到的统一报告**做契约级结构断言：
    # 口径声明句与反馈尾注必须在位，禁用断言词必须为 0。
    if section("report_contract"):
        print("\n[6b] 报告契约（render 段结构断言 · 八科逐科：口径句/反馈尾注在位，禁用断言词为 0）")
        from yishu_core.report.request import MD_FEEDBACK_NOTE, REPORT_FOOTER  # noqa: E402
        rc_dir = ROOT / "tools" / "scratch" / "report_contract"
        rc_dir.mkdir(parents=True, exist_ok=True)
        # 每科一条最小请求（覆盖八科 render 路径）；经 --request 传入，避免逐科拼 flag。
        cases = (
            {"discipline": "liuyao", "question": "占合同能否成交", "mode": "time",
             "datetime": "2026-09-23 10:00"},
            {"discipline": "ming", "question": "命局", "datetime": "1990-05-20 10:30", "gender": "男"},
            {"discipline": "ziwei", "question": "命盘", "datetime": "1990-05-20 10:30", "gender": "女"},
            {"discipline": "meihua", "question": "占投资", "way": "numbers", "numbers": "3,5,7"},
            {"discipline": "xiaoliuren", "question": "占出行", "datetime": "2026-09-30 10:30"},
            {"discipline": "zeji", "question": "择日", "date": "2026-09-30", "activity": "开市"},
            {"discipline": "liuren", "question": "占面试", "datetime": "2026-09-30 10:30"},
            {"discipline": "lingqi", "question": "占求财", "up": 2, "mid": 1, "down": 3},
        )
        problems: list[str] = []
        md_digests: dict[str, str] = {}
        for case in cases:
            disc = case["discipline"]
            req_p = rc_dir / f"{disc}.request.json"
            req_p.write_text(json.dumps(case, ensure_ascii=False), encoding="utf-8")
            code, out = _run_py(
                ["tools/report.py", "--request", str(req_p), "--name", disc,
                 "--outdir", str(rc_dir)], label=f"报告契约:{disc}")
            md_p = rc_dir / f"{disc}.md"
            html_p = rc_dir / f"{disc}.html"
            if code != 0 or not md_p.is_file() or not html_p.is_file():
                problems.append(f"{disc}：统一报告未生成（render 段端到端失败）")
                continue
            md = md_p.read_text(encoding="utf-8")
            html = html_p.read_text(encoding="utf-8")
            md_digests[disc] = hashlib.sha256(md.encode("utf-8")).hexdigest()[:16]
            if MD_FEEDBACK_NOTE.strip() not in md:
                problems.append(f"{disc}：MD 缺反馈尾注（MD_FEEDBACK_NOTE 未接线）")
            if REPORT_FOOTER not in html:
                problems.append(f"{disc}：HTML 缺口径声明（REPORT_FOOTER 未接线）")
            hit = BANNED_CLAIM.search(md + "\n" + html)
            if hit:
                problems.append(f"{disc}：出现禁用断言词「{hit.group(0)}」")
            # 关键字段必达：analyze 算出的结构化值必须出现在 narrate 正文
            an_p = rc_dir / f"{disc}.analyze.json"
            if an_p.is_file():
                cs = (json.loads(an_p.read_text(encoding="utf-8")) or {}).get("chart_summary") or {}
                for key in REPORT_REQUIRED.get(disc, ()):
                    val = cs.get(key)
                    if val and str(val) not in md:
                        problems.append(f"{disc}：narrate 未呈现 chart_summary.{key}={val}"
                                        "（算出来了但报告看不到）")

        # render 段内容指纹（A6 大动血）：MD 逐字节哈希，八科各一份，漂移即红。
        prior_render: dict = {}
        if RENDER_GOLDEN.exists():
            prior_render = json.loads(RENDER_GOLDEN.read_text(encoding="utf-8"))
        if args.raise_render:
            from datetime import datetime as _dt
            base = dict(prior_render.get("md") or {})
            log = list(prior_render.get("drift_log") or [])
            for d, v in sorted(md_digests.items()):
                if base.get(d) != v:
                    log.append({"discipline": d, "from": base.get(d), "to": v,
                                "date": _dt.now().strftime("%Y-%m-%d"),
                                "reason": args.reason.strip()})
                base[d] = v
            RENDER_GOLDEN.parent.mkdir(parents=True, exist_ok=True)
            RENDER_GOLDEN.write_text(json.dumps({
                "_meta": {
                    "what": "八科 render 段 Markdown 内容指纹基线（逐字节，含反馈尾注）",
                    "how": "改 render 模板/字段后跑 python tools/check.py --only "
                           "report_contract --raise-render --reason \"理由\"；同源验收已保证 "
                           "本地=网页，本基线保证「和上一版一样」（架构评审 A6）",
                },
                "md": base,
                "drift_log": log[-20:],
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"  · render 指纹已落基线 {RENDER_GOLDEN.name}"
                  f"（{len(md_digests)} 科，理由已记 drift_log）")
        else:
            base = prior_render.get("md") or {}
            if not base:
                problems.append("缺 render 指纹基线 data/golden/render_digest.json"
                                "（跑 --only report_contract --raise-render --reason … 落基线）")
            else:
                for d in sorted(set(md_digests) | set(base)):
                    if d not in md_digests:
                        continue
                    if d not in base:
                        problems.append(f"{d}：基线无该科 render 指纹（新增科目请重捕基线）")
                    elif base[d] != md_digests[d]:
                        problems.append(f"{d}：render MD 指纹漂移 {base[d]} → {md_digests[d]}"
                                        "（有意改版请 --raise-render --reason …）")
        gate("report_contract", problems, "报告契约（八科：口径句/尾注在位；无禁用词；关键字段必达）")

    print("\n[7] 合参层（synthesis 自检：person 校验 + 裁决规则 + 归一化）")
    gate_sub("synthesis", ["synthesis/cli.py", "selfcheck"], "synthesis 自检", fast=False)

    print("\n[7b] 纯前端站点（浏览器内跑同一份引擎：零凭证出报告）")
    if section("web"):
        # 站点自检里含"清单↔镜像逐条对齐"，所以必须先构建再校验。
        # 构建到**一次性目录**（评审 2026-10-03 定）：`site/` 是生成物但非本工具独占，
        # 逐文件记账清理在大目录下仍会触碰批量删除阈值；一次性目录随用随弃，
        # 既不需要删除权限，也不会把生成物写进仓库工作区（site/ 本已 gitignore）。
        import tempfile
        site_dir = Path(tempfile.mkdtemp(prefix="yi-site-verify-"))
        try:
            code, out = _run_py(["tools/build_web.py", "--outdir", str(site_dir)],
                                label="站点构建")
            if code == 0:
                print("  √ 站点构建（源码镜像 + 清单；一次性目录，不写工作区）")
            else:
                failures.append("站点构建失败")
                print("  × 站点构建")
                print(f"      …{_tail(out)}")
            code, out = _run_py(["tools/check_web_site.py", "--site", str(site_dir)],
                                label="站点自检")
            if code == 0:
                print("  √ 站点自检（清单/镜像/内核引用一致）")
            else:
                failures.append("站点自检失败")
                print("  × 站点自检")
                print(f"      …{_tail(out)}")
        finally:
            shutil.rmtree(site_dir, ignore_errors=True)

    # parity/tests 是"选项门"：默认档不跑，--full 或 --only 点名才跑（原语义，未改）。
    if section("parity") and (args.full or only is not None):
        print("\n[7c] 网页端与本地端同源（同一请求两边出报告，逐字节比对）")
        code, out = _run_py(["tools/verify_web_parity.py"], label="同源验收")
        if code == 0:
            print("  √ 同源验收（" + (out.strip().splitlines() or [""])[-1] + "）")
        else:
            failures.append("同源验收失败")
            print("  × 同源验收")
            print(f"      …{_tail(out, 6)}")

    # 各科案例评测一览：把 `tools/eval.py` 纳入门（HANDOFF §四.6 挂账）。
    # 它只转发各科 evaluate.py（不写第二套给分逻辑），故是"汇总可见性"门：
    # 无 evaluate.py 的学科（ming/ziwei/lingqi）按「无案例对齐评测」跳过、不计失败。
    if section("eval_overview") and (args.full or only is not None):
        print("\n[7d] 各科案例对齐分一览（tools/eval.py 转发各科 evaluate；非预测率）")
        code, out = _run_py(["tools/eval.py"], label="各科评测一览")
        if code == 0:
            print("  √ 各科评测一览（tune/holdout 均跑通）")
        else:
            failures.append("各科评测一览转发失败")
            print("  × 各科评测一览")
            print(f"      …{_tail(out, 6)}")

    if section("tests") and (args.full or only is not None):
        print("\n[8] 单元测试（pytest tests）")
        cands = _resolve_pytest_exe()
        code, out = 1, ""
        for idx, exe in enumerate(cands):
            code, out = _run_py(["-m", "pytest", "tests", "-q"], label="pytest tests", exe=exe)
            if code == 0:
                break
            # 仅因该解释器未装 pytest 且仍有候选 → 回退到 venv python；
            # 否则视为真实测试失败，停止尝试。
            if "No module named pytest" in out and idx < len(cands) - 1:
                continue
            break
        if code == 0:
            print("  √ pytest tests")
        else:
            failures.append("pytest tests 失败")
            print("  × pytest tests")
            print(f"      …{_tail(out)}")

    print()
    matched = [] if only is None else [n for n in seen_gates if n in only]
    unknown = [] if only is None else sorted(n for n in only if n not in seen_gates)

    if failures:
        print(f"质量门失败 {len(failures)} 项。")
        for f in failures:
            print(f"  × {f}")

    # 选择器自证：选了名字却没跑起来——这是"假绿"里最凶的一种（旧行为在此打印
    # "全部通过"并退出 0）。一律显式失败并列出可用检查项；用法错误一律退出码 2。
    if only is not None and (not matched or unknown):
        if not only:
            why = "`--only` 展开后为空，至少要给一个检查项"
        elif not matched:
            why = f"{sorted(only)} 里没有一个能对上的检查项"
        else:
            why = f"不认识这些检查项 {unknown}"
        print()
        print(f"--only 用法错误：{why}")
        if not matched:
            print("  （上面的 √ 不代表任何检查真的跑过——别把它当通过。）")
        print("  可用检查项（取自各门调用点；逗号与空格分隔等价）：")
        for i in range(0, len(seen_gates), 4):
            print("    " + "".join(f"{c:<24}" for c in seen_gates[i:i + 4]).rstrip())
        return 2

    if failures:
        return 1
    print("仓库级质量门全部通过。")
    print("分数含义：与古籍案例要点的一致性，不代表现实预测命中率。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
