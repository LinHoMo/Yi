# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。

## 2026-11-04 第五百一十六批（全仓·冻结面与死链门补齿）：**共享层 [5] 扩到四工具参数 schema 与 required、[7] 补报告模板禁语与免责提示语；两科死链门新加裸文件名存在性判定，实跑抓出 15 处悬空裸引用（含 SKILL.md 铁律仍指向 508 批已删的 engine.py）并逐条按实况改正**

1. **冻结面**：`plugins/scripts/selftest.mjs` [5] 新增 `FROZEN_SCHEMA`（四工具 props 键集与
   required），逐项比对 MCP `tools/list` 实返；输出 value 结构与文本块形状仍由
   `verify-in-dsh` 真跑 `execute()`／`render()` 覆盖，不重复。负例：改 `yi_kb.required` 即判红。
2. **报告口径**：[7] 新增 `REPORT_SOURCES`（`plugins/mcp/report.mjs`、两科 `scripts/render.py`），
   逐份扫禁语并要求含「专业意见为准」；0 目标判红，含缺提示语负例。三份实跑全覆盖。
3. **死链门裸名**：`devkit/shared/check_doc_refs.py` 原来对不含 `/` 的裸文件名一律放行，
   现按全仓在盘文件名集合判存在性（病史行仍按 HISTORY／LEGACY_HISTORY 豁免），
   含裸名负例与真裸名不误报两条自证。实跑两科共抓 15 处：`engine.py` ×6（508 批升格后
   已迁入 `engine/_core.py`）、两科 core 的 `classical_tables.py` ×4、
   `CHANGELOG-ARCHIVE.md`、`fangwei.py`、`provenance.json`、`断易鬼灵经.txt`、
   `check_baseline.json`。逐条改为现行路径、去掉文件名后缀或补病史，其中
   `liuyao/SKILL.md` 铁律「必须且只能由 `engine.py` 完成」是**活规程指向已删文件**，
   已改指 `engine/_core.py`。四个 kernel 变体经 `sync_kernel.py --write` 同步（[35] 同源）。
4. **精简**：`liuyao/scripts/output.py` 三段批次沿革 docstring 压成各 2–4 行；
   `chart.py`、`engine/__init__.py`、`source_ledger.md` 等同步去掉过期文件名。
5. **诚实结案**：`_resolves()` 的 basename 兜底有 124 处依赖，实测全是「省略 `domain/`
   前缀」的正当写法，收紧会把真引用判红，本批不动；案例隔离门的动态 import 痕迹检测
   亦未加（无实际案例，静态扫描面已扩到 core/ 与 data/）。

**收口实跑（全部 rc=0）**：两科 `check.py` 全量、两科 `check_doc_refs.py` 与 `--selftest`
（947／811 条引用、0 死链）、根级三门、readout_ledger full、两个 sync --check、
build/selftest/npm check、两科回归与冒烟。

## 2026-11-04 第五百一十五批（全仓·路径真源收敛与门盲区补齿）：**六爻 scripts 层数据路径硬算层级收进 `kernel_path` 单一真源，缺表一律抛错；案例隔离门扩到 core/ 与 data/ 并补负例，[42] 加覆盖防退化断言；零读数变更**

1. **路径真源**：`liuyao/scripts/kernel_path.py` 新增 `disc_path()` / `data_path()` /
   `load_data_json()`，向上搜 `core/yishu_core` 定位，不按 `parents[N]` 硬算。15 个模块的
   文案表装载统一改走它（advice_framework／labels_loader／trigram_symbolism／xiang／
   narrate_core／chain_tables／chain_verdicts／engine_format／narrate／render／timing／
   bing_yao_shensha／yilin_buyi_maps 等）；`load_data_json(required=...)` 同时校验必需表非空，
   缺文件、非法 JSON、表为空一律抛错。六爻 scripts 层只剩 6 处 `parents[1]`（shim 根定位、
   sys.path、输出目录），均不读数据表。
2. **静默空表清零**：新查出 `yilin_buyi_maps.py` 的 `except OSError: _MAPS = {}`、
   `bazi/scripts/xiang.py` 的 `except OSError: return {}`、`render.py::_grade_note` 的
   `try/except: return ""` 三处同型降级，一并改为缺表即抛错；顺带删重复 import、
   冗余空行与各模块长沿革 docstring。
3. **案例隔离门**：`devkit/shared/check_case_isolation.py` 扫描面由 scripts/＋engine/
   扩到 scripts/＋engine/＋core/＋data/，FORBIDDEN 补 `case_library`／`source_quote`，
   内核 `eval.py` 按评测层语义豁免；新增 core/ 探针负例。两科实跑检视 78／31 个模块、0 触达。
4. **[42] 防退化**：`check_source_provenance.py` 新增 `coverage_problems()`，扩展统计与
   登记元数据的覆盖量低于底本份数即判红（可选字段仍不强制每份都登记，双口径 0 属合法历史形态），
   含 4 件负例自证。两科 selftest 34 件全过。两门真源经 `sync_devkit.py --write` 分发，
   [37] 字节门同源。
5. **诚实结案**：`diff_jingshi_vs_core.py`／`diff_shangzhan_vs_core.py` 是书源逐格对拍工具
   （已由 [12]／[42] 覆盖），不是 data↔引擎同步器；挂进 check.py 需同批改账台 tier 期望、
   治理图与负例自证，收益不抵口径变更成本，本批不挂，也不再列为欠账。
   4 个 scripts/ 兼容 shim 的反向 import、门编号体系、pytest 框架同属需独立批次的契约级变更，未动。

**收口实跑（全部 rc=0）**：两科 `check.py` 全量、两科隔离门与 [42] `--selftest`、
根级三门、readout_ledger full、governance_map、两个 sync --check、build/selftest/npm check、
两科回归与冒烟。

## 2026-11-04 第五百一十四批（全仓·文档治理、门禁补齿与结构收敛）：**四组「现在时钉数」集体过期而无一门能拦（真探针塞「999 份」两门照绿）→ 数字改指真值源并上提为 AGENTS §六.6；后半按用户令并批修完门禁假绿、契约三件套同步、静默空表、产物同源与 CI 回归五组结构性欠账；不改判据口径、不改数据、不改读数**

**性质（前半）**：文档治理＋盘上清理（清掉 170 个 gitignore 垃圾，含 `devkit/handoff/` 27 份）。

### 〇、本批后半并入：门禁补齿与结构收敛（并批登记，不另立 515）

**性质（后半）**：门禁/结构修复；引擎行为唯一变化是数据表缺失由「静默降级为空表」改为**显式抛错**。

1. **假绿三处**：`plugins/scripts/selftest.mjs` [7b] 把不存在的目标 `.filter(existsSync)` 静默丢掉，
   0 份文档也判绿 → 改为缺失即红 + `caliberOk([])` 负例；`devkit/root/check_root_docs.py` 的
   `PLAN_DOCS` 整份跳过 `ARCHITECTURE-PLAN.md`（纳入扫描实测 0 死链）→ 删除跳过并补归档件负例；
   两科 `check.py --fast` 汇总补「分数门未生效、不代表合入门槛」。
   同批给 selftest [5]/[6] 补负例，新增 [1.6] `engine/` 165 文件、`skills/` 15 文件
   全量逐字节同源门（篡改／缺文件／0 文件三类负例）。
2. **契约三件套**：`CONTRACT.md` §四 曾写八字路径带 `domain/`（实为扁平）与 analyze 14／
   trigram 22 键（实为 15／35）。`devkit/shared/check_layer_contract.py` 新增
   `doc_sync_problems()`，§四 表格的顶层与嵌套键数逐项对两科 JSON 重放，缺段／0 行／
   漏登记均判红并带负例自证；`sync_devkit.py --write` 分发两科（[37] 字节门同源）。
3. **静默空表**：`trigram_symbolism.py`／`xiang.py`／`narrate_core.py` 的
   `except OSError: return {}` 改为读不到即抛错 + 必需表校验，数据路径统一走
   `kernel_path.repo_root(__file__)`，收敛 507 批同型的 `parents[N]` 事故面。
4. **口径落地**：六爻 [5] 分数行补 `n=` 与 tune/holdout 调参标记；八字医疗／法律／投资
   免责提示语落在 `render.py` 报告层，避开 narrate 措辞指纹漂移。
5. **docs 统一与精简**：知识库篇数 13/14/15/9 四套 → 一律以 `INDEX.md`／`KB_DOC` 为准；
   `dsh-plugin/README.md` 312 → 84 行（删体积实测快照表、历史踩坑叙事、三工具 vs 四工具冲突）；
   `DOCS.md` 阅读路径 3→4、`docs/CHANGELOG.md` 二义路径改指两科、JUDGMENT-TABLE 一句话校正；
   `plugins/CHANGELOG.md` 第三百零七批重复节去重并加 497 批勘误；
   `bazi/docs/CHANGELOG.md` 3948→294/296 矛盾统一为 296；
   `dsh-plugin/CHANGELOG.md` 补 497／508 批宿主侧登记；AGENTS／CAPABILITY／GOVERNANCE
   卷首沿革段压缩，`plugins/scripts/selftest.mjs` 与三个数据模块删除冗余注释。
6. **CI**：`min-python-smoke` 补 `liuyao/tests/regression_test.py`（实跑 19/19）与
   `thinking_chain_tests.py`（12/12），删过期的「17/19 待裁」排除注释；CI 注释精简。

**收口实跑（全部 rc=0）**：两科 `check.py` 全量与 `--fast`、根级三门（含 `--selftest`）、
`sync_kernel.py --check`／`sync_devkit.py --check`、`readout_ledger.py` full、
`governance_map.py --selftest`、`build.mjs`、`selftest.mjs`、`npm --prefix dsh-plugin run check`、
两科回归与思维链测试。`plugins/engine` 165／`dsh-plugin/engine` 165 文件全量同源。

### 一、起点：工作区停在半成品的一批

接手时工作区有两个未提交文件：本科 `CHANGELOG.md` 把 488–496 批压成一句话，
`CHANGELOG-HISTORY-INDEX.md` 收下这些标题、按批号倒序重排，头注自称「514 批按实重写」——
而主文件没有 514 的登记条目，按 §六.1 属未登记改动。旧索引头注另写「只保留最近 30 批标题」，
逐号实测：那 30 节收的是 **210–372**（373 之后一节没有，「最近」为假），且 **314–325 插在 246 与
213 之间**属倒序违例。本批按用户令**并批登记**：压缩面与本轮治理面合为本批，不再另立 515。

### 二、缺陷：文档抄走的数没有第二块表来验

机器面当时是全绿的（`check_docs_index` 44 份可达、两科 `check_doc_refs` 952＋816 条 0 死链、
`readout_ledger --quick` bad=0）。烂的只是给人读的散文——**所有文档门只判「路径是否可达」，
不判句子里的数**，于是同一组数字在账台里有齿、在正文里无齿：

1. `AGENTS.md` §二：「DOCS.md 是全仓 **51 份** Markdown 的总索引」。tracked `.md` 现 45，
   门口径 44（减 `DOCS.md` 自身）；51 是 330 批的值，510 批减量后没人回改（§六.2）。
2. `AGENTS.md` §二 目录树：`devkit/` 写「12 共享件 + **variants/** 4 变体」，真路径是
   `devkit/shared/variants/`；项数本身也落后过（见 5）。
3. `GOVERNANCE.md` 第一行「两科 dev_tools 已 **106** 个脚本（六爻 63／八字 43）」与
   §当前分布 整表（六爻 64／blk 28／nightly 11…、八字 43／blk 26…）——`governance_map.py`
   514 批实跑是**六爻 74／blk 34、八字 49／blk 30**。该节第一句自称「读数取自本次实跑，
   不抄旧快照」，而表就是上一批的快照：正文与自家表格互相打脸。
4. `GOVERNANCE.md` 墓碑行「新门从 `[37]` 续」——实跑 `check.py` 六爻尾号 `[44]`、八字 `[43]`。
5. `ARCHITECTURE-PLAN.md` 四处：§二 树与依赖图「**5 个宿主**适配器／5 宿主 src/」、V9
   「plugin-gates（五宿主 × 2 OS）」（497 批已删四家，只剩 `dsh-plugin/`）；V4「**51 份**全部
   登记可达」；§五.2「`files.shared` **仍为 11 项**」而 MANIFEST 是 12（同一文件 §一 D2 行
   写的也是 12——**自己和自己打架**）；§六.4「不回填 **9 个**空号」（实为 8）。

`ARCHITECTURE-PLAN.md` 在 DOCS.md 标「归档留证」，§六 维护口径又写「归档不改写正文」，
故该件按仓内先例（本文件 §顺带更正：「本行即更正，不改写历史条目原文」）处理：
**文首加五段勘误块点名五处、正文历史值一律保留**；V4／V14 行只在原值后追加现值口径，不抹旧数。

### 三、改法：不刷数字，改成指向真值源

- `AGENTS.md` §二：份数与共享件项数都不再写死，改指 `devkit/root/check_docs_index.py` 实跑首行
  与 `devkit/MANIFEST.json`，并把「variants/」路径写正。
- `GOVERNANCE.md` §当前分布：**删掉手抄分布表**，改为「现取命令 + `*/docs/GOVERNANCE-MAP.json`
  五个字段 + 判绿口径（`unclassified`／`curated_but_missing`／`blocking_not_referenced` 必须空，
  `referenced_not_blocking` 由账台 `tier一致性` 核账）」；历史增补事实（344／499／511／512 各加了什么）
  作为登记保留。墓碑行同改为「取实跑尾号 +1，不在文档钉」。
- `ARCHITECTURE-PLAN.md`：文首勘误①–⑤ ＋ §二/§三/V4/V14 的活引用与死路径标注（路径可达属
  §六 许可的唯一例外）。
- `DOCS.md`：`GOVERNANCE.md`／`ARCHITECTURE-PLAN.md` 两行的一句话职责同步（不写份数）。
- **规程上提**：AGENTS.md 新增 §六.6「现在时文案不钉会变数」，把 GOVERNANCE §精神条款 里只对
  该文件生效的规矩升成全仓口径，并把本批五例作为反例存档。沿用 README.md 既有范式
  （「小节号会随门禁增补变化，故此处不写死区间」）。

### 四、盘上清理（按用户令「全清，含 devkit/handoff」）

删 6 个目录共 **170 文件 ≈10.5 MB**，全部 gitignore、tracked 数为 0（删前逐个 `git ls-files` 核实，
`git status` 删后仍只有那两个本轮要写的文档）：根 `scratch/` 60、`bazi/scratch/` 13（含
`corpus_reports.txt` 5.1 MB）、`liuyao/scratch/` 69（含 `golden_before.json` 4.0 MB）、
`devkit/handoff/` 27、`liuyao/logs/` 1、`liuyao/outputs/` 0。

- **不可恢复且已知**：`devkit/handoff/` 从未进过 git，27 份交接报告原文就此消失——逐卡结论改由
  `ARCHITECTURE-PLAN.md` §三 的「批次 × 提交哈希」表加各科 CHANGELOG 331–339 批承载。
  这是清理时接受的代价，不是待补欠账，已在勘误③与 V14 写明。
- **未删（刻意）**：`devkit/pending/` 里 `.gitkeep` 是 **tracked**，删它要动入库面；
  `*/data/cache/`、`*/data/collation/` 与 `bazi/data/sources/*.wikitext.txt` 是底本/中间产物，
  其中 wikisource 系需联网重抓，删了会把 `check_source_provenance` 逼成红；
  `plugins/engine|skills`、`dsh-plugin/{src,engine,skills,SKILL.md}` 是 `build.mjs` 产物不是垃圾；
  `__pycache__` 不在批准范围内，未动。
- **同批修的活引用**：`ARCHITECTURE-PLAN.md` 有 5 处指向 `devkit/handoff/`（文首、§二 树、§三 标题、
  V13、V14）。`check_root_docs.py` 把 `devkit/handoff/` 列在 `RUNTIME_DIRS` 豁免里，**门不会红**，
  但按 §六.3 它仍是文档与事实不符——与 496 批「`rule_registry.json` 的『见 HANDOFF』」同一型。

### 五、自证（§四.8）与读数

- **真探针**：`AGENTS.md` 插「全仓 **999 份** Markdown」→ `check_docs_index` 仍报
  「44 份文档全部登记且可达」rc=0、`check_root_docs` 仍「126 条引用 0 死链」rc=0。
  即**这一类病确实没有门**，不是我没找到门。撤探针后逐字节还原（sha256 `562abd8a…` 与插探针前一致）。
- 本轮用的门自带 selftest 全过：`check_root_docs --selftest`（死链必抓／同名不兜底／真路径不误伤／0 份判红）、
  `check_docs_index --selftest`（漏登记与死链都抓到）。
- 收口读数：`check_docs_index` 44 份可达；`check_root_docs` 126 条（本轮由 122 增）0 死链；
  `check_doc_refs` 六爻 952／八字 816 条 0 死链；`check_house_conventions` 六爻 266／八字 174 tracked
  0 违规；`sync_devkit --check` 12 共享件逐字节一致；`governance_map` 两科未分类与幽灵均为空；
  `readout_ledger --quick` bad=0。
- **零引擎、零数据、零判据变更 → 读数不动属预期**（§四.7），且**不引用记忆**：改动**之后**重跑
  `readout_ledger --quick`，`liuyao.tune(97.9/64.7/1.53)`、`liuyao.holdout(90.2/50.0/1.6)`、
  `头牌值在位(9/9)`、`governance(74/49, blk 34/30)` 四项均 √（bad=0）。
  其中 `头牌值在位` 正是专门断言 README×2／CAPABILITY／**GOVERNANCE** 各含每个头牌数字的门——
  本批删掉过 GOVERNANCE.md 一节里的表，所以这项必须改后重跑，不能拿改前那次绿当数
  （改前那次是另一份字节）。不得拿「门全绿」当成果：本批的成果只是文档不再说谎。

### 六、立案（本批不做）

**「文档现在时钉数」无门**是本批查出的真缺口，但本批**不新增门**：GOVERNANCE.md 载明 176 批冻结
「守台账类新增」，新增须先证明属「让现实为预测判卷」方向，而文案 lint 属反向。若后续解冻，
候选形态是扩 `check_docs_index`（已有门，覆盖面扩展有 490/492/495 批先例）扫根级活文档的
「现在是 N 份／N 个脚本／从 [N] 续」句式，并沿用 `check_doc_refs` 的病史行豁免——
否则 331–339 批这类**归因用的历史数**会被集体误判红（2026-10-06 的假绿教训：豁免别把负例一起吞）。

**36 个批号「有提交而无登记」**（本批逐号核出，本批不修）：`check_batch_num` 只判
「CHANGELOG 登记 → 提交信息」这一向（防写了没提交），反向「提交 → CHANGELOG」只出 NOTE 不判红。
于是 375–382、387、398–407、417–419、421–423、425–429、438、448、452、455–456、472 这 36 号
在提交信息里出现过，而两科 `CHANGELOG.md` 与两份索引**都没有对应节**（同段 373–487 的其余 79 号
确实登记在八字侧，属正常分工，不是漏）。按 §六.1「一切登记逐批具名」这是存量欠账；补法二选一：
逐条 `git show` 核实后回溯建 36 条一句话（**不许拿提交标题当正文铸死**），或按 §六.5 结案说明
为何不补。本批**只立案不动手**——那 36 条多数属 375–406 区间的行为批，补登记会牵出读数归因，
超出「纯文档」范围，混进来反而违反 §四.7。

## 2026-11-04 第五百一十三批（六爻·建器分块越界）：**所谓「dry-run 与数据一处不同步」查成两处真问题——ZD214 的应期读到下一案（坎之井酉／戌），ZD102 的 expected 整段取自下一案（小过之丰「应在初九辰日即雨」）；前者靠「句号式占例头只作切块止界」修掉，后者按本卦临之蒙实文改回亥日，strict 87.4→86.5**

**性质**：构建器分块修复＋一条 expected 书证更正（**引擎零改动**；读数下调系去污染，不是回归）。

### 一、起点：512 留下的边界项

512 批只登记了「建器 `--dry-run` 与实际数据有一处已知不同步」，未定位。本批写 `liuyao/scratch/_verify_dryrun_513.py`
把 dry-run 清单与在册 JSON 逐例对拍（应期按**支集合**比、verdict 逐位比；第一版按字符串比，把「寅日」与「寅」
算两值，误报 29 条，已改）。先确认 512 的 `verdict` 空位沿用确实生效（6 例 dry-run 已显示吉／凶，不再 N/A），
再把真差异压到 1 条：**ZD214 dry-run=戌／酉，盘上=卯／辰**。

### 二、两处真问题（同一 bug 的两面）

1. **句号式占例头认不出**：`CASE_RE` 原要求「占…得」之间只有可选逗号，底本却有
   「如戌日丙午日占何日雨**。**得坎之井卦」这种句号式头 → 该案块并入 ZD214 块，锚句读到下一案的
   「果于酉日天变，戌日而雨」。
2. **ZD102 的 expected 被邻案串文**：其自身块（巳月丙申日·临之蒙，offset 84400）实文是
   「因巳火父空，亥日冲空则雨。亥日而雨，即于亥日酉时晴」，**全文没有「辰日」**；而盘上
   `yingqi=辰日`、`detail=「卦中辰父发动，当许中秋有雨，殊不知应在初九辰日即雨」`，逐字出自后一案
   （酉月初五戊子日占中秋雨·小过之丰，块内 +492 字）。`use_god_note`（巳火父空亥日冲空则雨）与本案块相符，
   说明当年只错在锚句与应期这一半——与 421 批「跨案引文」同型的病，落在 expected 上。

### 三、方案取舍

- **试验 A（否决）**：直接把 `CASE_RE` 放宽到允许 `。；` 作分隔。实跑分段 233、可评分 30，
  但 **ZD102 消失、多出 ZD230／ZD233**——动的是集身份，且消失的那例正是本批要修的，回退。
- **试验 B（采用）**：新增 `STOP_HEAD_RE`（行首锚定，可带 如／又／例 前缀），**只作切块止界、不新建案例**；
  `segment()` 事件表加 `"stop"` 类，向前找日期行遇 stop 跳过不取。这样 ZD214 的块止于下一案头，
  而「坎之井」那案不新增 id。
- 修完块界后 ZD102 一度掉出（「应期锚只剩占测日/预测假设」）：其实文写作「**亥日而雨**」，没有
  果／竟／卒／后／应 起句词。故给 `REALIZED_RE` 补窄口径 `而[雨晴]`（只在天时占出现，不改其他句式判定），
  ZD102 回到 29 例，应期读作 亥日。

### 四、改动

| 文件 | 改动 |
|---|---|
| `liuyao/dev_tools/build_zengshan_dz_cases.py` | `STOP_HEAD_RE`＋`segment()` 的 `"stop"` 止界；`REALIZED_RE` 补 `而[雨晴]`（各带 513 批注释） |
| `liuyao/data/cases/zengshan_dz_cases.json` | **仅 ZD102 一例**：`yingqi` 辰日→**亥日**、`yingqi_branches` `["辰"]`→`["亥"]`、`detail` 换成本案实文、新增 `yingqi_note` 记东窗（verdict／use_god 未动） |

### 五、读数（新旧不可比）

| 项 | 512 后 | 513 后 |
|---|---|---|
| zengshan_dz strict | 87.4%（n=29） | **86.5%**（n=29） |
| zengshan_dz legacy | 96.3% | **96.2%** |
| top-1（strict） | 48.3% | 48.3%（未动） |

降幅全部来自 ZD102 这一例：它原先**对着污染值命中**，等于白给一分；按书改回亥日后不再命中。
分维：use_god_category 24/29、branch 26/29、verdict 26/26、patterns 8/9、yingqi 14/29 均未动。

### 六、按实留证：为什么不一并改 ZD214

修完块界后 ZD214 的 dry-run 是 **寅／卯／辰**（果于寅日云、卯日大雨、辰日大晴），盘上是 **卯／辰**
（498 批按「卯日必雨辰日必晴」取的两日）。二者都对书，差别只在收不收「寅日阴云」。**不收**：把 broader
的建器值落盘等于放宽基准，读数会凭空变好（§四.7）。故盘上保持 2 支，差异以本条登记为已知，
`_verify_dryrun_513.py` 现报「不一致 1 条：ZD214」，就是这条被有意保留的口径差。

### 七、验证

- `python liuyao/dev_tools/check.py`：**全绿**（含 [44] 本体门「负例自证通过＋真实图谱 71 节点完整」、
  [43] 案例层源哈希与在盘底本逐项相符）。
- `python liuyao/dev_tools/readout_ledger.py`：**bad=0（44/44，跳过 0）**；`zengshan_dz(86.5/48.3)` 按实重挂。
- `python liuyao/eval/evaluate.py --split zengshan_dz_holdout`：86.5／48.3（n=29）；bushi 65.3／23.7 未动。
- `python liuyao/dev_tools/build_zengshan_dz_cases.py --dry-run`：分段 217、可评分 **29**（集身份与 id 全保持）；
  `_verify_dryrun_513.py` 对拍：29 vs 29，仅 ZD214 一条已知口径差。

## 2026-11-04 第五百一十二批（六爻·zengshan 书证复核＋本体门接线）：**26 条 expected verdict 逐例回到「断曰／果／卒」句，无一例由引擎回填；同时查出六例建器词表读不出的结论会在重建时被静默清成 N/A，已堵死；`check_ontology` 自带上「只跑负例、真实结果丢弃」的假绿缺陷，修好后正式进 `check.py` [44]**

**性质**：证据复核＋门禁接线＋构建器防清空（**引擎与判据零改动**；`data/cases` 只加注不改判）。

### 一、26 条 verdict 的书证核对（511 批留下的疑点）

方法：对 29 例逐例取 `provenance.offset` 回底本 `data/sources/zengshan_buyi_dz.dz.txt`，看该例的实录句／断语句；
不比对引擎输出，先只问「书上有没有写这一案的结果」。结论是 **26 条非空 verdict 全部有书载依据，没有一条只能由引擎回答**。

| 例 | expected | 书证锚句（底本实录／断语） |
|---|---|---|
| ZD194 | 吉 | 断曰：寅日得见财，亦如心 |
| ZD195 | 凶 | 果卒于癸卯日，应卯日者冲去元神之日也 |
| ZD014 | 吉 | 财爻克世，此财必得…果于甲寅得之 |
| ZD015 | 吉 | 世临月建之官，定得面见…果得见于丙子日 |
| ZD196 | 吉 | 定然三月高迁，果于三月升任云南太守 |
| ZD016 | 凶 | 月建作忌神，为祸不浅，大凶之象…果于本年下狱至申年而重刑 |
| ZD017 | 凶 | 六冲卦，不吉…果于六月疾至，八月伙计盗尽 |
| ZD197 | 凶 | 申金月建生亥水回头克世，卒于亥月 |
| ZD022 | 凶 | 女死辰日…此乃爻之遇合、卦逢六合之验也 |
| ZD023 | 吉 | 六冲变合…此婚一定还成，果于次年三月仍成婚 |
| ZD026 | 吉 | 此子必归。果于子年建功卯年得意而归 |
| ZD029 | 凶 | 许之可治，后死于寅日寅时 |
| ZD031 | 吉 | 世空者还至交春即归，果于二月得意而回 |
| ZD036 | 吉 | 准行无疑，果于乙卯日起程…满载而归 |
| ZD050 | 吉 | 兄动化退，已有归志…后至戌月方回 |
| ZD059 | 吉 | 许未日愈，果起床于未日 |
| ZD205 | 吉 | 许之卯科方得遂意。子年占，果于卯年登科 |
| ZD065 | 凶 | 不独削职，须防五六月还见凶灾…果于五月下狱 |
| ZD109 | 吉 | 后至巳年因开铅矿…富冠一乡 |
| ZD221 | 凶 | 余恐亥年不利，后卒于戌年 |
| ZD222 | 凶 | 须防卯岁，果卒于卯年 |
| ZD125 | 凶 | 今秋必有险厄…地震房塌，人口被伤，独伊得免（凶指流年险厄，本人得免不改断） |
| ZD139 | 吉 | 此子见归…果于次年六月父子相逢 |
| ZD151 | 凶 | 须防孝服…果于八月丁艰 |
| ZD160 | 吉 | 其价必涨，果于正月勃然大长 |
| ZD188 | 吉 | 辰年下葬，酉年孙中亚魁，及至子年次孙又登乡榜 |
| ZD095／ZD214／ZD102 | N/A | 书只记「何日／何雨」结果，无吉凶判断，按 N/A 不进分母 |

**26/26 与引擎同向是怎样发生的，也必须说清**（AGENTS §四.7）：这不是「expected 抄引擎」，而是**一个开发集被逐例修到全对**——
501 批按原文补 8 例空值与空 verdict；504–506 与 D1–D4／T29 又按书断逐例改规则（ZD016 化退压凶、ZD022 世动逢合压凶、
ZD029 痘症取子孙、ZD151 世化官空、ZD221 动爻生世压凶、ZD222 生世无源压凶、ZD017 用神取财＋鬼持世不抬吉、
ZD194 连续相生链、ZD160 待冲解、ZD015 回头克待时）。**这 10 例是调优，不是泛化证据**：87.4% 是开发集读数，
不得当外部集成绩讲（CAPABILITY 已按「外部·开发集」标注）。

### 二、顺手抓到的真缺陷：六例 verdict 会在重建时被静默清成 N/A

建器 `build_zengshan_dz_cases.py` 的 verdict 由 `GOOD_WORDS／BAD_WORDS` 只从「非假设子句」读；词表读不出的六例
（ZD029「治」与「死」同现、ZD221／ZD222「卒」不在表、ZD125 险厄而人免、ZD139「相逢」、ZD188「登科中魁」）
是历批按书校勘定的，`--dry-run` 显示 N/A——也就是说**下一次重建会把它们清掉，而 [38] 只盯字段非空下限，未必拦得住**。
处置两条：

1. `merge_old_expected` 增 `verdict`／`verdict_note` 的空位沿用（建器读出的值优先，旧值不覆盖）——与 419 批
   18 例用神书证被清空同一个病，同一种堵法；`--selftest` 补正负两例断言。
2. 数据侧给这六例补 `verdict_note`（写明书证锚句与「词表为何读不出」），**verdict 一字未改**（写入脚本先断言前后相等再落盘）。

### 三、`check_ontology` 接线：先修假绿，再上阻断位

- **旧实现有假绿**：`--selftest` 只造一个幽灵 parent 的临时节点验证能抓到，然后 `return 0`——**把刚算出的真实图
  problems 整个丢弃**。挂在 `check.py` 里会永远绿，正是 §四.8 说的「全绿的新门先怀疑」。已改为负例之后仍报真账。
  真实数据负例自证：往 `l4_evidence.json` 注入 `yi.l4.probe_negative`（parent 指向不存在的 `yi.l3.NO_SUCH_PROBE`）→
  `rc=1`，报「孤儿引用＋orphan」两条；还原后 `rc=0`（72 节点 → 71 节点）。
- 门注册：`check.py` 新增 **[44] 图谱本体门**（编号顺延；`[36]` 墓碑不回填），以 `--selftest` 调用。
  `governance_map` 的 `check_ontology` 由 ondemand 升 **blocking**（六爻 blocking 33→34，脚本总数 74 不变），
  账台 `governance` 期望值同批改为 `74／49／34／30`。

### 四、验证

- `python liuyao/dev_tools/check.py` → 全绿，其中 `[44]` 输出「负例自证通过」＋「真实图谱引用完整（71 节点）」。
- `python liuyao/dev_tools/readout_ledger.py`（full）→ **bad=0，44/44，跳过 0**。
- `python liuyao/dev_tools/governance_map.py` → 两科「未分类」空；`--selftest` rc=0。
- 建器 `--selftest` rc=0（含新增 verdict 空位沿用正负断言）；`--dry-run` 不再被当作数据现状（见 §二）。
- `zengshan_dz` 三读数未动：strict 87.4%／top-1 48.3%／legacy 96.3%（n=29）——本批只加注，评分面零变化。

### 五、边界

- 建器与数据之间仍有一处「已知不同步」：`--dry-run` 打印的是词表原始判定（六例 N/A），落盘值经 `merge_old_expected`
  沿用校勘值。要让二者彻底一致，得把那六例的结论做成词表可判（会牵动其他案例），本批不做，登记在此。
- `check_ontology` 的四条规则之外没有新规则（如 L2 节点必须引用 L1 之类），本批不扩面。

## 2026-11-04 第五百一十一批（六爻·读数账台五项归因）：**full 账台 bad=5 逐项查到底——golden 是登记过期（drift_log 有据），zengshan 的 87.4 是 501 批 N/A 清零后真实跳升 23.1 点、旧阶梯从未重跑，bushi 的 68.1 在八处提交上均不可复现；另补登记 4 个「从未入治理表」的脚本。账台回到 bad=0**

**性质**：读数登记纠错＋治理表补登记（**零引擎代码、零案例 expected、零评分口径**）。改的是「登记值」与「地图条目」，不是判据。

### 一、取证方法（可复现）

用 `git worktree add --detach` 把八个提交各检出到系统临时目录，逐点在**该提交自己的代码与数据**上跑
`python liuyao/scripts/evaluate.py --split zengshan_dz_holdout`／`--split bushi_zhengzong_holdout`：

| 检出点 | 时点 | zengshan strict | bushi strict |
|---|---|---|---|
| `308f009^` | 501 批父提交 | **64.3%**（use_god N/A=8，verdict 11/18） | 65.3% |
| `308f009` | 第 501 批 | **87.4%**（N/A=0，verdict 26/26） | 65.3% |
| `961528c`／`8b37efb`(505)／`41986c7`(506)／`43dfde6`／`356115f`／`9f497de` | 501 之后 | 87.4%（六点全同） | 65.3%（六点全同） |
| `HEAD`（`0f07ccf`） | 当前 | 87.4% | 65.3% |

- 这条 A/B 把「+13 是 507/508 重构造成的」排除了：**跳变发生在 501，且此后七个提交逐位不动**。
- 501 的动作是「按原文补全 8 例空用神（六亲+支）与 8 例空 verdict」——N/A 清零后这些维度从「不计分」变成
  「计分」，strict 分母结构变了，所以 64.3→87.4 是**口径变化＋补全命中**，不是引擎改判。登记当时只写
  「64.3→64.5」，说明那串 64.5/66.0/67.6/69.4/72.8/74.4 是**照旧阶梯手推的估计，没有一次按 strict 重跑**。
- bushi 八个点恒为 65.3：502/503 改的 verdict cap 只对 zengshan 生效，对 bushi 没有连带，登记里的
  「65.3→66.5→68.1」两跳同样查无实据。

### 二、五项逐条处置

| 项 | 旧登记 | 实跑／取证 | 处置 |
|---|---|---|---|
| `liuyao.golden` | `8f60`／`8168`（503 批） | `96c7f5d168ca6140`／`8168` | **登记过期**：`digest.json#drift_log` 记 `8f60→7f05`（T29 救应规则）`→96c7`（D 系列 direction caps），捕获后账未跟。按日志回补，**不是回归** |
| `liuyao.zengshan_dz` | 74.4%（n=29） | **87.4%**（n=29） | **口径变化＋补全**：501 批 N/A 清零所致（见上表）。按可复现实值重挂，并写明「61.8→74.4 旧阶梯不可复核」 |
| `liuyao.bushi_zhengzong` | 68.1% | **65.3%**（top-1 23.7 未变） | **登记虚增**：八点实跑均 65.3，502/503 的 +2.8 无对应。按实值回归并留证 |
| `governance` | 71/48 脚本 | **74/49** | **地图漏登记**：ontology 三件（`check_ontology`／`ontology_subgraph`／`render_ontology`）建图起就在库、从未入 `CURATED`，地图连批报「× 未分类」没人改；另八字 `cross_version_collate`（499 批）同样未入表。四个均已按实登记（tier 见下） |
| `登记×提交在册` | 8 | **2**（221／264） | 孤儿实降：两条都在 `SETTLED_ORPHANS` 有结案依据（221 提交号后无「批」字；264 是 264–268 范围简写）。按 2 重挂，新增孤儿仍判红 |

### 三、改了什么

1. `liuyao/dev_tools/readout_ledger.py`：五项标题与期望值改实值；每条登记理由里写入**为什么旧值不可复核**、
   取证提交点与「501 批 N/A 清零」这一句——下一个人看到的是可复算的因果，不是新数字。
2. `liuyao/dev_tools/governance_map.py`：补 4 条 `CURATED`——
   `check_ontology`（ondemand，**并注明它没挂 `check.py`，是待接线门**）、`ontology_subgraph`（tool）、
   `render_ontology`（build）、`cross_version_collate`（ondemand，观测非 blocking）。
3. `CAPABILITY.md`：六爻 T1 指纹改 `96c7/8168` 并写清 344 批旧值到现在的逐次漂移；
   `zengshan_dz` 行 61.8%→87.4%，写明 +23.1 的来源与「旧两档不可复现」。
   **至此 CAPABILITY、账台期望、盘上实值三处同值**（510 批 §六 指出的「同一读数三处各异」收口）。

### 四、验证

- `python liuyao/dev_tools/readout_ledger.py`（full）→ **bad=0，44/44，跳 0**（改前 bad=5）。
- `python liuyao/dev_tools/governance_map.py` → 两科「未分类」均为空；`--selftest` rc=0（负例仍判红）。
- `python liuyao/dev_tools/check.py`／`python bazi/dev_tools/check.py` → 全绿；
  `python liuyao/dev_tools/golden.py` → 288 例｜`96c7f5d168ca6140`／`8168eff9e560d6c2`｜异常 0。
- 根级三门（`check_root_docs`／`check_docs_index`／`check_batch_num`）rc=0。

### 五、边界（转第五百一十二批）

- **`zengshan_dz` verdict 26/26 全中仍存疑**：旧记 19/26，现在每条 expected 都与引擎同向。501 批声称
  「按原文补全」，但 26/26 的完美一致必须逐例回书，排除 §三.4「由引擎输出反填 expected」。本批**只登记这个疑点，
  不改任何案例文件**。
- `check_ontology` 仍是手工门：图孤儿检查没有进 `check.py`，等于图上加的节点错了也没人拦。本批只登记 tier，
  接线另批（要让图真的守得住，得先给它一个阻断位）。
- 旧梯度的语义债不再追改：`61.8/74.4` 这类数已在四处文档里流转过多批，本批在账台与 CAPABILITY 留了
  「不可复核」的明确标注，其余历史 CHANGELOG 按「登记时点事实」豁免，不做全文回改。

## 2026-11-04 第五百一十批（全仓·文档审计与减量）：**审 45 份在库 Markdown（920 KB），查出三类真实缺陷并当场改掉：八字主 CHANGELOG 占全仓文档 31%、索引 3 处同批重复、`RULE-ENGINE-REFACTOR-PLAN` 仍写「台账不回改」（509 已推翻）；减量 92%（265 KB → 22 KB）**

**性质**：文档审计＋删减（零代码、零判据、零读数；golden 未跑——本批不碰 `liuyao/` 代码面）。

### 一、审计口径

- 对象：`git ls-files "*.md"` 共 **45 份**、**920,284 字节**（含两科 references 与三份 CHANGELOG）；
  构建产物（`plugins/engine|skills`、`dsh-plugin/engine|skills`）不在库，不计入。
- 判据三条：① 与 `DOCS.md` 登记状态是否一致；② 与代码现行口径是否冲突（AGENTS §六.3）；
  ③ 同批身份是否在索引/正文中重复或丢失。
- **正面结论先记**：`check_root_docs`（根级 7 份、121 条路径引用、0 死链）与
  `check_docs_index`（44 份全登记可达）当时即全绿——本批的缺陷都在「状态与口径」，不在死链。

### 二、查出的三类缺陷（都属实，非推测）

1. **一份文件吃掉三成文档体积**：`bazi/docs/CHANGELOG.md` 3948 行 / 286,214 字节 = 全仓
   Markdown 的 **31.1%**；同科 `liuyao/docs/CHANGELOG.md` 仅 475 行 / 40 KB，两科纪律差 **7 倍**。
   该文件头自述「只留最近窗口」并按 342/343 批「不再保留全文」裁过一次，实际仍存 125 节全文。
2. **历史索引有同批重复且无时序**：`bazi/docs/CHANGELOG-HISTORY-INDEX.md` 里
   第三百一十一/三百一十/三百零八批各出现两次（首次 10-27、复现夹在 10-29 条目之间），
   另有 10-26／10-21 行散落在 10-29 之后——索引不是真值源，但重复行会让「批号在册」对账
   与人工检索都失真。
3. **活文档写了被推翻的决策**：`liuyao/docs/RULE-ENGINE-REFACTOR-PLAN.md` 第 102 行仍记
   「D2 台账旧指针不回改，判据侧 `_partition_remap` 转发」——509 批已按用户裁定改为**回改**，
  这正是 AGENTS §六.3「文档说的和代码做的不一致本身就是缺陷」。同文档还以「方案」在册
  挂着 D1–D5 蓝图、schema 草案、T29 三步迁移细目，而 D 系列与 T28–T31 全部已结案。

### 三、减量执行（三处，逐项可复核）

| 动作 | 前 | 后 | 减少 |
|---|---|---|---|
| `bazi/docs/CHANGELOG.md` 收紧为**最近 15 批**（与六爻同口径） | 3948 行 / 286 KB | 296 行 / 21.8 KB | **−92.4%** |
| `bazi/docs/CHANGELOG-HISTORY-INDEX.md` 去重＋补录 | 89 行 / 3 处重复 | 195 行 / **173 条不重复** | 重复 0 |
| `liuyao/docs/RULE-ENGINE-REFACTOR-PLAN.md` 降为结案记录 | 109 行（方案） | 50 行（结构＋完成台账＋边界） | −54% |

- **一条批号不少**：脚本按 `HEAD` 版两文件取 `## 日期 第N批`，与新盘做集合比对——
  八字侧 **188 个批号前后一致（丢失 0、新增 0）**；六爻侧 45 个不动。
- 移出的 110 节按「标题一行」入索引（日期与批号原样保留，正文在 git 历史）；索引内已有序的
  不重复追加，重复行按批号保留首行。
- `DOCS.md` 同步两行状态：八字 CHANGELOG 窗口改成「最近 15 批（510 起与六爻同口径）」、
  `RULE-ENGINE-REFACTOR-PLAN` 状态由「活文档」改「归档留证」。
- 结案记录里删掉的是**论证与草案**（为什么改、四层架构、规则 JSON schema、T29 三步细目），
  保留的是**现行结构与真源位置**（`rules/` 四件、`engine/pipeline|classical`、台账与规则层的分工、
  509 后的指针口径）——删的是过程，不是判据。

### 四、验证

- `check_batch_num`：孤儿 0（移入索引的批号仍被扫到；342 批起本门同时读主文件与索引）。
- `check_root_docs` 121 条引用 0 死链；`check_docs_index` 44 份全登记。
- `liuyao/dev_tools/check.py`、`bazi/dev_tools/check.py` 全绿（文档门在内）。
- **未跑** golden 与 build/selftest：本批不改任何 `.py`／`data`，六爻代码面零接触；
  分发产物不打包 Markdown，包体不变。

### 五、边界

- 「最近 15 批」是**两科共用窗口**；再往后让窗口滑动时，同批把退出窗口的标题补进索引即可。
- 归档留证类（`ARCHITECTURE-PLAN.md`、`SANMING-SIKU-COLLATION.md`）本批不动：它们是
  「结论在 CHANGELOG、正文留证」的既定形态，删掉会把可追溯性交给 git 单点。
- 索引不重排历史顺序（只去重、只追加），避免一次「美化」掩盖既有条目内容。

### 六、附带发现：读数账台是红的（未修，转第五百一十一批）

审计为「文档说的和代码做的不一致」取证时顺手跑了 `python liuyao/dev_tools/readout_ledger.py`
（full，44 项）：**bad=5**。本批**不改期望值**（AGENTS §六.2：禁止静默改期望），逐条立案：

| 项 | 账台期望 | 实跑 | 方向 | 初判 |
|---|---|---|---|---|
| `liuyao.golden` | 机械 `8f60…`／措辞 `8168…` | 机械 `96c7f5d168ca6140`／措辞同 | 同一性 | 504–506 批 capture 后**期望未跟**（503 批停在 8f60）；需按 digest 的 drift_log 回补 |
| `liuyao.zengshan_dz` | 74.4%（n=29） | **87.4%**（n=29，实跑复现） | **变好 +13** | 507/508 是重构批，按 §四.7「变好须先排除凑分/口径变化」——不得当成果，先归因哪一维抬升（`use_god_category 82.8/29`、`branch 89.7/29`） |
| `liuyao.bushi_zhengzong` | 68.1% | **65.3%**（top-1 23.7 未变） | **变差 −2.8** | 需立案：408–417 与 502/503 的连带读数是否被后续批改回 |
| `governance` | 71/48 脚本 | 74/49 | 计数落后 | 507/508 新增/迁移 `dev_tools` 脚本未回改治理图期望 |
| `登记×提交在册` | 8 | **2** | 改善 | 孤儿从 8 降到 2（509 提交补上），期望值未随之下调 |

- **同一读数在三处各自演化**：`CAPABILITY.md` 写六爻 T1 指纹 `6f70…`（344 批）、账台期望 `8f60…`
  （503 批）、盘上实值 `96c7…`（504 批起）——三个数全不同；`zengshan_dz` 同样三值
  （CAPABILITY 61.8%、账台 74.4%、实跑 87.4%）。这不是「一次没回改」，是**尚无单一真源**。
- 影响面如实记：`liuyao/dev_tools/check.py` 不含账台，故「check.py 全绿」与「账台红」可以同时成立；
  CI 的 `ledger` job 跑的就是 full 账台（见 `.github/workflows/ci.yml`），按现状会红。
  下一批（511）按上表逐项归因后改期望或修代码，不并进本批（本批零代码，改期望会掩盖真实分家）。

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

## 2026-11-02 第四百九十六批（六爻·裸文件名死引用）
`rule_registry.json` 的 note 写「见 HANDOFF」（该件已随扁平化删除）＋「wikisource top-1 ~20% n=35」旧快照；
`check_doc_refs` 原口径明文不判裸文件名，故一直无门。共享件补 `LEGACY`（只对已知已删旧件的裸文件名，病史行豁免），
note 改指 README 外部集表；门先于修正自证（改回 `见 HANDOFF` 即红，逐字节还原后全绿）。读数不变。

## 2026-11-02 第四百九十五批（八字·代码书证扩面）
共享件把代码书证门从 `scripts/core` 扩到 `dev_tools/eval`（八字 96+12 锚，首跑判红 10 条、9 条真错）；
六爻 [12] 描述同步为「core/scripts/dev_tools/eval（本科副本属跨科，不挂）」，本科零改动、读数不变。

## 2026-11-02 第四百九十四批（两科·书目异名）
《命理探原》/《命理探源》同书异写：共享件加 `_book_key` 别名表，L605 锚归入可解析；真探针（L605→L9999）判红并逐字节还原。

## 2026-11-02 第四百九十三批（六爻·用神词典元数据）
`question_use_gods.json` 的 `description` 写「195 条现代问法」，而 `key_count=275`、落盘 entries 合计 275（同一份数据两处事实不同）；
改 275，[12] 新增 `check_usegod_meta`（族数/键数/条数三查，缺声明也判红），selftest 五式。门先于修正自证。

## 2026-11-02 第四百九十二批（八字·注册表「语料行」）
`bazi/rule_registry.json` 3 处「语料行 2608/2612/2452」不以 L 写行号，此前无门；扩 `check_registry_line_claims` 三级解析，首跑 3/3 在册；六爻无此形态。

## 2026-11-02 第四百九十一批（六爻·用神词典族注）
`build_question_use_gods.py` 明写「note 不参与核验」，families 64–69 的 7 段「…」引文（占雨/借贷/讨债/六畜/坟墓）无门；
新增 `check_usegod_family_notes`（dz＋wikitext 两版全收）首跑 7/7——这 7 段只在 wikitext 版成立，只认 dz 会 0 命中。

## 2026-11-02 第四百九十批（八字·代码注释源L）
八字 `scripts`／`core` 51 个 `源L` 锚（`dayun.py` 49 个）此前不扫；扩 `check_bazi_code_anchors` 后首跑 51 锚、31 引文全符；六爻由本科 [14] 扫，不重复挂。

## 2026-11-02 第四百八十九批（八字·裁决散文裸行号）
`bazi/verdicts.json` 12 个底本行（14 处写法）只写行号不带引文；扩 `check_verdicts_prose_anchors`，首跑 14/14 在册，真探针（L1657→L9999）判红。

## 2026-11-02 第四百八十八批（六爻·问题题类注记）
`question_classes.json` 的 4 个源L（终身财福 L2219/L2221、天气 L1953、易隐 L1541）与 3 条「…」引文无门；
新增 `check_question_classes_notes` 后 4/4 行锚、3/3 引文全符。

> **精简口径**：主文件保留最近 **15 批**全文（政策值，不是当前节数——514 批实收 504–514 共 11 节全文
> ＋488–496 共 9 节一句话；旧版本行把政策值写成「15 批（504–513）」是把两件事钉在了一处）；
> 488–496 及更早的批次压成上面的一句话，完整标题与日期见
> [CHANGELOG-HISTORY-INDEX.md](CHANGELOG-HISTORY-INDEX.md)，需要正文时查 git log。
