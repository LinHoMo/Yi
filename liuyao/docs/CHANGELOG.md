# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。

## 2026-11-04 第五百零九批（六爻·台账指针回改）：**判据台账 42 处旧代码路径指针改回真实落点，行号随盘重算 25 处；`chart.py` 去冗余别名，`CONTRACT.md` 改按目录记段——纯指针与文档，golden 双指纹零漂移**

**性质**：指针口径修正（判据值一律不变；读数不动属预期，见 §四.7）。

### 一、决定反转（505 → 509，写明理由）

- 第五百零五批的在册决策是「**台账不回改、转发在判据侧**」，故 508 升格后台账里
  `scripts/engine/**`、`scripts/classical/**` 一类旧指针仍由 `check_rule_registry._partition_remap`
  四类转发兜住。本批经**用户裁定**改为回改：升格已定稿、落点不再动，指针与磁盘一致比
  靠转发兜底更可查；台账里「写的是哪一行」从此可直接 `git blame` 回验。
- **转发逻辑不删**：`_partition_remap` 与 `_PATH_RE` 的 `engine` 前缀保留作双保险
  （旧指针若被再引入或被外部工具带入，仍能回指，不会当场判红掩盖真错）。
- 台账不再是「冻结物」：本批起它与代码同步维护，改落点即同批改指针。

### 二、回改范围（42 处路径前缀，一处一类可核）

| 文件 | 处数 | 形如 |
|---|---|---|
| `data/rules/legacy/rule_registry.json` | 41 | `scripts/stepN.py` → `engine/pipeline/stepN.py`；`scripts/classical_enhancements*.py` → `engine/classical/classical_enhancements*.py`；`liuyao/scripts/…` 同规则带前缀 |
| `data/rules/domain/qianjin_fu_map.json` | 1 | 同上（`scripts/step3.py::compute_day_modifier`） |

- **只动路径前缀**：行号、符号名、引文、`verified`、`gap_detail` 等判据内容一字未改。
- **扁平模块不碰**：`scripts/effects.py`、`scripts/classical_analysis.py`、`scripts/timing.py`、
  `scripts/narrate_core.py` 仍在 `scripts/` 下，保持原样（这是升格后的正确落点，不是漏改）。
- 改写用一次性脚本 `scratch/repoint_ledger_to_engine.py`（JSON 树内逐字符串替换，幂等，
  重跑报「0 处」）；产物 diff 逐行核过：38 行路径 + 4 行含行号，无其他字段变化。

### 三、行号随盘重算（25 处，全部逐条报「登记值 → 实际值」）

1. **符号锚 17 处**（`符号(数字)` 形态，用 AST 取定义行，仅当符号确实存在于目标文件才改）：
   `effects.py:analyze_repetition 786→880`、`analyze_repetition_deep 914→1008`、
   `analyze_clash_harmony 697→791`、`analyze_officer_tomb 264→317`、`analyze_three_punishments 1215→1309`、
   `analyze_six_breaks 168→221`；`classical_enhancements.py:analyze_advance_retreat 1298→1390`、
   `analyze_triple_combo 1508→1597`、`find_hexagram_body 466→518`、`analyze_monthly_break 1185→1276`、
   `analyze_hidden_movement 986→1072`、`analyze_desperate_relief 1813→1902`、
   `analyze_hidden_spirit_emergence 763→895`、`analyze_twelve_growth 1707→1790`；
   `step2.py:step2_identify_use_god 57→64`、`_find_use_god_positions 556→696`；
   `timing.py:predict_timing_core 733→1152`。
   **其中 `effects.py`／`timing.py` 那 7 条是 508 之前的旧漂移**（这两个文件本轮没搬过），
   一并修正，不留「同册两种精度」。
2. **纯行号锚 6 处**（无符号名，按相邻描述在盘上定位后改）：
   `step3.py:196-198 极旺／旺两档` → `engine/pipeline/step3.py:241-246`；
   `step3.py:199-201『相』位上调（_xiang_bump）` → `:239`；
   `step3.py:653-660 月破修正` → `:764-800`；
   `step3.py:583 真空/假空` → `:750`；`step4.py:1058 check 3b 三会` → `:1174`；
   `timing Rule 8(615)/Rule 9(672)` → `Rule 8(1015)/Rule 9(1080)`。
3. **生成器内锚 2 处**：`dev_tools/build_adjudications.py` 的
   `xunkong_zhenjia → step3.py:583` 改 `:750`、`six_breaks → step5.py:615-619` 改 `:621-640`
   （后者原指腾蛇文案行，实为 5.5e 六破段），并重跑该构建器；产物
   `data/rules/domain/adjudications.json` 变化仅 `built_at` 与这两条锚。
- **刻意不改**：`verification_note_zengshan_2026_10`（L136）与 `effects.py:656-664` 里的行号
  属 **2026-10-07 的核查记录**（登记时点事实，不是当前指针），按 §六 台账纪律保留原值；
  纯行号锚无门可判，其准确性靠本批这次的逐条人工定位维持。

### 四、另两项（本轮一并清掉）

1. `scripts/chart.py`：`import engine as engine` → `import engine`。别名冗余（模块名本来就叫
   `engine`），去掉后属性访问（`engine.random` / `engine.handle_zi_hour` /
   `time_based_hexagram` / `number_based_hexagram`）语义不变，已由 chart 冒烟用例覆盖。
2. 根 `CONTRACT.md` 由**模块名前缀**改**按目录**记段：
   - §二-bis 六爻行：`step1.py`–`step5.py` → `engine/pipeline/step1.py`–`step5.py`，装配写 `scripts/chain_assembly.py`；
   - §三 层间矩阵 ASCII 图改为「`core ← engine/**`（推演）＋ `core ← scripts/**`（机械/数据/叙述/呈现）」，
     并加一段「目录口径（508 升格后，509 写入本节）」说明模块名与 import 名未变；
   - 允许表新增四条：`engine/** → core`、`engine/** → scripts/**(扁平模块)`、`scripts/** → engine/**`；
   - §二 通用边界「`core/**` 不得 import」补 `engine/**`；禁边表首行改 `engine/pipeline/step1..5`。

### 五、验证

- `python liuyao/dev_tools/check.py` → 质量门全部通过（含 [12] 规则台账指针回验：全部 `impl`
  文件在盘、符号可达；`[33]` 判定表；`[20]` 中文 CLI；`[1]` chart 冒烟）。
- `python dev_tools/golden.py` → 288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0，**与基线逐位一致**。
- `python bazi/dev_tools/check.py` → 通过（本科数据未动）；`devkit/sync_devkit.py --check` → 12 共享件一致。
- 根级三门：`check_root_docs.py`（`CONTRACT.md` 改动后 0 死链）／`check_docs_index.py`／`check_batch_num.py`。
- 交付面重跑：`node plugins/scripts/build.mjs` → `selftest.mjs`（`data/rules` 随包，指针不参与运行，包体不变）。

### 六、边界

- 台账从此**与代码同批维护**；若再搬落点，改指针是本批之后的标准动作，不再依赖转发。
- `_partition_remap` 保留（双保险），注释口径写明「509 起为兜底，非唯一通道」不另改。

## 2026-11-04 第五百零八批（六爻·engine 升格）：**`scripts/engine/`＋`scripts/classical/` 升格为 `liuyao/engine/`（与 `scripts/` 平级），16 处调用侧与 6 个共享门同步扩面——纯搬迁，golden 双指纹零漂移**

**性质**：目录升格（判据不变、读数不变；`engine/` 是 505 批蓝图的最终落点，D3/D4 至此合流）。

### 一、搬迁与落点

1. `git mv liuyao/scripts/engine liuyao/engine`、`git mv liuyao/scripts/classical liuyao/engine/classical`；
   `scripts/` 下已无子目录。`engine/` 现状：`__init__.py`／`__main__.py`／`_core.py`／`_bootstrap.py`／
   `pipeline/`（step1~5＋`_step5_{dates,factors,timing,weather}`）／`classical/`（8 个 `classical_enhancements*`）。
   **模块名、import 名一律不变**，`from engine import …` 仍是全仓统一公开入口。
2. 新建 `engine/_bootstrap.py`：`setup(start_file)` 在盘上**向上搜 `scripts/kernel_path.py`** 定学科根
   （不按层数硬算），把「本目录／`scripts`／`rules`／学科根」入 `sys.path`，再交给
   `kernel_path.ensure_kernel_on_path`。17 个 engine 文件的路径块统一改为调它一份实现。
3. `scripts/kernel_path.py`：导入时即把学科根入 `sys.path`；`ensure_kernel_on_path` 同步加学科根
   （调用方只要 `import kernel_path` 就能解析到 `<学科根>/engine`）。
4. 调用侧 16 处逐点改基准（均按「学科根在路径上」或「engine 子目录在路径上」两种手段）：
   `scripts/{chart,analysis_steps,effects,thinking_chain,classical_analysis}.py`、
   `eval/case_runner.py`、`dev_tools/{ablation,use_god_coverage,build_extra_dimensions,build_usegod_position,check_bing_yao,check_judgment_table,check_xiang,prospective,readout_ledger,check_bond_polarity}.py`、
   `tests/{smoke_test,regression_test,thinking_chain_tests,six_god_wang_shuai_test}.py`。

### 二、判据与扫描面（升格最容易被"悄悄退出扫描"的一面，逐处点名）

- `devkit/shared/check_rule_registry.py`：`_partition_remap` 的旧指针转发扩为四类
  （`scripts/classical_enhancements*.py`→`engine/classical/`、`scripts/classical/**`→`engine/classical/**`、
  `scripts/step*.py`→`engine/pipeline/`、`scripts/engine/**`→`engine/**`），**仍只在实体在盘时生效**；
  `_PATH_RE` 前缀集加 `engine`；「源L 锚」与「逐字引文回验」两处扫描根各加 `DISC/"engine"`。
- `devkit/shared/check_layer_contract.py`：禁边 import 图加入 `engine/**/*.py`（原只扫 scripts＋core）。
- `devkit/shared/check_case_isolation.py`：交付路径扫描面由 `scripts/` 扩为 `scripts/`＋`engine/`。
- `devkit/shared/check_cli_encoding.py`：`ROOTS` 加 `engine`（随之抓到 `engine/__main__.py` 缺 UTF-8 守卫，已补）。
- `devkit/shared/check_doc_refs.py`：BARE 路径正则前端集加 `engine`（文档里写 `engine/...` 的死指针同判红）。
- `devkit/shared/variants/check_source_readings.liuyao.py`：`GLOBS` 加 `engine/**/*.py`（书证逐字回验面）。
- 六爻自有机门：`check_verdict_external.py` 扫描改 `scan(scripts, engine)`；
  `check_xiang.py` 评分侧名单改 `engine/pipeline|classical/...` 且解析处「scripts/ 与学科根两处都试、
  都没有才判红」；`readout_ledger.py` 零随机 glob 换 `engine/pipeline/*.py`＋`engine/classical/*.py`＋
  `scripts/classical_analysis.py`（原 `scripts/classical*.py` 会整族漏扫）。
- 判据数据两份随落点动：`data/rules/domain/layer_contract.json` 两条 `edges.forbidden` 的 `from`
  改 `engine/pipeline/step5.py` / `engine/pipeline/step*.py`；`data/rules/domain/judgment_table.json`
  的 20 处 `overrides.line` 按 step5 新行号重算（**按 AST 清单顺序配对**，不按固定 delta 加减），
  `dev_tools/build_adjudications.py` 的 15 处散文 `engine_anchor` 改 `engine/...` 并重跑该构建器
  （产物 `adjudications.json` 仅 `built_at` 与 15 条锚点变化）。
- 分发面：`plugins/scripts/build.mjs` 的 `RUNTIME_INCLUDE.liuyao` 加 `'engine'`——漏收则包能装、调用即 ImportError。

### 三、实踩的四个坑（都已修，均属"门全绿但功能断了"类）

1. 路径块重写把 `step5.py` 里「向上搜 `rules/`」那段一并删掉 → `from direction import …`
   `ModuleNotFoundError`。修法：该步收进 `_bootstrap.setup`（`<学科根>/rules` 入路径），不再逐文件写。
2. `pipeline/*.py`、`classical/*.py` 只把自身目录入路径，`from _bootstrap import` 直接失败
   （`scripts/analyze.py`、`check_bing_yao.py`、六神单测三处实测）。修法：各文件先把**上层**（`engine/`）
   入路径，再导入 `_bootstrap`。
3. `step3.py` 的 `import labels_loader` 落在路径块之前 → `scripts/` 还没上路径就炸。修法：路径块整段上移
   到 `from __future__ import annotations` 之后（17 个文件统一）。
4. 承 507 批：`classical_enhancements_fushi` 的 `from kernel_path import repo_root as _repo_root`
   随块替换被抹掉 → `_repo_root` NameError。修法：导入行显式补回 `_ks_setup` 之后。

### 四、验证（全绿，读数零漂移）

- `python liuyao/dev_tools/golden.py` → 288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0，**与基线逐位一致**。
- `python liuyao/dev_tools/check.py` → 质量门全部通过（含 [20] 89 个中文 CLI 入口、[27]/[30]/[32]/[33]/[39]/[40]）。
- `python bazi/dev_tools/check.py` → 通过；`python devkit/sync_devkit.py --check` → 12 共享件逐字节一致。
- 根级三门：`check_root_docs.py`（7 份文档、119 条引用、0 死链）／`check_docs_index.py`（44 份全登记）／
  `check_batch_num.py`（未结案孤儿 0）。
- 分发：`node plugins/scripts/build.mjs` → `selftest.mjs` 全绿（包体 201 文件／2.93MB、**yi_liuyao 引擎冒烟
  以构建产物跑通出「贲」**——打包侧唯一端到端证据）。

### 五、边界（未做与已知）

- 旧路径**不留 `scripts/` 桩**：转发走判据侧 `_partition_remap`（四类，实体在盘才生效），
  台账（`legacy/rule_registry.json`）34 处旧指针按 505 批决策**不回改**。
- `scripts/chart.py` 的 `import engine as engine` 保留（同名变量沿用，导出语义未变）。
- 本批只动落点与扫描面，**不动任何推演判据**：读数不动属预期（§四.7）。

## 2026-11-04 第五百零七批（六爻·D2/D4 数据路径静默缺陷）：**`classical_enhancements_fushi` 按层数硬算表路径，迁入 `scripts/classical/` 后落到不存在的 `scripts/data/`，被 `except OSError` 吞成空表——九宫伏藏标签整族静默消失且所有门全绿**

**性质**：缺陷修复（判据不变；读数不动属预期，见 §三）。

### 一、缺陷与取证

1. `scripts/classical/classical_enhancements_fushi.py` 的 `_DATA` 原写
   `Path(__file__).resolve().parents[1] / "data" / "rules" / "domain" / "caiguan_fushi.json"`。
   D2 把表迁进 `domain/`、D4 把本文件从 `scripts/` 迁进 `scripts/classical/` 之后，
   `parents[1]` 由「学科根」变成「`scripts/`」，于是路径落到
   `liuyao/scripts/data/rules/domain/caiguan_fushi.json`（不存在）；`_table()` 里
   `except OSError: _TABLE = {}` 把它吞成空表 → `FU_SHI_PAIRS()` 返回 `{}` →
   `huozhulin_fushi_tags()` 第一行就 `return []`。**九条财官伏五乡标签整族消失，且无任何报错。**
   实测取证：`len(FU_SHI_PAIRS()) == 0`（在盘表实际 9 条：妻财伏官鬼／妻财伏兄弟／妻财伏父母／
   妻财伏子孙／官鬼伏兄弟／官鬼伏妻财／官鬼伏父母／官鬼伏子孙／官鬼伏官鬼）。
2. 为什么既有门全绿：`golden` 只封 chart 段排盘指纹（288 例不漂移属预期）；计分维度不消费该标签；
   `check_*` 各门只查书证、结构、契约，**没有一条判「数据表是否真被读进来」**。
   这与本仓 2026-10-13 的 `build_yingqi_set` 正则静默全盲同类：路径/提取器错了，门照样全绿。

### 二、修法

1. 路径改走仓库唯一路径规则 `kernel_path.repo_root(__file__)`：
   `_DATA = Path(_repo_root(__file__)) / "data" / "rules" / "domain" / "caiguan_fushi.json"`。
   **不再按层数硬算**——本轮同时把 `scripts/engine/`＋`scripts/classical/` 升格到 `liuyao/engine/`
   （见第五百零八批），该行在两种布局下都必须解析到同一个 `<学科根>/data/rules/domain/`，
   只有 repo_root 这一种写法成立。
2. `_table()` 改 fail-fast：表文件不在盘即 `RuntimeError`，消息里写明期望位置与
   「路径须走 kernel_path.repo_root，不按层数硬算」；删掉 `except OSError: _TABLE = {}`。
   `FU_SHI_PAIRS()` docstring 的「缺表返回 `{}`」改为「表缺失即报错」——同批把
   「静默退化成空表」这条路彻底关掉，避免下一次搬迁再复现。
3. 文件头 docstring 里 `data/rules/caiguan_fushi.json` 的指称同步为 `data/rules/domain/...`（D2 分区后事实）。

### 三、验证

- 行为级自证（`scratch/` 一次性探针，不入库）：合成 `flying_hidden_interaction` 三组飞伏 →
  `妻财伏官鬼` 出「财伏鬼乡」`src=huozhulin_dz.dz.txt:56`；`官鬼伏兄弟` 出「用鬼伏兄」`:72`；
  `父母伏子孙` 不在九宫九组内 → 正确跳过。修复前同一探针 `标签数= 0`。
- `python liuyao/dev_tools/check.py` → 质量门全部通过；`python dev_tools/golden.py` →
  288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0，与基线逐位一致。
- **读数不动属预期**（§四.7）：该标签不在任何计分维度内，修复前也没有案例因它失分，
  故 tune／holdout 与哨兵读数本就不该动；本批恢复的是 analyze 输出的结构标签本身。

## 2026-11-04 第五百零六批（六爻·D3 收编补登记＋D2 分区后文档路径收口）：**`scripts/engine/` 收 step1~5（提交 6101072 补登记）；`data/rules/` 分区后 22 处文档路径同步到 `domain/`／`legacy/`——纯文档与路径，零读数变化**

**性质**：登记补齐＋D2 收口遗漏（§六.1／§六.3）；不改判据、不改读数。

### 一、D3 收编补登记（提交 6101072）

1. 事实（该提交的内容，本批不再改动代码）：`scripts/step1~5.py` 与 `_step5_{dates,timing,weather,factors}.py` 迁入 `liuyao/scripts/engine/pipeline/`；`scripts/engine.py` 折叠为 `scripts/engine/_core.py`；`scripts/engine/__init__.py`、`__main__.py` 承接入口；外部引用方加 `scripts/engine` 的 `sys.path` 转发（`scripts/analysis_steps.py`、`eval/case_runner.py`、`dev_tools/` 若干），包导入语义不变。
2. 该提交**未写批号、未在 CHANGELOG 登记**——违反 §六.1「一切登记进 `<科>/docs/CHANGELOG.md`，逐批具名」。本批补登记，批号依蓝图 §六 D3 行取 506（与 `RULE-ENGINE-REFACTOR-PLAN.md` §六 表述一致）。
3. 落点现状如实登记：蓝图原写 `engine/`，实际收在 `liuyao/scripts/engine/`（与 D4 的 `scripts/classical/` 同层）；`scripts/engine/`＋`scripts/classical/` 升格为 `liuyao/engine/` 仍属**未启动**项，不在本批冒充完成。

### 二、D2 文档路径收口（22 处／9 份）

1. 根级文档门 `devkit/root/check_root_docs.py` 在干净 HEAD 判红 1 条：`CONTRACT.md:150` 指向分区前的 `data/rules/xiang_layer.json`。逐条排查后同类残留共 22 处：
   - 根：`AGENTS.md`（§二 四段契约段的「同目录」表述同时改为「各科」，因根目录本无此文件）、`CAPABILITY.md`、`CONTRACT.md`（5 处：三件套分工、§四真值源、`judgment_table` 出处、§五 `*.json` 通配、§六 象层映射表）；
   - 六爻：`README.md`、`SKILL.md`（2 处 basis 出处）、`docs/ONTOLOGY-CARDS.md`（4 处代码锚点）、`docs/RULE-ENGINE-REFACTOR-PLAN.md`（§一 旧台账指称）、`docs/YI-KNOWLEDGE-GRAPH.md`（6 处现有文件列）、`references/odd_questions.md`。
2. 改法（逐字替换，不重排段落）：`data/rules/<f>.json` → `data/rules/domain/<f>.json`；`rule_registry.json` → `data/rules/legacy/rule_registry.json`；`<科>/data/rules/*.json` → `<科>/data/rules/domain/*.json`。**只改路径串，不改论断、引文、批号**；CHANGELOG 历史条目一字未动（§二 照录条）。
3. 与 505 批决策不冲突：legacy 台账**内部**旧指针仍不回改（转发在判据侧 `_partition_remap`），本批只收口**文档**侧，台账刻意保留登记时点原文。

### 三、自证

- `python liuyao/dev_tools/check.py` → 质量门全部通过；`python bazi/dev_tools/check.py` → 通过。
- `python liuyao/dev_tools/golden.py` → 288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0，与基线逐位一致（文档不进语义面）。
- 根级三门：`check_root_docs.py`（此前 1 条红 → 本次转绿）、`check_docs_index.py`、`check_batch_num.py` 全绿；`devkit/sync_devkit.py --check` 12 件同源。
- 分发面：`node plugins/scripts/build.mjs`＋`node plugins/scripts/selftest.mjs` 全绿（README/SKILL/references 的路径改动随构建进包体）。

## 2026-11-03 第五百零五批（六爻·目录分层蓝图 D2＋D4）：**D2 `data/rules/` 物理分区（legacy/ 旧台账、domain/ 领域表）接续收口；D4 classical_enhancements 族 8 文件收进 `scripts/classical/`——两批同册提交，纯搬迁零漂移**

**性质**：目录分层物理收编（§六 D2/D4）；不改判据、不改读数。接续上一会话的半成品（16 个文件已 git-mv、20 个文件路径串已改，但门禁未收口）。

### 一、D2 收口（data/rules/ 分区）

1. 上一会话遗留：`liuyao/data/rules/*.json` 已 git-mv 为 `domain/` 15 份＋`legacy/rule_registry.json` 1 份，但四处判据仍按旧扁平路径写，[37] 门禁同源×5、[12] 死指针×24 判红。
2. **legacy 台账内容不回改**（§二「旧 `rule_registry.json` 不物理删除、旧路径留转发」条的在册口径：转发在**判据侧**，不在台账侧）：
   - `devkit/shared/check_rule_registry.py` 新增 `_rules_file(name, legacy=)` 与 `_partition_remap(base, rel)`——旧扁平指针 `data/rules/<f>` 按名转发 `domain/<f>`（`rule_registry.json` 进 `legacy/`），**只在目标实体真在盘上时生效**，不掩盖真被删的文件。
   - `devkit/shared/check_layer_contract.py:42` 改自适应 `_RULES_FLAT/_RULES_DOMAIN`（六爻取 `domain/layer_contract.json`、八字扁平回落，两科同一份代码）。
   - `devkit/shared/check_doc_refs.py` 的 selftest 临时件按 domain/ 在盘自适应落位。
   - `devkit/shared/variants/check_source_readings.liuyao.py` GLOBS `data/rules/*.json` → `data/rules/**/*.json`（分区后递归，覆盖面只增不减）。
3. 改共享件后 `python devkit/sync_devkit.py --write` 重分发（上一会话手改两科产物副本造成的 [37]×5 漂移由同一次 sync 归正——产物手改即判红，真源只有 `devkit/shared/`）。

### 二、D4 收编（classical_enhancements 族 → scripts/classical/）

1. **落点修正（登记时点决策）**：蓝图 §六 写 `engine/classical/`，但 `engine/` 树是 D3 的前置（step 链未收编，单建 `engine/` 会出现「古典族在 engine/、主管道在 scripts/」的倒挂）。本批先落 **`scripts/classical/`**，D3 收编 step 链时两目录一并升 `engine/`。8 个文件 git-mv，**模块名不变、import 名不变**，靠 sys.path 转发（`scripts/classical/__init__.py` 写明此约定）。
2. **运行时转发**：7 个被搬文件（`_fangwei.py` 自身无 sys.path 代码、靠 importer 兜底）在各自 `_ks_d` 块后插父目录（scripts/）转发；7 个外部引用方（`scripts/classical_analysis.py`／`scripts/effects.py`／`scripts/thinking_chain.py`／`dev_tools/ablation.py`／`dev_tools/build_extra_dimensions.py`／`tests/six_god_wang_shuai_test.py`／`eval/case_runner.py`）把 `scripts/classical/` 加进 sys.path。注释一律标「D4 收编」。
3. **判据面同步（本批的真风险——静态名单会静默缩水）**：
   - `check_rule_registry.py` 的 `_partition_remap` 加 scripts/ 收编转发（`scripts/classical_enhancements*.py` → `scripts/classical/<f>`，同样**只在实体在盘时生效**）。台账 24 条旧扁平 impl/quote_in_code 指针不回改（D2 同策）。
   - `liuyao/dev_tools/check_xiang.py` 的 `SCORING_MODULES` 静态名单：8 个族文件名改带 `classical/` 前缀，且**「文件不在盘」由静默 `continue` 改为判红**——静默跳过＝「评分侧禁读象」覆盖面悄悄缩水（象层门 [39] 的牙被搬目录磨掉）。
   - `devkit/shared/check_layer_contract.py` 禁边 AST 扫描名单 `scripts/*.py` → `scripts/**/*.py`（同理：单层 glob 会让 `scripts/classical/` 下 9 个文件整体退出 import 图扫描面）。八字 `scripts/bazi_factors/` 包（相对 import，不触禁边表）与六爻族模块（无 narrate_core/chart 禁边目标 import）经实跑确认不因此新增红。
   - `build_adjudications.py` 两条 `engine_anchor` 散文指针与产物 `domain/adjudications.json` 同步重建（builder→data 同源，--verify 77 条书证全回验）。
4. **负例自证（§四.8）**：转发落地后逐探针复跑——`scripts/classical_enhancements.py:analyze_shen_yao_activation`（符号搬进 `_shen_yao` 子模块）仍判「符号不在该文件内」√；`scripts/classical_enhancements_nothere.py:foo` 仍判「文件不存在」√（[12] 门 selftest 在册负例同判）。**转发只搬路径，不磨判据的牙。**

### 三、自证

- 六爻全门：`python liuyao/dev_tools/check.py` → 质量门全部通过；八字全门：`python bazi/dev_tools/check.py` → 通过（共享件双科分发后各自全绿）。
- `golden.py verify`：288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0——**与基线逐位一致，零漂移**（搬目录不进语义面，此为机器证明）。
- `tests/regression_test.py` 总通过 19/19；`smoke_test.py` 产出率 100%；`six_god_wang_shuai_test.py` 6/6；`thinking_chain_tests.py` 12/12。
- plugins 链：`node plugins/scripts/build.mjs`（`scripts/classical/` 随 RUNTIME_INCLUDE 的 scripts 递归进包，dsh-plugin/engine/liuyao/scripts/classical/ 9 文件在位）→ `selftest.mjs` 全绿（含 **yi_liuyao 引擎冒烟：以构建产物树跑通装卦出「贲」**——打包侧唯一端到端证据）→ `npm --prefix dsh-plugin run check` 通过。
- `python kernel/sync_kernel.py --check`：内核 17/15 文件逐字节同源（本批未碰 kernel）。
- `devkit/sync_devkit.py --check`：12 共享件与两科产物逐字节一致。

### 四、口径

- 纯搬迁批：不改任何判据语义与断语字面量；golden 双指纹与 tune 97.9（n=20）／holdout 90.2（n=12）读数不动属预期（§四.7），不动即正确。
- 台账旧指针（legacy/rule_registry.json 24 条扁平 impl、domain/adjudications.json 的 prose anchor 除本批同步重建的两条外）保留登记时点写法，由判据侧转发回验——**历史台账不回改**与**活引用必须可回指**同时成立。
- D 系列余下：D3（engine/pipeline/ 收 step 链，届时 scripts/classical/ 一并升格）、D5（=T31 已完成拆法外的进一步瘦身）。


## 2026-11-03 第五百零四批（六爻·规则引擎重构 D 系列收尾）：**`step5.apply_verdict_overrides` 的 7 条古籍强凶格局硬编码 if 链整体迁为 `rules/registry.json#verdict_overrides` 数据规则，由 `rule_engine.evaluate_verdict_overrides` 统一求值——纯重构零漂移**

**性质**：规则仲裁层数据化（D 系列最后一块硬编码）；不改判据、不改读数。

### 一、改法

1. **接线**：`step5.apply_verdict_overrides` 内原 1383–1425 行的 7 条 `if` 覆写链
   （行人散、合伙散、用神衰弱净动负、三刑六合相战、合处逢冲婚姻档、合处逢冲大凶档、财价跌）
   整体替换为：组装覆写期上下文 `cv`（verdict/final_score/qtext/q_l/sp_pat/net_effect/
   pattern_flags/world_relation/is_wealth/is_travel_return/xhe）→ 局部 `from rule_engine import
   evaluate_verdict_overrides` → 回收 verdict/final_score → 按 `reason_key` 非空逐个换判词文案。
   数组顺序复刻原 if/elif 语义（合处逢冲婚姻档在前、大凶档在后，后读前写）；
   `_fired` 仅对旧代码显式置 True 的四档（行人/合伙/用神弱/三刑六合）生效，与 `[1.8]` 同档收口一致。
2. **判定表对齐**：`judgment_table.json` 的 `overrides` 由 27 条对齐到 **20 条**——
   删去已迁走的 OV01–OV07（不再以 step5 AST 代码块形态存在），剩余 20 条 line/cond/assigns
   用 `_inventory` 重算逐字对齐；`stats.by_kind` 重算为 priority 2·exception 2·domain_overlay 16。
   verdict_map 两条悬空 note（「下跌」「平凶」）改指数据层 reason_key。
3. **值面覆盖扩面**：`check_judgment_table.py` 第 6 步除 step5 字面量外，纳入
   `registry.json#verdict_overrides` 的 target——数据层新判词同样要求 verdict_map 登记，
   消除「数据层加 target 而门看不见」的盲区（selftest 负例随之恢复有效）。

### 二、自证（§四.8）

- `golden.py`：288 例｜机械 `96c7f5d168ca6140`｜措辞 `8168eff9e560d6c2`｜异常 0——**与基线逐位一致**
- `check_judgment_table.py`：主检查 rc=0；`--selftest` 8 类负例全抓、健康副本放行
- 全量 `python dev_tools/check.py --fast` **rc=0**（各节全绿；tune/holdout 评测随下次完整跑）

### 三、口径

- 本批为纯重构：7 条覆写的 when 条件与旧 if 逐字核对等价（含 score_floor=0.5、空 reason_key
  不动 desc 等边角），golden 双指纹零漂移即其机器证明。
- 历史残留清理：调试探针 `probe_caps.py`/`probe_overrides.py` 与门禁快照 txt 此前已清；
  `scratch/` 下临时脚本按 gitignore 不入库。

## 2026-11-02 第四百九十六批（六爻·裸文件名死引用）：**`rule_registry.json` 的「见 HANDOFF」是活引用而 HANDOFF 已随扁平化删除；`check_doc_refs` 此前整段跳过裸文件名**

**性质**：共享门补裸文件名判据＋本科数据说明修正（不改判据、不改读数）。

### 一、缺陷

`data/rules/rule_registry.json` 的 `yingqi` 维度 note 写「…另 wikisource top-1
~20% n=35 为泛化读数——见 HANDOFF，非调参对象」。HANDOFF.md 已随仓库扁平化删除，
这是活引用指向已删文件（§六.3）；「~20% n=35」与 `README.md` 现行外部集表
（wikisource_holdout top-1 31.8%、n=50，308 批）也不一致，属旧快照。
`check_doc_refs.py` 原口径明文规定「裸文件名不构成本器的路径声明」，故一直无门。

### 二、改法

- 共享件新增 `LEGACY`：只对已知已删旧件的裸文件名（HANDOFF／TECH-DEBT／
  两个幽灵测试文件名）补判；病史行（整行或上一行含病史词，`LEGACY_HISTORY`
  另收「已删」）豁免；`check_house_conventions.py` 的正则字面量按 `LEGACY_SELF` 排除。
- selftest 加两式：活 `见 HANDOFF` 必抓、病史行「原 TECH-DEBT 已删」不得误判。
- 数据修正：note 改为「实时读数见 README 外部集表与 references/source_ledger.md」，
  删去 HANDOFF 与旧快照数字。

### 三、自证（§四.8）

- **门先于修正**：把 note 改回「见 HANDOFF」→
  `× data/rules/rule_registry.json:223 引用已随扁平化删除的旧件（裸文件名，无路径前缀）→ HANDOFF`；
  逐字节还原（sha256 `844AC5DC…`、91255 字节相同）后全绿。
- 两科全门通过；读数 tune 97.9（n=20）／holdout 90.2（n=12）不变（只改说明与门，§四.7）。


## 2026-11-02 第四百九十五批（八字·代码书证扩面）：**共享件把代码书证门从 `scripts/core` 扩到 `dev_tools/eval`；本科无该册变更，全门与读数不变**

**性质**：共享门覆盖面扩展（本科不改数据、不改判据、不改读数）。

- 八字 `dev_tools/`（96 锚）与 `eval/`（12 锚）的「《书名》源L####「…」」此前无门；
  共享件 `check_bazi_code_anchors` 扩面并按 AST 跳过 `selftest` 夹具、支持跨行引文与
  忽略 f-string 模板；八字侧扩面首跑判红 10 条（9 条真错）并逐条修正
（详见八字 CHANGELOG 第四百九十五批）。
- 六爻 [12] 的描述同步改为「core/scripts/dev_tools/eval 代码书证（本科副本属跨科，不挂）」；
  本科仍不挂该扫（共享件逻辑未在本科触发），但 selftest 跑同一套夹具。
- 真实探针在八字侧执行并逐字节还原；六爻全门通过，读数 tune 97.9（n=20）／
  holdout 90.2（n=12）不变。


## 2026-11-02 第四百九十四批（两科·书目异名）：**共享件为《命理探原》/《命理探源》加同书别名归一；L605 锚归入可解析**

**性质**：书目解析归一（本科无该册变更，不改数据、不改判据、不改读数）。

- 八字 `symbols.py` 的 `《命理探原》源L605` 与库内底本标题《命理探源》按字面不匹配；
  共享件加 `_book_key` 别名表（仅已实见同书异写），两个解析函数统一走它。
- 真实探针（L605→L9999）判红并逐字节还原；六爻全门与读数（97.9/90.2）不变。


## 2026-11-02 第四百九十三批（六爻·用神词典元数据）：**`description` 仍写「195 条现代问法」，而 `key_count=275`、落盘 entries 合计 275；同一份元数据自相矛盾**

**性质**：数据/构建器元数据修正＋门覆盖面扩展（不改判据、不改读数）。

### 一、缺陷

`question_use_gods.json` 的 `_meta.description` 写「六爻问题词典（195 条现代问法→六亲…）」，
同块 `family_count=74`、`key_count=275`，落盘 `families[*].entries` 合计 **275**；
构建器 `build_question_use_gods.py` 也照抄 195 写入。195 是早期版本遗留数，
从未随 249→275 的扩表更新（§六.3：同一份数据两处事实不同）。

### 二、改法

- 构建器与落盘 `_meta.description` 同步改为「275 条现代问法」。
- `[12]` 新增 `check_usegod_meta()`（仅六爻册）：`family_count == len(families)`、
  `key_count == Σentries`、`description` 里的「N 条现代问法」== 实际键数；
  任一项不符判红，缺声明也判红。
- selftest 加 5 式（正例＋description 条数/族数/键数不符/缺条数声明）。

### 三、自证（§四.8）

- **门先于修正挂上**：未改数据前跑 `check_rule_registry` 即
  `× 用神词典元数据：description 声明 195 条 ≠ 实际 275 键`；改 275 后全绿。
- 真实探针：改回 195 → 再判红；逐字节还原（sha256 相同）后全绿。
- `build_question_use_gods.py --check` 仍 69/69；读数 tune 97.9（n=20）／
  holdout 90.2（n=12）不变。


## 2026-11-02 第四百九十二批（八字·注册表「语料行」）：**共享件为 `bazi/rule_registry.json` 的「语料行 NNNN」补回验；六爻无此形态**

**性质**：共享门覆盖面扩展（本科不改数据、不改判据、不改读数）。

- 八字注册表 3 处「语料行 2608/2612」「语料行 2452」不以 L 写行号，465/474 都不覆盖；
  本批扩 `check_registry_line_claims`（同串路径／`corpus_files`／`source.book` 三级解析），
  首跑 3/3 在册；真实探针（2452→99999）判红并逐字节还原。
- 六爻无此形态，跳过；全门与读数（97.9/90.2）不变。


## 2026-11-02 第四百九十一批（六爻·用神词典族注）：**构建器明写「note 不参与核验」，families 64–69 的 7 段「…」引文（占雨/借贷/讨债/六畜/坟墓）无门；补门后 7/7 命中**

**性质**：共享门覆盖面扩展（不改数据、不改判据、不改读数）。

### 一、缺陷

`build_question_use_gods.py` 的族定义注释写着「label 与 note 是给人看的取舍依据
（note 不参与核验）」。实测 family 64–69 的 `note` 有 7 段 `「…」`：
占雨/占晴（`占雨用父爻…`、`占晴用子孫爻…`）、借贷、讨债两句、六畜、坟墓，
都称「章内逐字」却无行号锚；`[14]` 只认 `源L` 形态、只核到 1 条，483 又只覆盖
`families[71]` 的 file+L 注。这批族注的书据因此长期无人回验（§六.3）。

### 二、改法

- `[12]` 新增 `check_usegod_family_notes()`（仅六爻册）：
  · 扫 `families[*].note` 的每段 `「…」`，按省略号分段、折叠标点；
  · 须在《增刪卜易》**dz＋wikitext 两版**任一底本中逐字出现
    （wikitext 的 provenance 无 title，`_corpora_for_book` 只认 dz，
    本函数按 `zengshan_buyi*.txt` 两版全收）；
  · 下限 6 段，0 段判红。
- selftest 加 4 式（正例＋引文错/0 families/0 段）。

### 三、自证（§四.8）

- 首跑 **7/7 命中**：关键是 wikitext 版才是这 7 段的所在（dz 版为另一底本，
  实测 0 命中）；两版全收后全符，不改数据。
- 真实探针：families[64]「占雨用父爻」→「占雨用母爻」→ 判红
  `families[64].note 的引文不在《增刪卜易》底本`；逐字节还原（sha256 相同）后全绿。
- 读数 tune 97.9（n=20）／holdout 90.2（n=12）不变。


## 2026-11-02 第四百九十批（八字·代码注释源L）：**共享件为八字 `scripts`／`core` 的 51 个 `源L` 书证补回验；六爻无此形态**

**性质**：共享门覆盖面扩展（本科不改数据、不改判据、不改读数）。

- 八字 `scripts`／`core` 有 51 个 `源L` 锚（`dayun.py` 49 个），482 与 [10] 都不扫；
  本批扩 `check_bazi_code_anchors`（同行/前 9 行书名、provenance 全收、行号在册、
  同行 `「…」` 逐字；篇名式《》先向前找可解析书名），首跑 51 锚、31 引文全符。
- 六爻代码由本科自己的 [14] 扫 `源L`，不重复挂；全门与读数（97.9/90.2）不变。


## 2026-11-02 第四百八十九批（八字·裁决散文裸行号）：**共享件为 `bazi/verdicts.json` 的散文行锚补回验；六爻无该册跳过**

**性质**：共享门覆盖面扩展（本科不改数据、不改判据、不改读数）。

- 八字 `verdicts.json` 12 个底本行（14 处写法）只写行号不带引文的定位声明
  （五格 L1657…、L5265、L1668、L1704、L5115、L5137、L1734、L179）此前无门；
  本批扩 `check_verdicts_prose_anchors`（路径/书名/同条 locator→底本），
  首跑 14/14 在册；真实探针（L1657→L9999）判红并逐字节还原。
- 六爻无该册，跳过；全门与读数（97.9/90.2）不变。


## 2026-11-02 第四百八十八批（六爻·问题题类注记）：**`question_classes.json` 的 4 个源L（题类析出/天气分轨「书据」）与 3 条「…」引文无门；补门后 4/4、3/3 全符**

**性质**：共享门覆盖面扩展（不改数据、不改判据、不改读数）。

### 一、缺陷

`question_classes.json` 的 `classes[*].source_gates`／`note` 里有 4 个
`源L####`：终身财福类 **L2219/L2221**、天气类 **L1953**、易隐 L1541，
其中 3 处带 `「…」` 引文。这些正是「题类如何析出」「占雨为何不并进行人」的
书据，但此前没有任何门读取——`[12]` 的 `source_gates` 扫描面从未包含本题类表。

### 二、改法

- `[12]` 新增 `check_question_classes_notes()`（仅六爻册）：
  · 每个 `源L####` 的《书名》取同串最近《…》，经 provenance 解析
    （`_corpus_for_book`，同名多本 `_dz` 优先），行号在册；
  · 锚后到下一锚之间的首个 `「…」` 须在该行逐字命中；
  · `classes` 的字符串与**字符串列表**两种承载都扫（`source_gates` 是列表）。
- 下限 4 个源L／3 条引文；selftest 加 5 式（正例＋引文错/越界/缺书名/0 类）。

### 三、自证（§四.8）

- 首跑 **4/4 行锚、3/3 引文全符、0 处漂移**：L2221 的「凡占终身财福…」、
  L1953 的「占雨用父爻…」、L1541 的「占晴以子孙为用…」均在所署行逐字成立。
- 真实探针：L1953「占雨用父爻」→「占雨用母爻」→ 判红
  `classes[8].source_gates[0] 的引文不在 《增删卜易》源L1953`；
  逐字节还原（sha256 相同）后再跑全绿。
- 读数 tune 97.9（n=20）／holdout 90.2（n=12）不变。



> **精简**：更早的批次已归档到 [CHANGELOG-HISTORY-INDEX.md](CHANGELOG-HISTORY-INDEX.md)，需要时查 git log。

