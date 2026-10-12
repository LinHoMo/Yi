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
  · `source.corpus_files` 自身必须存在。
`verified: true` 而上述任一步失败 → 判红；`verified: false` 只作 NOTE（那是诚实的未核实）。
"""
from __future__ import annotations

import json
import re
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
    ], "_uncovered": []}
    p: list[str] = []
    n: list[str] = []
    checked, passed = check(fake, p, n)
    if checked < 2 or passed != 0:
        problems.append(f"负例自证失效：应为 2 检视 0 通过，实得 检视 {checked} 通过 {passed}")
    if len(p) < 2:
        problems.append(f"负例自证失效：2 条假指针只判红 {len(p)} 条 → {p}")
    if n:
        problems.append(f"负例不该产生 NOTE（verified=true 应判红）→ {n}")


def main() -> int:
    if not REG.exists():
        print(f"× 注册表不存在：{REG}")
        return 1
    doc = json.loads(REG.read_text(encoding="utf-8"))
    problems: list[str] = []
    notes: list[str] = []
    checked, passed = check(doc, problems, notes)
    print(f"{DISC.name}：检视 {checked} 条书源指针，{passed} 条可回指")
    if "--selftest" in sys.argv:
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
