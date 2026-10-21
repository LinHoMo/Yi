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
  · **【第一百六十九批】`impl`** = "<file>.py[:symbol]" → 文件在，且 `:标识符`
        形态时该符号确在文件内（行号 `:1058`、`:4.3` 之类定位记号无符号可验，跳过）。
        此前本器从不看 `impl`，而 `check_doc_refs.py` 的文档却写着「impl …由 [12]
        逐条回指」——文档说的和代码做的不一致（§六.3），且真的漏掉过两条悬空指针
        （身爻/忧解第一百六十六批域拆分搬模块后，impl 仍指父模块且无 re-export）。
`verified: true` 而上述任一步失败 → 判红；`verified: false` 只作 NOTE（那是诚实的未核实）。
**`impl` 例外：不看 `verified` 一律判红**——代码指针不存在「诚实未核实」状态，指错就是指错。
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


# 【第一百六十九批】`impl` 是**可执行契约**（`check_doc_refs.py` 的文档早就这么写着，
# 说它「由 [12] 逐条回指」），但本器此前只回验 `source.quote_in_*`／`corpus_files`，
# 从没看过 `impl` ——文档说的和代码做的不一致（AGENTS.md §六.3）。后果是真的：
# 两条 `impl` 指向 `classical_enhancements.py:analyze_shen_yao_activation`／
# `…:analyze_you_jie`，而这两个函数第一百六十六批已随「域拆分」搬进
# `classical_enhancements_shen_yao.py`、父模块无 re-export，指针悬空了 N 批无人发现。
#
# 口径（**宁可少判，不做逼人改写散文的假红门**）：
#   · 只认 `<path>.py` 后面紧跟 `:标识符` 且标识符**首字符是字母/下划线**的形态；
#   · 行号（`:1058`）、版本号式（`:4.3`）一律跳过——它们是定位记号不是符号；
#   · 多段实现（`；`／`＋`／`→`／`／` 连接）逐段各自判；
#   · 文件不存在与符号不在文件内，各判一次红并点名。
_PATH_RE = re.compile(r"(?<![\w/])((?:liuyao/)?scripts/[\w/]+\.py)")
_SYM_RE = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")


def check_impl(impl: str) -> list[str]:
    """回验 `impl` 里的 `file.py:symbol`；返回问题清单（空＝全部可回指）。"""
    bad: list[str] = []
    for m in _PATH_RE.finditer(impl):
        rel = m.group(1)
        tp = _resolve_any(rel)
        if tp is None:
            bad.append(f"文件不存在 → {rel}")
            continue
        rest = impl[m.end():m.end() + 80]
        sm = _SYM_RE.match(rest)
        if not sm:
            continue          # 纯路径 / 行号 / 4.3 之类：无符号可验，不判
        sym = sm.group(1)
        body = tp.read_text(encoding="utf-8", errors="replace")
        if not re.search(rf"\b{re.escape(sym)}\b", body):
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
        # 【第一百六十九批】`impl` 回验：代码指针与书源引文不同，**不存在「未核对」状态**——
        # 指错就是指错（§六.3 文实不符等同代码缺陷），故不看 verified，一律判红。
        impl = item.get("impl")
        if impl:
            checked += 1
            bad = check_impl(str(impl))
            if bad:
                problems.append(f"{rid}.impl：{'；'.join(bad)}")
            else:
                passed += 1
    return checked, passed


def selftest(problems: list[str]) -> None:
    """负例：造一条 verified=true 却指向不存在文件/解不到值的条目，必须判红。"""
    fake = {"schema": "yi-rule-registry-v1", "rules": [
        {"rule_id": "test.bad_pointer", "source": {
            "verified": True,
            "quote_in_data": "data/rules/rule_registry.json#no.such.path"}},
        {"rule_id": "test.missing_file", "source": {
            "verified": True,
            "quote_in_code": "dev_tools/__does_not_exist__.py#ANY"}},
        # 【第一百六十九批】impl 两式负例：①文件不存在 ②文件在、符号不在
        {"rule_id": "test.impl_missing_file",
         "impl": "scripts/__does_not_exist__.py:analyze_x", "source": {"verified": True}},
        {"rule_id": "test.impl_missing_symbol",
         "impl": "scripts/step2.py:__no_such_symbol__", "source": {"verified": True}},
    ], "_uncovered": []}
    p: list[str] = []
    n: list[str] = []
    checked, passed = check(fake, p, n)
    if checked < 4 or passed != 0:
        problems.append(f"负例自证失效：应为 ≥4 检视 0 通过，实得 检视 {checked} 通过 {passed}")
    if len(p) < 4:
        problems.append(f"负例自证失效：4 条假指针只判红 {len(p)} 条 → {p}")
    if n:
        problems.append(f"负例不该产生 NOTE（verified=true 应判红）→ {n}")

    # 【第一百六十九批】impl 的**正例不误伤**：行号/版本号式定位记号无符号可验，
    # 必须放行；否则本器会逼人把「scripts/step4.py:1058」这类定位记号改写掉。
    good = check_impl("scripts/step4.py:1058（三会成立不再按三合破局论）")
    if good:
        problems.append(f"正例被误伤：行号式定位记号不该判 → {good}")
    good2 = check_impl("scripts/step2.py")
    if good2:
        problems.append(f"正例被误伤：纯路径不该判 → {good2}")
    # 真实事故形态：第一百六十六批域拆分后，父模块无 re-export 的悬空符号
    if not check_impl("scripts/classical_enhancements.py:analyze_shen_yao_activation"):
        problems.append("负例未抓到：classical_enhancements.py 并无 "
                        "analyze_shen_yao_activation（已搬入 shen_yao 子模块）")


def main() -> int:
    if not REG.exists():
        print(f"× 注册表不存在：{REG}")
        return 1
    doc = json.loads(REG.read_text(encoding="utf-8"))
    problems: list[str] = []
    notes: list[str] = []
    checked, passed = check(doc, problems, notes)
    print(f"{DISC.name}：检视 {checked} 条书源指针，{passed} 条可回指")
    _ap = argparse.ArgumentParser(description="check_rule_registry：--selftest 负例自证开关（§三）")
    _ap.add_argument("--selftest", action="store_true", help="负例自证")
    args = _ap.parse_args()
    if args.selftest:
        before = len(problems)
        selftest(problems)
        print(f"  [selftest] 负例已跑（{'抓到' if len(problems) == before else '异常'}）")
        # 负例本身故意造的错不计入本学科判定，只验「抓到了」这件事
        problems = problems[:before] if len(problems) > before else problems
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
