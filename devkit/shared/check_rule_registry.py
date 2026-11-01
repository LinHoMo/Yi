# -*- coding: utf-8 -*-
"""规则注册表的书源指针回验器：`verified: true` 不许是自说自话。

为什么需要它（2026-10-10）：`core/yishu_core/ming_tables.py` 头注写着
「指针由 tests/test_ming_rule_registry.py 回验」——该测试文件**全仓不存在**，
bazi 也没有 tests/ 目录。也就是说 `rule_registry.json` 里每一条
`"verified": true` 从写下那天起没有任何东西复核过。本器把这条声明变成真话：

    python dev_tools/check_rule_registry.py             # 校验
    python dev_tools/check_rule_registry.py --selftest  # 负例：证明本器抓得住假 verified

校验三类指针（两科 schema 同源 `yi-rule-registry-v1`）：
  · `source.quote_in_data` = "<file>#<a.b.c>"   → 文件在、点分路径可解析、值非空；
        若同条带 `corpus_files`，则该值须**逐字命中**其中至少一份语料（归一化后）；
  · `source.quote_in_code` = "<file>#<text|IDENT>" → 目标文件里能找到该字串，
        或该标识符作为名字存在（`BING_YAO_THESIS` 这类是常量名，不是引文）；
  · `source.corpus_files` 自身必须存在；
  · 【362 批】`source.quote_in_source` = "<底本>:<行号>" → 该行逐字含本条 `quote`
        （quote2/quote3 同理）。写了行号就是在声称「引文在此」，故不看 verified 一律判红——
        此前本形态无人守，六爻 2 条 `verified=false` 因此长期挂着（362 批回验 4/4 命中后转真）；
  · **【第一百六十八批】`impl`** = "<file>.py[:symbol]" → 文件在，且 `:标识符` 形态时
        该符号确在文件内（`:1058`／`:4.3` 是定位记号不是符号，跳过）。此前本器从不看
        `impl`，六爻科同批实抓到两条悬空指针，本科是同一潜在缺口，本批两侧拉齐。
`verified: true` 而上述任一步失败 → 判红；`verified: false` 只作 NOTE（那是诚实的未核实）。
**`impl` 例外：不看 `verified` 一律判红**——代码指针不存在「诚实未核实」状态，指错就是指错。

447 批追加（仅六爻册；八字无此文件时跳过）：`qianjin_fu_map.json` 的**统计块自洽**——
`统计.联句总数` 必须等于 `联句映射` 条数；每个状态分项必须等于实际条目数（状态允许
`已落地_<机制>_<日期>` 后缀，按 `_` 前前缀计数）；统计键必须是 `_meta` 状态词汇的子集，
词汇表里的每个状态也必须出现在统计里（防漏项）；`registry_未被本表联句直接挂上`
里的 id 必须都存在于 `rule_registry`。本批首跑抓到 `_meta` 仍写「四态」而实际条目已用
第五态「已落地」——文档与实际状态词汇分家（§六.2），同批改为「五态」。

457 批追加：**逐联书源回指**。`_meta.纪律` 写着「联句与 src 逐字从书源抄来」，但 447
只核统计块，100 条联句与行号从未对拍。现按 [14] 同口径（所指行 ±2 行拼接、去空白标点）
逐条验证：`src` 必须带行号（`L8` 或 `《黄金策》源L124…`），行号须在底本范围内，联句须
在该行邻域逐字命中。首跑 100/100 全符（0 处改值）。
"""
from __future__ import annotations

import json
import re
import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parent
REG = DISC / "data" / "rules" / "rule_registry.json"
# 447 批：千金赋联句映射（仅六爻有该册；八字无文件则跳过，不判红）。
QIANJIN = DISC / "data" / "rules" / "qianjin_fu_map.json"
QIANJIN_SRC = DISC / "data" / "sources" / "huangjince_dz.dz.txt"
_QN_DROP = re.compile(r"[\s，。、；：「」『』“”\"'‘’（）()\[\]【】《》〈〉·．\-—_]+")

_DROP = re.compile(r"[\s，。、；：「」『』“”\"'‘’（）()【】\[\]《》<>·．\-—_/\\|+=:;,.*]+")
VARIANT = str.maketrans({"剋": "克", "裏": "里", "羣": "群", "徧": "遍", "啓": "启",
                         "蔵": "藏", "峯": "峰", "梟": "枭", "煙": "烟"})


def norm(s: str) -> str:
    return _DROP.sub("", str(s)).translate(VARIANT)


def _resolve_any(rel: str) -> Path | None:
    """指针按仓库根写（`bazi/data/…`），也容忍相对学科根的写法。"""
    rel = rel.split("#", 1)[0].strip().lstrip("./")
    for base in (ROOT, DISC):
        p = base / rel
        if p.exists():
            return p
    return None


def _dig(obj, dotted: str):
    """按 `a.b.c` 取嵌套值；键本身可含 `/`（如「独发/独静」），故从右往左不可分，
    改用逐段前缀尝试。"""
    parts = dotted.split(".")
    cur = obj
    i = 0
    while i < len(parts):
        if not isinstance(cur, dict):
            return None, parts[i:]
        # 尽量吃掉更多段（键里带点的罕见，带 / 的常见但已被 split 保留）
        matched = False
        for j in range(len(parts), i, -1):
            key = ".".join(parts[i:j])
            if key in cur:
                cur = cur[key]
                i, matched = j, True
                break
        if not matched:
            return None, parts[i:]
    return cur, []


def _iter_entries(doc: dict):
    for bucket in ("rules", "_uncovered"):
        for item in doc.get(bucket) or []:
            if isinstance(item, dict):
                yield bucket, item


# 【第一百六十八批·照六爻第一百六十九批同步】`impl` 是**可执行契约**，本器此前只回验
# `source.quote_in_*`／`corpus_files`，从没看过 `impl`。六爻科实抓到两条悬空指针
# （第一百六十六批「域拆分」把函数搬进子模块、父模块无 re-export，impl 仍指父模块），
# 于是「指针写了没人验」在本科同样是真事——本批把两侧判据拉齐。
#
# 口径（**宁可少判**，与六爻科同）：只认 `<path>.py` 后紧跟 `:标识符` 且标识符首字符是
# 字母/下划线的形态；行号 `:1058`、`:4.3` 这类**定位记号不是符号**，一律跳过，否则本器
# 会逼人改写正确定位记号。多段实现（`；`／`＋`／`（）`）逐段各自判。
#
# ⚠ 扫描面是**整条 impl 串，含括号内的说明文字**：注释里若把「旧壳 + 符号」拼成一条
# `path.py:symbol`，本器一样判红（本批实踩——更正死指针时在注里写了旧写法，当场被抓）。
# 这是**特性不是误伤**：说明文字里的死指针同样是死指针。登记旧值时**只写文件、不拼符号**。
# A1-1 归并：路径前缀两科都认（原八字版只认 bazi/，六爻版只认 liuyao/）
_PATH_RE = re.compile(r"(?<![\w/])((?:(?:liuyao|bazi)/)?(?:scripts|core|dev_tools)/[\w/]+\.py)")
_SYM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")
# 薄 re-export 壳（职责拆走后只留 `from X import *` 的模块）：
# 符号**在壳里不落字面**但运行时可达——照字面判会造 4 条假红（实测踩到）。
_REEXPORT = re.compile(r"from\s+[\w.]+\s+import\s+\*")


def _reachable_via_import(tp: Path, sym: str) -> bool:
    """薄 re-export 壳专用：改用**运行时可达性**判（真可达就不算死指针）。"""
    import importlib.util

    name = "_impl_probe_" + tp.stem
    try:
        spec = importlib.util.spec_from_file_location(name, tp)
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        parent = str(tp.parent)
        inserted = parent not in sys.path
        if inserted:
            sys.path.insert(0, parent)
        try:
            spec.loader.exec_module(mod)
            return hasattr(mod, sym)
        finally:
            if inserted and parent in sys.path:
                sys.path.remove(parent)
    except Exception:
        return False


def check_impl(impl: str) -> list[str]:
    """回验 `impl` 里的 `file.py:symbol`；返回问题清单（空＝全部可回指）。"""
    bad: list[str] = []
    for m in _PATH_RE.finditer(impl):
        rel = m.group(1)
        tp = _resolve_any(rel)
        if tp is None:
            bad.append(f"文件不存在 → {rel}")
            continue
        sm = _SYM_RE.match(impl[m.end():m.end() + 80])
        if not sm:
            continue          # 纯路径 / 行号 / 4.3：无符号可验，不判
        sym = sm.group(1)
        body = tp.read_text(encoding="utf-8", errors="replace")
        if re.search(rf"\b{re.escape(sym)}\b", body):
            continue
        if _REEXPORT.search(body):
            # 壳里不落字面但运行时可达 → 不是死指针；真不可达（如未进 __all__）仍判红
            if _reachable_via_import(tp, sym):
                continue
            bad.append(f"符号不可达（re-export 壳未导出）→ {rel}:{sym}")
            continue
        bad.append(f"符号不在该文件内 → {rel}:{sym}")
    return bad


def check(doc: dict, problems: list[str], notes: list[str]) -> tuple[int, int]:
    """返回 (检视指针数, 通过数)。"""
    checked = passed = 0
    for bucket, item in _iter_entries(doc):
        rid = item.get("rule_id") or "?"
        src = item.get("source") or {}
        verified = src.get("verified")
        for field in ("quote_in_data", "quote_in_code"):
            ref = src.get(field)
            if not ref or "#" not in str(ref):
                continue
            checked += 1
            target, _, ptr = str(ref).partition("#")
            tp = _resolve_any(target)
            if tp is None:
                msg = f"{rid}.{field}：目标文件不存在 → {target}"
                (problems if verified else notes).append(msg)
                continue
            body = tp.read_text(encoding="utf-8", errors="replace")
            ok = False
            detail = ""
            if field == "quote_in_code":
                # 允许两种：字面串命中，或作为标识符存在
                ok = ptr in body or bool(re.search(rf"\b{re.escape(ptr)}\b", body))
                detail = ptr[:32]
            else:
                try:
                    data = json.loads(body)
                except Exception as exc:
                    problems.append(f"{rid}.quote_in_data：目标不是合法 JSON（{exc}）")
                    continue
                val, rest = _dig(data, ptr)
                if val is None or (isinstance(val, str) and not val.strip()):
                    detail = f"路径解不到值（余 {rest[:2]}）"
                else:
                    val_s = val if isinstance(val, str) else json.dumps(val, ensure_ascii=False)
                    corpora = src.get("corpus_files") or []
                    hit_in = None
                    for c in corpora:
                        cp = _resolve_any(c)
                        if cp and norm(val_s) in norm(cp.read_text(encoding="utf-8", errors="replace")):
                            hit_in = cp.name
                            break
                    if corpora and not hit_in:
                        detail = "语料逐字未命中：" + val_s[:28] + "…"
                    else:
                        ok = True
                        detail = (f"{val_s[:24]}…（语料命中 {hit_in}）" if hit_in
                                  else val_s[:24] + "…")
            if ok:
                passed += 1
            else:
                line = f"{rid}.{field}：{detail}"
                (problems if verified else notes).append(line + "（verified=false，只记）"
                                                         if not verified else line)
        for c in (src.get("corpus_files") or []):
            checked += 1
            if _resolve_any(c) is None:
                (problems if verified else notes).append(f"{rid}.corpus_files：不存在 → {c}")
            else:
                passed += 1
        # 【第三百六十二批】`quote_in_source`（"底本文件:行号" 形态）此前**没有任何门在守**：
        # 门只认 `#` 形态的 quote_in_data/quote_in_code，而六爻 33 条里有 2 条用的是行号形态，
        # 于是它们的 `verified=false` 从登记那天起躺到今天——不是"无法核实"，是"没人核实"
        # （362 批回验：4 条引文 4/4 逐字命中底本该行）。本判据补上这个空档。
        for key, ptr_key in (("quote", "quote_in_source"),
                             ("quote2", "quote2_in_source"),
                             ("quote3", "quote3_in_source")):
            ref = src.get(ptr_key)
            quote = src.get(key)
            if not ref or ":" not in str(ref) or not quote:
                continue
            checked += 1
            target, _, ln = str(ref).rpartition(":")
            tp = _resolve_any(target)
            if tp is None:
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：底本不存在 → {target}")
                continue
            try:
                lines = tp.read_text(encoding="utf-8", errors="replace").split("\n")
                body = lines[int(ln) - 1]
            except (ValueError, IndexError):
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：行号不可解析或越界 → {ref}")
                continue
            # 行号形态的指针是「引文就在这一行」的强声明：命中即过，不命中即红
            # （不看 verified——既然写了行号，就是在声称引文在此）
            if norm(quote) in norm(body):
                passed += 1
            else:
                a, b = norm(quote), norm(body)
                i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]),
                         min(len(a), len(b)))
                (problems if verified else notes).append(
                    f"{rid}.{ptr_key}：引文不在 {ref} 该行（首异于第 {i} 字："
                    f"…{a[max(0, i - 12):i + 12]}… ≠ …{b[max(0, i - 12):i + 12]}…）"
                    + ("" if verified else "（verified=false，只记）"))
        # 【第一百六十八批】`impl` 回验：代码指针没有「诚实未核实」状态，指错即指错，
        # 故不看 verified 一律判红（§六.3 文实不符等同代码缺陷）。
        impl = item.get("impl")
        if impl:
            checked += 1
            bad = check_impl(str(impl))
            if bad:
                problems.append(f"{rid}.impl：{'；'.join(bad)}")
            else:
                passed += 1
    return checked, passed


def check_qianjin_map(doc: dict, problems: list[str],
                      registry_ids: set[str] | None = None,
                      src_lines: list[str] | None = None) -> tuple[int, int]:
    """千金赋联句映射的统计自洽＋逐联书源回指（447／457 批）。返回 (联句数, 状态种数)。"""
    entries = doc.get("联句映射")
    if not isinstance(entries, list) or not entries:
        problems.append("千金赋映射：联句映射缺失或为空——0 结果 ≠ 通过")
        return 0, 0
    meta = doc.get("_meta") or {}
    states = meta.get("五态") or meta.get("四态") or {}   # 兼容旧键名，词表仍须覆盖实际状态
    if not isinstance(states, dict) or not states:
        problems.append("千金赋映射：_meta 未登记状态词汇（五态/四态）")
        states = {}

    def state_of(e: dict) -> str:
        return str(e.get("状态") or "").split("_", 1)[0]

    usage: dict[str, int] = {}
    unknown: dict[str, str] = {}
    for e in entries:
        s = state_of(e)
        usage[s] = usage.get(s, 0) + 1
        if states and s not in states:
            unknown.setdefault(s, str(e.get("句") or "")[:16])
    for s, q in unknown.items():
        problems.append(f"千金赋映射：状态「{s}」未在 _meta 状态词汇中登记（{q}…）")

    stats = doc.get("统计") or {}
    total = stats.get("联句总数")
    if total != len(entries):
        problems.append(f"千金赋映射：统计.联句总数 {total} ≠ 实际 {len(entries)}")
    per_state = 0
    for key, val in stats.items():
        if key == "联句总数":
            continue
        if states and key not in states:
            problems.append(f"千金赋映射：统计里有未登记的状态键「{key}」")
        if not isinstance(val, int) or val != usage.get(key, 0):
            problems.append(f"千金赋映射：统计.{key} {val} ≠ 实际 {usage.get(key, 0)}")
        if isinstance(val, int):
            per_state += val
    if per_state != len(entries):
        problems.append(f"千金赋映射：统计分项之和 {per_state} ≠ 联句总数 {len(entries)}")
    if states:
        absent = sorted(set(states) - set(stats))
        if absent:
            problems.append(f"千金赋映射：状态词汇 {absent} 未在统计中列出")

    registry = doc.get("registry_未被本表联句直接挂上")
    if registry is not None:
        if not isinstance(registry, list):
            problems.append("千金赋映射：registry_未被本表联句直接挂上 必须是列表")
        elif registry_ids is not None:
            missing = [str(x) for x in registry if str(x) not in registry_ids]
            if missing:
                problems.append(f"千金赋映射：registry 列表有 {len(missing)} 个 id "
                                f"不在 rule_registry：{missing[:4]}")

    # 457 批：逐联书源回指——`_meta.纪律` 声明「联句与 src 逐字从书源抄来」，
    # 此前只核统计块，联句与行号从未对拍。窗口与 [14] 同口径（所指行 ±2 行拼接）。
    lines = src_lines
    if lines is None:
        if not QIANJIN_SRC.is_file():
            problems.append(f"千金赋映射：底本不存在 {QIANJIN_SRC.name}——无从回指")
            lines = []
        else:
            lines = QIANJIN_SRC.read_text(encoding="utf-8", errors="replace").splitlines()
    line_ref = re.compile(r"(?:源)?L(\d+)")
    qbad = 0
    for e in entries:
        m = line_ref.search(str(e.get("src") or ""))
        if not m:
            problems.append(f"千金赋映射：条目缺行号 src（{(e.get('句') or '')[:16]}…）")
            qbad += 1
            continue
        n = int(m.group(1))
        if lines and (n < 1 or n > len(lines)):
            problems.append(f"千金赋映射：src 行号 L{n} 超出底本（共 {len(lines)} 行）")
            qbad += 1
            continue
        q = _QN_DROP.sub("", str(e.get("句") or ""))
        window = "".join(_QN_DROP.sub("", x) for x in lines[max(0, n - 2):n + 3])
        if not q or q not in window:
            problems.append(f"千金赋映射：联句与底本源L{n} 邻域不符 → "
                            f"{(e.get('句') or '')[:24]}…")
            qbad += 1
    if qbad:
        problems.append(f"千金赋映射：逐联回指失败 {qbad}/{len(entries)} 条")
    return len(entries), len(usage)


def selftest(problems: list[str]) -> None:
    """负例：造一条 verified=true 却指向不存在文件/解不到值的条目，必须判红。"""
    fake = {"schema": "yi-rule-registry-v1", "rules": [
        {"rule_id": "test.bad_pointer", "source": {
            "verified": True,
            "quote_in_data": "data/rules/rule_registry.json#no.such.path"}},
        {"rule_id": "test.missing_file", "source": {
            "verified": True,
            "quote_in_code": "dev_tools/__does_not_exist__.py#ANY"}},
        # 【第一百六十八批】impl 两式负例：①文件不存在 ②文件在、符号不在
        {"rule_id": "test.impl_missing_file",
         "impl": "dev_tools/__does_not_exist__.py:analyze_x", "source": {"verified": True}},
        {"rule_id": "test.impl_missing_symbol",
         "impl": "scripts/chart.py:__no_such_symbol__", "source": {"verified": True}},
        # 【362 批】行号形态（quote_in_source）两式负例：①引文不在该行 ②底本不存在
        {"rule_id": "test.quote_in_source_mismatch", "source": {
            "verified": True,
            "quote": "这句话绝不在底本该行",
            "quote_in_source": "data/rules/rule_registry.json:1"}},
        {"rule_id": "test.quote_in_source_missing_file", "source": {
            "verified": True,
            "quote": "任意引文",
            "quote_in_source": "data/sources/__no_such__.dz.txt:1"}},
    ], "_uncovered": []}
    p: list[str] = []
    n: list[str] = []
    checked, passed = check(fake, p, n)
    if checked < 6 or passed != 0:
        problems.append(f"负例自证失效：应为 ≥6 检视 0 通过，实得 检视 {checked} 通过 {passed}")
    if len(p) < 6:
        problems.append(f"负例自证失效：6 条假指针只判红 {len(p)} 条 → {p}")
    if n:
        problems.append(f"负例不该产生 NOTE（verified=true 应判红）→ {n}")

    # 【第一百六十八批】正例不误伤：行号/版本号式定位记号无符号可验，必须放行
    if check_impl("scripts/chart.py:128（成破救应分支）"):
        problems.append("正例被误伤：行号式定位记号不该判")
    if check_impl("scripts/chart.py"):
        problems.append("正例被误伤：纯路径不该判")
    # 六爻专属负例（A1-1 归并保留，不在八字侧跑）：第一百六十六批域拆分后，
    # 父模块无 re-export 的悬空符号必须仍被抓住。
    _hist = "scripts/" + "classical_enhancements.py" + ":analyze_shen_yao_activation"
    if DISC.name == "liuyao" and not check_impl(_hist):
        problems.append("负例未抓到：父模块并无该符号（已搬入 shen_yao 子模块）")

    # 447 批：千金赋映射统计自洽（正例不误伤＋四类负例必须抓到）
    _states = ("已挂", "已落地", "未实现", "不适用", "无对应")
    _qlines = ["天玄地黄", "宇宙洪荒", "日月盈昃", "辰宿列张"]
    qbase = {
        "_meta": {"五态": {s: "" for s in _states}},
        "统计": {"联句总数": 3, "已挂": 1, "已落地": 1, "未实现": 0,
                 "不适用": 1, "无对应": 0},
        "联句映射": [{"句": "天玄地黄", "src": "L1", "状态": "已挂"},
                     {"句": "宇宙洪荒", "src": "L2", "状态": "已落地_日辰并爻_20261014"},
                     {"句": "日月盈昃", "src": "L3", "状态": "不适用"}],
        "registry_未被本表联句直接挂上": ["liuyao.andong"],
    }
    p_q: list[str] = []
    n_q = check_qianjin_map(qbase, p_q, {"liuyao.andong"}, _qlines)
    if p_q or n_q != (3, 3):
        problems.append(f"千金赋映射正例被误伤：{p_q}")

    def _qbad(mut) -> list[str]:
        d = json.loads(json.dumps(qbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_qianjin_map(d, p, {"liuyao.andong"}, _qlines)
        return p

    if not any("统计.已挂" in x for x in _qbad(lambda d: d["统计"].__setitem__("已挂", 2))):
        problems.append("负例未抓到：统计分项与实际条目数不符")
    if not any("未在 _meta 状态词汇" in x for x in
               _qbad(lambda d: d["联句映射"][0].__setitem__("状态", "新态"))):
        problems.append("负例未抓到：条目用了未登记的状态")
    if not any("不在 rule_registry" in x for x in
               _qbad(lambda d: d["registry_未被本表联句直接挂上"].__setitem__(0, "liuyao.nope"))):
        problems.append("负例未抓到：registry 列表含 rule_registry 不存在的 id")
    if not any("未在统计中列出" in x for x in _qbad(lambda d: d["统计"].pop("无对应"))):
        problems.append("负例未抓到：状态词汇漏进统计块")
    # 457 批：联句与 src 不符必须抓到；缺行号也必须抓到
    if not any("联句与底本源L1 邻域不符" in x for x in
               _qbad(lambda d: d["联句映射"][0].__setitem__("句", "绝无此语"))):
        problems.append("负例未抓到：联句与 src 行不符")
    if not any("缺行号 src" in x for x in
               _qbad(lambda d: d["联句映射"][0].pop("src", None))):
        problems.append("负例未抓到：条目缺行号 src")


def main() -> int:
    if not REG.exists():
        print(f"× 注册表不存在：{REG}")
        return 1
    doc = json.loads(REG.read_text(encoding="utf-8"))
    problems: list[str] = []
    notes: list[str] = []
    checked, passed = check(doc, problems, notes)
    print(f"{DISC.name}：检视 {checked} 条书源指针，{passed} 条可回指")
    registry_ids = {str(item.get("rule_id") or item.get("id"))
                    for _bucket, item in _iter_entries(doc)}
    registry_ids.discard("None")
    # 447 批：千金赋联句映射（仅六爻有该册；八字无文件则跳过，不判红）
    if QIANJIN.is_file():
        qdoc = json.loads(QIANJIN.read_text(encoding="utf-8"))
        q_total, q_states = check_qianjin_map(qdoc, problems, registry_ids)
        print(f"  千金赋映射：{q_total} 联、{q_states} 个状态；"
              f"统计块/五态词表/registry 列表/逐联书源回指已逐项核对")
    elif DISC.name == "liuyao":
        problems.append(f"千金赋映射：{QIANJIN.name} 不存在——0 结果 ≠ 通过，先确认路径")
    _ap = argparse.ArgumentParser(description="check_rule_registry：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        before = len(problems)
        selftest(problems)
        added = len(problems) - before
        # 447 批修旧缺陷：原文 `problems = problems[:before]` 会把**自证失败**的消息一起截掉，
        # 于是「负例没抓到」也以 EXIT=0 通过。自证失败必须保留并判红；通过则无新增。
        print(f"  [selftest] {'异常：' + str(added) + ' 条自证失败（保留并判红）' if added else '负例已跑（抓到）'}")
    if checked == 0:
        print("× 0 条指针可检视——本器等于没跑，不判通过")
        return 1
    for x in notes[:10]:
        print(f"  · {x}")
    for x in problems:
        print(f"  × {x}")
    if not problems:
        print("  √ 全部 verified 指针均可回指（verified=false 者只记不判）")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
