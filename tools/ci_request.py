# -*- coding: utf-8 -*-
"""把各类 GitHub 触发统一解析成 report.py 需要的 request.json + meta.json。

支持触发（GITHUB_EVENT_NAME）：
  workflow_dispatch  从 INPUT_* 风格环境变量取表单（workflow 里显式注入）
  repository_dispatch  client_payload 即请求体（event.client_payload）
  issues(opened/edited)   解析 issue 标题/正文（JSON 代码块 或 key:value）
  issue_comment(created)  解析评论正文（须以 /yi 开头）

解析出的请求字段（唯一真值源是内核 `yishu_core.report.request.REQUEST_FIELDS`，
本表的键值目标必须落在它里面，否则就是"收了没人读"的死字段）：
discipline/question/datetime/gender/mode/numbers/yao/seed/longitude/
hour/distinguish_zi_hour/zi_hour_type/name。
别名表已随学科收缩移除死键（way/date/activity/hour_branch/direction/up/mid/down）；
表外键不再静默丢弃，而是在 stderr 明示"本通道不接受"，因为通道 B 的下游
`tools/report.py` 同样会拒绝它们。同时：
  - 写 meta.json（触发器、issue 号、是否回写评论、是否提交 reports 分支等）
  - 若存在 GITHUB_OUTPUT，则追加 should_run / has_issue / commit_branch，
    供 workflow 的步骤 if 条件使用。

零第三方依赖。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# 中文别名 → 请求字段。右侧值 ⊆ request.REQUEST_FIELDS（tests/test_request_parity.py
# 逐条断言；多出一条就是死别名，会静默吞掉求测者给的输入）。
FIELD_ALIASES = {
    "discipline": "discipline", "学科": "discipline",
    "question": "question", "问题": "question", "占问": "question",
    "datetime": "datetime", "时间": "datetime", "出生": "datetime",
    "出生时间": "datetime",
    "gender": "gender", "性别": "gender",
    "mode": "mode", "模式": "mode", "起卦方式": "mode",
    "numbers": "numbers", "数字": "numbers",
    "yao": "yao", "爻值": "yao",
    "longitude": "longitude", "经度": "longitude",
    "name": "name", "名字": "name",
    # 六爻时间口径三旗标（chart.py 的 --hour / --distinguish-zi-hour / --zi-hour-type）
    "hour": "hour", "小时": "hour", "指定小时": "hour",
    "distinguish_zi_hour": "distinguish_zi_hour", "区分早晚子时": "distinguish_zi_hour",
    "子时区分": "distinguish_zi_hour",
    "zi_hour_type": "zi_hour_type", "子时类型": "zi_hour_type", "子时口径": "zi_hour_type",
    # 六爻随机种子
    "seed": "seed", "种子": "seed",
}
FIELDS = tuple(dict.fromkeys(FIELD_ALIASES.values()))

# issue 评论触发时允许的评论者权限（author_association）。公开仓库里任何人都能
# 评论 "/yi …"；不校验就等于把 Actions 分钟与 bot 的提交能力开放给全网。
# 需要更宽的口子时用 YI_ALLOW_ASSOCIATIONS 环境变量覆盖（逗号分隔）。
DEFAULT_ALLOWED_ASSOCIATIONS = ("OWNER", "MEMBER", "COLLABORATOR")


def _coerce(field: str, value):
    if field == "longitude":
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
    return str(value).strip()


def parse_kv_text(text: str, ignored: list[str] | None = None) -> dict:
    """解析 JSON 代码块 或 'key: value' / 'key=value' 行（含中文键别名）。

    兼容三种写法（issue 正文、issue 正文里的 `/yi` 命令行）：
        discipline: liuyao
        /yi discipline: liuyao
        /yi discipline=ming question=占求财     ← 同一行多个键值对
    历史缺陷：旧正则要求键紧跟在（去掉行首 `/` 之后的）行首，于是
    `/yi discipline: ming` 里的 `discipline` 前面还有 `yi ` 就整行不匹配，
    命令行的 key:value 会被**静默丢弃**（触发成功但请求为空）。

    `ignored` 给了就收集"形似键值对却不在字段宇宙里"的键名（issue 正文混着散文，
    这里不能直接报错；但静默吞掉同样不行——调用方会把它写进 stderr 与 meta.json，
    让人一眼看见"我给的那个键没人读"）。
    """
    text = text.strip()
    seen_unknown = ignored if ignored is not None else []

    def note_unknown(key: str) -> None:
        if key not in seen_unknown:
            seen_unknown.append(key)

    # 1) ```json fenced block
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidate = m.group(1) if m else None
    if candidate:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and data.get("discipline"):
                for k in data:
                    if k not in FIELDS:
                        note_unknown(str(k))
                return {k: v for k, v in data.items() if k in FIELDS}
        except json.JSONDecodeError:
            pass
    # 2) key:value / key=value（一行可含多组；中文键用 \w 覆盖不到，单列字符类）
    out: dict = {}
    key_re = re.compile(r"([A-Za-z_\u4e00-\u9fff]{2,20})\s*[:=：]\s*([^\s:=：][^\n]*)")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        # 去掉 `/yi` 命令前缀（含其后可能紧跟的空白）
        line = re.sub(r"^/\s*yi\b[\s:：]*", "", line, flags=re.I)
        for km in key_re.finditer(line):
            key = km.group(1).strip()
            val = km.group(2).strip().strip('"').strip("'")
            canon = FIELD_ALIASES.get(key)
            if not canon:
                note_unknown(key)
                continue
            # 同一行多组时，值只需截到下一个键值对之前
            v = _coerce(canon, val)
            if v not in (None, ""):
                out[canon] = v
    return out


def _from_workflow_inputs(ignored: list[str] | None = None) -> dict:
    """只认 workflow 显式注入的 INPUT_* 环境变量。

    **不再回落到裸 `os.environ.get(f)`**：字段名（如 `mode`、`name`）
    与 runner 上某些环境变量同名时，会把无关的值当成求测输入——"表单没填却出盘"，
    且没有任何提示。workflow 里每加一个字段就在 env: 段显式注入一个。

    高级字段逃生舱：`INPUT_EXTRA` 是一个 JSON 对象字符串（report.yml 表单只有 6 个
    输入，4 个余量），键可为字段名或中文别名，解析后并入请求。
    合并顺序：extra 先铺底，显式注入的核心 INPUT_* 字段覆盖同名键。
    extra 里认不出的键记入 `ignored`（AI 照旧文档传 `way`/`activity` 时不会静默消失）。
    """
    out: dict = {}
    seen_unknown = ignored if ignored is not None else []

    raw_extra = os.environ.get("INPUT_EXTRA")
    if raw_extra:
        try:
            data = json.loads(raw_extra)
        except json.JSONDecodeError as exc:
            print(f"⚠️ INPUT_EXTRA 不是合法 JSON，已忽略（{exc}）", file=sys.stderr)
            data = None
        if isinstance(data, dict):
            for k, v in data.items():
                canon = FIELD_ALIASES.get(str(k).strip())
                if not canon:
                    if str(k).strip() not in seen_unknown:
                        seen_unknown.append(str(k).strip())
                    continue
                v2 = _coerce(canon, v)
                if v2 not in (None, ""):
                    out[canon] = v2

    for f in FIELDS:
        raw = os.environ.get(f"INPUT_{f.upper()}")
        if raw is None or raw == "":
            continue
        v = _coerce(f, raw)
        if v not in (None, ""):
            out[f] = v
    return out


def _allowed_associations() -> tuple[str, ...]:
    raw = os.environ.get("YI_ALLOW_ASSOCIATIONS", "")
    if raw.strip():
        return tuple(x.strip().upper() for x in raw.split(",") if x.strip())
    return DEFAULT_ALLOWED_ASSOCIATIONS


def _commenter_allowed(event: dict) -> tuple[bool, str]:
    """评论触发时校验评论者权限。返回 (是否放行, 说明)。"""
    comment = event.get("comment") or {}
    assoc = str(comment.get("author_association") or "").upper()
    login = str((comment.get("user") or {}).get("login") or "?")
    allowed = _allowed_associations()
    if assoc in allowed:
        return True, f"评论者 {login}（{assoc}）在允许名单内"
    return False, (f"评论者 {login} 的权限为 {assoc or '未知'}，不在允许名单 "
                   f"{'/'.join(allowed)} 内；如需放开请设 YI_ALLOW_ASSOCIATIONS")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="request.json")
    ap.add_argument("--meta", default="meta.json")
    args = ap.parse_args()

    event_name = os.environ.get("GITHUB_EVENT_NAME", "workflow_dispatch")
    event = {}
    ep = os.environ.get("GITHUB_EVENT_PATH")
    if ep and Path(ep).is_file():
        event = json.loads(Path(ep).read_text(encoding="utf-8"))

    req: dict = {}
    ignored: list[str] = []
    issue_number = None
    should_run = False
    comment_body = ""
    note = ""

    if event_name == "workflow_dispatch":
        req = _from_workflow_inputs(ignored)
        should_run = bool(req.get("discipline"))

    elif event_name == "repository_dispatch":
        payload = event.get("client_payload") or {}
        req = {k: v for k, v in payload.items() if k in FIELDS}
        # `token` 是 dispatch 签名校验用的凭证字段（见 report.yml 的 auth 步骤），
        # 不是求测输入，不计入"被忽略的键"。
        for k in payload:
            if k not in FIELDS and k != "token" and k not in ignored:
                ignored.append(str(k))
        should_run = bool(req.get("discipline"))

    elif event_name in ("issues", "issue_comment"):
        if event_name == "issues":
            issue = event.get("issue") or {}
            body = issue.get("body") or ""
            title = issue.get("title") or ""
            text = f"{title}\n{body}"
        else:
            issue = event.get("issue") or {}
            comment = event.get("comment") or {}
            body = comment.get("body") or ""
            text = body
            if not body.lstrip().lower().startswith("/yi"):
                text = ""  # 仅响应 /yi 命令
            if text:
                allowed, why = _commenter_allowed(event)
                if not allowed:
                    text = ""
                    note = why
        parsed = parse_kv_text(text, ignored)
        # issues 触发需有明确标记，避免对普通 issue 起卦
        titled = re.search(r"\[\s*yi\s*\]", text, re.I) is not None
        if event_name == "issues" and not titled and not parsed.get("discipline"):
            parsed = {}
        req = parsed
        issue_number = issue.get("number")
        should_run = bool(req.get("discipline")) and issue_number is not None

    # 默认名（保证 reports 分支/产物文件名稳定）
    req.setdefault("name", "report")

    commit_branch_env = os.environ.get("INPUT_COMMIT_BRANCH")
    if commit_branch_env is None:
        commit_branch_env = os.environ.get("COMMIT_BRANCH", "true")
    commit_branch = str(commit_branch_env).strip().lower() not in ("false", "0", "", "no")

    meta = {
        "should_run": should_run,
        "event_name": event_name,
        "issue_number": issue_number,
        "commit_branch": bool(commit_branch and should_run),
        "repo": os.environ.get("GITHUB_REPOSITORY", ""),
        "server_url": os.environ.get("GITHUB_SERVER_URL", "https://github.com"),
        "api_url": os.environ.get("GITHUB_API_URL", "https://api.github.com"),
        "run_id": os.environ.get("GITHUB_RUN_ID", ""),
        "sha": os.environ.get("GITHUB_SHA", ""),
        "report_name": req.get("name", "report"),
        "request_discipline": req.get("discipline", ""),
        "request": req,
        # 本通道不接受的键名（issue 正文混散文，不据此失败；但必须让它可见——
        # 静默吞掉求测者给的键，与旧缺陷"收下死字段却不转发"是同一类口径问题）
        "ignored_keys": ignored,
        "note": note,
    }
    if ignored:
        print("⚠️ 已忽略字段宇宙之外的键（不参与推演，报告也不会据此改变）："
              + "、".join(sorted(ignored)), file=sys.stderr)

    Path(args.out).write_text(json.dumps(req, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    Path(args.meta).write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    out_path = os.environ.get("GITHUB_OUTPUT")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"should_run={str(should_run).lower()}\n")
            f.write(f"has_issue={str(issue_number is not None).lower()}\n")
            f.write(f"commit_branch={str(meta['commit_branch']).lower()}\n")

    print(json.dumps({"should_run": should_run, "request": req, "meta": meta},
                     ensure_ascii=False))
    if not should_run:
        reason = note or "未识别到 discipline"
        print(f"本次触发无需出报告（{reason}），后续步骤将跳过。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
