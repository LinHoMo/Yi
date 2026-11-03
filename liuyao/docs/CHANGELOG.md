# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。

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

