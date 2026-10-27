# plugins · Yi 的共享打包层

两科（六爻 / 八字）对外分发的**唯一共享层**。五个宿主适配器（`dsh-plugin/`、`claude-plugin/`、
`codex-plugin/`、`gemini-plugin/`、`yan-plugin/`）只保留宿主专属文件，
共享的运行时、技能正文、构建与自检都在本目录。

> 305 批前是「每个宿主一套 build + 一份 `src/*.mjs` 副本 + 一份知识库登记表」，
> 再接三家就是五份产物、五条漂移面。本目录即为此而立，契约见 `AGENTS.md` §二。

```
plugins/
├── SKILL.md             # 技能正文唯一真源（入库）
├── mcp/                 # 共享运行时唯一真源（入库）
│   ├── server.mjs       # 零依赖 stdio MCP 服务（JSON-RPC 2025-03-26，换行分隔）
│   ├── schema.mjs       # dsh 简写参数 → MCP JSON Schema（唯一一处方言转译）
│   ├── tools.mjs        # 四工具定义与 run（1.0 冻结契约）
│   ├── engine.mjs       # 引擎调用层：子进程跑打包的 Python 引擎
│   ├── python.mjs       # 解释器定位（DSH_PYTHON → YI_PYTHON → DSH 自带 → PATH → py）
│   ├── kb.mjs           # 判据检索（输出带 resource 句柄，供 Yan 侧读取）
│   ├── report.mjs       # 报告落盘
│   └── kb-synonyms.json
├── scripts/
│   ├── kb-docs.mjs      # 知识库登记表唯一真源
│   ├── build.mjs        # 一次构建 + 分发到各适配器
│   └── selftest.mjs     # 7 段自检（判红即 exit≠0）
├── engine/  skills/     # 构建产物（不入库）
└── CHANGELOG.md
```

## 当前宿主

| id | 目录 | 宿主专属文件（其余全是构建产物） |
|---|---|---|
| dsh | `dsh-plugin/` | `package.json`、`src/index.mjs`、`presets/` |
| claude | `claude-plugin/` | `.claude-plugin/plugin.json`、`.mcp.json` |
| codex | `codex-plugin/` | `.codex-plugin/plugin.json`、`.mcp.json` |
| gemini | `gemini-plugin/` | `gemini-extension.json`、`GEMINI.md` |
| yan | `yan-plugin/` | `yan-plugin.json`、`INSTRUCTIONS.md` |

## 常用命令

```bash
node plugins/scripts/build.mjs                 # 一次构建 + 分发到 ADAPTERS 登记表里的所有宿主
node plugins/scripts/build.mjs --only yan      # 只分发一个宿主（调试用）
node plugins/scripts/selftest.mjs              # 共享层 7 段自检
npm --prefix dsh-plugin run check              # 宿主侧：build → dsh 13 段 → verify-in-dsh
npm --prefix yan-plugin run check              # 宿主侧：build → 共享 7 段
```

改两科（`*/core`、`*/scripts`、`*/references`）之后**必须**重跑构建与自检：
`engine/` 与 `skills/` 会静默过期，这是唯一能在提交前抓到漂移的门。

## 发布（远程分发的解法）

`engine/`、`skills/`、`src/` 不入库，而四家远程通道都走 git（只拿已提交文件）——
所以发布靠一棵**独立的发行树**：

```bash
node plugins/scripts/publish.mjs           # 生成 plugins/dist/（五家各自的完整可安装目录）
node plugins/scripts/publish.mjs --check   # 只校验：入口齐备 / 零案例库 / 知识库篇数（含负例自证）
```

产物 ≈15MB（五份引擎副本；但内容相同的文件在 git 里只存一份 blob，进仓远小于此）。
把 `plugins/dist/` 推成一个独立发行仓（推荐）或同仓发行分支，各家即可远程装：

| 宿主 | 远程 |
|---|---|
| Claude Code | `/plugin marketplace add LinHoMo/yi-plugins` → `/plugin install yi`（**未真机验证**，见下） |
| Codex | 仓库根 `.agents/plugins/marketplace.json` 已生成，登记后即可装 |
| Gemini CLI | `gemini extensions install https://github.com/LinHoMo/yi-plugins`（仓库根本身即扩展，入口指进 `gemini-plugin/`） |
| Yan Agent | 市场添加来源 `https://github.com/LinHoMo/yi-plugins`，稀疏路径填 `yan-plugin` |
| DSH | 不走 git；用 npm 包或 `dsh plugin add` |

> ⚠ Claude 的 `marketplace.json` 把插件指向**同仓子目录**，而官方示例是
> 「市场仓 → 独立插件仓」——这条**未真机验证**，未跑通前请用
> `claude --plugin-dir ./claude-plugin` 本地试装。脚本只生成文件，不 commit、不 push。


## 新增一个宿主要做什么

1. 建适配器目录，只放宿主专属文件（清单、宿主入口、README/CHANGELOG/LICENSE）；
2. 在 `scripts/build.mjs` 的 `ADAPTERS` 里加一条（`dir` + 是否需要技能附加段）；
3. 若宿主有清单规范断言，在 `scripts/selftest.mjs` [6] 段按现成两家的写法加一组；
4. 在 `AGENTS.md` §二的「各宿主的硬约束」表里补一行，并登记批次。

共享运行时、技能正文、知识库登记表**都不用再写一遍**——那份是唯一的。
