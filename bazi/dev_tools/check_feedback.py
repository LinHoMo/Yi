# -*- coding: utf-8 -*-
"""现实反馈通道的回验门（#32 的门禁那一半）。

通道建起来而没人回验，就会变成第二具死副本——本仓已有一份那样的东西
（`core/yishu_core/feedback.py` 在八字树里躺了很久，只有六爻的 adapter）。所以本器验四件事：

  [1] 内核两份 `SOURCE_SYSTEMS` 都登记了 `bazi.feedback_store`，且**两科副本逐字相同**（孪生漂移守卫）；
  [2] `bazi/dev_tools/feedback_store.py --selftest` 的 4 类负例真的被抓（含 §三.4 的引擎回填拦截）；
  [3] 真实在册记录每条都能折成 canonical `FeedbackRecord` 且 `validate_feedback_record` 无告；
  [4] **空库存要说空话**：0 条回填就明报"可测性尚未闭合"，绝不让"通道已建"被读成"有现实证据"。

自检一律走临时目录（`SKILL.md` 铁律二）；读数一律称**现实回填对齐**，不称命中率（§四.4）。

    python dev_tools/check_feedback.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
ROOT = DISC.parent
sys.path.insert(0, str(DISC / "core"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.feedback import (SOURCE_SYSTEMS, from_bazi_feedback,  # noqa: E402
                                 validate_feedback_record)

force_utf8_stdio()

CORE_COPIES = (DISC / "core/yishu_core/feedback.py",
               ROOT / "liuyao/core/yishu_core/feedback.py")


def _digest(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest() if p.exists() else "<缺失>"


def main() -> int:
    errs: list[str] = []
    # [1] 登记 + 孪生一致
    if "bazi.feedback_store" not in SOURCE_SYSTEMS:
        errs.append("内核 SOURCE_SYSTEMS 未登记 bazi.feedback_store（adapter 无处可依）")
    digs = {str(p): _digest(p) for p in CORE_COPIES}
    if len(set(digs.values())) != 1:
        errs.append(f"两科内核副本已漂移：{digs}（canonical schema 只许一份）")

    # [2] 通道自检的负例真有牙齿（子进程实跑，不读源码猜）
    r = subprocess.run([sys.executable, str(DISC / "dev_tools/feedback_store.py"), "--selftest"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        errs.append(f"feedback_store --selftest 未过（rc={r.returncode}）：{out.strip()[:160]}")
    for kw in ("SELFTEST OK", "复制断语", "引擎出处", "自造判词", "覆盖现实"):
        if kw not in out:
            errs.append(f"负例清单缺项『{kw}』——拦截逻辑没被验到")

    # [3] 在册记录逐条可折叠、可校验
    store = DISC / "logs" / "reading_events.jsonl"
    recs = []
    if store.exists():
        for n, line in enumerate(store.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                recs.append(json.loads(line))
            except json.JSONDecodeError as exc:
                errs.append(f"{store.name} 第 {n} 行非法 JSON：{exc}")
    bad = 0
    for rec in recs:
        v = validate_feedback_record(from_bazi_feedback(rec))
        if v:
            bad += 1
            errs.append(f"{rec.get('event_id')}：不合 canonical schema → {v}")

    # [4] 空库要说空话
    filled = [x for x in recs if x.get("actual_outcome")]
    print(f"现实反馈通道：在册 {len(recs)} 条（schema 违规 {bad}），已回填现实 {len(filled)} 条，"
          f"待回填 {len(recs) - len(filled)} 条｜内核两副本一致={len(set(digs.values())) == 1}")
    if not filled:
        print("  注：尚无任何现实回填 ⇒ **可测性已从 0 变为可测，但现实证据仍为 0**。"
              "此数不得与古籍案例对齐分混算，也不构成任何命中率／准确率（§四.4、铁律三）。")

    for e in errs:
        print("  ×", e)
    if errs:
        return 1
    print("通道各项一致，负例有牙齿，在册记录合 schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
