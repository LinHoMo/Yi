# -*- coding: utf-8 -*-
"""金标准指纹共享壳：八字·六爻两科 dev_tools/golden.py 共用的 capture/verify 逻辑。

指纹分两层（SYS-REVIEW #2，2026-10-01l）：
  机械层 digest      —— fingerprint() 输出中除 narrate_* 外的全部字段；只准机械重构
                        前后取值不变，漂移即行为变化。
  措辞层 narrate_digest —— 各行 narrate_* 字段（narrate_sha / narrate_len）。
                        断语措辞改动会漂移；机械层零漂移时可单独 capture 归因。

学科 golden.py 只保留 GOLDEN_CASES + fingerprint()，main 一律调 run()。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

NARRATE_PREFIX = "narrate"
ROW_ID_KEYS = ("case", "id", "sample")


def _row_id(row: dict) -> str:
    for k in ROW_ID_KEYS:
        if k in row:
            return str(row[k])
    return "?"


def split_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    """把 fingerprint 输出拆成（机械层， 措辞层）两份独立 blob。"""
    machine: list[dict] = []
    narrate: list[dict] = []
    for row in rows:
        rid = _row_id(row)
        machine.append({k: v for k, v in row.items()
                        if not k.startswith(NARRATE_PREFIX)})
        n_part = {k: v for k, v in row.items() if k.startswith(NARRATE_PREFIX)}
        narrate.append({"row": rid, **n_part})
    return machine, narrate


def _digest(blob: str) -> str:
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _diff_summary(before: list[dict], after: list[dict]) -> list[tuple[str, list[str]]]:
    if len(before) != len(after):
        return []
    changed = []
    for a, b in zip(before, after):
        keys = [k for k in set(a) | set(b) if a.get(k) != b.get(k)]
        if keys:
            changed.append((_row_id(b), keys))
    return changed


def run(disc_name: str, what: str, how: str,
        fingerprint: Callable[[], list[dict]], *,
        out: Path, digest_path: Path) -> int:
    """两科 golden.py 的 main 主体。capture 必须给理由；verify 漂移退出码 1。"""
    from yishu_core.runtime import force_utf8_stdio

    force_utf8_stdio()
    ap = argparse.ArgumentParser(
        description=f"{disc_name}金标准指纹：capture 落基线 / verify 比对漂移（默认）")
    ap.add_argument("mode", nargs="?", default="verify", choices=("capture", "verify"))
    ap.add_argument("reason", nargs="?", default="",
                    help="capture 模式必填：为何允许漂移（防掩盖退步，见 AGENTS.md 四）")
    args = ap.parse_args()

    rows = fingerprint()
    machine_rows, narrate_rows = split_rows(rows)
    machine_digest = _digest(json.dumps(machine_rows, ensure_ascii=False, sort_keys=True, indent=1))
    narrate_digest = _digest(json.dumps(narrate_rows, ensure_ascii=False, sort_keys=True, indent=1))
    errors = [r for r in rows if "error" in r]
    print(f"用例 {len(rows)} 条｜机械 {machine_digest}｜措辞 {narrate_digest}｜异常 {len(errors)} 条")
    for e in errors[:10]:
        print("  !", _row_id(e), e["error"])

    prior: dict = {}
    if digest_path.exists():
        prior = json.loads(digest_path.read_text(encoding="utf-8"))
    old_machine = prior.get("digest")
    old_narrate = prior.get("narrate_digest", old_machine)

    if args.mode == "capture":
        if not args.reason.strip():
            print('× 重新落基线必须给理由：python dev_tools/golden.py capture "为何允许漂移"')
            print("  基线下调/漂移不写理由＝掩盖退步（AGENTS.md 四）。")
            return 2
        if machine_digest == old_machine and narrate_digest == old_narrate:
            print("· 指纹与基线一致，无需 capture（避免无意义滚动）")
            return 0
        machine_drift = machine_digest != old_machine
        narrate_drift = narrate_digest != old_narrate
        out.parent.mkdir(exist_ok=True, parents=True)
        out.write_text(json.dumps({"machine": machine_rows, "narrate": narrate_rows},
                                  ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")
        digest_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d")
        machine_log = list(prior.get("drift_log") or [])
        narrate_log = list(prior.get("narrate_drift_log") or [])
        if machine_drift:
            machine_log.append({"from": old_machine, "to": machine_digest,
                                "date": stamp, "reason": args.reason.strip()})
        if narrate_drift:
            narrate_log.append({"from": old_narrate, "to": narrate_digest,
                                "date": stamp, "reason": args.reason.strip()})
        digest_path.write_text(json.dumps({
            "_meta": {"what": what, "how": how},
            "digest": machine_digest,
            "narrate_digest": narrate_digest,
            "drift_log": machine_log[-20:],
            "narrate_drift_log": narrate_log[-20:]}, ensure_ascii=False, indent=2) + chr(10),
            encoding="utf-8")
        layer = "机械+措辞" if (machine_drift and narrate_drift) else (
            "仅机械" if machine_drift else "仅措辞")
        print(f"金标准已落盘（{layer}漂移归因）→ {digest_path}")
        return 0

    if not digest_path.exists():
        print(f"缺指纹基线 {digest_path}")
        return 2
    machine_ok = machine_digest == old_machine
    narrate_ok = narrate_digest == old_narrate
    if machine_ok and narrate_ok:
        print("√ 与基线指纹一致（机械+措辞均未漂移）")
        return 0
    if machine_ok and not narrate_ok:
        print(f"× 措辞层（narrate）漂移：基线 {old_narrate} → 现在 {narrate_digest}；"
              f"机械层零漂移。若为有意措辞变更，capture 记入 narrate_drift_log 即可。")
    else:
        print(f"\n× 机械行为漂移：基线 {old_machine} → 现在 {machine_digest}"
              + ("" if narrate_ok else f"（措辞层同时漂移：{old_narrate} → {narrate_digest}）"))
    if not out.exists():
        print("  本地无全量快照时只能据此判断「改的是不是你要改的东西」；"
              "要逐条比对请先 capture 再改动。")
        return 1
    try:
        snap = json.loads(out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        snap = None
    if isinstance(snap, dict) and "machine" in snap:
        before_machine = snap["machine"]
        before_narrate = snap.get("narrate") or []
    else:  # 旧格式：裸 list，无措辞层
        before_machine = snap or []
        before_narrate = []
    for label, before, after, ok in (
            ("机械", before_machine, machine_rows, machine_ok),
            ("措辞", before_narrate, narrate_rows, narrate_ok)):
        if ok:
            continue
        changed = _diff_summary(before, after)
        print(f"  {label}层逐条比对：{len(changed)} 条变化")
        for rid, keys in changed[:6]:
            print(f"    {rid}: {keys}")
    return 1
