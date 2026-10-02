# -*- coding: utf-8 -*-
"""真实应期反馈存储 —— 与古籍案例和调参引擎完全物理隔离。

存储位置: disciplines/liuyao/data/feedback/
永不参与调参（.gitignore 隔离）。

用法：
    from feedback_store import FeedbackStore
    store = FeedbackStore()
    rid = store.save(record)
    all_records = store.load_all()
    s = store.stats()

命中判定（strict / loose）的口径与常量**不在此处持有**：唯一真值源是
`yishu_core.yingqi`（架构评审 A2——此前本模块与合参层 `synthesis/outcome_eval.py`
各写一份应期口径，且本地支合表多出两条错项「丑午」「未申」，会造成虚假宽松命中；
现两处统一读内核一份，门 `tools/check.py [1i]` 锁死）。
本模块只做本学科的事：从 analyze JSON 取预测应期、落盘与汇总。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / "scripts"))
try:
    from kernel_path import ensure_kernel_on_path  # type: ignore
    ensure_kernel_on_path(__file__)
except ImportError:
    pass

# 判定口径唯一真值源（本模块不再持有任何窗口常量或支关系表）
from yishu_core.yingqi import (  # noqa: E402,F401
    BRANCH_WINDOW_DAYS,
    LOOSE_WINDOW_DAYS,
    STRICT_WINDOW_DAYS,
    WINDOW_CALIBER,
    branch_of as _branch_of,
    judge_window as _judge_window,
)


def _discipline_root(start_file: str | Path) -> Path:
    p = Path(start_file).resolve()
    for cand in (p, *p.parents):
        if (cand / "SKILL.md").is_file():
            return cand
    return Path(start_file).resolve().parents[1]


def _extract_yingqi_dates(analyze_json: dict) -> list[str]:
    """从 analyze JSON 的 conclusion 中提取预测日期（YYYY-MM-DD 格式列表）。"""
    dates: list[str] = []
    conclusion = analyze_json.get("conclusion") or {}
    for item in (conclusion.get("应期明细") or []):
        d = (item.get("date") or "").strip() if isinstance(item, dict) else ""
        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", d):
            dates.append(d)
    if not dates:
        for s in (conclusion.get("应期") or []):
            m = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", str(s))
            if m:
                dates.append(m.group(1))
    return dates


def _make_chart_id(analyze_json: dict) -> str:
    """从 analyze JSON 生成简短稳定的 chart_id。"""
    s = json.dumps(analyze_json, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]


class FeedbackStore:
    """存储真实应期反馈。

    存储位置: disciplines/liuyao/data/feedback/
    永不参与调参（.gitignore 隔离）。
    """

    def __init__(self, discipline: str = "liuyao"):
        root = _discipline_root(__file__)
        self.discipline = discipline
        self.dir = root / "data" / "feedback"
        self.dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: dict) -> str:
        """写入一条反馈记录，返回 record_id。

        调用方可直接传入完整 compute 好的 dict，或传入最小参数字段让本方法补全：
          store.save({"analyze_json": a, "actual_date": "2026-10-15"})
        内部自动补全 predicted_dates、chart_id、hit_strict、hit_loose。
        """
        now = datetime.now()
        if "analyze_json" in record and "chart_id" not in record:
            record["chart_id"] = _make_chart_id(record["analyze_json"])
        if "analyze_json" in record and "predicted_dates" not in record:
            record["predicted_dates"] = _extract_yingqi_dates(record["analyze_json"])
        if "analyze_json" in record and "predicted_main_yingqi" not in record:
            dates = record.get("predicted_dates") or _extract_yingqi_dates(record["analyze_json"])
            if dates:
                record["predicted_main_yingqi"] = dates[0]
            else:
                conclusion = (record["analyze_json"].get("conclusion") or {})
                yq_list = conclusion.get("应期") or []
                record["predicted_main_yingqi"] = yq_list[0] if yq_list else ""
        if "predicted_window" not in record:
            dates = record.get("predicted_dates") or []
            if len(dates) >= 2:
                record["predicted_window"] = f"相对窗 [{dates[0]}..{dates[-1]}]"
            elif dates:
                record["predicted_window"] = f"相对窗 [{dates[0]}..{dates[0]}]"
            else:
                record["predicted_window"] = "缺预测应期"
        if "actual_date" in record:
            actual = record["actual_date"]
            preds = record.get("predicted_dates") or []
            if actual:
                # 口径唯一真值源：yishu_core.yingqi.judge_window
                jw = _judge_window(preds, actual)
                record.setdefault("hit_strict", jw["hit_strict"])
                record.setdefault("hit_loose", jw["hit_loose"])
            else:
                record.setdefault("hit_strict", False)
                record.setdefault("hit_loose", False)
        rid = record.get("id") or "fb_{:%Y%m%d}_{}".format(now, os.urandom(3).hex())
        record["id"] = rid
        if "timestamp" not in record:
            record["timestamp"] = now.isoformat(timespec="seconds")
        if "discipline" not in record:
            record["discipline"] = self.discipline
        path = self.dir / f"{rid}.json"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return rid

    def load_all(self) -> list[dict]:
        """加载全部已提交的反馈记录。"""
        if not self.dir.exists():
            return []
        records = []
        for p in sorted(self.dir.glob("fb_*.json")):
            try:
                records.append(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return records

    def stats(self) -> dict:
        """读数汇总：n、strict_hit_rate、loose_hit_rate、有日期反馈数。"""
        records = self.load_all()
        total = len(records)
        with_actual = [r for r in records if r.get("hit_strict") is not None
                       or r.get("actual_date")]
        strict_hits = sum(1 for r in with_actual if r.get("hit_strict"))
        loose_hits = sum(1 for r in with_actual if r.get("hit_loose"))
        n_actual = len(with_actual)
        return {
            "total_records": total,
            "with_actual_outcome": n_actual,
            "strict_hits": strict_hits,
            "loose_hits": loose_hits,
            "strict_hit_rate": round(strict_hits * 100.0 / n_actual, 1) if n_actual else None,
            "loose_hit_rate": round(loose_hits * 100.0 / n_actual, 1) if n_actual else None,
        }
