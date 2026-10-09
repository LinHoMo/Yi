# -*- coding: utf-8 -*-
"""[1h] 字段活性门的负例自证（AGENTS.md §四.8）。

`tools/check.py` 的 [1h] 原只有一条**单向子集**判据
（`set(web.js DEEPLINK_KEYS 值) ⊆ request.REQUEST_FIELDS`）：白名单自己含死字段时
永远绿。2026-10-09 协议批次实测——往 `request.FIELD_USAGE` 塞一个假字段，
`tests/test_request_parity.py` 当场判红 2 项，而 `[1h]` 返回 `[]`（等于没这条门）。
本文件把同一条判据钉在根门上：

  ① 真表现状必须干净（`check_field_liveness()` 返回空）；
  ② argv 类字段没进任何一科的 chart/analyze/render_argv 产出 → 判红；
  ③ display 类字段没写 DISPLAY_PURPOSE 用途 → 判红；
  ④ 字段在 FIELD_USAGE 里、却没挂任何学科（FIELD_SCOPE）→ 判红；
  ⑤ DISPLAY_PURPOSE 指向 FIELD_USAGE 里没有的字段 → 判红。

负例一律用**注入参数**（与真值源门的 `SCAN_ROOTS_OVERRIDE` 同手法）：
绝不往 `core/**` 或仓库文件植假字段——并行批次会互相踩，而且撤干净与否没法自证。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for rel in ("core",):
    p = str(ROOT / rel)
    if p not in sys.path:
        sys.path.insert(0, p)

_spec = importlib.util.spec_from_file_location("yi_check_for_liveness", ROOT / "tools" / "check.py")
ck = importlib.util.module_from_spec(_spec)
sys.modules["yi_check_for_liveness"] = ck
_spec.loader.exec_module(ck)

from yishu_core.report import request as rq  # noqa: E402

PROBE = "__no_such_field_probe"


def _tables(**over):
    """取现表并叠加注入项（不改内核对象本身）。"""
    base = {"field_usage": dict(rq.FIELD_USAGE),
            "field_scope": dict(rq.FIELD_SCOPE),
            "display_purpose": dict(rq.DISPLAY_PURPOSE)}
    base.update(over)
    return base


def test_real_tables_are_live():
    """现状必须干净：这条门不是"永远红"的摆设，也不是"永远绿"的空壳。"""
    assert ck.check_field_liveness() == []


def test_argv_field_that_reaches_no_argv_is_red():
    """② argv 类字段不接线 → 判红并点名该字段。"""
    usage = dict(rq.FIELD_USAGE)
    usage[PROBE] = rq.USAGE_ARGV
    scope = dict(rq.FIELD_SCOPE)
    scope[PROBE] = rq.DISCIPLINES
    fails = ck.check_field_liveness(field_usage=usage, field_scope=scope)
    assert any(PROBE in f for f in fails), fails
    assert any("argv 类" in f for f in fails), fails


def test_display_field_without_purpose_is_red():
    """③ display 类字段不写用途 → 判红。"""
    usage = dict(rq.FIELD_USAGE)
    usage[PROBE] = rq.USAGE_DISPLAY
    scope = dict(rq.FIELD_SCOPE)
    scope[PROBE] = rq.DISCIPLINES
    fails = ck.check_field_liveness(field_usage=usage, field_scope=scope)
    assert any(PROBE in f and "DISPLAY_PURPOSE" in f for f in fails), fails


def test_field_without_scope_is_red():
    """④ 只进 FIELD_USAGE、不进 FIELD_SCOPE → 请求带不上去，判红。"""
    usage = dict(rq.FIELD_USAGE)
    usage[PROBE] = rq.USAGE_ARGV
    fails = ck.check_field_liveness(field_usage=usage, field_scope=dict(rq.FIELD_SCOPE))
    assert any(PROBE in f and "FIELD_SCOPE" in f for f in fails), fails


def test_purpose_entry_without_field_is_red():
    """⑤ 用途标注指向不存在的字段 → 判红。"""
    purpose = dict(rq.DISPLAY_PURPOSE)
    purpose[PROBE] = "探测用"
    fails = ck.check_field_liveness(display_purpose=purpose)
    assert any(PROBE in f for f in fails), fails


def test_unrecognised_usage_kind_is_red():
    """消费方式只有 argv/display 两种；写出第三种说明判据覆盖不到它。"""
    usage = dict(rq.FIELD_USAGE)
    usage[PROBE] = "silently_ignored"
    scope = dict(rq.FIELD_SCOPE)
    scope[PROBE] = rq.DISCIPLINES
    fails = ck.check_field_liveness(field_usage=usage, field_scope=scope)
    assert any(PROBE in f for f in fails), fails


def test_deeplink_short_keys_still_subset_of_whitelist():
    """原单向子集判据不得被这次加固弄丢（短键指向未知字段仍判红）。"""
    js = (ROOT / "web" / "web.js").read_text(encoding="utf-8", errors="ignore")
    assert "DEEPLINK_KEYS" in js
    fails = ck.check_deeplink_keys()
    assert fails == [], fails


def test_probe_values_cover_every_argv_field():
    """探针取值表必须覆盖每个 argv 类字段，否则"没测到"会伪装成"没死字段"。"""
    values = ck._request_probe_values()
    missing = [f for f, kind in rq.FIELD_USAGE.items()
               if kind == rq.USAGE_ARGV and values.get(f) is None]
    assert not missing, f"探针缺取值：{missing}"
