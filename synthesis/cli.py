# -*- coding: utf-8 -*-
"""合参层·命令行入口（synthesis CLI）。

  python cli.py init P001 --solar "1990-05-20 07:15" [--longitude 116.4]
  python cli.py validate P001
  python cli.py add-divination P001 --discipline xiaoliuren --analyze-json <file> \
      [--event-id EVT001] [--asked "…"] [--at "2026-09-23 10:30"] \
      [--policy "boundary=day,zi_hour=night_same_day"]
  python cli.py record-outcome P001 --event-id EVT001 --result "应验：…"
  python cli.py guide P001 [-o guidance/]
  python cli.py selfcheck

档案目录缺省 synthesis/person，指导输出缺省 synthesis/guidance。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE.parent / "core"
for _p in (str(HERE), str(CORE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from yishu_core.runtime import force_utf8_stdio  # noqa: E402

from person import PersonArchive, PersonError  # noqa: E402
from normalize import normalize  # noqa: E402
from cross_rules import adjudicate, selfcheck as cross_selfcheck  # noqa: E402
from guidance import write_guidance  # noqa: E402

PERSON_DIR = HERE / "person"
GUIDANCE_DIR = HERE / "guidance"


def _load(pid: str) -> PersonArchive:
    return PersonArchive.load(PERSON_DIR, pid)


def _parse_policy(text: str | None) -> dict | None:
    if not text:
        return None
    out = {}
    for pair in text.split(","):
        k, _, v = pair.partition("=")
        k, v = k.strip(), v.strip()
        if not k or not v:
            raise PersonError(f"policy 段须为 k=v：{pair!r}")
        out[k] = v
    return out


def cmd_init(args) -> int:
    policy = _parse_policy(args.policy)
    ganzhi = json.loads(args.ganzhi) if args.ganzhi else None
    arch = PersonArchive.create(
        args.pid, args.solar, longitude=args.longitude,
        ganzhi=ganzhi, policy=policy, assembled_from=args.assembled_from)
    errs = arch.validate()
    if errs:
        for e in errs:
            print(f"  · {e}")
        return 1
    p = arch.save(PERSON_DIR)
    print(f"档案 → {p}（id={arch.data['id']}）")
    return 0


def cmd_validate(args) -> int:
    arch = _load(args.pid)
    errs = arch.validate()
    if not errs:
        print(f"{args.pid}：档案合规（{len(arch.data.get('divinations') or [])} 条占问，"
              f"{len(arch.data.get('guidance') or [])} 条指导）")
        return 0
    print(f"{args.pid}：档案存在违规：")
    for e in errs:
        print(f"  · {e}")
    return 1


def cmd_add_divination(args) -> int:
    arch = _load(args.pid)
    analyze_out = json.loads(Path(args.analyze_json).read_text(encoding="utf-8"))
    rec = normalize(args.discipline, analyze_out, at=args.at)
    if args.asked:
        rec["asked"] = args.asked
    if args.policy:
        rec["calendar_policy"] = _parse_policy(args.policy)
    if args.event_id:
        rec["event_id"] = args.event_id
    eid = arch.add_divination(rec)
    arch.save(PERSON_DIR)
    print(f"已登记占问 {eid}：〔{rec['discipline']}·{rec['direction']}〕{rec['asked']}")
    print(f"  判据：{rec['verdict'][:120]}")
    if rec.get("timing"):
        print(f"  应期：{'、'.join(rec['timing'])}")
    return 0


def cmd_record_outcome(args) -> int:
    arch = _load(args.pid)
    arch.record_outcome(args.event_id, args.result)
    arch.save(PERSON_DIR)
    print(f"{args.pid}·{args.event_id} 结果已回填")
    return 0


def cmd_guide(args) -> int:
    arch = _load(args.pid)
    errs = arch.validate()
    if errs:
        print("档案校验未通过，先修：", file=sys.stderr)
        for e in errs:
            print(f"  · {e}", file=sys.stderr)
        return 1
    recs = arch.data.get("divinations") or []
    if not recs:
        print("无占问记录，先 add-divination。")
        return 1
    policies = [r.get("calendar_policy") for r in recs]
    out_dir = Path(args.out) if args.out else GUIDANCE_DIR
    p = write_guidance(arch, adjudicate(recs, policies=policies), out_dir)
    print("指导 →", p)
    return 0


def cmd_selfcheck(args) -> int:
    cross_selfcheck()
    # person 档案校验自检：ganzhi 存在时必须带 calendar_policy
    arch = PersonArchive.create(
        "TEST", "1990-05-20 07:15",
        ganzhi={"year": "庚午", "month": "辛巳", "day": "壬辰", "hour": "丙辰"},
        policy={"boundary": "day", "zi_hour": "night_same_day"})
    assert not arch.validate(), arch.validate()
    arch.data["birth"].pop("calendar_policy", None)
    assert any("calendar_policy" in e for e in arch.validate())
    # 归一化自检：小六壬 analyze 样例
    sample = {
        "schema": "xiaoliuren-analyze-v1",
        "question": "明日讨债顺利否",
        "conclusion": {"方向": "平", "说明": "留连事难成", "所本": "《贺氏六壬小手册》"},
        "timing": {"主数": [2, 8, 10]},
    }
    rec = normalize("xiaoliuren", sample, at="2026-09-23 10:30")
    assert rec["direction"] == "平" and rec["timing"] == ["主数 2", "主数 8", "主数 10"]
    print("synthesis 自检通过（person 校验 + cross_rules + 归一化）")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="易·合参层 CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="新建人档案")
    p.add_argument("pid")
    p.add_argument("--solar", required=True, help="出生时刻 YYYY-MM-DD HH:MM")
    p.add_argument("--longitude", type=float, help="出生地东经")
    p.add_argument("--ganzhi", help='四柱 JSON，如 \'{"year":"庚午","month":"辛巳"}\'')
    p.add_argument("--policy", help="历法口径，如 boundary=day,zi_hour=night_same_day")
    p.add_argument("--assembled-from", default="raw_solar")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="校验档案")
    p.add_argument("pid")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("add-divination", help="登记一次占问")
    p.add_argument("pid")
    p.add_argument("--discipline", required=True,
                   choices=["liuyao", "meihua", "xiaoliuren", "zeji"])
    p.add_argument("--analyze-json", required=True, help="该科 analyze 输出 JSON")
    p.add_argument("--event-id")
    p.add_argument("--asked", help="问句（缺省取 analyze.question）")
    p.add_argument("--at", help="起局时间 YYYY-MM-DD[ HH:MM]")
    p.add_argument("--policy", help="本次占问的历法口径（见 init）")
    p.set_defaults(func=cmd_add_divination)

    p = sub.add_parser("record-outcome", help="回填占问结果")
    p.add_argument("pid")
    p.add_argument("--event-id", required=True)
    p.add_argument("--result", required=True)
    p.set_defaults(func=cmd_record_outcome)

    p = sub.add_parser("guide", help="生成阶段性指导")
    p.add_argument("pid")
    p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_guide)

    p = sub.add_parser("selfcheck", help="合参层自检")
    p.set_defaults(func=cmd_selfcheck)

    args = ap.parse_args()
    try:
        return args.func(args)
    except PersonError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"错误：找不到文件 {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
