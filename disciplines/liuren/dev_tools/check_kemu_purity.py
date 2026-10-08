# -*- coding: utf-8 -*-
"""kemu.json 吉凶句混淆审计门：确保 verse/note 中的叙事候选句不得作为 IMPLEMENTED 依据。

纪律（AGENTS.md 铁律一/三）：
  - verse/note 里一切含吉凶方向词的字段，都必须独立标记 `narrative_candidate: true`；
    未标记者视为「吉凶句混入结构条件层」，审计判红。
  - 审计门不判断吉凶方向，只做「结构条件 vs 叙事句」的机械混淆检测。

检测范围（仅 v+note 字段，不碰 rules/aliases/xinjing_旁证等其它节）：
  - verse 字段中含下列任一即视为"含叙事候选"：
      吉、凶、利、不利、宜、不宜、主死、主祸、主灾、主殃、主刑、主凶
  - note 字段中含上述任一，同上。
  - 命中后：narrative_candidate 字段须为 true，否则 EXIT≠0。

负例自证（铁律四.8）：
  `--self-test` 注入一条 mock entry（含「主死」但未标 narrative_candidate），
  门应判红并报出 mock 行号，随后恢复原文件（不污染工作区）。
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
KEMU = DISC / "data" / "kemu.json"

# 叙事候选方向词表（机械文本匹配，不判断语义，不出吉凶方向）
NARRATIVE_KEYWORDS = [
    "吉", "凶", "不利", "不宜", "主死", "主祸", "主灾", "主殃", "主刑", "主凶",
]

# 注：单字「利」「宜」易撞普通词（如"利用"、"宜退"是动词，非吉凶判断），
# 故以双字组合 / 主字结构为主，避免误判；单字凶字「凶」「主」开头的已在集合里。
# 严格匹配采用**子串包含**，属机械比对。


def _contains_narrative(text: str) -> list[str]:
    """返回 field 中命中的叙事关键词列表（空=无命中）。"""
    return [kw for kw in NARRATIVE_KEYWORDS if kw in text]


def audit(entries: list[dict], src_label: str = "kemu.json") -> list[str]:
    """逐条审计：每条 entry 返回错误串（pass 返回 []）。"""
    errors: list[str] = []
    for i, e in enumerate(entries):
        name = e.get("name", f"<无name index={i}>")
        has_narrative = False
        parts: list[str] = []

        verse = e.get("verse", "")
        hit_v = _contains_narrative(verse)
        if hit_v:
            has_narrative = True
            parts.append(f"verse含{hit_v}")

        note = e.get("note", "")
        hit_n = _contains_narrative(note)
        if hit_n:
            has_narrative = True
            parts.append(f"note含{hit_n}")

        flagged = e.get("narrative_candidate", False)
        if has_narrative and not flagged:
            errors.append(
                f"  [{src_label}] entries[{i}] {name}：含叙事候选词（{'，'.join(parts)}），"
                f"未标 narrative_candidate=true → 判红"
            )
    return errors


def run_self_test() -> list[str]:
    """负例自证：塞入一条明知含「主死」但未打标目的 mock entry，确认判红。"""
    mock_path = DISC / "data" / "__narrative_self_test__.json"
    try:
        payload = {
            "schema": "self-test/mock",
            "entries": [
                {
                    "name": "__ MOCK_NARRATIVE __",
                    "verse": "mock verse",
                    "note": "此课主死，占者凶。",  # 明知含主死
                    # 故意不标 narrative_candidate
                    "implemented": False,
                }
            ],
        }
        mock_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        errors = audit(payload["entries"], src_label="__narrative_self_test__")
        return errors
    finally:
        if mock_path.exists():
            mock_path.unlink()


def main() -> int:
    args = sys.argv[1:]
    rc = 0

    # ---- 负例自证 ----
    if "--self-test" in args:
        print("[negative self-test] 注入含「主死」但未标目的 mock entry，期望判红：")
        st_errs = run_self_test()
        if st_errs:
            for e in st_errs:
                print(e)
            print("[negative self-test] PASS：门正确判红（EXIT 将置 1 仅对主审计生效）")
        else:
            print("[negative self-test] FAIL：门未判红 → 豁免逻辑失效")
            rc = 2

    # ---- 主审计 ----
    print("\n[kemu purity audit] 机械扫描 note/verse 中的叙事候选句 + narrative_candidate 必须成对：")
    data = json.loads(KEMU.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    errs = audit(entries)
    if errs:
        for e in errs:
            print(e)
        print(f"\nRESULT: FAIL — {len(errs)} 条叙事候选未标记")
        rc = 1
    else:
        # 总条目数 + 已标系统计
        flagged_cnt = sum(1 for e in entries if e.get("narrative_candidate", False))
        print(
            f"RESULT: PASS — 共 {len(entries)} 条课目，"
            f"{flagged_cnt} 条含叙事候选已标，无混淆"
        )
    return rc


if __name__ == "__main__":
    sys.exit(main())
