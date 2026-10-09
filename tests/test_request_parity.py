# -*- coding: utf-8 -*-
"""Request 契约与深链语义 parity 测试（P1 稳定协议）。

覆盖：
  7. CLI/Web/Actions request parity —— 同一输入在所有入口产生同一 normalized
     request；同一 normalized request 产出同一 chart argv（宿主无关）。
  8. deep-link semantic parity —— web.js DEEPLINK_KEYS 的短键映射在 Python 侧
     模拟后，与完整字段请求归一化结果逐字段一致；短键集合锁定在
     REQUEST_FIELDS 白名单内（[1h] 门的 pytest 侧等价）。
  9. **字段宇宙无死字段**（本文件的主判据，补 [1h] 的门盲区）——
     `REQUEST_FIELDS` 的每个键都必须二选一：
       (a) 声明为 `argv` 消费，且**实测**出现在 `chart_argv` 对某科的产出里
           （`FIELD_PROBES` 逐字段探针，含旗标名与旗标值两处比对）；
       (b) 声明为 `display` 用途，且由 `report_meta` 带用途标注回显
           （`DISPLAY_PURPOSE`，如 `name` =「仅用于产物文件命名，不参与任何推演」）。
     并把四处对外调用面（web.js 短键表 / ci_request 别名表 / report.py 请求字段 /
     cli execute 旗标）逐一对齐同一白名单——[1h] 只做 `短键 ⊆ 白名单` 的单向子集，
     白名单自身含死字段时它永远绿；这里的判据是双向的。
     同一判据建议搬进 `tools/check.py` 的 [1h]（本文件不依赖 check.py，可独立跑）。

协议指纹基线（normalize_request 正/负例）另有 [1f] 门
`tools/request_protocol_golden.py`，此处不重复其逐字段指纹。
"""
from __future__ import annotations

import importlib.util
import inspect
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "core"))

from yishu_core.report.request import (  # noqa: E402
    DISPLAY_PURPOSE,
    FIELD_LABEL,
    FIELD_SCOPE,
    FIELD_USAGE,
    REQUEST_FIELDS,
    USAGE_ARGV,
    USAGE_DISPLAY,
    analyze_argv,
    chart_argv,
    chart_inputs,
    fields_for,
    normalize_request,
    render_argv,
    report_meta,
)

# 已随学科收缩移除的死字段：曾经躺在白名单里、被 report_meta 印进页头，
# 却没有任何引擎阶段读它。此处的负例锁防它们被"顺手加回来"。
DEAD_FIELDS = ("way", "date", "activity", "hour_branch", "direction",
               "up", "mid", "down", "lunar", "year", "month", "day")

# 各的最小请求基线（探针在此之上叠加被测试字段）
BASE = {
    "liuyao": {"discipline": "liuyao", "question": "占求财"},
    "ming": {"discipline": "ming", "datetime": "1990-05-20 10:30"},
}

# argv 类字段探针：字段 → [(学科, 叠加请求, 期望旗标, 期望旗标值或 None=开关)]
# 判据是"旗标名与旗标值都要真的出现在 chart_argv 产出里"，不是"字段在白名单里"。
FIELD_PROBES: dict[str, list[tuple[str, dict, str, str | None]]] = {
    "question": [
        ("liuyao", {"question": "占本周面试"}, "--question", "占本周面试"),
        ("ming", {"question": "命局分析"}, "--question", "命局分析"),
    ],
    "datetime": [
        ("liuyao", {"datetime": "2026-09-30 10:30"}, "--datetime", "2026-09-30 10:30"),
        ("ming", {"datetime": "1990-05-20 10:30"}, "--datetime", "1990-05-20 10:30"),
    ],
    "gender": [("ming", {"gender": "女"}, "--gender", "女")],
    "mode": [("liuyao", {"mode": "number", "numbers": "3,5,7"}, "--mode", "number")],
    "numbers": [("liuyao", {"mode": "number", "numbers": "3,5,7"}, "--numbers", "3,5,7")],
    "yao": [("liuyao", {"mode": "manual", "yao": "7,8,9,7,6,8"}, "--yao", "7,8,9,7,6,8")],
    "seed": [("liuyao", {"seed": 7}, "--seed", "7")],
    "longitude": [
        ("liuyao", {"longitude": 116.4}, "--longitude", "116.4"),
        ("ming", {"longitude": 121.5}, "--longitude", "121.5"),
    ],
    "hour": [("liuyao", {"hour": 23}, "--hour", "23")],
    "distinguish_zi_hour": [
        ("liuyao", {"distinguish_zi_hour": True}, "--distinguish-zi-hour", None)],
    "zi_hour_type": [("liuyao", {"zi_hour_type": "late"}, "--zi-hour-type", "late")],
}

# 执行器自有选项（不是请求字段，不参与白名单比对）
RUNNER_ONLY_DESTS = {"output", "output_html", "request", "outdir", "result_json"}


def _read_deeplink_keys() -> dict[str, str]:
    """从 web.js 读 DEEPLINK_KEYS（短键 → 请求字段），与 [1h] 同源而非复制。"""
    js = (ROOT / "web" / "web.js").read_text(encoding="utf-8")
    block = re.search(r"DEEPLINK_KEYS\s*=\s*\{(.*?)\}", js, re.S)
    assert block, "web.js 缺 DEEPLINK_KEYS"
    return {k: v for k, v in re.findall(r"(\w+):\s*'([^']+)'", block.group(1))}


def _load_by_path(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _report_py_request_fields() -> set[str]:
    """tools/report.py 真正塞进请求 dict 的字段名（从源码取，不重复实现一遍）。"""
    src = inspect.getsource(_load_by_path("tools/report.py", "yi_report_for_probe")._request_from_args)
    return set(re.findall(r"(\w+)=args\.\w+", src))


def _cli_execute_dests() -> set[str]:
    """cli/main.py `execute` 子命令的旗标 dest 集合。"""
    mod = _load_by_path("cli/main.py", "yi_cli_for_probe")
    parser = mod._build_parser()
    exec_parser = next(a for a in parser._subparsers._group_actions[0].choices.values()
                       if getattr(a, "prog", "") == "yi execute")
    return {a.dest for a in exec_parser._actions if a.dest != "help"}


def _apply_deeplink(query: str) -> dict:
    """模拟 web.js readDeepLink()：d=学科 + 短键 → 请求 dict（空值丢弃）。"""
    keys = _read_deeplink_keys()
    qs = parse_qs(query)
    out: dict = {}
    disc = qs.get("d") or qs.get("discipline")
    if disc:
        out["discipline"] = disc[-1]
    for short, key in keys.items():
        if short in qs and qs[short][-1]:
            out[key] = qs[short][-1]
    return out


class TestFieldUniverse:
    """字段宇宙 = 有消费方的字段。死字段（收进白名单却没人读）在本类判红。"""

    def test_whitelist_scope_and_usage_tables_agree(self) -> None:
        assert set(FIELD_USAGE) == set(REQUEST_FIELDS), \
            "白名单与 FIELD_USAGE 不同源（ REQUEST_FIELDS 必须由 FIELD_USAGE 派生）"
        assert set(FIELD_SCOPE) == set(REQUEST_FIELDS), \
            "FIELD_SCOPE 与白名单不一致：新字段忘了声明消费学科"
        bad = {f: u for f, u in FIELD_USAGE.items() if u not in (USAGE_ARGV, USAGE_DISPLAY)}
        assert not bad, f"未知消费方式声明：{bad}"

    def test_no_dead_fields_in_whitelist(self) -> None:
        """已删学科遗留字段不得回到白名单（它们没有 chart.py 消费方）。"""
        back = [f for f in DEAD_FIELDS if f in REQUEST_FIELDS]
        assert not back, f"死字段复现：{back}"

    def test_every_argv_field_is_actually_forwarded(self) -> None:
        """argv 类字段：必须实测到"旗标 + 值"进了 chart_argv 产出，逐科覆盖其 scope。"""
        argv_fields = {f for f, u in FIELD_USAGE.items() if u == USAGE_ARGV}
        missing_probe = argv_fields - set(FIELD_PROBES)
        assert not missing_probe, f"argv 字段没有探针（无法证明被转发）：{sorted(missing_probe)}"
        for field in sorted(argv_fields):
            probes = FIELD_PROBES[field]
            covered = {d for d, _extra, _flag, _val in probes}
            assert covered == set(FIELD_SCOPE[field]), (
                f"{field} 的探针覆盖 {sorted(covered)}，"
                f"但其 scope 是 {sorted(FIELD_SCOPE[field])}——某科收下不转发")
            for disc, extra, flag, value in probes:
                req = normalize_request({**BASE[disc], **extra})
                argv = chart_argv(req, "chart.py", "o.json")
                assert flag in argv, (
                    f"{field} 声明为 argv 消费，但 {disc} 的命令行里没有 {flag}：{argv}")
                if value is None:
                    assert argv.count(flag) == 1
                else:
                    assert argv[argv.index(flag) + 1] == value, (
                        f"{field} 在 {disc} 的旗标值不符：期望 {value}，argv={argv}")

    def test_display_fields_are_echoed_with_explicit_purpose(self) -> None:
        """display 类字段：必须在 DISPLAY_PURPOSE 有口径，且 report_meta 真的带标注回显。"""
        display_fields = {f for f, u in FIELD_USAGE.items() if u == USAGE_DISPLAY}
        assert set(DISPLAY_PURPOSE) == display_fields, \
            "display 字段与 DISPLAY_PURPOSE 不一致（页头回显必须有显式用途口径）"
        for field in sorted(display_fields):
            # discipline 的值就是学科本身，不能用别的值去覆盖它
            extra = {} if field == "discipline" else {field: "张三"}
            req = normalize_request({**BASE["liuyao"], **extra})
            meta = report_meta(req, runtime="本机/CI 子进程")
            assert DISPLAY_PURPOSE[field] in meta, \
                f"{field} 声明为 display，但页头没有它的用途标注：{meta}"

    def test_report_meta_echoes_only_forwarded_inputs(self) -> None:
        """页头每一项：要么真的在 chart_argv 的旗标/取值里，要么明写"不参与推演"（铁律三）。"""
        req = normalize_request({
            "discipline": "liuyao", "question": "占合同", "mode": "time",
            "datetime": "2026-10-09 23:10", "hour": 23, "distinguish_zi_hour": "1",
            "zi_hour_type": "early", "longitude": 116.4, "seed": 7, "name": "张三",
        })
        argv = chart_argv(req, "chart.py", "o.json")
        meta = report_meta(req, runtime="本机/CI 子进程")
        label_to_field = {v: k for k, v in FIELD_LABEL.items()}
        switch_flags = {f: flag for f, probes in FIELD_PROBES.items()
                        for _d, _e, flag, value in probes if value is None}
        for bit in meta.split("　｜　"):
            label, _, value = bit.partition("：")
            if label in ("学科", "运行环境", "生成"):
                continue
            if "不参与任何推演" in bit:
                continue  # 仅命名类：已显式标注用途
            field = label_to_field.get(label)
            assert field in chart_inputs(req), \
                f"页头出现无出处的回显项（不在 chart_inputs 里）：{bit}"
            if field in switch_flags:
                assert switch_flags[field] in argv, \
                    f"开关字段 {field} 页头写了「{value}」却没进命令行旗标：{argv}"
            else:
                assert value in argv, f"页头回显了未进入命令行的输入：{bit}（argv={argv}）"

    def test_chart_inputs_is_the_single_source_for_argv(self) -> None:
        """chart_argv 的取值全部来自 chart_inputs（页头与命令行同源，防两处漂移）。"""
        req = normalize_request({**BASE["liuyao"], "mode": "manual",
                                 "yao": "7,8,9,7,6,8", "datetime": "2026-09-22 23:40"})
        ins = chart_inputs(req)
        argv = chart_argv(req, "chart.py", "o.json")
        assert set(ins) <= set(REQUEST_FIELDS)
        for value in ins.values():
            assert str(value) in argv
        # analyze/render 两段不读请求字段（除学科名），这里锁住"没有第三处悄悄加旗标"
        assert analyze_argv(req, "analyze.py", "c.json", "a.json") == \
            ["analyze.py", "c.json", "-o", "a.json"]
        assert render_argv(req, "render.py", "a.json", "r.md") == \
            ["render.py", "a.json", "-f", "md", "-o", "r.md"]


class TestEntrySurfacesUseTheSameWhitelist:
    """四处对外调用面不得各自兜售白名单之外的字段。"""

    def test_deeplink_short_keys_point_to_live_fields(self) -> None:
        keys = _read_deeplink_keys()
        unknown = {v for v in keys.values() if v not in REQUEST_FIELDS}
        assert not unknown, f"深链短键指向未知字段：{unknown}"

    def test_ci_request_aliases_point_to_live_fields(self) -> None:
        mod = _load_by_path("tools/ci_request.py", "yi_ci_request_for_probe")
        unknown = sorted({v for v in mod.FIELD_ALIASES.values()} - set(REQUEST_FIELDS))
        assert not unknown, f"通道 B 别名表指向死字段：{unknown}"
        # 反向：中文别名不能把已删学科的键再引进来
        for alias, target in mod.FIELD_ALIASES.items():
            assert target not in DEAD_FIELDS, f"别名 {alias} 仍映射到死字段 {target}"

    def test_report_py_flags_point_to_live_fields(self) -> None:
        used = _report_py_request_fields()
        dead = sorted(used - set(REQUEST_FIELDS))
        assert not dead, f"tools/report.py 仍收集白名单外的字段：{dead}"

    def test_cli_execute_flags_point_to_live_fields(self) -> None:
        dests = _cli_execute_dests() - RUNNER_ONLY_DESTS
        dead = sorted(dests - set(REQUEST_FIELDS))
        assert not dead, f"cli/main.py execute 仍暴露白名单外的旗标：{dead}"

    def test_executor_argparse_exposes_only_live_fields(self) -> None:
        """两个执行器的 `--旗标` 只能是请求字段或执行器自有选项。

        这是"四处调用面同步收口"里最容易漏的一处：旧 `tools/report.py --help`
        兜售过 `--way`（梅花/小六壬）、`--date/--activity`（择吉）、`--up/--mid/--down`
        （灵棋经）、`--hour-branch`、`--direction`——收了之后没有任何引擎阶段读它。
        """
        allowed = set(REQUEST_FIELDS) | RUNNER_ONLY_DESTS
        for rel in ("tools/report.py", "cli/main.py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            flags = {re.sub(r"-", "_", m) for m in
                     re.findall(r'add_argument\("--([a-z][a-z0-9-]*)"', text)}
            dead = sorted(flags - allowed)
            assert not dead, f"{rel} 仍暴露白名单外的旗标：{dead}"


class TestEntryParity:
    """一个输入在不同入口产生完全相同的 normalized request。"""

    FULL_REQUESTS = [
        {"discipline": "liuyao", "question": "占求财", "mode": "time",
         "datetime": "2026-09-30 10:30"},
        {"discipline": "ming", "question": "命盘", "datetime": "1990-05-20 10:30",
         "gender": "男"},
    ]

    def test_normalize_is_entry_independent(self) -> None:
        """normalize_request 是纯函数：同一 dict 从任何入口进来结果一致。"""
        for req in self.FULL_REQUESTS:
            a = normalize_request(dict(req))
            b = normalize_request(dict(req))
            assert a == b
            # 归一化输出只含白名单字段（无入口私有字段混入）
            assert set(a) <= set(REQUEST_FIELDS)

    def test_equivalent_forms_same_argv(self) -> None:
        """显式给默认值 vs 缺省 → 同一 argv（mode 默认逻辑单点在 request.py）。"""
        r1 = normalize_request({"discipline": "liuyao", "question": "q",
                                "mode": "time", "datetime": "2026-09-30 10:30"})
        r2 = normalize_request({"discipline": "liuyao", "question": "q",
                                "datetime": "2026-09-30 10:30"})
        assert chart_argv(r1, "chart.py", "o.json") == chart_argv(r2, "chart.py", "o.json")

    def test_actions_extra_json_fields_are_request_fields(self) -> None:
        """通道 B 的 extra 高级字段都在 REQUEST_FIELDS 白名单内——三条通道共用同一
        字段宇宙；死字段（way/date/activity/up/mid/down）不得再出现在任何通道。"""
        for f in ("mode", "numbers", "yao", "seed", "hour", "distinguish_zi_hour",
                  "zi_hour_type", "longitude", "datetime", "gender", "question",
                  "discipline", "name"):
            assert f in REQUEST_FIELDS
        for f in ("way", "date", "activity", "hour_branch", "direction",
                  "up", "mid", "down"):
            assert f not in REQUEST_FIELDS


class TestWhitelistIsEnforced:
    """"表外一律抛 ValueError"必须是实现，不只是 docstring。"""

    @pytest.mark.parametrize("req", [
        {"discipline": "liuyao", "question": "某事", "way": "time"},
        {"discipline": "liuyao", "question": "某事", "activity": "出行"},
        {"discipline": "liuyao", "question": "某事", "date": "2026-10-09"},
        {"discipline": "liuyao", "question": "某事", "hour_branch": "酉"},
        {"discipline": "liuyao", "question": "某事", "direction": "东"},
        {"discipline": "liuyao", "question": "某事", "up": 3, "mid": 4, "down": 1},
        {"discipline": "liuyao", "question": "某事", "bogus": "x"},
    ])
    def test_unknown_field_rejected_with_options(self, req: dict) -> None:
        with pytest.raises(ValueError) as exc:
            normalize_request(req)
        msg = str(exc.value)
        assert "未知字段" in msg
        # 报错要列出该科可选字段，任务 AI 才能自我纠正
        for f in fields_for(req["discipline"]):
            assert f in msg

    @pytest.mark.parametrize("req,off", [
        ({"discipline": "liuyao", "question": "某事", "gender": "男"}, "gender"),
        ({"discipline": "ming", "datetime": "1990-05-20 10:30", "mode": "coin"}, "mode"),
        ({"discipline": "ming", "datetime": "1990-05-20 10:30", "zi_hour_type": "early"},
         "zi_hour_type"),
    ])
    def test_out_of_scope_field_rejected(self, req: dict, off: str) -> None:
        """本科不消费的字段=会被静默丢弃=死输入，同样拒绝（不是收下不用）。"""
        with pytest.raises(ValueError) as exc:
            normalize_request(req)
        assert off in str(exc.value)

    @pytest.mark.parametrize("req", [
        {"discipline": "liuyao", "question": "某事", "mode": "no-such-mode"},
        {"discipline": "liuyao", "question": "某事", "hour": 99},
        {"discipline": "liuyao", "question": "某事", "hour": "辰"},
        {"discipline": "liuyao", "question": "某事", "zi_hour_type": "middle"},
        {"discipline": "liuyao", "question": "某事", "distinguish_zi_hour": "maybe"},
    ])
    def test_illegal_value_rejected(self, req: dict) -> None:
        with pytest.raises(ValueError):
            normalize_request(req)

    def test_flag_forms_all_accepted(self) -> None:
        """bool / "1" / "true" / "是" 都归一化成同一个开关注记。"""
        for raw in (True, "1", "true", "TRUE", "是", "yes"):
            req = normalize_request({"discipline": "liuyao", "question": "某事",
                                     "distinguish_zi_hour": raw})
            assert req["distinguish_zi_hour"] is True
            assert "--distinguish-zi-hour" in chart_argv(req, "chart.py", "o.json")
        for raw in (False, "0", "false", "否", "off"):
            req = normalize_request({"discipline": "liuyao", "question": "某事",
                                     "distinguish_zi_hour": raw})
            assert "--distinguish-zi-hour" not in chart_argv(req, "chart.py", "o.json")


class TestDeeplinkSemanticParity:
    def test_short_keys_within_whitelist(self) -> None:
        keys = _read_deeplink_keys()
        unknown = {v for v in keys.values() if v not in REQUEST_FIELDS}
        assert not unknown, f"深链短键指向未知字段：{unknown}"

    def test_ai_sop_deeplink_table_matches_js_short_keys(self) -> None:
        """docs/AI-SOP.md 的深链表（任务 AI 的唯一说明书）必须与 web.js 短键表恒等。

        收缩没做完的典型形态就是"引擎删了、说明书还在教收集"——所以这里做的是
        **双向**集合相等，不是"文档提到的键 ⊆ 代码支持的键"。
        """
        doc = (ROOT / "docs" / "AI-SOP.md").read_text(encoding="utf-8")
        section = doc.split("### 2.1", 1)[1].split("### 2.2", 1)[0]
        documented = set(re.findall(r"^\|\s*`([a-zA-Z_]+)`\s*\|", section, re.M))
        implemented = set(_read_deeplink_keys()) | {"d", "auto"}
        assert documented == implemented, (
            f"AI-SOP 深链表与 web.js 不一致：文档多出的键={sorted(documented - implemented)}，"
            f"代码有而文档没写的键={sorted(implemented - documented)}")
        dead = sorted(v for v in _read_deeplink_keys().values() if v in DEAD_FIELDS)
        assert not dead, f"深链短键仍指向死字段：{dead}"

    def test_deeplink_query_equals_full_request(self) -> None:
        """深链 query 的归一化结果 == 完整字段请求的归一化结果（语义等价）。"""
        query = "d=liuyao&q=占求财&mode=time&dt=2026-09-30 10:30"
        via_deeplink = normalize_request(_apply_deeplink(query))
        full = normalize_request({"discipline": "liuyao", "question": "占求财",
                                  "mode": "time", "datetime": "2026-09-30 10:30"})
        assert via_deeplink == full
        assert chart_argv(via_deeplink, "chart.py", "o.json") == \
            chart_argv(full, "chart.py", "o.json")

    def test_deeplink_ming_parity(self) -> None:
        query = "d=ming&dt=1990-05-20 10:30&g=男"
        via_deeplink = normalize_request(_apply_deeplink(query))
        full = normalize_request({"discipline": "ming", "datetime": "1990-05-20 10:30",
                                  "gender": "男"})
        assert via_deeplink == full

    def test_deeplink_discipline_shortkey_required(self) -> None:
        """无学科 = 无请求（d= 是深链的结构性必填，与 CLI --discipline 同位）。"""
        out = _apply_deeplink("q=占事")
        assert "discipline" not in out
        with pytest.raises(ValueError):
            normalize_request(out)

    def test_stale_deeplink_keys_dropped_and_announced(self) -> None:
        """收缩前教过的死键（&way / &date / &activity / &yb / &dir / &up）：
        短键表已不含它们，所以通道 A 不会把它们送进请求；同时 web.js 必须
        **说出来**（log 一行"已忽略"），不许静默吞——静默吞掉与旧缺陷"收下但
        不转发"是同一类口径问题。"""
        out = _apply_deeplink("d=liuyao&q=占事&way=time&date=2026-09-30&activity=开市")
        assert set(out) <= set(REQUEST_FIELDS)
        assert not ({"way", "date", "activity"} & set(out)), f"深链仍能夹带死字段：{out}"
        js = (ROOT / "web" / "web.js").read_text(encoding="utf-8")
        body = js.split("function readDeepLink()", 1)[1].split("\n}", 1)[0]
        assert "已忽略" in body, "readDeepLink 对未知键必须显式告警，不许静默丢弃"

    def test_dead_field_rejected_if_it_reaches_python(self) -> None:
        """任何入口把死字段送到内核（如 repository_dispatch 的 client_payload、
        request.json 手改），一律 ValueError——不是收下不用。"""
        for dead in ("way", "activity", "date", "hour_branch", "direction", "up"):
            with pytest.raises(ValueError):
                normalize_request({"discipline": "liuyao", "question": "某事", dead: "x"})
