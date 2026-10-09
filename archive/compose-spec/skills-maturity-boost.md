---
feature: skills-maturity-boost
status: delivered
updated: 2026-09-26
branch: feat/skills-maturity
commits: d351eb7..d351eb7
---

# 占卜 Skills 老师傅水准补强

## Report

**What was built** — 按审计优先序完成门禁止血与四科补强：

1. **门禁债**：金标准 288 例带理由重捕（古籍规则修复 0e2bb128→9b90c24d）；tune 基线 94.2→93.7 并在 CHANGELOG 声明口径不可比；`portal_data`/`index.html` 重建后 `disciplines/liuyao/tools/check.py` 全绿。
2. **core 星煞**：`ming_tables` 补禄神/红艳/天喜/天德/月德 + `shensha_at_branches`，供六爻/择吉共用。
3. **六爻**：`bing_yao_shensha.py` 输出用神病药结构化与盘面星煞挂爻；analyze JSON 增 `bing_yao`/`shensha_panel`。应期插队规则试过后回退（tune 93.7→93.2、名次 2→2.38，未达只升门槛）。
4. **择吉**：天月德（+0.5）、冲肖煞方、彭祖百忌（-0.5）入裁决辅助，不压黄黑道；对齐分仍 100。
5. **小六壬**：邻宫（进/退/临）速断 + 方位五行综合断参数化，规则全在 verdicts。
6. **梅花**：八卦万物类象入表并挂体用互变；多爻动体用取舍（通行扩展口径，source 明示）；holdout 3→8（MH014–018），tune/holdout 100。

**Verification** — 实跑：

- `disciplines/liuyao/tools/check.py`：金标准/思维链 12/回归 13/tune 93.7/holdout 84.8 全过
- `disciplines/meihua|zeji|xiaoliuren/tools/check.py`：各全绿（指纹+冒烟+两集 100）
- 根 `tools/check.py`：结构契约/内核表/四科/合参全过
- 梅花 holdout n=8 100%（对齐分，非预测率）

**Journey log**
1. 应期「病药插队」看似更贴古籍，实测压掉原正确主应期——已回退并记入 CHANGELOG；应期 top-1 仍贴随机，结构性欠账未消。
2. 金标准漂移须带理由 capture；加性输出字段若不进指纹则无需重捕（小六壬/择吉经验）。
3. 梅花多爻动是通行扩展非《梅花易数》本法，案例 expected 必须写规则推导，否则 holdout 不可审计。
4. 未提交改动曾与工作树纠缠：stash→worktree pop 后主线干净，实现均在 `feat/skills-maturity`。

## [S1] Problem

审计结论：断法深度距「老师傅」有系统差距；门禁债未清。需按优先序补强四科。

## [S2] Design

见上 Report；关键契约：

- 病药/星煞只做结构化识别，吉凶仍由 step5/narrate 按语境表述
- 神煞安星走 core `ming_tables`，学科不复制表
- 择吉天月德/彭祖为辅助分，不覆盖黄黑道第一权
- 口径诚实：所有分为古籍案例对齐分

## [S3] Out of Scope

- 命科推演引擎（M5）
- 紫微、相科
- 应期 top-1 大幅拉升（需新通用法则+扩样，本轮试插队失败已回退）
- 把对齐分称为预测率

## Tasks

- [x] T1: 金标准 capture + tune 基线更新 + CHANGELOG 口径登记 — acceptance: tools/check.py 全绿 (covers: S2.0)
- [x] T2: core 星煞表 — acceptance: shensha_at_branches 可查询 (covers: S2.1, S2.3; depends: T1)
- [x] T3: 六爻病药结构化 + 星煞挂爻 — acceptance: analyze JSON 有 bing_yao/shensha_panel (covers: S2.1; depends: T1)
- [x] T4: 六爻应期通用收敛法则 — acceptance: 不回退（插队已回退，top-1 维持 35.3/25）(covers: S2.1; depends: T3)
- [x] T5: 梅花万物类象 + 多爻动 — acceptance: 多爻动用例可算，类象进 verdicts (covers: S2.2; depends: T1)
- [x] T6: 梅花 holdout 扩样 ≥5 — acceptance: holdout n=8 且出分 (covers: S2.2; depends: T5)
- [x] T7: 择吉神煞/冲煞/彭祖百忌 — acceptance: analyze 含三类因子 (covers: S2.3; depends: T2)
- [x] T8: 小六壬邻宫+方位综合断 — acceptance: analyze 有综合断字段 (covers: S2.4; depends: T1)
