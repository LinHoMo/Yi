# -*- coding: utf-8 -*-
"""Request 契约与深链语义 parity 测试（P1 稳定协议）。

覆盖：
  7. CLI/Web/Actions request parity —— 同一输入在所有入口产生同一 normalized
     request；同一 normalized request 产出同一 chart argv（宿主无关）。
  8. deep-link semantic parity —— web.js DEEPLINK_KEYS 的短键映射在 Python 侧
     模拟后，与完整字段请求归一化结果逐字段一致；短键集合锁定在
     REQUEST_FIELDS 白名单内（[1h] 门的 pytest 侧等价）。

协议指纹基线（normalize_request 正/负例）另有 [1f] 门
`tools/request_protocol_golden.py`，此处不重复其逐字段指纹。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report.request import (  # noqa: E402
    REQUEST_FIELDS,
    chart_argv,
    normalize_request,
)


def _read_deeplink_keys() -> dict[str, str]:
    """从 web.js 读 DEEPLINK_KEYS（短键 → 请求字段），与 [1h] 同源而非复制。"""
    js = (ROOT / "web" / "web.js").read_text(encoding="utf-8")
    block = re.search(r"DEEPLINK_KEYS\s*=\s*\{(.*?)\}", js, re.S)
    assert block, "web.js 缺 DEEPLINK_KEYS"
    return {k: v for k, v in re.findall(r"(\w+):\s*'([^']+)'", block.group(1))}


def _apply_deeplink(query: str) -> dict:
    """模拟 web.js readDeepLink()：d=学科 + 短键 → 请求 dict（空值丢弃）。"""
    keys = _read_deeplink_keys()
    qs = parse_qs(query)
    out: dict = {}
    disc = qs.get("d") or qs.get("discipline")
    if disc:
        out["discipline"] = disc[-1]
    for short, key in keys.items():
        if short in qs and qs[short][-1]:
            out[key] = qs[short][-1]
    return out


class TestEntryParity:
    """一个输入在不同入口产生完全相同的 normalized request。"""

    FULL_REQUESTS = [
        {"discipline": "liuyao", "question": "占求财", "mode": "time",
         "datetime": "2026-09-30 10:30"},
        {"discipline": "ming", "question": "命盘", "datetime": "1990-05-20 10:30",
         "gender": "男"},
        {"discipline": "meihua", "question": "占投资", "way": "numbers",
         "numbers": "3,5,7"},
        {"discipline": "zeji", "date": "2026-09-30", "activity": "开市"},
        {"discipline": "lingqi", "up": 2, "mid": 1, "down": 3, "question": "占问"},
    ]

    def test_normalize_is_entry_independent(self) -> None:
        """normalize_request 是纯函数：同一 dict 从任何入口进来结果一致。"""
        for req in self.FULL_REQUESTS:
            a = normalize_request(dict(req))
            b = normalize_request(dict(req))
            assert a == b
            # 归一化输出只含白名单字段（无入口私有字段混入）
            assert set(a) <= set(REQUEST_FIELDS)

    def test_date_alias_same_argv(self) -> None:
        """同一日期的等价写法（CLI 习惯 / 深链习惯）→ 同一 chart argv。

        日期别名归一发生在 argv 构建层（request.norm_date），不在
        normalize_request——语义 parity 的断言点是解析后日期与 argv 一致。
        """
        from yishu_core.report.request import norm_date
        r1 = normalize_request({"discipline": "zeji", "date": "2026/09/30",
                                "activity": "开市"})
        r2 = normalize_request({"discipline": "zeji", "date": "2026.9.30",
                                "activity": "开市"})
        assert norm_date(r1["date"]) == norm_date(r2["date"])
        assert chart_argv(r1, "chart.py", "o.json") == chart_argv(r2, "chart.py", "o.json")

    def test_equivalent_forms_same_argv(self) -> None:
        """显式给默认值 vs 缺省 → 同一 argv（mode/way 默认逻辑单点在 request.py）。"""
        r1 = normalize_request({"discipline": "liuyao", "question": "q",
                                "mode": "time", "datetime": "2026-09-30 10:30"})
        r2 = normalize_request({"discipline": "liuyao", "question": "q",
                                "datetime": "2026-09-30 10:30"})
        assert chart_argv(r1, "chart.py", "o.json") == chart_argv(r2, "chart.py", "o.json")

    def test_actions_extra_json_fields_are_request_fields(self) -> None:
        """通道 B 的 extra 高级字段（mode/numbers/way/date/activity）都在
        REQUEST_FIELDS 白名单内——三条通道共用同一字段宇宙。"""
        for f in ("mode", "numbers", "way", "date", "activity",
                  "datetime", "gender", "question", "discipline"):
            assert f in REQUEST_FIELDS


class TestDeeplinkSemanticParity:
    def test_short_keys_within_whitelist(self) -> None:
        keys = _read_deeplink_keys()
        unknown = {v for v in keys.values() if v not in REQUEST_FIELDS}
        assert not unknown, f"深链短键指向未知字段：{unknown}"

    def test_deeplink_query_equals_full_request(self) -> None:
        """深链 query 的归一化结果 == 完整字段请求的归一化结果（语义等价）。"""
        query = "d=liuyao&q=占求财&mode=time&dt=2026-09-30 10:30"
        via_deeplink = normalize_request(_apply_deeplink(query))
        full = normalize_request({"discipline": "liuyao", "question": "占求财",
                                  "mode": "time", "datetime": "2026-09-30 10:30"})
        assert via_deeplink == full
        assert chart_argv(via_deeplink, "chart.py", "o.json") == \
            chart_argv(full, "chart.py", "o.json")

    def test_deeplink_ming_parity(self) -> None:
        query = "d=ming&dt=1990-05-20 10:30&g=男"
        via_deeplink = normalize_request(_apply_deeplink(query))
        full = normalize_request({"discipline": "ming", "datetime": "1990-05-20 10:30",
                                  "gender": "男"})
        assert via_deeplink == full

    def test_deeplink_zeji_parity(self) -> None:
        query = "d=zeji&date=2026-09-30&activity=开市"
        via_deeplink = normalize_request(_apply_deeplink(query))
        full = normalize_request({"discipline": "zeji", "date": "2026-09-30",
                                  "activity": "开市"})
        assert via_deeplink == full

    def test_deeplink_discipline_shortkey_required(self) -> None:
        """无学科 = 无请求（d= 是深链的结构性必填，与 CLI --discipline 同位）。"""
        out = _apply_deeplink("q=占事")
        assert "discipline" not in out
        with pytest.raises(ValueError):
            normalize_request(out)
