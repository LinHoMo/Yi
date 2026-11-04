# 易（Yi）· 项目级铁律（贡献者/编码 Agent 规程）

> **读者边界**：写给在本仓库**改代码的贡献者/编码 Agent**；调用 Yi 出报告的任务 Agent
> 入口是各科 `SKILL.md`。与单科 SKILL.md 冲突时本文件优先。
>
> **沿革**：第一百六十六批按现行两科布局重建；扁平化前的目录与工具已不在库，不复活。
> 历史裸编号引用（「铁律一／二／三」）的歧义见 §一 沿革条，新增引用一律写节号。

**范围**：两科正式术数，目录 `bazi/`（四柱八字）与 `liuyao/`（六爻纳甲），相互独立、
零耦合、各带私有内核副本（`<科>/core/yishu_core/`）。其余术数已正式移除，不预留目录、
不写占位实现。各科 `dev_tools/check.py` 的全绿状态只对所登记的 revision 成立。

## 一、三条不可动摇的铁律

> **「铁律」编号沿革（2026-10-13 按 git 历史实测对账，必读）**：根 `SKILL.md` §四「铁律
> （操作版）」曾以**四条**列出 ①机械运算归代码 ②案例库与解读物理隔离 ③口径诚实 ④一卦一事，
> 与本文件 §一／§五 的编号**同序**；该文件随扁平化删除后，两科 `SKILL.md` 只留了
> **①（铁律一）**，而 §三 以后的 dev_tools/docstring 沿用「铁律二／铁律三」时**另有含义**：
> ① `dev_tools/*` 的「铁律二」＝**自检夹具只走临时目录**（§四.8 的操作化，见
> 　`--selftest` 各门实现）；② `bazi/data/liushen_image.json` 等数据注记的「铁律二/铁律一」
> 　＝**引文逐字照录、可指回原文**（§二「数据缺陷 vs 引擎缺陷」条）；
> ③ 旧根 `SKILL.md` 与本文件 §一 的原始编号（铁律二＝案例隔离、铁律三＝口径诚实）。
> **现行权威以本文件 §一 为准**；历史引用不回改（改动面大且语义无害），但**新增引用一律写节号**
> （如「AGENTS.md §一.2」「§四.8」「§二 引文条」），不要再新增第四套裸编号。

### 1. 机械运算归代码，象数解读归 LLM

起局、排盘、装卦、定宫、纳甲、安世应、推六亲、配六神、查旬空、判旺衰、算应期、识别格局——
**必须且只能**由 Python 完成。LLM 严禁心算或"推算"任何上述结论。

脚本失败时重试一次；仍失败则告知"排盘异常"，**不得手动替代**。
吉凶断语不得进结构层：结构层只出标签与数值，断语字面量进 `data/*.json`（见 §三 表）。

### 2. 案例库与预测过程物理隔离（两科均已物理隔离）

> **第三百五十六／三百五十九批**：两科评测实现均已物理迁出 `scripts/`——六爻进
> `liuyao/eval/`（case_runner / evaluate / build_portal_assets），八字进
> `bazi/eval/`（evaluate）；`scripts/` 下同名文件只剩纯 re-export 兼容 shim。
> `check_case_isolation.py` 按该科有无 `eval/` 选档：两科现均走**物理隔离档**
> （`eval/` 实现必须存在（正面断言）＋ `scripts/` 零白名单，出现案例库字面路径/
> expected 取数即红）；白名单档仅作为未来新科的过渡判据保留，当前无科在用。

`*/data/cases/` 与 `references/case_library.md` 中的古籍案例，只允许三种访问场景：
测试运行器读取、用户明确要求事后校验、用户主动询问"有无类似案例"（须注明仅供参考）。

解读交付前禁止：打开案例库、提及案例名、以案例类比佐证、在推理链中联想案例。
机械门：各科 `dev_tools/check.py` 的「案例库隔离」小节（`check_case_isolation.py`，
解读路径模块逐一静态检查，触达 `data/cases` 即判红）。

### 3. 口径诚实：禁止把"对齐分"说成"预测率"

仓库内所有分数都是**古籍案例对齐分**（引擎输出与古籍案例要点的吻合度），用于回归审计。
它衡量不了现实世界命中率。任何文档、报告、UI、对话输出中：

- ❌ 不得出现"预测准确率 99%""断事如神"一类表述
- ❌ 不得只给一个百分比而不给集合名、样本量 n、是否为未参与调参的 holdout
- ✅ 医疗、法律、投资、重大决策必须提示以专业意见为准
- ✅ 凶象用"偏向/有…信号/结构上"，不用"注定/一定/绝无可能"

## 二、目录与依赖契约

```
Yi/
├── AGENTS.md            # 本文件：项目级铁律（贡献者读）
├── CONTRACT.md          # 四段契约：chart→analyze→narrate→render 的判据本体（310 批重建）
├── kernel/              # 引擎内核单一真源（316 批起）：common/ 两科共用 + variants/<名>.<科>.py 在册分叉
├── devkit/              # **门禁内核**单一真源（331–334 批）：shared/ 单一真源 +
│                        #   shared/variants/<名>.<科>.py 在册变体（项数以 MANIFEST.json 为准，
│                        #   433 批曾把 11 改 12 而本行落后过）；root/ 根级门（不分发）；
│                        #   sync_devkit.py --write/--check；handoff/ 不入库（514 批已清理）
├── liuyao/              # 六爻（独立）
│   ├── core/yishu_core/ # **产物**：由 kernel/sync_kernel.py 生成，勿手改
│   ├── engine/          # 推演引擎（第五〇八批升格）：_core.py 装卦入口、pipeline/ step1~5、classical/ 古籍增强族
│   ├── eval/            # 评测层（356 批起）：案例装载/评分/门户；scripts/ 同名文件为兼容 shim
│   ├── scripts/ data/ references/ dev_tools/ docs/ tests/
│   └── README.md  SKILL.md
├── bazi/                # 八字（独立）
│   ├── core/yishu_core/ # **产物**：同上（316 批起不再携带卦辞/纳甲/历法核对三个六爻专用模块）
│   ├── eval/            # 评测层（359 批起）：评测器实现；scripts/ 同名文件为兼容 shim
│   ├── scripts/ data/ references/ dev_tools/ docs/ tests/   # tests/ 335 批补建（smoke+regression）
│   └── README.md  SKILL.md
└── dsh-plugin/          # DSH 插件（Node 半，独立于两科；契约见下）
```

依赖方向单向：`<科>/engine → <科>/scripts(扁平模块) + <科>/rules + <科>/core`；
`<科>/scripts → <科>/engine + <科>/core`；`<科>/eval → <科>/scripts + <科>/engine + <科>/core`
（评测层可读 `data/cases`；交付路径不得反向 import `eval/`；门禁侧 `<科>/dev_tools → devkit/shared` 同理）。
**引擎族只走 `engine/_bootstrap.setup(__file__)` 定位；数据路径走各科路径真源**
（六爻 `kernel_path.data_path()`）——禁止按 `parents[N]` 硬算层级（507 批曾因此静默读到空表且门全绿）。
**两科之间禁止任何相互 import**，也不存在合参层（`synthesis` 已移除且不得复活）。
两科 `core/` 与 `dev_tools/` 里的共享件都是**生成产物**（316／334 批起）——手改即被
`[35]`／`[37]` 字节比对判红；改内核改 `kernel/`，改共享门改 `devkit/shared/`，再跑
`--write`。这是"零耦合、各自可独立运行"的刻意结果，不是待修的重复。

**门禁内核真源（第三百三十四批）**：11 个同名门/器已归并——7 个进 `devkit/shared/`
单一真源，4 个因两科逻辑不同按 kernel 变体范式登记（`devkit/MANIFEST.json` 的
`variants` ＋ `variant_reasons`）。**第四百三十三批新增第 12 个共享件
`check_source_provenance`（底本完整性门 [42]）**：provenance 的
sha256/bytes/chars/lines＋扩展统计（`ganzhi_pairs`／`tables`／`headings`）＋登记元数据
（`page_count`／`eol_on_disk`／`sha256_lf_text`）＋已登记双口径行数（`lines_nonempty`／
`lines_physical`）须与在盘底本逐项相符，「在库书源」台账表（含干支对／标题两列）同源
（442–445 批逐轮扩面，定义均由全仓登记值逐格复算反推）；首跑即抓到《火珠林》wikitext
的 CRLF→LF 失配与两份旧册缺 source_file。`data/cache/`（337 批）收所有评测/构建生成物，
整目录 gitignore，清掉即由脚本现场重生。

**文档地图（第三百三十批新增；第五百一十四批去钉数）**：根 `DOCS.md` 是全仓 Markdown 的总索引——
每份文档一句话职责 ＋ 状态（活文档／生成物／归档留证／历史索引）＋ 三条阅读路径。
**份数不在本文写死**（330 批立文时钉「51 份」，510 批减量后该行即成假事实，而索引门只查
「每份是否登记＋登记的路径是否可达」，不查句子里的总数，故没有任何门能拦到它）——
以 `python devkit/root/check_docs_index.py` 的实跑首行为准（该门计数口径是「tracked `.md` 减
`DOCS.md` 自身」）。
**新增文档必须同批在 `DOCS.md` 登记一行**，不登记等于没有。历史记录（CHANGELOG 归档）
自 342 批起**以逐批一句话索引为主，不再保留全文**：索引只压缩、不改事实，**批号与日期
必须保留**（`readout_ledger` 的「登记×提交」扫它）；索引里指向当年临时文件的旧路径按
「登记时点事实」豁免（`check_doc_refs` 的 EXEMPT 已同步）。

**四段契约的判据是根 `CONTRACT.md`**（第三百一十批重建；此前 5 个模块 docstring 引它
而文件已随扁平化丢失）。`chart → analyze → narrate → render` 的职责、四条不许越的界、
层间调用矩阵与各段输出键白名单都在那里；机器判据是各科 `data/rules/domain/layer_contract.json`，
门是各科 `dev_tools/check_layer_contract.py`（六爻 `[32]`、八字 `[28]`，第三百一十批同时挂上）。
**改层界 = 同批改 CONTRACT.md + JSON + CHANGELOG**，三者不同步即算缺陷（§六.3）。
引用它时写节号，不写裸编号（同 §一 沿革条的口径）。

**「零耦合」的口径（308 批定级，此前未定义，导致同一句话两种读法）**：
  1. **无 import**：两科之间不得有任何 `import` 与 `sys.path` 越界引用（AST 级扫描，账台有断言）；
  2. **无跨科写**：某一科的脚本**不得往另一科的目录里写任何文件**（含 `scratch/`——
     被 gitignore 不脏树，但仍是跨科副作用）。跨科**只读**（统计、探针、对拍）允许，
     但必须在调用处写明"跨科只读"，且产物一律落系统临时目录。
 两科 `core/yishu_core/` 的 17 个同名文件中 13 个曾**逐字节相同**（308 批 `cmp -s` 实测，
 仅 evidence/ming_tables/shensha/symbols 4 个分叉）。**316 批起口径改写**：内核收进
 `kernel/`（10 个共用 + 3 个六爻专用 + 1 个八字专用 + 4 个在册变体），两科 `core/` 降为
 **生成物**，由 `kernel/sync_kernel.py` 写、由 check 的 `[35]` 比对字节。因此：
 ① "零耦合"仍指**运行时**不跨科 import、不跨科写，与源码是否同源无关；
 ② 改内核一律改 `kernel/`，**直接改 `<科>/core/` 会被 [35] 判红**；
 ③ 两科不再"各自演进"同一份代码——变体只有 4 个，且理由写在 `kernel/MANIFEST.json`。

### plugins 共享打包层契约（2026-10-27 第三百零五批起；497 批起仅保留 DSH 宿主）

`plugins/` 是两科对外分发的**唯一共享层**；`dsh-plugin/` 只保留**宿主专属文件**
（`package.json`、`src/index.mjs`、`presets/`、README/CHANGELOG）。
497 批起 claude/codex/gemini/yan 四家适配器已删除——不再有多份产物、多条漂移面。

```
plugins/
├── SKILL.md             # 技能正文唯一真源（入库）
├── mcp/                 # 共享运行时唯一真源（入库）：server/schema/tools/engine/kb/report/python + 同义词表
├── scripts/             # kb-docs.mjs（登记表真源）、build.mjs（一次构建 + 分发）、selftest.mjs
├── engine/  skills/     # 构建产物（不入库）
└── CHANGELOG.md
```

- **一次构建、分发到 DSH**：`node plugins/scripts/build.mjs` 从两科收集 `plugins/engine/`
  与 `plugins/skills/`，再按 `scripts/build.mjs` 的 `ADAPTERS` 登记表分发到 `dsh-plugin/`。
- **适配器的 `src/*.mjs` 是产物**：手工改即被自检 [1] 段（逐字节同源门）判红。
  宿主专属入口（dsh 的 `src/index.mjs`）例外，仍为源码并已显式 negated 入库。
- **`engine/`、`skills/` 不入库**。发布走 GitHub Release 的 npm tgz（`npm pack`），
  不再有独立发行树（`publish.mjs` 随四家 git 通道宿主一并删除）。
- **1.0 API 冻结（277 批起，1.0.0 生效）**：对外契约冻结为
  四工具 `yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report` 的**工具名、参数 schema、输出
  value 结构**（含文本块形状）与技能条目 `yi-divination`。1.0 后：新增可选参数/
  新增输出字段 = minor+1；改名、删字段、改字段语义 = 破坏性，跨 1.0.0 并在 CHANGELOG
  单独声明旧读数不可比。自检 [5] 段是冻结面的机械面——动它必须先动本条。
- **口径**：面向会话交付，分数口径同 §一.3，不得出现"预测准确率"类表述
  （自检 [7] 段逐行扫描，含否定语境豁免与负例自证）。
- **月巡挂钩**：对两科 `references/`、`core/`、`scripts/` 的任何例行巡查
  （含月巡），末尾跑一次 `node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs`，
  再补跑 `npm --prefix dsh-plugin run check`（宿主侧 QA）——共享层与宿主面两条都要。
- **批次登记**：共享层进 `plugins/CHANGELOG.md`；宿主侧那点事进 `dsh-plugin/CHANGELOG.md`。
  批次号沿用全仓流水。
- **版本号纪律（275 批起）**：`package.json` 的 semver 只是粗粒度坐标，**批次号是唯一真源**。
  功能批 minor+1、修复/文档批 patch+1、破坏性跨 1.0.0 并单独说明；映射表逐批补记在
  `dsh-plugin/CHANGELOG.md`。

#### DSH 宿主硬约束

| 清单 | 能力声明面 | 本地 MCP 命令 | 已知硬约束 |
|---|---|---|---|
| npm `package.json` + `src/index.mjs`（Cordis `ctx`） | `ctx.tools.register` / `skills.registerProvider` / `systemPrompt.section` | 宿主注入 | `inject` 必须声明 `tools`/`systemPrompt`；skill `invocation` 必须是**对象**、`rank` 必须是有穷数字，漏则整轮会话 error 结束 |

### 内核唯一真值源（科内口径）

以下数据**在同一科的 core 内只存在一份**，该科脚本层不得复制：
天干地支、五行阴阳、六合六冲三合三刑六破、十二长生、墓库、旬空、六十四卦卦表、
八宫归属、纳甲支表、卦辞爻辞、干支历换算、调候用神表。

历史教训：同一批表曾在三个文件里各存一份且取值不一致；EIGHT_PALACES 三份不一致
（兑宫世次排错）是真实事故。新写规则表先确认该科 core 里没有；没有就加进该科 core，
不要就地新建第二份。

**写提取器/正则的现行硬性注意**：内核 `HEAVENLY_STEMS`/`EARTHLY_BRANCHES` 是 **list**，
插进正则字符类前必须 `"".join(...)` 展平。`[%s] % 列表` 会把 `['甲', '乙', …]` 的
括号引号当字面量，正则**永不命中且无报错**——`liuyao/dev_tools/build_yingqi_set.py`
曾因此静默全盲（2026-10-13 抓到并修复；同仓 `case_runner.py`、
`build_zengshan_dz_cases.py` 一直用展平写法，可作范式）。

### 数据缺陷 vs 引擎缺陷（读数不对时，先判责任方再动手）

是引擎错了，还是 expected/引文错了？手段：`git show HEAD:<file>` 抽旧表与当前逐格对拍
（范式 `bazi/dev_tools/diff_tiaohou_vs_head.py`）。

- **禁止按读数改数据**——把 expected 改成迎合引擎，等于用调参掩盖缺陷，
  且会让「分数」失去意义（同 §一.3 与 §三.4）。
- 案例库的 `source_quote` **必须是书源逐字子串**，否则违反「引文可指回原文」。
  机械门：各科 `dev_tools/check_source_readings.py`（书证引文逐字回验小节）。
  ⚠ 逐字要求不止案例库：任何「照录」字段一律不改字、不转简（这一条在
  `bazi/data/liushen_image.json`、`bazi/data/nayin_quxiang.json` 等数据注记里
  被称作「铁律一／铁律二（照录义）」，指的就是本条）。
- **月令 ≠ 月支**：正月建寅，故 6 月为**未**、午月为**五月**。改调候表前先核月支，
  勿把「午月案例」与「6 月（未）那一格」混为一谈。

## 三、命名与文件规范

| 规则 | 禁止 | 要求 |
|------|------|------|
| 文件名 | `run_blind_v5.py`、`HANDOFF_V8.md` | 名字不携带版本；版本走 git 与 `<科>/docs/CHANGELOG.md` |
| 调试脚本 | `data/cases/_patch_xxx.py`、`_debug_yyy.py` | 一次性脚本放各科 `scratch/`（**整目录不入库**：`.gitignore` 的 `scratch/` 无斜杠锚定，同时覆盖仓库根与两科内） |
| 产物 | `outputs/`、`*.html`、`*.jsonl` 入库 | 全部生成物 gitignore，需要留存样例的进 `docs/` 并说明 |
| 入口 | `sys.argv` 手解、无 `--help` | 每个 CLI 用 argparse，`--help` 可看，失败退出码非 0；中文入口必须自带 UTF-8 守卫（见 §四.9） |
| 路径 | 硬编码 `C:\Users\<name>\...` | 相对学科根解析，或用显式参数 |
| 断语字面量 | 在 .py 里堆砌上千条中文断语 | 断语/引文/卦辞进 `data/*.json` 或 `references/*.md`，代码只留算法 |

### 3.4 禁止用引擎输出反推 expected（数据侧核心纪律）

`expected`/基准值的每一项都要能在**书源逐字引文**或该书同节的表里找到依据；
**不许由引擎输出回填基准**——那会让读数自证，100% 的分数说明评测集与引擎同源。
机械配套：各科「基准自洽」门（`check_case_pillars.py`／`check_case_selfconsistency.py`）、
「书证引文逐字回验」门（`check_source_readings.py`）。
**定义式维度的例外**：当某维度在评测规范里被定义为"表驱动、唯一解"（如十神、藏干），
允许由案例**已存的书载真值**经规范定义函数机械派生回填（书载四柱→`relations.ten_god`
→期望），这与"由引擎判读反推"不同——派生只碰定义表，不碰强弱/格局/吉凶判读。

## 四、修改引擎的验收门槛

任何改动 `core/` 或学科层推演逻辑的提交，必须：

1. 跑 tune 与 holdout 两个集合并**分别出分**，禁止把 holdout 混进 tune 均分冒充提升。
2. tune 均分无故跌破基线即视为回归，停止合入（各科基线在 `dev_tools/check.py` 的
   `baseline` 表里，只准前进）。
3. 修复某类错误时，改**通用规则**并说明其古籍出处；**禁止为让某个案例过关而写
   私有别名或 case-specific 分支**。外部集只报数、不设门槛，**不得为过外部集写私有规则**。
4. 指标口径变了（计分方式、词典、缺失字段处理）必须在 `<科>/docs/CHANGELOG.md` 写明，
   并声明**新旧读数不可比**；否则分数失去意义。
5. **逐格对拍证明「真改进」**：改静态表/提取器前后，用 `git show HEAD:<file>` 抽旧表
   与新表逐格比对，报「新增 N 格 / 变空 N 格 / 改值 N 格」——**「变空」与「改值」
   必须逐条解释**。范式：`bazi/dev_tools/diff_tiaohou_vs_head.py`、
   `liuyao/dev_tools/diff_jingshi_vs_core.py`／`diff_shangzhan_vs_core.py`。
   只报「新覆盖了几格」会掩盖悄悄回归。
6. **静态表与 data 层不同源时用同步脚本，不手改**：引擎表是字面量、data 是产物，
   手改必漂移。改完跑该学科的同步脚本 `--check`（`bazi/dev_tools/sync_tiaohou_engine.py`、
   `bazi/dev_tools/sync_nayin_engine.py`），并把它挂进可跑的门。
7. **外部集读数持平不构成「修对了」的证据**：若本轮改的格在外集里没有对应案例，
   读数本就不该动。须明确写出「读数不动属预期」，不得拿持平当成果。
   反之读数变好时，须先排除「改数据/改 expected 凑分」（见 §二"数据缺陷 vs 引擎缺陷"
   与 §三.4）。
8. **新挂的门必须做负例自证**：往文档/数据里塞一个**明知不存在**的目标
   （文件名用单下划线，如 `docs/` + `_no_such_probe` + `.md` 拼出的那一个），
   确认门真的判红（EXIT≠0）并报出明细，再撤掉。
   **全绿的新门先怀疑、再证明**——2026-10-06 实踩：死链门挂完是「全绿」的，
   实为豁免逻辑把负例一起吞了（`Path.glob()` 返回 generator、真值恒 `True`）。
   任何「0 结果」都要先确认不是路径解析错了（扫了 0 份文件 ≠ 仓库没文档）。
   文档里**举例用的假路径一律用 `__` 双下划线前缀**（约定见各科
   `dev_tools/check_doc_refs.py` 的 `NEGATIVE`），死链门只豁免这类——
   单下划线仍是真死链，照样判红。
9. **中文 CLI 编码红线**（2026-10-12 起两科上门）：凡带中文的命令行入口，在
   cp936 控制台下必须交出可读 UTF-8 产物；守卫（`sys.stdout.reconfigure(...)`）
   写在**入口文件自身**，`dev_tools/check_cli_encoding.py` 静态判据＋`--help` 产物
   行为判据双重拦截。rc 为 0、分数与金标准都看不见 GBK 退化——只有这条门管得住。

## 五、一卦一事

同一问题不重复占卜（"再三则渎"）。用户在既问之后换实质角度提问（换用神、换层面、
假设未来、比较两人、测人心）——应提议另起一卦，不得在原卦里延伸硬推。
超出用神覆盖域的断言（对方家庭背景、未来伴侣身份、心里想什么）属臆测，不讲。

## 六、已知问题与文档说明的台账纪律（本仓库的"清空"口径）

1. **一切登记进 `<科>/docs/CHANGELOG.md`，逐批具名**：不另建 TECH-DEBT/OPT 台账文件
   （`docs/TECH-DEBT.md` 已随扁平化删除，其 §2.3／§2.7／§2.11 等节号**不再存在**，
   活引用一律改指登记批次或现行门）。
2. **改实现必须回头改登记**——改了判据而注释还写「未实现」、修了缺陷而台账还写
   「待修」，登记就从待办变成了**假事实**（本仓反复清除的正是这一类）。
3. **文档说的和代码做的不一致，本身就是已知问题**，优先级等同代码缺陷：
   以实跑读数改正文档，不许以旧文档"计划"代码现状。
4. 数标记（`待办|待补|待裁|欠账|未实现`）命中数 ≠ 真欠账数：逐条看语义，
   排除断事文案（如「月破待补」是判词不是待办）与回验器自己的 META 词表。
5. **诚实结案**：方向能由书确定的即解决；实证证明不可改进的不强改，
   把"为什么不实现、缺什么前置"写清后结案登记——不留说不清的读数，
   不留半接的代码，也不拿私有规则去凑外部集。
6. **现在时文案不钉会变数**（第五百一十四批把 GOVERNANCE.md §精神条款 上提为全仓规程）：
   文档里「现在有 N 份／N 个脚本／新门从 `[N]` 续」这类现在时数字，一律改写**取数命令或真值源**，
   不抄快照——抄一次就多一块没人对的表，因为所有文档门只判「路径是否可达」，不判句子里的数。
   514 批实见的四例同源病：330 批钉「DOCS.md 索引 51 份」在 510 批减量后成假事实；
   GOVERNANCE.md 的治理分布表停在 344 批（64／43）而实跑 74／49，同节第一句却写「不抄旧快照」；
   ARCHITECTURE-PLAN.md §五.2「`files.shared` 仍为 11 项」与该文件 §一 D2 行的 12 项互相打脸；
   同文 §六.4「新门从 `[37]` 续」挂着时，六爻实跑尾号已是 `[44]`。
   机器侧已有断言的数（如 `readout_ledger` 的 `governance(总数, blocking)`、`devkit/MANIFEST.json`
   的 `files.shared`）更该指过去而不是复述。
