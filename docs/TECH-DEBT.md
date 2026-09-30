# 技术债务登记（TECH-DEBT）

单一速查清单。**细节叙述见 `docs/HANDOFF.md` §四 与 `docs/CHANGELOG.md`**——本文件只做
**状态登记 + 提交锚点 + 阻塞说明 + 防新债纪律**，不重复叙述、不复制第二份真相。

- 报分口径铁律：仓库内所有分数都是**古籍案例对齐分**，非现实预测命中率（`AGENTS.md` §一.3）。
- 债务没有消失只有转移：本文件同时记录**已清偿**与**待清偿**，避免历史在某次
  HANDOFF 重写时被静默抹掉。

---

## 一、已清偿（resolved）

| 债务 | 处理 | 锚点 |
|---|---|---|
| **N1 大六壬未落地（骨架）** | 四段契约 + core `liuren_tables` + 九宗门判据树（720 例全枚举守门）+ 金标准 + 两条出报告通道（缺参澄清门禁）；深化第一批：合池修正（书例自证）+ 课例评测 4 例（机械一致率 3/4）；**深化第二批（2026-09-30j）**：课目识别首批八条（轩盖/斲轮/引从/亨通/三交/乱首/赎胥/冲破，kemu.json 诀表 58 条登记），八条在 720 例枚举全部有触发；铸印暂缓（诀文三传与链传中末对应存疑）；剩 65 课目其余条目/《毕法赋》/应期/涉害口径（LE004） | 2026-09-30h/i/j（见 CHANGELOG） |
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
| **六爻评测盲区**：旺衰定性、六神临用、卦身、三合、墓库开合零覆盖；反吟/伏吟/进退神/入墓/暗动/月破被降级为格局词**子串匹配**；`use_god_position` 在 tune/holdout **全为 N/A** | 待清偿 | 需先补基准例（expected 里 `use_god_position` 仅 3 例填了）。缺失环节第一批已把引擎侧格局检测补齐，剩的是**案例断言层** |
| **命科案例评测两维已立（2026-09-30n）**：调候 21 例（tune）+ 四柱 174 例（holdout，《穷通宝鉴》命例表 70 表提取，历法反查真实时刻，引擎 174/174=对表回归，随机基线≈1.7%）；十神/藏干/格局/神煞/大运仍无书源 expected | 待扩 | 需从古籍占验实录建例（**只评书上明写的量，缺的记 null 走 N/A 剔除**）；「状元/词林」等富贵断语已逐字保留于 note 但**不计分**；十神/藏干为四柱派生量（同源性高，价值有限），格局/大运需书例明写 |
| **命科八字缺失判据**：通关、病药、格局成败救应、三会、四柱间独立刑冲合害、胎元、小运、流月、岁运并临、天克地冲、十神组合、女命夫子星（~~调候用神~~ ✅ 2026-09-30g 已落地，`ming_tables.TIAO_HOU`） | 待清偿 | 新增神煞/起例**无逐字出处者一律标 `verified=false`**，不得把流俗起例写成古法 |

| 新门类：**N1 大六壬落地（骨架+两批深化+课目识别八条）+ 备选一灵棋经落地（第八科，124 课表直录，2026-09-30l）**，④ 已凑足两门；N1 剩余：65 课目其余条目/《毕法赋》/应期/涉害口径（LE004）；N2 奇门：kinqimen MIT 参照已核，**煙波釣叟歌已抓取（5970B，第三轮成功）但实测无定局表**——定局起例表的书源仍未落实（遁甲演义/御定奇门宝鉴均实测不存在），骨架维持不启动；N3 七政四余未动 | 待清偿 | 骨架状态见 `docs/NEW-DISCIPLINES.md` §2.1 落地状态；N2 可参照 kentang2017 MIT 引擎（许可先核实，见 `docs/RESEARCH-HOROSA.md` §四）；相科按铁律不做 |
| **Horosa 调研采纳项**：报告忠实度审计工具（AI 断言 vs 引擎结构化输出逐条分类 supported/invented/contradicted）、缺参结构化澄清信封、报告机器可读出处块（口径开关+指纹）、合参「分歧披露不平均」、kentang2017 MIT 引擎许可核实（奇门实现参照候选） | 待清偿 | 见 `docs/RESEARCH-HOROSA.md` §二/§四；**AGPL 代码不得复制**，上游许可须直接核实后方可 vendor |


### 2.2 有意保持（非缺陷，强改会违反铁律）

| 债务 | 为什么不动 |
|---|---|
| 命科从格仍 `tentative`；运年交互只记关系不批吉凶 | 不作命运定论（`AGENTS.md` §一.3）；不程式化成「注定」 |
| 星煞不进主分 | 无古籍定性表不臆断（HANDOFF 口径） |
| 报告「格局详释」依赖案例是否触发格局词 | 案例驱动，非缺陷（HANDOFF §四.7） |
| 断语残句 | 扫描确认残留多为 argparse help 与测试夹具文本（属 CLI 文档，不是断语）；**暂不再动**，避免误伤（HANDOFF §四.5） |

---

## 三、防新债纪律（改本仓库时必须）

1. **巨石看门狗**：学科 `.py` > 2200 行即失败（`tools/check.py` 结构检查）。
2. **拆分/搬家一律零指纹漂移验收**——用 `disciplines/liuyao/tools/refactor_guard.py`
   （在学科根即以 `tools/refactor_guard.py` 调用），**禁止临时脚本**
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
