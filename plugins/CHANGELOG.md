# plugins CHANGELOG

> 本卷登记**共享打包层**（`plugins/`）的批次；批次号沿用全仓流水。
> 305 批起，各宿主适配器（`dsh-plugin/`、`yan-plugin/`）自身只留宿主专属文件，
> 共享的运行时、技能正文、构建与自检都归本目录，各宿主卷只记「宿主侧那点事」。

## 2026-10-27 第三百零七批（plugins）：发布树建成——远程分发的结构性解法落地

**问题不是"没写安装文档"，是结构上互斥**：`engine/`、`skills/`、`src/` 按仓库纪律
不入库，而 Claude Code / Codex / Gemini CLI / Yan 的远程分发**全部走 git**（只拿已提交
文件）。于是 304～306 批四家都只能本地安装。改文档解决不了，得改结构。

**解法：源与发行分离。** 新增 `plugins/scripts/publish.mjs`，产出一棵只含可安装产物的
发行树 `plugins/dist/`（不入库），由它单独成为 git 仓/分支被各家拉取；
源仓继续维持"产物不入库"的纪律，两不相犯。

- `publish.mjs`（默认）：把五家适配器的**完整目录**（清单 + `engine/` + `skills/` +
  `src/` + README/CHANGELOG/LICENSE）复制到 `dist/`，并生成三份宿主入口文件：
  - `.claude-plugin/marketplace.json`（Claude 市场目录）
  - `.agents/plugins/marketplace.json`（Codex 仓库级市场，`source: local`）
  - 仓库根 `gemini-extension.json` + `GEMINI.md`——**Gemini 一个仓库 = 一个扩展**，
    没法像 Claude/Codex 那样用市场目录，故把仓库根本身做成扩展、入口指进
    `gemini-plugin/`。这是四家里唯一的结构性差异，已在文件与 README 写明。
  - Yan 不需要目录文件（它遍历树找 `yan-plugin.json`），DSH 不走 git。
- `publish.mjs --check`：发布树**可安装性**检查——五家各自"清单 + MCP 入口 +
  `engine/MANIFEST.json` + `skills/yi-divination/SKILL.md` + 引擎入口脚本"齐备、
  零 `case_library.md`、知识库篇数与登记表一致，**含负例自证**（多塞一个缺失入口即被抓到）。
- 脚本**只生成文件，不 commit、不 push、不建远程**——外部动作留给用户，
  末尾打印两条确切命令（独立发行仓 / 同仓发行分支）。
- `.gitignore` 加 `plugins/dist/`；根 README 与各宿主 README 的"只能本地安装"表述
  改为指向发布流程。

**实跑**：`build` rc=0 → `publish` rc=0 → 内置 `--check` 全绿（5 家自包含 + 负例自证 +
零案例库 + 知识库 9 篇）；`selftest` rc=0。产物 ≈15MB（五份引擎副本，
但相同内容在 git 里只存一份 blob，进仓远小于此）。

### 未做的事（如实）

- **没有真的发布**：脚本不 push，本批也未建发行仓/分支——那是你的外部动作。
- **Claude 的 marketplace.json 未真机验证**：官方示例是「市场仓 → 独立插件仓」，
  这里改指**同仓子目录**，能否被 Claude 接受未测。文件里写了 `_note` 提示，
  README 也标了；未跑通前请用 `claude --plugin-dir ./claude-plugin` 本地试装。
- Codex 第三方公开目录仍未开放，即便有发行树也进不了官方目录（只能 repo/用户级市场）。
- 五家宿主**全部未做真机安装验证**（本机无任何一家宿主）。

## 2026-10-27 第三百零七批（plugins）：发布树建成——远程分发的结构性解法落地

**问题不是"没写安装文档"，是结构上互斥**：`engine/`、`skills/`、`src/` 按仓库纪律
不入库，而 Claude Code / Codex / Gemini CLI / Yan 的远程分发**全部走 git**（只拿已提交
文件）。于是 304～306 批四家都只能本地安装。改文档解决不了，得改结构。

**解法：源与发行分离。** 新增 `plugins/scripts/publish.mjs`，产出一棵只含可安装产物的
发行树 `plugins/dist/`（不入库），由它单独成为 git 仓/分支被各家拉取；
源仓继续维持"产物不入库"的纪律，两不相犯。

- `publish.mjs`（默认）：把五家适配器的**完整目录**（清单 + `engine/` + `skills/` +
  `src/` + README/CHANGELOG/LICENSE）复制到 `dist/`，并生成三份宿主入口文件：
  - `.claude-plugin/marketplace.json`（Claude 市场目录）
  - `.agents/plugins/marketplace.json`（Codex 仓库级市场，`source: local`）
  - 仓库根 `gemini-extension.json` + `GEMINI.md`——**Gemini 一个仓库 = 一个扩展**，
    没法像 Claude/Codex 那样用市场目录，故把仓库根本身做成扩展、入口指进
    `gemini-plugin/`。这是四家里唯一的结构性差异，已在文件与 README 写明。
  - Yan 不需要目录文件（它遍历树找 `yan-plugin.json`），DSH 不走 git。
- `publish.mjs --check`：发布树**可安装性**检查——五家各自"清单 + MCP 入口 +
  `engine/MANIFEST.json` + `skills/yi-divination/SKILL.md` + 引擎入口脚本"齐备、
  零 `case_library.md`、知识库篇数与登记表一致，**含负例自证**（多塞一个缺失入口即被抓到）。
- 脚本**只生成文件，不 commit、不 push、不建远程**——外部动作留给用户，
  末尾打印两条确切命令（独立发行仓 / 同仓发行分支）。
- `.gitignore` 加 `plugins/dist/`；根 README 与各宿主 README 的"只能本地安装"表述
  改为指向发布流程。

**实跑**：`build` rc=0 → `publish` rc=0 → 内置 `--check` 全绿（5 家自包含 + 负例自证 +
零案例库 + 知识库 9 篇）；`selftest` rc=0。产物 ≈15MB（五份引擎副本，
但相同内容在 git 里只存一份 blob，进仓远小于此）。

### 未做的事（如实）

- **没有真的发布**：脚本不 push，本批也未建发行仓/分支——那是你的外部动作。
- **Claude 的 marketplace.json 未真机验证**：官方示例是「市场仓 → 独立插件仓」，
  这里改指**同仓子目录**，能否被 Claude 接受未测。文件里写了 `_note` 提示，
  README 也标了；未跑通前请用 `claude --plugin-dir ./claude-plugin` 本地试装。
- Codex 第三方公开目录仍未开放，即便有发行树也进不了官方目录（只能 repo/用户级市场）。
- 五家宿主**全部未做真机安装验证**（本机无任何一家宿主）。

## 2026-10-27 第三百零六批（plugins）：三家新宿主接入（Claude Code / Codex / Gemini）＋ Python 解释器探活

**这是 305 批「一次构建 + N 份清单」的第一次实战检验**：接三个新宿主，
每个只新增 **2 个宿主专属文件**（清单 + MCP 声明；Gemini 是清单 + 上下文文件），
共享运行时、技能正文真源、知识库登记表**一行没复制**。

- 新增适配器：`claude-plugin/`（`.claude-plugin/plugin.json` + `.mcp.json`）、
  `codex-plugin/`（`.codex-plugin/plugin.json` + `.mcp.json`）、
  `gemini-plugin/`（`gemini-extension.json` + `GEMINI.md`）。
  三家的 MCP 入口都用宿主变量 `${CLAUDE_PLUGIN_ROOT}` / `${CODEX_PLUGIN_ROOT}` /
  `${extensionPath}`——**写死绝对路径换台机器就指不到包内入口**，
  自检 [6] 段各自断言 + 替换负例自证。
- **自检 [6] 段改为按宿主分流**（`MANIFEST_RULES` / `MCP_SPEC` 两张表）。
  原因：306 批首跑时这块只按「有没有 manifest」分两类，把 Claude 也套进 Yan 的
  `resources` 对账里，一口气报了 12 条红——**那是断言写宽，不是真的缺陷**。
  现在 Yan 的 `resources` 对账由 `reconcileResources` 显式开门，其余宿主各走各的规则。
- **共享层补强（影响全部宿主）**：`python.mjs` 增加**探活**。
  Windows 上 PATH 里的 `python` 常是微软商店的「应用执行别名」空壳（0 字节占位，
  `existsSync` 为真、spawn 只会弹商店）；306 批前只判存在，
  于是"装了 Python"的机器上第一次起卦就崩在一个打不开的解释器上。
  现在每个候选都要 `-c` 探针跑通才算数，被跳过的会列进报错信息；
  显式覆盖变量（`DSH_PYTHON`/`YI_PYTHON`）指了但跑不起来则**直接报错，不悄悄回退**。
- 各宿主卷各自登记 306 批（见 `claude-plugin/`、`codex-plugin/`、`gemini-plugin/` 的 CHANGELOG）。

**实跑**：`build` rc=0（一次构建分发到 **dsh / claude / codex / gemini / yan 五家**）；
`selftest` **全绿 rc=0**。

### 未做的事（如实）

- **三家都没做真机安装验证**（本机无 Claude Code / Codex / Gemini 宿主）。
  清单与协议面都是复刻各家官方约束的机械断言，**复刻≠放行**；
  首次安装请按各 README 走一遍并回填对应 CHANGELOG。
- **分发方案仍未定**：`engine/`、`skills/`、`src/` 不入库，而 Claude/Codex/Gemini 的
  远程通道都要已提交文件 → 三家目前都只能本地安装。
  解法未变：开 `plugins-dist` 发行分支，或走 Release tarball 后本地装。
- Codex 的**第三方公开目录尚未开放**，即便产物能提交也进不了官方目录，
  只能走 repo/用户级 marketplace.json。

## 2026-10-27 第三百零五批（plugins）：共享打包层建成——从「N 个宿主 N 套 build」收敛为「一次构建 + N 份清单」

**动机**：304 批建成 yan-plugin 时，`dsh-plugin/` 与 `yan-plugin/` 各有一套
`build*.mjs`、一份 `KB_DOC` 登记表、一份 `src/*.mjs` 运行时副本、一份 `engine/`
与 `skills/` 产物。yan 侧靠自检 [2.4] 段机械对拍两份 `KB_DOC` 防漂移——
**那是补丁，不是解法**：两份真源迟早分叉，门只能事后报警。
照那个形态再接 Claude / Codex / Gemini 三家，就是 5 份产物、5 条漂移面。

**改动**

- 新增 `plugins/`：
  - `SKILL.md` —— 技能正文**唯一真源**（从 `dsh-plugin/SKILL.md` 迁来，
    构建期可按宿主追加附加段，正文永不被改）。
  - `mcp/` —— 共享运行时唯一真源（8 个文件）：`server.mjs`（零依赖 stdio MCP）、
    `schema.mjs`（dsh 简写→JSON Schema 的唯一一处方言转译）、`tools.mjs`（1.0 冻结契约）、
    `engine.mjs`、`kb.mjs`、`report.mjs`、`python.mjs`、`kb-synonyms.json`。
  - `scripts/kb-docs.mjs` —— 知识库登记表唯一真源（原两份合并，对拍门随之删除）。
  - `scripts/build.mjs` —— **一次构建**：从两科收集 `plugins/engine/` 与
    `plugins/skills/`，再分发到 `ADAPTERS` 登记表里的每个适配器目录。
  - `scripts/selftest.mjs` —— 7 段自检，见下。
- 删除：`dsh-plugin/scripts/{build-engine,build-skills}.mjs`、
  `yan-plugin/scripts/{build,kb-docs,selftest}.mjs`、
  `dsh-plugin/src/{engine,python,tools,kb,report}.mjs`、`dsh-plugin/src/kb-synonyms.json`、
  `yan-plugin/src/`（全部改为构建分发）。
  两家的 `package.json` 脚本改为指向 `../plugins/scripts/*`。
- `python.mjs` 合成一份：优先级为 `DSH_PYTHON` → `YI_PYTHON` → DSH 桌面自带运行时
  → PATH `python`/`python3` → `py` 启动器。各宿主只走自己那一档，其余同序。
- `.gitignore`：新增 `plugins/engine/`、`plugins/skills/`、
  `dsh-plugin/src/*.mjs`（保留 `index.mjs`）、`dsh-plugin/SKILL.md`、`yan-plugin/src/`。

**自检 7 段**（`node plugins/scripts/selftest.mjs`，判红即 exit≠0）

| 段 | 守什么 |
|---|---|
| [1] | **分发一致性**：适配器 `src/*.mjs` 与 `plugins/mcp/` 真源**逐字节同源**（含负例自证：篡改一个字节即红） |
| [1.5] | 共享层与所有适配器零 `case_library.md`（含负例自证） |
| [2] | 两科 chart/analyze/narrate/render + 内核副本 + MANIFEST 齐备 |
| [3] | 各适配器 SKILL.md 正文以真源为前缀 + frontmatter + 知识库篇数对账 |
| [4] | **直接跑真源** `plugins/mcp/server.mjs` 冒烟：initialize / tools/list / `yi_kb` / `yi_liuyao` |
| [5] | 工具契约：四工具在列、inputSchema 为 object、`yi_liuyao` 参数集与 1.0 冻结面一致 |
| [6] | 适配器清单规范 + resources 双向对账（负例自证 a/b）+ 包体预算 |
| [7] | 对外文本无禁语（逐行 + 否定语境豁免，含负例自证） |

**首跑实测**：构建一次产出 `plugins/engine/` 与 `plugins/skills/`（9 篇 + INDEX），
分发到两家后自检全绿（rc=0）；`yi_kb` 命中带 `resource:kb-liuyao-interpretation-guide`，
`yi_liuyao` 用 Python 3.13.12 起出「贲」卦。

**首跑抓到并当场修掉的真 bug**（登记在此，防复发）：
`kb.mjs` 的 `resolveKbRoot()` 按目录名判层级（`src` 上一级、否则上两级），
而共享真源在 `plugins/mcp/` —— 命中 else 分支后多跳一级到**仓库根**，
于是 `files_scanned: 0`、`yi_kb` 永远空手。**这个 bug 只会在"跑真源"的那条路上现形**：
若自检仍跑适配器里的副本（旧形态），两家都正常，缺陷会被一直盖住。
改法：统一约定模块恒在 `<root>/mcp/` 或 `<root>/src/`，包根恒为 `..`。

### 未做的事（如实）

- **适配器登记表目前只有 dsh 与 yan 两家**，Claude / Codex / Gemini 尚未接入
  （304 批只做了选型核实，未动手）。
- **`dsh-plugin/scripts/selftest.mjs`（13 段）未合并**进本目录——它是已发布包
  （v1.0.23）的宿主侧 QA，含 npm 包内容与 DSH 内验证，本批只改了它的构建入口，
  未改其判据。是否合并、怎么合并，留给下一批。
- 未重跑 `npm --prefix dsh-plugin run verify-in-dsh`（需 DSH 宿主）。
- 分发方案（`plugins-dist` 分支 / Release tarball）仍未定，各宿主"远程市场装不上"
  的限制依然存在。
