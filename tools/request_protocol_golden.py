# -*- coding: utf-8 -*-
"""输入协议金标准：request.py 的参数映射/校验行为与引擎 golden 同价锁定。

    python tools/request_protocol_golden.py capture "理由"  # 有意变更后落基线
    python tools/request_protocol_golden.py verify          # 默认；漂移退出码 1

引擎行为有八字·六爻两科 golden，但输入协议（参数名/别名/校验/默认值）没有对应机制——
协议漂移只能靠网页同源验收间接发现（SYS-REVIEW #4）。本工具把 normalize_request
在固定输入集（含别名、非法输入负例）上的产出做成指纹。
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report.request import normalize_request  # noqa: E402

OUT = ROOT / "scratch" / "request_protocol_before.json"
DIGEST = ROOT / "data" / "golden" / "request_protocol_digest.json"

# 正例：别名/默认值/归一化各路径；负例：必须被拒绝的输入
CASES = [
    {"discipline": "liuyao", "question": "占求财", "mode": "time", "datetime": "2026-09-30 10:30"},
    {"discipline": "liuyao", "question": "占求财", "mode": "manual", "datetime": "2026-09-22 23:40",
     "yao": "7,8,9,7,6,8"},
    {"discipline": "ming", "datetime": "1990-05-20 10:30", "gender": "男"},
    # 协议负例：非法学科/非法性别/非法 mode/越界掷数 —— 现在拒绝什么，指纹就锁什么
    {"discipline": "not-a-disc"},
    {"discipline": "ming", "gender": "不详"},
    {"discipline": "liuyao", "mode": "no-such-mode"},
]


def fingerprint() -> list[dict]:
    rows = []
    for i, case in enumerate(CASES):
        try:
            req = dict(normalize_request(case))
            rows.append({"case": f"c{i}", "normalized": req})
        except Exception as exc:
            rows.append({"case": f"c{i}", "rejected": f"{type(exc).__name__}: {exc}"})
    return rows


def main() -> int:
    from yishu_core.golden_kit import run
    return run(
        "输入协议",
        what="request.py 输入协议指纹基线（normalize_request 正/负例逐字段）",
        how='改动输入协议后跑 python tools/request_protocol_golden.py capture "理由"；'
            "与两科 golden 同价，防协议漂移只被同源验收间接发现",
        fingerprint=fingerprint, out=OUT, digest_path=DIGEST)


if __name__ == "__main__":
    raise SystemExit(main())
