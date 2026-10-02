# -*- coding: utf-8 -*-
"""把生成的报告回写到触发 issue/评论 下（GitHub REST，stdlib urllib）。

评论含：reports 分支上可匿名读取的 MD/HTML raw 链接、本 run 的 artifact 页面，
以及折叠内联的报告正文。令牌取 GITHUB_TOKEN/GH_TOKEN。

  python tools/ci_deliver.py --meta meta.json --outdir out
  python tools/ci_deliver.py --meta meta.json --outdir out --dry-run
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

_CORE = Path(__file__).resolve().parents[1] / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))
from yishu_core.report.request import FOOTER_TEXT  # noqa: E402  口径句唯一真值源

DISC_TITLE = {
    "liuyao": "六爻纳甲", "ming": "四柱八字", "ziwei": "紫微斗数",
    "meihua": "梅花易数", "xiaoliuren": "小六壬", "zeji": "择吉",
}
COMMENT_LIMIT = 65536
INLINE_MAX = 48000


def build_comment(meta: dict, outdir: Path) -> str:
    name = meta.get("report_name", "report")
    md_text = ""
    md_file = outdir / f"{name}.md"
    if md_file.is_file():
        md_text = md_file.read_text(encoding="utf-8")
        if len(md_text) > INLINE_MAX:
            md_text = md_text[:INLINE_MAX] + "\n\n…（正文较长，已截断，完整内容见 MD 链接/Artifact）"

    repo, run_id = meta["repo"], meta["run_id"]
    server = meta.get("server_url", "https://github.com")
    run_page = f"{server}/{repo}/actions/runs/{run_id}"
    disc = meta.get("request_discipline", "")
    heading = "Yi 报告已生成"
    if disc:
        heading += f" · {DISC_TITLE.get(disc, disc)}"

    links = []
    if meta.get("latest_md_url"):
        links.append(f"- **固定链接（本科最近一次，可直接给网页 AI 读）**：{meta['latest_md_url']}")
    if meta.get("latest_html_url"):
        links.append(f"- 固定链接 HTML：{meta['latest_html_url']}")
    if meta.get("md_url"):
        links.append(f"- 本次留档 Markdown：{meta['md_url']}")
    if meta.get("html_url"):
        links.append(f"- 本次留档 HTML（下载后用浏览器打开）：{meta['html_url']}")
    if meta.get("index_url"):
        links.append(f"- 各科最近报告索引：{meta['index_url']}")
    links.append(f"- Artifact（含 MD+HTML，下载需登录）：{run_page}")
    if not meta.get("md_url"):
        links.append("\n> 未启用 reports 分支时，请在上面的 run 页面下载 Artifact。")

    return (
        f"## {heading}\n\n"
        + "\n".join(links)
        + "\n\n<details><summary>报告正文（Markdown）</summary>\n\n"
        + md_text
        + "\n\n</details>\n\n"
        "---\n"
        + FOOTER_TEXT + "\n"
        "> 想在本机/离线出报告、或不想用 GitHub 账号，可用同一份引擎的纯前端页面"
        "（浏览器内 Pyodide 运行，无需凭证），见仓库 `web/` 与 `docs/AI-SOP.md` §2。\n"
        "> 结果如何？欢迎在本 issue 下回复实际进展——反馈进入应期/效度统计"
        "（也可用 `synthesis record-outcome` 回填）。\n"
    )


def post(api_url: str, repo: str, issue: int, token: str, body: str) -> None:
    url = f"{api_url}/repos/{repo}/issues/{issue}/comments"
    data = json.dumps({"body": body}).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    with urllib.request.urlopen(req) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"回评失败：HTTP {resp.status}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta", default="meta.json")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
    issue = meta.get("issue_number")
    if not meta.get("should_run") or not issue:
        print("非 issue 触发或无需回评，跳过。")
        return 0

    body = build_comment(meta, Path(args.outdir))
    if len(body) > COMMENT_LIMIT:
        # 极端情况下进一步压缩内联正文
        body = build_comment({**meta}, Path(args.outdir))

    if args.dry_run:
        out = Path(args.outdir) / "comment.dryrun.md"
        out.write_text(body, encoding="utf-8")
        api = meta.get("api_url", "https://api.github.com")
        print(f"[dry-run] POST {api}/repos/{meta['repo']}/issues/{issue}/comments")
        print(f"[dry-run] 评论长度 {len(body)}，已写出 {out}")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    if not token:
        raise RuntimeError("缺少 GITHUB_TOKEN，无法回评")
    post(meta.get("api_url", "https://api.github.com"), meta["repo"], issue,
         token, body)
    print(f"已回写 issue #{issue} 评论。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
