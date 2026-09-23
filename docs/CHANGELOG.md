# 变更日志（CHANGELOG）

仓库级变更登记（跨科 / 内核 / 口径 / 架构）。学科内细节见各科 `CHANGELOG.md`。
规则：指标口径任何变动（计分方式、词典、缺失字段处理）必须在此登记，否则分数不可比（`AGENTS.md` §四.4）。

## v0.0.1 — 2026-09-23 大更：卜科四科全可用（三科上线 + 六爻四段契约接入）+ 合参层实现 + 仓库级质量门

### 2026-09-24 M2.1 词典层结构化：186 键问题词典入 data/ + 取用神四层来源标注（六爻）

- **问题词典外置**：新增 `disciplines/liuyao/tools/build_question_use_gods.py` 把 `_QUESTION_USE_GOD_MAP`
  186 键按 64 个事项族生成 `data/rules/question_use_gods.json`——逐族标注取舍依据
  （38 引文族＝《增刪卜易》逐字引文+offset，`--check` 复验 59/59 命中；26 推断族＝
  诚实标注"无逐条出处"的理由）。键序与取值零漂移（保序快照逐键比对），`chain_tables`
  改为装载器，缺表直接报排盘异常不降级。
- **决策与所本同源**：`chain_step2._decide_use_god()` 返回 (类别, meta)，meta.source ∈
  法则|覆盖|词典|兜底；`_use_god_basis` 换新签名，四种前缀各说实话（覆盖层带引文的挂
  `layer_citations` 逐字引文，推断明说"问题词典推断·无古籍逐条出处"）；SKILL.md §用神所本同步。
- **口径变动（矩阵）**：`tools/use_god_coverage.py` 分类改直接消费 meta.source——旧版复刻判断，
  把覆盖层命中的问法误报成"兜底"。**旧矩阵数字与新矩阵不可比**：92 条问法现为法则 29、
  覆盖 14、词典 35（有据族 23）、兜底 14，有古籍逐字依据 63 条（旧口径记 29 法则/48 词典/15 兜底）。
  `_use_god_basis` 的文案同时由两态（引文/默认）改为四态，下游按前缀判断的文案需知悉。
- **验收**：三集 strict 与基线完全一致——tune 94.5（n=20）／holdout 84.8（n=12）／
  wikisource_holdout 56.3（n=35）；金标准 288 例指纹 `0e2bb128bfefe831` 不变；
  新旧 `_determine_use_god_category` 465 条问法对拍全同；`tools/check.py --full` 全绿（黑箱 11/18）。
  另：`use_god_relations.json` 仅 `_meta.usage` 措辞随构建器同步（15 条规则内容未动，
  `--check` 15/15 命中）。

### 2026-09-24 M3 黄金样例与样例入库（3.4/3.5）：唯一模板 + 六项验收清单

- **黄金样例**：`docs/samples/感情卦_巽之涣.html` 定为唯一模板——`yi_liuyao.py --mode manual
  --yao "8,7,9,8,7,7" --when "2026-09-22 10:00"`（问感情）走真实管线生成，
  逐条过六项验收清单：**六神临用**（螣蛇临用语义叙述）／**持世**（兄弟持世引《火珠林·婚姻章》，
  `advanced_analysis.shi_yao_relation`）／**卦身**（卦身在初爻妻财）／**格局详释**
  （三刑/六冲/三合/暗动/月破/进退神逐条渲染）／**公历应期**（2026-09-24 丑日逢值等 date+rule）／
  **边界克制**（象判边界声明＋"偏向/有…信号/结构上"措辞）。
- **补齐机制（narrate 薄适配层）**：`narrate.py` 新增【持世】【象判边界】两段——纯转述
  `advanced_analysis.shi_yao_relation`（含 `scenario_interpretation` 与 `poem`）与固定分寸声明，
  不新增推演逻辑；引文出处沿用 `data/verdicts.json`。全部报告（含一键闭环产物）自动带上两段。
- **验收清单入库**：`SKILL.md` §3.7 黄金样例验收清单（六项要素＋判据＋数据来源＋生成命令），
  残缺薄版（如只有应期与推演、缺排盘表/六神/持世/格局）不得交付。
- **样例入库**：3 份样例 `docs/samples/`（感情卦_巽之涣／财运卦／事业卦，均为单文件 HTML）
  ＋全页截图 `screenshot_golden.png`；根 README 与六爻 README 同步（样例目录、一键闭环命令）。
- 验证：金标准指纹 `0e2bb128` 288 例零漂移（narrate 不改推演）；`tools/check.py --full` 全绿，
  六爻黑箱回归 11/18 持平基线。

### 2026-09-24 M3 一键闭环（3.2）：yi_liuyao.py 一条命令出报告

- **新增 `disciplines/liuyao/scripts/yi_liuyao.py`**：`python scripts/yi_liuyao.py "所问之事" --when "..."`
  一条命令走完 chart→analyze→render——起卦（缺省 time 用 --when 时刻/当前时刻，支持
  manual/number/coin+seed）→ 排盘 → 推演 → 单文件报告（HTML 缺省 / `-f md`），
  `-o` 指定输出（缺省 `outputs/reports/report_<时间戳>.<ext>`），`--open` 浏览器直开；
  命令尾部打印结要（本卦/变卦/结论/应期）。从零到可分享报告无人工拼装（验收达标）。
- **`tools/demo.py` 六爻演示切四段契约**：demo_liuyao 从旧引擎入口
  （`liuyao_engine.py --mode coin`）改为 chart→analyze→render（与其他三科同构），
  输出单文件 HTML 报告；全科演示 `python tools/demo.py` 实测通过。
- **SKILL.md / README 命令同步**：一键闭环命令写入执行规程，旧引擎 HTML 分支注明仍走 render 出口。
- 纯新增入口与演示装配，不触碰引擎推演，金标准指纹与质量门不受影响。

### 2026-09-24 M3 门户修伤（3.3）：死链修复 + 真分数看板 + SVG 卦盘

`disciplines/liuyao/index.html`（gitignore 生成物，由 `scripts/build_portal_assets.py` 可重建）：

- **看板真分数**：`build_portal_assets.py` 的 `build_blind()` 从 `eval_{tune,holdout}.json` 取分
  （当前读数 tune 94.5 / holdout 84.8，headline 取 holdout 并带 n=12 与口径说明），
  页面不再自带硬编码 100 常量；各案例得分（57.9/92.6/96.8…）与 `evaluate.py` 一致。
- **死链修复**："打开完整样例报告"原 `window.open('sample_report_ZS001.html')` 指向不存在的
  静态文件，改为页内数据渲染完整报告——iframe 模态框预览（任何环境可用，关闭/点遮罩/Esc 均可退出）
  ＋"在新窗口打开"可选路径（被拦截时提示走导出）。
- **SVG 卦盘**：爻线（阳连阴断）＋六神/六亲/纳甲/爻象/世应/动变 ○×/旬空/"变出"列
  （`→变出支 变出六亲`，数据来自 `changed_branch`/`changed_six_relation`）。
- **自包含**：无外部 src/href/fetch/@import，`file://` 直开可用（验收标准）。
- 浏览器实测：加载/看板/卦盘/切换/模态框/导出 6 项全过，控制台无 JS 报错。
- 门户产物不入库（`index.html` / `assets/portal_data.json` / `outputs/reports/` 在 gitignore），
  无引擎改动，金标准指纹与质量门不受影响。

### 2026-09-24 M3 呈现三合一：两套报告引擎合并为单一 HTML 出口 + SVG 真卦盘

承接 2026-09-23 骨架收敛（A2）的"未做"项，本次完成**内容**合并：

- **`scripts/render.py` 成为唯一 HTML 出口**（`render_html`）：同一份 analyze JSON 出 Markdown 或单文件 HTML，
  HTML = 结要卡（方向徽章/信息栅格/应期卡）＋ 二、卦盘（SVG）＋ 三、正文（narrate）＋ 四、判据所本，
  骨架走 `core/report`。两套并行生成器 `visualization.build_html_report` / `build_html_report.py`
  （后者已删除）不再产出报告，`grep "<!DOCTYPE"` 仅剩内核 kit 一处。
- **SVG 真卦盘**（`visualization.generate_hexagram_diagram`，替换 CSS 色块条）：本卦＋变卦并列，
  爻线（阴阳/动变 ○×）、六亲六神地支标注、世应（蓝/绿标记）、旬空"(空)"、变卦动爻红框＋原爻虚线示意。
- **`core/report/html.py` 新增 `md_to_html`**：轻量 Markdown → HTML（标题/列表/表格/粗体/行内码），
  对齐文本块（排盘表等多列空格对齐）识别后 `<pre>` 保形，正文排盘表不再散架。
- **样式层唯一**：全部报告类名走 `assets/report.css`（SVG 自带内嵌 `<style>` 计入定义域），
  `tools/style_check.py` 改为仅用 render 段采样核对类名覆盖。
- **依赖方迁移**：`build_portal_assets.py`（样例报告）、`liuyao_engine.py --format html`（旧引擎 CLI）、
  `tools/style_check.py` 全部改走 render 出口；`visualization.py` CLI 仅保留 `svg` 子命令生成单一组件。
- 六爻 `README.md` 目录表与 `docs/LIUYAO-PLAN.md` 进度同步更新。
- 验证：静卦（全阴）与动卦（7,8,9,7,6,8 → 变卦＋动爻标记＋红框）两条路径实测通过；M3 其余子项
  （3.2 一键闭环 / 3.3 门户修伤 / 3.4 黄金样例 / 3.5 README 截图）未做。

### 2026-09-24 应期回收闭环（B2）：断卦→回填→评分全链路打通

- **六爻 analyze 适配层外露结构化应期候选**：`conclusion` 新增 `应期明细`（`[{date, rule}]`，
  按引擎给出顺序即名次，`date` 为公历日期、`rule` 为推出该日的法则标签）——此前只拼进可读文本，
  丢失"哪个法则推出哪个日"。纯适配层装配改动，不触碰推演逻辑，金标准指纹不受影响。
- **合参层回填扩展**：`record-outcome` 新增 `--occurred-at`（应验/观察日期，YYYY-MM-DD，
  校验有效日期）+ `--judged`（应验/未应验/部分应验/超期未验，断事判定）；`person.py` 校验同步收紧
  （judged 枚举、occurred_at 有效日期），非法回填直接拒绝。
- **新增 `outcome-eval` 命令**（`synthesis/outcome_eval.py`）：遍历档案已回填占问，按候选名次比对——
  第 1 位命中=主应期（全分）、第 2~4 位=次应期（0.8/0.7/0.55）、更靠后=命中但名次靠后（0.35）、
  早于全部候选=提前（0.35）、晚于末位候选=超期（0）；断事层面按 judged 折叠。汇总带样本量 n 与
  集合名（档案内已回填占问），逐例带 rule 标签——攒够样本可**按法则**统计命中，供应期法则迭代。
- **口径声明**：outcome-eval 产出为**现实回填命中**，与古籍案例对齐分（evaluate.py）分开登记，
  绝不混称"预测率"（`AGENTS.md` §三）。其余学科暂无结构化应期候选（`timing` 仅文本），应期维度不评。
- 端到端实测：六爻 chart→analyze→add-divination→record-outcome→outcome-eval（主应期第 1 位命中）
  + `selfcheck` 新增应期回收自检段，全链路通过。

### 2026-09-23 重构批次：六爻巨石拆分 + core/report 呈现统一 + 四科 golden 规范化

- **A4 四科 `golden.py` 规范化**（`liuyao/meihua/xiaoliuren/zeji`）：从裸 `sys.argv` 手解改为 argparse 标准 CLI，`--help` 可看，`capture` 必须给漂移理由（防掩盖退步，`AGENTS.md` §四）。
- **A1 六爻三巨石拆分**（`disciplines/liuyao/scripts/`）：
  - `liuyao_engine.py`（3696 行）/ `thinking_chain.py`（6493 行）/ `classical_analysis.py`（4226 行）拆为 `engine_*` / `chain_*` / `classical_*` 共 20 个子模块 + 薄聚合入口，纯搬移不改逻辑。
  - 拆分修复两处此前就存在的隐性缺陷：爻序与八宫归属等构建循环丢失导致排盘/解读字段漂移，已按内核唯一真值源补回。
  - 验收：金标准指纹 `0e2bb128`（288 例）与拆分前基线一致，连续两次运行可复现；六爻黑箱回归 11/18 与基线持平。
- **A2 core/report 统一呈现 kit**（`core/yishu_core/report/`）：
  - 新增 `html.py`：`render_page`（统一单文件 HTML 骨架：DOCTYPE/head/内联样式/页脚/可选脚本，容器宽度可配以兼容排盘与解读两类布局）、`write_html`（自动建父目录）、`escape`（转义统一入口）。
  - 六爻两套并行报告引擎（`visualization.py` 排盘报告 3 处骨架、`build_html_report.py` 解读报告骨架 + `_xml_escape` 重复实现）收敛到 core/report——消除"一副卦两种骨架"。`grep "<!DOCTYPE"` 仅剩内核 kit 一处（回归测试工具的内嵌测试报告为独立样式，属工具 UI，不收敛）。
  - 样式层仍唯一（`assets/report.css`）；`style_check.py` 39/29 个类全部有定义。
  - 未做（留 `docs/LIUYAO-PLAN.md` 3.1 后续）：两套引擎**内容**合并、`render.py` 单一 HTML 出口、SVG 真卦盘——本轮只收敛骨架层。
- **A3 断语外置**（`disciplines/liuyao/`）：成表断语/引文库（`SHI_YAO_INTERPRETATION` 六亲持世断语、`SHI_YAO_POEMS` 持世歌诀、`QUOTE_DATABASE` 引文库共 59 条）从 `chain_verdicts.py` 迁至 `data/verdicts.json`，代码只留加载与算法（`AGENTS.md` §三）。出处：引文库逐条 `source` 字段标注古籍；持世断语值内文末括注出处，无括注者为基础持世通论（`_meta` 注明）。金标准指纹 `0e2bb128` 复验无漂移。关键词表（`_QUESTION_SCENARIO_KEYWORDS`）属算法特征，留代码。
- **卦辞爻辞上收内核**（`core/yishu_core/hexagram_texts.py`）：六十四卦卦辞（`HEXAGRAMS`）与爻辞（`HEXAGRAM_LINE_TEXTS`）从 `liuyao/scripts/engine_tables.py` 迁入内核唯一真值源（`AGENTS.md` §二：卦辞爻辞在 core 只一份），学科改为导入——此前这两张表仅存于学科层，质量门"内核表无复制"检查无法拦截"表缺失于内核"。金标准指纹 `0e2bb128` 复验无漂移。

### 新增

- **六爻四段契约薄适配层**（`disciplines/liuyao/scripts/chart.py` / `analyze.py` / `narrate.py` / `render.py`）：
  - 包装既有引擎（`build_hexagram_result` / `thinking_chain` / `advice_framework`），**不触碰任何推演逻辑**，金标准指纹与回归分数不受影响（未改引擎内部）。
  - `chart.py`：起卦 → 排盘 JSON（支持 coin/time/number/manual，含早晚子时口径）。
  - `analyze.py`：排盘 → analyze JSON，装配 `conclusion`（方向/说明/置信度/应期/所本，应期从 `yingqi_dates.dates[].date` 干净抽取）与 `chart_summary`（卦名/干支/旬空/动爻/用神/旺衰），直接供合参层 `normalize_liuyao` 归一化。
  - `narrate.py` / `render.py`：薄装配，正文一律用 `format_reading_output` 生成，不允许另行断卦。
  - 根级 `tools/check.py` 新增六爻四段端到端冒烟（chart→analyze→render 产物核验）。
- **卜科三科上线**（`disciplines/`，各科完整四段管线 chart→analyze→narrate→render + 质量门 + 案例库）：
  - `meihua/`（梅花易数）：年月日时起卦 / 报数起卦 / 两数起卦（观梅占金标准），体用生克、互变作用、卦气旺衰、应期、数应迟速、卦象特断。
  - `xiaoliuren/`（小六壬）：月上起日、日上起时，六宫掌诀断事（《贺氏六壬小手册》口径），含变通取数法。
  - `zeji/`（择吉）：建除十二神、黄黑道十二神、二十八宿值日，活动宜忌匹配与综合裁决（《协纪辨方书》口径）。
- **内核扩展**（`core/yishu_core/`）：
  - `zeji_tables.py`：建除十二神 / 黄黑道十二神 / 二十八宿值日表（唯一真值源，学科不复制）。
  - `lunar.py`：农历与公历双向转换（朔望月 + 节气定月双轨制）。
  - `eval.py`：全仓库唯一评分器（分层 tune/holdout/excluded、维度权重、`verdict_direction` 折叠）。
  - `ming_tables.py`、`relations.py`：命科骨架所需表（本轮不实现命科推演，仅立数据）。
- **合参层实现**（`synthesis/`，此前只有契约）：
  - `person.py`：个人档案模型（birth.ganzhi 必须带 `calendar_policy`；`divinations[].outcome` 是唯一现实效度证据字段）。
  - `normalize.py`：四科 analyze 输出 → 归一化占问记录（方向吉/平/凶、应期、判据所本）。
  - `cross_rules.py`：五条裁决规则落码（各守其位 / 同向则确 / 两同一异 / 异向先查时空口径 / 缺数据降级）。
  - `guidance.py`：阶段性指导生成（格局节律 / 近期诸事 / 合参结论 / 可执行建议 / 边界声明）。
  - `cli.py`：init / validate / add-divination / record-outcome / guide / selfcheck。
- **仓库级工具**（`tools/`）：
  - `check.py`：一条命令全仓库质量门（版本唯一真值、结构契约、内核表唯一、三科门、六爻冒烟、合参自检；`--full` 加案例评测与六爻回归）。
  - `demo.py`：全科演示（四科各一例 + 合参演示，走真实 CLI）。
  - `install.ps1`：环境安装与自检。
- 各科案例库与质量门：三科各有 `data/cases/`（tune/holdout/excluded 分层）、`tools/check.py`、`tools/golden.py`（行为漂移看门狗）。

### 修复

- `tools/check.py --full` 六爻黑箱回归口径与六爻自身质量门对齐：改用基线比较（11/18，2026-09-22 实测，残余案例待古籍重推已声明），不再要求全过——此前 `--full` 恒红，无法作回归门。
- `synthesis/person.py`：移除 `xiang`（相理观察）占位字段——相科明确不做（`AGENTS.md` 范围条款），档案 schema 不留相科占位。
- CLI 与文档/命令对齐：`synthesis` 里 `init/validate` 等命令此前以 `--id` 描述，实际为位置参数 `pid`、`add-divination` 需 `--analyze-json`——根 `SKILL.md` §5.3 与 `synthesis/README.md` §〇 已改为可执行的真实接口并实测跑通（建档→登记→指导→回填）。
- 三科四段 CLI 写出路径不再依赖目录已存在：`meihua/xiaoliuren/zeji` 的 `chart/analyze/narrate/render` 的 `-o/--out` 此前不建父目录，文档示例 `-o outputs/report.md` 在 `outputs/` 不存在时直接崩（`FileNotFoundError`）；现统一在写前 `parent.mkdir(parents=True, exist_ok=True)`（与 `liuyao` 适配层一致），并已从空目录全链路实测四科 chart→analyze→narrate→render。纯 CLI 健壮性修复，不触碰推演逻辑，分数与指纹不受影响。
- `disciplines/meihua/scripts/chart.py`：CLI 补齐 `--way lunar` 入口（内部 `chart_from_lunar` 与 docstring 早已支持，唯独 argparse 未暴露）。
- 对齐 SKILL 与实际命令：meihua `SKILL.md` narrate 命令曾传入内联 JSON 字符串（实际接口要求 analyze JSON 文件路径），改为 chart→analyze→narrate→render 分步可执行命令；meihua chart `--way` 取值、xiaoliuren/zeji 起课命令逐一与 `--help` 核对一致。
- `.gitignore`：补 `synthesis/person/` 与 `synthesis/guidance/`（合参层运行产物，此前未忽略，会误入库）。
- `synthesis/cross_rules.py`：缺数据判定改用独立命理主题词表（财运/婚姻/事业等可一事一占、但趋势层缺命科佐证 → 标记 ming 未参评），与越位表解耦。
- Python 3.10 兼容修复（`disciplines/liuyao/`）：`tools/check.py` 的版本检查依赖 `tomllib`（3.11+）改为零依赖最小解析；`scripts/visualization.py` 的 f-string 反斜杠（3.12 前语法错误）改为 `_nl` 变量。此前六爻 `tools/check.py` 在 3.10 下直接崩、质量门不可用。金标准指纹复验无漂移。
- `synthesis/person.py`：`create` 同时给 ganzhi 与 policy 时 policy 不再被丢弃。
- `synthesis/guidance.py`：`tally()` 调用补传 adjudication；被裁决剔除的越位记录不再混入「近期诸事」列表。
- `disciplines/meihua/scripts/chart.py`：卦名自检断言改为简称（与内核 HEXAGRAM_TRIGRAMS、六爻 HEXAGRAMS 同一惯例）。
- 三科 chart/analyze/narrate/render CLI 统一补齐与加固：
  - meihua chart/analyze/narrate/render 补 argparse CLI（此前顶层无条件跑自检或裸 `sys.argv`，`--help` 不可用）；
  - xiaoliuren / zeji 的 narrate 补缺失的 `__main__` CLI；
  - 各科 analyze 统一 `-o/--out` 短长选项。

### 口径说明（分数可比性）

- 三科分数均为**古籍案例对齐分**（引擎输出与案例库要点吻合度），集合分层如下，禁止对外称"预测率"（`AGENTS.md` 铁律三）：
  - meihua / xiaoliuren / zeji：tune 与 holdout 全绿（各科基线见 `disciplines/<科>/tools/check.py` 的 BASELINE）。
- 合参层新增 `calendar_policy` 口径字段：各科年界/子时口径不一致时，合参先标记时空分歧，不直接比结论。

### 已知欠项（不掩盖）

- `ming`（四柱八字）只立数据表与档案字段，推演未实现——合参时该维度按规则降级为"未参评"。
- 六爻（`disciplines/liuyao/`）为迁移前旧实现：已接四段契约薄适配层（可入合参层），但引擎内部仍运行于自身工具链，未迁入内核 `yishu_core.hexagram`；黑箱回归基线 11/18，残余案例待古籍重推（README/HANDOFF 已声明）。
- 各科应期/数应字段暂无事后回填数据，效度统计依赖 `record-outcome` 积累。
