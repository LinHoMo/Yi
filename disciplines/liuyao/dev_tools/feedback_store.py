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

独立判定 hit_strict / hit_loose：
    本模块自行从 analyze JSON 解析预测应期，不做任何 import from
    evaluate.py 或评分引擎，避免耦合。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / "scripts"))
try:
    from kernel_path import ensure_kernel_on_path  # type: ignore
    ensure_kernel_on_path(__file__)
except ImportError:
    pass

DAY_CHARS = "子丑寅卯辰巳午未申酉戌亥"

LOOSE_WINDOW_DAYS = 7  # loose 判定容差：预测日期 ±7 天


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


def _branch_of(date_str: str) -> str | None:
    """从 YYYY-MM-DD 反推当日地支（由日柱序数 mod 12 得到，0=子 … 11=亥）。"""
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
    except ValueError:
        return None
    seq = _day_ganzhi_seq(dt)
    return DAY_CHARS[seq % 12] if seq >= 0 else None


# 已知锚点：1900-01-31 是甲子日（序数 0）
_ANCHOR = datetime(1900, 1, 31)


def _day_ganzhi_seq(dt: datetime) -> int:
    """日柱序数（甲子=0, 乙丑=1, … 癸亥=59）。"""
    delta = (dt - _ANCHOR).days
    return delta % 60


BRANCH_WINDOW_DAYS = 21  # 地支合/冲默认窗口：自此跨度的日期内才允许按支判定


def _compute_hits(predicted_dates: list[str], actual_date: str) -> tuple[bool, bool]:
    """独立计算 hit_strict 与 hit_loose。

    hit_strict: 实际日期精确命中某条预测日（含 ±1 天容差，抵消排盘日差）。
    hit_loose: 实际日期在任一预测日的 ±LOOSE_WINDOW_DAYS 天范围内；
               或在 ±BRANCH_WINDOW_DAYS 天内且该地支与任一预测日的地支
               相同/相合/相冲（六爻应期直读法）。

    注：地支窗口约束是为了防止日期跨度过大时（如 86 天）地支恰好按周期
    重复而导致虚假命中判——地支循环周期是 12 天，会与远距日期反复重影。
    """
    if not actual_date or not predicted_dates:
        return False, False
    try:
        actual_dt = datetime.strptime(actual_date[:10], "%Y-%m-%d")
    except ValueError:
        return False, False
    actual_branch = _branch_of(actual_date)
    hit_strict = False
    hit_loose = False
    for p in predicted_dates:
        try:
            p_dt = datetime.strptime(p[:10], "%Y-%m-%d")
        except ValueError:
            continue
        delta = (actual_dt - p_dt).days
        if abs(delta) <= 1:
            hit_strict = True
            hit_loose = True
            break
        if abs(delta) <= LOOSE_WINDOW_DAYS:
            hit_loose = True
        if abs(delta) <= BRANCH_WINDOW_DAYS:
            p_branch = _branch_of(p)
            if actual_branch and p_branch and (
                actual_branch == p_branch
                or _is_he(actual_branch, p_branch)
                or _is_chong(actual_branch, p_branch)
            ):
                hit_loose = True
    return hit_strict, hit_loose


_HE = (("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"),
       ("申", "巳"), ("丑", "午"), ("未", "申"), ("戌", "卯"),
       ("亥", "寅"), ("酉", "辰"), ("巳", "申"), ("午", "未"))
_CHONG = (("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"),
          ("辰", "戌"), ("巳", "亥"))


def _is_he(a: str, b: str) -> bool:
    return (a, b) in _HE or (b, a) in _HE


def _is_chong(a: str, b: str) -> bool:
    return (a, b) in _CHONG or (b, a) in _CHONG


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
                hs, hl = _compute_hits(preds, actual)
                record.setdefault("hit_strict", hs)
                record.setdefault("hit_loose", hl)
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
