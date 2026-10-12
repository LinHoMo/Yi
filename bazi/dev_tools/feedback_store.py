# -*- coding: utf-8 -*-
"""八字科现实反馈通道（#32）：把"当时断了什么"与"后来实际如何"分两次落盘。

为什么要有它：八字侧此前**没有通道**（无 `logs/`、无 store、无回看器），
所以"回填 0 条"其实是**可测性为 0**——见 `docs/EVAL-PLAN.md` §七。本器只做一件事：
让"现实证据"第一次有地方放，并**用结构拦住建号**（不是靠自觉）。

三条硬规矩（都写成代码，不写进注释就算了）：

1. **AGENTS.md §三.4：禁止用引擎输出回填基准。**
   `backfill()` 拒收两类记录：`actual_outcome` 与引擎当时的 `engine_claim` 同串
   （那是抄引擎结论，不是现实），以及 `source_note` 里出现引擎／评测／金标准等字样。
2. **`SKILL.md` 铁律二：自检只写临时目录。** 构造器可传 `path`；
   `--selftest` 一律走 `tempfile`，绝不往真实 `logs/` 播种。
3. **`SKILL.md` 铁律一：判词外置。** `judged` 只准取内核 `JUDGED_VALUES` 的词汇，
   本器不自造吉凶词，也不把"应验"折算成分数。

读数口径：产出的永远是**现实回填对齐**（带 n 与集合名），不是命中率／准确率，
更不与古籍案例对齐分混算——两者分母不同、可比性不同（§四.4）。

    python dev_tools/feedback_store.py log   --id E001 --question "占功名" --chart "丙午 庚寅 丙午 庚寅" --claim "官印相生，有科名之象"
    python dev_tools/feedback_store.py fill  --id E001 --actual "次年甲榜及第" --occurred-at 2027-05-01 --judged 应验 --source-note "来访者面述"
    python dev_tools/feedback_store.py list
    python dev_tools/feedback_store.py stats
    python dev_tools/feedback_store.py --selftest
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DISC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DISC / "core"))

from yishu_core.runtime import force_utf8_stdio  # noqa: E402  GBK 控制台下中文不乱码
from yishu_core.feedback import (JUDGED_VALUES, from_bazi_feedback,  # noqa: E402
                                 validate_feedback_record)

force_utf8_stdio()

DEFAULT_PATH = DISC / "logs" / "reading_events.jsonl"

# 现实情形只能来自人的事后记述；这些字样一出现就说明"实际"是引擎侧复制来的
BANNED_SOURCE = ("引擎", "engine", "evaluate", "golden", "金标准", "回归", "regression", "输出")


class FeedbackStore:
    def __init__(self, path: Path | str = DEFAULT_PATH):
        self.path = Path(path)

    # ── 读写 ────────────────────────────────────────────────
    def load(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for n, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{self.path.name} 第 {n} 行不是合法 JSON：{exc}") from exc
        return out

    def _write_all(self, recs: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs),
                             encoding="utf-8")

    # ── 登记断语（不含任何现实信息）──────────────────────────
    def log_reading(self, *, event_id: str, question: str, chart: str,
                    engine_claim: str, gender: str = "") -> dict:
        if not (event_id and question and engine_claim):
            raise ValueError("event_id／question／engine_claim 三项齐备才可登记（缺项＝无法事后对账）")
        recs = self.load()
        if any(r.get("event_id") == event_id for r in recs):
            raise ValueError(f"event_id {event_id} 已存在：断语一经落盘不得改写")
        rec = {
            "event_id": event_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "question": question,
            "chart": chart,
            "gender": gender,
            "engine_claim": engine_claim,
            "actual_outcome": "",
            "occurred_at": "",
            "judged": "",
            "source_note": "",
        }
        errs = validate_feedback_record(from_bazi_feedback(rec))
        if errs:
            raise ValueError(f"记录不合 canonical schema：{errs}")
        self._write_all(recs + [rec])
        return rec

    # ── 事后回填现实（§三.4 的结构性拦截在这里）───────────────
    def backfill(self, event_id: str, *, actual_outcome: str, occurred_at: str,
                 judged: str, source_note: str) -> dict:
        recs = self.load()
        rec = next((r for r in recs if r.get("event_id") == event_id), None)
        if rec is None:
            raise ValueError(f"找不到 event_id {event_id}：先 log 再 fill")
        if rec.get("actual_outcome"):
            raise ValueError(f"{event_id} 已回填过：现实记录不得覆盖（要改请新增一条并注引用）")
        if judged not in JUDGED_VALUES:
            raise ValueError(f"judged 须取自内核 JUDGED_VALUES（{list(JUDGED_VALUES)}），实到：{judged!r}")
        if not (actual_outcome.strip() and source_note.strip()):
            raise ValueError("actual_outcome 与 source_note 均不可空：无出处的现实记述不进册")
        low = source_note.lower()
        hit = [b for b in BANNED_SOURCE if b in low or b in source_note]
        if hit:
            raise ValueError(f"source_note 含引擎侧字样 {hit}——按 §三.4 现实情形不得取自引擎输出")
        if actual_outcome.strip() == str(rec.get("engine_claim") or "").strip():
            raise ValueError("actual_outcome 与当时断语逐字相同：那是复制引擎结论，不是现实回填")
        rec.update({"actual_outcome": actual_outcome, "occurred_at": occurred_at,
                    "judged": judged, "source_note": source_note})
        errs = validate_feedback_record(from_bazi_feedback(rec))
        if errs:
            raise ValueError(f"回填后不合 canonical schema：{errs}")
        self._write_all(recs)
        return rec

    # ── 读数 ────────────────────────────────────────────────
    def stats(self) -> dict:
        recs = self.load()
        filled = [r for r in recs if r.get("actual_outcome")]
        judged = {}
        for r in filled:
            judged[r["judged"]] = judged.get(r["judged"], 0) + 1
        return {"在册断语": len(recs), "已回填现实": len(filled),
                "待回填": len(recs) - len(filled), "判定分布": judged}


def selftest() -> list[str]:
    """全部写临时目录（铁律二）。四条负例都要被抓，正例要能走通。"""
    errs: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        st = FeedbackStore(Path(td) / "events.jsonl")
        st.log_reading(event_id="T1", question="占功名", chart="丙午 庚寅 丙午 庚寅",
                       engine_claim="官印相生，有科名之象")
        # 负例①：现实=复制断语
        try:
            st.backfill("T1", actual_outcome="官印相生，有科名之象", occurred_at="2027-05-01",
                        judged="应验", source_note="来访者面述")
            errs.append("负例①失效：逐字复制断语没被抓")
        except ValueError:
            pass
        # 负例②：出处写着引擎
        try:
            st.backfill("T1", actual_outcome="次年果捷", occurred_at="2027-05-01",
                        judged="应验", source_note="按引擎输出整理")
            errs.append("负例②失效：引擎侧出处没被抓")
        except ValueError:
            pass
        # 负例③：判定词不在内核词表
        try:
            st.backfill("T1", actual_outcome="次年果捷", occurred_at="2027-05-01",
                        judged="很准", source_note="来访者面述")
            errs.append("负例③失效：自造判词没被抓（铁律一）")
        except ValueError:
            pass
        # 正例：人记的现实可以入册，且重复回填被拒
        st.backfill("T1", actual_outcome="次年甲榜及第", occurred_at="2027-05-01",
                    judged="应验", source_note="来访者面述")
        try:
            st.backfill("T1", actual_outcome="另说", occurred_at="2027-06-01",
                        judged="未应验", source_note="来访者面述")
            errs.append("负例④失效：已回填的例被允许覆盖")
        except ValueError:
            pass
        s = st.stats()
        if not (s["在册断语"] == 1 and s["已回填现实"] == 1 and s["判定分布"].get("应验") == 1):
            errs.append(f"正例失效：临时库读数不对 → {s}")
    if not path_guard_ok():
        errs.append("守卫失效：真实 logs/ 被自检写过")
    return errs


def path_guard_ok() -> bool:
    """自检不许碰真实落盘文件。"""
    return DEFAULT_PATH.exists() is False or DEFAULT_PATH.read_text(encoding="utf-8").strip() == ""


def main() -> int:
    ap = argparse.ArgumentParser(description="八字科现实反馈通道")
    ap.add_argument("cmd", nargs="?", choices=["log", "fill", "list", "stats"])
    ap.add_argument("--id", dest="event_id", default="")
    ap.add_argument("--question", default="")
    ap.add_argument("--chart", default="")
    ap.add_argument("--claim", dest="engine_claim", default="")
    ap.add_argument("--gender", default="")
    ap.add_argument("--actual", dest="actual_outcome", default="")
    ap.add_argument("--occurred-at", default="")
    ap.add_argument("--judged", default="")
    ap.add_argument("--source-note", default="")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    st = FeedbackStore()

    if args.selftest:
        bad = selftest()
        print("SELFTEST OK：4 类负例（复制断语／引擎出处／自造判词／覆盖现实）全被抓，正例走通"
              if not bad else "SELFTEST FAIL：" + "；".join(bad))
        return 1 if bad else 0
    if not args.cmd:
        ap.print_help()
        return 2
    try:
        if args.cmd == "log":
            r = st.log_reading(event_id=args.event_id, question=args.question, chart=args.chart,
                               engine_claim=args.engine_claim, gender=args.gender)
            print(f"已登记断语 {r['event_id']} @ {r['recorded_at']}（现实字段留空，待回填）")
        elif args.cmd == "fill":
            r = st.backfill(args.event_id, actual_outcome=args.actual_outcome,
                            occurred_at=args.occurred_at, judged=args.judged,
                            source_note=args.source_note)
            print(f"已回填 {r['event_id']}：{r['judged']}｜{r['actual_outcome'][:30]}")
        elif args.cmd == "list":
            recs = st.load()
            print(f"在册 {len(recs)} 条")
            for r in recs:
                print(f"  · {r.get('event_id')}｜断：{str(r.get('engine_claim'))[:26]}"
                      f"｜实：{str(r.get('actual_outcome'))[:26] or '（待回填）'}｜{r.get('judged') or '—'}")
        else:
            print(json.dumps(st.stats(), ensure_ascii=False))
    except ValueError as exc:
        print(f"× 拒绝：{exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
