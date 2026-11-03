# plugins · Yi 的共享打包层

两科（六爻 / 八字）对外分发的**唯一共享层**。DSH 适配器（`dsh-plugin/`）只保留
宿主专属文件，共享的运行时、技能正文、构建与自检都在本目录。

> 497 批起只保留 DSH 一个宿主（claude/codex/gemini/yan 四家适配器已删除）。
> 契约见 `AGENTS.md` §二。

```
plugins/
├── SKILL.md             # 技能正文唯一真源（入库）
├── mcp/                 # 共享运行时唯一真源（入库）
│   ├── server.mjs       # 零依赖 stdio MCP 服务（JSON-RPC 2025-03-26，换行分隔）
│   ├── schema.mjs       # dsh 简写参数 → MCP JSON Schema（唯一一处方言转译）
│   ├── tools.mjs        # 四工具定义与 run（1.0 冻结契约）
│   ├── engine.mjs       # 引擎调用层：子进程跑打包的 Python 引擎
│   ├── python.mjs       # 解释器定位（DSH_PYTHON → DSH 自带 → PATH → py）
│   ├── kb.mjs           # 判据检索（输出 resource 句柄）
│   ├── report.mjs       # 报告落盘
│   └── kb-synonyms.json
├── scripts/
│   ├── kb-docs.mjs      # 知识库登记表唯一真源
│   ├── build.mjs        # 一次构建 + 分发到 dsh-plugin/
│   └── selftest.mjs     # 共享层自检（判红即 exit≠0）
├── engine/  skills/     # 构建产物（不入库）
└── CHANGELOG.md
```

## 当前宿主

| id | 目录 | 宿主专属文件（其余全是构建产物） |
|---|---|---|
| dsh | `dsh-plugin/` | `package.json`、`src/index.mjs`、`presets/` |

## 常用命令

```bash
node plugins/scripts/build.mjs       # 一次构建 + 分发到 dsh-plugin/
node plugins/scripts/selftest.mjs     # 共享层自检
npm --prefix dsh-plugin run check     # 宿主侧：build → dsh 内验证 → verify-in-dsh
```

改两科（`*/core`、`*/scripts`、`*/references`）之后**必须**重跑构建与自检：
`engine/` 与 `skills/` 会静默过期，这是唯一能在提交前抓到漂移的门。

## 发布

`engine/`、`skills/`、`src/` 不入库；DSH 发布走 GitHub Release 的 npm tgz
（`npm pack`，见 `dsh-plugin/README.md`），不再有独立发行树。
