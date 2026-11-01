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

462 批追加（仅八字册）：**大运起例引文库的行锚**。`dayun_quotes.json` 自称「引文必须与
`corpus_line` 那一行逐字一致」，而本器此前只验 quote_in_data「值在语料某处出现过」，
不看行号——声明比门宽。现按该声明核对：`_provenance.source_file` 在盘、`corpus_line`
在册、`quote` 落在该行（[14] 同归一化）。两科 selftest 都跑夹具（六爻无此册则跳过）。

465 批追加（仅八字册）：**裁决引文书源回验**。`data/verdicts.json` 自称「书源引文唯一
真值源」：20 个字段带 `locator`（`data/sources/<书>:<行>`），4 条分支总则（病药 thesis、
化格/从格 verse）在 `_meta` 声明了底本。此前 [12] 只回指 `病药引文.thesis` 一个点，
locator 从未被读取。现按声明核对：行号在册、`quote/full_quote/cond_quote/verse_quote`
落在该行；分支总则逐行命中声明底本（不跨行拼接）。两科 selftest 都跑夹具。

466 批追加（仅八字册）：**六神取象/十神作用的行号出处**。`liushen_image.json` 声明
「值只收逐字引文与行号」，但实抓到两条 `取象` 是注释式改写且无 `_src`，`narrate`
仍按引文渲染出空行号（§六.3）。现核：每个非空 `能力/构成/取象/别名` 必须有
`<字段>_src`、行号在册、值落在该行；`shi_shen_actions` 每条 `source` 必须能解析
行号（`L####` 或 `:####`），`actions` 每项落在该行 ±3 行邻域。两科 selftest 都跑夹具。

467 批追加（仅六爻册）：**引文库 `quote_kind`**。`liuyao/data/verdicts.json#quote_database`
旧称「引文库，source 字段为古籍出处」，全库实测 49 条仅 1 条逐字可回原文，其余 48 条
是今译。现要求每条声明 `quote_kind`：`verbatim` 必须带 `source_ref`（`file[:line]`）
且逐字命中（折叠标点）；`paraphrase` 只要求非空 `source`（所本篇章）。报告层标题
沿用「经典引文」的问题登记为下一批（468）。两科 selftest 都跑夹具。
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
# 462 批：大运起例引文库（仅八字有该册；六爻无文件则跳过，不判红）。
DAYUN = DISC / "data" / "rules" / "dayun_quotes.json"
# 465 批：裁决引文真值源（仅八字有该册；六爻无文件则跳过）。
VERDICTS = DISC / "data" / "verdicts.json"
# 466 批：六神取象 / 十神作用（仅八字有该册）。
LIUSHEN = DISC / "data" / "liushen_image.json"
SHISHEN = DISC / "data" / "shi_shen_actions.json"
# 467 批：六爻引文库（仅六爻有该结构；八字同名文件结构不同）。
LIUYAO_QUOTES = DISC / "data" / "verdicts.json"
_VERDICT_LOCATOR = re.compile(r"(data/sources/[^:]+):(\d+)")
_VERDICT_MARK = re.compile(r"''+|={2,}|\{\{|\}\}|\||\*")
_VERDICT_FIELDS = ("quote", "full_quote", "cond_quote", "verse_quote")


def _verdict_plain(s: str) -> str:
    return re.sub(r"\s+", "", _VERDICT_MARK.sub("", str(s)))


def _walk_entries(obj, path: str = "$"):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from _walk_entries(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk_entries(v, f"{path}[{i}]")


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


def check_dayun_quotes(doc: dict, problems: list[str],
                       lines: list[str] | None = None) -> int:
    """大运起例引文库的行锚回验（462 批）。返回条目数。

    为什么需要它：`dayun_quotes.json` 的 `_comment` 声明「引文必须与 …
    `corpus_line` 那一行逐字一致」，但 [12] 的 `quote_in_data` 只验「值在语料
    某处出现过」，从不看行号——声明比门宽（§六.3）。本函数按该声明逐条核对：
    `_provenance.source_file` 在盘、`corpus_line` 在册、`quote` 落在该行。

    `lines` 参数供 selftest 注入夹具底本；正式路径由 `source_file` 现场读。
    """
    entries = [(k, v) for k, v in doc.items()
               if isinstance(v, dict) and "quote" in v and "corpus_line" in v]
    if not entries:
        problems.append("大运起例引文：0 条 corpus_line+quote——0 结果 ≠ 通过")
        return 0
    if len(entries) < 2:
        problems.append(f"大运起例引文：只扫到 {len(entries)} 条（下限 2）——先确认字段/路径")
    if lines is None:
        src = str((doc.get("_provenance") or {}).get("source_file") or "")
        rp = _resolve_any(src) if src else None
        if rp is None:
            problems.append(f"大运起例引文：source_file 不存在 → {src!r}")
            return len(entries)
        lines = rp.read_text(encoding="utf-8", errors="replace").splitlines()
    bad = 0
    for key, e in entries:
        try:
            n = int(str(e.get("corpus_line")).strip())
        except Exception:
            problems.append(f"大运起例引文：{key} 的 corpus_line 非整数 → {e.get('corpus_line')!r}")
            bad += 1
            continue
        if not (1 <= n <= len(lines)):
            problems.append(f"大运起例引文：{key} 的行号 L{n} 超出底本（共 {len(lines)} 行）")
            bad += 1
            continue
        q = _QN_DROP.sub("", str(e.get("quote") or ""))
        if not q or q not in _QN_DROP.sub("", lines[n - 1]):
            problems.append(f"大运起例引文：{key} 的引文不在所署行 L{n} → "
                            f"{str(e.get('quote') or '')[:30]!r}")
            bad += 1
    if bad:
        problems.append(f"大运起例引文：行锚不符 {bad}/{len(entries)} 条")
    return len(entries)


def check_verdicts_quotes(doc: dict, problems: list[str], lines_of=None) -> tuple[int, int]:
    """裁决引文的书源回验（465 批）。返回 (locator 字段数, 分支总则引文数)。

    为什么需要它：`data/verdicts.json` 自称「书源引文唯一真值源」，其中 20 个字段
    带 `locator`（`data/sources/<书>:<行>`）、4 条分支总则（病药 thesis、化格/从格
    verse）在 `_meta` 声明了底本——但 [12] 的 quote_in_data 只指向 `病药引文.thesis`
    一个点，`locator` 从未被任何门读取。本函数按声明核对：

      · 带 locator 的条目：行号在册、quote/full_quote/cond_quote/verse_quote 落在该行；
      · 三条分支总则：逐行命中 `_meta` 声明的底本（不跨行拼接，避免假阳性）。

    `lines_of` 供 selftest 注入夹具底本；正式路径按 locator/固定路径现场读。
    """
    n_loc = n_grp = 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    for path, e in _walk_entries(doc):
        loc = str(e.get("locator") or "").strip()
        m = _VERDICT_LOCATOR.fullmatch(loc)
        if not m:
            continue
        f, n = m.group(1), int(m.group(2))
        L = get_lines(f)
        if L is None:
            problems.append(f"verdicts：{path}.locator 指向不存在的底本 {f}")
            continue
        if not (1 <= n <= len(L)):
            problems.append(f"verdicts：{path}.locator 行号 L{n} 超出底本（共 {len(L)} 行）")
            continue
        for key in _VERDICT_FIELDS:
            q = e.get(key)
            if not q:
                continue
            n_loc += 1
            if _verdict_plain(q) not in _verdict_plain(L[n - 1]):
                problems.append(f"verdicts：{path}.{key} 不在所署行 {f}:{n} → "
                                f"{str(q)[:30]!r}")

    for group, field, src in (
            ("病药引文", "thesis", "data/sources/shen-feng-tong-kao.wikitext.txt"),
            ("化格引文", "verse", "data/sources/di-tian-sui.wikitext.txt"),
            ("从格引文", "verse", "data/sources/di-tian-sui.wikitext.txt")):
        v = (doc.get(group) or {}).get(field)
        if v is None:
            continue
        vals = v if isinstance(v, list) else [v]
        as_list = isinstance(v, list)
        L = get_lines(src)
        if L is None:
            problems.append(f"verdicts：{group}.{field} 的底本不存在 {src}")
            continue
        for i, q in enumerate(vals):
            if not q:
                continue
            n_grp += 1
            label = f"{group}.{field}[{i}]" if as_list else f"{group}.{field}"
            if not any(_verdict_plain(q) in _verdict_plain(x) for x in L):
                problems.append(f"verdicts：{label} 非书源逐字（{src}）→ "
                                f"{str(q)[:30]!r}")
    return n_loc, n_grp


def check_liushen_sources(doc_img: dict, doc_acts: dict, problems: list[str],
                          lines_of=None) -> tuple[int, int]:
    """六神取象/十神作用的行号出处回验（466 批）。返回 (取象字段数, 作用条目数)。

    为什么需要它：`liushen_image.json` 的 `_meta` 明写「值只收逐字引文与行号，
    不做改写（铁律二）」；但 466 批实抓到两条 `取象` 是**注释式改写**且没有
    `_src`，`narrate` 仍按引文渲染成「（《千里命稿》 行）」——空行号+改写句冒充
    引文（§六.3）。本函数把声明变成机械判据：

      · 每个非空 `能力/构成/取象/别名` 必须有 `<字段>_src`，形态 `data/sources/<书>:<行>`；
        行号在册、值落在该行（保标点，与 465 批同口径）；
      · `shi_shen_actions` 每条 `source` 必须能解析出行号（`L####` 或 `:####`），
        `actions` 每项须落在该行 ±3 行邻域。

    `lines_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    n_fields = n_acts = 0
    cache: dict[str, list[str] | None] = {}

    def get_lines(f: str) -> list[str] | None:
        if lines_of is not None:
            return lines_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = (p.read_text(encoding="utf-8", errors="replace").splitlines()
                        if p else None)
        return cache[f]

    img = (doc_img or {}).get("十神取象")
    if not isinstance(img, dict) or not img:
        problems.append("六神取象：十神取象缺失或为空——0 结果 ≠ 通过")
    else:
        for god, e in img.items():
            if not isinstance(e, dict):
                continue
            for key in ("能力", "构成", "取象", "别名"):
                q = e.get(key)
                if not q:
                    continue
                n_fields += 1
                src = str(e.get(key + "_src") or "").strip()
                m = _VERDICT_LOCATOR.fullmatch(src)
                if not m:
                    problems.append(f"六神取象：{god}.{key} 缺行号出处（_meta 声明"
                                    f"「值只收逐字引文与行号」）→ {str(q)[:24]!r}")
                    continue
                f, n = m.group(1), int(m.group(2))
                L = get_lines(f)
                if L is None:
                    problems.append(f"六神取象：{god}.{key} 的底本不存在 {f}")
                    continue
                if not (1 <= n <= len(L)):
                    problems.append(f"六神取象：{god}.{key} 行号 L{n} 超出底本（共 {len(L)} 行）")
                    continue
                if _verdict_plain(q) not in _verdict_plain(L[n - 1]):
                    problems.append(f"六神取象：{god}.{key} 不在所署行 {f}:{n} → "
                                    f"{str(q)[:24]!r}")

    acts = (doc_acts or {}).get("shi_shen_actions")
    if not isinstance(acts, dict) or not acts:
        problems.append("十神作用：shi_shen_actions 缺失或为空——0 结果 ≠ 通过")
    else:
        for god, e in acts.items():
            if not isinstance(e, dict):
                continue
            n_acts += 1
            src = str(e.get("source") or "")
            fm = re.match(r"(data/sources/[^: \s]+)", src)
            nm = re.search(r"(?:L|:)(\d+)", src)
            if not fm or not nm:
                problems.append(f"十神作用：{god}.source 缺可解析底本/行号 → {src!r}")
                continue
            f, n = fm.group(1), int(nm.group(1))
            L = get_lines(f)
            if L is None:
                problems.append(f"十神作用：{god}.source 的底本不存在 {f}")
                continue
            if not (1 <= n <= len(L)):
                problems.append(f"十神作用：{god}.source 行号 L{n} 超出底本（共 {len(L)} 行）")
                continue
            window = _verdict_plain("".join(L[max(0, n - 3):n + 2]))
            missing = [a for a in (e.get("actions") or [])
                       if _verdict_plain(a) not in window]
            if missing:
                problems.append(f"十神作用：{god} 的 actions 不在所署行 L{n} 邻域 → "
                                f"{missing[:3]}")
    return n_fields, n_acts


def check_quote_database(doc: dict, problems: list[str], text_of=None) -> tuple[int, int]:
    """六爻引文库 `quote_kind` 自洽与逐字回验（467 批）。返回 (verbatim 数, paraphrase 数)。

    为什么需要它：`liuyao/data/verdicts.json#quote_database` 的 `_meta` 旧写
    「引文库，source 字段为古籍出处」，但 467 批全库实测 **49 条只有 1 条能逐字回原文**，
    其余 48 条是现代今译。声明把「释义」说成「古籍引文」，属口径分家（§六.3）。
    本函数把区分变成机械判据：

      · 每条的 `quote_kind` 必须是 `verbatim` 或 `paraphrase`；
      · `verbatim` 必须带 `source_ref`（`data/sources/<file>[:<line>]`），
        文件在盘；带行号时按该行、不带行号时按整文件逐字命中（折叠标点）；
      · `paraphrase` 只需非空 `source`（所本篇章），不做逐字断言。

    `text_of` 供 selftest 注入夹具底本；正式路径现场读。
    """
    qs = (doc or {}).get("quote_database")
    if not isinstance(qs, list) or not qs:
        problems.append("引文库：quote_database 缺失或为空——0 结果 ≠ 通过")
        return 0, 0
    cache: dict[str, str | None] = {}

    def get_text(f: str) -> str | None:
        if text_of is not None:
            return text_of(f)
        if f not in cache:
            p = _resolve_any(f)
            cache[f] = p.read_text(encoding="utf-8", errors="replace") if p else None
        return cache[f]

    n_v = n_p = 0
    for i, q in enumerate(qs):
        if not isinstance(q, dict):
            problems.append(f"引文库：第 {i} 条不是对象")
            continue
        kind = str(q.get("quote_kind") or "")
        quote = str(q.get("quote") or "")
        src = str(q.get("source") or "")
        if kind not in ("verbatim", "paraphrase"):
            problems.append(f"引文库：第 {i} 条 quote_kind 缺失/非法 → {kind!r}")
            continue
        if not quote or not src:
            problems.append(f"引文库：第 {i} 条 quote/source 为空")
            continue
        if kind == "paraphrase":
            n_p += 1
            continue
        n_v += 1
        ref = str(q.get("source_ref") or "").strip()
        m = re.fullmatch(r"(data/sources/[^:]+)(?::(\d+))?", ref)
        if not m:
            problems.append(f"引文库：第 {i} 条 verbatim 缺 source_ref（file[:line]）→ {ref!r}")
            continue
        f, ln = m.group(1), m.group(2)
        body = get_text(f)
        if body is None:
            problems.append(f"引文库：第 {i} 条 source_ref 底本不存在 {f}")
            continue
        if ln:
            lines = body.splitlines()
            n = int(ln)
            if not (1 <= n <= len(lines)):
                problems.append(f"引文库：第 {i} 条 source_ref 行号 L{n} 超出底本")
                continue
            ok = _DROP.sub("", quote) in _DROP.sub("", lines[n - 1])
        else:
            ok = _DROP.sub("", quote) in _DROP.sub("", body)
        if not ok:
            problems.append(f"引文库：第 {i} 条 verbatim 引文非书源逐字（{ref}）→ "
                            f"{quote[:30]!r}")
    return n_v, n_p


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

    # 462 批：大运起例引文行锚（正例不误伤＋四类负例必抓）
    _dlines = ["如乙丑年，乙庚之岁戊为头，正月起戊寅",
               "如甲子年，甲己之年丙作首，正月逢丙寅"]
    dbase = {"_provenance": {"source_file": "data/sources/shen-feng-tong-kao.wikitext.txt"},
             "a": {"corpus_line": 2, "quote": "甲己之年丙作首"},
             "b": {"corpus_line": 1, "quote": "乙庚之岁戊为头"}}
    p_d: list[str] = []
    n_d = check_dayun_quotes(dbase, p_d, _dlines)
    if p_d or n_d != 2:
        problems.append(f"大运起例引文正例被误伤：{p_d}")

    def _dbad(mut) -> list[str]:
        d = json.loads(json.dumps(dbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_dayun_quotes(d, p, _dlines)
        return p

    if not any("不在所署行 L1" in x for x in
               _dbad(lambda d: d["a"].__setitem__("corpus_line", 1))):
        problems.append("负例未抓到：行号错（引文不在所署行）")
    if not any("超出底本" in x for x in
               _dbad(lambda d: d["a"].__setitem__("corpus_line", 99))):
        problems.append("负例未抓到：corpus_line 超出底本")
    if not any("0 条" in x for x in _dbad(lambda d: (d.pop("a"), d.pop("b")))):
        problems.append("负例未抓到：0 条目")
    p_m: list[str] = []
    check_dayun_quotes({"_provenance": {"source_file": "data/sources/__no_such__dayun.txt"},
                        "a": {"corpus_line": 1, "quote": "任意"}}, p_m)
    if not any("source_file 不存在" in x for x in p_m):
        problems.append("负例未抓到：source_file 不存在")

    # 465 批：裁决引文 locator/分支总则（夹具底本注入，不落盘）
    _vdefault = ["有病方为贵，无伤不是奇；格中如去病，财禄两相随"]
    _vlines = {
        "data/sources/__no_such__v.txt": ["", "有病方为贵，无伤不是奇"],
        "data/sources/shen-feng-tong-kao.wikitext.txt": _vdefault,
        "data/sources/di-tian-sui.wikitext.txt": _vdefault,
    }
    vbase = {
        "a": {"locator": "data/sources/__no_such__v.txt:2", "quote": "有病方为贵"},
        "病药引文": {"thesis": "有病方为贵"},
        "化格引文": {"verse": ["有病方为贵", "无伤不是奇"]},
        "从格引文": {"verse": "有病方为贵"},
    }
    p_v: list[str] = []
    n_v = check_verdicts_quotes(vbase, p_v, lambda f: _vlines.get(f))
    if p_v or n_v != (1, 4):
        problems.append(f"裁决引文正例被误伤：{p_v}（返回 {n_v}）")

    def _vbad(mut) -> list[str]:
        d = json.loads(json.dumps(vbase, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_verdicts_quotes(d, p, lambda f: _vlines.get(f))
        return p

    if not any("不在所署行" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator", "data/sources/__no_such__v.txt:1"))):
        problems.append("负例未抓到：locator 行号错（引文不在该行）")
    if not any("行号 L99 超出底本" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator", "data/sources/__no_such__v.txt:99"))):
        problems.append("负例未抓到：locator 行号越界")
    if not any("指向不存在的底本" in x for x in
               _vbad(lambda d: d["a"].__setitem__("locator",
                                                  "data/sources/__no_such__v2.txt:1"))):
        problems.append("负例未抓到：locator 底本不存在")
    if not any("病药引文.thesis" in x for x in
               _vbad(lambda d: d["病药引文"].__setitem__("thesis", "有病方为贼"))):
        problems.append("负例未抓到：分支总则引文非书源逐字")

    # 466 批：六神取象/十神作用（夹具底本注入，不落盘）
    _lline = ["", "泄身，生财，敌杀，损官"]
    limg = {"十神取象": {"伤官": {"能力": "泄身，生财",
                                  "能力_src": "data/sources/__no_such__l.txt:2"}}}
    lact = {"shi_shen_actions": {"伤官": {"actions": ["泄身", "生财"],
                                          "source": "data/sources/__no_such__l.txt:2"}}}
    p_l: list[str] = []
    n_l = check_liushen_sources(limg, lact, p_l,
                                lambda f: _lline if f.endswith("__no_such__l.txt") else None)
    if p_l or n_l != (1, 1):
        problems.append(f"六神取象/十神作用正例被误伤：{p_l}（返回 {n_l}）")

    def _lbad(mut_img=None, mut_act=None) -> list[str]:
        i = json.loads(json.dumps(limg, ensure_ascii=False))
        a = json.loads(json.dumps(lact, ensure_ascii=False))
        if mut_img:
            mut_img(i)
        if mut_act:
            mut_act(a)
        p: list[str] = []
        check_liushen_sources(i, a, p,
                              lambda f: _lline if f.endswith("__no_such__l.txt") else None)
        return p

    if not any("缺行号出处" in x for x in
               _lbad(mut_img=lambda d: d["十神取象"]["伤官"].pop("能力_src", None))):
        problems.append("负例未抓到：取象值无 _src")
    if not any("不在所署行" in x for x in
               _lbad(mut_img=lambda d: d["十神取象"]["伤官"].__setitem__("能力", "泄身，破财"))):
        problems.append("负例未抓到：取象值不在所署行")
    if not any("actions 不在所署行" in x for x in
               _lbad(mut_act=lambda d: d["shi_shen_actions"]["伤官"]["actions"].append("制杀"))):
        problems.append("负例未抓到：作用项不在所署行邻域")
    if not any("缺可解析底本/行号" in x for x in
               _lbad(mut_act=lambda d: d["shi_shen_actions"]["伤官"].__setitem__(
                   "source", "data/sources/__no_such__l.txt"))):
        problems.append("负例未抓到：作用 source 无行号")

    # 467 批：六爻引文库 quote_kind（夹具底本注入）
    _qtext = {"data/sources/__no_such__q.txt": "六合卦者，买卖交通，和合纳财，百事皆吉。"}
    qdb = {"quote_database": [
        {"pattern": "六合卦", "source": "《卜筮正宗·六合论》",
         "quote": "六合卦者，买卖交通，和合纳财，百事皆吉。",
         "quote_kind": "verbatim", "source_ref": "data/sources/__no_such__q.txt"},
        {"pattern": "六冲卦", "source": "《卜筮正宗·六冲论》",
         "quote": "六冲卦者，行人不通。", "quote_kind": "paraphrase"},
    ]}
    p_q: list[str] = []
    n_q = check_quote_database(qdb, p_q, lambda f: _qtext.get(f))
    if p_q or n_q != (1, 1):
        problems.append(f"引文库正例被误伤：{p_q}（返回 {n_q}）")

    def _qbad(mut) -> list[str]:
        d = json.loads(json.dumps(qdb, ensure_ascii=False))
        mut(d)
        p: list[str] = []
        check_quote_database(d, p, lambda f: _qtext.get(f))
        return p

    if not any("quote_kind 缺失/非法" in x for x in
               _qbad(lambda d: d["quote_database"][0].pop("quote_kind", None))):
        problems.append("负例未抓到：quote_kind 缺失")
    if not any("缺 source_ref" in x for x in
               _qbad(lambda d: d["quote_database"][0].pop("source_ref", None))):
        problems.append("负例未抓到：verbatim 缺 source_ref")
    if not any("非书源逐字" in x for x in
               _qbad(lambda d: d["quote_database"][0].__setitem__(
                   "quote", "六合卦者，买卖不通，和合纳财"))):
        problems.append("负例未抓到：verbatim 引文不在底本")
    if not any("quote/source 为空" in x for x in
               _qbad(lambda d: d["quote_database"][1].__setitem__("source", ""))):
        problems.append("负例未抓到：paraphrase 缺 source")
    if not any("行号 L99 超出底本" in x for x in
               _qbad(lambda d: d["quote_database"][0].__setitem__(
                   "source_ref", "data/sources/__no_such__q.txt:99"))):
        problems.append("负例未抓到：verbatim source_ref 行号越界")


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
    # 462 批：大运起例引文行锚（仅八字有该册；六爻无文件则跳过，不判红）
    if DAYUN.is_file():
        ddoc = json.loads(DAYUN.read_text(encoding="utf-8"))
        d_total = check_dayun_quotes(ddoc, problems)
        print(f"  大运起例引文：{d_total} 条 corpus_line+quote；source_file/行号/行内逐字已核对")
    # 465 批：裁决引文 locator/分支总则（仅八字册；六爻另有同名 data/verdicts.json，结构不同，跳过）
    if DISC.name == "bazi" and VERDICTS.is_file():
        vdoc = json.loads(VERDICTS.read_text(encoding="utf-8"))
        v_loc, v_grp = check_verdicts_quotes(vdoc, problems)
        if v_loc < 20 or v_grp < 4:
            problems.append(f"裁决引文：locator 字段 {v_loc}（下限 20）／分支总则 {v_grp}"
                            f"（下限 4）——先确认字段/路径")
        if v_loc == 0 or v_grp == 0:
            problems.append("裁决引文：有一面扫到 0 条——0 结果 ≠ 通过")
        print(f"  裁决引文：{v_loc} 个 locator 字段、{v_grp} 条分支总则引文；"
              f"行锚/文件内逐字已核对")
    # 466 批：六神取象 / 十神作用（仅八字册）
    if DISC.name == "bazi":
        if not LIUSHEN.is_file() or not SHISHEN.is_file():
            problems.append("六神取象/十神作用：数据文件缺失——0 结果 ≠ 通过")
        else:
            limg = json.loads(LIUSHEN.read_text(encoding="utf-8"))
            lact = json.loads(SHISHEN.read_text(encoding="utf-8"))
            l_fields, l_acts = check_liushen_sources(limg, lact, problems)
            if l_fields < 16 or l_acts < 7:
                problems.append(f"六神取象/十神作用：取象字段 {l_fields}（下限 16）／"
                                f"作用条目 {l_acts}（下限 7）——先确认字段/路径")
            print(f"  六神取象/十神作用：{l_fields} 个引文字段、{l_acts} 条作用枚举；"
                  f"行号出处/邻域已核对")
    # 467 批：六爻引文库 quote_kind（仅六爻册；八字同名文件结构不同）
    if DISC.name == "liuyao" and LIUYAO_QUOTES.is_file():
        qdoc = json.loads(LIUYAO_QUOTES.read_text(encoding="utf-8"))
        qv, qp = check_quote_database(qdoc, problems)
        if qv < 1 or qp < 48 or qv + qp < 49:
            problems.append(f"引文库：verbatim {qv}／paraphrase {qp}／合计 {qv + qp}"
                            f"（下限 1/48/49）——先确认字段/路径")
        print(f"  引文库：{qv + qp} 条（verbatim {qv}／paraphrase {qp}）；"
              f"quote_kind 与逐字回验已核对")
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
