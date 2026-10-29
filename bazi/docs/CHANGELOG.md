# 八字 CHANGELOG

> **第三百三十六批（A2-B）瘦身**：本文件只留最近窗口。
> **第三百四十二批精简**：更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)，`CHANGELOG-ARCHIVE.md` 全文已删除；
> 下面历史条目若提到 ARCHIVE，一律按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 3 节标题已并入索引。

## 2026-10-29 第三百五十三批（全仓）：**跨科共用契约信封 schema 落地（§3.6 关闭；八字侧同步）**

**性质**：schema＋shared gate。零引擎、零数据、零读数改动。

- 新增 `devkit/layer_contract.schema.json`；`devkit/shared/check_layer_contract.py`
  增 `validate_contract_envelope()` 零依赖信封校验（含 3 类负例），并由
  `sync_devkit.py --write` 分发到两科 `dev_tools/`。
- 八字 `check_layer_contract.py --selftest` rc=0：chart 9/analyze 26、4 条禁边、
  「信封 schema 通过」。
- 详见同批 `liuyao/docs/CHANGELOG.md` 第三百五十三批；`CONTRACT.md §四/§七` 同批回改。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十八批（八字）：**bazi README 回改 308 批读数（pattern 100.0／外部 62）＋根级文档同步**

**性质**：docs。零引擎、零数据、零读数改动。

- `bazi/README.md` 的判断维×常数段仍停在 187 批旧读：`pattern 80.6%／p=0.727 未达显著`、
  `外部 53 集`。308 批已实测 **pattern 100.0%（36/36，配对 b=9 c=0，McNemar p=0.004，
  已显著优于常数）**，339 批外部集扩样后为 **62 例**。本批按 308/339 实测回改，
  **不是新提升**（旧值保留为历史注记）。
- `GOVERNANCE.md`：八字 43 的 `build_siku_dz.py` 已随 345 批入库，clean clone 不再是 42；
  `ARCHITECTURE-PLAN.md` V9 改五 job（344 批新增 ledger）、V12 改 40 项/full bad=0、
  V13 改「327–329 六路径已补交」。
- 复验：`python bazi/dev_tools/check.py` rc=0；`readout_ledger.py` full **bad=0/40**；
  `check_root_docs.py`／`check_docs_index.py`／`check_batch_num.py` 全 rc=0。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十七批（全仓）：**329 批结构分层体检 10 项 triage（八字侧只读结论）**

**性质**：docs。零引擎、零数据。

- 329 批登记的 10 项结构体检条目已逐项复核：§3.1/§3.2/§3.3 复核不成立（0 模块级 import 环、
  [32] 零反向依赖、`effects.py` 导入名全在 `classical_enhancements.__all__`）；
  §3.4 部分成立（10 组同名，5 组跨模块重复另批）；§3.5 成立（白名单隔离，物理搬迁待办）；
  §3.6 部分成立；§4.1 体量成立（step5 已补 docstring）；§4.2/§4.3/§4.5 为设计或无可测分母，结案。
- 详细证据与处置表见同批 `liuyao/docs/CHANGELOG.md` 第三百四十七批；`CONTRACT.md §六-2` 销账，
  `AGENTS.md §一.2` 按“白名单隔离”实况改写。
- 复验：`liuyao/scripts/step5.py` docstring 不动行为，`liuyao golden verify` 双指纹零漂移。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十六批（全仓）：**`check_batch_num.py` 落地——八字 CHANGELOG 批号纳入根级门**

**性质**：root gate。零引擎、零数据改动。

- 根级 `devkit/root/check_batch_num.py` 已挂 CI `root-gates`：读两科
  `CHANGELOG.md`＋`CHANGELOG-HISTORY-INDEX.md` 的标题批号，与 `git log` 的「第N批」
  对账；允许名单从 `readout_ledger.py` 的 `SETTLED_ORPHANS` 单源读取。
- 实跑：标题批号 151、提交提及 158、未结案孤儿 0；负例五类全过。
- 详见同批 `liuyao/docs/CHANGELOG.md` 第三百四十六批；`ARCHITECTURE-PLAN §五.5` 欠账关闭。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十五批（八字）：**《三命通会》校订件补交入库 ＋ 抓取/校订链复跑 ＋ 报告元数据口径修正**

**性质**：content＋tooling＋docs。把 327–329 批一直留在工作区、导致干净 HEAD 判红的
三命通会文件正式落库；零引擎、零评分口径改动。

- **补交文件**：`data/sources/sanming_tonghui_siku.dz.txt`（1,419,789 字节，
  sha256 `47028eb5…`）、`data/sources/sanming_tonghui_siku.provenance.json`、
  `dev_tools/build_siku_dz.py`、`dev_tools/diff_siku_sanming.py`（改读校订件、章名顶格切分、
  `_meta.siku_file` 改 `.dz.txt`）、`dev_tools/scan_siku_gaps.py`（改读校订件、【】注文统一）、
  `docs/SANMING-SIKU-COLLATION.md`。
- **可复跑实测**：`fetch_siku_sanming.py` 重新抓取 12 卷，raw 1,467,204 字节／sha256
  `2d070238…`；`fetch_siku_sanming.py --check` rc=0；`build_siku_dz.py --check` rc=0
  （校订件 1,419,789 字节／sha256 `47028eb5…` 与重算一致）。
- **报告口径修正**：原底部注记把 `.meta.json` 说成“旧命名、应改 `.provenance.json`”，
  与抓取链实际契约相反——`.meta.json` 是抓取侧车（gitignore），`.provenance.json` 是
  入库真源；`build_siku_dz.py` 读前者写后者。注记已按实改写。
- **干净 HEAD**：此前 `[11]` 判红（`scan_siku_gaps.py:6` 指向旧路径）与账台
  `governance 42≠43` 均因这批文件未提交；本批落库后 clean worktree 复跑见下。
- 复验：`python bazi/dev_tools/check.py` rc=0；clean worktree `bazi check.py --fast`
  与 `readout_ledger --quick` 均 rc=0；`diff_siku_sanming.py`／`scan_siku_gaps.py`
  实跑产出可重现报告读数。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十四批（八字）：**账台 pattern 期望回填 80.6→100.0（308 批实测漏登）**

**性质**：docs/账台。零引擎、零判据、零读数改动。

- `readout_ledger.py` 的 `bazi(tiaohou96.2 pattern80.6 …)` 行仍停在 187 批旧值；
  308 批已实测 pattern **100.0%（36/36，McNemar p=0.004）** 并写入 CAPABILITY／check.py，
  但账台期望漏改。本批按 308 实测回填为 `pattern100.0`，并删掉该函数里一行重复正则
  （`th` 死变量）。
- `readout_ledger.py` full 实跑：**bad=0，已跑 40/40**；quick 实跑 rc=0，输出明确
  「已跑 34/40，跳过 6」（不再自称「全账」）。
- `python bazi/dev_tools/check.py` 全量 rc=0（本批未改八字门）。

分数含义：与古籍案例要点的一致性，不代表现实预测命中率（AGENTS.md §一.3）。

## 2026-10-29 第三百四十三批（八字）：**主 CHANGELOG 再瘦身——只留 10-29，3 节标题并入索引**

- 把 10-27 及更早的 3 个 `##` 节移入 `docs/CHANGELOG-HISTORY-INDEX.md`（标题保留、批号不变）。
- 主文件 43KB→38KB；索引 14.7KB→15.2KB；连同 342 批删除的 240KB 归档，
  八字历史记录总量由约 294KB 降至约 53KB。
- 复验：`check_docs_index` 51 份、`check_root_docs` 0 死链、`check_doc_refs` 0 死链、
  `check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十二批（八字）：**历史记录精简——删除 240KB 归档全文，只留逐批索引**

**性质**：docs（用户令"历史记录文件可以删减，精简为主"）。零代码、零判据改动。

- 删除 `docs/CHANGELOG-ARCHIVE.md`（239,520 B／81 个 `##` 标题）；
- `docs/CHANGELOG-HISTORY-INDEX.md` 改为**逐批标题索引**：原 81 节保留
  `## 日期 第N批` 标题（截 120 字），14.7KB；
- `readout_ledger` 的「登记×提交」扫描面改扫 `CHANGELOG-HISTORY-INDEX.md`；
  `check_doc_refs` 的 EXEMPT 同步；
- `DOCS.md` 八字 15→14、全仓 54→51；`AGENTS.md` 历史记录政策改为"索引为主，不保留全文"。
- 复验：`check_docs_index` rc=0（51 份）、`check_root_docs` rc=0、
  `check_doc_refs` rc=0（432 条/0 死链）、`dev_tools/check.py` rc=0、`readout_ledger --quick` rc=0。

## 2026-10-29 第三百四十一批（全仓文档收口·续）：**已关闭/已完成内容从活文档删除**

- `docs/EVAL-PLAN.md` §五：删除已完成步 1–5、7，只留未闭合的步 6（关闭登记在本卷 CHANGELOG）；
  节名改为「剩余落地项」。
- `CONTRACT.md` §六 删除已关闭原 4/5/6；`CAPABILITY.md` 删除已更正虚构欠账；
  `GOVERNANCE.md` 删除已结案案例清单；`AGENTS.md` 删一条措辞沿革；`dsh-plugin/README.md`
  删已修踩坑表。
- 复验：`check_root_docs` rc=0、`check_docs_index` rc=0（54 份）、`dev_tools/check.py` rc=0、
  `plugins/selftest.mjs` 全绿。

## 2026-10-29 第三百四十批（全仓文档收口）：**删除已执行的派发件＋把总方案压成完成记录**

**性质**：docs。零代码、零门禁判据改动。

- 删除 `DISPATCH.md`（26 个位全部执行完毕）；`ARCHITECTURE-PLAN.md` 压成完成记录
  （D1–D3、最终形态、完成台账、V1–V15 实测、偏差/欠账、显式不做），已修好的问题描述
  与 25 张卡的逐步指令从正文删除。
- `DOCS.md` 根级 8→7、总 55→54；`README.md`／`AGENTS.md`／`CONTRACT.md` 指路同步。
- 实测：`check_root_docs` rc=0、`check_docs_index` rc=0（54 份）、两科 `check.py` rc=0。

## 2026-10-29 第三百三十九批（八字，A5-1）：**按 GOVERNANCE 五档过存量——本批无降档、无删除**

- 实跑 `python dev_tools/governance_map.py`：八字 **43 脚本｜blocking 26｜nightly 0｜
  ondemand 7｜build 8｜tool 2｜未分类 0｜表中有序实无 0**（旧快照 36/25/0/5/4/2 已过期）。
- 登记 6 个存量未分类脚本：`build_dts_cases`/`build_t2s_table`/`build_siku_dz`/
  `fetch_siku_sanming` 归 build，`diff_siku_sanming`/`scan_siku_gaps` 归 ondemand
  （后三者属外部三命通会会话，**只登记不改文件**）。
- **降档/删除判据逐条对照 §一**：blocking→nightly 需连续一季 0 判红＋负例可跑＋CHANGELOG
  具名，本仓无按工具的季度判红台账；ondemand 删除需两季 0 使用记录＋活引用检查，同样
  无台账。故本批**不降不删**，只让地图不再报"未分类"。
- `readout_ledger.py --quick` 同步改期望并注明理由：governance `37→43`（含外部会话的
  `build_siku_dz.py`，clean clone 在其提交前为 42）、八字案例分母 `53→62`（语料扩样）、
  `bazi.external n53→n62（33/54）`；`tracked×ignore` 由 9 回 0（9 份历史 wikitext
  显式 negated，新增抓取件仍不入库）。账台实跑 **bad=0/全账 39**。

## 2026-10-29 第三百三十七批（八字，A3-1/A3-2）：**core 产物显式化 ＋ data/cache 层**

- **A3-1**：`.gitattributes` 给两科 `core/yishu_core/**` 标 `linguist-generated`（D1=C：
  仍入库，不 gitignore）；`kernel/sync_kernel.py` 新增 `--standalone <科> --out <目录>`，
  产出 `core＋scripts＋data/rules/golden＋data/*.json` 的独立可拷目录。
  实测：`python kernel/sync_kernel.py --standalone bazi --out %TEMP%\yi_bz_standalone`
  rc=0；`python …/scripts/chart.py --help` rc=0 且 cp936 下产物可按 UTF-8 读；
  负例：手改 `core/yishu_core/runtime.py` → `--check` rc=1 并点名，`--write` 后回绿。
- **A3-2**：`.gitignore` 加 `**/data/cache/`；`scripts/evaluate.py --save` 改落
  `data/cache/eval_*.json`；`dev_tools/corpus_reports.py` / `corpus_wiring_report.py` 与
  八字 `check.py` 的 eval_file 同步改读 cache。**迁移 0 个 / 落空 0 个**（330 批已清空盘上
  旧产物，本次无存量可迁；改写的是写入点与读取点）。
  关键验收：清空两科 `data/cache/` 后 `python dev_tools/check.py` 仍 rc=0（现场重生成
  13 个 eval 文件），`git ls-files '*/data/cache/*'` = 0。

## 2026-10-29 第三百三十六批（八字，A2-B）：**CHANGELOG 三件套瘦身 ＋ 契约文档修正 ＋ 八字侧欠账审计**

**性质**：docs。零引擎行为、零评分口径、零键面改动。

### 一、三件套（照 330 批六爻同款做法）

| 文件 | 内容 | 实测行数 |
|---|---|---|
| `docs/CHANGELOG-ARCHIVE.md` | 原文**全文，一字未删**（`read_bytes`/`write_bytes` 保字节） | 2500 |
| `docs/CHANGELOG.md` | 最近窗口：2026-10-27 及之后的条目 | 460 |
| `docs/CHANGELOG-HISTORY-INDEX.md` | 归档 71 节的逐节一句话（标题截 90 字） | 76 |

### 二、`CONTRACT.md` 三项修正

1. §三件套/§四/§五 的 `data/rules/layer_contract.json` → `<科>/data/rules/layer_contract.json`
   （根目录没有此文件，A4 诊断）；
2. §二 改为「四段职责的通用边界」，新增 **§二-bis 各科剖面**：六爻 = `step1`–`step5`；
   八字 = 单体 `analyze.py`（`bazi_factors.strength_and_pattern` → `dayun_table`/`liunian_table`
   → `conclusion`），并写明八字**无**推演链对应物、不为对称而克隆；
3. §六 新增「八字侧契约欠账审计」7 行表：**新增欠账 0 条**，`trigram_interpretation` 与
   `reasoning_chain` 两项无对应物如实标 N/A。

本轮**未改键面/禁边**，故两科 `data/rules/layer_contract.json` 不动——§七.1 的三件套条件
未触发，已在 §六 结论行注明；两科 `check_layer_contract.py --selftest` 实跑均 rc=0。

### 三、验收

- `python dev_tools/check_layer_contract.py --selftest` rc=0（3 夹具 × 两段键面、4 条禁边）；
- `python dev_tools/check.py` rc=0（含 [37] 门禁同源、[38] tests）；
- 归档件行数 2500 = 原文行数（`wc -l` 口径见 handoff）。

## 2026-10-29 第三百三十五批（八字，A2-A）：**补 `tests/`（smoke ＋ regression）并挂 [38] 门**

**性质**：tests ＋ tooling。零引擎行为改动。

- `tests/smoke_test.py`：两条起盘入参路径（公历 datetime／书载四柱）× 四段
  （chart→analyze→narrate→render）都要有产出；只验接线，不验对错。
  键面直接取 `data/rules/layer_contract.json`（chart 9／analyze 26）。
- `tests/regression_test.py`：固定 3 例的四柱与 `conclusion` 规范化哈希（前 16 位）。
  四柱是定义式机械层（干支历唯一确定），指纹只作回归哨兵，不代表正确率。
- `dev_tools/check.py` 新增 **[38] 八字 tests**：任一测试 rc≠0 即判红。
  编号取当前最大号 +1（[37] 之后；[29]–[36] 在八字侧不使用）。
- 负例自证：把期望指纹改成 `deadbeef…` → `[38]` 判红并点名该例；恢复后 rc=0。

## 2026-10-29 第三百三十二～三百三十四批（八字，A1-1/A1-2/A1-3）：**门禁内核归并到 `devkit/`＋挂 [37]**

| 批次 | 内容 |
|---|---|
| 332–334 | 11 个同名门/器归并：7 个进 `devkit/shared/` 单一真源；`check_source_readings`／`golden`／`baselines`／`feedback_store` 两科逻辑不同，按 **kernel 变体范式**登记为 4 个变体（`shared/variants/<名>.<科>.py`），不伪造"合并成一份" |
| 334 | 两科 `check.py` 挂 **[37] 门禁同源**：手改共享产物、dev_tools 野文件（`_*.py`）、第二份异名拷贝都判红 |
| 334 | `devkit/MANIFEST.json`：`files.shared` 11 项、4 个变体、8 个共享门的两科现行编号（`gate_ids`） |

归并前后逐格对拍：两科 `check.py` 均 rc=0；`check_doc_refs` 检视数 781→774（差异为
`.wikitext/.meta/_diff` 非声明载体排除与迁出文件的引用），0 条死链不变。
**八字侧 `check_doc_refs.py` 的校勘豁免改动本属外部三命通会会话的工作区改动，
由 A1-1-06 以六爻 HEAD 版（已含同款豁免）为归并源一并落库，未替该会话提交其它文件。**

## 2026-10-29 第三百三十一批（八字，A0/A1-2）：**根级文档门与 `devkit/` 骨架**

- `devkit/` 建立：`MANIFEST.json` ＋ `sync_devkit.py`（`--write`/`--check`/`--selftest`），
  handoff 目录 gitignore；
- `devkit/root/check_root_docs.py`：扫根级 8 份 `.md`，**禁 basename 兜底**；上线实测恰判红
  `AGENTS.md:200/226/262` 与 `CONTRACT.md:94` 四处 `docs/CHANGELOG.md`，A0-3 修正后 rc=0；
- `devkit/root/check_docs_index.py`：原 `liuyao/dev_tools/check_docs_index.py`（[36]）上提到根，
  六爻 `check.py` 的 [36] 段位移除，编号空出不回填；
- CI 加 `root-gates` job（`sync_devkit --check` ＋两道根级文档门）。

## 2026-10-29 第三百二十九批（八字，兼全仓整理）：**四库本转成「校订件」真源形态（可入库）＋ 清掉 55 MB 垃圾产物 ＋ 承接《结构分层体检》的未决条目立案**

**性质**：content＋tooling（新增规范化脚本 ＋ 底本换形态 ＋ 全仓清理 ＋ 未决项登记）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、底本形态没按仓库约定走＝交付物不入库

`.gitignore` 第 23–30 行早已定调（commit 17c8407）：抓取/校对原始件（维基文库转写 `*.wikitext.txt`、
元数据 `*.meta.json`）与衍生比对件 `*_diff.json` **不入库**——**校订件 `*.dz.txt` + `*.provenance.json`
才是真源**；注释里甚至直接点名 `diff_siku_sanming.py`、`scan_siku_gaps.py`。
本批前半程把四库本留在抓取件形态，**等于交付物不入库**。

新增 `dev_tools/build_siku_dz.py`：抓取件 → 校订件（只动标记形态，正文与注文**一字不改**）——
`SK anchor` → 顶格章名行（981 个）、`SK notes` → `【】`（3,272 条，**与在库 dz 本同一套注文标记**）、
版式包装（`SKQS header/footer`、`poem/onlyinclude`、注释、页脚标记）删除。

**底本形态统一后对拍口径又简化一层**（注文标记两边一致，不必再靠归一化剥【】消解差异）：

| 读数 | 327 批 | 328 批 | **329 批（校订件）** |
|---|---|---|---|
| 逐字一致章数 | 180 | 319 | **328 / 765（42.9%）** |
| dz 本无此段 | 0 | 0 | **0** |
| 反向真脱漏候选 | 92 | 26 | **16** |
| 去注文后正文互相覆盖 | — | 76.4% / 88.5% | **92.9% / 89.8%** |

校订件：`data/sources/sanming_tonghui_siku.dz.txt`（483,593 字 / 1,419,789 字节）＋
`data/sources/sanming_tonghui_siku.provenance.json`（title=「三命通会（四库全书本）」，
与在库 dz 本的「三命通会」区分开，否则 `_source_titles()` 的 title→`.dz.txt` 映射会指错底本）。

### 二、文档整理：清掉 55 MB 垃圾产物

盘点发现全仓 593 个 `.md` 里**只有 61 个是源文档**，其余全是构建产物副本
（`plugins/{engine,skills,dist}` 与五个适配器各一份同一文件）。清理清单：

| 删除 | 体积 | 理由 |
|---|---|---|
| `scratch/dist-clone/` `scratch/yi-claude/` `scratch/yan-verify/` | 24 MB | 仓库/适配器副本，`build.mjs`／`publish.mjs` 可重建 |
| `plugins/dist/` | 15 MB | 发行树产物（`publish.mjs` 生成） |
| `liuyao/outputs/` `liuyao/scratch/` | 10 MB | 一次性报告与探针产物（`.gitignore` 已定） |
| `scratch/*.png|log|txt|json|py`（38 件） | 1.5 MB | 截图、日志、一次性探针 |
| `scratch/REVIEW-2026-10-27.md` | 12 KB | **自述不入库**（结论已拆进 CHANGELOG） |
| `scratch/release-notes-v1.0.0.md` | 4 KB | 已被 `dsh-plugin/README.md` 取代（后者口径章节更全：含 CI、随机期望、封存状态） |
| `scratch/incident-20261029/` `scratch/311/` | — | 1 例自检夹具与旧批产物 |

**保留**：`dsh-plugin/dsh-yi-divination-1.0.0.tgz`（发布包）、`scratch/` 目录本身。
**未动任何被 git 跟踪的文件**（`git status` 无 ` D` 条目）。清理后 175 MB → **120 MB**。

### 三、承接《结构分层体检》的未决条目（原件按 scratch 规矩不入库，此处只留条目）

2026-10-27 全仓审查（304 批过程稿）的未决条目，原件在 scratch 一次性区、按 AGENTS §六.1
「不另立台账」不入库；删除前把条目与出处登记在此，**链不断**：

| 条目 | 要点 | 状态 |
|---|---|---|
| §3.1 三条 import 环 | `effects.py:34` 引 `classical_enhancements` 三个私有名；`engine.py` 函数体内 5 处 import（192/378/388/402/419 行） | 未修，待复核 |
| §3.2 三处明确的反向依赖 | — | 未修，待复核 |
| §3.3 私有名当公共 API | 与 §3.1 同源 | 未修，待复核 |
| §3.4 同名函数并存 7 组 | — | 未修，待复核 |
| §3.5 评测层与交付层同目录 | `case_runner.py`（365 行）、`evaluate.py`（672 行）住在 `scripts/`，隔离靠 `check_case_isolation.py:34` 的**文件名白名单**——AGENTS §一.2 承诺的是「物理隔离」，实际是「名单隔离」 | 未修，待复核 |
| §3.6 跨科「共用契约」无 schema | — | 未修，待复核 |
| §4.1 三个 2,000 行级模块 | `liuyao/scripts/step5.py` 2,176 行、`classical_enhancements.py` 2,227 行；step5 连 docstring 都没有 | **仍成立**（329 批实测） |
| §4.2 两科结构不对称 | 同一份规程两种落地 | 未修，待复核 |
| §4.3 呈现层分裂成两套语言 | 六爻 HTML 在 Python（`render.py`＋`visualization.py`＋`core/report/html.py`），八字 HTML 在 Node（`plugins/mcp/report.mjs` 315 行） | 未修，待复核 |
| §4.5 文档覆盖不到一半 | 329 批源文档 53 篇 | 待复核 |

**已解决，不再列**：§4.4「分发副本没有同源门」——`plugins/scripts/selftest.mjs` **[1] 段现为逐字节同源门**
（含负例自证，329 批实跑全绿）。

### 四、门

八字全量门 ✓、六爻全量门 ✓、`plugins/scripts/selftest.mjs` ✓、`dsh-plugin` selftest ✓；
`fetch_siku_sanming.py --check` 哈希一致、`build_siku_dz.py --check` 可复跑。

## 2026-10-29 第三百二十八批（八字）：**修掉 327 批埋的四层口径缺陷（吞字＋漏转）＋ 全量扫描与注文集合比对：结论是「两本各有所取，必须并用」**

**性质**：content＋tooling（修脚本缺陷 ＋ 新增扫描脚本 ＋ 读数更新 ＋ 结论改写）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、327 批的口径有四层问题，其中两层是我自己的实现缺陷

| 层 | 问题 | 修法 |
|---|---|---|
| 一 | 全文正则 `\{\{SK anchor\|[^\n]*\}\}` **贪婪**匹配，吞掉同行 notes 与其后正文（40 行 anchor+notes 组合、400 行 notes 后接正文）→ 四库本**少归一化 7,506 字** | 模板取「`{{` 与其后**第一个** `}}` 之间的内容」 |
| 二 | 字表转换写成逐字 `tbl.get(c,c)`，而**注文是整段字符串** append 进缓冲的 → **注文内容从未被繁简转换**，四库本注文一直是繁体，与 dz 简体注文处处失配 | 字表用 `str.maketrans` 一次编译，注文按整段 `translate` |
| 三 | 注文标记两边形态不同（dz【】3,449 处 / 四库本 `{{SK notes}}`，原文含【】0 次）→ 注文边界窗口必然失配 | 两边统一剥掉【】 |
| 四 | 字表「以 dz 本字集消歧、歧义保留原形」是**净损失**（dz 是词组转换过的转录本：「乾坤」34 处保留「乾」、「天干」213 处用「干」；四库「乾」162 处 vs dz 49 处） | 改回 zhconv 逐字表（1,308 条），生成过程留档 `dev_tools/build_t2s_table.py` |

**只修第二层，逐字一致就从 120 章涨到 311 章**；四层修完 319 章。
**读数从 180 涨到 319，不是数据变好，是口径从四层缺陷里爬出来了。**

### 二、最终读数

| 读数 | 327 批 | 328 批最终 |
|---|---|---|
| 四库本归一后字数 | 427,265 | **434,771** |
| 逐字一致章数 | 180 | **319 / 767（41.6%）** |
| 局部差异章数 | 591 | 448 |
| dz 本无此段 | 0 | **0** |
| 反向真脱漏候选（抽样 289 窗） | 92 | **26** |
| 去注文后正文互相覆盖 | — | **四库→dz 76.4% / dz→四库 88.5%** |

### 三、结论再改一次：不是「一方选择性录入」，是「两本各有所取」

328 批中期的「四库本选择性录入」说法**作废**。最硬的证据是**注文集合直接比对**
（集合比对不受一字之差干扰，比窗口匹配可靠）：

| | 条数 | 字数 |
|---|---|---|
| dz 注文（【】） | 3,449（去重 2,669） | 126,288 |
| 四库本 notes | 2,504（去重 2,342） | 155,994 |
| 两本都有 | 1,776 | — |
| **仅 dz 有** | **893** | **50,753** |
| **仅四库有** | **566** | **81,562** |

**两本的注文各有对方没有的内容。** 再加：dz 正文多 4.2 万字（307,383 vs 265,235）。
故两本**互补、必须并用**——dz 本给正文与注文的**量**，四库本给**章节结构与注文归属**
（981 个 `{{SK anchor}}` 把归属标得清清楚楚，dz 本无此结构）。

### 四、全量扫描（新增 `dev_tools/scan_siku_gaps.py`）

不抽样，逐 12 字滑窗全量扫。**连续失配 ≥4 个 12-gram（跨度 ≥48 字）才算一段**——
一字之差只影响 11 个窗口，按单点聚合会把「字面差异」放大成「整段缺失」
（实测按单点判会得出 35% 连续失配，那是假象）。

结果：dz 有四库无 3,534 段 / 109,957 字（25.4%）；四库有 dz 无 3,413 段 / 108,915 字（25.1%）。
**双向几乎对称** → 剩余差异**主要是字面差异**（一字之差、生僻字、异体字），
**这份区段清单不可直接当缺失清单用**；唯一干净的缺失信号是注文集合比对。

### 五、两条硬校勘条目不变（脚本内自检）

- **E1** dz 本卷标「三命通**防**」18 处（应为「会」），四库本统一「三命通會」54 处；
- **E2** dz 本「著」仅 6 处、「着」52 处（四库本「著」36 处）——四库本「復著之述作」↔ dz 本「复着之述作」；
  **引用 dz 本时凡「著」字词不可直接采信。**

### 六、产物

| 文件 | 变化 |
|---|---|
| `dev_tools/diff_siku_sanming.py` | 归一化重写（四层修正）＋行映射＋反向逐条判定；`data/collation/sanming_tonghui_siku_diff.json` 随之重出 |
| `dev_tools/scan_siku_gaps.py` | **新增**：全量双向扫描 ＋ 注文集合比对 ＋ 正文覆盖率 |
| `dev_tools/build_t2s_table.py` | **新增**：字表生成脚本（**唯一需要 zhconv 的一步**，表入库后日常零依赖） |
| `data/collation/sanming_tonghui_siku_gaps.json` | **新增**：区段清单、注文集合比对、正文覆盖率 |
| `docs/SANMING-SIKU-COLLATION.md` | 重写：§二 四层修正记录、§五 注文集合比对、§七 两本怎么用 |

### 七、局限

全量扫描的区段清单**不可直接当缺失清单**（见 §四）；`present_but_differs`（49 条抽样）里
注文位置差与字面异文尚未逐条拆；两本都没有标点，断句责任在引用者。

## 2026-10-29 第三百二十七批（八字）：**《三命通会》四库本入册（12 卷）＋ 两转录渠道内容级对拍：查出 dz 本两处系统性转写缺陷**

**性质**：content（新增底本 ＋ 新增抓取/对拍脚本 ＋ 新增校勘报告）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、先弄清两底本是什么关系

在库底本 `data/sources/sanming_tonghui_dz.dz.txt` 开头是「钦定四库全书　子部七／三命通会　术数类五」
＋四库提要＋「乾隆四十四年九月恭校上」，每卷卷首还带四库版式标记
`<子部,术数类,命书相书之属,三命通会>`（全文 12 处，均单行内闭合）——
**它本身就是四库全书本**，只是经殆知阁渠道转录。

维基文库把同一底本按卷切成 12 页数字化，于是同一本书有了**第二条转录渠道**。
所以这批做的**不是版本校勘，是转录校勘**：差异即脱漏与转写处理之差。

### 二、新底本（`dev_tools/fetch_siku_sanming.py`，可复跑）

`data/sources/sanming_tonghui_siku.wikitext.txt`：卷01–卷12，**538,884 字 / 1,467,204 字节**，
字符级保存，一字不改（**无标点**，四库扫描版原文如此，卷首自注「加標點請另外建立頁面」）。
逐卷 sha256 与全文件字节 sha256 记在 `data/sources/sanming_tonghui_siku.meta.json`。

**元数据刻意不叫 `*.provenance.json`**：八字科 `check_source_readings.py` 的 `_source_titles()`
硬编码「`*.provenance.json` → 同名 `*.dz.txt`」，任何 provenance 都会被登记成「书名 → 底本文件名」。
本底本不是 dz 底本文件，登记成 provenance 会指向**并不存在的文件**，污染既有回验的书名映射。
故另起 `*.meta.json`，台账信息写在里面。

### 三、对拍口径（三道，写死在脚本里）

**行号体系不同，绝不能按行号对拍**（四库本 981 个 `{{SK anchor}}` 章节锚点，dz 本无对应锚），只做内容级：

1. **繁简**：四库本繁体、dz 本简体，按 `dev_tools/t2s_table.json`（1153 条）转成 dz 本字形。
   该表**以 dz 本字集为判据**消歧：字 c 若 dz 本同时含 c 与其简体形（歧义，如「乾/干」）则保留原形。
   比全局词组转换准——通用转换工具会把「乾坤」转成「干坤」（实测 65 处）。
2. **注文**：四库本夹注以 `{{SK notes}}` 独立标记、dz 本与正文连排，故对拍**含注文**
   （不取注文会把「排版差异」误报成「缺文」）。
3. **模板与标签**：`{{…}}`（notes/anchor 除外）、`<…>`、全角空格与换行一律去除，**不改一个字**。

### 四、结果（`data/collation/sanming_tonghui_siku_diff.json`，报告 `docs/SANMING-SIKU-COLLATION.md`）

| 项 | 结果 |
|---|---|
| dz 本**整段缺失** | **0 章**（四库本 771 个有实质正文的章，dz 本全部找得到） |
| 逐字一致 | 180 / 771（23%） |
| 存在字面差异 | 591 / 771（77%） |
| 反向（dz 本有、四库本无） | 293 个等距采样窗中 117 窗为四库本所无（候选脱漏，含大量**表格转文本顺序差**） |

失配窗按首尾 20 字各自是否命中分四类：`middle_dropped`（首尾都在、中段 dz 本没有，**真脱漏候选**，
11 例样本）/`tail_differs`/`head_differs`（多为一字之差）/`both_differ`（多为注文位置与表格换序）。

### 五、两条硬校勘条目（**脚本内自检**，底本一变即失效）

机器猜的配对噪声大（短前缀会把配对算到别处，实测随机配对一度盖过真差异；故只收公共前缀 ≥30
的对齐，且**不做抹平**——「乾/干」「著/着」这类**就是校勘结论本身**，抹掉等于把发现藏起来）。
下列两条是逐字比对原文后确认的，计数写死在 `dev_tools/diff_siku_sanming.py` 里：

- **E1　dz 本卷标误字**：dz 本「三命通**防**」**18 处**、「三命通会」20 处（同一卷标两形并存）；
  四库本统一作「三命通會」54 处。刻工/转录层错字，不是版本差异。
- **E2　dz 本「著」被系统性过度转成「着」**：dz 本「著」仅 6 处、「着」52 处。已核实例：
  四库本「復著之述作」↔ dz 本「复着之述作」；四库本「萬物皆炳然著見」↔ dz 本「万物皆炳然着见」。
  **引用 dz 本时，凡「著」字词不可直接采信。**

### 六、局限（别跳过）

本对拍是**机器初筛**，只指出「两本不同」的位置，**不判谁是正本**（按理校断字是人的活）；
对照文本按位置截取，可能有一两字错位，定位以行号为准；
「dz 本无整段缺失」**只覆盖四库本那 771 章**，反向 117 窗候选脱漏尚未逐条人工核，
现在就说「四库本更全」是过头的；两本**都没有标点**，凡需断句的引用，断句责任在引用者。

### 七、产物

| 文件 | 是什么 |
|---|---|
| `data/sources/sanming_tonghui_siku.wikitext.txt` | 四库本原文（12 卷，卷次有 grep 标记） |
| `data/sources/sanming_tonghui_siku.meta.json` | 出处、逐卷哈希、字节哈希、许可 |
| `dev_tools/fetch_siku_sanming.py` | 抓取脚本（`--check` 只验哈希） |
| `dev_tools/diff_siku_sanming.py` | 内容级对拍脚本（含校勘条目自检） |
| `dev_tools/t2s_table.json` | 繁简字表（以 dz 本字集消歧） |
| `data/collation/sanming_tonghui_siku_diff.json` | 逐章命中率、字面差异清单、校勘条目 |
| `docs/SANMING-SIKU-COLLATION.md` | 校勘报告 |

## 2026-10-29 第三百二十六批（八字）：**调候判据补进本体（新建 `bazi_tiaohou.md`，13 条逐字可回验）＋《滴天髓阐微》9 例显式标注命例入外部集**

**性质**：content（新建一篇判据文档 ＋ 新增抽取器 ＋ 外部集扩容 ＋ 一处登记表修正）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、本体：调候这一路此前**没有文档**

全库检索「调候」「穷通宝鉴」命中 **0 处**——而 `data/tiaohou_quotes.json` 里躺着 120 条
（10 日干 × 12 月）带主用／辅用／逐字引文的成品数据，引擎 `analyze` 也已出 `tiaohou` 维度。
**数据在、引擎在、判据不在**：会话里模型要讲「这个月生人取什么用」，没有可依据的成文判据，
只能靠通识补，那就是在编。

新建 `references/bazi_tiaohou.md`：

- 底本 `data/sources/qiong_tong_bao_jian_dz.dz.txt`（殆知阁本），引文一律以它为准；
- **异文明写**：120 条引文中只有 **30 条**能在 dz 本逐字命中，其余属异文或断行差异——
  **不拿两个版本拼一句话**；
- 十二个月各一条代表判据（逐字引文 + 行号），讲清三种句式的差别：
  「专用 X」是只此一路，「先取 X 次用 Y」有先后，「X 为君 Y 为臣」是配合不是备选；
- 三条读法：调候看**太过不及**不是「缺什么补什么」；**月令是提纲、日干是受体**；
  透与藏分量不同（方向 ≠ 已经有这个字）；
- 边界写死：调候≠命局总评；不据调候断吉凶；引用原文的「富贵双全」是**记录该书怎么判**，
  不是本库背书。

`dev_tools/check_source_readings.py --doc references/bazi_tiaohou.md` 实测：
**可验 13 条，逐字命中 13 条，判红 0，NOTE 0**。

### 二、验证集：《滴天髓阐微》扩容 9 例，且只收**人工认定**的

既有 `bazi_external_cases.json` 53 例是**人工构建**的，纳入规则是「任注**显式标注**衰旺类别者全收，
无显式类别词者剔除」。该书全书 513 个命造块里，带显式类别词的只有 69 条——逐条人读后，
**机器规则只能确认 12 条**，其余是两类误判：

- **主语不是日主**：「地旺极矣」「财官太旺」「木旺金衰」「劫刃太旺」「金水太旺」……把旺衰安在别的五行上；
- **成语与通理**：「旺者冲衰衰者拔」「衰神冲旺旺神发」「身旺者杀皆是官」——不是对本造的判断。

这两类混进来等于给引擎喂**假基准**，比不收更糟。所以本批的做法是：
**机器负责定位与自洽，人工负责认定，结论固化在脚本 `APPROVED` 表里可审计可复跑**——
每条写明「书里原话是哪一句」「归到哪一档」「为什么收」。12 条认定中 3 条与在册案例同四柱，
去重后**新增 9 例**（DT001–DT009），外部集 53 → **62 例**。

机器自洽门（不靠人判）：四柱竖排解析 → 判语「X日生／X日元」须与日干相符、「X月生」须与月支相符 →
原话逐字命中 → 公历由**内核历法反查**（穷举 1900–2100 逐日取四柱全同者）→ 与在册案例四柱去重。

**两处口径写死**：

- **datetime 的年份不是命例真实年份**（同一四柱在窗口内多解，取首个命中）。本集只作
  四柱级与强弱级校验，**不用于大运/流年判断**。
- **强弱分布偏斜是文本特征不是抽样偏差**：9 例里偏弱 8、中和 1——任注多言「病」少言「旺」。
  故本集**不可用于推断总体强弱分布**，只作逐例对拍与回归。

实测：`check_case_pillars.py` 合计 414 例、174 例可对账、**174 例与内核反算一致、0 判红**；
`evaluate.py --split external_holdout` 62 例，强弱对齐 33/54（report-only，不设门槛、非命中率），
新例确有分歧（DT001 书「日主本衰」→ 引擎判偏旺），**在真实检验引擎，不是凑数**。

### 三、顺带修一处名不副实的登记

`plugins/scripts/kb-docs.mjs` 里 `bazi/bazi_yue_shi_ge.md` 登记为「月支与格局」，
而该文件实际是**五虎遁／五鼠遁歌诀**（推月推时），与登记描述不符。按现文改登记，
不按登记改文。

## 2026-10-29 第三百一十九批（八字）：**三篇「读人」文档落地（六亲家宅／疾病体质／前事验盘）＋ 引文回验器支持多底本 ＋ 评测自检不再写真实案例集**

**性质**：content＋tooling（C1/C2）。零引擎行为改动、零评分口径改动、golden 指纹未触碰。

### 一、为什么做这一批

`bazi/references/` 此前只有四篇：十神术语、纳音、月支格局、接口速查——**全是"术语与口径"，
没有一篇讲"落到人身上怎么读"**。用户问"我跟我妈怎么回事""我身体哪块要留心""你先说我以前"，
模型手上只有盘面 JSON，没有判据，只能自由发挥，这正是铁律一最该防的空档。

本批补三篇，全部以**库内古籍**为据、逐字引文、可机器回验：

| 文档 | 解决 | 主底本 | 附底本 |
|---|---|---|---|
| `references/bazi_liuqin_gongwei.md` | 父母／配偶／子女／家庭氛围；星宫双参、五种「破」的关系语义、禁句表、三样不读（人数／性别／生死） | 命理探源 | 三命通会、神峰通考、滴天髓阐微、渊海子平 |
| `references/bazi_jibing_tizhi.md` | 体质倾向与关注部位；五行配脏腑、取伤重、虚实、相生亦生病；不诊断的硬边界 | 三命通会 | 渊海子平、五行精纪、千里命稿 |
| `references/bazi_qianshi_yanpan.md` | 「你先说我以前」与出生时辰校定；时刻切法、三件事验盘、已过往运只讲感受层 | 命理探源 | 滴天髓阐微、千里命稿 |

三篇共同的写法约束（写进各篇正文）：**只读关系质地与结构倾向，不读生死、不数人数、不判离婚、
不诊断**；古法原话里的"克"一律译成"张力"，并在文中给出禁句／改写对照表。

### 二、引文回验器升级：多底本（本批唯一的工具改动）

旧 `dev_tools/check_source_readings.py` 只认文档头声明的**一个**底本；锚点左边写着别的书名时，
整条锚被剔除并记「跨书锚点，无从回验」——而六亲、疾病这类题目天然跨书，
等于新文档一半引文落在门的盲区里，NOTE 还把盲区说成"已尽力"。

改动（`check_source_readings.py`）：

1. 文档可用 `附底本：data/sources/….dz.txt` 声明多本；锚点按**最近的《书名》**绑到对应底本逐字核，
   未声明的书仍只记不判（宁可显式说"没核"，不给假绿）；
2. 书名归一（`闡→阐`、`刪→删`、`淵→渊`、`黃→黄` 等），否则正文写简体《滴天髓阐微》会回落主底本，
   把一条正确引文判成"与底本不符"；
3. `bad` 键由行号改为 `(底本, 行号)`（两本书都有 L54，旧键会串）；
4. selftest 增**多底本正负例**：挂在附底本书名下的真引文必须命中，编造引文必须判红——
   没有这条自证，"支持多底本"只是措辞。

### 三、顺带修掉一个会毁数据的地雷（如实登记）

跑 `check.py` 时发现 `data/cases/bazi_classical_cases.json` 已被覆盖成一份
`（框架自检，非古籍）` 的夹具（338 例 → 1 例），导致 holdout 为空、评测门全线报红。

- **根因**：`dev_tools/eval_selftest.py` 把夹具**写进真实案例集**，再靠 `finally` 还原。
  进程被硬杀（超时／内存／终端关闭）时 `finally` 不执行，真实案例集就被永久覆盖。
- **恢复**：从版本库恢复（`git checkout --`），实测 **338 例／tune 60／holdout 278**，与 316 批登记一致；
  覆盖前的坏副本留档 `scratch/incident-20261029/`（不入库）。本批**未改任何评分口径**，不产生读数不可比。
- **修复**：`scripts/evaluate.py` 新增 `--cases`（缺省仍为主案例集）；`eval_selftest.py` 改为
  **夹具只走系统临时目录**，真实案例集全程只读，并加一道守卫——若发现案例集里残留自检夹具，
  直接报错并提示从版本库恢复，不再"备份坏文件再还原回去"。
  这也正是 AGENTS.md §四.8「自检夹具只走临时目录」的既定口径，本器此前是唯一违例。

### 四、读数（本批实跑）

- `python dev_tools/check.py` → **rc=0，28 节全过**；`[10] 书证行号逐字回验` 由 **101 条**增至 **140 条**，
  140/140 命中、0 判红；新增三篇分别 **12／19／8 条**全部逐字命中。
- `python dev_tools/eval_selftest.py` → 9 场景全过（夹具改临时目录后行为不变）。
- `python dev_tools/check_doc_refs.py` → 394 条路径引用 0 断链。
- 金标准指纹未动（本批不碰 `analyze`，`golden.py verify` 随 `check.py` 通过）。

### 五、开口（如实登记，未在本批解决）

- **本文三篇是"读法"，不是"新因子"**：六亲宫位、脏腑对应目前仍要模型从 `chart`／`analyze`
  已有字段里组合，没有独立的结构化输出。要变成引擎因子，须按 CONTRACT §四 加键（会动 golden 指纹），
  单独一批做。
- **多底本回验只在八字科**：六爻科的 `check_source_readings.py`（688 行）早已支持按《书名》解析，
  两科实现仍不同文；是否收敛成共享实现，留待内核/门壳统一批。
- **古症候名与现代病名的映射**：本篇只做到"系统"层，不做病名映射（需医学资质）。

## 2026-10-29 第三百一十六批（八字，六爻侧主批）：**内核降为生成物 + 删掉三个用不到的六爻模块（−874 行）**

**性质**：architecture（C2）。字节层不改行为：保留下来的文件与原文逐字节相同，只删未引用模块。

1. **内核改由 `kernel/` 生成**：八字收 10 个共用 + 1 个专用（`conflict_resolution.py`）+ 4 个在册变体，
   共 **15 文件**（原 18）。`core/yishu_core/` 从此是产物，由 `python kernel/sync_kernel.py --write` 写，
   手改会被六爻 `check.py` 的 `[35]` 判红。
2. **删除** `hexagram_texts.py`（591）／`calendar_check.py`（244）／`najia.py`（39）——AST 全扫确认
   八字侧无任何 import，却一直被塞进发布包。**`yingqi.py` 不删**：`core/yishu_core/feedback.py`
   有两处转调用。
3. **口径**：`AGENTS.md` §二 与根 `README.md` 的「17 同名 13 相同」改写成"单一真源 + 4 变体 + 产物"。
4. **读数**：`bazi/dev_tools/check.py` **rc=0**（28 节）；40 例指纹 `fda7482656967518`／
   `3512deff79fa1f72` 未动；holdout 99.5%（n=278）未动。

## 2026-10-29 第三百一十二批（八字，六爻侧主批）：**仅治理图补登记与读数归位，零引擎零判据**

**性质**：bookkeeping（承接六爻 312 批归位）。本批对八字只有两处副作用，逐条记：

1. **治理图补一条 curated**：`dev_tools/check_layer_contract.py` 系 310 批新增，当时未入 `governance_map.py` 的人工分类表，
   `--strict` 会判 UNCLASSIFIED。补后重生成 `docs/GOVERNANCE-MAP.json`：脚本 36→**37**、blocking 25→**26**；
   账台 `governance` 期望值随之改（57/36→58/37、blk 24/25→25/26），理由写在六爻 312 批条目里。
2. **无代码改动**：八字 `check.py` 28 节实跑 **rc=0**，40 例指纹 `fda7482656967518`／`3512deff79fa1f72` 未动，
   holdout 99.5%（n=278）未动。310 批的分层契约门在本批复跑仍绿（chart 9 键／analyze 26 键，禁边 4 条规则）。

六爻侧的 import 收敛、禁边还清、账台假阳性修复见 `liuyao/docs/CHANGELOG.md` 同批。
