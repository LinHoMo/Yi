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
# 学科清单唯一真值源：与 build_web.py 同源，避免 check.py 再硬编码一份学科名字
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
# 四段契约豁免条目（查表直录类学科，已随学科收缩移除）。保留键位防历史配置引用。
CONTRACT_EXEMPT_FILES = ("data/verdicts.json",)
TABLE_LOOKUP_DISCIPLINES = ()

# 目录级预算（架构评审 A3）：单文件看门狗对「几十个文件合计上万行」的分布式巨石无感。
# 超过基础预算的科必须在 DECLARED_HEAVY 里显式申报上限，否则失败——
# 「重科」是显式声明，不是默认漂移。
SCRIPTS_BUDGET_BASE = 6000
DECLARED_HEAVY = {"liuyao": 22000}

# 快速冒烟门（跑 golden，成本高）只跑 ming；两科的"静态结构门"（文件齐全）由
# check_structure 用 request.DISCIPLINES 全覆盖，新科接入时不必改这里。
SMOKE_DISCIPLINES = ("ming",)

# render 段内容指纹基线（架构评审 A6）：render 是四段里唯一无内容指纹的一段。
# 只锁 Markdown 逐字节（同源验收口径即「MD 逐字节一致」；HTML 页头 runtime 标签是有意差异）。
RENDER_GOLDEN = ROOT / "data" / "golden" / "render_digest.json"

# ── 内核唯一真值源（AGENTS.md §二）：表名名单与干支序列一律从 core **运行期反射** ──
# 2026-10-09 实测缺陷：这里曾手写 35 个表名，而 §二 亲自点名的
# `NAJIA_BRANCHES` / `TOMB_MAP` / `TIAO_HOU` / `JIE_SHA` 一个都不在名单里，
# 于是往学科层复制这四张表中的任意一张，门都不判红。名单的唯一来源改为
# core 模块级集合名（真值即名单），贡献者新增内核表**不必回来改这里**。
LEGACY_CORE_TABLE_NAMES = (
    # core 已无同名表的历史别名/拆分名（§一 历史教训里点名的形态）。
    # 同名检测靠反射，改名检测靠下面的内容指纹三档；这里只补"历史上真出现过"的名字。
    "NAYIN_TABLE", "SAN_HE", "NAJIA", "LIU_QIN", "LIU_SHEN", "STEMS", "BRANCHES",
    "TWELVE_CHANGES", "ER_SHISI_XIU", "JIAN_CHU", "HUANG_HEI_DAO",
)
# 逐条人工定性的豁免（`相对路径::变量名`）。新增必须写理由，且只豁免一条命中，
# 不做目录/前缀级豁免——豁免面扩大等于判据消失（AGENTS.md §四.3 同一口径）。
CORE_TABLE_ALLOW: dict[str, str] = {
    "disciplines/ming/dev_tools/sync_tiaohou_engine.py::_ORDER":
        "寅首（正月建寅）月支序：与 core EARTHLY_BRANCHES 同集不同序（轮转而非复制）。"
        "2026-10-09 由排序无关指纹首次抓出；正确写法是由 core 派生（rotate），"
        "该 dev_tool 不在本轮改动所有权内，故先显式登记，改完即删本条。",
}
# core 包目录（测试注入扫描根时不跟着漂移；`ROOT` 仍供其它门使用）
_CORE_ROOT = ROOT / "core"
CORE_PKG = _CORE_ROOT / "yishu_core"
# 反射用的学科/工具扫描根覆盖（tests/test_gate_truth_source.py 注入临时树用）
SCAN_ROOTS_OVERRIDE: list[Path] | None = None
# 反射结果进程内缓存（core 表名/真值库各扫一遍，负例自证时 refresh 丢掉）
_NAMES_CACHE: dict = {}
_CORE_LIB_CACHE: dict = {}

# 学科间 import（违反 disciplines 禁止互相 import 的契约）
# 四种形态都要拦（2026-10-08 扩）：
#   bare   —— `from liuyao import x` / `import ming`（旧门只有这一条，且只扫 scripts/）
#   dotted —— `from disciplines.ming.scripts.analyze import …`
#   dyn    —— `importlib.import_module("disciplines.liuyao.scripts.classical_analysis")`
#   path   —— 把 `disciplines/liuyao/…` 当字符串路径拼进 sys.path 再裸 import
# 实测教训：ming 的跨科审计脚本用 dotted+dyn 两种形态，旧门两种全漏；它一旦放在
# 学科目录里，学科→学科的依赖就绕过了结构门（现已移到仓库级 tools/）。
_CROSS_DISC = "liuyao|ming"
CROSS_DISC_IMPORT = re.compile(
    r"^\s*(?:from|import)\s+(" + _CROSS_DISC + r")\b")
CROSS_DISC_DOTTED = re.compile(
    r"(?:from|import)\s+disciplines\.(" + _CROSS_DISC + r")\b")
CROSS_DISC_DYN = re.compile(
    r"import_module\(\s*[\"'](?:disciplines\.)?(" + _CROSS_DISC + r")\b")
CROSS_DISC_PATHISH = re.compile(
    r"[\"']disciplines[/\\\\](" + _CROSS_DISC + r")[/\\\\]")

# 报告禁用断言词（铁律三）：只拦"肯定式"断言——「命中率/准确率」后紧跟数字，或「断事如神」。
# 不拦"不宣称现实预测命中率"这类否定式免责句（其后不是数字）。
BANNED_CLAIM = re.compile(r"(?:命中率|准确率)\s*[:：]?\s*\d|断事如神")

# 报告契约·两科必达字段（analyze.chart_summary 的键 → 其值必须出现在 narrate 正文）。
# 取「实测确认会渲染」的结构化键，专抓「算出来了但报告没呈现」（AGENTS.md §四.6 报告层同步）。
REPORT_REQUIRED = {
    "liuyao": ("用神", "旺衰"),
    "ming": ("强弱", "格局", "胎元"),
}

# 文件名版本号标记（AGENTS.md §三：名字不携带版本；版本走 git 与 CHANGELOG）
# 排除 archive/ 目录和 .git/ 目录，匹配 _v2 / _V3 / _v10 等
VERSIONED_FILENAME = re.compile(
    r"_v\d+(?:\.[A-Za-z0-9_]+)?\.(?:py|md|json|txt|yaml|yml|toml)$", re.I)

# 中文断语字面量检测（AGENTS.md §三：断语/引文进 data/*.json，代码只留算法）
# 检测 .py 文件中 dict/List 值含连续 8+ 中文字符的字符串
CHINESE_VERDICT_LITERAL = re.compile(r"[\u4e00-\u9fff]{8,}")

# 干支序列唯一字面量：完整十天干串 / 完整十二地支串。
# 2026-10-09 起**不在此处写字面量**（本文件自己也在扫描面 `tools/**` 里，
# 写死一串等于门自己违规），序列值由 `_core_ganzhi_sequences()` 从 core 反射取；
# 判定也从"逐行正则"改为"AST 折叠后比对"，于是 `"甲乙丙丁" + "戊己庚辛壬癸"`
# 这种拆两段拼接的绕过形态照样命中（见 `check_core_string_tables`）。


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
    # 学科清单唯一真值源 = request.DISCIPLINES（本文件已 import 为 ALL_DISCIPLINES）。
    # 2026-10-09：这里曾另存一份写死的 ["liuyao", "ming"]——两科收缩恰好没变形，
    # 但 `eval.py` 里还有第二份，三份并存就是 §二「同一批表在三个文件里各存一份」的同病。
    all_ids = list(ALL_DISCIPLINES)
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


def _request_probe_values() -> dict:
    """字段活性探针用的取值表：每个字段给一个**能让该科真的消费它**的值。

    取值域逐字取自 `request.py` 的白名单（LIUYAO_MODES / LIUYAO_ZI_HOUR_TYPES /
    gender 男|女 / yao 6-9）——取值不合法会让 normalize_request 先炸，
    探针就测不到"字段是否真的进了命令行"。
    """
    from yishu_core.report.request import LIUYAO_MODES, LIUYAO_ZI_HOUR_TYPES  # noqa: PLC0415
    return {
        "question": "占求财",
        "datetime": "2026-09-30 10:30",
        "gender": "男",
        "mode": "manual" if "manual" in LIUYAO_MODES else LIUYAO_MODES[0],
        "numbers": "3,8,5",
        "yao": "7,8,9,7,6,8",
        "seed": "42",
        "longitude": "116.4",
        "hour": "23",
        "distinguish_zi_hour": "1",
        "zi_hour_type": LIUYAO_ZI_HOUR_TYPES[-1],
        "name": "probe",
        "discipline": None,          # 由请求本身给出
    }


def check_field_liveness(*, field_usage: dict | None = None,
                         field_scope: dict | None = None,
                         display_purpose: dict | None = None) -> list[str]:
    """[1h] 的第二半：**字段活性**（与 `tests/test_request_parity.py` 同判据）。

    `check_deeplink_keys` 只做 `set(短键) ⊆ REQUEST_FIELDS` 的**单向子集**——
    白名单自己含死字段时它永远绿（2026-10-09 协议批次实测：往 `FIELD_USAGE`
    塞一个假字段，`tests/test_request_parity.py` 判红 2 项，本门返回 `[]`）。
    现逐字段判"有没有人真的消费它"：
      · `argv` 类：必须出现在某科 `chart_argv`/`analyze_argv`/`render_argv` 的产出里
        （旗标名 = 字段名短横化；取值由 `_request_probe_values()` 喂给真映射层）；
      · `display` 类：必须在 `DISPLAY_PURPOSE` 里有用途标注（页头得说清它干什么）；
      · 两类都必须挂在至少一个学科上（`FIELD_SCOPE`），否则请求根本到不了它。
    判据处只有 `request.py` 一处：本函数不改写映射，只调用它并看产出。
    三个关键字参数供 `tests/test_gate_field_liveness.py` 注入假字段做负例自证
    （与真值源门的 `SCAN_ROOTS_OVERRIDE` 同一手法——负例绝不真往仓库植文件）。
    """
    from yishu_core.report import request as rq  # noqa: PLC0415
    usage = field_usage if field_usage is not None else rq.FIELD_USAGE
    scope = field_scope if field_scope is not None else rq.FIELD_SCOPE
    purpose = display_purpose if display_purpose is not None else rq.DISPLAY_PURPOSE
    values = _request_probe_values()

    # 逐科逐字段构造"只多带这一个字段"的请求，收集真映射层实际吐出的旗标名。
    # FIELD_SCOPE 的形状是 字段 → 消费它的学科（不是 学科 → 字段），别取反。
    # 基架要按**起卦方式各来一份**：有些字段只在某一 mode 下被消费
    # （如 `yao` 只在 mode=manual 时进命令行），单一基架会把它误判成死字段。
    bases: dict[str, list[dict]] = {d: [{}] for d in rq.DISCIPLINES}
    if "liuyao" in bases:
        bases["liuyao"] = [{"mode": m} for m in rq.LIUYAO_MODES]
    emitted: set[str] = set()
    for disc in rq.DISCIPLINES:
        for field in [f for f, ds in scope.items() if disc in ds]:
            if field == "discipline" or values.get(field) is None:
                continue
            for base in bases[disc]:
                req = {"discipline": disc, **base}
                # 该科必填项先补齐，否则 normalize_request 在字段校验之前就炸
                for need in rq.REQUIRED.get(disc, ()):
                    req.setdefault(need, values.get(need))
                req[field] = values[field]
                try:
                    normed = rq.normalize_request(req)
                    argv = (rq.chart_argv(normed, "chart.py", "c.json")
                            + rq.analyze_argv(normed, "analyze.py", "c.json", "a.json")
                            + rq.render_argv(normed, "render.py", "a.json", "r.md"))
                except ValueError:
                    # 被 normalize_request 拒收 = 这一形态不消费它（换下一个基架再试；
                    # 若所有形态都拒收，下面按死字段判红）
                    continue
                emitted |= {tok[2:].replace("-", "_")
                            for tok in argv if tok.startswith("--")}

    fails: list[str] = []
    for field, kind in usage.items():
        on = [d for d in rq.DISCIPLINES if d in scope.get(field, ())]
        if not on:
            fails.append(f"死字段 {field}：FIELD_USAGE 收了它、FIELD_SCOPE 却没挂任何学科"
                         "——请求永远带不上去，是个纯占位")
            continue
        if kind == rq.USAGE_ARGV:
            if field not in emitted:
                fails.append(
                    f"死字段 {field}：声明为 argv 类（应进命令行），但 "
                    + "、".join(f"{d} 的 chart/analyze/render_argv" for d in on)
                    + " 产出里没有 --" + field.replace("_", "-")
                    + "——看着像输入、实际没有任何引擎阶段收到它（铁律三）")
        elif kind == rq.USAGE_DISPLAY:
            if field not in purpose:
                fails.append(f"死字段 {field}：display 类却不写 DISPLAY_PURPOSE 用途——"
                             "页面看得见却不说明它干什么，读者会以为它参与了推演")
        else:
            fails.append(f"字段 {field} 的消费方式 {kind!r} 不属于 argv/display 两种，"
                         "本门无法认定它该被谁消费")
    for field in purpose:
        if field not in usage:
            fails.append(f"DISPLAY_PURPOSE 里的 {field} 不在 FIELD_USAGE——"
                         "用途标注指向一个不存在的字段")
    return fails


def check_structure() -> list[str]:
    """学科目录契约：八字 / 六爻两科四段文件齐全；依赖方向单向。

    清单取 `request.DISCIPLINES`（唯一真值源，仅含 ming/liuyao），扩展正式学科时
    自动覆盖。
    查表直录类学科豁免 `CONTRACT_EXEMPT_FILES`，见 `docs/CONTRACT.md` §四。
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
    # 学科互相 import（全学科目录扫描：含 dev_tools/tests/其它子包；
    # 旧门只扫 `scripts/` 且只认裸模块名，于是学科层用点分路径 / importlib 动态加载别科
    # 完全畅通——实测曾在 ming/dev_tools 里命中两处）
    for p in sorted((ROOT / "disciplines").rglob("*.py")):
        if "scratch" in p.parts or "__pycache__" in p.parts:
            continue
        parts = p.relative_to(ROOT).parts
        own = parts[1] if len(parts) > 1 else ""
        if own not in ALL_DISCIPLINES:
            continue          # 未注册目录由 §2.4 债务行管
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            hits = []
            for pat in (CROSS_DISC_IMPORT, CROSS_DISC_DOTTED,
                        CROSS_DISC_DYN, CROSS_DISC_PATHISH):
                m = pat.search(line)
                if m and m.group(1) != own:
                    hits.append(m.group(1))
            for other in sorted(set(hits)):
                fails.append(f"{p.relative_to(ROOT)}:{i}: 学科间 import {other}"
                             f"（本科={own}；§二 依赖方向单向，跨科审计请放 tools/）")
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
    """两科每个 `scripts/*.py` 都能独立 import 成功。

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


def _truth_source_scan_roots() -> list[Path]:
    """唯一真值源门的扫描根（AGENTS.md §二 声称覆盖 `disciplines/**` 与 `tools/**`）。

    2026-10-08 实测教训：本函数存在之前，四条判据一律只 `rglob(ROOT/"disciplines")`，
    于是 `tools/report_faithfulness.py` 里的地支串与六亲表副本长期放行——文档说覆盖、
    代码没覆盖，比"没写这条规则"更危险。改扫描根时请同步 AGENTS.md §二 的措辞。

    `SCAN_ROOTS_OVERRIDE` 供 `tests/test_gate_truth_source.py` 注入临时树做负例自证：
    负例绝不能真往仓库里植文件（并行批次会互相踩），也不能只测正则而不测整条判据。
    """
    if SCAN_ROOTS_OVERRIDE is not None:
        return list(SCAN_ROOTS_OVERRIDE)
    return [ROOT / "disciplines", ROOT / "tools"]


def _truth_rel(p: Path) -> str:
    """扫描面内统一展示路径（临时树不在 ROOT 下，故逐级回退）。"""
    try:
        return p.relative_to(ROOT).as_posix()
    except ValueError:
        pass
    for r in _truth_source_scan_roots():
        try:
            return p.relative_to(r).as_posix()
        except ValueError:
            continue
    return p.as_posix()


def _core_allow(path: Path, name: str) -> bool:
    """逐条人工定性的豁免（`相对路径::变量名` 精确命中，不做前缀/目录级豁免）。"""
    key = f"{_truth_rel(path)}::{name}"
    return key in CORE_TABLE_ALLOW


def _truth_source_files() -> list[Path]:
    """扫描根下的 .py 文件（排除 scratch/__pycache__）。"""
    out: list[Path] = []
    for root in _truth_source_scan_roots():
        if not root.is_dir():
            continue
        out.extend(p for p in root.rglob("*.py")
                   if "scratch" not in p.parts and "__pycache__" not in p.parts)
    return sorted(out)


def _module_level_names(py_file: Path) -> set[str]:
    """本文件**模块级**（非下划线）赋值名：用来区分"core 自己定义的表"与
    "core 里 from … import 进来的别名"（后者不该算进本模块的真值名单）。"""
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return set()
    out: set[str] = set()
    for node in tree.body:
        tgts: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            tgts = list(node.targets)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            tgts = [node.target]
        for t in tgts:
            if isinstance(t, ast.Name) and not t.id.startswith("_"):
                out.add(t.id)
    return out


def core_table_names(*, refresh: bool = False) -> tuple[set[str], list[str]]:
    """内核真值表名（运行期反射 `core/yishu_core/*.py` 的模块级 dict/list/tuple/set）。

    返回 `(名字集合, 失败明细)`；失败明细非空**调用方必须判红**——名单取空等于整条
    同名门静默空转（与 2026-10-09 修掉的 `if not core_fps: return []` 同一类缺陷）。
    """
    if refresh:
        _NAMES_CACHE.clear()
    if _NAMES_CACHE:
        return _NAMES_CACHE["v"]
    names: set[str] = set()
    fails: list[str] = []
    files = sorted(CORE_PKG.glob("*.py"))
    if not files:
        fails.append(f"内核真值表名反射：{CORE_PKG} 下没有 .py —— 扫描根解析错了，"
                     "「无第二份」的结论无效")
        return names, fails
    if str(_CORE_ROOT) not in sys.path:
        sys.path.insert(0, str(_CORE_ROOT))
    for p in files:
        if p.stem == "__init__":
            continue
        local = _module_level_names(p)
        try:
            mod = importlib.import_module(f"yishu_core.{p.stem}")
        except Exception as exc:  # noqa: BLE001 —— 反射失败必须显形
            fails.append(f"内核真值表名反射：import yishu_core.{p.stem} 失败"
                         f"（{type(exc).__name__}: {exc}）——名单不完整，本结果不可信")
            continue
        for n in local:
            v = getattr(mod, n, None)
            if isinstance(v, (dict, list, tuple, set, frozenset)) and v:
                names.add(n)
    _NAMES_CACHE["v"] = (names, fails)
    return names, fails


def _core_table_assign_pat(names: set[str]) -> re.Pattern:
    """同名赋值判据（由反射名单现搭，不手写名单）。

    2026-10-09 实测的两处盲区一并补掉：
      ① 旧式要求 `=` 后首字符是 `[`/`{` —— `LIU_QIN = ("比肩", …)` 的 tuple 形态逃逸；
      ② 旧锚 `^\\s*(NAME)\\s*=` —— 注解式 `TIAO_HOU: dict[str, …] = {` 逃逸
         （仓库内已有 7 处注解式表赋值）。
    """
    alt = "|".join(sorted((re.escape(n) for n in names), key=len, reverse=True))
    return re.compile(
        r"^\s*(" + alt + r")\s*(?::[^=\n]+?)?=\s*[\[\({]", re.M)


def check_core_tables() -> list[str]:
    """内核表唯一：学科/工具层不得重新定义 core 已有规则表（同名 + 改名副本两层检测）。"""
    fails: list[str] = []
    files = _truth_source_files()
    if not files:
        return ["内核真值源门扫描 0 个文件：扫描根解析错了"
                "（应覆盖 disciplines/** 与 tools/**），「无复制」的结论无效"]
    names, refl = core_table_names()
    fails.extend(refl)
    if names:
        pat = _core_table_assign_pat(names | set(LEGACY_CORE_TABLE_NAMES))
        for p in files:
            for i, line in enumerate(
                    p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                m = pat.match(line)
                if not m:
                    continue
                name = m.group(1)
                if _core_allow(p, name):
                    continue
                fails.append(f"{_truth_rel(p)}:{i}: 复制内核表 {name}（唯一真值源在 core）")
    fails.extend(check_core_table_renames())
    fails.extend(check_core_tables_in_scope())
    fails.extend(check_core_string_tables())
    return fails


def _lit_kind(node: ast.AST) -> str | None:
    """字面量容器类型名（dict/list/tuple/set）；其它形态返回 None。"""
    return ("dict" if isinstance(node, ast.Dict) else
            "list" if isinstance(node, ast.List) else
            "tuple" if isinstance(node, ast.Tuple) else
            "set" if isinstance(node, ast.Set) else None)


def _canon_fp(kind: str, val: object) -> str | None:
    """归一化内容指纹：dict 按键排序、set 按元素排序、list/tuple 保序（逐字节口径）。

    空容器不参与指纹比对：`{}`/`[]` 常是"运行时从 core 派生填充"的合法形态
    （如 chain_tables 用 core HE_PAIRS 现算六合表），并非复制。
    """
    if not val:
        return None
    try:
        if kind == "dict":
            return json.dumps(val, ensure_ascii=False, sort_keys=True)
        if kind == "set":
            return json.dumps(sorted(map(str, val)), ensure_ascii=False)
        return json.dumps(list(val), ensure_ascii=False)
    except (TypeError, ValueError):
        return None


def _orderfree_fp(kind: str, val: object) -> str | None:
    """排序无关指纹（抓「改名 + 改序」的 list/tuple/set 副本）。

    dict 不适用：键集相同而值不同的形态由 `_core_table_tier_fails` 的第 3 档判，
    拿"键排序串相同"当指纹会把「同样按五行取键的任意两张表」都判成副本（实测噪声）。
    """
    if not val or kind == "dict":
        return None
    try:
        return json.dumps(sorted(map(str, val)), ensure_ascii=False)
    except (TypeError, ValueError):
        return None


def _canonical_literal(node: ast.AST) -> str | None:
    """AST 字面量节点 → 归一化指纹（保留给既有调用方/测试）。"""
    kind = _lit_kind(node)
    if kind is None:
        return None
    try:
        val = ast.literal_eval(node)
    except Exception:
        return None
    return _canon_fp(kind, val)


def _module_table_fingerprints(py_file: Path) -> dict[str, list[str]]:
    """收集一个 .py 模块级 dict/list/tuple/set 字面量赋值：指纹 → [变量名]。"""
    out: dict[str, list[str]] = {}
    for name, (kind, val, _ln) in _literal_tables(py_file, module_level_only=True).items():
        fp = _canon_fp(kind, val)
        if fp:
            out.setdefault(fp, []).append(name)
    return out


def _literal_tables(py_file: Path, *, module_level_only: bool) -> dict[str, tuple[str, object, int]]:
    """文件里的容器字面量赋值 → {变量名: (类型, 值, 行号)}。

    覆盖 `X = {...}` 与注解式 `X: dict[str, str] = {...}`（AnnAssign），
    以及 list/tuple/set 三种容器——2026-10-09 之前只看 dict/list 的模块级赋值，
    `LIU_QIN = ("比肩", …)` 这类 tuple 副本与 7 处注解式赋值全在盲区里。
    """
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {}
    out: dict[str, tuple[str, object, int]] = {}

    def take(node: ast.AST) -> None:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            return
        value = node.value
        kind = _lit_kind(value) if value is not None else None
        if kind is None:
            return
        try:
            val = ast.literal_eval(value)
        except Exception:
            return
        if not val:
            return
        targets = (node.targets if isinstance(node, ast.Assign) else [node.target])
        for t in targets:
            if isinstance(t, ast.Name):
                out[t.id] = (kind, val, node.lineno)

    if module_level_only:
        for child in tree.body:
            take(child)
    else:
        for node in ast.walk(tree):
            take(node)
    return out


def _all_scope_literals(py_file: Path) -> dict[str, dict[str, list[str]]]:
    """全作用域 dict/list/tuple/set 字面量赋值：指纹 → {作用域名: [变量名]}。

    `_module_table_fingerprints` 只看模块级，看不见函数内的 dict 赋值
    （如 `def f(): sheng_wo = {"木": "水", ...}`）。这类副本与模块级副本同样危险：
    同份数据的第二份，改 core 漏改即口径分叉。故单独开一路全作用域收集。
    """
    out: dict[str, dict[str, list[str]]] = {}

    def walk(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                walk(child, getattr(child, "name", "<scope>"))
                continue
            if isinstance(child, (ast.Assign, ast.AnnAssign)):
                kind = _lit_kind(child.value) if child.value is not None else None
                if kind is not None:
                    fp = _canonical_literal(child.value)
                    if fp:
                        targets = (child.targets if isinstance(child, ast.Assign)
                                   else [child.target])
                        for t in targets:
                            if isinstance(t, ast.Name):
                                out.setdefault(fp, {}).setdefault(scope, []).append(t.id)
            walk(child, scope)

    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {}
    walk(tree, "<module>")
    return out


def _core_module_values(py_file: Path) -> dict[str, str]:
    """import 一个 core 模块，收集其模块级 dict/list 变量的运行值指纹。

    目的见 `check_core_tables_in_scope`：推导式派生的表（SHENG_WO/KE_WO 等）不是
    ast 字面量，只靠静态扫描会漏，故实际 import 一次取运行值补进指纹库。
    core 仅依赖 stdlib，import 无副作用。
    """
    out: dict[str, str] = {}
    for name, (kind, val) in _core_module_tables(py_file).items():
        fp = _canon_fp(kind, val)
        if fp:
            out[name] = fp
    return out


def _core_module_tables(py_file: Path) -> dict[str, tuple[str, object]]:
    """core 一个模块的真值表：{名: (类型, 值)}＝模块级字面量 ∪ 运行期反射值。

    两路并集的理由：推导式/字典推导派生的表（`SHENG_WO = {v: k for …}`）不是
    ast 字面量，静态扫描收不到，学科层反向复制它就漏检。
    """
    if str(_CORE_ROOT) not in sys.path:
        sys.path.insert(0, str(_CORE_ROOT))
    out: dict[str, tuple[str, object]] = {}
    try:
        mod = importlib.import_module(f"yishu_core.{py_file.stem}")
    except Exception:  # noqa: BLE001 —— 反射失败由 core_table_names() 统一判红
        return out
    for name in _module_level_names(py_file):
        val = getattr(mod, name, None)
        if isinstance(val, (dict, list, tuple, set, frozenset)) and val:
            kind = ("dict" if isinstance(val, dict) else
                    "list" if isinstance(val, list) else
                    "tuple" if isinstance(val, tuple) else "set")
            out[name] = (kind, set(val) if kind == "set" else val)
    return out


def _core_table_lib(*, refresh: bool = False) -> tuple[dict[str, tuple[str, object]], list[str]]:
    """内核真值库 `yishu_core.<module>.<NAME>` → (类型, 值) + 失败明细。"""
    if refresh:
        _CORE_LIB_CACHE.clear()
    if _CORE_LIB_CACHE:
        return _CORE_LIB_CACHE["v"]
    lib: dict[str, tuple[str, object]] = {}
    fails: list[str] = []
    files = [p for p in sorted(CORE_PKG.glob("*.py")) if p.stem != "__init__"]
    if not files:
        fails.append(f"内核真值库：{CORE_PKG} 下没有 .py —— 内容指纹门无法建立基线，"
                     "「无改名副本」的结论无效")
        return {}, fails
    for p in files:
        for name, kv in _core_module_tables(p).items():
            lib.setdefault(f"yishu_core.{p.stem}.{name}", kv)
    if not lib:
        fails.append("内核真值库取空（core 模块级没有任何 dict/list/tuple/set）——"
                     "改名副本门静默空转，本结果不可信")
    _CORE_LIB_CACHE["v"] = (lib, fails)
    return lib, fails


def _core_table_tier_fails(files: list[Path], *, module_level_only: bool) -> list[str]:
    """内容指纹四档：逐字节相同 / 改序相同 / 键集相同值不同 / 键为 core 子集。

    旧判据只有第 1 档（`fp in core_fps` 逐字节相等），于是「改名 + 改序」
    「改一格值」「取子集」三种改头换面的副本必然逃逸（2026-10-09 实测）。
    第 3/4 档是**报警**语义：键集取自五行/十二支这类公共取值域时，两张毫不相干的
    表也会键集相同，故第 3 档要求「多数值仍然相同」（≥1/2）才算副本改值，
    第 4 档要求交集值**全部**相同且键数 ≥3——现仓实测两档均 0 命中。
    """
    lib, fails = _core_table_lib()
    if not lib:
        return fails or ["内核真值库为空：内容指纹门没有基线，「无改名副本」不成立"]
    by_fp: dict[str, list[str]] = {}
    by_ofp: dict[str, list[str]] = {}
    dicts: list[tuple[str, dict]] = []
    for cn, (kind, val) in lib.items():
        fp = _canon_fp(kind, val)
        if fp:
            by_fp.setdefault(fp, []).append(cn)
        ofp = _orderfree_fp(kind, val)
        if ofp:
            by_ofp.setdefault((ofp), []).append(cn)
        if kind == "dict":
            dicts.append((cn, val))
    out: list[str] = list(fails)
    for p in files:
        rel = _truth_rel(p)
        for name, (kind, val, ln) in _literal_tables(p, module_level_only=module_level_only).items():
            if _core_allow(p, name):
                continue
            fp = _canon_fp(kind, val)
            if fp and fp in by_fp:
                out.append(f"{rel}:{ln}: 复制内核表 {name}"
                           f"（内容与 core {'、'.join(by_fp[fp])} 逐字节相同，唯一真值源在 core）")
                continue
            ofp = _orderfree_fp(kind, val)
            if ofp and ofp in by_ofp:
                out.append(f"{rel}:{ln}: 复制内核表 {name}"
                           f"（元素与 core {'、'.join(by_ofp[ofp])} 全同、仅顺序不同——"
                           "排序无关指纹命中）")
                continue
            if kind != "dict":
                continue
            ks = set(val.keys())
            hit3 = hit4 = None
            for cn, cv in dicts:
                cks = set(cv.keys())
                if ks == cks:
                    same = sum(1 for k in ks if cv[k] == val[k])
                    if same and same * 2 >= len(ks) and hit3 is None:
                        hit3 = (cn, same, len(ks))
                elif ks < cks and len(ks) >= 3 and all(cv.get(k) == val[k] for k in ks):
                    if hit4 is None:
                        hit4 = (cn, len(ks), len(cks))
            if hit3:
                out.append(f"{rel}:{ln}: 疑似改值复制内核表 {name}"
                           f"（键集与 core {hit3[0]} 完全相同、{hit3[1]}/{hit3[2]} 值相同而整体不同）")
            elif hit4:
                out.append(f"{rel}:{ln}: 疑似取自 core {hit4[0]} 的子集副本 {name}"
                           f"（{hit4[1]}/{hit4[2]} 键取值与 core 全同；唯一真值源在 core）")
    return out


def check_core_tables_in_scope() -> list[str]:
    """函数级 / 嵌套作用域的内核表副本检测（补 `check_core_table_renames` 盲区）。

    背景：模块级指纹门对 `def f(): sheng_wo = {...}` 这类**函数内**字面量 100% 失明，
    六爻 engine_chart.py 的五行生克 dict 即因此长期挂着（AGENTS.md §二 真值源清单
    里"五行生克"赫然在列）。本函数用 ast 遍历全部作用域补齐。
    """
    lib, fails = _core_table_lib()
    if not lib:
        return fails or ["内核真值库为空：作用域副本门没有基线"]
    core_fps: dict[str, list[str]] = {}
    for cn, (kind, val) in lib.items():
        fp = _canon_fp(kind, val)
        if fp:
            core_fps.setdefault(fp, []).append(cn)
    out: list[str] = list(fails)
    for p in _truth_source_files():
        rel = _truth_rel(p)
        for fp, scopes in _all_scope_literals(p).items():
            if fp not in core_fps:
                continue  # core 里没有这份内容 → 不是内核表的副本，不算违规
            src = "、".join(core_fps[fp])
            for scope, names in scopes.items():
                if scope == "<module>":
                    continue  # 模块级由 check_core_table_renames 负责，避免重复报
                if all(_core_allow(p, n) for n in names):
                    continue
                out.append(f"{rel}: 作用域 {scope}() 内复制内核表 {'、'.join(names)}"
                           f"（内容与 core {src} 逐字节相同，唯一真值源在 core）")
    return out


def _core_ganzhi_sequences() -> dict[str, str]:
    """内核干支全串（唯一真值源＝core 的 STEMS/BRANCHES 序列，反射取，不写字面量）。"""
    seqs: dict[str, str] = {}
    for mod_name, attr in (("symbols", "HEAVENLY_STEMS"), ("symbols", "EARTHLY_BRANCHES")):
        try:
            mod = importlib.import_module(f"yishu_core.{mod_name}")
        except Exception as exc:  # noqa: BLE001
            seqs[f"__import_error__{mod_name}"] = f"{type(exc).__name__}: {exc}"
            continue
        val = getattr(mod, attr, None)
        if isinstance(val, (list, tuple)) and val and all(isinstance(x, str) for x in val):
            seqs[attr] = "".join(val)
    return seqs


def _folded_strings(node: ast.AST) -> list[str]:
    """把一个表达式节点折叠成候选字符串：字面量、`+` 拼接、元素全为 str 的 list/tuple。

    Python 解析器会把相邻字面量 `"甲乙" "丙丁"` 合成**一个** Constant，所以隐式相邻
    拼接天然被第一条覆盖；显式 `+` 与"列表分段落"要靠后两条。
    """
    out: list[str] = []
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        out.append(node.value)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _folded_strings(node.left), _folded_strings(node.right)
        out.extend(a + b for a in left for b in right)
    elif isinstance(node, (ast.List, ast.Tuple)):
        parts = [_folded_strings(e) for e in node.elts]
        if len(parts) > 1 and all(parts):
            acc = [""]
            for p in parts:
                acc = [a + q for a in acc for q in p]
            out.extend(acc)
    return out


def check_core_string_tables() -> list[str]:
    """干支序列字符串字面量唯一性（core/yishu_core/symbols.py 为唯一真值源）。

    上两条门只比对 dict/list/tuple/set 字面量：裸字符串形式的完整十天干串 / 完整十二地支串
    既不匹配同名正则，也不是可指纹的 dict —— 两层门同时放行。且同一函数里常出现
    "一半用 core 一半手写串"（如某科 chart.py 手写 stems 串、同行却用 core
    EARTHLY_BRANCHES），是最容易漏改半截的形态。

    2026-10-09 实测的绕过形态：`"甲乙丙丁" + "戊己庚辛壬癸"`（拆两段拼接）对旧的
    逐行正则完全隐形。现改为 **AST 折叠后与 core 反射出的全串比对**（拼接归一化），
    本函数自身也走 `_truth_source_files()`，故此处不写示例字面量。
    """
    seqs = _core_ganzhi_sequences()
    errs = {k: v for k, v in seqs.items() if k.startswith("__import_error__")}
    if errs or not [k for k in seqs if not k.startswith("__")]:
        return [f"干支序列门：反射 core 序列失败（{errs}）——「无复制串」的结论无效"]
    targets = {v: k for k, v in seqs.items() if not k.startswith("__")}
    fails: list[str] = []
    for p in _truth_source_files():
        rel = _truth_rel(p)
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, UnicodeDecodeError, OSError):
            continue
        line_owner = {ln: name for name, (_k, _v, ln)
                      in _literal_tables(p, module_level_only=False).items()}
        for node in ast.walk(tree):
            for s in _folded_strings(node):
                seq = targets.get(s)
                if seq is None:
                    continue
                ln = getattr(node, "lineno", 0)
                owner = line_owner.get(ln)
                if owner and _core_allow(p, owner):
                    continue
                fails.append(f"{rel}:{ln}: 复制内核干支序列 {s}"
                             f"（＝ core/yishu_core/symbols.py::{seq}；拆段拼接同样命中）")
    return fails


def check_core_table_renames() -> list[str]:
    """改名副本检测：学科层出现与 core 真值表内容相同的模块级字面量即视为复制。

    背景：历史事故形态之一是把 core 表换名复制（如 XUN_KONG → EMPTY_DEATH），
    同名检测对此失明，故增加内容指纹比对。判据分四档，见 `_core_table_tier_fails`。
    """
    return _core_table_tier_fails(_truth_source_files(), module_level_only=True)


def _tail(out: str, n: int = 3) -> str:
    return "\n".join(out.strip().splitlines()[-n:])


# 同源验收的通过口令（`tools/verify_web_parity.py` 自己打印的那一行）
PARITY_PASS = re.compile(r"同源验收通过（正例\s*(\d+)\s*例\s*\+\s*负例\s*(\d+)\s*例）")
# eval.py 的分数行：`=== tune [strict] 平均分 = 96.8%  (n=20，…) ===`
EVAL_SCORE = re.compile(r"^===\s*(\w+)\s*\[strict\]\s*平均分\s*=\s*([\d.]+)%\s*\(n=(\d+)")
EVAL_SECTION = re.compile(r"^===\s*(\w+)\s*·\s*(\w+)\s*===")


def _load_script_module(rel_path: str, module_name: str):
    """按路径加载 tools/ 下的脚本，只为读它的用例常量（tools/ 不是包）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(module_name, ROOT / rel_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_parity_verdict(code: int, out: str) -> list[str]:
    """[7c] 判据：退出码 0 只证明脚本跑到了末尾，不证明它比对过任何用例。

    2026-10-09 实跑复现：本门原实现**只看退出码**，而 `tools/verify_web_parity.py`
    当时已被"两科收缩"那笔提交删成没有 `main()` 的空壳（73 行、退出 0、零输出），
    于是门打印 `√ 同源验收（）`——括号里是空的。现在三条都要断言：
      ① 有输出；② 报出通过口令；③ 口令里的正/负例数 == **被调脚本自己的**
         `len(CASES)` / `len(NEG_CASES)`（从模块常量现读，此处不写死 4，
         否则用例被删光还会"对上号"）。
    """
    if code != 0:
        return [f"同源验收退出码 {code}：\n{_tail(out, 6)}"]
    if not out.strip():
        return ["同源验收退出码 0 但 stdout/stderr 全空——脚本是空壳（没有 main/assert）"
                "也会长这样；判红（AGENTS.md §四.8）"]
    try:
        mod = _load_script_module("tools/verify_web_parity.py", "yi_parity_for_gate")
    except Exception as exc:  # noqa: BLE001
        return [f"同源验收：无法加载 tools/verify_web_parity.py 读取用例常量"
                f"（{type(exc).__name__}: {exc}）——断言用例数的前提没了，判红"]
    n_pos, n_neg = len(getattr(mod, "CASES", ())), len(getattr(mod, "NEG_CASES", ()))
    if not n_pos or not n_neg:
        return [f"同源验收：被调脚本的常量为空（CASES={n_pos}、NEG_CASES={n_neg}）——"
                "正例/负例任一侧被删空，比对集就不成立"]
    m = PARITY_PASS.search(out)
    if not m:
        return ["同源验收退出码 0，但输出里没有通过口令"
                f"「同源验收通过（正例 {n_pos} 例 + 负例 {n_neg} 例）」——"
                "只判退出码会被空壳蒙过（§四.8 同一病灶）"]
    got_pos, got_neg = int(m.group(1)), int(m.group(2))
    fails: list[str] = []
    if got_pos != n_pos or got_neg != n_neg:
        fails.append(f"同源验收计数对不上：脚本自报 正例 {got_pos}/负例 {got_neg}，"
                     f"而其模块常量为 CASES={n_pos}、NEG_CASES={n_neg}"
                     "——有用例没被跑到，或跑的是别的一套")
    if "覆盖检查：站点挂载" not in out:
        fails.append("同源验收未打印「覆盖检查：站点挂载 …」——覆盖恒等断言（正例集合 ≡ "
                     "站点挂载集合）没被执行")
    return fails


def check_eval_scores(out: str) -> list[str]:
    """[7d] 判据：每一科都必须**真的**报出 tune 与 holdout 两个分数。

    `tools/eval.py` 只转发各科 evaluate.py；原实现只看退出码，于是
    「把某科的 evaluate.py 删掉」在 eval.py 里被记成 `return 0, "无 evaluate.py"`、
    在 [7d] 里也照样打勾（评测器消失＝零报警）。现在按学科×split 逐个点名。
    """
    fails: list[str] = []
    seen: dict[str, set[str]] = {}
    cur: str | None = None
    for line in out.splitlines():
        m = EVAL_SECTION.match(line.strip())
        if m:
            cur = m.group(1)
            continue
        s = EVAL_SCORE.match(line.strip())
        if s and cur:
            # group(1) 是 split 名（tune/holdout），group(2) 是分数——原实现取错格，
            # 于是把分数当 split 名存进去，`"tune" in got` 恒不成立，两科永远报「没出分」。
            seen.setdefault(cur, set()).add(s.group(1))
    for disc in ALL_DISCIPLINES:
        got = seen.get(disc) or set()
        missing = [sp for sp in ("tune", "holdout") if sp not in got]
        if missing:
            fails.append(f"{disc}：没有真的出 {'、'.join(missing)} 分数"
                         "（eval.py 转发失败或该科 evaluate.py 不在位——"
                         "「无 evaluate.py」不等于通过）")
    if not seen:
        fails.append("各科评测一览：整段输出里一个分数都没有——"
                     "eval.py 空转也会打勾，判红")
    return fails


def verdict_audit_case_count() -> int:
    """[1c]/[1d] 标签里的"跑几份真实报告"——从 `verdict_audit.CASES` 现算。

    2026-10-09：文档与标签里手写的"10 份/10 例"在两科收缩后全是过期读数
    （实际 3 例；`verdict_consumption` 另加 5 例样本＝8）。凡计数一律现算插值。
    """
    try:
        mod = _load_script_module("tools/verdict_audit.py", "yi_verdict_audit_for_label")
        return len(getattr(mod, "CASES", ()))
    except Exception:  # noqa: BLE001 —— 标签取不到真值就退回"若干"，不写假数字
        return 0


def source_readings_count() -> int:
    """[1l] 标签里的书源解读文档篇数——从磁盘现数（2026-10-09：原写死"54 篇"）。"""
    try:
        return len(sorted((ROOT / "docs" / "source-readings").glob("*.md")))
    except OSError:
        return 0


def faithfulness_corpus_count() -> int:
    """[6] 标签里的忠实度语料例数——从 `CORPUS_CASES` 现算（原写死"12 例"）。"""
    try:
        mod = _load_script_module("tools/report_faithfulness.py", "yi_faith_for_label")
        return len(getattr(mod, "CORPUS_CASES", ()))
    except Exception:  # noqa: BLE001
        return 0


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
                    help=f"全量：{len(ALL_DISCIPLINES)} 科案例评测（tune/holdout）+ 六爻黑箱回归 + "
                         "网页/本地同源验收 + pytest tests（慢）")
    ap.add_argument("--raise-render", action="store_true",
                    help="以本次两科 render MD 指纹覆盖基线 data/golden/render_digest.json"
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

    def gate_sub(name: str, cmd: list[str], label: str, *, fast: bool = True,
                 expect: str | None = None, empty_is_fatal: bool = False):
        """跑一个子进程门。

        `expect`：**stdout 必须出现的口令**（正则）。只判退出码的门可以被"空壳化"绕过——
        2026-10-09 实跑：`tools/verify_web_parity.py` 被删成没有 `main()` 的空壳后
        退出码 0、stdout/stderr 全空，[7c] 照样打勾并打印 `√ 同源验收（）`。
        `empty_is_fatal`：输出全空即判红（"什么都没做"永远不等于"做完了且没问题"）。
        """
        _register(name)
        if only is not None and name not in only:
            return
        argv = list(cmd)
        if fast:
            argv.insert(1, "--fast") if cmd[0].endswith("check.py") else None
        code, out = _run_py(argv, label=label)
        if code == 0:
            if empty_is_fatal and not out.strip():
                failures.append(f"{label}：退出码 0 但 stdout/stderr 全空——"
                                "子门空转（被删空/提前 return 也长这样）")
                print(f"  × {label}（退出 0 但零输出＝空转）")
                return
            if expect and not re.search(expect, out):
                failures.append(f"{label}：退出码 0 但输出里没有口令 /{expect}/——"
                                "只判退出码会被空壳蒙过（§四.8 同一病灶）")
                print(f"  × {label}（退出 0 但未报出口令）")
                print(f"      …{_tail(out)}")
                return
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
         "两科 scripts 模块均可独立导入（import 期不得炸、也不得静默降级）")

    print("\n[1b] 命名与断语规范（AGENTS.md §三: 文件名无版本号 + 断语进 data JSON）")
    gate("filenames", check_filenames(), "文件名无版本号标记")
    gate("verdict_literals", check_verdict_literals(), "断语/引文外置到 data JSON（文本粗筛）")

    # 文档死链门：文档里点名的仓库内路径（`docs/xxx.md`、`dev_tools/xxx.py`）
    # 必须真的存在，且必须**已被 git 追踪**（本机未跟踪的文件会让门本地绿、干净 clone 红）。
    # 2026-10-06 实测挖出 7 处真死链，其中 4 处是学科工具目录
    # 早已从 tools/ 迁到 dev_tools/、文档却还写旧路径——纯靠人读是查不出来的。
    # 口令断言：必须报出「扫描活跃文档 N 份」且 N>0（扫 0 份不等于全绿）。
    print("\n[1b-2] 文档死链（活跃文档点名的仓库内路径必须存在且已入库）")
    gate_sub("doc_deadlinks",
             ["tools/check_doc_deadlinks.py"],
             "文档死链（活跃文档内仓库路径引用均可解析、且引用目标已入库）",
             expect=r"扫描活跃文档 [1-9]\d* 份")

    # [1b-3] 符号级指认回验：`[1b-2]` 只判「路径是否存在」，看不见
    # 「文档写 `mod.py::NAME`，而那个符号从来不存在」——AGENTS.md §二 曾把
    # `ming_tables.py::NAYIN_XIANGGE` 当已落实实体指认（实测全仓从未存在）。
    print("\n[1b-3] 文档符号级指认回验（路径存在≠符号存在）")
    gate_sub("symbol_claims",
             ["tools/check_symbol_claims.py"],
             "文档符号级指认均可解析到真实符号（AST 判，删除公告类语境按窗口跳过）",
             expect=r"CHECK PASS")

    # [1b-4] 文档 HTML 渲染在位：PLAN_DOCS 清单是"人敲一次就废"的典型——
    # 里面躺着死路径（docs/NEW-DISCIPLINES.md 实测早已迁 archive/）而旧实现
    # 只打印「× 跳过（不存在）」再 return 0，等于把人敲的入口做成假绿。
    print("\n[1b-4] 文档渲染清单在位（PLAN_DOCS 全部存在且可渲染）")
    gate_sub("doc_html",
             ["tools/doc_html.py", "--check", "--all-plan"],
             "文档 HTML 渲染清单（规划类文档全部在位且跑得通）",
             expect=r"DOC-HTML CHECK PASS")

    # 黑箱取证门：不看代码长什么样，只看用户读到什么（verdict_audit.py 的说明）
    # 比上面的文本粗筛准——粗筛会把 docstring/help 当成断语，取证门不会漏真断语。
    # 要跑 len(verdict_audit.CASES) 份真实报告（2026-10-09 起从常量现算，见下面 label），
    # 故归到 --full 档。
    print("\n[1c] 断语外置取证（跑真实报告，反查未进 data/*.json 的结论句）")
    gate_sub("verdict_audit",
             ["tools/verdict_audit.py", "--strict"],
             f"断语外置取证（跑 {verdict_audit_case_count()} 份真实报告；"
             "白名单外的未外置句判失败）", fast=False)

    # 语料消费审计（verdict_audit 的反向，SYS-REVIEW #1）：跑报告统计语料池
    # 覆盖率，零消费键打印明细。抽样覆盖有限（主题键合法不触发），只报告不判败；
    # 发现整块死语料（如某科命宫格局事件）从手工排查变成机械可见。
    print("\n[1d] 语料消费审计（同一批报告反查语料池覆盖率；报告零消费键）")
    gate_sub("verdict_consumption",
             ["tools/verdict_consumption.py"],
             "语料消费审计（报告制，零消费键可见）", fast=False)

    # 能力矩阵锁（SYS-REVIEW #3）：llms.txt 的权威矩阵必须与
    # tools/build_web.py 的 DISCIPLINE_META 一致，防「文档 / 网页口径漂移（均为八字+六爻）」。
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

    print("\n[1h] 深链短键锁 + 字段活性（短键 ⊆ 白名单，白名单里每个字段都真被消费）")
    gate("deeplink_keys", check_deeplink_keys(), "深链短键均指向有效请求字段")
    gate("field_liveness", check_field_liveness(),
         "请求字段无死字段（argv 类必进某科命令行、display 类必写明用途）")

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

    # 案例引文逐字性（2026-10-06m）：[1j] 只管「构建器重跑==入库」，管不了案例集里
    # 人工/临时脚本写入的 source_quote——QTBJ 批 9 条压缩改写/拼接引文就是这样静默
    # 入库且全门 EXIT=0 的。本门对每条引文要求书源逐字子串（剥 wikitext 标记+去空白），
    # 书源不在库的书逐条披露（不静默跳过）；内置 --selftest 负例自证。
    print("\n[1k] 案例引文逐字性（data/cases 每条 source_quote 必须是书源逐字子串）")
    gate_sub("case_quotes", ["tools/check_case_quotes.py"],
             "案例引文逐字性（压缩/拼接/跨段引文判败；书源不在库逐条披露）")

    # 书源深度解读文档门（2026-10-08 挂门）：docs/source-readings/ **全部**文档逐条要求
    # （篇数不写死在注释里，由下面 label 从磁盘现数——2026-10-09 原注释写"五十余篇"、
    #  label 写"54 篇"，实测 29 篇，数字比现状落后一轮就变成文档里的假事实）。
    # 引文 ⊆ 书源、OPT 表六列齐、ID 前缀与文件名同构。此前该门**只被 --selftest 引用**、
    # 真扫描从未排进 check（"写了门不跑"＝死代码，AGENTS.md §四.8 同一病灶）。
    # 实测 2 秒，故进默认档。
    print("\n[1l] 书源解读文档（引文逐字 + OPT 表结构 + ID 前缀一致）")
    gate_sub("source_readings", ["tools/check_source_readings.py"],
             f"书源解读文档门（{source_readings_count()} 篇，篇数现数："
             "引文逐字回指书源，OPT 行六列齐、ID 前缀同文件名）")

    # 纳音使用审计（OPT-shenfeng_tongkao_dz-02；2026-10-07 创建后未挂门，死代码）：
    # NAYIN 只作排盘取值/叙述取象，不得参与吉凶判据。静态扫 nayin 消费点 + 动态反事实
    # （整表替换伪值后跑 eval，读数不变即旁证）。自带注入生效负例自证（铁律四.5）。
    print("\n[1m] 纳音使用审计（NAYIN 只作取值/叙事，不参与吉凶判据；静态+动态反事实双通道）")
    gate_sub("nayin_audit", ["tools/audit_nayin_usage.py"],
             "纳音使用审计（静态分类+动态反事实双通道；含注入生效负例自证）",
             fast=False)

    # [1n] 已随大六壬学科移除（kemu purity 仅服务于 liuren）

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

    # 门自证（2026-10-08）：负例自证写在文档里、却没被任何地方执行，等于没有负例。
    # AGENTS.md §四.8 的实踩教训（死链门"全绿"其实是豁免吞掉负例）只有在**每次跑**时
    # 才防得住，故把四把自带 --selftest 的门排进默认档，而不是留在 CHANGELOG 的叙述里。
    print("\n[2b] 门自证（负例必须被判红、扫空必须判红；漏挂即死代码）")
    # 段名与四个子门名一一登记：`--only gate_selftest` 这类"选了段名、子门名对不上"
    # 的写法必须报错列出可用项，而不是静默跳过后打印"全部通过"（本文件的设计口径第 1 条）。
    # 第四列 expect：子门必须**报出自证通过的口令**——只看退出码的话，
    # 一个把断言删光的 --selftest 照样退出 0（[7c] 的同源验收空壳就是这么混过去的）。
    _SELFTESTS = (
        ("gate_selftest_isolation", ["tools/case_isolation_check.py", "--selftest"],
         "案例隔离门自证（显式路径/组合名判红、书源 slug 不误报、扫空判红）",
         r"SELFTEST PASS"),
        ("gate_selftest_case_quotes", ["tools/check_case_quotes.py", "--selftest"],
         "引文逐字门自证（尾拼/压缩/跨段三负例）",
         r"负例全被抓、正例通过"),
        ("gate_selftest_source_readings", ["tools/check_source_readings.py", "--selftest"],
         "书源解读文档门自证（编造引文/空壳/挂错著作判红）",
         r"SELFTEST PASS"),
        ("gate_selftest_crosscheck", ["tools/crosscheck_source.py", "--selftest"],
         "书源对勘门自证（同段自比=1.0、异书互比判对不上；底料为两科在库书源）",
         r"SELFTEST PASS"),
        ("gate_selftest_doc_deadlinks", ["tools/check_doc_deadlinks.py", "--selftest"],
         "文档死链门自证（裸引用必咬、语境豁免精准、docs 子目录递归生效、未入库目标判红）",
         r"SELFTEST PASS"),
        ("gate_selftest_doc_html", ["tools/doc_html.py", "--selftest"],
         "文档渲染清单门自证（PLAN_DOCS 死路径、点名不存在仍退 0 两种都必须被抓）",
         r"SELFTEST PASS"),
        ("gate_selftest_symbol_claims", ["tools/check_symbol_claims.py", "--selftest"],
         "符号指认门自证（临时合成文档注入 1 真 1 假指认：假的必判红、真的不误报）",
         r"SELFTEST PASS"),
        ("gate_selftest_truth_source", ["tests/test_gate_truth_source.py"],
         "内核真值源门自证（反射名单/tuple/注解/拆串拼接/内容四档，含不误报侧）",
         None),
        ("gate_selftest_faithfulness", ["tools/report_faithfulness.py", "--selftest"],
         "报告忠实度门自证（引文段后的越界断言必须被抓、冒号形态/否定句不漏不假阳）",
         r"SELFTEST PASS（正例 [1-9]\d* 例 \+ 负例 [1-9]\d* 例）"),
        ("gate_selftest_verdict_audit", ["tools/verdict_audit.py", "--selftest"],
         "断语外置取证门自证（表格断语、四字短句断语都必须被抓）",
         r"SELFTEST PASS（正例 [1-9]\d* 例 \+ 负例 [1-9]\d* 例）"),
    )
    if section(*[n for n, _, _, _ in _SELFTESTS]):
        for _st_name, _st_cmd, _st_label, _st_expect in _SELFTESTS:
            if _st_cmd[0].startswith("tests/"):
                # 真值源门的负例自证住在 tests/（要注入临时扫描根，不能往仓库植文件）。
                # 但选择器照样要认：旧实现这一段**不看 only**，于是
                # `--only gate_selftest_faithfulness` 会连带跑一条与被选门无关的
                # pytest（2026-10-09 实测多跑一项），既拖慢单门复现，也可能用
                # 别门的绿掩盖本门没跑。
                if only is not None and _st_name not in only:
                    continue
                code, out = _run_py(["-m", "pytest", _st_cmd[0], "-q"], label=_st_label)
                if code == 0:
                    print(f"  √ {_st_label}")
                else:
                    failures.append(f"{_st_label} 退出码 {code}")
                    print(f"  × {_st_label}")
                    print(f"      …{_tail(out)}")
            else:
                gate_sub(_st_name, _st_cmd, _st_label, fast=False, expect=_st_expect)

    for disc in SMOKE_DISCIPLINES:
        print(f"\n[{SMOKE_DISCIPLINES.index(disc) + 3}] {disc} 质量门"
              f"{'（含案例评测）' if args.full else '（快速：指纹+冒烟）'}")
        gate_sub(disc, [f"disciplines/{disc}/dev_tools/check.py"], disc, fast=not args.full)

    print("\n[5] 两科行为指纹（golden 基线：重构只准改结构，不准改行为）")
    for disc in ALL_DISCIPLINES:
        g = ROOT / "disciplines" / disc / "dev_tools" / "golden.py"
        if not g.is_file():
            continue
        gate_sub(f"golden_{disc}", [str(g.relative_to(ROOT))], f"{disc} 行为指纹", fast=False)

    print("\n[6] 六爻（迁移前旧实现：冒烟 + 四段契约端到端；--full 加黑箱回归）")
    gate_sub("liuyao", ["disciplines/liuyao/tests/smoke_test.py"], "六爻冒烟", fast=False)
    # 报告忠实度审计：narrate 正文断言 vs 引擎结构化输出，出现 invented/contradicted 即失败。
    # A10 已落地：原只跑单例 --demo（证明不了换个起卦法/换类问事时叙述模板仍不越界），
    # 现跑内置语料（例数从 `CORPUS_CASES` 现算，见 label；不再手写"12 例"）。
    gate_sub("faithfulness", ["tools/report_faithfulness.py", "--corpus"],
             f"报告忠实度（{faithfulness_corpus_count()} 例语料：narrate 断言 vs 引擎结构）",
             fast=False)
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

    # render 段是全库唯一无内容保护的段落（架构评审 A6）：两科 golden 均不含 render，
    # 根门原本只判"产物存在"。这里对**用户真正读到的统一报告**做契约级结构断言：
    # 口径声明句与反馈尾注必须在位，禁用断言词必须为 0。
    if section("report_contract"):
        print("\n[6b] 报告契约（render 段结构断言 · 两科逐科：口径句/反馈尾注在位，禁用断言词为 0）")
        from yishu_core.report.request import MD_FEEDBACK_NOTE, REPORT_FOOTER  # noqa: E402
        rc_dir = ROOT / "tools" / "scratch" / "report_contract"
        rc_dir.mkdir(parents=True, exist_ok=True)
        # 每科一条最小请求（覆盖两科 render 路径）；经 --request 传入，避免逐科拼 flag。
        cases = (
            {"discipline": "liuyao", "question": "占合同能否成交", "mode": "time",
             "datetime": "2026-09-23 10:00"},
            {"discipline": "ming", "question": "命局", "datetime": "1990-05-20 10:30", "gender": "男"},
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

        # render 段内容指纹（A6 大动血）：MD 逐字节哈希，两科各一份，漂移即红。
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
                    "what": "两科 render 段 Markdown 内容指纹基线（逐字节，含反馈尾注）",
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
        gate("report_contract", problems, "报告契约（两科：口径句/尾注在位；无禁用词；关键字段必达）")

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
            # 两子门同样带口令断言：build_web 打印「镜像文件 N 个」（N 必须 >0），
            # check_web_site 打印「√ 站点自检全部通过」——只看退出码的话，
            # "构建器改了输出格式后什么都不镜像"这种空转不会被发现。
            code, out = _run_py(["tools/build_web.py", "--outdir", str(site_dir)],
                                label="站点构建")
            m = re.search(r"镜像文件\s*(\d+)\s*个", out or "")
            if code == 0 and m and int(m.group(1)) > 0:
                print(f"  √ 站点构建（镜像 {m.group(1)} 个文件；一次性目录，不写工作区）")
            else:
                failures.append("站点构建"
                                + ("：退出 0 但没报出「镜像文件 N 个」或 N=0——空构建"
                                   if code == 0 else f" 退出码 {code}"))
                print("  × 站点构建")
                print(f"      …{_tail(out)}")
            code, out = _run_py(["tools/check_web_site.py", "--site", str(site_dir)],
                                label="站点自检")
            if code == 0 and "站点自检全部通过" not in (out or ""):
                failures.append("站点自检：退出 0 但未报出「站点自检全部通过」——子门空转")
                print("  × 站点自检（退出 0 但未报出口令）")
                print(f"      …{_tail(out)}")
            elif code == 0:
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
        pfa = check_parity_verdict(code, out)
        if pfa:
            failures.extend(pfa)
            print("  × 同源验收")
            for f in pfa:
                print(f"      · {f}")
            print(f"      …{_tail(out, 6)}")
        else:
            print("  √ 同源验收（" + (out.strip().splitlines() or [""])[-1] + "）")

    # 各科案例评测一览：把 `tools/eval.py` 纳入门（HANDOFF §四.6 挂账）。
    # 它只转发各科 evaluate.py（不写第二套给分逻辑），故是"汇总可见性"门。
    # 2026-10-09 起不再容忍"无 evaluate.py 就跳过"：eval.py 默认对缺失评测器的学科
    # 判败（要豁免须显式 --allow-missing），本门另加"每科都真出了 tune/holdout 两个
    # 分数"的断言——否则删掉 evaluate.py 也能让 [7d] 绿。
    if section("eval_overview") and (args.full or only is not None):
        print("\n[7d] 各科案例对齐分一览（tools/eval.py 转发各科 evaluate；非预测率）")
        code, out = _run_py(["tools/eval.py"], label="各科评测一览")
        if code != 0:
            failures.append("各科评测一览转发失败")
            print("  × 各科评测一览")
            print(f"      …{_tail(out, 6)}")
        else:
            efa = check_eval_scores(out)
            if efa:
                failures.extend(efa)
                print("  × 各科评测一览（退出 0 但有学科没出分）")
                for f in efa:
                    print(f"      · {f}")
            else:
                print("  √ 各科评测一览（"
                      + "、".join(f"{d} tune+holdout" for d in ALL_DISCIPLINES) + "）")

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
