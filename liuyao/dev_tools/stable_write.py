# -*- coding: utf-8 -*-
"""观察册幂等写（第两百零三批）——内容不变则文件一字不动，时间戳＝内容最后变化时刻。

背景（202 批登记陷阱）：带 `generated_at` 的观察册放 tracked 路径，重跑必产生
「只有时间戳变」的脏文件——把「重新算了一遍」误报成「事实变了」，稀释 git 信号。
本模块把语义修正为：**generated_at 记录内容何时最后一次真实变化**。

    from stable_write import write_stable

纪律：只比较 generated_at 以外的字段；结构不同即写；不比较浮点显示串（直接比 JSON 对象）。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


VOLATILE = ("generated_at", "built_at")  # 时间戳变体字段：内容比较时一律剔除


def content_equal(a: dict, b: dict) -> bool:
    ka = {k: v for k, v in a.items() if k not in VOLATILE}
    kb = {k: v for k, v in b.items() if k not in VOLATILE}
    return ka == kb


def write_stable(path: Path, doc: dict, indent: int = 1) -> bool:
    """返回 True=已重写，False=内容未变化保持原文件。"""
    payload = dict(doc)
    if path.exists():
        try:
            old = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            old = None
        if isinstance(old, dict) and content_equal(old, payload):
            return False
    now = datetime.now().isoformat(timespec="seconds")
    for k in VOLATILE:
        if k in payload:
            payload[k] = now
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=indent), encoding="utf-8")
    return True


def selftest() -> int:
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory(prefix="yi_sw_st_") as td:
        p = Path(td) / "book.json"
        d1 = {"generated_at": "X", "a": 1, "rows": [1, 2]}
        assert "generated_at" in d1
        # 首写必落
        if not write_stable(p, d1):
            fails.append("首写未落盘")
        ts1 = json.loads(p.read_text(encoding="utf-8"))["generated_at"]
        # 内容相同重写：不落，时间戳保持
        if write_stable(p, {"generated_at": "Y", "a": 1, "rows": [1, 2]}):
            fails.append("同内容仍重写（幂等失效）")
        if json.loads(p.read_text(encoding="utf-8"))["generated_at"] != ts1:
            fails.append("同内容但时间戳被刷新")
        # 内容真变：落且时间戳更新（含 built_at 变体，203 批第二案：首版只认 generated_at，
        # graduate/adjudications 用 built_at 照样空转重写——volatile 集合必须对齐全部变体）
        if not write_stable(p, {"generated_at": "Z", "a": 1, "rows": [1, 3]}):
            fails.append("内容变化未触发重写")
        if json.loads(p.read_text(encoding="utf-8"))["generated_at"] == "Z":
            fails.append("时间戳未被刷新为现值")
    with tempfile.TemporaryDirectory(prefix="yi_sw_st2_") as td2:
        p2 = Path(td2) / "b.json"
        write_stable(p2, {"built_at": "X", "rows": [1]})
        ts = json.loads(p2.read_text(encoding="utf-8"))["built_at"]
        if write_stable(p2, {"built_at": "Y", "rows": [1]}):
            fails.append("built_at 变体未纳入幂等（同内容仍重写）")
        if json.loads(p2.read_text(encoding="utf-8"))["built_at"] != ts:
            fails.append("built_at 被空转刷新")
    print("√ selftest：首写/幂等/真变三态全过" if not fails else "× " + "；".join(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    # 中文 CLI 编码守卫（[24]/[20] 静态红线）：库本体 import 时不动 stdout，仅入口分支内配置
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(selftest())
