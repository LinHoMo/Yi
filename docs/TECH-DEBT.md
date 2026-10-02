# 技术债务登记（TECH-DEBT）

单一速查清单。**细节叙述见 `docs/HANDOFF.md` §四 与 `docs/CHANGELOG.md`**——本文件只做
**状态登记 + 提交锚点 + 阻塞说明 + 防新债纪律**，不重复叙述、不复制第二份真相。

- 报分口径铁律见 `AGENTS.md` 铁律三（对齐分≠命中率）。
- 债务没有消失只有转移：本文件同时记录**已清偿**与**待清偿**，避免历史在某次
  HANDOFF 重写时被静默抹掉。

---

## 一、已清偿（resolved）

| 债务 | 处理 | 锚点 |
|---|---|---|
| **N1 大六壬未落地（骨架）** | 四段契约 + core `liuren_tables` + 九宗门判据树（720 例全枚举守门）+ 金标准 + 两条出报告通道（缺参澄清门禁）；深化第一批：合池修正（书例自证）+ 课例评测（**2026-10-02p 扩容：4 → 43 例，机械一致率 33/43=76.7%；按引擎自标 `verified` 分桶：可验证桶 26/28=92.9%、异说桶 7/15**）；**深化第二批（2026-09-30j）**：课目识别首批八条（轩盖/斲轮/引从/亨通/三交/乱首/赎胥/冲破，kemu.json 诀表 58 条登记），八条在 720 例枚举全部有触发；铸印暂缓（诀文三传与链传中末对应存疑）；**第四批（2026-10-01r）**：九丑/天网/游子三条纯结构判据落地，判据数 31 → **34**；余 30 条仍为旺相/神煞/年命依赖，只登记诀文不写占位识别；另欠《毕法赋》判据/应期/涉害口径 | 2026-09-30h/i/j、2026-10-01r、2026-10-02p（见 CHANGELOG） |
| **命科调候用神缺失 + 案例评测空白** | `TIAO_HOU` 入内核（51/120 格原文提取、宁缺勿滥，引文留档 `tiaohou_quotes.json`）；`pattern/analyze/narrate` 透出调候；首批案例对齐评测 51 例（tune 30 / holdout 21，历法反查真实时刻，铁律三全遵守）；佐神分母口径修正见 CHANGELOG 2026-09-30g | 2026-09-30g（见 CHANGELOG） |
| **六爻缺失环节第一批**：三会局、独发独静、卦级反吟伏吟、本卦↔变卦双卦对比、三传克制、"真空/假空"标签 | 六项全部按古籍通则落地（三会±0.5 有界；独发独静/三传克制只标象不进主分；双卦对比 ±1.5；卦体合冲判定由卦名白名单改内核对应位纳支判——旧两表白名单互相矛盾，属通则修复）；内核增 `SAN_HUI_GROUPS`/`hexagram_branches`/`hexagram_he_chong_kind` 唯一真值源；独发独静域切出 `classical_enhancements_dufa.py`（2251→2184 行，看门狗线内）；金标准 `capture` 带理由，tune 93.9 / holdout 87.5 / 应期 58.8/50.0 / 黑箱 12/18 全部持平，refactor_guard 117 例零漂移 | 2026-09-30e（见 CHANGELOG 2026-09-30f） |
| **三科（梅花/小六壬/择吉）"tune/holdout 均 100%"读数误导**：expected 与引擎同源（自洽项权重梅花 70/100、小六壬与择吉 100/100）；梅花 holdout MH014–MH018 按本仓 `verdicts.json#multi_move_rules` 构造且与该表同提交 `010bcee` 引入（硬泄漏） | 逐例审计落三科 `docs/EVAL-AUDIT.md`；cases 逐例 `provenance` + `_meta._provenance`；三科 `evaluate.py` 报分自动 `[口径披露]`（n<20 不发百分比，改打逐维度命中数）；一键复核 `tools/eval_audit_recheck.py`；HANDOFF §一/§四、DEEP-DIVE-PLAN §三 读数同步订正 | 2026-09-30e（见 CHANGELOG） |
| **云端链路整体未入版本控制**（`.github/workflows/report.yml`、`tools/report.py`、`tools/ci_*.py`、`cli/main.py`、`disciplines/base/*.py`，以及六爻核心模块 `liuyao_step1-5`/`classical_enhancements`/`effects`/`chart_tables`/`liuyao_timing` 等、紫微斗数整科、`docs/ARCHITECTURE|MIGRATION`）——**推到 GitHub 也是空的**，云报告通道等于零功能 | 全部纳入索引并提交；同时清掉已合并的旧模块（`chain_*`/`classical_rules_*`/`human_narrative*`/`yingqi_windows` 等 25 个）与 `archive/` 冗余副本 | `b86e4b7`（2026-09-30d） |
| **"给链接即出报告"缺零凭证通道**：云端触发半场必须要 Token 或人工点链接 | 新增纯前端通道（Pyodide 在浏览器内跑同一份引擎）+ 深链协议 + Pages 工作流 + 站点自检 + 同源验收 | `b86e4b7`（同上，详见 CHANGELOG 2026-09-30d） |
| **请求→命令行参数映射双份**（本机执行器与浏览器执行器各写一份 → 必然"本地对的、网页端错"） | 上收内核 `core/yishu_core/report/request.py` 单一映射；`tools/report.py` 瘦身为纯执行器 | `b86e4b7`（同上） |
| 六爻起卦时刻**丢分钟**（`engine_chart` 硬编码 `HH:00`，报告内部自相矛盾） | 新增 `minute` 形参（缺省 0，不参与推演）并在 `chart.py` 透传 | `b86e4b7`（同上） |
| 梅花 `way=numbers` 直接 argparse 崩；小六壬同参数**静默忽略**按 datetime 出课；择吉日期不接受 `2026/09/30`；表外 `mode/way` 无校验 | 白名单校验 + 正确映射（梅花按"年数,月数,日数"）+ 日期归一化；表外取值明确报错 | `b86e4b7`（同上） |
| `/yi` 命令行里的 `key:value` **被静默丢弃**（旧正则要求键紧跟行首） | 重写 `parse_kv_text`，支持 `/yi k: v` 与一行多组 `k=v` | `b86e4b7`（同上） |
| `ci_request._from_workflow_inputs` 回落裸 `os.environ` → 字段名与 runner 环境变量同名时"表单没填却出盘" | 只认显式注入的 `INPUT_*` | `b86e4b7`（同上） |
| `/yi` 评论**不校验评论者权限** → 公开仓库任何人可消耗 Actions 分钟并让 bot 提交代码 | 限定 OWNER/MEMBER/COLLABORATOR（`YI_ALLOW_ASSOCIATIONS` 可放开） | `b86e4b7`（同上） |
| 报告取回 URL 带 run_id，网页 AI 拿不到（只能轮询 API，限流 60/h） | `reports/<科>/latest.{md,html}` 固定别名 + `reports/index.json`；`ls-remote` 区分"分支不存在"与网络/凭证失败 | `b86e4b7`（同上） |
| **B1 生产目录里的 2,533 行测试**（`regression_test`/`smoke_test`/`thinking_chain_tests` 住 `disciplines/liuyao/scripts/`） | 三个测试 CLI `git mv` 到科内 `tests/`（不跨树，保「每科自包含」）；三处路径基址改由 `../scripts` 派生使 outputs/报告语义不变；6 处调用点同步 | 见 AUDIT §四之二（2026-09-29） |
| 仓库级质量门在中文 Windows **恒红**（唯一失败项 ming [3]「narrate 应声明非命运断言」） | 根因：gate 以 UTF-8 解码子进程输出，而子进程按控制台代码页（GBK）写字节。新增 `yishu_core.runtime.utf8_subprocess_env()` 单点强制子进程 `PYTHONUTF8=1`，接入 6 处 subprocess 调用点；ming 各 CLI 补 `force_utf8_stdio()`（`runtime.py` 明文约定此前 6 个 CLI 全缺） | `ea3a0e2`（2026-09-29） |
| `ctext`/`ctpl` 断语取用器**五份逐字节相同副本**（sha256 `cbdd3873274473d2`） | 唯一实现收进 `chain_verdicts.py`（与 `note_text`/`vdesc` 同居），五个规则模块改 import，清死导入 `_CR_NOTES`/`_CR_TPL`；每文件 −16/+1 | `f500b25`（2026-09-29） |
| **B3 内核领域命名泄漏**：`ming_tables` 放着命卜两科共用的纳音/三合/星煞，模块头却写「唯一消费方：命科，卜科不用」 | 纳音 + 三合局分组 → `symbols.py`（顺带补齐章程里本就写着的「三合」）；星煞 → 新 `shensha.py`（模块头标注两科共用）；`ming_tables` 只剩藏干十神/大运/命宫身宫；6 处消费方同步 | `697bc75`（2026-09-29，记录见 AUDIT §四之三） |
| **B2 巨型模块** `classical_rules_patterns` 909 行（`scripts/` 最大） | 按域切出 `classical_rules_combo`（合破局）与 `classical_rules_growth`（十二长生/绝处逢生），patterns → 369 行；死导入同步清零 | `0b11419`（2026-09-29） |
| `tools/eval.py` 两处长期缺陷：引用从未存在的 `ming/scripts/evaluate.py`（默认命令恒失败）+ docstring/默认 split 不一致（`all` 纳入排除案例恒报错） | 缺评测器改为非致命跳过；默认改回 `tune+holdout`（`--full` 追加外部集）；`check.py` 不依赖它 | 2026-09-27ab |
| **`tools/eval.py` 未挂门**（HANDOFF §四.6「在 `--full` 盒之外，回归不会被测出」）+ 各科 evaluate **CLI 契约不齐**（大六壬 evaluate 不认 `--split`，使 `tools/eval.py` 恒失败 2 项） | ① 大六壬 `evaluate.py` 增 `--split`（接受但明说忽略：本科是单一机械一致率集）；② 根门新增 `[7d] 各科案例对齐分一览` 跑 `tools/eval.py`（`--full`/`--only eval_overview`），无 evaluate 的学科按「无案例对齐评测」跳过 | 2026-10-02i（见 CHANGELOG） |
| 范围收缩：卜科四科 → 仅 `ming`（四柱）+ `liuyao`（六爻） | `git mv` 三科归档至 `archive/`（保历史、可还原）；清理 `tools/`+`synthesis/` 引用，删 `normalize_*` 死代码 | `d341b0b`（CHANGELOG 2026-09-27z） |
| pytest 从根目录收集失败（四科同名 `smoke_test`/`evaluate` 撞车） | `--import-mode=importlib` + `testpaths=["tests"]`，纯配置零逻辑 | `0e08202`（2026-09-27y） |
| `human_narrative` 979 行巨石 | 正文段落八段素材切出 `human_narrative_segments` | `3de6502`（26x） |
| `chain_narrate._inject_pattern_tags` 359 行巨石 | 格局标签切出 `chain_narrate_patterns`（曾因循环依赖回退过） | `1e302dd`（26w） |
| `_predict_timing` 491 行应期巨石 | 按职责切出 `chain_step5_yp_timing` | `32a2f61`（26v） |
| 26u 三次拆分（step5 991 / format 445 / step3 509）+ 验收假阳性修正 | 分别切出 `chain_step5_adjust` / `engine_format_report` / `chain_step3_strength`；新增 `refactor_guard` | `92acbfc` `00e678e` `9f813e2` `70a0314`（26u） |
| 仓库整洁：死代码与过期文档 | 删 `factor_waterfall` / `engine_legacy` / `hallucination_guard` / 冗余可视化 / 过期研究稿；双 HANDOFF 合一 | `dae6522`（26e） |
| `classical_rules` / `chain_step4` / `chain_step5` 拆分 + 巨石看门狗 | 按域/职责拆分，零指纹漂移 | `7245408` `b0daa52` `f5dc349`（26k/26m） |
| 真值表上收内核、假拆清理、命科机械扩充 | 旬空/三刑/长生上收 `core.symbols`；清理复制的死 step5 | `f4645c3`（26n） |
| 应期判别力（两次调优，含一次已否证的退让） | 古例通用规则排序；否证项见 HANDOFF 否证清单 | `27bc352` `5099e86`（26c/26d） |
| 应期回收闭环（B2） | 结构化候选外露 + 回填扩展 + `outcome-eval` 评分 | `ffef571` |
| 六爻四段契约 + 合参层 + 仓库级质量门 | 立项实现 | v0.0.1 大更（2026-09-23） |

---

## 二、待清偿（pending，按阻塞类型分组）

### 2.1 阻塞于外部数据（**无法在库内解决，禁止考卷调参**）

| 债务 | 现状 | 阻塞说明 |
|---|---|---|
| `wikisource` 应期泛化 top-1 ~20%（n=35） | 待验证 | 需换书或真实反馈 **n≥30**；**禁止考卷调参**（HANDOFF §四.1） |
| 《卜筮正宗》卷次 | 未数字化 | 原文存 `data/sources/`，不伪造占验例 |
| **三科外部独立集（梅花/小六壬/择吉）** | 阻塞于外部数据（2026-09-30k/30l 定性） | 复刻核验已证《梅花易數》书源占例与现有集完全同集（5/5 字段一致，转录无误）、无新增例；他本/续书（梅花心易/易学入门/易隐）实测维基文库均不存在，小六壬/择吉书源未数字化。解除路径＝用户供书/扫描他本/实占积累后照六爻范式建 `external_cases.json` 永不调参 split；**禁止考卷调参** |
| 《火珠林》候选 | 3 例未过校验 | 卦变/缺时刻未过三方校验，存 `huozhulin_candidates.json`，**不入 holdout** |
| 择吉通书真黑箱 | 已还原 | 2026-09-29 从 `archive/zeji/` 还原；重启机械因子 + 裁决口径回归全绿（当时所记"100%"的口径性质已于 2026-09-30e 审计订正，见 §一） |
| 小六壬外部书源 | 已还原 | 2026-09-29 从 `archive/xiaoliuren/` 还原；落宫为历法真值，诀句同源，n=15 |

### 2.3 深度能力缺口（已论证，见 `docs/DEEP-DIVE-PLAN.md`）

| 债务 | 现状 | 阻塞说明 |
|---|---|---|
| **六爻「用神伏藏 + 合绊」进方向聚合**（2026-10-01u 登记）——**✅ 伏藏半边已清偿（2026-10-02s）**：核实合绊已有有界方向权重（原神贪合忘生 −2.0 / 日月合绊 −0.2 梯度 / 动化合绊 −0.3）；真空缺是「伏而不得出」方向零反馈，已补 −1.0（判据读 step2 `fu_cang_detail.results[].can_emerge` 结构，所本《黄金策·千金赋》"伏无提挈终徒尔"；分列验收全持平、golden 零漂移、`tests/test_liuyao_fu_no_emerge.py` 锁定） | 已清偿（残余：reg_07 引擎「飞空得出 +1.5」与占行人古籍直断的解释分歧，证据链可见；「不得出」书源基准例待建——119 例探针核实评测集暂无触发例） |
| **六爻评测盲区**（~~旺衰定性、六神临用、墓库零覆盖~~ ✅ 30p 激活；~~卦身、三合零覆盖~~ ✅ 30r **卦身口径修复**：原实现按日干阴阳+代数定爻位，与《卜筮正宗》安月卦身诀（世爻阴阳+世爻位→卦身支）不符，已修并古籍例验证；卦身/三合/用神入三合维度激活；**六合/六冲判据已归一**（2026-10-01u：删手写卦名白名单，改由 core `hexagram_he_chong_kind` 判，tune 96.8 / holdout 89.7）；~~墓库只验临日/月墓~~ ✅ 2026-10-02a 补齐**动墓/化墓**（判据唯一源 `use_god_tomb_tags`，新外部集 `suigui_holdout` 两例书源真例），见 CHANGELOG 10-02a）：剩 ~~反吟/伏吟/进退神/入墓/暗动/月破为格局词子串匹配~~ ✅ 2026-10-02g 已改**读 `advanced_analysis` 结构**（`hidden_movement`/`monthly_break`/`triple_combo`/`three_punishments`/`repetition`；不再扫 `step5`/`summary` 文本），口径变更后读数：holdout 89.7→**90.2**、wikisource 56.3→**56.9**、suigui 92.0→**94.5**，tune 96.8 不变；`tests/test_liuyao_pattern_tags.py` 锁三口径（~~use_god_position 全 N/A~~ ✅ 30o 补 14 例） | 待清偿 | 需继续补基准例；用神多现案例爻位留 N/A 不硬填；卦身/三合无古籍案例锚点，只填主集（对通则对表） |
| **命科案例评测两维已立（2026-09-30n）**：调候 21 例（tune）+ 四柱 174 例（holdout，《穷通宝鉴》命例表 70 表提取，历法反查真实时刻，引擎 174/174=对表回归，随机基线≈1.7%）；十神/藏干/格局/神煞/大运仍无书源 expected | 待扩 | 需从古籍占验实录建例（**只评书上明写的量，缺的记 null 走 N/A 剔除**）；「状元/词林」等富贵断语已逐字保留于 note 但**不计分**；十神/藏干为四柱派生量（同源性高，价值有限），格局/大运需书例明写 |
| **命科八字缺失判据**：~~从格 kind 缺口~~ ✅ 2026-10-02t（通用规则「官杀当权不落从势」，from_kind 15/15，见 CHANGELOG 10-02t）；~~通关~~ ✅ 2026-10-02b 已落地（《滴天髓·通隔論》逐字入库 + 日主两路「官杀克身得印 / 身财相战得食伤」结构标签，只出结构不批吉凶）、病药、~~格局成败救应~~ ✅ 30t/30u、~~三会~~ ✅ 10-01p、~~四柱间独立刑冲害合~~ ✅ 2026-10-02f 已落地（`pattern.pillar_relations`：四支两两六合/六冲/六害 + 三刑，表取内核；《滴天髓·地支論》逐字三首入库；**合化/争合妒合/冲开墓库**仍欠，须透干与月令条件，语料待拓）、~~天干五合~~ ✅ 2026-10-02h（同函数四干两两，表取 `core.relations.STEM_WUHE`）、~~胎元~~ ✅ 10-01p、~~小运~~ ✅ 10-01p、~~流月~~ ✅ 10-01p、~~岁运并临~~ ✅ 30u、~~天克地冲~~ ✅ 10-01p、~~十神组合~~ ✅ 10-01p、女命夫子星（~~调候用神~~ ✅ 2026-09-30g 已落地，`ming_tables.TIAO_HOU`） | 待清偿 | 新增神煞/起例**无逐字出处者一律标 `verified=false`**，不得把流俗起例写成古法；病药（《神峰通考》）、女命夫子星（《滴天髓·女命章》有子星取法）仓库暂无对应语料，须先拓书源 |

| 新门类：**N1 大六壬落地（骨架+多批深化+课目识别纯结构判据，条数与分组以 `scripts/kemu.py::IMPLEMENTED` 为准）+ 备选一灵棋经落地（第八科，124 课表直录，2026-09-30l）**，④ 已凑足两门；N1 剩余：课目表中**倚赖旺相/神煞/年月/年命**者（含需节气的天祸、二烦、天寇、孤寡、地盘等）/《毕法赋》/应期/涉害口径；N2 奇门：kinqimen MIT 参照已核，**煙波釣叟歌已抓取（5970B，第三轮成功）但实测无定局表**——定局起例表的书源仍未落实（遁甲演义/御定奇门宝鉴均实测不存在），骨架维持不启动；N3 七政四余未动 | 待清偿 | 骨架状态见 `docs/NEW-DISCIPLINES.md` §2.1 落地状态；N2 可参照 kentang2017 MIT 引擎（许可先核实，见 `docs/RESEARCH-HOROSA.md` §四）；相科按铁律不做 |
| **大六壬课例集扩至 43 例后暴露的 2 例非涉害失配**（2026-10-02p；其余 8 例失配均落在引擎自标 `verified=false` 的涉害门，属已知异说）：`LE036` 癸未「似返吟卦…缘三传申寅申」（引文自述近昴星柔日，引擎按贼克出寅卯辰）、`LE041` 乙巳「传鬼化父母…三传酉巳丑」（引擎出子申辰，两读分属金局/水局） | 待追源 | 须先判定是**书源传抄讹误**还是**引擎通则缺陷**：两例引文已逐字留档（`data/cases/course_examples.json` 的 `source_quote`），可对照《大六壬指南》他本或卷一取传诀复核；**禁止为过此二例写 case 分支**（`AGENTS.md` §四.3），须落通用规则并说明古籍出处 |
| **Horosa 调研采纳项**：① 报告忠实度审计工具 ✅（`tools/report_faithfulness.py`，12 例语料、确定性 supported/invented/contradicted 分类，已挂根门 [6]）；② 缺参结构化澄清信封 ✅（`core/yishu_core/report/request.py` 结构性缺参门禁：六壬无时刻不起课、灵棋三部缺一即无课等）；③ 合参「分歧披露不平均」✅（`synthesis/cross_rules.py`：分歧如实并列两趋向及触发条件，不平均不调和）；④ 报告机器可读出处块（口径开关+指纹）——部分：report_meta 页头+口径声明页脚已统一单源，机器可读指纹块未建；⑤ kentang2017 MIT 引擎许可核实——未做（奇门 N2 维持不启动，见 NEW-DISCIPLINES） | 部分清偿 | ④ 待建（须评估 render 指纹影响）；⑤ 随 N2 启动一并核（**AGPL 代码不得复制**） |


### 2.2 有意保持（非缺陷，强改会违反铁律）

| 债务 | 为什么不动 |
|---|---|
| 命科从格仍 `tentative`；运年交互只记关系不批吉凶 | 不作命运定论（`AGENTS.md` §一.3）；不程式化成「注定」 |
| 星煞不进主分 | 无古籍定性表不臆断（HANDOFF 口径） |
| 报告「格局详释」依赖案例是否触发格局词 | 案例驱动，非缺陷（HANDOFF §四.7） |
| ~~断语残句~~ **判据已换代（2026-10-01e）**：旧判据数 `.py` 中文字面量条数，假阴性（漏小六壬整句）与假阳性（docstring 当断语）并存；现由 **[1c] 黑箱取证门**（`tools/verdict_audit.py --strict`，跑真实报告反查未外置句）接管。残留的 argparse help / 测试夹具由白名单 `NON_VERDICT` 口径排除；白名单逐条复核为 HANDOFF §四.B |

### 2.4 工程卫生（可机械判定，不涉学科能力）

| 债务 | 现状 | 阻塞说明 |
|---|---|---|
| ~~`liuyao/guard/*.json` + `dev_tools/guard/base_human.json` + `liuyao/scratch/golden_before.json`~~ **✅ 已判定（10-01q）** | 已确认为**报告产物快照**（`human_markdown` 全文）；**已从取证门语料池剔除**——留着会让"写过的就算外置"，审计失效 | **结论：不属仓库债务**。`guard/` 与 `scratch/` 均在 `disciplines/liuyao/.gitignore` 内（本地临时快照，不入库）；全仓仅 `dev_tools/refactor_guard.py` 在**显式** `--write/--compare` 时读写，无门或脚本常态读取；`tools/verdict_audit.py` 已把 `guard/scratch` 排除出语料池。本地文件可按需清理，不影响任何门 |
| **render 段（四段契约之四）无行为保护** ~~✅ 已清偿（2026-10-02c）~~ | 六爻 golden `rows` 只罩 chart+analyze；`narrate_sha` 是 `i % 24 == 0 and not moving` 抽样（288 例约 12 条） | **已清偿**：① `[6b]` 结构级（八科口径句/尾注/禁用词，10-01p）；② **内容级 2026-10-02c**——`[6b]` 对八科 render MD 取逐字节 sha 并与 `data/golden/render_digest.json` 比对，漂移即判败，重捕须 `--raise-render --reason`（负例自证会咬人）。全局与站点共用同一批最小请求 |
| `tools/scratch/` 一次性调试产物（847 文件） | ✅ 已清（847 → 0，空目录保留）；取证门改落临时目录，加 `--save` 才落盘，不再每次跑门攒 80 个钩子文件 | 已清偿 |
| `check_verdict_literals` 与 [1c] 功能重叠 | 降级为粗筛（两个方向都有漏），主判据是 [1c] | **已拍板：留**（2026-10-02s）——作为零成本粗筛，在 [1c] 跑真实报告前先拦截成堆字面量；其粗筛局限已在 [1c] docstring 说明 |
| **引文层构建器与入库 `data/*.json` 可能脱钩**（脱钩后重跑构建器会**静默删掉手工补录条目**，且现行门全绿——"做错无人知"） | **机制已建 ✅ 2026-10-02k**：内核 `corpus_kit.check()` 语义比对 + 根门 `[1j] 语料可复现`（负例自证会咬人）。已接入 **ming/`build_dts_corpus.py`**、**ziwei/`build_corpus.py`**、**meihua/`build_classics.py`**、**zeji/`build_citations.py`**、**lingqi/`build_ketable.py`**、**ming/`build_tiaohou.py`**（2026-10-02m 接入时当场查出该建器两个叠加缺陷——内核路径错位 + list 插进字符类导致「重跑即把调候书证写成 120 个空格」，修复后与入库逐格一致，见 CHANGELOG 10-02m）、**liuren/`build_course_cases.py`**（2026-10-02n 同类缺陷：`STEMS = HEAVENLY_STEMS` 使 `DAY_RE` 恒不命中 → 重跑会把 `course_examples.json` 清成空集；修复后与入库一致）、**liuren/`build_kemu_notes.py`**（2026-10-02o 接入；**就地合并**语义按其自身口径比对——把「合并后应落盘的那份」与入库比，`_comment` 提为常量供两处共用，见 CHANGELOG 10-02o）——**语料建器已全部纳入 `[1j]`，无待补**。**不适用者**：案例集构建器（含人工裁决）与 `build_question_use_gods`/`build_use_god_rules`（其 `--check` 语义是「复验引文仍逐字命中源文」） |

---

## 三、防新债纪律（改本仓库时必须）

1. **巨石看门狗**：学科 `.py` > 2200 行即失败（`tools/check.py` 结构检查）。
2. **拆分/搬家一律零指纹漂移验收**——用 `disciplines/liuyao/dev_tools/refactor_guard.py`
   （在学科根即以 `dev_tools/refactor_guard.py` 调用），**禁止临时脚本**
   （26u 踩过「传错参数 → 115 例全挂 → 两次指纹一致其实都是全失败」的假阳性）。
3. **内核表唯一真值源**：天干地支/六冲六合三刑/十二长生/墓库/旬空/卦表/纳甲/卦辞爻辞
   只能在 `core/yishu_core` 存在一份，学科不得复制（违反直接驳回）。
4. **死脚本**：一次性脚本进 `tools/scratch/`（已 gitignore）或写完即删，**不入库**。
5. **断语/引文/卦辞进 `data/*.json`，代码只留算法**（`AGENTS.md` §三）。
6. **改引擎**：tune/holdout **分列出分**，禁止 holdout 混进 tune 冒充提升；tune 无故
   跌破基线即回归；改**通用规则**并给古籍出处，禁止 case-specific 私有分支。
7. **口径变更必须登记** `docs/CHANGELOG.md`，否则分数不可比。
8. **命名不携带版本**（`run_blind_v5.py` / `HANDOFF_V8.md` 禁写），版本走 git 与 CHANGELOG。

---

## 四、2026-09-27 治理扫描结论

本轮对「死脚本 / 冗余 skills / 债务文档化」三条线索逐一扫描，**结论与处置如实登记，不美化**：

| 线索 | 扫描结果 | 处置 |
|---|---|---|
| **死脚本** | tracked 层**已干净**：`tools/scratch/` 全程 gitignore（仅 demo 产物 + 2 个一次性 snapshot 辅助，不入 git）；无遗留 `split_*.py`；`disciplines/liuyao/scripts/` 各模块均被导入或具 CLI，未发现孤儿模块 | **无需动作**（若强行删无关文件会引入回归风险，违背「正确改对」） |
| **冗余 skills** | 活跃 `SKILL.md` 三份职责分明：根路由 205 行 / `liuyao` 419 行 / `ming` 25 行（路由器 vs 各科实现指南，**非冗余**）；`.workbuddy/skills/` 无项目级技能，用户级无 yi 相关冗余 | **不强行合并**——无安全合并点，拆合只会破坏现有装配、制造新债 |
| **历史债务文档化** | 此前债务散落在 CHANGELOG 各条目 + HANDOFF 叙述中，缺一份速查登记 | **新增本文件**（现有 HANDOFF §四 保留为叙述版，互为指针不互为副本） |

> 判断原则：宁可登记「扫描后确认无需动作」，也不为了交付感去动 codebase 制造新风险。
> 「已清偿」表随时间只增不改，「待清偿」表里每条都要写清**阻塞原因**——写不出阻塞原因的
> 债务通常说明它其实已经能解决，或根本不该叫债务。
