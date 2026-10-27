# yan-plugin · Yi 术数的 Yan Agent 插件

把 [Yi](https://github.com/LinHoMo/Yi) 的两科术数引擎（六爻纳甲、八字四柱）包装成
**Yan Agent**（`ViaTumLab/Yan-Agent`，Windows 桌面 AI 工程工作区）的插件。
装了即用：模型直接调 `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report`，不需要 clone 仓库、
不需要手敲 python（但仍需本机有 Python 3.10+，引擎是 Python）。

> 口径提醒（AGENTS.md §一.3 铁律三）：本插件一切分数都是**古籍案例对齐分**（回归审计用），
> **不是现实命中率**——现实侧样本为零。它是排盘与推演参考工具，不是预言；
> 重大决策以专业意见为准。

## 它提供什么

| 层 | Yan 机制 | 落点 |
|---|---|---|
| 工具 | `yan-plugin.json` → `mcpServers`（本地 stdio MCP） | `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report` |
| 技能 | `skills[]` → `plugins_read_resource` 读 `skill:yi-divination` | `skills/yi-divination/SKILL.md` |
| 知识库 | `resources[]` → `plugins_read_resource` 读 `resource:kb-*` | 9 篇判据文档 + INDEX（共 10 条资源） |
| 入口说明 | `instructions` | `INSTRUCTIONS.md`（激活后自动注入） |

**没有**的东西（刻意）：古籍案例库（`case_library.md`）按 AGENTS.md §一.2 铁律二
**永不随包**——打包层、扫描层、自检层三道闸各排除一次。

## 安装

### A. 从文件夹安装（推荐，构建产物不入库所以必须本地构建一次）

```bash
# 1) 在本仓库里构建 engine/ 与 skills/（两者都是构建产物，不在 git 里）
node plugins/scripts/build.mjs

# 2) Yan → 插件页 → 添加插件 → 选择本目录 <仓库>/yan-plugin
#    Yan 会读 yan-plugin.json，校验后复制整个目录进插件存储
```

### B. 作为本地插件市场添加（同一份目录，走市场通道）

在 Yan 的插件市场里添加来源时填**本地路径** `<仓库>/yan-plugin`（Yan 支持本地目录作为
市场来源，`lib/plugins/marketplaces.js` 的 `add({source})` 会 `git`/目录两路自适应）。

> 为什么没有「GitHub 仓库直装」这一条：Yan 的远程市场是 **git 稀疏克隆**，
> 只会拿到**已提交**的文件，而 `engine/` 与 `skills/` 按仓库纪律不入库。
> 真要开远程通道，需要一条只放构建产物的发行分支（如 `yan-plugin-dist`），
> 本批未开——见 CHANGELOG「未做的事」。

### C. 先自检再装

```bash
npm --prefix yan-plugin run check     # plugins 构建 → 共享自检（7 段，含负例自证）
```

## 结构

```
yan-plugin/
├── yan-plugin.json        # 清单（入库；Yan 的 schemaVersion 1 规范）
├── INSTRUCTIONS.md        # 激活后注入模型的入口说明（入库）
├── README.md / CHANGELOG.md / LICENSE
├── src/                   # 由 plugins/scripts/build.mjs 分发的共享运行时（**产物**，手工改即判红）
│   │                      #   真源在 ../../plugins/mcp/，各宿主共用同一份
│   ├── server.mjs         # JSON-RPC 2025-03-26，换行分隔，零依赖
│   ├── schema.mjs         # dsh 简写参数 → MCP JSON Schema（唯一一处方言转译）
│   ├── tools.mjs          # 工具定义与 run（1.0 冻结契约）
│   ├── engine.mjs         # 引擎调用层（子进程跑打包的 Python 引擎）
│   ├── python.mjs         # 解释器定位（YI_PYTHON → python → python3 → py）
│   ├── kb.mjs             # 判据检索，输出带 resource 句柄
│   ├── report.mjs         # 报告落盘
│   └── kb-synonyms.json
├── engine/                # 构建产物（不入库）
└── skills/                # 构建产物（不入库）

构建与自检都在共享层：node plugins/scripts/build.mjs、node plugins/scripts/selftest.mjs
（或 npm --prefix yan-plugin run check）。
```

## 与 dsh-plugin 的关系

两个宿主插件**共用同一份工具契约**（`yi_liuyao`/`yi_bazi`/`yi_kb`/`yi_report`
的工具名、参数集、输出 value 结构——1.0 冻结面，见 `dsh-plugin/CHANGELOG.md` 277 批）：

- `src/tools.mjs`、`src/engine.mjs`、`src/kb.mjs`、`src/report.mjs` 从 dsh-plugin 逐字复用，
  只有 `python.mjs`（宿主没有自带 Python 运行时）与 `server.mjs`/`schema.mjs`（宿主方言）
  是 Yan 侧新增；
- 技能正文的真源是 `plugins/SKILL.md`，构建期只**追加**一段「Yan 侧读法」；
- 共享运行时与登记表都只有一份（`plugins/mcp/`、`plugins/scripts/kb-docs.mjs`），
  305 批起不再需要「两侧对拍」这种补丁式防漂移门。

两科自身仍是唯一真源：`engine/` 与 `skills/` 都是现场收集的产物，改两科后
**必须重跑 `npm --prefix yan-plugin run check`**，否则包里的引擎会过期。

## 自检覆盖了什么

305 批起，自检统一在共享层：`node plugins/scripts/selftest.mjs`（7 段，判红即 exit≠0）。
本适配器**只保留宿主专属的两项断言**：`yan-plugin.json` 是否符合 Yan 的
`schemaVersion: 1` 规范（id/semver/`$node`/超时上限/路径在位）、
以及 `resources[]` 与实收知识库的**双向对账**（`resource:kb-*` 句柄必须同式）。
其余——分发一致性、案例库零随包、引擎入口、技能正文同源、MCP 真机冒烟、
工具契约、包体预算、禁语扫描——都在共享层跑一次，覆盖所有宿主。

## 已知边界

- **需要 Python**：Yan 是 Electron 应用，不自带 Python 运行时（这是它与 DSH 桌面的差异）。
  找不到解释器时工具如实报错并列出尝试过的路径，不在插件里做任何降级。
- **工具名会被宿主改写**：Yan 把插件工具重命名为 `t_<sha1前20位>`，描述前缀里带原名，
  模型按描述认名字即可（INSTRUCTIONS.md 与 SKILL.md 都写明了这点）。
- **包资源不在工作区**：模型要用 `plugins_read_resource` 读知识库，`read` 读不到。
- 完全离线：零网络请求、零凭据读取；报告只写系统临时目录，不写用户工作区。
