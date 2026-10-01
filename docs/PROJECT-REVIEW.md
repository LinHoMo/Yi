# 易（Yi）项目完整审查报告

> 审查范围：整个 `C:/Users/31103/Desktop/program/Yi` 仓库
> 审查方式：根 `tools/check.py` 跑测 + 4 路并行 Explore 深扫（架构契约 / web 通道 / 代码质量 / 命名规范）+ 关键 P1 项逐条源码复核
> 基准时间：2026-10-01

---

## 0. 一句话结论

仓库**工程质量整体扎实**：依赖方向单向、内核单一入口、断语外置、CLI 规范、web 双通道同源前提成立、根 `check.py` 全绿。
但存在 **1 个 P0（安全网自身失盲）** 与 **7 个 P1**，核心风险是：

1. **仓库级自检门给出"假绿"** —— 唯一真值表防复制检测只认同名重定义，漏掉了"改名但内容逐字节相同"的副本；
2. 架构契约在 liuyao 层被悄悄突破（复制了 core 的旬空表）；
3. web 通道的模块隔离不变量未真正兑现、同源验收未进 CI。

下面按优先级展开，每一项都给出 `文件:行` 证据。

---

## 1. P0 — 自检门失盲（最该先看的问题）

### 1.1 根 `check.py` 报"全绿"，但存在改名副本未被检出

`tools/check.py:39-47` 的 `CORE_TABLE_ASSIGN` 正则只匹配**同名**赋值（如 `XUN_KONG = [...]`）在学科层出现即判复制。
然而 liuyao 把 core 的 `XUN_KONG`（旬空）**改名**为 `EMPTY_DEATH`，内容逐字节相同，正则无法命中 → 闸门放行。

证据（已逐行核对）：
- core 真值：`core/yishu_core/symbols.py:89-92` `XUN_KONG`
- liuyao 副本：`disciplines/liuyao/scripts/chart_tables.py:189-196` `EMPTY_DEATH`（内容相同）
- 使用点：`engine_chart.py:356-357,374`、`liuyao_engine.py:54`

**影响**：AGENTS.md 明确警示"同一批表在多处各存一份、取值可能不一致"是历史事故形态。当前 gates 对此类"改名副本"完全失明，
意味着仓库对外宣称的"内核规则表无学科复制 = √"含有水分，且**无法保证没有第二处同类副本**。

**修复**：
- 短期：删 `EMPTY_DEATH`，改从 `yishu_core` 引入 `XUN_KONG`（`engine_chart.py`/`liuyao_engine.py` 改引用）。
- 治本：在 `check.py` 的"内核规则表无学科复制"项中，除同名检测外，增加**内容指纹比对**（对学科层出现的 dict/list 字面量与 core 真值表做规范化后哈希比对），堵住改名副本的盲点。

---

## 2. P1 — 架构 / 真值源契约

### 2.1 liuyao 复制 core 旬空表（改名副本）
见 1.1。属 AGENTS §二"学科不得复制这些表"的直接违反。

### 2.2 core 内部天干/地支被定义三处
`HEAVENLY_STEMS`/`EARTHLY_BRANCHES` 在 core 内重复：
- `core/yishu_core/symbols.py:23,25`（list 形式）
- `core/yishu_core/ganzhi_calendar.py:24,25`（字符串形式）
- `core/yishu_core/ziwei_tables.py:17,18`（字符串形式）

违反"core 中只存在一份"。list 版与字符串版并存，存在取值漂移隐患。

### 2.3 纳甲系统被拆两处
- core `najia.py:17` 仅提供 `najia_branch`（纳甲**地支**）；
- liuyao `chart_tables.py:116` 自行定义 `NAJIA_STEMS`（纳甲**天干**）。

纳甲整体被列为 core 真值源（"纳甲支表"），但其天干一半落在学科层，违反"新表加进 core、不要就地新建"，易漂移。建议把 `NAJIA_STEMS` 并入 core。

### 2.4（P2，顺带记）`disciplines/base` 共享层未被接入
`base/cli.py` 的 `DisciplineCLI` 与 `base/protocol.py` 全仓零引用；`cli/main.py` 走 subprocess 而非继承基类。
属设计漂移（不违反方向性），建议：要么学科 CLI 统一接入 `DisciplineCLI`，要么删除该闲置抽象。

---

## 3. P1 — Web 通道 / 报告流水线

### 3.1 `_isolate` 隔离不变量未真正兑现
`web/engine_runtime.py:47-74`：
- 清 `sys.modules` 里别的学科的模块（✓ 正确）；
- 但 `sys.path[:] = [scripts_s] + [p for p in sys.path if p != scripts_s]`（`:73`）**只把当前科 scripts 提到最前并去重，没有移除之前跑过的兄弟科 scripts 目录**。

后果：浏览器同进程先跑 A 科再跑 B 科后，`sys.path = [B_scripts, A_scripts, core, …]`。若 B 科（或其 helper）`import` 了一个**只在 A 的 scripts 目录存在的裸模块名**，Python 会解析到 A 的模块 → 仍发生同名遮蔽。这正是 AGENTS §六明令禁止的情形，当前只实现了隔离的一半。

当前未触发（流水线各段只 import 自己科内 helper），但**不变量未被强制保证**，属正确性风险。
**修复**：`_isolate` 先把所有 `disciplines/*/scripts` 从 `sys.path` 移除，再只 prepend 当前科。

### 3.2 同源验收未接入任何 CI
`grep -rln "verify_web_parity\|check.py" .github/` → **空**。
`verify_web_parity.py`（产出同源头号契约的自动验收）只靠人工 `check.py --full` 触发（AGENTS §六修订门槛要求改相关文件必须跑，但**无工作流强制**）。
一旦 `request.py` 与某执行器漂移，CI 不会拦截。建议：在 `pages.yml`/`report.yml` 中加一步 `python tools/verify_web_parity.py`。

### 3.3 学科目录被硬编码在 3 处且可漂移
- `web/engine_runtime.py:29` `DISCIPLINES`（6 科，**从未被引用**）
- `core/yishu_core/report/request.py:26` `DISCIPLINES`（8 科）
- `tools/build_web.py:46` `DISCIPLINE_META`（6 科）

`request.py` 接受 liuren/lingqi（`normalize_request` 不拒绝），但 `build_web.py` 不镜像它们 → web 跑这两科时 `_isolate` 发现 scripts 非目录 → 不加入 sys.path → `FileNotFoundError` → `RuntimeError("chart 段失败")`（engine_runtime.py:130-131）。属响亮崩溃而非干净拒绝，且无"web 不支持该科"的卫语句。

**修复**：学科目录收敛为单一真值源 + 断言；`build_report` 对未镜像/web 不支持的科给出清晰报错。

### 3.4（P2）`report.yml` 输入数恰好顶到 GitHub 上限
`report.yml:12-58` `workflow_dispatch.inputs` = 正好 **10 个**，顶到 GitHub 10 输入硬上限（注释已声明超量即"工作流直接不注册"）。再添任一输入会使整个通道 B 静默失注册。设计性脆弱，建议把超量字段改走 issue 正文 / `repository_dispatch`。

### 3.5（P2）同源验收的固有局限
- `_html_without_runtime_tag`（verify_web_parity.py:81-91）替换的是**整行** `class="meta"`，过度归一化，可能掩盖真实 meta 差异。
- `CASES` 只测 6 个 web 科，从不测 liuren/lingqi。
- 等价 ≠ 正确：若 `request.py` 共有映射本身出错，两通道会**一致地错误**，验收照过。需另行正确性测试兜底。

---

## 4. P1 — 仓库清洁度 / §三 规范

### 4.1 `_site/` 是 `site/` 的陈旧重复构建产物
- 两者均被 `.gitignore` 忽略，都是 `tools/build_web.py` 的产物；
- `build_web.py:116` 已主动排除 `_site`，`build_web.py:292` 默认输出到 `site/`；
- `diff -rq` 仅 3 文件不同（ming 两个脚本更新过 + manifest），`_site` 早约 3.5 小时。

**结论**：`_site/` = 已废弃旧快照。建议**删除 `_site/`**，保留 `site/`，避免误改错误副本。

### 4.2 `.gitignore` 与 §三 直接冲突（生成物 *.html/*.jsonl 未忽略）
`grep -nE "html|jsonl" .gitignore` 仅返回 `.trae-html-share-packages/`，**无 `*.html`/`*.jsonl` 规则**，违反 AGENTS §三"生成物（outputs/、*.html、*.jsonl）不得入库"。
当前已提交 `docs/DEEP-OPTIMIZE-PLAN.html`（位于 docs 根，非 `docs/samples/`，按 §三 属可疑生成物）。
**风险**：脚本误生成 `report.html` 极易被 `git add` 提交。
**修复**：`.gitignore` 增加 `*.jsonl` 与收窄的 `*.html` 规则（不误伤 `web/index.html` 与 `docs/samples/*`）；把 `docs/DEEP-OPTIMIZE-PLAN.html` 移入 `docs/samples/` 并加说明。

---

## 5. P2 — 代码质量其余项

- **`cli/main.py` argparse 成装饰**：`:97-124` 构建了子解析器却从不 `parse_args()`，路由靠 `:133,142,153,157` 手动切 `sys.argv`。建议改由 subparser 完成路由，或注释说明为何手动。
- **`tools/demo.py` 绕过映射层**：`:69-72` 硬编码六爻 CLI，不经 `request.chart_argv`；其 `DISCIPLINES` 仅列 5 科（漏 ziwei）→ demo 输出可随映射变更悄悄失真。
- **`tools/scratch/` 调试残留**：`reading_final.md`、`debug_cong2.py`、`dbg*.py` 等（gitignored，不入库，但属 §三 点名的应清残留）。
- **`archive/`、`mcp-server/`（仅 README）**：归属不明，建议确认或清理。
- **`liuyao_analyze.py` 兼容壳**：仍被 `thinking_chain.py:48` import，未来可清。
- **`engine_chart.py:394-398`**：六爻爻名枚举（`初九…上九`/`初六…上六`）写死在代码，可移 `data/*.json`。

---

## 6. 健康面（勿过度反应）

以下经核查**确实合规**，审查中未发现违规：
- 根 `check.py` 全绿（版本唯一、结构契约同名检测、断语外置、内核自检、各学科门、web 构建/自检）；
- **无**跨科 import；依赖方向单向；`yishu_core` 为唯一内核入口；**无**硬编码用户路径；**无**已提交 `.pyc`；**无**入库版本化文件名；
- 双报告通道共用 `request.py` 唯一映射源、执行相同的 chart→analyze→render 契约（AGENTS §六 一致）；liuren/lingqi 的 web 排除是**有意且文档化**的（PROMPTS.md）；
- `.github/workflows` YAML 合法、用内置 `GITHUB_TOKEN`、`paths` 过滤能触发重建；
- 中文断语/引文基本都外置 `data/*.json`，无大段硬编码经典文本。

---

## 7. 修复优先级建议

| # | 优先级 | 项 | 动作 |
|---|---|---|---|
| 1 | **P0** | 自检门失盲（1.1） | 治本：check.py 增加内容指纹比对；先修 `EMPTY_DEATH`→`XUN_KONG` |
| 2 | P1 | core 天干/地支三处（2.2） | 收敛为单一定义 + re-export |
| 3 | P1 | 纳甲拆分（2.3） | `NAJIA_STEMS` 并入 core |
| 4 | P1 | `_isolate` 隔离（3.1） | 先全清 `disciplines/*/scripts` 再 prepend 当前科 |
| 5 | P1 | 同源验收无 CI（3.2） | 在 `pages.yml`/`report.yml` 加 `verify_web_parity` 步骤 |
| 6 | P1 | 学科目录多源（3.3） | 单一真值源 + 断言 + 干净拒绝未镜像科 |
| 7 | P1 | `_site/` 陈旧副本（4.1） | 删除 `_site/` |
| 8 | P1 | `.gitignore` 冲突（4.2） | 加 `*.jsonl`/收窄 `*.html`，移 `DEEP-OPTIMIZE-PLAN.html` 到 samples |
| 9 | P2 | `base` 层闲置（2.4） | 接入或删除 `DisciplineCLI` |
| 10 | P2 | `report.yml` 10 输入上限（3.4） | 超量字段改 issue/dispatch |
| 11 | P2 | `cli/main.py` 手动路由（5） | 走 argparse subparser 或注释说明 |
| 12 | P2 | 调试残留 / 归属不明目录（5） | 清 `scratch/`、确认 `archive/`、`mcp-server/` |

> 注：1 号是元问题——它让"全绿"结论本身不可尽信，建议最先处理，处理完再重新跑全量审查确认无同类改名副本遗漏。

---

## 8. 修复状态（2026-10-01 同日修复回执）

| # | 项 | 状态 | 修复方式 |
|---|---|---|---|
| 1 | P0 自检门失盲 | ✅ 已修 | ① 删 liuyao `EMPTY_DEATH`，`get_empty_death` 委托 core `xunkong_of`；② `check.py` 新增内容指纹检测（ast 解析 + 归一化 JSON 指纹，空 dict/list 不参与），**立即又揪出 3 处隐藏改名副本并全部修复**（meihua `_STEM_ELEMENT`/`_BRANCH_ELEMENT`、liuren `_TOMB_OF_ELEM`、liuren ETL `JI_GONG`） |
| 2 | core 天干/地支三处 | ✅ 已修 | 唯一字面量收进 `ganzhi_calendar`（依赖链最底层）；`symbols` 派生 list、`ziwei_tables` 改 import；顺手删除 core 内部无人使用的 `ganzhi_calendar.BRANCH_ELEMENT/STEM_ELEMENT`，并把 `liuren_tables.STEM_HE` 收敛为 `relations.STEM_WUHE` 别名（指纹扫描另发现的 core 内部重复） |
| 3 | 纳甲拆分 | ✅ 已修 | `NAJIA_STEMS` 迁入 `symbols.py`（与 `NAJIA_BRANCHES` 合璧），`najia.py` 再导出，liuyao `chart_tables` 改引 core |
| 4 | `_isolate` 隔离 | ✅ 已修 | 先剥离 sys.path 上**所有**学科的 scripts 目录，再 prepend 当前科；行为测试：连跑两科后 path 仅剩当前科 |
| 5 | 同源验收无 CI | ✅ 已修 | `pages.yml` 构建任务新增「网页/本地同源验收」步骤（`verify_web_parity`），不一致即阻断部署 |
| 6 | 学科目录多源 | ✅ 已修 | `engine_runtime` 弃用死常量、改 `WEB_DISCIPLINES` + 未挂载学科**干净拒绝**（ValueError 带可用科目清单）；`build_web` 构建期断言 `DISCIPLINE_META ⊆ request.DISCIPLINES`（fail-fast），并写明三处清单的同步规程 |
| 7 | `_site/` 陈旧副本 | ✅ 已删 | 磁盘构建产物，`build_web.py` 随时可重建 |
| 8 | `.gitignore` 与 §三 冲突 | ✅ 已修 | 新增 `*.html`/`*.jsonl` 兜底忽略 + 白名单（`web/index.html`、`docs/samples/**`）；`docs/DEEP-OPTIMIZE-PLAN.html` 移入 `docs/samples/` |
| 9 | `base` 层闲置 | ✅ 已修（独立重构 2026-10-01） | 全仓零引用确认后**删除** `disciplines/base/`；契约强制本就靠 CONTRACT.md + check.py 结构门 + golden/忠实度回归；同步 AGENTS/README/ARCHITECTURE/HANDOFF/MIGRATION/CHANGELOG |
| 10 | `report.yml` 10 输入上限 | ✅ 已修（独立重构 2026-10-01） | 表单 10→6 个（核心 4 字段 + `extra` JSON 逃生舱 + commit_branch，留 4 余量）；`ci_request.py` 解析 `INPUT_EXTRA`（extra 铺底、显式字段覆盖、坏 JSON 容错）；旧逐字段调用兼容；AI-SOP/AGENTS 同步 |
| 11 | `cli/main.py` 手动路由 | ✅ 已修 | 补注设计理由：argparse 只作帮助视图，手动路由是为把未知参数透传给学科脚本 |
| 12 | `demo.py` 清单缺 ziwei | ✅ 已修 | `DISCIPLINES` 补 ziwei（含 chart_args）；硬编码 CLI 参数补注"有意为之"（与 SKILL.md 文档命令一致） |
| — | `tools/scratch/` 残留 | ⏸ 保留 | AGENTS.md §三 明文指定一次性脚本放 `tools/scratch/`（gitignored），属合规去处，不清 |

**验证**：`python tools/check.py --full` 全量门（版本/结构/指纹/内核自检/ming·ziwei 质量门/六爻黑箱/合参/站点构建+自检/网页本地同源/pytest）通过后回执见仓库提交记录。
