# -*- coding: utf-8 -*-
"""书源深度解读机械门（source readings gate）。

验收 docs/source-readings/ 下每部著作的深度解读文档（登记表
data/sources/works_registry.json）：

  1. 覆盖完整：登记表内每部著作都有解读文档；
  2. 章节齐全：六大必填节（一 书目与版本 / 二 逐卷（章）深读 / 三 可用判据清单 /
     四 对勘与口径分歧 / 五 不适用与存疑 / 六 优化建议）；
  3. 引文逐字：``源L<num>：`……` ``（多文件著作用图例 tag：``源J3L45：`…` ``）
     的引文必须是该书源**被引那一行**的逐字子串——指回原文可机械核验；
  4. 深度下限：引文条数 / 文档行数 / 「###」小节数 / §三判据表行数 不得低于阈值；
  5. 优化建议可机读：§六表格行 ID 必须是 ``| OPT-<work_key>-NN |``，六列固定，
     供 --index 聚合为全仓优化清单。

用法：
  python tools/check_source_readings.py              # 全量验收（门）
  python tools/check_source_readings.py --doc PATH   # 验收单篇（写解读时的自检回路）
  python tools/check_source_readings.py --index      # 重建 docs/source-readings/INDEX.md
  python tools/check_source_readings.py --selftest   # 负例自证（坏文档必须被判红）

EXIT=0 全过；EXIT=1 有失败明细。
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "sources" / "works_registry.json"
SRC_DIR = ROOT / "data" / "sources"
DOCS_DIR = ROOT / "docs" / "source-readings"
INDEX_MD = DOCS_DIR / "INDEX.md"

REQUIRED_SECTIONS = [
    "一、书目与版本",
    "二、逐卷（章）深读",
    "三、可用判据清单",
    "四、对勘与口径分歧",
    "五、不适用与存疑",
    "六、优化建议",
]
# 引文标记：源[tag]L<num>：`逐字引文`（tag 留空 = 主源）
QUOTE_RE = re.compile(r"源([A-Za-z0-9_\-]*)L(\d+)：`([^`\n]{2,200})`")
# 图例行：- TAG = 文件名
LEGEND_RE = re.compile(r"^[-*]\s*([A-Za-z0-9_\-]+)\s*=\s*([\w.\-]+\.txt)\s*$", re.M)
# OPT 行：| OPT-<key>-NN | 目标 | 现状 | 建议 | 验收方式 | 优先级 |
OPT_RE = re.compile(r"^\|\s*OPT-([^\s|]+?)-(\d+)\s*\|(.+)$")

# 举例用假路径约定：__ 双下划线前缀（与 tools/check_doc_deadlinks.py 一致）
FAKE_PATH = "__"


def _read_lines(p: Path) -> list[str]:
    text = p.read_text(encoding="utf-8-sig")
    return [ln.rstrip("\r") for ln in text.split("\n")]


def check_doc_lines(lines: list[str], work: dict, src_cache: dict | None = None) -> list[str]:
    """单篇规则主体：落盘文档与 selftest 文本共用。返回失败明细（空 = 过）。"""
    fails: list[str] = []
    text = "\n".join(lines)
    cache = src_cache if src_cache is not None else {}

    # 1) 必填节
    for sec in REQUIRED_SECTIONS:
        if f"## {sec}" not in text:
            fails.append(f"缺必填节「{sec}」")

    # 2) 主源文件名绑定
    primary = work["sources"][0]
    if primary not in text:
        fails.append(f"正文未绑定主源文件名 {primary}")

    q_fails, n_quotes = verify_quotes(text, primary, cache)
    fails.extend(q_fails)
    min_q = work.get("min_quotes", 4 if work.get("tiny") else 8)
    if n_quotes < min_q:
        fails.append(f"引文仅 {n_quotes} 条 < 下限 {min_q}")

    # 4) 深度下限
    min_lines = work.get("min_lines", 60 if work.get("tiny") else 120)
    if len(lines) < min_lines:
        fails.append(f"文档仅 {len(lines)} 行 < 深度下限 {min_lines}")
    n_subsec = sum(1 for ln in lines if ln.startswith("### "))
    if n_subsec < (1 if work.get("tiny") else 3):
        fails.append(f"「###」小节仅 {n_subsec} 个 < 下限")

    # 5) §三判据表数据行（§三 起、§四 前的 | 行，排除表头与分隔行）
    n_ju = 0
    in_ju = False
    for ln in lines:
        if ln.startswith("## 三、"):
            in_ju = True
            continue
        if ln.startswith("## 四、"):
            in_ju = False
            continue
        if in_ju and ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) >= 2 and "---" not in cells[0] and cells[0] not in ("判据", "ID", ""):
                n_ju += 1
    min_ju = 2 if work.get("tiny") else 5
    if n_ju < min_ju:
        fails.append(f"§三判据表数据行仅 {n_ju} 行 < 下限 {min_ju}")

    # 6) OPT 行：ID 前缀须挂本著作，六列固定
    n_opt = 0
    for ln in lines:
        m = OPT_RE.match(ln)
        if m:
            if m.group(1) != work["key"]:
                fails.append(f"OPT 行 ID 前缀须为 OPT-{work['key']}-NN，实为 OPT-{m.group(1)}-{m.group(2)}")
                continue
            cells = [c.strip() for c in m.group(3).strip().strip("|").split("|")]
            if len(cells) < 5:
                fails.append(f"OPT 行列数不足（须 ID/目标/现状/建议/验收方式/优先级 6 列）：{ln[:60]}")
                continue
            n_opt += 1
    if n_opt < 2:
        fails.append(f"§六 OPT 行仅 {n_opt} 条 < 下限 2")
    return fails


def verify_quotes(text: str, primary: str, cache: dict | None = None) -> tuple[list[str], int]:
    """引文逐字核验：返回 (失败明细, 引文条数)。tag 经图例解析；空 tag = primary。"""
    fails: list[str] = []
    cache = cache if cache is not None else {}
    legend = {m.group(1): m.group(2) for m in LEGEND_RE.finditer(text)}
    n_quotes = 0
    for m in QUOTE_RE.finditer(text):
        n_quotes += 1
        tag, ln_s, quote = m.group(1), int(m.group(2)), m.group(3)
        fname = legend.get(tag) if tag else primary
        if not fname:
            fails.append(f"引文 tag={tag} 无图例可解析（需「- {tag} = 文件名」行）")
            continue
        if fname not in cache:
            fpath = SRC_DIR / fname
            if not fpath.exists():
                fails.append(f"引文指向不存在的书源：{fname}（L{ln_s}）")
                cache[fname] = None
                continue
            cache[fname] = _read_lines(fpath)
        src_lines = cache[fname]
        if src_lines is None:
            continue
        if not (1 <= ln_s <= len(src_lines)):
            fails.append(f"{fname} L{ln_s} 越界（全文 {len(src_lines)} 行）：{quote[:30]}…")
            continue
        if quote not in src_lines[ln_s - 1]:
            fails.append(
                f"引文非逐字/行号错位：{fname} L{ln_s} 不含「{quote[:40]}…」"
                f"｜该行实为：{src_lines[ln_s - 1][:60]}"
            )
    return fails, n_quotes


def check_doc(doc_path: Path, work: dict) -> list[str]:
    if FAKE_PATH in doc_path.name:
        return [f"文档名含举例假路径前缀 {FAKE_PATH}：{doc_path.name}"]
    if not doc_path.exists():
        return [f"文档缺失：{doc_path}"]
    return check_doc_lines(_read_lines(doc_path), work)


def load_registry() -> list[dict]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return data["works"]


def doc_stats(w: dict) -> tuple[int, int]:
    doc_path = ROOT / w["doc"]
    if not doc_path.exists():
        return 0, 0
    text = doc_path.read_text(encoding="utf-8-sig")
    nq = len(QUOTE_RE.findall(text))
    nopt = len([1 for ln in text.splitlines() if OPT_RE.match(ln)])
    return nq, nopt


def run_gate() -> int:
    works = load_registry()
    total = len(works)
    failed = 0
    n_quotes_all = 0
    print(f"书源深度解读门：登记 {total} 部著作")
    for w in works:
        fails = check_doc(ROOT / w["doc"], w)
        if fails:
            failed += 1
            print(f"\n[FAIL] {w['key']}《{w['title']}》")
            for f in fails:
                print(f"  - {f}")
        else:
            nq, nopt = doc_stats(w)
            n_quotes_all += nq
            print(f"[PASS] {w['key']}《{w['title']}》 引文{nq} OPT{nopt}")
    print(f"\n合计：{total - failed}/{total} 过，引文 {n_quotes_all} 条")
    if failed:
        print(f"EXIT=1（{failed} 部未达标）")
        return 1
    print("EXIT=0")
    return 0


OPT_STATUS_PATH = SRC_DIR / "opt_status.json"


def load_opt_status() -> tuple[set[str], int, int, int]:
    """读已处理 OPT 清单（data/sources/opt_status.json）。

    返回 (已处理 ID 集合, 落实数, 归档数, 撤销数)。文件缺失时返回空集——即
    「未登记则全部视为待办」，保证工具在无状态文件时行为与从前一致。
    """
    if not OPT_STATUS_PATH.exists():
        return set(), 0, 0, 0
    try:
        d = json.loads(OPT_STATUS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:  # 状态文件损坏不应阻断索引生成
        print(f"⚠ opt_status.json 读取失败（{e}），按「全部待办」处理")
        return set(), 0, 0, 0
    done = set(d.get("done", []))
    arch = set(d.get("archived", []))
    rej = set(d.get("rejected", []))
    return done | arch | rej, len(done), len(arch), len(rej)


def collect_opt_rows(works: list[dict]) -> list[dict]:
    rows = []
    for w in works:
        doc_path = ROOT / w["doc"]
        if not doc_path.exists():
            continue
        for ln in _read_lines(doc_path):
            m = OPT_RE.match(ln)
            if m and m.group(1) == w["key"]:
                cells = [c.strip() for c in m.group(3).strip().strip("|").split("|")]
                if len(cells) >= 5:
                    rows.append({
                        "id": f"OPT-{m.group(1)}-{m.group(2)}",
                        "work": w["key"], "title": w["title"], "discipline": w["discipline"],
                        "target": cells[0], "status": cells[1], "suggestion": cells[2],
                        "accept": cells[3], "priority": cells[4],
                    })
    return rows


def write_index(works: list[dict]) -> int:
    lines = [
        "# 书源深度解读总索引（机械生成，勿手改）",
        "",
        f"> 由 `tools/check_source_readings.py --index` 从 `data/sources/works_registry.json` + 各解读文档聚合。",
        "> 引文逐字可核（`源L行号：` 反引号引文）；优化项 ID 可机读。对齐分口径见 `AGENTS.md` 铁律三。",
        "",
    ]
    ok = 0
    rows_tbl = ["| key | 书名 | 类别 | 归属 | 引文数 | OPT数 | 状态 |", "|---|---|---|---|---|---|---|"]
    for w in works:
        doc_path = ROOT / w["doc"]
        nq, nopt = doc_stats(w)
        exists = doc_path.exists()
        ok += 1 if exists else 0
        rows_tbl.append(
            f"| {w['key']} | 《{w['title']}》 | {w['kind']} | {w['discipline']} "
            f"| {nq} | {nopt} | {'完成' if exists else '✘ 缺文档'} |"
        )
    lines.append(f"覆盖：{ok}/{len(works)} 部。")
    lines.append("")
    lines.extend(rows_tbl)

    opt_rows = collect_opt_rows(works)
    handled, n_done, n_arch, n_rej = load_opt_status()
    todo_rows = [r for r in opt_rows if r["id"].replace("OPT-", "") not in handled]
    lines.append("")
    lines.append(f"## 待办优化清单（{len(todo_rows)} 项，按优先级）")
    lines.append("")
    if handled:
        lines.append(
            f"> 已处理 **{len(opt_rows) - len(todo_rows)}** 项（落实 {n_done}／归档不动 {n_arch}／"
            f"实测推翻撤销 {n_rej}），明细见 `docs/OPT-LEDGER.md`、`docs/OPT-ARCHIVED.md` 与 "
            f"`data/sources/opt_status.json`。本清单只列**真正待做**项。"
        )
        lines.append("")
    lines.append("| ID | 书 | 归属 | 目标 | 现状 | 建议 | 验收方式 | 优先级 |")
    lines.append("|---|---|---|---|---|---|---|---|")
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for r in sorted(todo_rows, key=lambda r: (order.get(r["priority"], 9), r["id"])):
        lines.append(
            f"| {r['id']} | 《{r['title']}》 | {r['discipline']} | {r['target']} "
            f"| {r['status']} | {r['suggestion']} | {r['accept']} | {r['priority']} |"
        )
    INDEX_MD.parent.mkdir(parents=True, exist_ok=True)
    INDEX_MD.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(
        f"INDEX.md 已重建：覆盖 {ok}/{len(works)}，待办 {len(todo_rows)} 项"
        f"（共 {len(opt_rows)} 项，已处理 {len(opt_rows) - len(todo_rows)}："
        f"落实 {n_done}／归档 {n_arch}／撤销 {n_rej}） -> {INDEX_MD}"
    )
    return 0


def selftest() -> int:
    """负例自证：坏文档必须被判红；正例必须过。"""
    works = load_registry()
    by_key = {w["key"]: w for w in works}
    demo = by_key.get("wenwang_jinqianke_dz")
    if demo and (ROOT / demo["doc"]).exists():
        fails = check_doc(ROOT / demo["doc"], demo)
        if fails:
            print("SELFTEST FAIL：范文被判红（应当过）：")
            for f in fails:
                print(f"  - {f}")
            return 1
        print("正例：范文通过 ✔")
    # 负例 1：引文造假（逐字核验必须咬人）
    bad_quote_doc = (
        f"# 负例自证（{FAKE_PATH}selftest_bad，不入库）\n\n"
        f"主源 wenwang_jinqianke_dz.dz.txt\n\n"
        f"## 一、书目与版本\n\nx\n\n## 二、逐卷（章）深读\n\n### 假节\n\nx\n\n"
        f"## 三、可用判据清单\n\n| 判据 |\n|---|\n| a |\n| b |\n| c |\n| d |\n| e |\n\n"
        f"## 四、对勘与口径分歧\n\nx\n\n## 五、不适用与存疑\n\nx\n\n"
        f"## 六、优化建议\n\n| ID | 目标 | 现状 | 建议 | 验收方式 | 优先级 |\n"
        f"|---|---|---|---|---|---|\n"
        f"| OPT-wenwang_jinqianke_dz-01 | t | s | g | a | P3 |\n"
        f"| OPT-wenwang_jinqianke_dz-02 | t | s | g | a | P3 |\n"
        f"源L1：`这句引文是编造的必然不在书源里`"
    )
    fails = check_doc_lines(bad_quote_doc.split("\n"), demo)
    if not any("非逐字" in f for f in fails):
        print("SELFTEST FAIL：编造引文未被逐字门拦截！")
        return 1
    print(f"负例1（编造引文）被判红 ✔（{len(fails)} 项失败）")
    # 负例 2：空壳文档（章节/深度/判据/OPT 门全咬）
    fails2 = check_doc_lines(["# 假文档", "", "只有一行"], demo)
    if len(fails2) < 5:
        print(f"SELFTEST FAIL：空壳文档失败项过少（{len(fails2)}），章节/深度门失效！")
        return 1
    print(f"负例2（空壳文档）被判红 ✔（{len(fails2)} 项失败）")
    # 负例 3：OPT 挂错著作 key
    bad_opt = (
        f"## 六、优化建议\n\n| OPT-别的书-01 | t | s | g | a | P3 |"
    )
    fails3 = check_doc_lines(bad_opt.split("\n"), demo)
    if not any("前缀须为" in f for f in fails3):
        print("SELFTEST FAIL：OPT 挂错著作未被拦截！")
        return 1
    print("负例3（OPT 挂错著作）被判红 ✔")
    print("SELFTEST PASS")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="书源深度解读机械门")
    ap.add_argument("--doc", help="只验收单篇解读文档")
    ap.add_argument("--part", help="验收分读稿（只做引文逐字核验，不做章节/深度门）")
    ap.add_argument("--source", help="--part 的默认书源文件名（data/sources 下；空 tag 引文指向它）")
    ap.add_argument("--index", action="store_true", help="重建 INDEX.md")
    ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    works = load_registry()
    if args.index:
        return write_index(works)
    if args.part:
        ppath = Path(args.part)
        if not ppath.exists():
            print(f"EXIT=1：分读稿不存在 {ppath}")
            return 1
        text = ppath.read_text(encoding="utf-8-sig")
        fails, n = verify_quotes(text, args.source or "")
        print(f"分读稿 {ppath.name}：引文 {n} 条")
        for f in fails:
            print(f"  - {f}")
        print("EXIT=0" if not fails else f"EXIT=1（{len(fails)} 项失败）")
        return 0 if not fails else 1
    if args.doc:
        doc_path = Path(args.doc).resolve()
        hit = [w for w in works if (ROOT / w["doc"]).resolve() == doc_path]
        if not hit:
            print(f"EXIT=1：{doc_path} 不在登记表内")
            return 1
        fails = check_doc(doc_path, hit[0])
        for f in fails:
            print(f"  - {f}")
        print("EXIT=0" if not fails else f"EXIT=1（{len(fails)} 项失败）")
        return 0 if not fails else 1
    return run_gate()


if __name__ == "__main__":
    sys.exit(main())
