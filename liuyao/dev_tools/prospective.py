# -*- coding: utf-8 -*-
"""前瞻预测封存登记（第一百七十七批）——预测先冻结，结果后揭晓，判卷口径先写死。

为什么单独建这条通道：`outcome.py`/`feedback_store.py` 记的是「已落盘事件的现实回填」，
本模块管的是**判卷纪律**本身——事件定义、时间窗、方向断与应期候选在结果揭晓前随哈希链
封存；回填只追加、封存段永不可变；命中由口径规则**现算**、判卷人不手写；无法核验/失联
记为删失并单独报比例，不充数也不冤枉。没有这套封存，「准不准」永远可能被事后解释污染
（铁律三的根；第一百七十六批工程重心声明：新增能力只开往「让现实为预测判卷」的方向）。

信任边界（如实声明）：本地哈希链防的是**流程漂移与自我改写**，不是对手攻击——链头摘要
随批次写进 CHANGELOG 人肉锚定；`data/feedback/` 不入库（现实反馈与古籍调参物理隔离，
本目录同样永不参与调参）。门 `dev_tools/check.py [28]` 每次跑批复核链完整性。

用法：
    python dev_tools/prospective.py create --analyze <analyze.json> \
        --question-type 事业 --event "定义：offer 是否发到我手上（以邮件为准）" \
        --window 2026-10-25..2026-11-08 [--note …]
    python dev_tools/prospective.py resolve --id <pid前缀> \
        --state occurred|not_occurred|unverifiable|lost [--actual-date YYYY-MM-DD] [--note 核验出处]
    python dev_tools/prospective.py list [--due] [--json]
    # 外部排程/测试改库存放：设环境变量 YI_PROSPECTIVE_STORE=<路径>（第一百七十八批），
    # 或顶级 --store 参数（须写在子命令之前）。
    python dev_tools/prospective.py report [--json]
    python dev_tools/prospective.py verify
    python dev_tools/prospective.py --selftest
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tempfile
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
DISC = HERE.parent
sys.path.insert(0, str(DISC / "scripts"))
from kernel_path import ensure_kernel_on_path  # noqa: E402
ensure_kernel_on_path(__file__)
from yishu_core.runtime import force_utf8_stdio  # noqa: E402
from yishu_core.eval import verdict_direction  # noqa: E402
from yishu_core.yingqi import LOOSE_WINDOW_DAYS, STRICT_WINDOW_DAYS, judge_window  # noqa: E402

sys.path.insert(0, str(HERE))
from outcome import MIN_N_FOR_CONCLUSION, wilson  # noqa: E402

STORE_DEFAULT = Path(os.environ["YI_PROSPECTIVE_STORE"]) if os.environ.get(
    "YI_PROSPECTIVE_STORE") else DISC / "data" / "feedback" / "predictions.jsonl"
GENESIS = "GENESIS"
STATES = ("occurred", "not_occurred", "unverifiable", "lost")

# 判卷口径本体：先于任何结果写死在此处。改动它＝改口径，须按 §四.4 在 CHANGELOG
# 登记并声明新旧记录不可比——scoring_rule_sha 不同组的记录会被 report 自动剔出汇总。
SCORING_RULE = (
    "判卷由口径现算、判卷人不手写命中：event_definition 须按正向框架「X 是否发生」书写；"
    "polarity=+1（吉组）且 state=occurred → 方向命中；polarity=-1（凶组）且 state=not_occurred → 方向命中；"
    "polarity=0 → 弃权（进弃权率，不进命中分母）；state∈{unverifiable,lost} → 右删失（不进分母，单独报比例）；"
    "应期严格窗 ±%d 日、宽松窗 ±%d 日（内核 yingqi 唯一口径），落窗=应验日∈封存窗口；"
    "task=占天候 的记录：事件定义即断语本身，occurred→命中、not_occurred→未命中（极性不参与判卷），"
    "与事项记录分桶列示、汇总同表不混计；"
    "口径改动＝新 scoring_rule_sha，旧口径记录自动剔出汇总、只报在册。"
    % (STRICT_WINDOW_DAYS, LOOSE_WINDOW_DAYS))


def rule_sha() -> str:
    return hashlib.sha256(SCORING_RULE.encode("utf-8")).hexdigest()[:12]


def _canon(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _strategy_version() -> str:
    parts = []
    for rel in ("data/rules/rule_registry.json", "scripts/timing.py", "scripts/step5.py"):
        p = DISC / rel
        parts.append(p.read_bytes() if p.exists() else rel.encode("utf-8"))
    return "v0.0.1+" + hashlib.sha1(b"|".join(parts)).hexdigest()[:8]


def read_rows(store: Path) -> list[dict]:
    if not store.exists():
        return []
    rows = []
    for ln in store.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            rows.append({"_bad_line": ln})
    return rows


def _row_digest(row: dict) -> str:
    s = "%s|%s|%s|%d" % (row.get("prev", ""), _canon(row.get("payload", {})),
                         row.get("kind", ""), row.get("seq", -1))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


def append_row(store: Path, kind: str, payload: dict) -> dict:
    rows = read_rows(store)
    seq = len(rows)
    prev = rows[-1]["digest"] if rows else GENESIS
    row = {"seq": seq, "ts": _now(), "kind": kind, "payload": payload,
           "prev": prev, "digest": ""}
    row["digest"] = _row_digest(row)
    store.parent.mkdir(parents=True, exist_ok=True)
    with open(store, "a", encoding="utf-8") as fh:
        fh.write(_canon(row) + "\n")
    return row


def verify(store: Path) -> list[str]:
    """返回问题清单（空＝链完整）。静默少算禁止：坏行/断链/悬空引用/重复封存全部显形。"""
    problems: list[str] = []
    rows = read_rows(store)
    seen_pid: dict[str, int] = {}
    resolved_pid: set[str] = set()
    for i, row in enumerate(rows):
        if "_bad_line" in row:
            problems.append("第 %d 行不是合法 JSON（截断/手改？）" % (i + 1))
            continue
        if row.get("seq") != i:
            problems.append("第 %d 行 seq=%s 不连续" % (i + 1, row.get("seq")))
        prev_expect = rows[i - 1]["digest"] if i > 0 else GENESIS
        if row.get("prev") != prev_expect:
            problems.append("第 %d 行 prev 断链（%s≠%s）" % (i + 1, row.get("prev"), prev_expect))
        if _row_digest(row) != row.get("digest"):
            problems.append("第 %d 行 digest 与重算不合（封存段被改写？）" % (i + 1))
        pl = row.get("payload", {})
        if row.get("kind") == "seal":
            if pl.get("pid") in seen_pid:
                problems.append("重复封存 pid=%s（第 %d 行）" % (pl.get("pid"), i + 1))
            seen_pid[pl.get("pid", "?")] = i
        elif row.get("kind") == "resolve":
            pid = pl.get("pid", "")
            if pid not in seen_pid:
                problems.append("回填引用了不存在的封存 pid=%s（第 %d 行）" % (pid, i + 1))
            if pid in resolved_pid:
                problems.append("pid=%s 被第二次判卷——封存事件只允许一次回填，"
                                "更正须走新记录并在 note 里说明" % pid)
            resolved_pid.add(pid)
    return problems


def _parse_window(s: str) -> tuple[date, date] | None:
    try:
        a, b = s.split("..")
        d0 = datetime.strptime(a.strip(), "%Y-%m-%d").date()
        d1 = datetime.strptime(b.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (d0, d1) if d1 >= d0 else None


def cmd_create(store: Path, analyze_path: str, qtype: str, event: str,
               window: str, note: str, task: str = "事项") -> int:
    if len(event) < 10:
        print("× 事件定义少于 10 字——「近期有变化」这类无法判卷的措辞不收（这正是本通道存在的原因）")
        return 1
    w = _parse_window(window)
    if w is None:
        print("× --window 需为 YYYY-MM-DD..YYYY-MM-DD 且止≥起")
        return 1
    if w[1] < date.today():
        print("× 窗口已关闭——前瞻通道只收「结果尚未揭晓」的登记；补录历史占断请走 outcome.py，"
              "事后立字据没有意义")
        return 1
    try:
        analyze = json.loads(Path(analyze_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print("× analyze JSON 读取失败：%s" % e)
        return 1
    concl = analyze.get("conclusion") or {}
    if "方向" not in concl:
        print("× 该 analyze 无 conclusion.方向——不是四段契约产物，拒绝入册")
        return 1
    dates = [d.get("date") for d in (concl.get("应期明细") or []) if isinstance(d, dict) and d.get("date")]
    payload = {
        "pid": hashlib.sha1(("%s|%s|%s|%s" % (_now(), event, analyze_path,
                                              os.urandom(4).hex())).encode("utf-8")).hexdigest()[:12],
        "sealed_at": _now(),
        "question": analyze.get("question", "") or concl.get("问题", ""),
        "question_type": qtype,
        "event_definition": event,
        "window": [w[0].isoformat(), w[1].isoformat()],
        "direction": str(concl.get("方向") or ""),
        "polarity": verdict_direction(concl.get("方向")),
        "main_yingqi": dates[0] if dates else "",
        "yingqi_dates": dates[:8],
        "hexagram": (analyze.get("chart_summary") or {}).get("卦名", "")
        or (analyze.get("original_hexagram") or {}).get("name", ""),
        "input_sha": hashlib.sha256(Path(analyze_path).read_bytes()).hexdigest()[:16],
        "task": task,
        "strategy_version": _strategy_version(),
        "scoring_rule_sha": rule_sha(),
        "note": note,
    }
    row = append_row(store, "seal", payload)
    print("√ 已封存 %s｜%s｜窗口 %s..%s｜方向 %s(pol%+d)｜主应期 %s"
          % (payload["pid"], payload["strategy_version"], payload["window"][0],
             payload["window"][1], payload["direction"], payload["polarity"],
             payload["main_yingqi"] or "—"))
    print("  口径 %s｜链头 %s（下次入库批次写进 CHANGELOG 锚定）"
          % (payload["scoring_rule_sha"], row["digest"]))
    return 0


def cmd_resolve(store: Path, id_prefix: str, state: str,
                actual_date: str, note: str) -> int:
    rows = read_rows(store)
    seals = {r["payload"]["pid"]: r["payload"] for r in rows
             if r.get("kind") == "seal" and "pid" in r.get("payload", {})}
    done = {r["payload"].get("pid") for r in rows if r.get("kind") == "resolve"}
    match = [p for p in seals if p.startswith(id_prefix)]
    if len(match) != 1:
        print("× pid 前缀需唯一命中一条封存：匹配 %d 条（%s）" % (len(match), id_prefix))
        return 1
    pid = match[0]
    if pid in done:
        print("× pid=%s 已回填过——封存事件的判卷只允许一次（改判请登记新记录，勿改写历史）" % pid)
        return 1
    if state in ("occurred", "not_occurred"):
        if not actual_date:
            print("× state=%s 必须带 --actual-date（结果事实没有日期就不算核验过）" % state)
            return 1
        try:
            datetime.strptime(actual_date, "%Y-%m-%d")
        except ValueError:
            print("× --actual-date 需为 YYYY-MM-DD")
            return 1
    elif actual_date:
        print("× state=%s（删失）不应携带应验日期——删失就是没有事实可登记" % state)
        return 1
    append_row(store, "resolve", {"pid": pid, "resolved_at": _now(), "state": state,
                                  "actual_date": actual_date or "", "note": note})
    print("√ 已回填 %s → %s%s（命中与分母由 report 按口径现算，此处不手写）"
          % (pid, state, "（应验 %s）" % actual_date if actual_date else ""))
    return 0


def cmd_list(store: Path, due_only: bool, as_json: bool = False) -> int:
    rows = read_rows(store)
    seals = [r["payload"] for r in rows if r.get("kind") == "seal"]
    resolved = {r["payload"].get("pid"): r["payload"] for r in rows if r.get("kind") == "resolve"}
    today = date.today().isoformat()
    due_items = []
    for s in sorted(seals, key=lambda x: x["window"][1]):
        r = resolved.get(s["pid"])
        overdue = r is None and s["window"][1] < today
        status = ("已回填:" + r["state"]) if r else ("逾期未判卷" if overdue else "待揭晓")
        if r is None:
            due_items.append({"pid": s["pid"], "window_end": s["window"][1],
                              "direction": s["direction"], "overdue": overdue,
                              "event_definition": s["event_definition"]})
        if as_json:
            continue
        if due_only and r is not None:
            continue
        print("  %s  窗 %s..%s  断=%s  %s  %s" % (s["pid"], s["window"][0], s["window"][1],
                                                  s["direction"] or "—", status, s["event_definition"][:24]))
    overdue_n = sum(1 for d in due_items if d["overdue"])
    if as_json:
        print(json.dumps({"seals": len(seals), "judged": len(resolved),
                          "pending": len(due_items), "overdue_unjudged": overdue_n,
                          "due": due_items, "today": today}, ensure_ascii=False))
        return 0
    print("在册封存 %d 条，已判卷 %d 条，逾期未判卷 %d 条" % (len(seals), len(resolved), overdue_n))
    return 0


def _wilson_block(label: str, hits: int, n: int) -> str:
    if n == 0:
        return "  %s：无数据" % label
    lo, hi = wilson(hits, n)
    flag = "样本足" if n >= MIN_N_FOR_CONCLUSION else \
        "样本不足(<%d)——仅为计数，不构成结论（铁律三）" % MIN_N_FOR_CONCLUSION
    return "  %s：%d/%d = %.1f%% [95%%CI %.1f–%.1f]  %s" % (label, hits, n, hits * 100.0 / n,
                                                            lo * 100, hi * 100, flag)


def cmd_report(store: Path, as_json: bool) -> int:
    problems = verify(store)
    if problems:
        print("× 封存链校验未过——先修复登记纪律再谈读数（禁止带病出分）：")
        for p in problems:
            print("  · " + p)
        return 2
    rows = read_rows(store)
    seals = {r["payload"]["pid"]: r["payload"] for r in rows if r.get("kind") == "seal"}
    reses = [r["payload"] for r in rows if r.get("kind") == "resolve"]
    cur = rule_sha()
    scorable: list[tuple[dict, dict]] = []   # (seal, resolve) 同口径可判卷
    abstained = censored = stale_rule = 0
    dir_hits = strict_hits = loose_hits = inwin_hits = win_n = 0
    task_n = task_hits = 0
    for r in reses:
        s = seals.get(r["pid"])
        if s is None:
            continue
        if s.get("scoring_rule_sha") != cur:
            stale_rule += 1
            continue
        if r["state"] in ("unverifiable", "lost"):
            censored += 1
            continue
        scorable.append((s, r))
        if s.get("task") == "占天候":
            task_n += 1
            if r["state"] == "occurred":
                task_hits += 1
        else:
            pol = s.get("polarity", 0)
            if pol == 0:
                abstained += 1
            elif (pol > 0) == (r["state"] == "occurred"):
                dir_hits += 1
    n_dir = sum(1 for s, _ in scorable
                if s.get("task") != "占天候" and s.get("polarity", 0) != 0)
    for s, r in scorable:
        ad = r.get("actual_date") or ""
        if not ad:
            continue
        win_n += 1
        j = judge_window(s.get("yingqi_dates") or [], ad)
        strict_hits += 1 if j["hit_strict"] else 0
        loose_hits += 1 if j["hit_loose"] else 0
        inwin_hits += 1 if s["window"][0] <= ad <= s["window"][1] else 0
    out = {
        "seals": len(seals), "resolved": len(reses), "censored": censored,
        "stale_rule_excluded": stale_rule, "abstained": abstained,
        "scoring_rule_sha": cur, "chain_head": rows[-1]["digest"] if rows else GENESIS,
        "direction": {"hits": dir_hits, "n": n_dir},
        "tianhou": {"hits": task_hits, "n": task_n},
        "yingqi_strict": {"hits": strict_hits, "n": win_n},
        "yingqi_loose": {"hits": loose_hits, "n": win_n},
        "in_window": {"hits": inwin_hits, "n": win_n},
        "min_n_for_conclusion": MIN_N_FOR_CONCLUSION,
    }
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print("═══ 前瞻封存判卷报告（现实效度样本，与古籍对齐分永不同屏混算——铁律三）═══")
    print("  在册封存 %d 条｜已判卷 %d 条｜删失(unverifiable/lost) %d 条｜旧口径剔除 %d 条｜弃权 %d 条"
          % (len(seals), len(reses), censored, stale_rule, abstained))
    if len(seals):
        print(_wilson_block("方向命中（事项）", dir_hits, n_dir))
        print(_wilson_block("占天候断语（独立桶，不并入上行）", task_hits, task_n))
        print(_wilson_block("应期·严格(±%d日)" % STRICT_WINDOW_DAYS, strict_hits, win_n))
        print(_wilson_block("应期·宽松(±%d日)" % LOOSE_WINDOW_DAYS, loose_hits, win_n))
        print(_wilson_block("应验日落封存窗", inwin_hits, win_n))
    else:
        print("  在册 0 条——通道就绪、证据为零。「回填 0 条」要读作尚无判卷样本，不是没有通道。")
    print("  判卷口径 sha=%s｜链头 %s" % (cur, out["chain_head"]))
    return 0


def _selftest_analyze(tmp: Path) -> str:
    a = {"question": "自检卦", "conclusion": {"方向": "吉",
         "应期明细": [{"date": (date.today() + timedelta(days=3)).isoformat(),
                       "rule": "逢值"}]}}
    p = tmp / "analyze.json"
    p.write_text(json.dumps(a, ensure_ascii=False), encoding="utf-8")
    return str(p)


def _w(ahead_days: int = 1, until_days: int = 10) -> str:
    return "%s..%s" % ((date.today() + timedelta(days=ahead_days)).isoformat(),
                       (date.today() + timedelta(days=until_days)).isoformat())


def cmd_selftest() -> int:
    """负例自证（§四.8）：篡改/悬空引用/重复判卷/缺日期/旧口径/短定义 全部必须被抓。"""
    captured: list[str] = []
    with tempfile.TemporaryDirectory(prefix="yi_prospective_st_") as td:
        tmp = Path(td)
        store = tmp / "predictions.jsonl"
        az = _selftest_analyze(tmp)
        ok_msgs: list[str] = []
        # 正向链路：create → resolve → report
        if cmd_create(store, az, "事业", "定义：offer 是否发到我手上（以邮件为准）",
                      _w(),
                      "") != 0:
            print("× selftest 正向 create 失败")
            return 1
        rows = read_rows(store)
        pid = rows[-1]["payload"]["pid"]
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_resolve(store, pid, "not_occurred",
                             (date.today() + timedelta(days=11)).isoformat(), "自检：窗满未发生")
        if rc != 0:
            print("× selftest 正向 resolve 失败：%s" % buf.getvalue())
            return 1
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_report(store, False)
        t = buf.getvalue()
        if rc != 0 or "不构成结论" not in t:
            captured.append("小样本拒绝出结论（report n<30 措辞）")
        # 负例1：篡改封存段 → verify 必红
        lines = store.read_text(encoding="utf-8").splitlines()
        bad = json.loads(lines[-2])
        bad["payload"]["event_definition"] = "定义：被我改写的事件"
        lines[-2] = _canon(bad)
        store.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if not verify(store):
            captured.append("封存段篡改未被哈希链识破")
        # 负例2：判卷引用不存在的封存 → verify 必红
        store.unlink()
        cmd_create(store, az, "事业", "定义：offer 是否发到我手上（以邮件为准）",
                   _w(), "")
        append_row(store, "resolve", {"pid": "ffffffffffffff", "state": "occurred",
                                      "actual_date": date.today().isoformat(), "note": ""})
        if not any("不存在的封存" in p for p in verify(store)):
            captured.append("悬空回填引用未被识破")
        # 负例3：同一封存被二次判卷 → verify 必红
        store.unlink()
        cmd_create(store, az, "事业", "定义：offer 是否发到我手上（以邮件为准）",
                   _w(), "")
        pid = read_rows(store)[0]["payload"]["pid"]
        cmd_resolve(store, pid, "occurred", date.today().isoformat(), "")
        if cmd_resolve(store, pid, "not_occurred", date.today().isoformat(), "改判") == 0:
            captured.append("同一封存的二次判卷未被拒绝（历史可被改写）")
        # 负例4：occurred 缺应验日期 → 拒绝
        store.unlink()
        cmd_create(store, az, "事业", "定义：offer 是否发到我手上（以邮件为准）",
                   _w(), "")
        pid = read_rows(store)[0]["payload"]["pid"]
        if cmd_resolve(store, pid, "occurred", "", "") == 0:
            captured.append("occurred 缺 --actual-date 竟放行")
        # 负例5：窗口已关闭的「事后立字据」→ create 拒绝
        if cmd_create(store, az, "事业", "定义：上周是否已经发生的事",
                      "2020-01-01..2020-01-10", "") == 0:
            captured.append("窗口已关闭的事后登记竟放行")
        # 负例6：事件定义过短（不可判卷措辞）→ create 拒绝
        if cmd_create(store, az, "事业", "有变化",
                      _w(), "") == 0:
            captured.append("少于 10 字的不可判卷定义竟放行")
        # 负例7：旧口径记录 → report 剔出汇总并具名计数
        store.unlink()
        cmd_create(store, az, "事业", "定义：offer 是否发到我手上（以邮件为准）",
                   _w(), "")
        rows = read_rows(store)
        r0 = rows[0]
        r0["payload"]["scoring_rule_sha"] = "deadbeef0000"
        r0["digest"] = ""  # 重算前留空
        r0["digest"] = _row_digest(r0)
        store.write_text(_canon(r0) + "\n", encoding="utf-8")
        cmd_resolve(store, r0["payload"]["pid"], "occurred", date.today().isoformat(), "")
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_report(store, False)
        t = buf.getvalue()
        if rc != 0 or "旧口径剔除 1 条" not in t:
            captured.append("旧口径记录未被剔出汇总（口径变更会静默混算）")
        # 负例8：占天候 task 桶独立判卷（不依赖吉凶极性、不混事项分母）
        store.unlink()
        th = json.loads(Path(az).read_text(encoding="utf-8"))
        th["conclusion"]["方向"] = "晴"   # verdict_direction("晴")=0 → 走极性规则必入弃权
        Path(az).write_text(json.dumps(th, ensure_ascii=False), encoding="utf-8")
        if cmd_create(store, az, "天候", "定义：offer 是否发到我手上（以邮件为准）",
                      _w(), "", "占天候") != 0:
            captured.append("占天候 create 未走通")
        pid = read_rows(store)[-1]["payload"]["pid"]
        cmd_resolve(store, pid, "occurred", date.today().isoformat(), "判据：open-meteo 模拟值")
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc = cmd_report(store, True)
        rep = {}
        try:
            rep = json.loads(buf2.getvalue())
        except json.JSONDecodeError:
            captured.append("report --json 输出非纯 JSON")
        if rc != 0 or rep.get("tianhou", {}).get("hits") != 1 or rep.get("tianhou", {}).get("n") != 1:
            captured.append("占天候 task 桶未独立判卷：%r" % rep.get("tianhou"))
        if rep.get("direction", {}).get("n") != 0:
            captured.append("占天候记录混进了事项方向分母（两桶混算）")
    if captured:
        print("× selftest 抓到漏洞（本模块是摆设）：")
        for c in captured:
            print("  · " + c)
        return 1
    print("√ selftest：正向链路通；小样本拒判 + 8 类负例（篡改链/悬空引用/二次判卷/缺日期/事后立据/短定义/旧口径混算/占天候桶独立）全部被抓")
    # 真实库存在时顺手复核（在册数字必须显形，不许静默）
    if STORE_DEFAULT.exists():
        probs = verify(STORE_DEFAULT)
        n = len(read_rows(STORE_DEFAULT))
        if probs:
            print("× 盘上在册库链校验未过：")
            for p in probs:
                print("  · " + p)
            return 1
        print("√ 盘上在册库链完整：%d 行（封存判卷在册，report 出数）" % n)
    else:
        print("√ 盘上在册库尚未建立（0 条）——通道就绪、证据为零，与 README 口径一致")
    return 0


def main() -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(description="前瞻预测封存登记：预测先冻结、结果后揭晓、口径先写死")
    ap.add_argument("--selftest", action="store_true", help="负例自证（门 [28] 用）")
    ap.add_argument("--store", default=None, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd")
    p_c = sub.add_parser("create", help="封存一条前瞻预测（analyze JSON 为唯一事实源）")
    p_c.add_argument("--analyze", required=True)
    p_c.add_argument("--question-type", default="综合")
    p_c.add_argument("--event", required=True, help="事件定义：什么算发生，以何为准")
    p_c.add_argument("--window", required=True, help="YYYY-MM-DD..YYYY-MM-DD，止须晚于今日")
    p_c.add_argument("--note", default="")
    p_c.add_argument("--task", default="事项", help="任务面（事项/占天候），决定判卷分支")
    p_r = sub.add_parser("resolve", help="回填一条结果（只追加，不判卷）")
    p_r.add_argument("--id", required=True)
    p_r.add_argument("--state", required=True, choices=STATES)
    p_r.add_argument("--actual-date", default="")
    p_r.add_argument("--note", default="")
    p_l = sub.add_parser("list", help="在册封存与判卷状态")
    p_l.add_argument("--due", action="store_true", help="只列待揭晓/逾期未判卷")
    p_l.add_argument("--json", action="store_true", help="机器可读到期队列（外部排程回访用，第一百七十八批）")
    p_p = sub.add_parser("report", help="按口径现算命中（必带 n/Wilson CI，n 不足拒判）")
    p_p.add_argument("--json", action="store_true")
    sub.add_parser("verify", help="复核哈希链")
    args = ap.parse_args()
    if args.selftest:
        return cmd_selftest()
    store = Path(args.store) if args.store else STORE_DEFAULT
    if args.cmd == "create":
        return cmd_create(store, args.analyze, args.question_type, args.event,
                          args.window, args.note, args.task)
    if args.cmd == "resolve":
        return cmd_resolve(store, args.id, args.state, args.actual_date, args.note)
    if args.cmd == "list":
        return cmd_list(store, args.due, args.json)
    if args.cmd == "report":
        return cmd_report(store, args.json)
    if args.cmd == "verify":
        probs = verify(store)
        for p in probs:
            print("  · " + p)
        print("√ 链完整（在册 %d 行）" % len(read_rows(store)) if not probs else "× 链断，见上")
        return 0 if not probs else 2
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
