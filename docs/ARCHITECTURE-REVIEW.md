# 易（Yi）· 输入→输出全链路系统工程评审

| 项 | 值 |
|---|---|
| 评审对象 | 仓库 `C:\Users\31103\Desktop\program\Yi`（八科 · 唯一内核 `yishu_core` · 双通道出报告） |
| 评审轴线 | 输入 → 运算 → 语料 → 质量门 → 输出 → 反馈 |
| 读数时点 | 2026-10-01 18:22 与 18:28:41 两次实测（本地）；期间读数已漂移，见下方行数口径声明 |
| 上一版 | [`docs/SYS-REVIEW.md`](SYS-REVIEW.md)（其「三之一、落地状态」表 10 条建议：1–9 已 ✅ 落地，#7 / #10 ⏳ 挂账） |
| 判读方法 | 沿用 SYS-REVIEW 的「逐段 · 已落地 / 仍缺口」结构；本版每条论断附 `文件:行号`，深度收敛到**可机械化的门**与**跨层一致性** |
| 铁律口径 | 本仓库内一切分数都是**古籍案例对齐分**（引擎输出与古籍案例要点的吻合度），**不是现实世界预测命中率**；引用一律带集合名 + 样本量 n + 是否未参与调参的 holdout（`AGENTS.md` §一.3） |

> **更新（2026-10-01p / 10-01t）——本版「仍缺口」栏的部分条目已落地，读时以本行为准：**
> 已落地 **A3 折中**（`check_structure` 目录级预算 + `DECLARED_HEAVY` 显式申报）、
> **A5 折中**（`request.REQUEST_FIELDS` 单一真值源 + `[1h]` 深链短键锁；附带补 `tools/report.py --seed`，
> 修「深链有、本地 CLI 无」的能力落差）、**A6 折中**（`[6b]` 报告契约门：口径句/反馈尾注在位、禁用断言词为 0）、
> **A8 残余**（合参层四处学科清单统一到 `request.DISCIPLINES`，并修复 `ziwei` 被判「未知学科」的跨层缺陷；
> 文档层三处已于 10-01n 订正）。A1 / A4 / A11 经核实为前轮已落地。
> **A2 大动血版已落地（2026-10-01t）**：应期判定口径收归内核 `core/yishu_core/yingqi.py`
> 唯一一份（两种口径并列、各自带口径语句），`synthesis/outcome_eval.py` 与
> `disciplines/liuyao/dev_tools/feedback_store.py` 双双改为调用内核；六爻侧本地支合表
> （多出「丑午」「未申」两条错项）、1900-01-31 自设锚点与自写日支反推**已删**；
> 新增门 `[1i]`（三层锁：身份/内容/行为 + 旧错项点名回归）与六爻 `[1.7]` 假例自检
> （该通道此前**零门**）。逐项证据见 `docs/CHANGELOG.md` 2026-10-01t。
> **仍未落地**：A7 的合成回填集。
> **A10 已落地（2026-10-01u）**：忠实度门由单例 `--demo` 改为 `--corpus`（12 例合成请求 ×
> 三种起卦法）；当轮即揪出并修复一处用户可见的矛盾——六爻格局层的手写六冲/六合卦名白名单
> 与 core 结构判据冲突（详见 CHANGELOG 10-01u）。
> **A6 大动血已落地（2026-10-02c）**：`[6b]` 在既有结构断言之上，对**八科 render 段
> Markdown 取逐字节指纹**（基线 `data/golden/render_digest.json`），漂移即判败，重捕须
> `tools/check.py --raise-render --reason`（理由必填）。未采本项原方案的 `golden_kit` 三层改造
> （要动八科 `golden.py` + 八个 digest，收益相同而 blast radius 大得多）。负例自证见 CHANGELOG 10-02c。
> 逐项证据见 `docs/CHANGELOG.md` 2026-10-01p。

> **本版不重提已落地项。** SYS-REVIEW「三之一」表标 ✅ 的 9 条（`docs/SYS-REVIEW.md:146-151`、`:153-154`）视为既有资产，只在「已落地」栏引用为**证据**，绝不出现在「仍缺口」栏与改进项清单里。

> **行数口径声明。** 本文所有行数由 `tools/scratch/_archreview_count.py`（splitlines 口径，排除 `site/`、`tools/scratch/` 下的副本）在同一次运行内测得，可重跑复核。**该读数与仓库文档中的既有读数不一致**，这是本次评审发现的问题之一（见 §二 A8）：`docs/HANDOFF.md:47` 记「scripts/ 37 文件 / 18,578 行」，`:248` 记「37 / 18,560」，而本次实测为 **37 文件 / 18,117 行**。原因有二：一是 `tools/scratch/` 下已出现 `scripts-backup-20261001/`、`regress-proof-20261001/`、`web-review/before-site/` 三处备份目录，说明**另一条瘦身工作流正在并行改动六爻**；二是各文档的计数口径（是否含 `dev_tools/`、是否含空行、`wc -l` vs `splitlines`）从未统一。因此下文凡引用行数，均标明「本次实测」并给出占比，不引用文档里的旧值。**同一次评审内复测（18:28:41）已见漂移**：`disciplines` 合计由 35,907 → **36,713** 行（`lingqi` 582→751、`zeji` 1249→1464、`ziwei` 1418→1840 三科被并行工作流改动），而 `liuyao` 未变（58 文件 24,850 行 / `scripts/` 37 文件 18,117 行）。故本文正文的占比按 18:22 那次读数写作 69.2% / 50.5%；若以 18:28:41 的 36,713 为分母，则为 **67.7% / 49.3%**。两个读数都只对各自时点成立，不构成对方的证据。

---

## 一、逐段评审

### 1. 输入侧 —— 协议单一真值源已建立，但存在**第二份协议**未被覆盖

**已落地**

| 事实 | 证据 |
|---|---|
| 输入归一化是唯一的 Python 侧入口，八科清单由元组唯一定义 | `core/yishu_core/report/request.py:26`（`DISCIPLINES` 八科元组）、`:105-118`（`normalize_request`，表外/缺项直接 `ValueError`） |
| 表内取值有白名单，非法取值进不来 | `request.py:39-42`（`LIUYAO_MODES` / `MEIHUA_WAYS` / `XIAOLIUREN_WAYS`）、`:45-54`（`REQUIRED`：ming/ziwei/liuren 必须有 datetime） |
| 日期容错归一（`2026/09/30`、`2026.9.30`、`20260930` 通吃） | `request.py:69-74`（`norm_iso`）、`:77-92`（`norm_date`）、`:95-102`（`split_ints`） |
| **输入协议已被指纹锁**（SYS-REVIEW #4 落地） | `tools/check.py:584-585`（`[1f]` `request_protocol_golden.py verify`）、`tools/request_protocol_golden.py:22`（`DIGEST` 路径）、`:54`（`main`） |
| 口径声明句是共享语料的**唯一真值源**，被多宿主同点引用（SYS-REVIEW #5 落地） | `request.py:284-288`（`FOOTER_TEXT` 原文）、`:289`（`REPORT_FOOTER`）、`:293-298`（`MD_FEEDBACK_NOTE`，内含「反馈 n=0 时，一切效度讨论无从谈起」）；消费点：`tools/report.py:39`（import）、`:95`（`+ MD_FEEDBACK_NOTE` 追加） |
| 深链协议让「给一条 URL 即出报告」成立 | `web/web.js:115`（`DEEPLINK_KEYS` 短键表）、`:123`（`readDeepLink`）、`:131`（`auto: p.get('auto') === '1'`）、`:134`（`buildDeepLink`）、`:554`（auto 触发 `runReport`） |

**仍缺口**

- **深链协议是第二份输入协议，完全在 Python 指纹覆盖之外。** 短键（`d` / `q` / `auto` 等）只存在于 JS 侧别名表 `web/web.js:115-131`；`request.py:105-118` 的 `normalize_request` 只吃**规范键名**（`discipline` / `question` / `datetime` / `auto` 一类短键不在其中），`tools/request_protocol_golden.py:22` 的 digest 只锁 `normalize_request` 的正例 8 + 负例 4。也就是说：**改短键、改默认值、改 `auto` 语义，没有任何门会红**，而本地 `[1f]` 依然全绿。
- 深链的正确性只被 `tools/verify_web_parity.py` 间接摸到一点边，而它的用例是**在 Python 里构造规范 dict** 后分别喂本地与 web（`verify_web_parity.py:34` `CASES`、`:53` `NEG_CASES`、`:70` `_run_local`、`:87` `_run_web`），**从不走 `readDeepLink` 的短键解析**。因此深链解析的回归风险是零覆盖。

### 2. 运算侧 —— 真值源纪律严格，复杂度分布严重失衡

**已落地**

| 事实 | 证据 |
|---|---|
| 内核真值表只有一份，学科不得复制 | `docs/ARCHITECTURE.md:264`（「八、内核真值表（仅此一份）」） |
| 分层契约「取值层在 core / 引文层在学科 data」已登记 | `docs/ARCHITECTURE.md:286`（「八之一、合法分层」） |
| 依赖单向 `disciplines → core`，学科间互 import 有结构性扫描门 | `tools/check.py:222`（`check_structure`）、`:551`（`gate("structure", ...)`，判词「学科目录完整、无学科间 import」） |
| 四段契约 `chart→analyze→narrate→render` 定义明确 | `docs/CONTRACT.md:7-9`（§一 四段管线） |
| 巨石看门狗存在（硬失败） | `tools/check.py:260`（`max_lines = 2200`）、`:265-266`（超线即 `fails.append`） |
| 浏览器侧执行器与本地共用同一套请求→argv 映射（不是各写一份） | `web/engine_runtime.py:24`（`import runpy`）、`:98`（`runpy.run_path`）、`:51`（`_isolate` 清模块，因八科 `scripts/` 目录同名） |

**仍缺口**

- **复杂度失衡（本次实测，2026-10-01 18:22）**：

  | 口径 | 读数 |
  |---|---|
  | `disciplines/liuyao/scripts/` | 37 文件 / **18,117 行** |
  | `disciplines/liuyao/` 全部 `.py` | 58 文件 / **24,850 行** |
  | `disciplines/` 全部 `.py` | **35,907 行** |
  | liuyao scripts 占 disciplines 全 `.py` | **50.5%** |
  | liuyao（含 dev_tools/tests）占 disciplines 全 `.py` | **69.2%** |
  | 第二大单文件 | `disciplines/liuyao/scripts/classical_enhancements.py` **2,030 行**（`tools/check.py:260` 的看门狗线是 2,200，余量 **7.7%**） |
  | 骨架科对照 | `lingqi` 582 行、`liuren` 1,793 行、`ziwei` 1,418 行 |

  「学科分层统一模板」并不存在：`lingqi` 的 `scripts/` 只有 4 个文件 268 行（薄适配），`liuyao` 的 `scripts/` 是 37 个文件 18,117 行（巨石群）。同一个四段契约，一端的适配层比另一端小 **67 倍**。
- **`classical_enhancements.py` 距硬红线只剩 170 行**。一旦越过 2,200，仓库级 `--full` 直接红（`tools/check.py:265-266`）。这不是风格问题，是**下一个提交就可能踩响的硬门**。
- `ziwei` 的 `data/cases/` 为空（本次实测 `ziwei cases json=0`），而 `tools/check.py:241-243` 明确「不把目录存在当硬条件」，只在 `:246` 打印「尚无案例库」提示。命科里 ming 有 2 个案例 json、ziwei 有 0 个——同一层能力，一半有回归资产、一半没有。

### 3. 语料侧 —— 消费审计已补全，但**铁律二的隔离无门可守**

**已落地**

| 事实 | 证据 |
|---|---|
| 语料消费审计门已落地（SYS-REVIEW #1） | `tools/check.py:569-575`（`[1d]` `verdict_consumption`，**报告制：只报告不判败**） |
| 黑箱取证门已落地，且是主判据 | `tools/check.py:565-566`（`gate_sub("verdict_audit", ["tools/verdict_audit.py","--strict"])`）、`:156`（注释：「**主判据是 `tools/verdict_audit.py --strict`**（[1c] 门）：它跑真实报告」）、`:561`（「黑箱取证门：不看代码长什么样，只看用户读到什么」） |
| 语料池统计时刻意排除案例库与产物快照，避免把案例算成语料 | `tools/verdict_audit.py:171-174`（注释说明 `guard/` 是报告产物快照，「六爻一份 guard 就有 63 万汉字，五份口径叠起来吃掉语料池 67%」）、`:176`（`if p.name == "case_library.md" or {"cases","guard","scratch"} & set(p.parts)`：**主动排除**） |
| 案例统一放 `<科>/data/cases/`，散落由门挡 | `tools/check.py:240`（注释：散落别处由 `check_filenames` 挡） |

**仍缺口**

- **铁律二（案例库与预测过程物理隔离）** ~~目前**没有任何机械门在守**~~ **（A1 已落地）**：`tools/case_isolation_check.py`（静态 import 闭包 BFS + AST 判据 + 运行层 `sys.addaudithook` 实跑解读请求记录真实 `open`）已接入 `tools/check.py:847` `gate_sub`，判败制。现状是：
  - `tools/check.py:240-246` 把 `data/cases/` **只做分级打印**，并在 `:241-243` 写明「这里不把『目录存在』当硬条件——空目录 git 带不走，拿它当『分层守住了』的证据只会假红」。这是**对目录存在性的豁免**，不是对**读取行为**的检查。
  - 全门清单（`tools/check.py:507-725`）逐项：版本一致性、结构契约、filenames+verdict_literals、verdict_audit、verdict_consumption、能力矩阵锁、request_protocol、内核自检、各科 `dev_tools/check.py`、八科行为指纹、六爻冒烟+忠实度、六爻四段端到端、六爻黑箱回归、synthesis 自检、站点构建+自检、同源验收、pytest——**没有任何一项检查「解读期脚本是否打开了案例库」**。
  - 唯一碰过案例库路径的代码是 `tools/verdict_audit.py:176`，而它的动作是**排除**（「不把案例库算进语料池」），与「禁止解读期访问」无关。
  - 标的物是真实存在的：`disciplines/liuyao/references/case_library.md`（165,055 B）与六爻 `data/cases/` 下 13 个 json（本次实测清单：`case_splits` / `classical_cases` / `eval_holdout` / `eval_huozhulin_holdout` / `eval_tune` / `eval_wikisource_direction` / `eval_wikisource_holdout` / `eval_yingqi_holdout` / `huozhulin_candidates` / `huozhulin_cases` / `huozhulin_qualitative` / `wikisource_cases` / `yingqi_cases`）。
  - 即：**这条铁律现由 A1 机械门守住**（非仅人自觉）；详见 `tools/case_isolation_check.py` 与 `tools/check.py:847`。原评审判词「无任何机械支撑」已过时。

### 4. 质量门 —— 覆盖广、灵敏度高，但有三处结构性盲区

**已落地**

| 门 | 证据 |
|---|---|
| 版本一致性 | `tools/check.py:547-548` |
| 结构契约（目录完整 + 无学科间 import） | `:551`（`gate("structure", check_structure(), ...)`） |
| 黑箱取证（主判据） | `:565-566` |
| 语料消费审计（报告制） | `:569-575` |
| 能力矩阵锁 | `:580`（`gate("capability_matrix", check_capability_matrix(), "llms.txt 能力矩阵与站点清单一致")`）、`:123`（`check_capability_matrix`） |
| 输入协议指纹 | `:584-585` |
| 内核自检（干支历 / API / 断语键一致性） | `:588-610` |
| 各科质量门 | `:612-615`（`gate_sub(disc, [f"disciplines/{disc}/dev_tools/check.py"], ...)`） |
| 八科行为指纹（机械层 / 措辞层分列） | `:617-622`；分层实现见 `core/yishu_core/golden_kit.py:22`（`NARRATE_PREFIX`）、`:33`（`split_rows`）、`:46`（`_digest`）、`:61`（`run`） |
| 报告忠实度（narrate 断言 vs 引擎结构，**invented / contradicted 即失败**） | `:626-628` |
| 六爻四段端到端 | `:630-658` |
| 六爻黑箱回归 ≥ 基线 11/18 | `:659-669`（`:664` 判 `>= 11`） |
| synthesis 自检 | `:672` |
| 站点构建 + 站点自检 | `:678-693` |
| 网页端/本地端同源逐字节比对 | `:698` |
| pytest | `:709` |
| 口径声明句随门输出（铁律三的机械提醒） | `:724`（「分数含义：与古籍案例要点的一致性，不代表现实预测命中率。」） |

**仍缺口**

- **盲区一：`render` 段无任何内容指纹。** 对八科 `disciplines/*/dev_tools/golden.py` 逐科 grep `render` → **八科全部 0 命中**（本次实测：lingqi / liuren / liuyao / meihua / ming / xiaoliuren / zeji / ziwei 各 0）。根门 `tools/check.py:630-658` 是唯一的 render 覆盖，而它的判据是 `:651` `if pipe_ok and report_md.is_file() and analyze_json.is_file()`——**只判产物存在，不看内容**。`core/yishu_core/golden_kit.py:33-43` 的 `split_rows` 只把 fingerprint 行切成「机械层 / `narrate_*` 措辞层」两类，render 产物不在任何一层。→ 改进项 **A6**。
- **盲区二：忠实度门只跑一个内置 demo。** `:626-628` 的 `gate_sub("faithfulness", ["tools/report_faithfulness.py","--demo"], ...)` 是**单例 demo**，不是语料集。它证明了「这条断言链能抓 invented」，**没证明「全部八科、全部读物路径都抓得到」**。→ 并入改进项 **A10**。
- **盲区三：两条 faithfulness 与 consumption 都是「报告制 vs 判败制」混用，口径不写在门里。** `:569-575` 明说是报告制（只报告不判败），`:626-628` 是判败制。两者的**强弱差异**没有任何文档统一说明，读者容易误以为二者同级。
- 门清单里**没有任何一项**覆盖：案例库隔离（A1）、反馈子系统一致性（A2）、深链协议（A5）、render 内容（A6）、文档读数一致性（A8）。
- `capability_matrix` 门只对齐 `llms.txt` ↔ `build_web.DISCIPLINE_META`（`tools/check.py:580`、`:123`），**不校验** `tools/verify_web_parity.py:59` 的同源覆盖清单——这正是 A4 能长期潜伏的原因。

### 5. 输出侧 —— 双通道同源已锁死，站点挂载集合已扩到八科

**已落地**

| 事实 | 证据 |
|---|---|
| 站点镜像源与构建入口 | `tools/build_web.py:42`（`MIRROR_DIRS = ("core","synthesis","cli")`）、`:43`（`MIRROR_FILES = ("tools/report.py",)`）、`:170`（`WEB_FILES`） |
| 站点学科清单**已含全部八科**（含骨架科 liuren / lingqi） | `tools/build_web.py:60`（`DISCIPLINE_META`）、`:126`（`liuren`）、`:138`（`lingqi`）、`:58-59`（注释：liuren 是骨架科、lingqi 断语为《靈棋經》原文逐字直录） |
| 构建期 fail-fast：站点清单必须是 `request.DISCIPLINES` 的子集 | `tools/build_web.py:289`（docstring）、`:291`、`:295` |
| 浏览器侧允许科目与站点清单同口径 | `web/engine_runtime.py:32`（`WEB_DISCIPLINES`）、`:129-132`（不在白名单即拒绝并列出支持科目） |
| 能力矩阵权威表**已明确「通道 A 挂载全部八科、三通道集合一致、无落差」**（SYS-REVIEW #3 落地并已扩科） | `llms.txt:9-18`（八科 × 三通道全 ✓）、`:20-22`（「通道 A 站点挂载**全部八科**…本地 CLI、通道 A、通道 B 的学科集合一致，无落差」） |
| 同源验收：本地子进程 vs web 同进程，MD 逐字节、HTML 只放行页头 runtime 标签差异 | `tools/verify_web_parity.py:34`（正例）、`:53`（负例）、`:70`（`_run_local`）、`:87`（`_run_web`） |
| 云端发布链：push(main) 触发 → 构建 → 站点自检 → 同源 → 上传 → 部署 | `.github/workflows/pages.yml`（工作流存在，2,324 B） |

> **修订（相对上一版架构图与旧文档）**：`llms.txt:20-22` 与 `build_web.py:126/138` 表明**通道 A 已收编骨架科，八科无落差**。凡「通道 A 只挂六科」「liuren/lingqi 仅本地 CLI 与通道 B」的表述**均已过期**，不得再作为待办依据。

**仍缺口**

- **同源验收的覆盖清单**（**A4 已落地**）：`tools/verify_web_parity.py` 的 `CASES`/`NEG_CASES` 已纳入 `liuren`/`lingqi`（见 `:61-63`），docstring 声明覆盖集合由 `build_web.DISCIPLINE_META` 派生并与站点挂载集合同一条断言绑死；原文所述 `WEB_CHANNEL_UNAVAILABLE` 常量已移除。于是：站点挂载八科与同源验收八科**一致**，骨架科（逐字直录最敏感）恰恰被纳入比对。→ 改进项 **A4 已落地**。
- **构建链在图与文档中均未表达。** `web/` → `tools/build_web.py` → `site/` → GitHub Pages 这条链在 `tools/check.py:678-693` 有实现、在 `.github/workflows/pages.yml` 有发布，但既不进架构图（旧版无对应节点），也不进任何单一总览。→ 改进项 **A9**。
- **发布链路的触发口径没有门。** `pages.yml` 的 `paths` 过滤若漏一个目录，站点就会静默不更新，而 `--full` 全绿（因为它跑的是本地构建，不校验 workflow 的 paths 表）。

### 6. 反馈回路 —— 唯一的开环，而且开环旁边多长了一套并行实现

**已落地**

| 事实 | 证据 |
|---|---|
| synthesis 侧的回填与评分入口存在 | `synthesis/cli.py:105`（`cmd_record_outcome`）、`:115`（`cmd_outcome_eval`）、`synthesis/outcome_eval.py:51`（`eval_outcomes`） |
| 反馈尾注已接线到三宿主同点（SYS-REVIEW #6 落地） | `core/yishu_core/report/request.py:293-298`（`MD_FEEDBACK_NOTE`）、`tools/report.py:39` + `:95`（报告生成处追加） |
| 六爻侧的自述隔离纪律写进了 docstring | `disciplines/liuyao/dev_tools/feedback_store.py:39`（`LOOSE_WINDOW_DAYS = 7  # loose 判定容差：预测日期 ±7 天`）、`:153`（`class FeedbackStore`）、`:214`（`load_all`）；`disciplines/liuyao/dev_tools/feedback_report.py:45`（`summary`）、`:108`（`export_csv`）、`:150`（`FeedbackStore("liuyao")`） |
| 六爻 CLI 有独立反馈入口 | `disciplines/liuyao/scripts/yi_liuyao.py:47`（`_collect_feedback`）、`:61-62`（import 并实例化 `FeedbackStore`）、`:99-100`（`--feedback` 参数）、`:137-138`（调用点） |

**仍缺口**

- **回路仍是开的（n = 0）。** `synthesis/cli.py:119` 判 `n_回填`：`return 0 if res.get("n_回填") else 1`——空集直接非零退出。SYS-REVIEW `:117` 已记「系统唯一的开环」。**这是设计上的诚实体征（没有真数据就不装成有），不是缺陷**；但它意味着 `outcome_eval` 的整条评分链（`synthesis/outcome_eval.py:35` 的 `YQ_SCORE` 名次制）**从未在真实样本上跑过一次**。→ 改进项 **A7**（把「链路可跑」与「有数据」解耦）。
- **同一语义存在两套并行实现（新发现）。**

  | | synthesis 侧 | 六爻侧 |
  |---|---|---|
  | 入口 | `synthesis/cli.py:105` `cmd_record_outcome` / `:115` `cmd_outcome_eval` | `disciplines/liuyao/scripts/yi_liuyao.py:99-100` `--feedback` → `:47` `_collect_feedback` |
  | 存储/评分 | `synthesis/outcome_eval.py:51` `eval_outcomes` | `disciplines/liuyao/dev_tools/feedback_store.py:153` `FeedbackStore`（`:214` `load_all`） |
  | 汇报 | `synthesis/cli.py:115` | `disciplines/liuyao/dev_tools/feedback_report.py:45` `summary` / `:108` `export_csv` |
  | 应期判定口径 | 名次制 `YQ_SCORE`（`synthesis/outcome_eval.py:35`） | 容差窗 `LOOSE_WINDOW_DAYS = 7`（`feedback_store.py:39`） |
  | 门覆盖 | 被 `tools/check.py:672` 的 synthesis selfcheck 覆盖（EVT001/EVT002 假例断言） | **无门**：`tools/check.py` 与 `disciplines/liuyao/dev_tools/check.py` 对 `feedback` 关键字均 0 命中 |

  两套实现**语义相同（应期回填 → 评分 → 汇报）、口径不同（名次制 vs ±7 天容差）、覆盖不同（一门有假例断言、一门无门）**，且两者都不共享 `request.py:293-298` 的同一份口径语句。→ 改进项 **A2**。
- 反馈目录里没有任何数据文件，只有 `.gitignore` 与 `README.md`（六爻 `data/feedback/`）；`synthesis/person/` 目录不存在。即「有存储位置、有读写代码、无样本」——与 A7 的结论一致，但**六爻侧的 `FeedbackStore` 连假例断言都没有**，属于「有实现、无测试、无数据」的三重空转。

---

## 二、架构级改进项

> 每条给：**问题 / 证据（file:line）/ 影响 / 改法（大动血 + 折中）/ 成本 / 风险 / 优先级**。
> 优先级判据：是否**守住铁律** > 是否**即将踩响硬门** > 是否**造成跨层不一致** > 是否只是表达式问题。

---

### A1 · 铁律二（案例库物理隔离）没有任何机械门

**问题**
`AGENTS.md` §一.2 规定 `**/cases/` 与 `references/case_library.md` 只允许三种访问场景（测试运行器 / 用户要求事后校验 / 用户主动问类似案例），解读交付前禁止打开。**这条铁律目前靠人自觉**：全门清单里没有一项检查读取行为。

**证据**
- `tools/check.py:240-246`：案例分层**只打印提示**，`:241-243` 明确不把目录存在当硬条件（怕空目录假红）。豁免的是「目录存在性」，而**不是**「解读期读取」。
- `tools/check.py:507`–`:725` 全门清单逐项含：版本一致性(`:547`)、结构(`:551`)、filenames+verdict_literals(`:557`)、verdict_audit(`:565`)、verdict_consumption(`:569`)、能力矩阵(`:580`)、request 协议(`:584`)、内核自检(`:588`)、各科门(`:612`)、八科指纹(`:617`)、六爻冒烟+忠实度(`:624`)、四段端到端(`:630`)、黑箱回归(`:659`)、synthesis(`:671`)、站点(`:674`)、同源(`:695`)、pytest(`:706`)——**无一项涉及案例库读取**。
- `tools/verdict_audit.py:176`：唯一触及该路径的代码，动作是**排除**（`if p.name == "case_library.md" or {"cases","guard","scratch"} & set(p.parts)`），与「禁止解读期访问」无关。
- 标的物真实存在：`disciplines/liuyao/references/case_library.md`（165,055 B）＋ 六爻 `data/cases/` 下 13 个 json（清单见 §一.3）。

**影响**
这是**三条铁律里唯一一条完全没有机械支撑的**。风险不是「已经违规」，而是「无法证明没有违规」：任何一次把案例要点抄进断语、或在 analyze 里比对案例，都不会有任何门变红。对外的可信度（「机械推演，不抄案例」）因此是**声明级**而非**证明级**。

**改法**

- **大动血：新增独立门 `tools/case_isolation_audit.py`，并进 `--full`。**
  1. **静态层（读源码，不跑引擎）**：对 `disciplines/*/scripts/{chart,analyze,narrate,render}.py` 与 `core/**` 做 AST + 文本双扫，命中即失败：字符串里出现 `cases/`、`case_library`、`huozhulin`、`wikisource`、`yingqi_cases`；或 `pathlib` / `open()` 组合里出现上述片段；或对 `data/cases` 的目录遍历。豁免机制**显式白名单**：只在 `dev_tools/`、`tests/`、`*_eval*.py`、`*_audit*.py`、`*_report*.py` 里放行（这些正是铁律二允许的三种场景）。
  2. **运行层（强证据）**：借 `web/engine_runtime.py` 的同进程 `runpy` 思路，在受控进程里跑一条**正常解读请求**，用 `sys.addaudithook`（Python 3.8+ 的 `open` 审计事件）记录实际打开的文件路径，断言**没有一条落在 `data/cases/**` 或 `references/case_library.md`**。这一层不依赖源码形状，**抓的是真实行为**，与 `tools/check.py:561` 的黑箱取证哲学一致。
  3. **门定位**：判败制（与 `:565` 的 verdict_audit 同级），因为铁律二不容「报告制」。
- **折中：只做静态层。** 复用 `check_structure()` 的 rglob 扫描框架（`tools/check.py:222`），在现有 `[1]` 门里加一个 `check_case_isolation()`，扫 `scripts/` 四个文件名，正则命中即 `fails.append`。约 40 行，零新依赖，能挡住 90% 的显式违规（把案例路径写死进解读代码）。

**成本**：大动血 ≈ 180–260 行新文件 + 测试；折中 ≈ 40 行。
**风险**：静态层有假阳性（注释里提到案例名就会红）——须把注释/字符串分列处理，或直接接受「解读层不许出现案例字样」这条更严但更简单的规矩。运行层需注意审计 hook 的性能与误报（`import` 遍历目录也会触发 `open`）。
**优先级：P0**。这是三条铁律中唯一的**零机械支撑**项，且实现成本可控。

---

### A2 · 应期反馈存在两套并行子系统，口径不同、覆盖不同

**问题**
同一语义（应期回填 → 评分 → 汇报）在仓库里有**两个独立实现**：synthesis 侧一套、六爻侧一套。二者口径不同、门覆盖不同、都不共享同一份口径语句。

**证据**

| | synthesis 侧 | 六爻侧 |
|---|---|---|
| 记录入口 | `synthesis/cli.py:105` `def cmd_record_outcome(args)` | `disciplines/liuyao/scripts/yi_liuyao.py:99-100`（`--feedback`）、`:47` `def _collect_feedback(...)`、`:137-138`（调用点） |
| 存储实现 | `synthesis/outcome_eval.py:51` `eval_outcomes`（读 `synthesis/person/`，该目录**不存在**） | `disciplines/liuyao/dev_tools/feedback_store.py:153` `class FeedbackStore`、`:214` `def load_all`（存储位置 `disciplines/liuyao/data/feedback/`，仅有 `.gitignore` + `README.md`，无数据文件） |
| 汇报 | `synthesis/cli.py:115` `cmd_outcome_eval` | `disciplines/liuyao/dev_tools/feedback_report.py:45` `def summary`、`:108` `def export_csv`、`:150` `store = FeedbackStore("liuyao")` |
| 评分口径 | **名次制**：`synthesis/outcome_eval.py:35` `YQ_SCORE = {1:1.0, 2:0.8, 3:0.7, 4:0.55, "late":0.35, "early":0.35, "overrun":0.0}` | **容差窗**：`disciplines/liuyao/dev_tools/feedback_store.py:39` `LOOSE_WINDOW_DAYS = 7` |
| 学科范围 | `synthesis/cli.py:215` `choices=["liuyao","ming","ziwei"]`（**3 科**）；`synthesis/normalize.py:18` `DISCIPLINES` 列 **7 科**（缺 ziwei）；`normalize.py:236` `_NORMALIZERS` 却有 **8** 个适配器 | 仅 liuyao |
| 门覆盖 | ✅ `tools/check.py:672`（`synthesis selfcheck`，含 EVT001/EVT002 假例断言） | ❌ `tools/check.py` 与 `disciplines/liuyao/dev_tools/check.py` 对 `feedback` 关键字**均 0 命中** |
| 口径句共享 | ✅ 走 `request.py:293-298` 的 `MD_FEEDBACK_NOTE` | ❌ 自述隔离纪律写在 `feedback_store.py` 的 docstring 里，**不是**共享语料 |

**影响**
1. **口径分叉**：同一个「应期是否命中」，一套按名次给分（1/0.8/0.7/0.55…），一套按 ±7 天窗口判 loose。将来真实数据回来时，**两套会给出两个数**，且都能自称「应期命中率」——直接违反铁律三的「报分必带口径」精神。
2. **门覆盖不对称**：有门的那套没有数据（`synthesis/person/` 不存在），有数据通道的那套没有门（`feedback_report.py` 从无断言跑过）。**两边都不能自证正确。**
3. **学科范围三层错位**：`synthesis/cli.py:215` 只允许 3 科回填、`normalize.py:18` 列 7 科、`normalize.py:236` 有 8 个适配器。**同一个合参层，三个清单。**
4. **腐蚀「唯一真值源」纪律**：`AGENTS.md` §二 要求同类数据只在 core 存一份；这里同类**语义**在仓库里存了两份（分属 `synthesis/` 与 `disciplines/liuyao/dev_tools/`），且学科侧那份被学科私有化——与「学科之间禁止互相 import、合参层只依赖契约」的方向相反。

**改法**

> **已落地（2026-10-01t）**：取「大动血」中的**口径归一**一支——应期判定口径（名次制得分表 +
> 容差窗常量 + 支关系表 + 日期/日支解析 + 口径语句）收归 `core/yishu_core/yingqi.py`，
> 两处消费方退化为调用方；`synthesis/person/` 与学科 `data/feedback/` 的**存储位置仍双轨**
> （未取「二选一」那一支：合参层读人档案、六爻侧读学科反馈记录，两者的数据来源本就不同，
> 强行合目录会把「人档案」概念塞进学科）。门 `[1i]` + 六爻 `[1.7]` 已把口径与旧错项锁死。

- **大动血：归一到 synthesis，六爻侧降级为薄适配。**
  - 把 `feedback_store.py:153` 的 `FeedbackStore` 上提为 `core/yishu_core/feedback/store.py`（存储位置参数化，仍按学科分目录，物理上与 `cases/` 隔离）；`feedback_store.py` 退化为 5–10 行的 re-export。
  - 把「应期判定」收敛为**唯一口径**：在 `core` 里定义 `OutcomeSpec`（容差窗 / 名次制**二选一并写进 docstring**），`synthesis/outcome_eval.py:35` 的 `YQ_SCORE` 与 `feedback_store.py:39` 的 `LOOSE_WINDOW_DAYS` 都改为**从 core 读同一份常量**，禁止各写一份。
  - 存储位置统一走一个 `feedback_root(disc)` 函数，`synthesis/person/` 与 `disciplines/*/data/feedback/` 二选一（建议后者，与 `AGENTS.md` §二「学科 data 归学科」一致）。
  - 把 `synthesis/cli.py:215` 的 `choices` 改为 `request.DISCIPLINES`（八科），`normalize.py:18` 的 `DISCIPLINES` 补齐 ziwei → **三处清单合一**。
  - 给六爻侧补上假例断言（照 `synthesis/cli.py:186` 的 `assert r["n_回填"] == 2 ...` 写法），并进 `disciplines/liuyao/dev_tools/check.py`。
- **折中：保留双轨，加一道一致性门 `tools/feedback_consistency.py`。**
  - 不合并实现，只**锁口径**：门读取两份实现的评分常量与窗口常量，断言二者来自同一个常量源（或断言二者显式声明「口径不同且互不比较」）；再断言 `synthesis/cli.py:215`、`normalize.py:18`、`normalize.py:236` 三处学科清单**互为子集且并集等于 `request.DISCIPLINES`**。
  - 六爻侧补假例断言（新文件 +10 行），纳入 `dev_tools/check.py`。
  - 成本极低，能把「三份清单」与「两个口径」立刻锁住；代价是**双轨仍在**，长期仍会漂移。

**成本**：大动血 ≈ 300–450 行（跨 `core` / `synthesis` / `disciplines/liuyao`，涉及移动文件，风险最高的一个改法）；折中 ≈ 60–90 行 + 1 个新门。
**风险**：大动血要动 `disciplines/liuyao/`（本仓最重的目录，且**另一条瘦身工作流正在并行改动它**），合并窗口期极易冲突；建议等瘦身收敛后再做。折中的风险是「锁住现状」——两个口径长期并存会被后人误读为「两个指标」，务必在门里输出一句明确的口径声明。
**优先级：P1**（不是铁律级红线，但它是**腐蚀唯一真值源纪律**的第一个实例，且修复成本低）。折中版应在下一轮即做。

---

### A3 · 复杂度失衡：六爻占全库约七成，学科分层没有统一模板

**问题**
八科共用一套四段契约，但适配层厚度差 67 倍；六爻单科吃掉了 almost 七成代码量，且第二大文件距硬红线只剩 170 行。仓库没有「学科该多厚」的模板或阈值，只有一条 2,200 行的单文件看门狗。

**证据（本次实测，2026-10-01 18:22，`tools/scratch/_archreview_count.py`）**
- `disciplines/liuyao/scripts/` 37 文件 **18,117 行**；`disciplines/liuyao/` 全 `.py` 58 文件 **24,850 行**；`disciplines/` 全 `.py` **35,907 行**。
- liuyao 占 disciplines = **69.2%**（全 `.py`）/ **50.5%**（仅 `scripts/`）。
- 骨架科对照：`lingqi` 7 文件 **582 行**、`liuren` 11 文件 **1,793 行**、`ziwei` 9 文件 **1,418 行**。
- `disciplines/liuyao/scripts/classical_enhancements.py` = **2,030 行**，硬线在 `tools/check.py:260`（`max_lines = 2200`），余量 **170 行（7.7%）**。
- `tools/check.py:265-266`：超线即 `fails.append("... 过长（{n} 行 > {max_lines}）——按域拆分，勿再堆巨石")`。
- 已落地的长期挂账项：SYS-REVIEW `:152`「#7 六爻 scripts < 15k 行 ⏳ 未达（18,560 行）」——本次实测 18,117，**仍高于 15k 门槛**。

**影响**
1. **硬门即将踩响**：`classical_enhancements.py` 只要再长 170 行，全仓 `--full` 直接红，与业务改动无关。
2. **单点风险集中**：任何针对六爻的重构都要在最重的目录里做，回归面最大（六爻黑箱回归基线仅 11/18，`:664`）。
3. **分层模板缺失导致「新科该写多少」无参照**：新学科作者没有可对标的骨架，要么像 lingqi 一样薄（582 行）要么向 liuyao 漂移。
4. **`tools/check.py:260` 的看门狗只按单文件计**，对「37 个文件合计 18,117 行」这种**分布式巨石**完全无感——真正的病理不在任何单个文件，而在目录总量。

**改法**

- **大动血：把「单文件行数」升级为「分层预算」，并把预算写进 `docs/CONTRACT.md`。**
  1. 在 `tools/check.py` 的 `check_structure()`（`:222`）里新增**目录级预算**：`disciplines/<科>/scripts/` 合计行数上限（建议 6,000，即当前 liuyao 的 1/3），并按「骨架科 / 常规科 / 重科」三档给出**不同上限**——让「重科」是一种**显式申报**，而不是默认漂移。
  2. 定义**学科分层统一模板**：`scripts/` 只放薄适配（每段 ≤ 150 行、合计 ≤ 600 行），所有推演逻辑进 `disciplines/<科>/<域>/` 子包，`dev_tools/` 只放门与生成器。模板落 `docs/CONTRACT.md` §五，并给出 `lingqi`（582 行）作为合规模板、`liuyao`（18,117 行）作为待收敛标本。
  3. 六爻侧按域拆：`classical_enhancements.py`（2,030）、`liuyao_narrate.py`（1,847）、`liuyao_step5.py`（1,687）、`effects.py`（1,415）、`liuyao_step4.py`（1,366）——按**古籍来源**拆（《增删卜易》/《火珠林》/《卜筮正宗》…）而不是按代码形态拆，这样拆分同时服务于「通用规则 + 古籍出处」的验收要求（`AGENTS.md` §四.3）。
- **折中：只把看门狗从「单文件」扩到「目录合计」，并给 `classical_enhancements.py` 单独设 2,000 行上限。**
  - 在 `check_structure()` 里加一次 `sum(splitlines) per disciplines/<科>/scripts/`，超阈值（建议 12,000，即当前值的 2/3）即失败；同时把 `max_lines` 从 2,200 降到 2,000，**逼六爻先动那一个文件**。
  - 约 25 行改动，零风险，立刻把「分布式巨石」纳入视野。

**成本**：大动血 ≈ 数周（涉及六爻全目录重排 + 大量回归）；折中 ≈ 25 行 + 一次 `classical_enhancements.py` 拆分。
**风险**：大动血与正在并行跑的瘦身工作流**直接冲突**（`tools/scratch/` 下已有 `scripts-backup-20261001/`、`regress-proof-20261001/`、`web-review/before-site/` 三处备份），必须等它收敛。折中的风险是阈值很快需要再调（但那本身是好事，说明门在起作用）。
**优先级：P1**。硬门余量只剩 7.7%，折中版应立即做。

---

### A4 · 骨架科的旁路没统一：站点已收编八科，同源验收仍排除两科

**问题**
站点挂载集合与同源验收集合**不一致**：站点已能跑全部八科，但同源比对只覆盖六科。两科（liuren / lingqi）**从未被逐字节验证过网页端与本地端同源**。

**证据**
- 站点侧**已含八科**：`tools/build_web.py:60`（`DISCIPLINE_META`）、`:126`（liuren）、`:138`（lingqi）。
- 浏览器侧白名单同口径：`web/engine_runtime.py:32`（`WEB_DISCIPLINES`）、`:129-132`（不在白名单即拒绝）。
- 权威矩阵声明无落差：`llms.txt:20-22`（「通道 A 站点挂载**全部八科**…本地 CLI、通道 A、通道 B 的学科集合一致，**无落差**」）。
- 但同源验收**仍排除两科**：`tools/verify_web_parity.py:59` `WEB_CHANNEL_UNAVAILABLE = ("liuren", "lingqi")`、`:179`（据此跳过）。
- 能力矩阵门**不校验**这一点：`tools/check.py:580`（`gate("capability_matrix", check_capability_matrix(), "llms.txt 能力矩阵与站点清单一致")`）、`:123`（`check_capability_matrix` 只比对 `llms.txt` ↔ 站点清单）。

**影响**
1. **「无落差」是声明而非证明**：`llms.txt:20-22` 说三通道集合一致，而同源门根本不跑那两科——**权威表说的与门验的不是一回事**，正中铁律三的「只给结论不给口径」。
2. 骨架科恰是**最需要同源验证**的两科：liuren 只出机械结构标签（`build_web.py:58`），lingqi 是《靈棋經》原文逐字直录（`build_web.py:59`）——这两科的输出**对文本零漂移最敏感**，却恰好不在字节比对范围内。
3. 两科在同源门上的沉默，会让「八科同源」这个结论**无法交给外部复核**。

**改法**

- **大动血：把同源验收的覆盖集合从「常量」改为「派生 + 差集断言」。**
  1. 删除 `verify_web_parity.py:59` 的 `WEB_CHANNEL_UNAVAILABLE`，改为从 `tools/build_web.py` 的 `DISCIPLINE_META` 派生 `CASES`（`:34`）与 `NEG_CASES`（`:53`）——**清单只有一份**，不再各写一份。
  2. 给 liuren / lingqi 各补 1 条正例（liuren 需带 datetime，`request.py:45-54`）与 1 条负例（lingqi 三部掷数全零这类边界，照现有负例风格）。
  3. 在 `check_capability_matrix()`（`tools/check.py:123`）里加一条断言：`llms.txt` 声称 ✓ 的通道，必须在该通道的验收用例里有对应学科——**让权威表与验收集合互相咬住**。
- **折中：保留常量，但加一道集合相等断言。**
  - 在 `tools/check.py:580` 的 `capability_matrix` 门里加 3 行：断言 `(build_web.DISCIPLINE_META 的 id 集合) − (verify_web_parity 覆盖集合) == WEB_CHANNEL_UNAVAILABLE`，并要求 `WEB_CHANNEL_UNAVAILABLE` 里的每科都带**显式豁免理由**（写在同一行注释里，理由缺省即失败）。
  - 这样「两科不验」从**静默默认**变成**显式申报**，但不能消除覆盖缺口。

**成本**：大动血 ≈ 60–120 行（含两科用例的构造与调试）；折中 ≈ 5 行。
**风险**：liuren / lingqi 进同源比对后**可能真的暴露出不一致**（这正是价值所在，但会立刻变成红灯，需要同步修）；`llms.txt:20-22` 的「无落差」表述在修好之前应改为「六科已逐字节验证、两科待补」。
**优先级：P0**。这是「权威表与门说的不是一回事」的**现行实例**，直接违反铁律三。

---

### A5 · 深链协议未入指纹：第二份输入协议零覆盖

**问题**
输入协议有两份：Python 侧的规范键名，JS 侧的短键别名。**只有前者进了 golden**。

**证据**
- Python 侧已锁：`tools/check.py:584-585`（`[1f]`）、`tools/request_protocol_golden.py:22`（`DIGEST` 路径）、`:54`（`main`）。
- 规范键名清单：`core/yishu_core/report/request.py:105-118`（`normalize_request`，**只吃规范键**）。
- 短键只在 JS 侧：`web/web.js:115`（`DEEPLINK_KEYS`）、`:123`（`readDeepLink`）、`:127`（遍历短键做映射）、`:131`（`auto: p.get('auto') === '1'`）、`:134`（`buildDeepLink`）。
- 同源验收不走深链：`tools/verify_web_parity.py:34/53/70/87`（在 Python 构造规范 dict，直接喂两侧；**不经 `readDeepLink`**）。

**影响**
改短键名、改默认值、改 `auto=1` 的触发条件（`:554`）——**任何一条都不红**，而 `[1f]` 依旧全绿。深链是「给一条 URL 即出报告」（`AGENTS.md` §六）这条产品能力**唯一的输入面**，却是**唯一没有指纹保护**的输入面。恶意/误操作改一个字符就会静默改变所有外部 AI 的调用结果。

**改法**

- **大动血：把深链解析从 JS 收进 Python，JS 只做渲染。**
  1. 在 `core/yishu_core/report/request.py` 里新增 `parse_deep_link(query: str) -> dict`，短键表由**同一份常量**导出（Python 侧定义 → `build_web.py` 生成 JS 常量，或反之），彻底消灭双清单。
  2. `web/web.js:123` 的 `readDeepLink` 退化为一行调用宿主提供的 `parse_deep_link`（浏览器内通过 `engine_runtime.py` 暴露）。
  3. 把 `parse_deep_link` 纳入 `tools/request_protocol_golden.py` 的正/负例，与 `normalize_request` **同一次指纹**（同一个 digest 文件，两个函数）。
- **折中：在 JS 侧建一份可被 Python 校验的短键清单，并加一致性断言。**
  - 把 `web/web.js:115` 的 `DEEPLINK_KEYS` 抽成 `web/deeplink_keys.json`；`tools/request_protocol_golden.py` 增加一条用例：读该 json，断言键集与 van `normalize_request` 的规范键集**双向映射完备**；再对 `web/web.js` 做文本断言（`DEEPLINK_KEYS` 只能从 json 加载，不许内联）。
  - 约 40 行，能挡住「短键悄悄增删」，挡不住「映射逻辑改了」。

**成本**：大动血 ≈ 120–180 行（跨 `request.py` / `web/web.js` / `build_web.py` / golden，且 `web/` 与 `core/` 都属 §六「修订需跑 `--full`」的范围）；折中 ≈ 40 行。
**风险**：大动血要改浏览器侧执行路径，必须重跑 `tools/check.py --full`（含站点构建 + 同源，`:674-704`）；JS → Python 的调用链在 Pyodide 里走 `engine_runtime.py`，要确认不引入异步问题。折中的风险是「键集锁住了，语义没锁」。
**优先级：P1**。

---

### A6 · `render` 段没有任何内容指纹，只有「产物存在」冒烟

**问题**
四段契约里的 `render` 段是全库**唯一没有任何内容保护**的段落：八科 golden 全部不含 render，根门只判文件是否生成。

**证据**
- 逐科 grep：`disciplines/{lingqi,liuren,liuyao,meihua,ming,xiaoliuren,zeji,ziwei}/dev_tools/golden.py` 对 `render` **全部 0 命中**（本次实测）。
- 分层机制也不含 render：`core/yishu_core/golden_kit.py:22`（`NARRATE_PREFIX`）、`:33`（`split_rows`）、`:40-41`（只切机械层 / `narrate_*` 措施层）、`:46`（`_digest`）、`:61`（`run`）。
- 唯一的 render 覆盖是根门的冒烟：`tools/check.py:630-658`，而判据在 `:651` `if pipe_ok and report_md.is_file() and analyze_json.is_file()`——**只判存在**；`render` 步骤本身在 `:641-642`（`disciplines/liuyao/scripts/render.py` → `report_md`）。
- 八科指纹门（`:617-622`）只跑各科 `dev_tools/golden.py`，因此**天然不含 render**。

**影响**
1. **渲染层是最容易「悄悄变形」的一层**：模板改动、字段改名、markdown 表格列序调整、CJK 宽度处理——全都不会红。而 render 产物**正是用户看到的东西**，也是同源验收（`verify_web_parity.py:34`）唯一逐字节比对的对象。
2. **保护强度倒挂**：最不该变的（机械层）有指纹、最常被误改的（渲染模板）没有。同源验收只保证「本地与网页一样」，**不保证「和上一版一样」**——两边同时改坏，门依然绿。
3. 骨架科受害最深：lingqi 是原文逐字直录（`build_web.py:59`），render 段一旦改模板就可能破坏逐字性，而没有任何门会红。

**改法**

- **大动血：给八科各加一条 render golden。**
  1. 在每科 `dev_tools/golden.py` 里加第三段：固定 analyze 输入 → 跑 `render.py` → 对**归一化后的文本**取 sha256[:16]（归一化规则要写死：行尾统一、空白折叠、页头 runtime 标签剔除——后者与 `verify_web_parity.py` 的放行口径保持一致）。
  2. 扩展 `core/yishu_core/golden_kit.py:33` 的 `split_rows`，从两层（机械 / narrate）扩到**三层**（机械 / narrate / render），并让 `:61` 的 `run()` 支持第三层的 drift log。
  3. 根门加 `[5b] 八科 render 指纹`，与 `[5]` 同级（`:617-622`）。
- **折中：只给 render 加「结构断言」，不加字节指纹。**
  - 在 `tools/check.py:630-658` 的端到端冒烟里，把 `:651` 的「文件存在」升级为**结构断言**：报告 md 必须含页脚口径句（取自 `request.py:289` 的 `REPORT_FOOTER`，唯一真值源）、必须含反馈尾注（`request.py:293-298`）、表格列头集合固定、不含「预测命中率」等禁用词（可复用 `tools/check.py` 已有的 verdict_literals 词表机制）。
  - 约 50 行，只覆盖**契约级**不变式，覆盖不了排版细节；但能挡住「页脚丢了」「尾注丢了」「口径句被改」这三类最危险的漂移。

**成本**：大动血 ≈ 八科 × ~30 行 + `golden_kit` 扩展 ~60 行；折中 ≈ 50 行（集中一处）。
**风险**：字节指纹对**有意改版**会频繁红，需要配套的 `capture` 理由机制（`golden_kit.py:61` 的 `run()` 已要求必填理由，可直接复用）；结构断言的风险是「看起来有保护，实际很薄」——必须在门输出里标明它只是结构级。
**优先级：P1**。折中版成本极低，建议先落。

---

### A7 · 反馈回路 n = 0 的开环：把「链路可跑」与「有数据」解耦

**问题**
`synthesis record-outcome` 整条评分链在真实样本上从未跑过一次；空集直接非零退出，导致这份能力**无法被回归测试，只能被人工相信**。

**证据**
- 空集即非零退出：`synthesis/cli.py:119`（`return 0 if res.get("n_回填") else 1`）。
- 空集返回：`synthesis/outcome_eval.py:102-103`（`{"n_回填":0,"cases":[]}`）。
- 存储位置为空：六爻 `data/feedback/` 只有 `.gitignore` + `README.md`；`synthesis/person/` 目录**不存在**。
- SYS-REVIEW `:117`：「反馈回路 —— 系统唯一的开环」。
- 已有的假例断言证明**链路本身可跑**：`synthesis/cli.py:186`（`assert r["n_回填"] == 2 and r["n_应期可评"] == 2`）。

**影响**
反馈是「口径诚实」的最后一道自证：没有真实回填，`outcome_eval` 的 `YQ_SCORE`（`synthesis/outcome_eval.py:35`）永远是纸面常量，任何调参都无法用真实应期验证。更实际的问题是：**这条链路的退化（字段改名、评分表改值、窗口常量改值）不会有任何门发现**——因为门里的假例只断言 n，不断言分数。

**改法**

- **大动血：建一条「合成回填」的常驻回归集。**
  1. 在 `core/yishu_core/feedback/` 下建 12–20 条**人造应期样本**（覆盖 `YQ_SCORE` 的 7 个档位：1/2/3/4/late/early/overrun），标注为 `synthetic`，与真实反馈**分目录**存储。
  2. `synthesis/cli.py:115` 的 `cmd_outcome_eval` 增加 `--synthetic` 分支：读合成集，输出**逐档得分**并对 `YQ_SCORE` 做**表驱动断言**（每个档位的得分必须等于表里写的值）。
  3. 把 `synthesis/cli.py:119` 的空集返回从 `1` 改为**区分两种情况**：真实集为空 → 退出码 0 但打印明确的口径声明（「n=0，本项效度无从讨论」）；合成集为空 → 退出码 1（说明回归资产丢了）。
  4. 进 `tools/check.py:672` 的 synthesis 门。
- **折中：只把空集退出码改成语义化，并加一条「评分表自洽」断言。**
  - 在 `synthesis/cli.py:119` 区分「无数据」与「评测失败」；在 `outcome_eval.py` 里加一段纯函数的表驱动自测（对 `YQ_SCORE` 的 7 个档位各跑一次纯计算，断言单调性：1 > 2 > 3 > 4 > late/early > overrun = 0），挂到 `synthesis/cli.py:141-191` 的 `cmd_selfcheck`。
  - 约 30 行，零新数据；能挡住「评分表被改坏」，**不能**提供真实效度。

**成本**：大动血 ≈ 150–250 行 + 合成样本构造；折中 ≈ 30 行。
**风险**：合成集一旦被误认为「真数据」，会违反铁律三。必须在**目录名、字段名、输出文案**三处都标 `synthetic`，并让门在输出里强制打印「本集合为合成样本，不代表任何真实命中率」。折中版无此风险。
**优先级：P2**（不违反铁律，但影响能力可验证性）。折中版可顺带做。

---

### A8 · 文档层读数多源重复且互相矛盾（至少 5 处）

**问题**
同一事实（学科数、指纹值、文件行数、裁决规则条数、学科清单）在多个文档里各写一份，**已经出现互相矛盾的读数**。这直接对抗 `AGENTS.md` §二「唯一真值源」与铁律三「报分必带口径」。

**证据（5 处矛盾）**

| # | 事实 | 出处 A | 出处 B | 矛盾 |
|---|---|---|---|---|
| 1 | 学科范围 | `docs/ARCHITECTURE.md:19`「**范围（六科）**」 | `llms.txt:9-18` 八科矩阵；`tools/build_web.py:60` 八科 | A 说六科，B 说八科 |
| 2 | `report.py` 覆盖 | `docs/ARCHITECTURE.md:117`「统一报告运行器（**六科** chart→analyze→render→MD+HTML）」 | `request.py:26`（`DISCIPLINES` 八科） | 同上 |
| 3 | 金标准 288 例指纹 | `docs/ARCHITECTURE.md:240` `5c6e77ee253b0ddd` | `docs/HANDOFF.md:37` `46fd569fbe945814` | **同一个指纹，两个值** |
| 4 | 六爻 scripts 行数 | `docs/HANDOFF.md:47` 18,578 | `docs/HANDOFF.md:248` 18,560 | 同一文档内不一致；本次实测 18,117 |
| 5 | 裁决规则条数 | `SKILL.md:65`「裁决规则**四条**」 | `synthesis/cross_rules.py:6`（规则 1「各守其位」起）、`:175`（自检打印**五类**判据：越位/同向/两同一异/异向口径/缺数据降级） | 四条 vs 五条 |
| 6 | 学科清单（合参层内部） | `synthesis/cli.py:215` `choices=["liuyao","ming","ziwei"]`（3 科） | `synthesis/normalize.py:18` 列 7 科（缺 ziwei）；`:236` `_NORMALIZERS` 8 个适配器 | **同一层三份清单** |
| 7 | 同源验收覆盖 | `llms.txt:20-22`「三通道集合一致，无落差」 | `tools/verify_web_parity.py:59` 排除 liuren/lingqi | 见 A4 |

**影响**
`AGENTS.md` 开篇即写「同一批表曾在三个文件里各存一份且取值不一致」，并为此立了内核唯一真值源。**文档层正在重演同一剧本**：第 3 条（指纹两个值）与第 5 条（规则四条/五条）已经是**事实性错误**，任何引用方都会踩坑。对一个「AI 靠读文档出报告」的仓库，文档读数错误会被**逐级放大**。

**改法**

- **大动血：文档读数全部改为「派生」而非「抄写」。**
  1. 建 `tools/doc_facts.py`：从源码派生出权威读数（学科数取自 `request.py:26`；指纹取自 `disciplines/*/data/golden/digest.json`；规则条数取自 `synthesis/cross_rules.py` 的规则注册表；行数取自 `tools/scratch/_archreview_count.py` 的正式化版本），并**生成**一个 `docs/GENERATED-FACTS.md`。
  2. 各文档凡引用上述事实，一律改为「见 `docs/GENERATED-FACTS.md`」，禁止内联数值。
  3. 新增门 `[1g] doc_facts`：跑 `doc_facts.py` 并与 `docs/GENERATED-FACTS.md` 逐字比对；再对 `docs/*.md`、`SKILL.md`、`llms.txt` 做**禁用内联数值**的 grep（如「金标准 288 例指纹 \`[0-9a-f]{16}\`」这种模式一旦出现在生成文件之外即失败）。
- **折中：只修现状 + 加一条「指纹一致性」断言。**
  - 修掉第 3 条（把 `docs/ARCHITECTURE.md:240` 的 `5c6e77ee253b0ddd` 改为 `46fd569fbe945814`）、第 1/2 条（「六科」→「八科」）、第 5 条（`SKILL.md:65` 的「四条」→ 与 `cross_rules.py` 对齐）。
  - 新增门：扫全仓 markdown，凡出现 16 位 hex 指纹字面量，必须能在 `disciplines/*/data/golden/digest.json` 或 `data/golden/request_protocol_digest.json` 里找到同值——**指纹不许手抄**。约 40 行，直接消灭第 3 类错误。
  - 第 6 条（合参层三份清单）与 A2 合并处理。

**成本**：大动血 ≈ 200–300 行（含生成器 + 全文档改写）；折中 ≈ 40 行 + 三处文案修正。
**风险**：大动血会大面积触碰既有文档——**须与「减法工作流」协调**（见 §四），否则两边同时改文档必冲突。折中版零风险，立即可做。
**优先级：P0**（第 3 条已是**事实性错误**，且在这一类仓库里错误读数的放大效应最大）。

---

### A9 · 架构图自身表达力：boundary 只包 4 节点、synthesis 输入缺失、构建链缺失、全部节点无 `sources`

**问题**
上一版架构图（`.archify/architecture-yi-20261001-190000/candidate.json`）名义上表达了系统，但有四处**结构性缺口**，并且四门回执本身给出了 6 条布线修复提示未采纳。

**证据**
- **boundary 只包 4 个节点**：上一版 `candidate.json` 仅有 1 条 boundary（`security-group`，判词「铁律 · 机械运算归代码 / 案例隔离 / 口径诚实」），`wraps` 只有 `[mingg, bug, kernel, data]`。三条铁律里覆盖了「机械运算」，**没有任何区域边界表达「浏览器沙箱」「CI runner」「合参层契约」**。
- **synthesis 的输入未被表达**：`syn` 节点只有两条 dashed 反向边（来自 `rep` 与 `out`），**没有一条正向输入边**（无 `four→syn` / `bug→syn`），读者无法从图上看出合参层的输入是什么。
- **构建链未表达**：`pages` 节点的 sublabel 只写「web/ 静态站 · 深链即报告」，图里**没有** `web/` → `tools/build_web.py` → GitHub Pages 的节点与连线，尽管这条链在 `tools/build_web.py:42-43`、`:60` 与 `tools/check.py:678-693` 都有实现。
- **全部 16 个节点无 `sources` 字段**，`meta.repository` 未设置——即图上每个论断都**不可追溯**，与本文「每条论断带 file:line」的标准不一致。
- **上一版四门回执的待采纳提示**（`.archify/architecture-yi-20261001-190000/yi-architecture.finalize-summary.json`）：`visualReviewRecommendation.action = "inspect-route-readability"`，signals `{resolvedCrossovers: 2, routesOverSuggestedBends: 4, routesOverSuggestedStretch: 1}`；2 处 crossings（`webai→pyo × act→req`、`webai→act × act→req`）、4 处 detours（`webai→act` 4 弯 / `act→req` 3 弯 / `four→mingg` 4 弯 / `out→syn` 3 弯），以及 6 条 hints。

**影响**
架构图是这个仓库**唯一面向外部读者的整体视图**（`docs/AI-SOP.md` 让 AI 靠它建立系统印象）。表达力缺口会导致：
1. 读者以为「铁律只约束学科层」，看不出浏览器沙箱与 CI runner 也是隔离面；
2. 合参层在图上是个只有输出的黑箱，**它的输入契约（各科 analyze）不可见**；
3. 站点构建链隐形，读者会以为 `web/` 直接就是 Pages；
4. 无 `sources` → 图上的每条断言都**无法复核**，与仓库「机械可验」的精神相反。

**改法**

- **大动血：把架构图升级为「带证据的系统视图」。**
  1. boundary 从 1 条扩到 4 条：`铁律（机械+隔离+诚实）` 包 `four/engine/kernel/data`；`浏览器沙箱（零凭证·输入不上传）` 包 `pyo`；`CI runner（零第三方依赖·只读检出）` 包 `act`；`合参层契约（只依赖各科 analyze 输出）` 包 `syn`。
  2. 补齐 synthesis 的正向输入边（`engine→syn`），补齐构建链（`wsrc→bw→pages`）。
  3. 给关键节点挂 `sources`（`file:line`），并设 `meta.repository`（origin URL + 40 位 commit），四门全程带 `--repo-root`。
  4. 采纳 6 条布线 hints：让 `webai` 与 `act` 同行、`act` 与 `req` 同列（消灭 2 处 crossing 与 `webai→act`/`act→req` 的 4 弯/3 弯），让 `four` 与下游同列、`out` 与 `syn` 同列（消灭另外两处 4 弯/3 弯）。
- **折中：只补 boundary 与输入边，不挂 `sources`。**
  - 加 3 条 boundary、加 `engine→syn` 与构建链三节点三边、采纳 hints 重排坐标，但不做 `sources` / `meta.repository`（省去证据核对成本）。
  - 成本约为大动血的一半，但图依旧**不可追溯**。

**成本**：大动血 ≈ 一次完整重写 + 1–2 轮 `finalize` 修复（本仓已有此路径的经验）；折中 ≈ 一次重写 + 1 轮修复。
**风险**：节点变多（16 → 17）与 boundary 变多（1 → 4）会**提高布线失败概率**，需要按 hints 的布局规则（同行/同列对齐中心）预排坐标，可能要 2 轮 `finalize`。**本轮已按大动血方案执行**，结果见 §三。
**优先级：P2**（表达力问题，不违反铁律，但它是「对外可信度」的载体）。

---

### A10 · 铁律一的覆盖缺口：忠实度门只跑一个内置 demo

**问题**
铁律一（机械运算归代码、LLM 严禁心算）目前有**两个间接支撑**：机械层指纹（挡「机械结果被人为改动」）与忠实度门（挡「narrate 里编造数字」）。但忠实度门**只跑一个硬编码 demo**，覆盖不到八科、覆盖不到多读物路径。

**证据**
- 忠实度门：`tools/check.py:626-628`（`gate_sub("faithfulness", ["tools/report_faithfulness.py","--demo"], "报告忠实度（narrate 断言 vs 引擎结构）")`），判词明说「出现 invented/contradicted 即失败」（`:626` 注释）。
- 机械层指纹：`tools/check.py:617-622`（八科 `dev_tools/golden.py`）+ `core/yishu_core/golden_kit.py:33`（`split_rows` 把机械层与 `narrate_*` 措辞层分开）。
- 但**措辞层被显式排除在机械指纹之外**（`golden_kit.py:40-41`：`n_part` 单独成组），所以「narrate 里自己加一个数字」在**指纹门**上看不见；唯一能看见它的是忠实度门——而它只跑 `--demo`。

**影响**
铁律一是三条铁律里**唯一有权重最高**的一条（`AGENTS.md` §一.1 称「必须且只能由 Python 完成」）。当前它的机械保障是：机械层有指纹（强）、narrate 层只有单例 demo（弱）。这意味着**八科里只要有一科的 narrate 路径没被 demo 走到，那里就可以自由编造数字而不红**。

**改法**

- **大动血：把忠实度审计从 `--demo` 扩成「语料驱动」。**
  1. `tools/report_faithfulness.py` 增加 `--cases <path>` 模式：读各科 `data/cases/*.json`（用**允许的三种场景之一**：测试运行器，`AGENTS.md` §一.2），逐例跑完整四段，逐句比对 narrate 断言与 analyze 结构。
  2. 根门改为按科跑（照 `:612-615` 的 `for disc in SMOKE_DISCIPLINES` 结构），输出每科的 invented / contradicted 计数，任一 > 0 即失败。
  3. 与 A6 的 render 结构断言复用同一套「报告 → 结构」解析器。
- **折中：把 `--demo` 从单例扩成八科各一例。**
  - 为八科各写一条最小 demo（固定输入、固定期望的 narrate 断言集合），`tools/report_faithfulness.py` 支持 `--demo <disc>`，根门循环八科。
  - 约 80 行（八条 demo 数据 + 循环），**不碰案例库**（避免与铁律二纠缠），能覆盖「每科的 narrate 路径至少被忠实度审计走过一次」。

**成本**：大动血 ≈ 150–250 行（复用案例集但需处理铁律二的访问合规）；折中 ≈ 80 行。
**风险**：大动血一旦读案例库，就**同时触发铁律二的访问审计问题**（只能以「测试运行器」身份访问，且必须在门输出里显式声明用途）——建议先落 A1 的门，再落 A10 的大动血版。折中版无此耦合。
**优先级：P1**。

---

### A11 · 架构产物无法 pin 任何 revision：工作树领先 HEAD 132 个文件

**问题**：本轮要为架构图挂 `sources` 时发现，仓库的**可引用事实有两个互相矛盾的版本**——工作树与 HEAD。而这恰恰是架构图/评审文档「取证」的地基。

**证据**：

- `git cat-file -e HEAD:docs/SYS-REVIEW.md` 失败（未入库），而工作树里该文件存在（`docs/SYS-REVIEW.md:1-155`）——同一次评审的上一版分析**不在任何 revision 里**。
- `core/yishu_core/report/request.py` 在 `f74c7439` 上只有 **287 行**，而 archify 门实测报「requests line 289, but … has 287 lines at revision」（`repository-evidence/line-out-of-range`）；工作树里 `:284-289` 的 `FOOTER_TEXT` / `REPORT_FOOTER` 存在。
- `web/engine_runtime.py:31`（HEAD）的 `WEB_DISCIPLINES` 只列 6 科，工作树 `:31-32` 列 8 科；`tools/check.py` HEAD 682 行 vs 工作树 729 行；`llms.txt:20-22` HEAD 讲 skills 清单、工作树讲三通道集合一致。
- 结果：archify `validate` 两次失败（`repository-evidence/file-missing`、`repository-evidence/line-out-of-range`），最终只能**放弃 pin revision 与 `sources`**（见 §三）。全仓 `git status` 显示已暂存未提交文件 132 个。

**影响**：任何「以 revision 为锚」的机械门（archify 的 repository-evidence 是第一个，未来任何取证类工具都会踩同一个坑）在**工作树领先 HEAD**时全部失效或说谎。更严重的是口径层面：读者会把「HEAD 的 6 科」当成当下架构，而实际是 8 科——这与 `docs/ARCHITECTURE.md:19`「范围（六科）」的过期表述叠加，会持续产出错误结论（A8 的第 1 条正是同一个病的另一个症状）。

**改法**：

- **大动血**：把「产出架构产物」这一步移到提交之后——即制定一条纪律：**评审/架构产物只在干净工作树上生成**，并在产物里记录 `git status --porcelain` 的行数与 `HEAD` sha；门侧加一道「工作树漂移报告」（`tools/check.py` 新增 `[1g]`，比对 HEAD 与工作树在 `web/`、`core/`、`tools/` 的差异行数，超阈值就打印警告——**报告制，不阻断**，因为开发期漂移是常态）。约 200–300 行。
- **折中**：本次已是折中——**不 pin**，并在图与文档里显式声明「描述工作树、非 HEAD」。再补 5 行：评审文档头部增加一行 `HEAD 漂移` 读数（本轮为 132 个已暂存文件 / HEAD `f74c7439`），让读者一眼看到锚点状态。约 30–40 行（含 CI 报告）。

**成本**：大动血 ≈ 200–300 行（含 CI 报告门）；折中 ≈ 30–40 行。
**风险**：大动血版会给 `tools/check.py` 增压，且「只在干净工作树上生成产物」的纪律会与当前频繁迭代的节奏冲突；折中版只是声明，**不解决**取证失效，只让失效可见。
**优先级：P2**（不阻断当下产出，但它是「机械可验」这条仓规的地基问题；建议与 A8 折中版同批做，二者共享一个「读数单一权威源」的机制）。

---

### 改进项汇总（供总控取舍）

| ID | 问题一句话 | 成本（大动血 / 折中） | 风险 | 优先级 |
|---|---|---|---|---|
| **A1** | 铁律二（案例库隔离）无任何机械门 | 180–260 行 / **40 行** | 静态层假阳性；运行层 hook 性能 | **P0** |
| **A4** | 站点已挂八科，同源验收仍排除两科 | 60–120 行 / **5 行** | 补验后可能立刻红灯（正是价值） | **P0** |
| **A8** | 文档读数多源矛盾（含指纹两个值） | 200–300 行 / **40 行** | 大动血与减法工作流冲突 | **P0** |
| **A2** | 应期反馈双套并行、口径不同、覆盖不同 | 300–450 行 / **60–90 行** | 大动血要动 `disciplines/liuyao/`，与瘦身流冲突 | **P1** |
| **A3** | 六爻占 69.2%，巨石距硬线仅 170 行 | 数周 / **25 行** | 大动血与瘦身流冲突 | **P1** |
| **A5** | 深链协议（短键）零指纹覆盖 | 120–180 行 / **40 行** | 改浏览器执行路径，须全量重跑 | **P1** |
| **A6** | `render` 段无内容指纹（八科 0 命中） | ~300 行 / **50 行** | 字节指纹会频繁红，需 capture 理由 | **P1** |
| **A10** | 忠实度门只跑单例 `--demo` | 150–250 行 / **80 行** | 大动血触发铁律二访问审计 | **P1** |
| **A7** | 反馈回路 n=0，空集直接非零退出 | 150–250 行 / **30 行** | 合成集被误当真数据 | P2 |
| **A9** | 架构图 boundary/输入边/构建链/sources 缺失 | 一次重写+1~2 轮修复 / 一次重写+1 轮 | 节点变多，布线失败概率上升 | P2 |
| **A11** | 架构产物无法 pin revision：工作树领先 HEAD 132 个文件 | 200–300 行 / **30–40 行** | 大动血与迭代节奏冲突；折中版只让失效可见 | P2 |

**建议的执行序（依赖关系）**：A8（修事实性错误，零风险）→ A4（5 行，消灭「权威表与门不符」）→ A1 折中版（40 行，补上唯一零机械支撑的铁律）→ A3 折中版（25 行，先给六爻松绑硬门）→ A6 折中版 / A7 折中版（各 30–50 行）→ 待瘦身工作流收敛后做 A2 / A3 大动血版 → 最后 A5 / A9 / A10 → A11 折中版与 A8 同批（两者共享「读数单一权威源」机制，见 A11 优先级说明）。

---

## 三、目标态架构图（本轮已执行）

按 A9 的**大动血**方案重写，并采纳上一版 6 条布线提示。

| 项 | 值 |
|---|---|
| 目录 | `.archify/architecture-yi-20261001-182134/` |
| 规格 | `candidate.json`（同 schema：`architecture`） |
| 相对上一版的**结构变化** | ① boundary 由 1 条 → **5 条**（铁律一 / 唯一真值源 / 合参层契约 / 浏览器沙箱 / CI runner）；② 新增构建链三节点（`web/` 源 → `tools/build_web.py` → GitHub Pages）；③ 新增 **`engine→syn`** 正向输入边，补上合参层在图上的输入；④ 规模：**17 组件 / 19 连线 / 5 boundary / 5 cards**；⑤ 坐标按上一版 6 条 hints 重排（`webai` 与 `act` 同行、`act` 与 `req` 同列、`engine` 与 `four` 同列、`out` 与 `syn` 同列、`cli` 与 `req` 同行、`webai→pyo` 走 `bottom→left` 的下行走廊）。 |
| 四门 | `validate → deliver → check → browser-check`（由 `finalize` 一次走完） |
| **四门结果** | **全过**：`{"ok":true,"status":"pass","gates":{"validate":"pass","deliver":"pass","check":"pass","browser-check":"pass"},"diagnostics":[],"diagnosticSummary":{"total":0}}`，exit 0（`yi-architecture.finalize-summary.json:2-29`） |
| **布线信号（hints 修复效果）** | `properCrossings: 0` / `resolvedCrossovers: 0` / `routesOverSuggestedBends: 0` / `routesOverSuggestedStretch: 0` / `crossings: []` / `detours: []`，`maxBends: 2`（`yi-architecture.finalize.json:182-212`）。上一版同位置为 `resolvedCrossovers: 2` / `routesOverSuggestedBends: 4` / `routesOverSuggestedStretch: 1` —— **6 条 hints 全部消解** |
| 视口复核 | 1440×900 / 1600×1000 / 1920×1080 三个视口 `overflowX: false`，`overflowDisposition: "readable-vertical-scroll"`（`yi-architecture.browser-check.json:29-104`） |
| 回执 | 见同目录 `yi-architecture.finalize-summary.json` / `.finalize.json` / `.browser-check.json` / `.delivery.json` |
| 渲染产物 | 同目录 `yi-architecture.html`（790,361 B，sha256 `2fca30e0…`） |

> **本图故意不 pin revision、不挂 `sources`**（与 A9 原方案第 ④ 项不同，此处按实测修正）。原因是一条**门给出的硬证据**：archify 的 `repository-evidence` 门按 `meta.repository.revision` 校验，而本仓库 HEAD（`f74c7439344aef96a1cc1e2630e911bbef7d42d5`）落后工作树 132 个文件 —— 实测 HEAD 的 `web/engine_runtime.py:31` 的 `WEB_DISCIPLINES` 只有 **6 科**（工作树为 8 科）、`tools/check.py` 682 行（工作树 729 行）、`llms.txt:20-22` 讲的是 skills 清单而非「三通道集合一致」。本图描述的是**工作树**架构，若 pin 该 revision，就等于以 HEAD 之名断言工作树事实，直接违反铁律三（口径诚实）。两次 `finalize` 的失败回执（先 `repository-evidence/file-missing` 命中 `docs/SYS-REVIEW.md` 不在 HEAD，再 `repository-evidence/line-out-of-range` 命中 `request.py` 只有 287 行）就是这一落差的直接证据。该落差本身已立为改进项 **A11**。
>
> 需注意与上一版的口径差异：上一版（`.archify/architecture-yi-20261001-190000/`）同样未挂 `sources`、未 pin `repository`，但它把「站点挂载 6 科」画进了图；本版按 `tools/build_web.py:60` / `web/engine_runtime.py:32` 的实测改为八科。`browser-check` 需 `ARCHIFY_CHROME` 指向本机 Edge（`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`）——无该变量时该门为 `skipped`，不是 pass。

---

## 四、AI 痕迹反例点名（减法依据）

**`docs/ARCHITECTURE-REFACTOR-PLAN.md`（35,700 B，`docs/` 下最大文件，git 未跟踪）是典型的 AI 痕迹产物，本评审**不引用其任何结论**。** 具体病症：

1. **把已落地项当待办重提**：其 §1.2 把 `docs/SYS-REVIEW.md:146-151`、`:153-154` 已标 ✅ 的项重新列为「问题」。这正是本任务书明令禁止的错误模式（会直接污染下一棒的判断）。
2. **表格化的伪精确**：其 §3.1.1 的「六爻瘦身表」把 37 个文件**一律**写成「提取公共函数到 `chart_tables.py`」——包括 `__init__.py`（2 行 → 标注 150 行）。规范化的空话被包装成逐文件方案，是典型的大模型填充痕迹。
3. **体量与信息量倒挂**：35.7 KB 的篇幅里没有任何 `file:line` 证据，与仓库「机械可验」的标准不符。

**处置**：本评审**不删除**该文件（删除由另一条工作流统一处理），仅在此点名，供「减法」工作时作为判据：凡「把已落地项当待办」「逐文件套同一句式」「无 file:line 的大段方案」者，均属同类。

**同时建议的减法**（本次未执行，因超出写作范围）：`docs/ARCHITECTURE.md:19`、`:117` 的「六科」过期表述应改为八科；`docs/ARCHITECTURE.md:240` 的旧指纹 `5c6e77ee253b0ddd` 应改为 `46fd569fbe945814`（与 `docs/HANDOFF.md:37` 对齐）；`SKILL.md:65` 的「裁决规则四条」应与 `synthesis/cross_rules.py:175` 的五类判据对齐。以上三处属 A8 折中版范围。

---

## 五、口径与免责

- 本文所有**行数**为 `tools/scratch/_archreview_count.py`（splitlines 口径，排除 `site/` 与 `tools/scratch/` 副本）在 **2026-10-01 18:22** 与 **18:28:41** 的两次读数（`disciplines` 合计 35,907 → 36,713 行，前者作正文占比的分母、后者反映漂移速度）。仓库中另有 `docs/HANDOFF.md:47`（18,578）、`:248`（18,560）两个旧读数，且 `tools/scratch/` 下存在 `scripts-backup-20261001/`、`regress-proof-20261001/`、`web-review/before-site/` 三处备份目录，**说明另一条瘦身工作流正在并行改动六爻**——行数会继续漂移，引用时务必带上读数时点（A11）。
- 本文引用的评测分数**全部是古籍案例对齐分**（引擎输出与古籍案例要点的吻合度），**不是现实世界预测命中率**。凡引用均带集合名与 n，并标明是否未参与调参（`docs/HANDOFF.md:54-58`：tune n=20 / 95.0 / 参与调参；holdout n=12 / 89.7 / **未参与调参**；wikisource_holdout n=35 / 57.1 / **永不调参**；yingqi_holdout n=2 / 87.9 / **n 过小仅参照**；黑箱回归 18 例 12/18，基线 ≥11）。
- 本文不对任何医疗、法律、投资或重大人生决策提供意见；涉及的凶吉表述一律为**条件化倾向**，非注定结论（`core/yishu_core/report/request.py:284-288` 的口径句为本仓唯一真值源）。
- 本次评审**未修改任何 `.py`**，未改动 `disciplines/`，未重写或删除任何既有文档。产物清单见交付回报。
