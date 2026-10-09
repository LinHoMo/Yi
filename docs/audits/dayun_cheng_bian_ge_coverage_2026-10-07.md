# 行运成格变格覆盖度审计（OPT-ziping_zhenquan_pingzhu_dz-02）

| 字段 | 值 |
|---|---|
| OPT ID | OPT-ziping_zhenquan_pingzhu_dz-02 |
| 优先级 | P1 |
| 审计日期 | 2026-10-07 |
| 审计人 | 妙手 (CatPaw) |

## 一、审计目标

确认 `disciplines/ming/scripts/evaluate.py` 及其调用的 `pattern.py` 中是否具备**行运触发的成格/变格**逻辑（即大运流年参与格局成判断，而非仅凭本命四柱）。

## 二、审计范围

| 文件 | 关键函数/段 |
|---|---|
| `disciplines/ming/scripts/pattern.py` | `judge_pattern_cheng_bai()` — 格局成败救应 |
| `disciplines/ming/scripts/pattern.py` | `dayun_table()` — 大运 8 步排盘 |
| `disciplines/ming/scripts/pattern.py` | `dayun_liunian_interactions()` — 大运×流年干支交互因子 |
| `disciplines/ming/scripts/evaluate.py` | `score_case()` — 格局维度打分 |

## 三、审计结论

### 3.1 pattern.py — 格局成败仅论本命

`judge_pattern_cheng_bai()` 的判定流程（L485-603）：
1. 成条件满足（书源明写的成格结构）→ 成格
2. 否则忌神透干：救应透 → 救应成格；无救 → 破格
3. 忌神未透 → 成格

**判据完全来自本命四柱**：月令本气十神定格 → 透干十神查成/忌/救应集合。**无大运/流年干支参与**。

### 3.2 pattern.py — 大运仅排盘不改格局

- `dayun_table()` (L776) 只排 8 步大运干支 + 起运岁数
- `dayun_liunian_interactions()` (L888) 只输出干支交互因子（岁运并临等）
- 两者都**不返回格局成/变结论**，不成也不判"逢运成格"或"逢运变格"

### 3.3 evaluate.py — 格局打分维度不涉及行运

`score_case()` 中的 pattern 维度（L250-268）只评 `exp.strength.pattern` + `exp.pattern_cheng_bai`。expected 案例中是否纳入行运触发的成格变格——当前引擎无此输出，故无此 expected，也不打分。

### 3.4 结论

**当前仓库不存在行运触发成格/变格的结构判定逻辑。**

书源依据（`data/sources/ziping_zhenquan_pingzhu_dz.dz.txt:325`）：
 > 命之格局，成于八字，然配之以运，亦有成格变格之要权。其成格变格，较之喜忌祸福尤重。

明确指出"成格变格"是独立于"喜忌祸福"且"尤重"的判定层，但此层**未在当前引擎中实现**。

## 四、处理方式

按 OPT 指令：**审计结论落档 + evaluate.py 补注释**，不改判定值/不改分数。

- 不新增判定逻辑（P1 审计只做确认，不写新引擎代码）
- 补注释于 `evaluate.py` 格局维度打分段，标记此行运成格变格缺口，引用书源 L325

## 五、验收

- [x] 审计结论落档：`docs/audits/dayun_cheng_bian_ge_coverage_2026-10-07.md`
- [x] `evaluate.py` 格局维度段含行运成格变格缺口注释
