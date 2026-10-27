# codex-plugin · Yi 术数的 Codex 插件

把 [Yi](https://github.com/LinHoMo/Yi) 的两科术数引擎（六爻纳甲、八字四柱）包装成
**OpenAI Codex CLI 插件**（`.codex-plugin/plugin.json`）。装了即用：模型直接调
`yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report`（会话里带 `mcp__yi__` 前缀）。
本机需有 **Python 3.10+**（引擎是 Python）与 node（MCP 入口）。

> 口径提醒：一切分数都是**古籍案例对齐分**，不是现实命中率。它是排盘与推演参考工具，
> 不是预言；重大决策以专业意见为准。

## 结构

```
codex-plugin/
├── .codex-plugin/plugin.json   # 清单（入库；**只有清单能放这个目录里**）
├── .mcp.json                   # MCP 声明（入库，用 ${CODEX_PLUGIN_ROOT}）
├── README.md / CHANGELOG.md / LICENSE
├── skills/                     # 构建产物
├── src/  engine/               # 构建产物（由 plugins/scripts/build.mjs 分发）
```

共享运行时、技能正文真源、知识库登记表都在 `plugins/`（唯一一份），本目录不复制第二份。

## 安装

```bash
node plugins/scripts/build.mjs          # 先构建（产物不在 git 里）
codex plugins install ./codex-plugin    # 本地安装
```

或走仓库级市场：在 `$REPO_ROOT/.agents/plugins/marketplace.json` 里登记
`{ "name": "yi", "source": { "source": "local", "path": "./codex-plugin" } }`。

> Codex 的**第三方公开目录尚未开放**，因此不能进官方目录；repo 级与用户级
> （`~/.agents/plugins/marketplace.json`）市场现在就能用。
> 另：远程 git 市场同样拿不到不入库的 `engine/`、`skills/`、`src/`——
> 与 Claude/Yan 是同一个限制，见 `plugins/CHANGELOG.md`。

## 已知边界

- **未在真机 Codex 里安装验证**（本机无该宿主）；断言是复刻其官方清单约束的机械检查。
- 需要 Python；找不到时工具如实报错并列出尝试过的路径（会跳过微软商店的空壳别名）。
- 完全离线：零网络请求、零凭据读取；报告只写系统临时目录。
