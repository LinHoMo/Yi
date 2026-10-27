# claude-plugin · Yi 术数的 Claude Code 插件

把 [Yi](https://github.com/LinHoMo/Yi) 的两科术数引擎（六爻纳甲、八字四柱）包装成
**Claude Code 插件**。装了即用：模型直接调 `yi_liuyao` / `yi_bazi` / `yi_kb` /
`yi_report`，不需要 clone 仓库、不需要手敲 python（但本机要有 **Python 3.10+**，引擎是 Python）。

> 口径提醒（AGENTS.md §一.3 铁律三）：本插件一切分数都是**古籍案例对齐分**（回归审计用），
> **不是现实命中率**。它是排盘与推演参考工具，不是预言；重大决策以专业意见为准。

## 它提供什么

| 层 | Claude Code 机制 | 落点 |
|---|---|---|
| 工具 | 插件根的 `.mcp.json`（本地 stdio MCP） | `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report`（会话里带 `mcp__yi__` 前缀） |
| 技能 | 插件根的 `skills/<name>/SKILL.md`，按插件名做命名空间 | `skills/yi-divination/SKILL.md` |
| 知识库 | 同上目录的 `references/`（9 篇判据文档 + INDEX） | `skills/yi-divination/references/` |

**没有**的东西（刻意）：古籍案例库 `case_library.md` 按 AGENTS.md §一.2 铁律二
**永不随包**——打包层、扫描层、自检层三道闸各排除一次。

## 安装

### A. 本地试装（推荐先走这条）

```bash
# 1) 构建 engine/ 与 skills/（产物，不在 git 里）
node plugins/scripts/build.mjs

# 2) 试装
claude --plugin-dir ./claude-plugin
```

### B. 从市场装（309 批真机验证通过）

```bash
/plugin marketplace add LinHoMo/yi-plugins
/plugin install yi@yi-plugins
```

发行链：源仓 `LinHoMo/Yi`（产物不入库）→ `plugins/scripts/publish.mjs` 生成发行树
→ 市场仓 `LinHoMo/yi-plugins` ＋ **独立的 Claude 插件仓 `LinHoMo/yi-claude`**。

> ⚠ 为什么 Claude 要单独一个仓：官方 `marketplace.json` 的插件条目**没有子目录字段**
> （写 `path` 会被静默忽略），市场仓必须指向「根就是插件」的独立仓库。
> 309 批前把条目指向同仓子目录，装出来是 Skills 0 / MCP 0 的**空壳**——已改为独立仓。

### C. 自检

```bash
node plugins/scripts/selftest.mjs     # 共享层 7 段，含本适配器的清单/.mcp.json 断言
```

## 结构

```
claude-plugin/
├── .claude-plugin/plugin.json   # 清单（入库；**只有清单能放这个目录里**）
├── .mcp.json                    # MCP 服务声明（入库，用 ${CLAUDE_PLUGIN_ROOT}）
├── README.md / CHANGELOG.md / LICENSE
├── src/                         # 构建产物：由 plugins/scripts/build.mjs 从 plugins/mcp/ 分发
├── skills/                      # 构建产物
└── engine/                      # 构建产物
```

共享运行时、技能正文真源、知识库登记表都在 `plugins/`（唯一一份），
本目录**不复制第二份**——手工改 `src/` 会被共享自检 [1] 段（逐字节同源门）判红。

## 已知边界

- **需要 Python**：找不到解释器时工具如实报错并列出尝试过的路径；
  Windows 上微软商店的「应用执行别名」`python.exe` 是空壳，探活门会自动跳过它并说明原因。
  实在不行就在 `.mcp.json` 的 `env.YI_PYTHON` 填真正的 python.exe 绝对路径。
- **需要 node**：MCP 入口是 node 脚本（Claude Code 用户一般都有）。
- 完全离线：零网络请求、零凭据读取；报告只写系统临时目录，不写工作区。
- **未做真机验证**：本机没有 Claude Code，协议与清单面是复刻其官方约束的断言，
  首次安装请按上面的 A 走一遍并回填 CHANGELOG。
