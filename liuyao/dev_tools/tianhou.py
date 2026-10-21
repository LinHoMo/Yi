# -*- coding: utf-8 -*-
"""占天候试验台（第一百八十批）——协议见 docs/TIANHOU.md，本文件是它的可执行半边。

    python dev_tools/tianhou.py draft  --chart <chart.json>            # 盘面→晴雨裁决预览
    python dev_tools/tianhou.py seal   --chart <chart.json> --target-day 2026-10-22 \
                                       --location 北京 --lat 39.904 --lon 116.407
    python dev_tools/tianhou.py check  --id <pid前缀>                  # 取客观源判卷（离线降级 rc=2）
    python dev_tools/tianhou.py abstain-stats
    python dev_tools/tianhou.py --selftest

纪律（§一 铁律一 / 第一百七十六批重心声明）：
  - 本台架**不改引擎**：晴雨裁决表是 dev 层的「盘面结构→任务断语」映射，书证逐字可回指
    底本（源L1917/L1926/L1935/L1953，见 TIANHOU.md），不产吉凶断语、不进评分面。
  - 弃权即不封存不落账——书无现成先后序时不强断；弃权率在 scratch 台账单独显形。
  - 判卷口径（阈值/数据源）先于实验冻结在常量里；换源=改口径，由 prospective 的
    scoring_rule_sha 分组自动隔离旧记录。
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import urllib.request
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
sys.path.insert(0, str(HERE))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
import prospective as pr  # noqa: E402
from outcome import read_jsonl  # noqa: E402

LEDGER = DISC / "scratch" / "tianhou_abstain.jsonl"
ENDPOINT_DEFAULT = ("https://archive-api.open-meteo.com/v1/archive"
                    "?latitude={lat}&longitude={lon}&start_date={day}&end_date={day}"
                    "&daily=precipitation_sum,cloud_cover_mean&timezone=auto")

CLEAR_REL = ("子孙", "妻财")
RAIN_REL = ("父母",)
CRITERIA = {
    "雨": "precipitation_sum≥1.0mm",
    "晴": "precipitation_sum<0.1mm且cloud_cover_mean≤30%",
}
BASIS = {
    "晴": "《增刪卜易》：子孙/财动主晴（源L1917「子孙为日月星斗，动则万里晴光」、源L1935「妻财天气晴明」、源L1953「占雨用父爻，占晴用子孙爻、财爻」）",
    "雨": "《增刪卜易》：父母动主雨（源L1926「父爻发动，云雾迷天，日月掩藏而雨矣」、源L1953 同条）",
    "双动冲突": "晴雨两属同动，书无现成先后序——弃权，不强断（弃权素材入台账）",
    "无晴雨动": "发动者非晴雨之亲或六爻安静（源L1953「六爻不动者，务必求其动而验之」）——弃权",
}
EVENT_TPL = ("占天候·{location}·{day} {claim}（判据：open-meteo archive daily {crit}，"
             "lat {lat} lon {lon}，窗=当日整日）")


def judgment(chart: dict):
    """盘面结构 → (断语|None, 所本, 动爻六亲表)。只看发动六亲（源L1971「占天时，不论旺衰」）。"""
    yao = (chart.get("original_hexagram") or {}).get("yao_lines") or []
    movers = [str(y.get("six_relation") or "") for y in yao if y.get("is_moving")]
    has_clear = any(r in CLEAR_REL for r in movers)
    has_rain = any(r in RAIN_REL for r in movers)
    if has_clear and has_rain:
        return None, BASIS["双动冲突"], movers
    if has_clear:
        return "晴", BASIS["晴"], movers
    if has_rain:
        return "雨", BASIS["雨"], movers
    return None, BASIS["无晴雨动"], movers


def outcome(claim: str, precip, cloud) -> bool:
    if precip is None:
        raise ValueError("判据缺 precipitation_sum，无法判卷")
    if claim == "雨":
        return float(precip) >= 1.0
    if claim == "晴":
        cc = cloud if cloud is not None else 100.0
        return float(precip) < 0.1 and float(cc) <= 30.0
    raise ValueError("断语只能是 晴/雨")


def _ledger_append(entry: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cmd_draft(chart_path: str) -> int:
    chart = json.loads(Path(chart_path).read_text(encoding="utf-8"))
    claim, basis, movers = judgment(chart)
    print("动爻六亲：%s" % (",".join(movers) or "六爻安静"))
    print("裁决：%s" % (claim if claim else "弃权"))
    print("所本：%s" % basis)
    if claim is None:
        _ledger_append({"at": datetime.now().isoformat(timespec="seconds"),
                        "chart": Path(chart_path).name, "claim": None, "movers": movers})
        print("（弃权不封存、不落账；已记弃权台账 abstain-stats 可见）")
    return 0


def cmd_seal(chart_path: str, target_day: str, location: str, lat: str, lon: str) -> int:
    try:
        tday = datetime.strptime(target_day, "%Y-%m-%d").date()
        float(lat), float(lon)
    except (ValueError, TypeError):
        print("× --target-day 需 YYYY-MM-DD，--lat/--lon 需数值")
        return 1
    if tday <= date.today():
        print("× 目标日须晚于今日——前瞻台架不接已揭晓的天（事后立据无意义）")
        return 1
    chart = json.loads(Path(chart_path).read_text(encoding="utf-8"))
    claim, basis, movers = judgment(chart)
    if claim is None:
        print("× 弃权不可封存（%s）" % basis)
        return 1
    event = EVENT_TPL.format(location=location, day=tday.isoformat(), claim=claim,
                             crit=CRITERIA[claim], lat=str(lat), lon=str(lon))
    synth = {"question": chart.get("question", "") or ("占天候：%s %s 是否%s" % (location, tday, claim)),
             "conclusion": {"方向": claim,
                            "应期明细": [{"date": tday.isoformat(), "rule": basis[:36]}]}}
    tmp = Path(os.environ.get("TIANHOU_TMP", str(DISC / "scratch")))
    tmp.mkdir(parents=True, exist_ok=True)
    spath = tmp / ("tianhou_analyze_%s.json" % tday.strftime("%Y%m%d"))
    spath.write_text(json.dumps(synth, ensure_ascii=False), encoding="utf-8")
    note = "台架=TIANHOU.md lat=%s lon=%s target=%s claim=%s" % (lat, lon, tday, claim)
    rc = pr.cmd_create(pr.STORE_DEFAULT, str(spath), "天候", event,
                       "%s..%s" % (tday, tday), note, "占天候")
    if rc == 0:
        _ledger_append({"at": datetime.now().isoformat(timespec="seconds"),
                        "chart": Path(chart_path).name, "claim": claim, "movers": movers})
    return rc


def _fetch(lat: str, lon: str, day: str):
    url = os.environ.get("YI_TIANHOU_ENDPOINT", ENDPOINT_DEFAULT).format(
        lat=lat, lon=lon, day=day)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        daily = data.get("daily") or {}
        return daily.get("precipitation_sum", [None])[0], daily.get("cloud_cover_mean", [None])[0]
    except Exception as e:  # noqa: BLE001 —— 判卷降级必须宽捕：网络/证书/结构缺失一律如实报
        print("× 取数失败（%s）" % e)
        return None


NOTE_RE = re.compile(r"lat=([\-\d.]+) lon=([\-\d.]+) target=(\d{4}-\d{2}-\d{2}) claim=(晴|雨)")


def cmd_check(pid_prefix: str) -> int:
    rows = pr.read_rows(pr.STORE_DEFAULT)
    seals = {r["payload"]["pid"]: r["payload"] for r in rows if r.get("kind") == "seal"}
    done = {r["payload"].get("pid") for r in rows if r.get("kind") == "resolve"}
    hits = [p for p in seals if p.startswith(pid_prefix) and seals[p].get("task") == "占天候"
            and p not in done]
    if len(hits) != 1:
        print("× pid 需唯一命中一条**未判卷**的占天候封存（匹配 %d 条）" % len(hits))
        return 1
    pid = hits[0]
    m = NOTE_RE.search(seals[pid].get("note", ""))
    if not m:
        print("× 封存 note 缺台架参数——判据不可复现，这条记录按 unverifiable 回填处理")
        return 1
    lat, lon, target, claim = m.group(1), m.group(2), m.group(3), m.group(4)
    vals = _fetch(lat, lon, target)
    if vals is None or vals[0] is None:
        print("降级：客观源不可达，人工判卷须给观测出处：")
        print("  判据：%s =「%s」" % (claim, CRITERIA[claim]))
        print("  回填：python dev_tools/prospective.py resolve --id %s "
              "--state occurred|not_occurred|unverifiable --actual-date %s "
              "--note \"人工观测出处…\"" % (pid, target))
        return 2
    precip, cloud = vals
    state = "occurred" if outcome(claim, precip, cloud) else "not_occurred"
    note = "open-meteo archive daily precip=%smm cloud=%s%% 判据=TIANHOU§二" % (precip, cloud)
    print("√ 取数：precipitation_sum=%s cloud_cover_mean=%s → %s %s → %s"
          % (precip, cloud, target, claim, state))
    return pr.cmd_resolve(pr.STORE_DEFAULT, pid, state, target, note)


def cmd_abstain_stats() -> int:
    rows = read_jsonl(LEDGER)
    if not rows:
        print("弃权台账空——台架尚未跑过 draft/seal")
        return 0
    ab = sum(1 for r in rows if r.get("claim") is None)
    print("draft/seal 台账 %d 条：裁决成断 %d，弃权 %d（弃权率 %.1f%%）——覆盖面诚实读数"
          % (len(rows), len(rows) - ab, ab, ab * 100.0 / len(rows)))
    return 0


def cmd_selftest() -> int:
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory(prefix="yi_th_st_") as td:
        tdp = Path(td)
        def chart_with(rels):
            yao = [{"position": i + 1, "six_relation": r or "兄弟", "is_moving": bool(r)}
                   for i, r in enumerate(rels)]
            return {"question": "占天候", "original_hexagram": {"yao_lines": yao}}
        cases = [
            ([None, None, "子孙", None, None, None], "晴"),
            ([None, "父母", None, None, None, None], "雨"),
            (["子孙", "父母", None, None, None, None], None),
            ([None, "官鬼", None, None, None, None], None),
            ([None, None, None, None, None, None], None),
        ]
        for rels, want in cases:
            claim, _b, _m = judgment(chart_with(rels))
            if claim != want:
                fails.append("映射错 %r→%r≠%r" % (rels, claim, want))
        if not (outcome("雨", 1.2, 50) and not outcome("雨", 0.5, 90)):
            fails.append("雨判据边界错")
        if not (outcome("晴", 0.05, 20) and not outcome("晴", 0.05, 60)):
            fails.append("晴判据（云量项）边界错")
        # 隔离验证：封存只进临时库（YI_PROSPECTIVE_STORE），真实库不得被 selftest 碰
        old_env = os.environ.get("YI_PROSPECTIVE_STORE")
        os.environ["YI_PROSPECTIVE_STORE"] = str(tdp / "predictions.jsonl")
        pr.STORE_DEFAULT = Path(os.environ["YI_PROSPECTIVE_STORE"])
        global LEDGER
        _ledger_bak = LEDGER
        LEDGER = tdp / "st_ledger.jsonl"  # selftest 不得污染 scratch 弃权台账
        os.environ["TIANHOU_TMP"] = str(tdp)  # 合成 analyze 也不落 scratch
        chart_p = tdp / "chart.json"
        chart_p.write_text(json.dumps(chart_with([None, None, None, "父母", None, None]),
                                      ensure_ascii=False), encoding="utf-8")
        tday = (date.today() + timedelta(days=1)).isoformat()
        rc = cmd_seal(str(chart_p), tday, "测试地", "39.9", "116.4")
        rows = pr.read_rows(pr.STORE_DEFAULT)
        if rc != 0 or not rows or rows[0]["payload"].get("task") != "占天候":
            fails.append("seal 未走通临时链")
        elif not EVENT_TPL.split("{")[0] in rows[0]["payload"]["event_definition"]:
            fails.append("事件模板前缀不合")
        os.environ["YI_TIANHOU_ENDPOINT"] = "http://127.0.0.1:9/unreachable?lat={lat}&lon={lon}&day={day}"
        pid = rows[0]["payload"]["pid"] if rows else ""
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc2 = cmd_check(pid) if pid else 1
        if rc2 != 2 or "降级" not in buf.getvalue():
            fails.append("客观源不可达时未走人工降级（应 rc=2）")
        # 过期目标日与弃权不可封存
        if cmd_seal(str(chart_p), "2020-01-01", "测试地", "39.9", "116.4") == 0:
            fails.append("目标日已过竟可封存")
        quiet_chart = tdp / "q.json"
        quiet_chart.write_text(json.dumps(chart_with([None] * 6), ensure_ascii=False),
                               encoding="utf-8")
        before = len(pr.read_rows(pr.STORE_DEFAULT))
        if cmd_seal(str(quiet_chart), tday, "测试地", "39.9", "116.4") == 0:
            fails.append("弃权竟能封存")
        if len(pr.read_rows(pr.STORE_DEFAULT)) != before:
            fails.append("弃权被落账（应只进 scratch 台账）")
        if old_env is None:
            os.environ.pop("YI_PROSPECTIVE_STORE", None)
        else:
            os.environ["YI_PROSPECTIVE_STORE"] = old_env
        LEDGER = _ledger_bak
        os.environ.pop("TIANHOU_TMP", None)
    real = DISC / "data" / "feedback" / "predictions.jsonl"
    if real.exists() and "predictions" not in str(pr.STORE_DEFAULT):
        fails.append("selftest 触碰了真实库！")
    if fails:
        print("× selftest：")
        for f in fails:
            print("  · " + f)
        return 1
    print("√ selftest：映射五态/判据边界/临时链隔离/离线降级rc=2/过期拒封/弃权不落账 全过")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="占天候试验台（协议见 docs/TIANHOU.md；真实运行待授权）")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    p_d = sub.add_parser("draft", help="盘面→晴雨裁决预览")
    p_d.add_argument("--chart", required=True)
    p_s = sub.add_parser("seal", help="有断才封存（哈希链，task=占天候）")
    p_s.add_argument("--chart", required=True)
    p_s.add_argument("--target-day", required=True)
    p_s.add_argument("--location", required=True)
    p_s.add_argument("--lat", required=True)
    p_s.add_argument("--lon", required=True)
    p_c = sub.add_parser("check", help="目标日过后取客观源判卷")
    p_c.add_argument("--id", required=True)
    sub.add_parser("abstain-stats", help="弃权率台账")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    if args.cmd == "draft":
        return cmd_draft(args.chart)
    if args.cmd == "seal":
        return cmd_seal(args.chart, args.target_day, args.location, args.lat, args.lon)
    if args.cmd == "check":
        return cmd_check(args.id)
    if args.cmd == "abstain-stats":
        return cmd_abstain_stats()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
