# dsh-yi-divination

> DeepSeek Harness（DSH）插件：**六爻纳甲** 与 **八字四柱** 的确定性排盘与解读。
>
> **装了即用**——插件自带 Python 引擎与运行必需数据，不需要先 clone 仓库、
> 不需要手动配路径、也不需要单独装 Python（DSH 桌面自带运行时会被自动发现）。

## 它解决什么

在这之前，想用这套术数引擎得：clone 仓库 → 找到脚本路径 → 让 agent 敲
`python liuyao/scripts/chart.py --mode coin --question "..."` → 再敲 analyze → 再敲 narrate。
每一步都可能因为路径、工作目录、编码而失败。

装上本插件后，模型直接调用 `yi_liuyao` / `yi_bazi` 排盘、用 `yi_kb` 检索随包判据知识库、
用 `yi_report` 出单文件 HTML 报告，一次拿到结构化结论与正文。

## 安装

**发布版（推荐）**：从 GitHub Release 下载 tgz 后安装——
<https://github.com/LinHoMo/Yi/releases/tag/v1.0.0>

```sh
# 0) 发布版：tgz 换成实际下载路径
dsh plugin --profile <你的profile> install ./dsh-yi-divination-1.0.0.tgz

# 1) 开发版（用本机路径）
dsh plugin --profile <你的profile> add "link:<本目录绝对路径>"

# 2) 装 agent preset（可选但推荐：让新建会话能选「Yi 术数」）
node scripts/install-preset.mjs <你的profile>

# 重启 DSH，或刷新 Web 页面
```

`<你的profile>` 是 `$DSH_HOME/profiles/` 下的目录名。桌面版用 `desktop`；
命令行 Web 版通常是 `web`。

`install-preset.mjs` 是**幂等**的：重复运行不会插入第二份；会先备份你的
`cordis.patch.yml` 再写入，且**只追加**缺少的行，不碰你已有的其它配置。

卸载：`dsh plugin --profile <profile> remove dsh-yi-divination`
（preset 行如需移除，手动删 `cordis.patch.yml` 里 `- insert:` 下那两个 id 即可。）

## 三件套：插件 / 预设 / 知识库

本包同时提供 DSH 的三层能力，对应「agent 预设 + 知识库」的完整形态：

| 层 | 机制 | 在哪 |
|---|---|---|
| **工具** | `ctx.tools.register()` | `src/tools.mjs` → `yi_liuyao` / `yi_bazi` / `yi_kb` |
| **技能** | `ctx.skills.registerProvider()` + 官方 `bundledSkillDir` | `skills/yi-divination/SKILL.md` |
| **预设** | `@deepseek-ai/dsh-agent-preset` 的 Cordis YAML | `presets/yi-divination.yml` |

装上 preset 后，新建会话时可选「**Yi 术数（六爻 / 八字）**」——该 Agent 自带术数工具、
技能与知识库，与其它用途的 Agent 互不干扰（官方机制：同一进程可跑能力不同的 Agent）。

### 知识库

`skills/yi-divination/references/` 内含 9 篇判据文档，先从 `INDEX.md` 看该读哪一篇；
也可用 `yi_kb` 工具关键词检索定位（返回 文件:行 + 节标题 + 摘录）：

| 学科 | 文档 |
|---|---|
| 六爻 | `najia_rules.md`（纳甲规则 47KB）、`interpretation_guide.md`（断卦指南 24KB）、`pattern_reference.md`（格局速查 8KB）、`classical_synthesis.md`（四经典综合 52KB）、`source_ledger.md`（书源台账） |
| 八字 | `bazi_shishen_terminology.md`、`bazi_nayin_shiyi.md`、`bazi_yue_shi_ge.md`、`api_spec.md` |

> ⛔ **古籍案例库（`case_library.md`，165KB）刻意不随包发货**。按本仓 AGENTS.md §一.2
> 铁律二，案例库与解读必须物理隔离——断卦时不得联想、类比或引用历史案例。
> 打包脚本按文件名硬排除，自检 [1.5] 有一条专门断言它不在包内（带负例自证）。

## 四个工具

### `yi_liuyao` — 六爻纳甲

| 参数 | 必填 | 说明 |
|---|---|---|
| `question` | ✅ | 求测问题 |
| `mode` | | `coin`（铜钱，默认）／`time`／`number`／`manual` |
| `datetime` | | 起卦时刻 `"YYYY-MM-DD HH:MM"` |
| `numbers` | | `mode=number` 时必填，如 `"3,5,7"` |
| `yao` | | `mode=manual` 时必填，6 个爻值如 `"7,8,9,7,6,8"` |
| `seed` | | 铜钱摇卦的随机种子（可复现） |
| `gender` | | `男`／`女`——占感情时影响用神取法 |

返回：卦名/宫/世应/六爻（六亲·六神·地支·动静）/用神及其旺衰/结论与应期/关键影响项/正文。

### `yi_bazi` — 八字四柱

| 参数 | 必填 | 说明 |
|---|---|---|
| `datetime` | ✅ | 出生时间 `"YYYY-MM-DD HH:MM"`（公历） |
| `gender` | ✅ | `男`／`女`（大运顺逆依赖于此） |
| `longitude` | | 出生地东经，用于真太阳时校正 |

返回：四柱（干支·纳音·十神）/正文，另含结构化岁运字段——`conclusion`（旺衰·分数·格局·成败·
喜忌·调候·空亡·胎元·通关·天克地冲·病药）、`dayun`（大运 8 步，起讫岁+十神+明动事件）、
`liunian`（流年 12 年，干支·十神·所临大运·明动与岁运交叉事件）、`liuyue`（流月 12 月干支十神）。

### `yi_kb` — 判据知识库检索

| 参数 | 必填 | 说明 |
|---|---|---|
| `query` | ✅ | 关键词，可多个，空格分隔（如 `"用神 取法"`）；无空格长词自动 2-gram 兜底，同义词自动展开 |
| `discipline` | | `liuyao`／`bazi`（缺省两科都搜） |
| `limit` | | 最多返回几条（默认 5，上限 10） |

返回「文件:行 + 节标题 + 摘录」。纯 Node 实现（`src/kb.mjs`），不依赖 Python；
先检索定位、再按 `file:line` 读具体节段。案例库在扫描层硬排除（铁律二第三道闸：
打包层 `plugins/scripts/build.mjs` 排除 + 自检 [1.5] 断言 + 本工具扫描层排除）。

### `yi_report` — 完整排盘报告（文件）

| 参数 | 必填 | 说明 |
|---|---|---|
| `discipline` | ✅ | `liuyao`／`bazi` |
| `format` | | `html`（默认）／`md` |
| 其余 | | 与对应排盘工具相同（六爻 `question` 等；八字 `datetime`/`gender`） |

先判读（yi_liuyao / yi_bazi）、后出报告。六爻 html 与两科 md 走**引擎 render 段**；
八字 html 由插件排版层（`src/report.mjs`）生成——四柱卡、旺衰格局喜忌徽章、大运时间条、
流年结构事件表、流月格，文字全部来自引擎字段、零新断语，页脚自带口径说明
（古籍对齐分≠命中率）。返回 `{path, format, bytes, generator, preview}`，把路径转告用户。

## Python 解释器怎么找

按优先级：

1. `DSH_PYTHON` 环境变量（显式覆盖，调试/CI 用）
2. **DSH 桌面自带运行时**：`$DSH_HOME/dsh-runtimes/*/dependencies/python/python.exe`
   （实测本机 DSH 0.2.1-rc.2 自带 Python 3.12.14）
3. PATH 里的 `python` / `python3`
4. Windows 的 `py` 启动器

全找不到时工具会报错并**逐条列出已尝试的路径**，不会静默回退到某个不确定的解释器
——那会让不同机器跑出不同结果，而这套引擎的全部口径都建立在确定性上。

## 体积

发布包只含运行必需部分，**不含评测数据**。

**以下为 `npm pack --dry-run --json` 实测值**（163 个文件，非估算）：

| 内容 | 解包体积 |
|---|---|
| 引擎（core + scripts + data/rules + data/*.json + references + assets，两科，139 文件） | 2.35 MB |
| 知识库（技能目录下 9 篇判据文档 + SKILL.md + INDEX，11 文件） | 0.17 MB |
| 插件源码（7 文件） | 0.06 MB |
| 文档与配置（README/SKILL/LICENSE/package.json/patch/preset） | ≈ 0.02 MB |
| **解包合计** | **2.6 MB** |
| **npm 分发 `.tgz`** | **0.77 MB** |

| 未打包 | 体积 | 原因 |
|---|---|---|
| `data/cases/` | 38 MB | 只服务古籍对齐分与回归门，起卦断卦用不到 |
| `data/sources/` | 9.5 MB | 同上（书源原文，评测用） |
| `references/case_library.md` | 165 KB | 铁律二：案例库与解读必须物理隔离 |

复现：`cd dsh-plugin && npm pack --dry-run --json`

`plugins/scripts/build.mjs` 用**白名单**收集文件：新增目录不会因为「忘了排除」
而被悄悄打进包，只会因为「忘了收录」在自检里报红——后者是安全的失效方向。

## 构建与自检

```sh
npm run build          # = build-engine（打包引擎）+ build-skills（组装技能目录与知识库）
npm run selftest       # 13 段包级自检，含负例自证
npm run verify-in-dsh  # DSH 内验证：技能条目形状 + 真实执行工具回调 + render 产出
npm run check          # 以上三件一起跑
```

**为什么需要第四步 `verify-in-dsh`**：前三轮我只验证到"插件加载无 warning"，
以为就算装好了。真跑一次模型才发现——技能 provider 返回的 `invocation` 写成字符串、
缺了 `rank`，会让**整轮会话直接 error 退出**，模型一个字都答不了。加载无 warning ≠ 能用。

`verify-in-dsh` 不调模型（不依赖额度/密钥），而是构造一个够真的 Cordis 上下文，
走 `apply()` 注册，然后**真的执行一次工具回调**，断言：

- 工具确实进了注册表，参数 schema 在场
- 技能条目**逐字段对齐** `dsh-skill` 的校验（`invocation` 必须是对象、`rank` 必须是有限数）
- `execute()` 返回结构化结果且正文非空
- `output.render()` 能摊出模型可见的文本块

自检覆盖：包结构 / 知识库随包与案例库隔离（含负例）/ SKILL.md frontmatter（含坏样本）/
Python 定位（含指向不存在路径必须报错）/ 打包引擎完整性 / 六爻与八字端到端 /
**随官入墓去重的判据回归（含负例）** / 参数语义校验 / 正文不得出现「预测准确率」/
引擎与知识库逐文件一致性 + 反向覆盖（防过期、防漏收）/
Agent preset 声明合法性（含负例）/ 安装脚本幂等与 YAML 安全性 /
引擎目录不被运行期派生文件污染（含负例）。

当前实跑：**77 项通过 / 0 失败**。

一致性门是**逐文件全量**的，不是抽查：137 个引擎文件 + 9 篇知识库逐篇与两科真源对拍，
外加「真源有、包里缺」的反向核对（案例库按铁律二豁免）。
实测过它能抓过期——往包里注一行脏数据，门立即报 `已过期：liuyao/core/yishu_core/symbols.py`。


## 口径边界（重要）

- 引擎内一切分数是**古籍案例对齐分**（与古籍要点的吻合度），**不是现实命中率**。
  现实侧样本为零。
- 输出是**象征推演与方向参考**，不是预言。凶象用「偏向／有…信号／结构上」表述。
- 医疗、法律、投资、重大决策请以专业意见为准。
- 八字结论是机械推演（旺衰/格局/喜用/调候），**不含命运吉凶断言**；
  方向字段为空是正常的，不是缺数据。
- 六爻外部验证集（未参与调参）主应期 top-1 **31.8%**（n=44，308 批实测，旧登记 27.3）：
  高于 k=1 随机 8.3%，**低于全池随机 34.1%**（池均值 4.1/12），CI [20.0, 46.6]——
  样本小、区间宽，`liuyao/README.md` 同屏。如实摆出，不进任何宣传话术。

## 已知限制（1.0.0）

- **时区口径**：引擎按你提供的本地钟表时**直接**排盘（`calendar_policy` 只管换日边界与
  子时归属，不做时区换算）；海外生辰请先自行换算成出生地当地钟表时再输入，
  `longitude` 参数只做真太阳时经度校正。
- **报告文件**：`yi_report` 产物写入系统临时目录（Windows `%TEMP%/yi-reports/`），
  工具返回值带绝对路径与预览；目录只增不清，需要留存的卷面请自行拷出，其余可手动清理。
- **平台实测**：开发与实测为 Windows；CI（277 批起）在 windows + ubuntu 双平台跑插件门禁，
  Linux 侧以 CI 首跑为准。
- **反馈通道**：现实占断反馈在册 0 条（`liuyao/data/feedback/`），八字侧无通道——
  本插件**没有**任何现实命中率数据，也请勿替它宣称。

## 兼容性（manifest 已显式声明）

这些范围已在 manifest 的 `dsh.compatibility` 与 `engines.node` 中**显式声明**（DSH STORE 契约要求），本节为可读版：

- **Node.js**：`>=22`（`engines.node` 与 `dsh.compatibility.node` 双写；实测 22.x / 24.x）。
- **DSH**：`>=0.2.1-rc.2`（`dsh.compatibility.dsh`）。开发与实测环境 **0.2.1-rc.2**（build `332895e`）；
  官方最新 **0.2.1-rc.3**（2026-10-23）的升级指南仅涉及「普通 session fork 变为独立 Session」，
  与插件扩展点无交集，故在 rc.3 上预期可直接运行。
- 用到的扩展点：`ctx.tools.register()`、`ctx.skills.registerProvider()`、
  `ctx.systemPrompt.section()`、`@deepseek-ai/dsh-agent-preset`、
  `@deepseek-ai/dsh-skill-filesystem` 的 `bundledSkillDir`——均为官方登记的公开扩展点。

## 开发时踩到的坑（全部已修，留档给后来者）

| # | 坑 | 后果 | 为什么本地测试看不见 |
|---|---|---|---|
| 1 | `systemPrompt` / `skills` 没写进 `inject` | 整条插件不激活 | 假 `ctx` 测试全过；真机只打一行 warning 就继续启动 |
| 2 | `section()` 漏了 `order` | 同上 | 同上；官方只说「外部贡献可用任何有限 order」，没说漏了会失败 |
| 3 | 子进程未设 `PYTHONDONTWRITEBYTECODE` | 每次运行长出 ≈1.2MB `__pycache__`；只读安装位上会写失败 | 自检只看「能不能跑通」，不看跑完目录脏没脏 |
| 4 | 补丁层写成裸 `- id:` 而非 `- insert:` | 宿主报 `entry "xxx" not found`，插件不加载 | 必须真的 `--dump-config` 才看见 |
| 5 | 安装脚本把条目追加到空 flow `[]` 之后 | YAML 非法，**整个 profile 起不来** | 单元测试不解析 YAML |
| 6 | 幂等判定只匹配行首 `- id:` | 重复安装插入第二份 | 需要「连跑两次比对 md5」才暴露 |
| 7 | 技能的 `invocation` 写成字符串 `'model'` | **整轮会话 error 退出**，模型一个字都答不了 | 加载无 warning；只有真跑模型才触发 |
| 8 | 技能条目缺 `rank` | 同上（`invalid rank`） | 同上 |
| 9 | fallback 注册路径漏了 `output.render` | 工具能执行但**模型看不到正文** | 需要真的执行回调并检查 render 产出 |

第 7–9 条是**同一轮真机验证**里连锁暴露的：把 `dsh` 当完整运行时真跑一次模型，
才从 `turn_end.reason` 里看到 `non-object invocation policy` → 修完又是
`invalid rank` → 修完才发现 render 缺失。前六轮验证全部绿，一条都没碰到。

共同点：**它们全都在"看起来装好了"与"真的装好了"之间**。所以本项目的开发流程硬性要求是
「改代码 → 装进临时 profile → 启动看有没有 warning → **真跑一次模型/执行一次工具回调** → 再跑自检」。
只跑单元测试、或只看启动日志，都不够。

## 权限与安全（DSH STORE 契约）

本插件在 manifest 的 `dsh.permissions` / `dsh.externalServices` / `dsh.failureBounds` 中
**显式声明**了运行期用到的能力与边界，并附范围与理由（manifest 为唯一真源，本节为可读版）。
所有声明均与源码逐条对应，供人工复核。

### 依赖

- **运行期 npm 依赖：零**。本包不依赖任何第三方 npm 包；`@deepseek-ai/dsh-*` 是宿主提供的
  peer，不打包进本包。
- **Python 引擎**：随包内置（只读），无需另装；找不到时用 DSH 桌面自带运行时 / PATH /
  Windows `py` 启动器（见上文「Python 解释器怎么找」）。

### 权限声明

| 能力 | 是否启用 | 范围与理由 |
|---|---|---|
| `files` | ✅ | 读随包引擎与技能；报告只写到系统临时目录（`os.tmpdir()/yi-*`、`%TEMP%/yi-reports`），绝不写用户工程目录；加载时读 `SKILL.md`。 |
| `commands` | ✅ | 只 `spawn` 本地 Python 解释器运行随包、**只读**的引擎；不用 shell、不执行任何用户命令。 |
| `credentials` | ⚠️ 受限 | 只读**白名单**非机密环境变量 `DSH_HOME` / `DSH_PYTHON` / `PATH` / `PYTHONIOENCODING` / `PYTHONDONTWRITEBYTECODE`（用于定位解释器与设 UTF-8）。**不读密钥 / 钥匙串 / 令牌 / API key / 网络凭证，零出站网络调用**。 |

### 外部服务

- **网络：无**。插件在本地离线运行，不发任何出站请求，不回传任何数据。
- **数据外传：无**。

### 失败边界

- **找不到 Python**：工具如实报错并**逐条列出已尝试的解释器路径**，**绝不静默回退**到不确定的
  解释器（不同机器跑出不同结果是本仓最忌）。
- **引擎阶段超时**：单阶段 120 秒（`engine.mjs` 的 `timeoutMs`），超时即杀进程并抛错。
- **引擎 / 数据缺失**：启动自检 `selftest()` 打印告警；调用时工具报错，不返回半成品。

### 一次性 Profile 安装 / 启动 / 卸载证据

按 DSH STORE 要求，在**一次性（throwaway）Profile** 中验证「安装 → 启动 → 卸载」链路：

```sh
# 1) 全新一次性 profile
dsh profile create yi-disposable            # 或用临时目录

# 2) 安装（开发版 link，不污染全局）
dsh plugin --profile yi-disposable add "link:<repo>/dsh-plugin"
node dsh-plugin/scripts/install-preset.mjs yi-disposable   # 幂等追加 preset

# 3) 启动并验证（不消耗真实模型额度）
npm --prefix dsh-plugin run check
#   = build（引擎+技能白名单收集）
#     → selftest（77 项，含负例自证）
#     → verify-in-dsh（27 项：注册面 / 技能条目形状 / 真实执行工具回调 / render 产出）

# 4) 卸载
dsh plugin --profile yi-disposable remove dsh-yi-divination
dsh profile remove yi-disposable
```

`npm run check` 即是「装进一次性 Profile、启动后工具可被注册并真实执行一次回调」的工程等价证据：
`verify-in-dsh` 构造够真的 Cordis 上下文，**真跑 `execute()`** 并断言正文非空、
`output.render` 摊出模型可见文本块。当前实跑：**selftest 77 项通过 / 0 失败；
verify-in-dsh 27 项通过 / 0 失败**。

> 声明本身不保证自动批准：本插件属「本地 spawn Python + 写临时文件」的 elevated 能力，
> 即便声明完整，DSH STORE 仍可能维持 user-reviewed / blocked；声明与文档的目的只是把
> 能力与边界讲清，供人工复核。

## 许可

MIT。许可证在**三处一致**：仓库根 `LICENSE`（新增，GitHub 仓库元数据据此识别）、
`dsh-plugin/LICENSE`（随包分发）、manifest `license: "MIT"`。
