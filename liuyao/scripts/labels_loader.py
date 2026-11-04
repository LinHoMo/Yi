# -*- coding: utf-8 -*-
"""结构层断语外置册装载器：scripts 层共读，缺表/缺分节一律抛错，不静默降级。"""
from __future__ import annotations

from kernel_path import load_data_json
_CACHE: dict | None = None


def load(section: str) -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = load_data_json("rules", "domain", "scripts_labels.json")
    if section not in _CACHE:
        raise KeyError("scripts_labels.json 无分节 %r——键面被改，装载即失败，不静默" % section)
    return _CACHE[section]
