# 六爻 CHANGELOG

> **第三百四十二批精简**：`CHANGELOG-ARCHIVE.md` 全文已删除；更早条目压成逐批一句话索引
> [`CHANGELOG-HISTORY-INDEX.md`](CHANGELOG-HISTORY-INDEX.md)。下面历史条目若提到
> ARCHIVE／P0-INVENTORY，按索引读（不再保留全文）。
> **第三百四十三批**：主文件只留 2026-10-29 的条目；10-27 及更早的 51 节标题已并入索引。
> **第五百二十三批（窗口复滑＋压缩）**：按 510 批定的两科共用窗口重新收紧为**最近 15 批**，
> 每批只留一行自足的结论摘要；退出窗口的批号＋日期按 510 批规则补进历史索引（一条不丢），
> 过程叙述、分点论证与收口实跑明细一律交 git 历史／对应提交，不在主文件留存。
> 窗口与单批长度由 `devkit/root/check_docs_index.py` 现场判，**不在本文钉数**。

## 2026-11-06 第五百二十八批（全仓·门号登记同源门）：**做 CI／本地覆盖差集盘点，先确证三项正面事实（CI 14 条 `python <path>` 命令目标全可达、全仓 `.py` 用 `ast.parse(feature_version=(3,10))` 复核 0 处语法不兼容、`MANIFEST.json` 的 `gate_ids` 与两科 `check.py` 18 项逐项一致），再查出真缺口：这两份门号清单靠手工同步（518 批重排时即手工改），改一边忘另一边无任何门拦。本批扩 `devkit/sync_devkit.py --check`／`--selftest`（CI 两处已挂）用 AST 双路解析两科结构不同的门表（六爻规整三元组／八字「`# [N]` 注释 + `run([...])`」顺序块）逐项对拍；首轮正则探查误报 9 处已澄清为「抓到相邻门编号」的解析口径问题、非真分家，两套真探针（六爻 `[11]→[99]`、八字 `[27]→[99]`）均判红并逐字节复原，`--selftest` 补第 7 类负例。不新增门文件、不改 CI、不改判据、不改数据、不改读数**

## 2026-11-06 第五百二十七批（全仓·根级文档门 --selftest 假绿根治与 526 批结论更正）：**做 CI／本地覆盖差集盘点时用真探针复查「`--selftest` 是否报真账」，抓出 512 同型第二处：`devkit/root/check_root_docs.py` 的 `selftest()` 只在临时目录跑负例就 `return 0`，从不对真仓 `check()`；往 `GOVERNANCE.md` 塞一条死引用时裸门 rc=1 而 `--selftest` rc=0。526 批静态 AST 因 `fails`／`problems5` 变量名误判「已传播真实结果」而漏报，上批「未发现第二处」结论按 §六.2 作废更正。本批在 `selftest()` 末尾补真仓检查并传播 rc（含 0 引用判红），`main()` 加纯内存负例自证；修复后真探针两者同步判红、恢复后全绿，另用变异探针实证 `check_docs_index.py`／`check_pytest_bridge.py` 的 `--selftest` 确实报真账（各判红 rc=1）。不改判据、不改数据、不改读数**

## 2026-11-06 第五百二十六批（全仓·器具全体检声明面收口）：**按上批留的候选做 512 同型系统遍历：全体检基线声明 77｜PASS 77｜FAIL 0｜NOTIMPL 0，静态 AST 扫「selftest 硬编码 return 0 且无真实结果传播」仅命中 `corpus_wiring_report.py` 的纯单元夹具（测 `classify_leaf`，本身不是门），未发现第二处假绿。遍历却查出另一处真盲区：`sweep_selftests.py` 自称「全部声明器具逐真跑」，`declared_files()` 只扫两科 `dev_tools/`，`devkit/root/` 四门、`devkit/sync_devkit.py`、`kernel/sync_kernel.py` 全漏（522 批新增覆盖门在内）。本批扩声明面到 83（`devkit/shared/` 为 [37] 字节同源产物、刻意排除），并把 `--selftest` 的 wired 负例从单 victim 扩成「学科门＋根级门」两处同批注入、只跑一次 sweep 证明覆盖有牙。同批修掉注入夹具在 `core.autocrlf=input` 下把 LF 文件复原成 CRLF 的字节副作用（改 bytes 级保存/复原＋逐字节自证）。扩展后实跑声明 83｜PASS 83｜FAIL 0｜NOTIMPL 0；不改判据、不改数据、不改读数**

## 2026-11-06 第五百二十五批（全仓·生成物同源复验补齐）：**实证巡检续查剩余生成物：`CASE-LIBRARY-AUDIT-YINGQI.md` 报告头用 `date.today()`、每重生成必改且无法逐字对拍，而 [46] 的 `--check` 只回验落盘 JSON、报告无人守；`adjudication_brief.py --selftest` 自建库起从未挂线（tier=nightly、check.py／CI 都无调用）且会调用 `build()` 写真产物。本批把应期抽取拆出 `extract()`／`report_text()` 纯函数，报告头改数据源 sha256 前 8 位（幂等、可回指），`--check` 扩到报告逐字对拍（[46] 自动覆盖，零连锁）；简报拆出只读 `--check`（临时目录重算）＋负例 `--selftest` 并挂进 CI root-gates，探针不碰仓库，挂 CI 而非 check.py 是为不制造治理图／账台连锁。首跑判红、重生成转绿、手改负例判红、重生成两次逐字节不变均有实跑。不改引擎、不改数据、不改读数**

## 2026-11-06 第五百二十四批（六爻·ontology 锚定门假绿根治与产物同源）：**真探针重生成 `ONTOLOGY-CARDS.md` 抓出 4 行锚点漂移，追出 [44] 自 512 批上线只校验 `registry.json:ID` 一种形态——全量核查 55 条锚点里 12 条路径形态（8 条少 `core/`、4 条少 `domain/`）全部指向不存在文件，且 `l1_xiangshu.json` 的 `_comment` 自己写着 `core/yishu_core/symbols.py` 与字段打架；产物 4 条 JSON 锚点被手改成正确路径，按源重生成反而写回死引用。本批扩 `check_ontology.py` [44] 守 registry ID／`*.json` 路径／`*.py:SYMBOL` 三形态（未知形态判红）＋人读产物与 `render_ontology.render(当前图谱)` 逐字同源，补 6 类负例；按真源修 12 条 `engine_impl` 并重生成产物（8 行变化）。取 HEAD(523) 旧数据实跑扩面判据报 12 条死引用，修后 0 条。不改引擎、不改评分、不改读数**

## 2026-11-06 第五百二十三批（全仓·文档历史减量、窗口上门与缺口收口）：**按 510 批既定「最近 15 批」窗口复滑两科主 CHANGELOG（六爻 28→15、八字 26→15；880→37 行／379→43 行），退出窗口的批号＋日期一条不丢补进历史索引；保留批次每批只留一行自足结论摘要，过程叙述与收口明细交 git 历史。扩 `devkit/root/check_docs_index.py` 守窗口≤15 批、单批≤12 行、与 HEAD 对拍防滑窗口丢批号（首跑真抓 22 条违规、4 类负例自证），按用户令对 176 批「守台账类新增」冻结作一次限定解冻、采用 514 批写下的扩已有门形态而不新建门。并批逐条核实结案历史待办：G1「静态表外置」无对象（两道静态表同步门实跑全绿）、G3「36 个批号」结案不补、G4 305 批四条已关闭，缺口总账入 `GOVERNANCE.md`「当前真缺口」。不改判据、不改数据、不改读数**

## 2026-11-06 第五百二十二批（全仓·pytest 桥接清单单一真源与覆盖门）：**520 批留下的三份手工清单（`conftest.py:collect_ignore`、`bridge_test.py:_MAIN_STYLE`、CI `min-python-smoke` 的 6 条直跑命令）彼此独立、无任何门守护，新增测试文件会同时「不被收集、不被桥接、不被 CI 直跑」而全绿；`thinking_chain_tests.py` 不匹配 `python_files = *_test.py` 更让这条盲区隐形。本批把清单收进根 `pytest_manifest.py` 单一真源（两种消费方只 import），新增根级 `devkit/root/check_pytest_bridge.py` 对拍「清单 × 盘上文件 × CI 直跑」，并订正 520 批四处错登记；收口实跑另抓出并清掉 519 批两处存量分家（DOCS.md 漏登记一篇审计文档；[46] 接线后治理图产物与账台期望双双滞后）。不改判据、不改数据、不改评分读数，`python -m pytest` 仍 11 passed**

## 2026-11-05 第五百二十一批（全仓·消除 scripts/ 兼容 shim 反向 import eval/）：**删 356/359 批遗留的 4 个纯 re-export 兼容入口——liuyao/scripts/{evaluate,case_runner,build_portal_assets}.py、bazi/scripts/evaluate.py（仅 `from eval.X import *` 反向导入，无自有逻辑）。35 处真调用方 + 3 处 devkit 变体源改为把对应科 `eval/` 直挂 sys.path，裸 `import evaluate`/`case_runner`/`build_portal_assets` 直接命中 eval/ 真模块（单一模块身份，消除双模块陷阱）；`core/yishu_core/gate_kit.py`（liuyao/bazi/kernel 三处）与 `dev_tools/readout_ledger.py` 的子进程调用由 `scripts/evaluate.py` 改写为 `eval/evaluate.py`。`devkit/shared` 的 check_doc_refs.py（运行时读 eval/evaluate.py --engine-file 注释）、check_case_isolation.py（隔离档口径去掉「scripts/ 同名只准 shim」旧规）经 `sync_devkit.py --write` 分发两科；CAPABILITY／bazi README／两科 eval 文档／CHANGELOG／YIIN-CASE-AUDIT 等处「scripts/ 旧入口仍可用」表述改「已于 521 批删除、请走 eval/」。数据文件内 baseline_note/_comment prose 不动（改之击穿 519 批数据同步门）。门禁与同步门全绿：liuyao/bazi check EXIT=0（[37] 同源、[46] 构建器同步均过）、sync_kernel/sync_devkit --check 通过、plugins/dsh-plugin selftest RC=0（先 `build.mjs` 重建引擎产物再验）**

## 2026-11-05 第五百二十批（引入 pytest 测试框架）：**两科 tests/ 既有单测接入 pytest 运行器。six_god_wang_shuai_test.py 本即原生 pytest（def test_* + assert），直接收集；其余 main() 式（liuyao smoke/regression/thinking_chain、bazi smoke/regression，沿用 `python xxx_test.py` 习惯、errs 累积 + return 1）由根 conftest 的 collect_ignore 排除出自动收集，改由 bridge_test.py 以独立子进程 `python <file>` 桥接成 pytest 用例（进程间零 import 污染、与 CI 既有调用一致）。新增 pyproject.toml（[tool.pytest.ini_options]：testpaths/python_files=`*_test.py`/pythonpath）、根 conftest.py（collect_ignore）、bridge_test.py（subprocess 桥接）、requirements-dev.txt（pytest>=7）；CI 新增 pytest job。旧 `python tests/xxx_test.py` 直接跑路径保持不变。实跑 `python -m pytest`：11 passed（6 原生 + 5 桥接）**

## 2026-11-05 第五百一十九批（六爻构建器同步门·[46] 接入）：**6 个此前只落盘、从不挂同源复验的构建器补齐 `--check`：转译型案例集（zengshan_dz / bushi_zhengzong / yiin / yingqi）逐条回验 `expected.detail` 仍逐字命中底本/文献；用神爻位（usegod_position）与派生维度（extra_dimensions）逐字段回验与引擎当前派生一致；均不写文件、命中缺失即非零退出。六爻 `check.py` 新增 `[46]` 构建器同源复验门，把 6 个 `--check` 收口成一道同步门（[0]–[45] 已占满，[36] 为文档索引门迁出墓碑空位不复用，故取 [46]）。同步门实跑抓出并修复三处真问题：① ZD214 `detail`/`yingqi` 被手改漂移（阴云/缺寅日），已按底本 L2084 逐字改回「果于寅日云卯日大雨辰日大晴」、应期 寅日/卯日/辰日；② yingqi_cases.json `_meta` 缺 `source_sha256` 锚，已重建补齐（案例库文献逐字未变）；③ build_usegod_position 的 `compute_position` 只处理六亲+地支、漏判 `世爻` 案例（SG001/SG002），已补 `is_world`/`is_ying` 派生。实跑全绿：6 个 `--check` 全 rc=0、liuyao/bazi check EXIT=0、`sync_kernel --check`/`sync_devkit --check` 通过、两处 selftest RC=0**

## 2026-11-05 第五百一十八批（门编号规范化·跨仓重排）：**liuyao 10 个小数门号并入连续整数——[1.5]→[7]、[1.6]→[8]、[1.7]→[9]、[1.8]→[10]、[2.2]→[21]、[2.3]→[22]、[2.4]→[23]、[2.5]→[24]、[2.7]→[25]、[4.6]→[45]；其余 35 个整数号（含 [36] 文档索引门迁出后的墓碑空位）保持不变，故广泛引用的整数号（[18]/[28]/[38]/[42] 等）引用零改动。八字无小数号、其 [29]–[36] 预留空位为跨科对表保留，本批不动。内核真源 `kernel/yishu_core/common/yingqi.py` 的 `[1.7]`→`[9]` 经 `sync_kernel --write` 分发到两科 core 与 dsh-plugin/engine 副本；`plugins/engine` 与 `dsh-plugin/engine` 经 `node plugins/scripts/build.mjs` 重建逐字节一致。Node selftest 体系（[1.5]/[1.6]/[2.4]）为独立编号，非 liuyao 门，保持不动。门禁与同步门全绿：liuyao/bazi check EXIT=0、`sync_kernel --check`/`sync_devkit --check` 通过、两处 selftest RC=0**

## 2026-11-05 第五百一十七批（全仓·文档治理收口与剩余欠账定性）：**DOCS.md 四节硬编码份数（根级7／六爻19／八字14／共享层5）去除，顶部加「份数不钉死、以 `git ls-files '*.md'` 为准」声明——消除「数字无门」在索引文档自身的最后死角（AGENTS.md §六明令份数不写死，此前 DOCS.md 违反且无门守护）。同期探查确证：八字 [7] 已带 n=、六爻 render 免责语已被 516 [7] 门覆盖、dev_tools 的 parents[N] 全为根目录定位（无读数据表风险，507 批同型事故的真风险点在 scripts/ 层、515 批已根除）、check_rule_registry 三份字节同源（sync_devkit 守护）、门编号体系为非阻断可读性；门编号重排／静态表外置／scripts 兼容 shim 反向 import eval／引入 pytest 四项列为已知非阻断待办，需独立批次逐格对拍，本批不动**

## 2026-11-04 第五百一十六批（全仓·冻结面与死链门补齿）：**共享层 [5] 扩到四工具参数 schema 与 required、[7] 补报告模板禁语与免责提示语；两科死链门新加裸文件名存在性判定，实跑抓出 15 处悬空裸引用（含 SKILL.md 铁律仍指向 508 批已删的 engine.py）并逐条按实况改正**

## 2026-11-04 第五百一十五批（全仓·路径真源收敛与门盲区补齿）：**六爻 scripts 层数据路径硬算层级收进 `kernel_path` 单一真源，缺表一律抛错；案例隔离门扩到 core/ 与 data/ 并补负例，[42] 加覆盖防退化断言；零读数变更**

## 2026-11-04 第五百一十四批（全仓·文档治理、门禁补齿与结构收敛）：**四组「现在时钉数」集体过期而无一门能拦（真探针塞「999 份」两门照绿）→ 数字改指真值源并上提为 AGENTS §六.6；后半按用户令并批修完门禁假绿、契约三件套同步、静默空表、产物同源与 CI 回归五组结构性欠账；不改判据口径、不改数据、不改读数**
