# -*- coding: utf-8 -*-
"""合参层·人的档案（person/<id>.json）模型。

schema 见 synthesis/README.md §一。要点（README 明文）：
  - birth.ganzhi 必须带 calendar_policy —— 各科年界/子时口径不同，合参就是在比两件事。
  - divinations[].outcome 是唯一能产生现实效度证据的字段，其余一律只报古籍对齐分。

本模块只做档案的加载/保存/校验与增改，不产生任何命理/占卜结论。
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

DISCIPLINES = ("liuyao", "meihua", "xiaoliuren", "zeji", "ming")
_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _valid_date(text) -> bool:
    if not _DATE_RE.match(str(text or "")):
        return False
    try:
        datetime.strptime(str(text), "%Y-%m-%d")
        return True
    except ValueError:
        return False
JUDGED = ("应验", "未应验", "部分应验", "超期未验")


class PersonError(ValueError):
    pass


class PersonArchive:
    """person/<id>.json 档案。"""

    def __init__(self, data: dict):
        self.data = data

    # ------------------------------------------------------------ 加载 / 保存
    @classmethod
    def load(cls, person_dir: str | Path, pid: str) -> "PersonArchive":
        p = Path(person_dir) / f"{pid}.json"
        if not p.exists():
            raise PersonError(f"档案不存在：{p}")
        return cls(json.loads(p.read_text(encoding="utf-8")))

    def save(self, person_dir: str | Path) -> Path:
        p = Path(person_dir) / f"{self.data['id']}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
        return p

    # ------------------------------------------------------------ 创建
    @classmethod
    def create(cls, pid: str, solar: str, *,
               longitude: float | None = None,
               ganzhi: dict | None = None,
               policy: dict | None = None,
               assembled_from: str = "raw_solar") -> "PersonArchive":
        """新建档案。ganzhi 未给时以 raw_solar 存出生时刻，命科接入后另行回填。"""
        if not pid or not pid.strip():
            raise PersonError("pid 不能为空")
        if not re.match(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$", solar):
            raise PersonError(f"出生时刻须为 'YYYY-MM-DD HH:MM'，收到 {solar!r}")
        if not re.match(r"^[A-Za-z0-9_-]+$", pid):
            raise PersonError("pid 只允许字母数字下划线连字符")
        birth = {"solar": solar, "assembled_from": assembled_from}
        if longitude is not None:
            birth["place_longitude"] = longitude
        if ganzhi:
            birth["ganzhi"] = ganzhi
        if policy:
            birth["calendar_policy"] = dict(policy)
        return cls({
            "id": pid,
            "created": datetime.now().strftime("%Y-%m-%d"),
            "birth": birth,
            "divinations": [],
            "guidance": [],
        })

    # ------------------------------------------------------------ 校验
    def validate(self) -> list[str]:
        """返回违规清单；空列表 = 合规。每条附字段路径。"""
        errs: list[str] = []
        d = self.data
        pid = d.get("id")
        if not pid:
            errs.append("id 缺失")

        birth = d.get("birth") or {}
        if not birth.get("solar"):
            errs.append("birth.solar 缺失")
        if "ganzhi" in birth:
            gz = birth["ganzhi"] or {}
            for k in ("year", "month", "day", "hour"):
                if not gz.get(k):
                    errs.append(f"birth.ganzhi.{k} 缺失")
            policy = birth.get("calendar_policy")
            if not policy or not policy.get("boundary") or not policy.get("zi_hour"):
                errs.append("birth.ganzhi 必须带 calendar_policy{boundary, zi_hour}"
                            "（口径不同＝合参在比两件事）")

        for i, div in enumerate(d.get("divinations") or []):
            p = f"divinations[{i}]"
            if not div.get("event_id"):
                errs.append(f"{p}.event_id 缺失")
            if not div.get("asked"):
                errs.append(f"{p}.asked 缺失")
            at = div.get("at")
            if at and not _AT_RE.match(str(at)):
                errs.append(f"{p}.at 格式应为 YYYY-MM-DD[ HH:MM]，收到 {at!r}")
            if div.get("discipline") not in DISCIPLINES:
                errs.append(f"{p}.discipline 须在 {DISCIPLINES}，收到 {div.get('discipline')!r}")
            oc = div.get("outcome") or {}
            if "recorded" not in oc:
                errs.append(f"{p}.outcome.recorded 缺失（须为 null 或文本）")
            elif oc["recorded"] is not None and not isinstance(oc["recorded"], str):
                errs.append(f"{p}.outcome.recorded 须为 null 或 str")
            if "judged" in oc and oc["judged"] not in JUDGED:
                errs.append(f"{p}.outcome.judged 须在 {JUDGED}，收到 {oc.get('judged')!r}")
            if "occurred_at" in oc and oc["occurred_at"] is not None \
                    and not _valid_date(oc["occurred_at"]):
                errs.append(f"{p}.outcome.occurred_at 应为有效 YYYY-MM-DD，收到 {oc.get('occurred_at')!r}")

        for i, g in enumerate(d.get("guidance") or []):
            p = f"guidance[{i}]"
            if not g.get("issued"):
                errs.append(f"{p}.issued 缺失")
            for ref in g.get("based_on") or []:
                if not re.match(r"^(liuyao|meihua|xiaoliuren|zeji|ming):", str(ref)):
                    errs.append(f"{p}.based_on 元素须形如 'discipline:…'，收到 {ref!r}")
        return errs

    # ------------------------------------------------------------ 增改
    def add_divination(self, rec: dict) -> str:
        """追加一条占问记录（rec 为归一化记录，见 normalize.py）。返回 event_id。"""
        if rec.get("discipline") not in DISCIPLINES:
            raise PersonError(f"未知学科 {rec.get('discipline')!r}")
        if not rec.get("event_id"):
            seq = len(self.data.get("divinations") or []) + 1
            rec["event_id"] = f"EVT{seq:03d}"
        rec.setdefault("outcome", {"recorded": None,
                                   "note": "待事后回填，用于真实效度"})
        self.data.setdefault("divinations", []).append(rec)
        return rec["event_id"]

    def record_outcome(self, event_id: str, result: str, *,
                       occurred_at: str | None = None,
                       judged: str | None = None) -> None:
        """回填某次占问的现实结果（唯一能产生现实效度证据的字段）。

        occurred_at：应验/观察发生的日期（YYYY-MM-DD），评应期命中用；
        judged：应验 / 未应验 / 部分应验 / 超期未验（断事层面的判定）。
        """
        if judged is not None and judged not in JUDGED:
            raise PersonError(f"judged 须在 {JUDGED}，收到 {judged!r}")
        if occurred_at is not None and not _valid_date(occurred_at):
            raise PersonError(f"occurred_at 应为有效 YYYY-MM-DD，收到 {occurred_at!r}")
        for div in self.data.get("divinations") or []:
            if div.get("event_id") == event_id:
                oc = div.setdefault("outcome", {})
                oc["recorded"] = result
                if occurred_at is not None:
                    oc["occurred_at"] = occurred_at
                if judged is not None:
                    oc["judged"] = judged
                oc["note"] = f"回填于 {datetime.now().strftime('%Y-%m-%d')}"
                return
        raise PersonError(f"无此占问记录：{event_id}")

    def add_guidance(self, entry: dict) -> None:
        """追加一条指导记录（entry 须含 issued/window/advice/based_on）。"""
        for key in ("issued", "advice", "based_on"):
            if key not in entry:
                raise PersonError(f"guidance 缺 {key}")
        self.data.setdefault("guidance", []).append(entry)
