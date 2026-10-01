# -*- coding: utf-8 -*-
"""把各类 GitHub 触发统一解析成 report.py 需要的 request.json + meta.json。

支持触发（GITHUB_EVENT_NAME）：
  workflow_dispatch  从 INPUT_* 风格环境变量取表单（workflow 里显式注入）
  repository_dispatch  client_payload 即请求体（event.client_payload）
  issues(opened/edited)   解析 issue 标题/正文（JSON 代码块 或 key:value）
  issue_comment(created)  解析评论正文（须以 /yi 开头）

解析出的请求字段：discipline/question/datetime/gender/mode/way/numbers/date/
activity/hour_branch/longitude/name。同时：
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

FIELD_ALIASES = {
    "discipline": "discipline", "学科": "discipline",
    "question": "question", "问题": "question", "占问": "question",
    "datetime": "datetime", "时间": "datetime", "出生": "datetime",
    "出生时间": "datetime",
    "gender": "gender", "性别": "gender",
    "mode": "mode", "模式": "mode",
    "way": "way", "方式": "way", "起课方式": "way",
    "numbers": "numbers", "数字": "numbers",
    "yao": "yao", "爻值": "yao",
    "date": "date", "日期": "date",
    "activity": "activity", "事类": "activity", "活动": "activity",
    "hour_branch": "hour_branch", "时支": "hour_branch",
    "direction": "direction", "方位": "direction",
    "longitude": "longitude", "经度": "longitude",
    "name": "name", "名字": "name",
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


def parse_kv_text(text: str) -> dict:
    """解析 JSON 代码块 或 'key: value' / 'key=value' 行（含中文键别名）。

    兼容三种写法（issue 正文、issue 正文里的 `/yi` 命令行）：
        discipline: liuyao
        /yi discipline: liuyao
        /yi discipline=liuyao question=占求财     ← 同一行多个键值对
    历史缺陷：旧正则要求键紧跟在（去掉行首 `/` 之后的）行首，于是
    `/yi discipline: ming` 里的 `discipline` 前面还有 `yi ` 就整行不匹配，
    命令行的 key:value 会被**静默丢弃**（触发成功但请求为空）。
    """
    text = text.strip()
    # 1) ```json fenced block
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    candidate = m.group(1) if m else None
    if candidate:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict) and data.get("discipline"):
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
                continue
            # 同一行多组时，值只需截到下一个键值对之前
            v = _coerce(canon, val)
            if v not in (None, ""):
                out[canon] = v
    return out


def _from_workflow_inputs() -> dict:
    """只认 workflow 显式注入的 INPUT_* 环境变量。

    **不再回落到裸 `os.environ.get(f)`**：字段名（如 `mode`、`date`、`name`）
    与 runner 上某些环境变量同名时，会把无关的值当成求测输入——"表单没填却出盘"，
    且没有任何提示。workflow 里每加一个字段就在 env: 段显式注入一个。

    高级字段逃生舱：`INPUT_EXTRA` 是一个 JSON 对象字符串（report.yml 表单只有 6 个
    输入，4 个余量），键可为字段名或中文别名，解析后并入请求。
    合并顺序：extra 先铺底，显式注入的核心 INPUT_* 字段覆盖同名键。
    """
    out: dict = {}

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
    issue_number = None
    should_run = False
    comment_body = ""
    note = ""

    if event_name == "workflow_dispatch":
        req = _from_workflow_inputs()
        should_run = bool(req.get("discipline"))

    elif event_name == "repository_dispatch":
        payload = event.get("client_payload") or {}
        req = {k: v for k, v in payload.items() if k in FIELDS}
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
        parsed = parse_kv_text(text)
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
        "note": note,
    }

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
