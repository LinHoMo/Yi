# -*- coding: utf-8 -*-
"""合参层·命令行入口（synthesis CLI）。

  python cli.py init P001 --solar "1990-05-20 07:15" [--longitude 116.4]
  python cli.py validate P001
  python cli.py add-divination P001 --discipline ming --analyze-json <file> \
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
from normalize import normalize, DISCIPLINES  # noqa: E402
from cross_rules import adjudicate, selfcheck as cross_selfcheck  # noqa: E402
from evidence_cross import (  # noqa: E402
    attach_rule_registries,
    cross_examine,
    load_rule_registry,  # noqa: F401  （cli 历史导出名，实现单源在 evidence_cross）
    selfcheck as evidence_selfcheck,
)
from guidance import write_guidance  # noqa: E402
from outcome_eval import eval_outcomes, report as yq_report, selfcheck_scoring  # noqa: E402

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
    arch.record_outcome(args.event_id, args.result,
                        occurred_at=args.occurred_at, judged=args.judged)
    arch.save(PERSON_DIR)
    print(f"{args.pid}·{args.event_id} 结果已回填"
          + (f"（{args.judged}，{args.occurred_at}）" if args.judged or args.occurred_at else ""))
    return 0


def cmd_outcome_eval(args) -> int:
    arch = _load(args.pid)
    res = eval_outcomes(arch.data.get("divinations") or [])
    yq_report(res)
    if res.get("n_回填"):
        return 0
    # 空集 = 「无数据」，不是「评测失败」（架构评审 A7）：如实声明口径并退出 0，
    # 否则这条链路的"可跑"永远被误报成失败，回归无从谈起。
    print("口径：本档案尚无已回填占问（n=0），效度无从讨论——此为空集，非评测失败。")
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
    # 证据级检视进主合参文档：趋向之外，同向/冲突/缺口一并给出（evidence-first）
    ev = cross_examine(attach_rule_registries(recs))
    out_dir = Path(args.out) if args.out else GUIDANCE_DIR
    p = write_guidance(arch, adjudicate(recs, policies=policies), out_dir,
                       evidence_view=ev)
    print("指导 →", p)
    n_conf = len(ev.get("conflicts") or [])
    n_gap = len((ev.get("unassessed") or {}).get("evaluation_gaps") or [])
    print(f"  证据级检视：冲突 {n_conf} 处、unassessed 缺口 {n_gap} 条"
          + ("（已内嵌指导文档 §三）" if ev.get("dimensions") else
             "（档案无结构化证据，指导文档已如实声明）"))
    return 0


def cmd_evidence_cross(args) -> int:
    """证据级检视：档案内各占问的 evidence → same/conflict/unassessed 清单。"""
    arch = _load(args.pid)
    recs = arch.data.get("divinations") or []
    if not recs:
        print("无占问记录，先 add-divination。")
        return 1
    res = cross_examine(attach_rule_registries(recs))
    print(f"证据级检视（{res['schema']}）")
    for factor, dim in ((d["factor"], d) for d in res["dimensions"]):
        sides = "、".join(f"{e['discipline']}:{e['effect'] or '—'}"
                          for e in dim["entries"])
        print(f"  · {factor}［{dim['relation']}］{sides}"
              + (f"（{dim['note']}）" if dim["note"] else ""))
    conf = res["conflicts"]
    if conf:
        print(f"  冲突 {len(conf)} 处（双方条件已保留，不做平均）：")
        for c in conf:
            for s in c["sides"]:
                print(f"    · {s['discipline']}：{s['claim']}"
                      + (f"｜条件：{s['applicability']}" if s["applicability"] else "")
                      + (f"｜所本：{s['source']}" if s["source"] else ""))
    gaps = res["unassessed"]["evaluation_gaps"]
    print(f"  unassessed：评测缺口 {len(gaps)} 条"
          f"（{res['unassessed']['note'][:30]}…）")
    for g in gaps[:10]:
        print(f"    · {g['discipline']}·{g['factor']}：{g['evaluation_status']}"
              f"｜{g['claim']}")
    if res["unassessed"]["silent_disciplines"]:
        print(f"  未表态学科：{'、'.join(res['unassessed']['silent_disciplines'])}")
    no_ev = res["unassessed"].get("no_evidence_disciplines") or []
    if no_ev:
        print(f"  未携带证据（旧档案记录，不参与证据级对照）：{'、'.join(no_ev)}")
    print("  口径：" + res["note"])
    return 0


def cmd_selfcheck(args) -> int:
    cross_selfcheck()
    evidence_selfcheck()
    # 学科清单锁：合参层各清单必须与内核唯一真值源同源（防四处清单再次分叉）
    import person as _person  # noqa: E402
    from yishu_core.report.request import DISCIPLINES as _core_disc  # noqa: E402
    assert set(DISCIPLINES) == set(_person.DISCIPLINES) == set(_core_disc), \
        "合参层学科清单与 request.DISCIPLINES 不同源"
    # person 档案校验自检：ganzhi 存在时必须带 calendar_policy
    arch = PersonArchive.create(
        "TEST", "1990-05-20 07:15",
        ganzhi={"year": "庚午", "month": "辛巳", "day": "壬辰", "hour": "丙辰"},
        policy={"boundary": "day", "zi_hour": "night_same_day"})
    assert not arch.validate(), arch.validate()
    arch.data["birth"].pop("calendar_policy", None)
    assert any("calendar_policy" in e for e in arch.validate())
    # 归一化自检：命 analyze 样例
    sample = {
        "schema": "ming-analyze-v1",
        "question": "命局排盘",
        "chart_summary": {"四柱": {"year": "庚午", "month": "辛巳",
                                  "day": "壬辰", "hour": "丙辰"}},
        "conclusion": {"strength": "中和", "pattern": "正官格"},
    }
    rec = normalize("ming", sample, at="1990-05-20 07:15")
    assert rec["discipline"] == "ming" and rec["direction"] == "平"
    # 六爻应期结构化候选 + 回填评分自检（B2 应期回收闭环）
    lya = {
        "schema": "liuyao-analyze-v1",
        "question": "本季度能否入职",
        "conclusion": {
            "方向": "吉", "verdict": "吉",
            "应期": ["2026-10-05（冲空填实）", "2026-10-17（出旬）"],
            "应期明细": [{"date": "2026-10-05", "rule": "冲空填实"},
                       {"date": "2026-10-17", "rule": "出旬"}],
        },
    }
    rec = normalize("liuyao", lya, at="2026-09-23 10:30")
    assert rec["yingqi_offered"] == [
        {"date": "2026-10-05", "rule": "冲空填实"},
        {"date": "2026-10-17", "rule": "出旬"}]
    from outcome_eval import eval_outcomes  # noqa: E402
    fake = [{"event_id": "EVT001", "discipline": "liuyao", "direction": "吉",
             "asked": "本季度能否入职", "yingqi_offered": rec["yingqi_offered"],
             "outcome": {"recorded": "10-05 收到 offer", "occurred_at": "2026-10-05",
                         "judged": "应验"}},
            {"event_id": "EVT002", "discipline": "liuyao", "direction": "吉",
             "asked": "何时能回款", "yingqi_offered": rec["yingqi_offered"],
             "outcome": {"recorded": "至今未回", "occurred_at": "2026-12-20",
                         "judged": "超期未验"}}]
    r = eval_outcomes(fake)
    assert r["n_回填"] == 2 and r["n_应期可评"] == 2
    yq = {c["event_id"]: c["应期"] for c in r["cases"]}
    assert yq["EVT001"]["命中"] and yq["EVT001"]["名次"] == 1
    assert not yq["EVT002"]["命中"] and yq["EVT002"]["判定"].startswith("超期")
    # 评分表自洽（A7）：7 档位跑真实判定路径，锁「名次→得分」映射
    selfcheck_scoring()
    print("synthesis 自检通过（person 校验 + cross_rules + 证据级检视 + 归一化 + 应期回收闭环 + 评分表自洽）")
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
    p.add_argument("--discipline", required=True, choices=list(DISCIPLINES))
    p.add_argument("--analyze-json", required=True, help="该科 analyze 输出 JSON")
    p.add_argument("--event-id")
    p.add_argument("--asked", help="问句（缺省取 analyze.question）")
    p.add_argument("--at", help="起局时间 YYYY-MM-DD[ HH:MM]")
    p.add_argument("--policy", help="本次占问的历法口径（见 init）")
    p.set_defaults(func=cmd_add_divination)

    p = sub.add_parser("record-outcome", help="回填占问结果（结构化字段供应期回收评分）")
    p.add_argument("pid")
    p.add_argument("--event-id", required=True)
    p.add_argument("--result", required=True, help="现实结果自由文本")
    p.add_argument("--occurred-at", help="应验/观察发生日期 YYYY-MM-DD（评应期命中用）")
    p.add_argument("--judged", choices=["应验", "未应验", "部分应验", "超期未验"],
                   help="断事层面的判定")
    p.set_defaults(func=cmd_record_outcome)

    p = sub.add_parser("outcome-eval", help="应期回收评分：回填结果与断卦应期比对")
    p.add_argument("pid")
    p.set_defaults(func=cmd_outcome_eval)

    p = sub.add_parser("guide", help="生成阶段性指导")
    p.add_argument("pid")
    p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_guide)

    p = sub.add_parser("evidence-cross", help="证据级检视：same/conflict/unassessed 清单")
    p.add_argument("pid")
    p.set_defaults(func=cmd_evidence_cross)

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
