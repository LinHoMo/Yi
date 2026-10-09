# 易（Yi）· 第三轮深潜：加法 / 减法 / 瘦身清单

> 日期：2026-10-01｜方法：全仓树 + `git ls-files`（342 个入库文件）+ AST 重复函数体检测 +
> 逐文件核对文档事实，共 8 项机械扫描；**本轮只探查，未改任何代码**。
> 口径：以 `AGENTS.md` 三条铁律 + §二内核唯一真值源 + §三断语外置 + §六产出同源为准。
> 关系：本轮**取代并吸收** `docs/PROJECT-REVIEW.md`（第一轮，12 项已全部 ✅）与
> `docs/DEEP-REVIEW.md`（第二轮）——那两份的结论已落地或转入本文件的 §二/§三。
> 分数一律为**古籍案例对齐分**，非现实命中率（`AGENTS.md` §一.3）。

> ### ⚠️ 执行状态（2026-10-01f 补，落库时写）
> 本文件是**第三轮"只探查、未改代码"的清单**。阶段4（`2026-10-01e/f`，提交 `d34c269`）
> 把 §五 的五轮顺序合并成了一轮做掉，因此：
> - **§四 第 6 项（S-D11 断语外置启发式补假阴性）已解决**——不是"补假阴性"，
>   而是**整类判据换代**：`tools/verdict_audit.py --strict` 跑真实报告反查未外置句，
>   接入根门 [1c]（详见 `docs/HANDOFF.md` §八 与 CHANGELOG 2026-10-01e/f）。
> - **§五 的五轮顺序作废**，别再按"第 1 轮零风险先做"往外派下一棒；
>   直接看 `docs/HANDOFF.md` §八 的行动清单（A–F，每项带完成标准与验收命令）。
> - §四 其余未决项 2026-10-01f 复核（实跑 grep）：`tools/eval.py` 未挂门（→ 已补为
>   HANDOFF §八.F）；`.gitignore` 仍 `!docs/samples/**` 通配白名单（未收窄，未定）；
>   三科 `case_runner` 仍分科存在未合并（S-D3，未做）；`build_web.py` 已挂 check
>   （站点构建）。
> - §六「健康面」仍然有效：**不要**在下一棒顺手去改那几条"确实合规"的项。

**一句话结论**：代码逻辑本身已经干净（根门全绿、依赖单向、无跨科 import、无硬编码路径）。
剩下的负担全在**代码之外**：① 铁律三（口径诚实）在文档层没有门，被推翻的 100% 还挂在门面上；
② 项目最核心的资产「机械门」**从未在 CI 里跑过**；③ 文档与注释里堆着已消费的过程叙事，
且同一句口径被抄了 10+ 遍——正是 §「只引用不复制」自己没被应用。

---

## 一、体量与覆盖实测（本轮基线）

| 项 | 实测 | 说明 |
|---|---|---|
| 入库文件 | 342 | 工作区另外 479 个未入库文件（`*.pyc` 253、`site/` 镜像 142、`.preview/`+`.workbuddy/` 9），均已 gitignore；工作区合计 34.5 MB |
| Python 总量 | 48,430 行 / 185 个文件（不含 `site/` 镜像） | 学科层 37,152 行；六爻一科 26,734 行 = **55%** |
| 注释 + docstring 占比 | **18.6%**（`core/` 24.7%、`tools/` 17.7%、`web/` 28.4%） | 其中相当比例是历史叙事而非行为约束 |
| 入库 Markdown | 70 份 / 18,532 行 | `case_library` 4419 + `CHANGELOG` 1579 + 六爻 `CHANGELOG` 561 + 其余 ~12,000 |
| CI 是否跑质量门 | **否** | `.github/` 内 `grep check.py` 零命中；`pages.yml:57` 只跑了同源验收（11 道门里的 [7b] 一步 + 站点自检），且要 `paths` 命中才触发 |
| `narrate` 段有文案哈希的科 | **1/8**（六爻；`lingqi` 5 处见 narrate 但非哈希） | 其余 6 科 `golden.py` 只 2 处提及（仅调用，不校验文案） |
| `references/` 目录齐全的科 | **5/8** | `CONTRACT.md` §四.1 要求必备；缺 `ziwei` / `liuren` / `lingqi` |
| 跨文件重复函数体 | **12 组** | 最重的是梅花/小六壬/择吉三科 `dev_tools` 与 `case_runner` 逐字同构 |
| `.py` 内非注释中文长字面量（≥8 汉字） | **1,734 处 / 138 个文件** | 断语外置门只认 `{"condition": "中文…"}` 一种形态，这一大类整体**无门**（详见 S-D9） |

---

## 二、减法清单

### S-A · 口径诚实（铁律三直接违规面，两轮审查都没查这一层）★先修

| # | 位置 | 现状 | 动作 |
|---|---|---|---|
| S-A1 | `README.md:157-167` | 人类第一入口的「现在的真实水平」表，列名写着**古籍对齐分**，却填着已被 2026-09-30 审计推翻的 **100%**（梅花 10+8 / 小六壬 15 / 择吉 5+5）；同表六爻 tune 93.9、holdout 87.5 是 30r 前的旧口径（现行 95.0 / 89.7，`HANDOFF.md:36`），wikisource 57.3 现为 57.1（`CHANGELOG.md:369`） | **删表**，只留一句「读数见 `docs/HANDOFF.md`」；或按 HANDOFF 整表重写 |
| S-A2 | `disciplines/README.md:11,13,15` | 仍写「meihua / zeji tune·holdout 均 100%」（两科 `docs/EVAL-AUDIT.md` 已订正为"规则自洽回归数"）；同表只有 6 科，缺 liuren/lingqi；:15 写「当前范围（六科）」 | 删分数列，补两科 |
| S-A3 | `disciplines/{meihua,xiaoliuren,zeji}/README.md:19-25` | 三张分数表仍是 100%，与各自 `docs/EVAL-AUDIT.md` 的订正结论并存 | 删表改链接 |
| S-A4 | `README.md:19,86,157` / `llms.txt:3` / `ARCHITECTURE.md:18,117` / `AI-SOP.md:219` | 「六科 / 八科 / 五科」三种说法并存；`AGENTS.md` 说八科、`request.DISCIPLINES` 是八科、通道 A 实际只挂 6 科（liuren/lingqi 仅本地，只有 `PROMPTS.md:34-35` 写了） | 建**唯一能力矩阵**（科 × 本地 CLI / 通道A / 通道B / MCP / 评测集），其余文档一律引用 |

> **治本规则**：仓库内任何**分数**只允许写在 1 处（各科 `docs/EVAL-AUDIT.md` 或
> `evaluate.py` 的 `[口径披露]` 输出），任何**清单/口径**只允许写在 1 处（`AGENTS.md`）。
> 其余文档只写指针。不立这条，下一轮还会漂。

### S-B · 过期 / 已消费的过程文档（约 2,500 行）

| # | 文件 | 行数 | 判据 |
|---|---|---|---|
| ~~S-B1~~ | ~~`docs/DEEP-OPTIMIZE-PLAN.md`~~ | ~~1,370~~ | **已删除（2026-10-01j）**：文件头自承"不再作为执行依据"，且 6 处引用已删的 `disciplines/base/` |
| ~~S-B2~~ | ~~`docs/PROJECT-REVIEW.md`~~ | ~~182~~ | **已删除（2026-10-01b）**：12 项全部修完，只剩历史 |
| ~~S-B3~~ | ~~`docs/DEEP-REVIEW.md`~~ | ~~155~~ | **已删除（2026-10-01b）**：第二轮清单，本轮即它的续做 |
| S-B4 | `docs/compose/spec/` 6 份 | 525 | 全部 `status: delivered`，含 2026-09-26 的旧指纹 `a1a7d34c3532f2f2` 与旧分 `93.7 < 基线 94.2` |
| S-B5 | `disciplines/liuyao/docs/compose/spec/classical-holdout-benchmark.md` | 119 | 同类 |
| ~~S-B6~~ | `docs/MIGRATION.md` | 166 | v0→v1 迁移已完成；`:148` ~~教"继承 `base/cli.py` 的 `DisciplineCLI`"~~ **已修正为"参考 meihua/scripts/chart.py 范式"（2026-10-01j）** |

→ 合并为一份《决策与教训归档》（只留"什么被否证了、为什么"，不过程叙事），或直接删（git 里有完整历史）。
**判据来自 `AGENTS.md` §三本身**：产物/过程叙事不入库。

### S-C · 事实漂移的现行文档（必须改，不是删）

| # | 位置 | 漂移 |
|---|---|---|
| S-C1 | `README.md:86` | 目录树仍列 `disciplines/base/` 为现存共享层（已删） |
| S-C2 | `docs/ARCHITECTURE.md` | 整份停在"巨石拆分"时代：`liuyao/scripts/` 条目名是 `chain_*` / `human_narrative`（早已合并为 28 个模块）、写 `liuyao/tools/`（实际 `dev_tools/`）、`:241` 指纹 `5c6e77ee253b0ddd`（现行 `46fd569fbe945814`）、完全不含 liuren/lingqi/zeji 之外两科 |
| S-C3 | `docs/CONTRACT.md:3` | 开头仍写"当前范围仅 `ming`；`liuyao` 为迁移前旧实现" |
| S-C4 | `docs/HANDOFF.md:354-369` §五之一 | "当前状态（2026-09-29c 重构后）"整节过期：写"五分科"、列旧 scripts 数 |
| S-C5 | `docs/HANDOFF.md:16` | "六科均经各学科 `dev_tools/check.py` 全绿"——实际根门只跑 2 科（见 A-4） |

### S-D · 重复实现与重复入口（AST 实测 12 组跨文件同体函数）

| # | 项 | 证据 | 动作 |
|---|---|---|---|
| S-D1 | 三科 `dev_tools/check.py` 的 `measure`/`eval_metrics`/`gate` | meihua / xiaoliuren / zeji 逐字相同（494 行三份） | 上收内核；`CONTRACT.md` §四.6 本就要求"复用 `yishu_core.eval`，禁止另写一套" |
| S-D2 | 三科 `dev_tools/golden.py::main` | 逐字相同（131 行 × 3） | 同上 |
| S-D3 | 三科 `scripts/case_runner.py` | `load_cases`/`load_meta`/`run_cases`/`main` 逐字相同（370 行三份） | 同上（第二轮 B2 判"需评估"，本轮给出更硬的依据：CONTRACT 已明文禁止） |
| S-D4 | 六爻内部同体异名副本 | `classical_enhancements.is_ba_zu_he/_chong` ↔ `narrative_utils._is_he/_is_chong` 四份同体 | 合一（§二"改名副本"纪律在**代码层**同样适用） |
| S-D5 | 六爻门面/再导出链 | `liuyao_step1.py`（243 行 / 1 个 def）、`liuyao_analyze.py`（87 行 / 0 个 def）、`classical_analysis.py`（275 行 / 2 个 def）——三个模块只做转发 | 合并或降为一行 re-export |
| S-D6 | ~~5 份 `scripts/mcp_server.py`~~ | **已作废**：用户 2026-10-01 决策"不使用 MCP"，5 份 `mcp_server.py` + `tools/mcp_router.py` + `mcp-server/` 整体删除 | 无（不再是"统一"的问题） |
| S-D7 | 六爻本地门户 | `build_portal_assets.py`（201 行）+ `index.html`/`assets/portal_data.json` + `docs/samples/screenshot_golden.png` + `disciplines/liuyao/README.md:25,66` + `dev_tools/check.py:138-150` 的版本门 | **半已修**：②号问题（新克隆必 `FileNotFoundError`）已修——产物缺失时明确跳过并打印 `·` 注记，不再判红（见 §七 1-8）。①号"是否删门户"仍待用户拍板 |
| S-D8 | 结果回收四套并存 | `event_logger.py`（618 行，写 gitignored `logs/`）、`dev_tools/outcome.py`、`data/feedback/`、`synthesis/outcome_eval.py` | 抽一条唯一链路 |
| S-D9 | `check_verdict_literals`（`tools/check.py:185-187`） | 弱启发式：只认 `"condition"/"meaning"/"advice"` 等键，plain `str→str` 的真断语一条报不出；而 `tools/check.py:133` **自己已经写明**"主判据是 `verdict_audit.py --strict`（[1c] 门），本函数（[1b]）是辅助"。同一件事挂着两道门，其中一道已知失明 | 降为提示或删。**"已确定失明的门"继续占着"全绿"的位置，是首轮 P0 的同类风险** |
| S-D10 | 书源双份 | `data/sources/bushi_zhengzong.wikitext.txt` 与 `bushi_卜筮正宗_河潞武子龄校本_.wikitext.txt` **sha256 完全相同**（`47A8C226…`）；`archive/sources/meihua_梅花易數*`（4 份 128 KB）与 `data/sources/mei-hua-yi-shu.wikitext.txt` 同书两处 | 书源也守"唯一真值源"：一处存副本，一处只留 `provenance.json` |
| S-D11 | 断语门盲区的规模（本轮新测） | 门只认一种形态，因此**形态之外全放行**：实测 `.py` 内非注释中文长字面量 **1,734 处 / 138 文件**，且大头不是测试夹具——`core/yishu_core/hexagram_texts.py` **263 处（64 卦卦辞直接写成 Python 字面量表**，§二 认它为内核表、§三 却要求"卦辞进 `data/*.json`"，两条自相矛盾）；`liuyao/scripts/liuyao_step4.py` 94 处（`"静卦无动爻，以用神旺衰论吉凶"` 一类叙述句）；`ming/scripts/pattern.py` 29 处（`"忌神犯格且无救应（《子平真诠》）"` 一类带出处断语） | 三选一，**必须显式定一次**：① 把 `HEXAGRAMS` 移到 `core/yishu_core/data/*.json`（§三 原意）；② 在 §二 明确豁免"内核独立表可以是 .py 字面量"，并把 step4/pattern 的叙述句外置；③ 维持现状但在 §三 写明该类不在门范围内。**当前这种"门看不见、文档也没说清"的状态最贵** |

### S-E · 注释与文档瘦身（不删信息，只搬到对的地方）

- 量化：48,430 行 `.py` 里注释+docstring 占 18.6%；其中**历史叙事型**（讲"上一版怎样、
  某次重构之后怎样、为什么当初这么定"）对读者没有约束作用。典型四处：
  `disciplines/liuyao/scripts/visualization.py` 头 6 行讲 M3.1 之后的收敛；
  `trigram_symbolism.py` 头 15 行 +「下面三张表原先内嵌在本文件共约 230 行…已整体外提」；
  `build_portal_assets.py` 头 10 行讲"上一版把 v8 的 100.0 硬编在脚本里"；
  `core/yishu_core/report/request.py` 头 30 行讲"为什么放在内核里"。
- 规则建议：**模块 docstring ≤ 10 行**，只回答"是什么 + 调用约束 + 边界"；历史与教训压成
  一句话 + `docs/CHANGELOG.md` 指针；函数 docstring 只写参数/返回/异常。
  按此规则过一遍六爻主模块，估减 800–1,200 行注释。
- 文档侧重复：`铁律` 出现 **111 次**、「只引用不复制 / 唯一真值源 / 不互为副本」**48 次**、
  徽记 `✅⚠️🔶❌⛔` **120 个**，同一段"分数是对齐分不是命中率"在 10+ 份文件各写一遍。
  → 铁律与口径**只在 `AGENTS.md` 写一次全文**，其余写 `见 AGENTS.md §一.3` 一行。

---

## 三、加法清单

### A 档 · 让机械门真的存在（最高杠杆，成本最低）★

| # | 补什么 | 现状为什么不算数 | 成本 |
|---|---|---|---|
| **A-1** | **新增 `.github/workflows/ci.yml`：push / PR 跑 `python tools/check.py --full`** | `.github/` 内 `grep check.py` **零命中**：`report.yml` 不跑任何门，`pages.yml:57` 只跑了同源验收一步（还要 `paths` 命中才触发）。整个项目的可信度建立在"机械门"上，而门**只在人手动跑时才存在**；本轮我自己跑 `tools/check.py` 才拿到全绿 | ~30 行 YAML |
| **A-2** | **`narrate` 段文案哈希进 8 科 golden** | 实测只有六爻记了（`liuyao/dev_tools/golden.py` 7 处 narrate），其余 6 科改一个中文标点都不会红 → 铁律一「LLM 不得自行推断象数结论」在 6 科无机械验收 | 每科 ~5 行 |
| **A-3** | **报告忠实度审计扩到 8 科** | `tools/report_faithfulness.py:31` 硬编码 `LIUYAO_SCRIPTS`，且只跑 `--demo` | 中 |
| **A-4** | **根门覆盖 8 科** | `tools/check.py:47 SMOKE_DISCIPLINES = ("ming","ziwei")`——其余 6 科自己的 `dev_tools/check.py`（**各科 tune/holdout 基线就在里面**）不在根门内；`HANDOFF.md:16` 却宣称"六科均经各学科 `dev_tools/check.py` 全绿" | 1 行 |
| **A-5** | **口径措辞门（把铁律三做成可执行的门）** | 现在"不得出现预测准确率/命中率"只靠人自律，所以才会出现 S-A1~S-A3 | 扫报告正文 + `data/*.json` 断语：`准确率/命中率/必然/注定/绝无可能` 命中即失败；出现百分比必须同行带集合名 + n。**实现注意**：规格类文档（本清单、`AGENTS.md`）必然要引用禁用词本身——门只扫**产出物**，或对显式引用块开白名单，否则第一步就自伤 |
| **A-6** | **书源回指门**（第二轮 D5，仍未做） | `data/verdicts.json` 的「所本」字符串目前无人校验 | `所本` 必须在 `references/` 或 `data/sources/` 至少命中一处 |
| **A-7** | **补 `references/` 三科**（第二轮 D1，仍未做） | `CONTRACT.md` §四.1 要求必备，实缺 `ziwei`/`liuren`/`lingqi` | 各补一份最小 `api_spec.md`，或把契约改成"五科以上必需 + 登记制"（**二选一，别放着**） |

### B 档 · 把"立身之本"接到用户面前

| # | 补什么 | 现状 |
|---|---|---|
| **B-1** | **合参进交付通道** | `synthesis/README.md:3` 自称"易的立身之本…这层不做，易就只是一个路由"，但：`cli/main.py` 没有 synthesis 命令、`tools/report.py` 不支持、web 与 CI 都不覆盖（`build_web.py:42` 只镜像了源码）。现在要一份合参报告只能人肉 `cd synthesis && python cli.py`。建议给 `request` 加一条多科→合参的请求类型，让通道 A/B 都能出合参报告 |
| **B-2** | **结果回收归一，并接到报告尾部** | 四套并存（S-D8）且都不在出报告链路上。在"无法评估现实命中率"（铁律三）的前提下，回填积累是唯一能提升实际有用性的路径——应当像出报告一样有一键入口 |

### C 档 · 把文档里的数字与清单变成"生成的产物"（治本）

| # | 补什么 | 现在为什么漂 |
|---|---|---|
| **C-1** | `tools/status.py`：从 `request.DISCIPLINES` + 各科 golden / evaluate 现状**生成**"科 × 能力/通道/分数"表，README 只贴生成结果 | README / llms.txt / SKILL / AI-SOP / ARCHITECTURE / disciplines-README / PROMPTS 各抄一份，必然漂 |
| **C-2** | 能力矩阵单一处（含"通道 A 挂 6 科、liuren/lingqi 仅本地 CLI+MCP"） | 只有 `PROMPTS.md:34-35` 写了这个事实，README 没写 → 读者以为八科都能走网页 |

---

## 四、第二轮遗留未决（本轮复核后的状态）

| 项 | 第二轮结论 | 本轮实测 |
|---|---|---|
| 同源验收扩负例 | 待做 | ✅ 已做（`verify_web_parity.py:53 NEG_CASES`） |
| `tools/eval.py` 挂门还是删 | 待你定 | ⏸ 仍未挂（`tools/check.py` 无引用）——建议挂 `--full` 快照 |
| `tools/eval_audit_recheck.py` / `doc_html.py` / `demo.py` / `fetch_source.py` | 保留 + 文件头加"手工运行、不在质量门" | ⏸ 未加 |
| `.gitignore` 白名单收窄到显式文件名 | 待做 | ⏸ 仍是 `!docs/samples/**` 通配 |
| `build_*.py` 挂进 check 重建提示 | 待做 | ⏸ 未挂 |
| 断语外置启发式补假阴性 | 待做 | ⏸ 未改；本轮升级了结论：不是"补假阴性"，而是这一整类（1,734 处）**根本不在门的形态范围内**，见 S-D9 + S-D11 |
| 三科 `case_runner` 合并 | "需评估，单开一轮" | → 本轮升为 **S-D3 建议执行**（CONTRACT §四.6 已明文禁止另写评分逻辑） |

---

## 五、执行顺序建议

| 轮次 | 内容 | 风险 |
|---|---|---|
| **第 1 轮（立刻做，全是零风险）** | S-A1~S-A4（口径纠错）+ S-C1~S-C5（事实漂移）+ **A-1（CI 跑门）** + S-D11 的"三选一"**先**定下 | 零（不动引擎、不动数据） |
| **第 2 轮** | A-4 / A-2 / A-5（门扩覆盖 + 两个新门）+ S-D9（撤掉已失明的旧门） | 低 |
| **第 3 轮** | S-B1~S-B6（清 2,500 行过程文档）+ S-E 注释瘦身 + C-1/C-2 | 零（文档） |
| **第 4 轮（动代码，需零指纹漂移验收）** | S-D1~S-D3（上收三科同构实现）、S-D4/S-D5/S-D6、S-D7（删门户）、S-D8（回收归一）、`meihua/scripts/analyze.py:341` 的 tone 表外置 | 中：一律走 `refactor_guard` + 各科 `golden.py` |
| **第 5 轮** | A-3 / A-6 / A-7 / B-1 / B-2 | 中 |

> 每轮结束跑 `python tools/check.py --full`（第 1 轮做完 A-1 后，这一步会由 CI 自动兜住）。

## 六、健康面（勿过度反应）

以下经本轮核查**确实合规**，不要在下一轮里"顺手改"：

- 根门全绿（本轮实跑）；依赖方向单向；8 科零跨科 import；无硬编码绝对路径；无入库 `.pyc`；文件名无版本号；
- 内核表唯一真值源已经**收敛到位**：全作用域（含函数内 dict）与干支串两条盲区均已由
  `check.py` 补上，改名副本检测也在；本轮**未再发现任何内核表副本**；
- 生成物一律 gitignore，工作区无未跟踪垃圾；`.gitignore` 与 §三 已不冲突。
- **撤下一条上一版的乐观结论**：我先前按第二轮 §C 清单推断"断语基本已外置、残留多为测试夹具"，
  本轮用 AST 全量扫过后**不成立**——见 S-D11（1,734 处 / 138 文件）。上一轮的 C 清单是抽样，不是全量。

---

## 七、执行记录（边执行边记）

> 本节是**实际执行轴**，§五 那张表是开写时的设想（已被实跑推翻，见 7-9）。
> 规则：每条记「改了什么 / 为什么 / 怎么验收 / 实测结果」；没过验收的不算完成。
> 环境：Windows；解释器 `C:/Users/31103/.workbuddy/binaries/python/envs/default/Scripts/python.exe`；
> 慢门（>15s）自动转后台，日志落 `scratch/*.log`。

系名说明：下面 `1-x` 是 2026-10-01 这一轮（第三轮审查的落地轮）的条目，按实际动手顺序编号。

### 第 1 轮 · 2026-10-01（零风险面 + 一个 P0）

| # | 动作 | 为什么 | 验收命令 | 实测结果 |
|---|---|---|---|---|
| 1-1 | **MCP 全量移除** | 用户决策"不使用 MCP"；且实跑证明它已经是死入口：`tools/mcp_router.py` 的范围收缩后 `DISCIPLINES` 只剩 `ming`，而三科 `mcp_server.py` 仍在委派 `meihua`/`xiaoliuren`/`zeji` → 一敲就 `未知学科` | `git grep -i mcp`（活跃面）；`python tools/check.py` 与 `--full` | 删 7 文件 + `mcp-server/` 目录 + 1 份 772 行 MCP 接口文档；活跃面引用 **189 → 0**；双档 EXIT=0 |
| 1-2 | **新增 `.github/workflows/ci.yml`**（A-1） | 11 道门此前只在人手动敲命令时才存在（`.github/` 里 grep `check.py` 零命中） | pyyaml 解析 + 逐 job 打印结构 | 三份工作流全部解析通过；`push(main)`/PR/手动 → `python tools/check.py --full`；并在 `pyproject.toml` 补 `dev = ["pytest>=8"]` 作为版本约束**声明**（不改变"零第三方依赖"事实） |
| 1-3 | 三科 README 口径纠错（S-A2/S-A3） | 三张 100% 分数表既违铁律三、又与各科 `docs/EVAL-AUDIT.md` 自相矛盾 | 逐条比对案例集 JSON 实计数（`scratch/count_splits.py`） | 3 张表删除，改为"命中数/适用数 + n"；顺带纠正：zeji holdout **5→6**、zeji 指纹 15→**16 例**、meihua 指纹 18→**23 例**、三科 `tools/check.py` → **`dev_tools/check.py`**（学科下没有 `tools/`） |
| 1-4 | `disciplines/README.md` 范围与分数（S-A2） | 同上；且它当时写"当前范围（六科）" | — | 六科 → **八科**（补 liuren/lingqi 两行）；删除分数列，改指向各科 `EVAL-AUDIT.md` |
| 1-5 | `docs/CONTRACT.md:3`、`docs/HANDOFF.md` §一/§五之一（S-C3/S-C5） | 现行文档写着过期事实 | 八科门逐一实跑（见 1-9） | CONTRACT"当前范围仅 `ming`" → 八科并列；HANDOFF"六科均绿" → 八科实跑 + **显式标注根门盲区** |
| 1-6 | **P0 修复：核心常量进正则**（本轮最重要的发现） | 六爻案例评测已坏死，而根门全绿 | 见下"证据链" | 六爻门由红转绿，读数**回到文档原值** |
| 1-7 | **门在干净克隆上必红的两处**（新发现，见下） | 1-2 的 CI 会一上来就常红 | 干净克隆副本上复跑 | 两处都由"假红"变为"显式注记"，克隆上八科全绿 |
| 1-8 | **八科分科门挂进 CI**（A-4 落地） | 1-6 的门盲区正是被 CI 该盯的缝 | 干净克隆 + LF 化两份副本各跑一遍 | 两份副本：**根门 `--full` EXIT=0、八科门八绿** → 才有资格挂门 |
| 1-9 | 记录与登记 | 用户要求"边执行边记录" | 本文件 §七 + `docs/CHANGELOG.md` | 本节；CHANGELOG 新增 `2026-10-01g`（MCP）、`h`（正则回归 + 八科实跑）、`i`（克隆必红两处 + 挂门） |

**1-6 的证据链**（每一步都是实跑，不是推断）：

1. **症状**：`cd disciplines/liuyao && python dev_tools/check.py` → EXIT=1，[5] "tune 评测失败"；
   而同一时刻根门 `python tools/check.py --full` **EXIT=0**。
2. **复现**：`python scripts/evaluate.py --split tune` → 20 例里只有 1 例跑成，**19 例报错**
   "既无干支也无公历日期"；在一次 holdout 留痕里读到"时刻还原方式：error=19"。
3. **定位**（`scratch/probe_liuyao_case.py`）：`EARTHLY_BRANCHES` 是 **list**；
   `_DAY_RE.pattern` 打出来是 `([['甲', '乙', …]])日` —— 正则扫到 list repr 的**第一个** `]`
   就闭合了字符类，其后多出 `])` 两个必须逐字匹配的字符，**整条正则从此永不匹配**；
   `parse_ganzhi_hint("巳月戊戌日")` 返回 `(None, None)`。
4. **追责**：`git blame` → `244dd00`（2026-10-01c「真值源门升级」）：把 `DAY_CHARS` 由字面串
   换成了 `yishu_core.symbols.EARTHLY_BRANCHES`（list）。三处受害点都只"值换了类型"，
   行号、注释、调用方一字未改——**review 看不出来，也没有门盯它**。
5. **修**：进字符类前一律 `"".join(...)`（`case_runner.py` 2 处、`evaluate.py` 1 处），
   并在原处留一行注释说明为何必须 join。
6. **验收**：`FutureWarning: Possible nested set` 4 条 → **0**；
   `parse_ganzhi_hint("巳月戊戌日") → ("巳","戊戌")`；ZS001–ZS003 的 `resolve_case_time`
   由 `error` 变 `ganzhi_resolved`；六爻门转绿且读数回到 **tune 95.0 / holdout 89.7 /
   主应期 58.8、50.0 / wikisource 57.1(n=35) / direction 72.2(n=36)**，
   与 `HANDOFF.md` §一 逐项一致 → 证明是**恢复行为**而不是改行为；八科行为指纹零漂移。

**1-7 / 1-8 的证据链**（为什么必须先修门、再挂门）：

用 `git ls-files` 把**入库文件**复制成干净副本（`%TEMP%\yi_fresh`，无任何 gitignored 产物）
模拟新克隆，在其上跑门：

| 检查 | 干净克隆（CRLF） | 再统一成 LF | 结论 |
|---|---|---|---|
| 根门 `--full` | 先红 → 修后 **EXIT=0** | **EXIT=0** | 可挂 CI |
| liuyao 门 | 先是 **Traceback `FileNotFoundError: assets/portal_data.json`** → 修后绿 | 绿 | 可挂 CI |
| ziwei 门 | 先是 **`data/cases 目录缺失`** → 修后绿 | 绿 | 可挂 CI |
| 其余六科 | 绿 | 绿 | — |

两处红是**同一族**：门断言了 git 克隆不可能有的东西。

- liuyao：`assets/portal_data.json` 与 `index.html` 是本地构建产物（gitignore），
  新克隆里没有 → 改成"缺了就跳过并打印 `· 本地门户未构建 → 跳过该版本门`"。
- ziwei：门要求 `data/cases/` **目录存在**。但空目录 git 带不走，而 ziwei 恰恰**没有案例库**
  （该目录本机是个空目录、0 个入库文件）——"靠本机一个空目录过门"就是它此前全绿的全部原因。
  改成：有案例文件才谈分层，没有就打印 `· 尚无案例库（data/cases 下没有 *.json）`。
  > **由此新增一条待办（不是缺陷，是缺口）**：**ziwei 没有案例库**。其余七科
  > `data/cases/` 下都有入库的案例 JSON（ming 2 份、liuyao 7 份、其余各 1 份）。
  > 建库要选案例、核出处，属作者工作，本轮不擅自造数据。

挂门的前提是**基线**：两份克隆副本上八科门全绿之后，才把 `discipline-gates` 矩阵写进 `ci.yml`。

### 本轮对原清单的订正（写下来，免得下一轮再按旧结论走）

1. **S-D6 作废** —— 5 份 `mcp_server.py` 已整体删除（1-1），不再是"统一"问题。
2. **S-D7 折半** —— ②号"新克隆必崩"已修（1-7）；①号"门户是否删"仍待用户拍板。
3. **A-2 的判断是错的** —— 原写"六爻 `narrate_sha` 只有 1 科带、建议 promote 到内核"，
   实测**八科 golden 都已带 narrate 指纹**（1-8 的实跑里八科 [金标准指纹] 都在过）。
   这条从"加法"里划掉，别再动。
4. **A-4 的前提变了** —— 原写"把各科 check.py 挂进根门，约 1 行"。若照原样挂，根门
   **当场变红**（六爻评测当时已坏死）。正确顺序是：先修"分科门自己坏了没人知道"的问题
   （1-6），再在干净克隆上取基线（1-7/1-8），最后挂门。**已按正确顺序做完。**
5. **§五 的五轮顺序作废** —— 它按"零风险/低风险/动代码"分层，而实跑证明：**最贵的一步是
   让门真的可信**（1-6/1-8），不是清 2,500 行过程文档。本轮把顺序改成"先让门可信，
   再清理文档"。§二/§三 的具体条目仍然有效，只是不再按 §五 的轮次走。
6. **新增待办** —— ziwei 案例库（见 1-7 注），性质是内容缺口，不是代码缺陷。
