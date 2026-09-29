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
| 《火珠林》候选 | 3 例未过校验 | 卦变/缺时刻未过三方校验，存 `huozhulin_candidates.json`，**不入 holdout** |
| 择吉通书真黑箱 | 已归档 | 2026-09 范围收缩归档至 `archive/zeji/`；重启再做（**不优先**） |
| 小六壬外部书源 | 已归档 | 同上，归档至 `archive/xiaoliuren/`（**不优先**） |

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
