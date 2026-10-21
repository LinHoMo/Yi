# -*- coding: utf-8 -*-
"""结构层断语外置册装载器（第两百一十批，§一.1）——scripts 层共读，读取失败响亮报错。

与 `_use_god_rules`「读不到退回词典不装绿」的取向不同：本册的内容**没有代码内副本**
（搬家的意义就是唯一真值在 data），读失败继续跑＝输出静默缺判语——宁可炸在启动，
不可错在交付（§六.3 精神）。golden 指纹（[1.6]）在链层会立刻抓住半装状态。
"""
from __future__ import annotations

import json
from pathlib import Path

_PATH = Path(__file__).resolve().parents[1] / "data" / "rules" / "scripts_labels.json"
_CACHE: dict | None = None


def load(section: str) -> dict:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(_PATH.read_text(encoding="utf-8"))
    if section not in _CACHE:
        raise KeyError("scripts_labels.json 无分节 %r——键面被改，装载即失败，不静默" % section)
    return _CACHE[section]
