# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。

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

