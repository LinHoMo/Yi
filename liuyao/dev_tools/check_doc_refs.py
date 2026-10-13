# -*- coding: utf-8 -*-
"""文档/注释里的**活引用**必须指向存在的文件（历史登记散文除外）。

为什么需要它（2026-10-10）：CHANGELOG 与代码注释里长期存在「见 HANDOFF 四·三」
「可经 `python tools/check_source_readings.py …` 回验」这类指针，而 HANDOFF.md、
tools/、docs/source-readings/ 都随仓库扁平化删除了——照着跑必然失败，
却没有任何东西会发现。本轮已把这些活引用改指真路径，本器负责让它不再长回来。

口径（宁可少判，也不做逼人删注释的假红门）：
  · 只查「看起来是路径」的反引号串：含 `/` 且以 .md/.py/.json/.txt/.css/.html 结尾；
  · 相对学科根解析，允许 `<占位符>`、绝对 URL、`outputs/…` 与 `scratch/…` 这类
    运行时产物目录（gitignore，本就不该存在）；
  · **不查 CHANGELOG**：老条目是登记时点的事实（文件头已声明一字未改），
    历史里提到已删除的根文档不是 bug；
  · **【照八字科第一百六十六批·同步判据不同文字】`.json` 数据文件里的路径字样同样扫**：
    本器此前只走 `.md`/`.py`，于是 `data/rules/rule_registry.json` 一类**声明载体**里
    写的死指针门永远看不见（八字科实抓到三条从未存在的 `tests/*.py` 幽灵指针）。
    数据 JSON 里 `"impl": "file.py#symbol"` 这类本就是**可执行契约**（由 [12] 逐条回指），
    扫得到只会更严，不误伤：字段值以 `/` 分段且带已知扩展名的串本来就该在盘上。
    `data/cases/`（案例正文含内嵌 markdown 与书文）与 `data/sources/`（古籍底本）不扫，
    否则会把史料当声明造出假红——反向激励删史料。
  · 找不到 → 判红并点名出处行号。

    python dev_tools/check_doc_refs.py
    python dev_tools/check_doc_refs.py --selftest
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
import pathlib
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parent          # 学科根之外的仓库根：注释里 `bazi/...` 这类同仓兄弟学科引用为真

# 反引号内、含 / 且带已知扩展名的串
REF = re.compile(r"`([A-Za-z0-9_\-./\u4e00-\u9fff]+\.(?:md|py|json|txt|css|html))(?![A-Za-z])`")
# 2026-10-10 补：**没打反引号的路径**同样是活引用。本器原先只认反引号内串，
# 于是 `scripts/timing.py` 头部「【甲】《易隐》应期四诀（docs/source-readings/yiin_dz.md …）」
# 这条指向扁平化时已删除目录的指针，一路以「84 条全可达」的身份躲过了门。
# 只认以真实顶层目录开头的串，避免把散文里的 `a/b.md` 之类速记当声明。
BARE = re.compile(r"(?<![\w/.-])((?:docs|scripts|data|references|dev_tools|core|tests"
                  r"|bazi|liuyao)/[A-Za-z0-9_\-./\u4e00-\u9fff]*"
                  r"\.(?:md|py|json|txt|css|html)(?![A-Za-z]))")
SKIP_MARK = ("<", "…", "...", "http://", "https://")
# 运行时产物目录：本就不入库，存在性不检查
RUNTIME_DIRS = ("outputs/", "scratch/", "logs/", "assets/")
# 【第一百六十六批】上述目录里的**文件本身**也不作为声明载体扫描：RUNTIME_DIRS 的旧口径
# 只豁免「指向这些目录的引用」，但 scratch/ 下的一次性探针脚本里写死的旧路径字符串
# （查 git 历史用）会被扫成死指针——那些不是对仓库的声明，判红等于逼工作脚本绕着写。
SKIP_ROOTS = ("outputs/", "scratch/", "logs/")
# 历史登记文档：其中提到的旧路径是登记时点事实，不判
EXEMPT = ("docs/CHANGELOG.md",)
# 本器自己的源文件里有负例样本的字面死引用，不能自查
SELF = "dev_tools/check_doc_refs.py"
SUFFIXES = (".md", ".py", ".json", ".txt", ".css", ".html")
# 「曾在四处各存一份…」「同指该不存在的文件」「负例：dev_tools/nope.py」这类行是**病历与自测样本**，
# 不是可照跑的指针。把它们判红，等于逼文档把事故记录删干净——那是反向激励。
HISTORY = re.compile(r"曾[并未已在经]|勘误|不采此说|已失效|原有|原挂|已删除|已随|随仓库|不存在|改指|作废|"
                     r"无此文件|负例|造的|自测|selftest")
SKIPPED_HISTORY: list[str] = []
# 故意编造的负例文件名（各门 selftest 里造的靶子）不是对仓库的声明
NEGATIVE = ("__does_not_exist__", "definitely_missing", "nope.py", "_selftest_")
# 「step3/4/5.py」这类散文速记：出现纯数字段就不是一个真路径
SHORTHAND = re.compile(r"(^|/)\d+(?=/|\.|$)")


def _resolves(rel: str) -> bool:
    """相对学科根或仓库根解析；容忍书写省略前缀（同名文件存在即认）。"""
    clean = rel.lstrip("./")
    for base in (DISC, ROOT):
        if (base / clean).exists():
            return True
    name = clean.split("/")[-1]
    return any(p.name == name for p in DISC.rglob(f"*{name}") if p.is_file())


def scan() -> tuple[list[str], int]:
    problems: list[str] = []
    examined = 0
    # examined 是"本次扫描"的局部量，SKIPPED_HISTORY 却是模块级——不每轮清空的话，
    # --selftest 里连着调三次 scan() 会把跳过数报成三倍（实测 57 vs 真值 21）。
    SKIPPED_HISTORY.clear()
    for p in sorted(DISC.rglob("*")):
        if not p.is_file() or p.suffix not in (".md", ".py", ".json"):
            continue
        parts = set(p.parts)
        if "__pycache__" in parts:
            continue
        rel_to_disc = str(p.relative_to(DISC)).replace("\\", "/")
        if any(rel_to_disc.startswith(s) for s in SKIP_ROOTS):
            continue      # 一次性工作脚本所在目录：其中的路径字符串不是对仓库的声明
        if any(rel_to_disc.endswith(e) for e in EXEMPT) or rel_to_disc == SELF:
            continue
        if rel_to_disc.startswith("data/cases/") or rel_to_disc.startswith("data/sources/"):
            continue      # 语料与古籍底本：正文是案例数据/书文（含内嵌 markdown），不是路径声明载体
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = text.splitlines()
        for n, line in enumerate(lines, 1):
            found: list[str] = []
            for m in REF.finditer(line):
                found.append(m.group(1).strip())
            for m in BARE.finditer(line):        # 反引号外的裸路径同样算声明
                s = m.group(1)
                if s not in found:
                    found.append(s)
            for ref in found:
                if HISTORY.search(line) or HISTORY.search(lines[n - 2] if n >= 2 else ""):
                    SKIPPED_HISTORY.append(f"{rel_to_disc}:{n} → {ref}")
                    continue
                if any(k in ref for k in NEGATIVE):
                    continue
                if any(k in ref for k in SKIP_MARK):
                    continue
                if not ref.endswith(SUFFIXES):
                    continue
                if "/" not in ref and not ref.startswith("."):
                    continue      # 裸文件名（如 SKILL.md）不构成本器的路径声明
                if ref.startswith(RUNTIME_DIRS):
                    continue
                if SHORTHAND.search(ref):
                    continue      # 「step3/4/5.py」一类散文速记，不是路径声明
                examined += 1
                if not _resolves(ref):
                    problems.append(f"{rel_to_disc}:{n} 指向不存在的文件 → {ref}")
    return problems, examined


def selftest(problems: list[str]) -> None:
    """负例自证：造一个含死引用的临时文件，本器必须抓到。"""
    tmp = DISC / "references" / "_selftest_deadref.md"
    real_md = sorted((DISC / "references").glob("*.md"))
    real_py = sorted((DISC / "scripts").glob("*.py"))
    if not real_md or not real_py:
        problems.append("负例自证无法执行：本学科没有可借的真路径样本")
        return
    ok_a = "references/" + real_md[0].name
    ok_b = "scripts/" + real_py[0].name
    tmp.write_text("见 `docs/zz_probe_deadref_a.md` 与 `dev_tools/zz_probe_deadref_b.py`。\n"
                   "裸路径也要抓（docs/zz_probe_deadref_c.md 无反引号）。\n"
                   f"真路径不得误报：{ok_a} 与 {ok_b} 都在。\n",
                   encoding="utf-8")
    # 第四式（照八字科第一百六十六批·同步判据不同文字）：**JSON 数据文件里**的死指针
    # 同样必抓——本器旧版只走 .md/.py，rule_registry.json 的 HANDOFF 幽灵指针就是这么漏的。
    tmp_json = DISC / "data" / "rules" / "_selftest_deadref.json"
    tmp_json.write_text(json.dumps(
        {"coverage": "见 `docs/zz_probe_deadref_d.md`；真路径不误报 " + ok_a},
        ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        got, n = scan()
        hits = [g for g in got if "_selftest_deadref.md" in g]
        if len(hits) < 3:
            problems.append(f"负例自证失效：造的 3 条死引用（含 1 条裸路径）只抓到 {len(hits)} 条")
        jhits = [g for g in got if "_selftest_deadref.json" in g]
        if len(jhits) < 1:
            problems.append("负例自证失效：data/rules/*.json 里的死指针没被抓到（JSON 载体盲区）")
        if any("_selftest_deadref" in g and ok_a in g for g in got):
            problems.append("负例假阳性：真实存在的裸路径被判成死引用，本器不足以当硬门")
    finally:
        tmp.unlink(missing_ok=True)
        tmp_json.unlink(missing_ok=True)
    # 复扫：临时文件删掉后不应留下痕迹（防自测污染）
    got2, _ = scan()
    if any("_selftest_deadref" in g for g in got2):
        problems.append("负例样本未清理干净")


GATE_RANGE = re.compile(r"\[\d{1,2}\]\s*[～~\-–—]\s*\[\d{1,2}\]")
LIVE_DOCS = ("README.md", "SKILL.md", "docs/EVAL-PLAN.md", "docs/CASE-LIBRARY-AUDIT.md")


def range_claims() -> list[str]:
    """**活文档**里不得写死门禁编号区间（形如「[1]～[17]」）。

    门禁会增补：区间一写死，多加一道门就自动变成假话。本仓真发生过——
    `docs/EVAL-PLAN.md` 写「[1]～[17]」时实际已有 `[22]`/`[23]`/`[24]`。
    CHANGELOG 不查（老条目是登记时点的事实，一字不改）。
    要引用门就写「对应小节」或逐条列号，别写区间。
    """
    bad: list[str] = []
    for rel in LIVE_DOCS:
        p = DISC / rel
        if not p.exists():
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if GATE_RANGE.search(line):
                bad.append(f"{rel}:{i} 写死了门禁区间 → {line.strip()[:70]}")
    return bad


def range_selftest(problems: list[str]) -> None:
    """负例两式：区间写法必被抓；逐条列号不得误伤。夹具只落临时目录（铁律二）。"""
    with tempfile.TemporaryDirectory(prefix="docrange_") as td:
        root = pathlib.Path(td)
        (root / "docs").mkdir()
        (root / "README.md").write_text("数字可在 [1]～[17] 里逐字回指", encoding="utf-8")
        (root / "docs" / "EVAL-PLAN.md").write_text("逐小节现号：[1] 冒烟｜[4] 金标准", encoding="utf-8")
        held = globals()["DISC"]
        globals()["DISC"] = root
        try:
            hits = range_claims()
        finally:
            globals()["DISC"] = held
    if not any("README.md:1" in h for h in hits):
        problems.append(f"负例自证失效：写死的门禁区间没被抓到 → {hits}")
    if any("EVAL-PLAN" in h for h in hits):
        problems.append("负例自证假阳性：逐条列号的合法写法被误判")


def main() -> int:
    ap = argparse_flags()
    problems, examined = scan()
    for x in range_claims():
        problems.append("门禁区间写死（会随增补变假话）：" + x)
    if ap:
        selftest(problems)
        range_selftest(problems)
        print("  [selftest] 负例已跑（死路径必被抓／JSON 载体死指针必被抓 / 写死的门禁区间必被抓 / 病历与逐条列号不误伤）")
    print(f"合计：检视 {examined} 条路径引用，{len(problems)} 条指向不存在的文件"
          f"（另有 {len(SKIPPED_HISTORY)} 条按「病历/负例」口径未判）")
    if examined == 0:
        print("× 0 条被检视——本器等于没跑，不判通过")
        return 1
    for x in problems:
        print(f"  × {x}")
    if not problems:
        print("  √ 活引用全部可达（CHANGELOG 历史散文按口径不查）")
    return 1 if problems else 0


def argparse_flags() -> bool:
    return "--selftest" in sys.argv


if __name__ == "__main__":
    raise SystemExit(main())
