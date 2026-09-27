# 易 · 现状交接

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。
> **一切分数是古籍案例对齐分，不是现实预测命中率**（`AGENTS.md` 铁律三）。
> 路线：`docs/YI-PLAN.md`、`docs/LIUYAO-PLAN.md`。规格归档：`docs/compose/spec/`。

**基线**：`main` @ `42cdc7c`（2026-09-26，含 deep-optimize 与 internal-depth-pack 两轮合入）。

---

## 一、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹 **`5c6e77ee253b0ddd`**；清刻本 822 纳甲/105 卦变/120 世应 0 不合） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 186 键词典 → 世爻兜底 |
| 吉凶方向 | tune **93.9**、holdout **87.5**（strict 对齐分） |
| **应期** | tune top-1 **58.8%**（随机~38）；holdout **50.0%**（随机~36.5）；**日/月/年分列**已输出 |
| 病药 | step5 有界加减；**星煞不进主分**（`shensha_policy`：《卜筮正宗》辟星煞） |
| 断语治理 | 标签/口吻/建议/场景/开场/动变/特殊格局句入 `verdict_texts.json` + `narrative_templates.json` + `advice_rules.json` |
| 呈现 | `render` + SVG；MCP `liuyao.*` |
| 现实命中率 | **无法评估** |

**当前读数（strict，`cd disciplines/liuyao && python tools/check.py`）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **93.9** | 58.8% | 参与过调参 |
| holdout | 12 | **87.5** | 50.0% | 未参与调参 |
| wikisource_holdout | 35 | **57.3** | 20.0% | 永不调参 |
| wikisource_direction | 36 | **72.2** | — | 有吉凶无验期 |
| yingqi_holdout | 2 | 87.2 | — | n 过小仅参照 |
| 黑箱回归 | 18 | 12/18 | — | 基线 ≥11 |

对外引用：优先 holdout/wikisource，**必须带 n 与集合名**。

### 梅花 / 小六壬 / 择吉 — 已归档（2026-09 范围收缩）

- 三科曾完整实现（四段管线 + 案例评测 + 质量门），已于 2026-09 经 `git mv` 归档至 `archive/meihua/`、`archive/xiaoliuren/`、`archive/zeji/`，保留完整 git 历史、可随时还原。
- 不在当前实现、测试、质量门与文档「可用」范围内；本节历史读数仅作留存。

### 命科 — 机械推演已立（非命运断言）

- 强弱 / 月令定格 / 扶抑喜用 / 大运 8 步 / 流年干支×十神 / **大运×流年机械对照**
- 起运：顺行下一节、逆行上一节；运干十神；空亡；从儿/从财/从杀/专旺（tentative）
- 金标准 `3d4ff149ef6be933`；机械回归 5 例；pytest 覆盖
- **不做**：命运断语、流年吉凶定论

### 合参 / 工具

- `tools/check.py`（结构/内核自测/断语键一致/ming 质量门/六爻冒烟/合参/**pytest**）
- `tools/eval.py`、`tools/demo.py`、`tools/mcp_router.py`、`tools/core_selftest.py`、`tools/text_keys_selftest.py`
- person + outcome-eval

---

## 二、怎么跑

```bash
python tools/check.py              # 快速门
python tools/check.py --full       # + 案例评测 + 黑箱回归 + pytest tests
python -m pytest tests -q          # 76 项单测
python tools/eval.py               # 两科对齐分一览

# 六爻
cd disciplines/liuyao
python tools/check.py
python scripts/evaluate.py --split tune|holdout|wikisource_holdout|wikisource_direction
python scripts/yi_liuyao.py "所问之事" --when "..."
python scripts/mcp_server.py

# 命科
cd disciplines/ming
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男
python tools/check.py                # 含机械回归

# MCP（当前仅命 ming 注册；六爻走专用 mcp_server.py）
python tools/mcp_router.py --help
python tools/mcp_router.py --discipline ming --test-narrate

# 其余（meihua/xiaoliuren/zeji 已归档至 archive/，不再维护）
# cd archive/meihua && python tools/check.py
```

流派开关（改了分数不可比）：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

# 拆分/搬家前后的零漂移验收（报告文本 + 思维链 + 人话叙述，115 例）
python tools/refactor_guard.py --write  guard/base.json   # 改前
python tools/refactor_guard.py --compare guard/base.json  # 改后

**金标准**：`python tools/golden.py verify`；改动后 `capture "理由"`。

---

## 三、应期规则（核心资产）

位置：`chain_step5_yp_timing.predict_timing_core`（`_predict_timing` 经 `chain_step5_yp` 再导出，26v 拆出；签名不变）。**通用古例归纳，禁止 case-specific**。

优先级（高→低）：

1. 化出之支逢空 → 出空值日
2. 空而化回头生 → 不作空论，期于生我之日
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实
4. 伏藏：飞克伏→先冲飞；飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 不空：动爻先值日再逢合；静爻值日再逢冲
7. 空亡出空 / 三合 / 原神 / 化出 / 旺相

**评分（strict）**：相对窗 / `RHYTHM_PAIRS` 0.7× / 绝对窗（`yingqi_windows`）。
**分列**：`evaluate` 输出 `yingqi_day/month/year`（只报数，不设新门槛）。

否证（勿重复踩坑）：

- 病药/药码进应期主排序 → holdout top-1 掉，**已回退**
- 书序整体重排 → 三集全降，**已回滚**
- 回头生全局前插 → 挤掉值日，**改仅空卦**

---

## 四、还欠什么（按优先序）

1. **wikisource 应期泛化** top-1 ~20%（n=35）：等换书或真实反馈 n≥30；**禁止考卷调参**。
   - 《卜筮正宗》卷次未数字化（原文存 `data/sources/`）；《火珠林》3 例未过卦变/时刻门（`huozhulin_candidates.json`）。
2. **择吉通书真黑箱** ⌛ 已随择吉科 2026-09 归档至 `archive/zeji/`；如重启再做（不优先）。
3. **小六壬**外部书源仍缺 ⌛ 已随小六壬科 2026-09 归档至 `archive/xiaoliuren/`；如重启再做（不优先）。
4. **巨石残余**（已全部清，见 CHANGELOG）：
   `chain_step5` 991→351、`format_reading_output` 445→~30、`step3_analyze_strength` 509→322、
   `_predict_timing` 491→四职责模块 `chain_step5_yp_timing`（26v）、
   `chain_narrate._inject_pattern_tags` 359→三职责模块 `chain_narrate_patterns`（26w）、
   `human_narrative` 979→编排/渲染/格局引文/推因 + 新模块 `human_narrative_segments`（正文段落八段素材，26x）。
   全部零指纹漂移验收通过。
5. **断语残句**：扫描后确认残留多为 argparse help 与测试夹具文本（属 CLI 文档，不是断语），
   真正面向求测者的文案已在 `data/*.json`；此项**暂不再动**，避免误伤。
6. **命科**：从格仍 tentative；运年交互只记关系不批吉凶（有意如此）。
7. 报告「格局详释」依赖案例是否触发格局词。

---

## 五、口径与纪律

1. 对齐分 ≠ 预测率；禁止「准确率 X%」
2. 报分必带：集合名 + n + 是否调参
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；通用规则 + 古籍出处
4. 口径变更记 `docs/CHANGELOG.md`
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由
7. 拆分/搬家以**零指纹漂移**验收（用 `tools/refactor_guard.py`，别自己写临时脚本——
   26u 就踩过「脚本传错参数 → 115 例全挂 → 两次指纹一致其实都是全失败」的假阳性，
   该脚本现在会强制校验有效样本数）；巨石看门狗 2200 行

---

## 六、架构要点

```
core/yishu_core     唯一真值源（历法/象数/旬空三刑长生/纳音/十神/评分）
disciplines/<科>    四段契约 chart→analyze→narrate→render
synthesis           person + 合参 + outcome-eval
tools               check / eval / demo / mcp_router / selftests
tests/              pytest（relations/symbols/najia/yingqi/ming_dayun）
```

- **真值表**：旬空/三刑/十二长生/纳音/三合 已上收 core；看门狗盯同义表名
- **已拆**：`classical_rules_*`、`effects_harmony/structure/change`、`chain_step5` 假拆死体已删
- **已拆（26u）**：`chain_step5_adjust`（step5 八个加减项）、`engine_format_report`（报告九段）、
  `chain_step3_strength`（step3 八个修正项）。三个新模块都不反引调用方，单向依赖。
- **已拆（26v）**：`chain_step5_yp_timing`（应期四职责：收集/法则/排序/组装 + 5 个原闭包辅助提升）。
  `chain_step5_yp` 退化为再导出入口，依赖单向。
- **已拆（26w）**：`chain_narrate_patterns`（叙事格局标签三职责：收集标签 / 收集详释 / 编排注入；
  `_inject_pattern_tags` 原 359 行巨石）。`chain_narrate` 退化为再导出入口，依赖单向，规避循环依赖。
  **再拆的硬约束**：`thinking_chain.py` 从 `chain_step3` / `chain_step5` 再导出一批名字，
  搬动前先 grep `from chain_stepN import` 确认不是再导出项，否则断链。
- **已拆（26x）**：`human_narrative_segments`（正文段落素材八段：旺衰 / 结论开头 / 动变 / 特殊格局 /
  应期 / 综合定性 / 病药 / 星煞 + 私有辅助 `_pos_name`/`_question_focus`/`_clean_reason`/
  `_resolve_bing_yao_shensha`/`_line_on_pos`/`_line_plain` + 模板加载；从 `human_narrative` 按域切出）。
  `human_narrative` 保留编排（`build_human_narrative`）/ 渲染（`render_human_markdown`）/
  格局引文（`_extract_pattern_tags`/`_select_relevant_quotes`/`_pattern_advice_hint`）/ 推因
  （`_build_explain_summary`），并再导出搬移名。`human_narrative_segments` 只 import 叶子模块
  （`chain_verdicts`/`chain_tables`），单向依赖、无循环。
- **MCP**：六爻 7 方法（专用 `mcp_server.py`）；命 ming 经 `tools/mcp_router.py` 注册 chart/analyze/narrate/render/list_methods（meihua/xiaoliuren/zeji 已归档）

---

## 七、变更索引（查 CHANGELOG）

| 记号 | 内容 |
|---|---|
| 26e–m | 整洁/断语第一批/命骨架/大运/巨石拆分 |
| 26n | 真值表上收 + step5 假拆清理 + 命科机械扩充 |
| 26o–s | 星煞口径/建议库/场景提示/键自测 |
| 26t | internal-depth-pack：断语收尾 + effects 拆分 + pytest + MCP 四科 + 应期分列 + 运年交互 |
| 26u | 巨石收尾：step5 / 报告排版 / step3 三拆（零指纹漂移）+ 死导入清理 |
| 26v | 巨石收尾续：_predict_timing 491 行应期巨石按职责切出（零指纹漂移）+ 死代码清理 |
| 26w | 巨石收尾续：chain_narrate._inject_pattern_tags 359 行格局标签巨石按职责切出（零指纹漂移）+ 死导入清理 |
| 26x | 巨石收尾续：human_narrative 979 行按域拆——正文段落八段素材切到 human_narrative_segments，编排/渲染/格局引文/推因留 human_narrative（零指纹漂移）+ 死导入清理 |
