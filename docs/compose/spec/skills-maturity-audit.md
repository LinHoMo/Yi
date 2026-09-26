---
feature: skills-maturity-audit
status: delivered
updated: 2026-09-26
branch: main
commits: # analysis-only, no implementation commits
---

# 占卜 Skills 完备性与 Harness 黑箱水平审计

## Report

**What was built** — 对 Yi 仓库做全量认知重建：core / synthesis / 四科 disciplines / tools 评估链。按「老师傅」标准逐科评估机械推演、断语、案例、契约完备性；并用古书案例实跑黑箱评测（tune / holdout / wikisource_holdout），核对 harness 真实水平。本文件为审计结论，不改引擎。

**Verification** — 实跑命令与读数见 §[S4]。六爻 `tools/check.py` 当前未全绿（金标准指纹漂移 + tune 93.7 < 基线 94.2），属仓库现状，非本次审计引入。

**Journey log**
1. 四科 100 分主要来自「规则与案例同源」的自洽，不等于泛化能力；六爻外部集 56.3% 才是更诚实的尺子。
2. 应期 top-1（25–35%）接近或低于随机期望（33–38%），文档自认不可用，与实测一致。
3. 病药、星煞在六爻代码中 0 命中；择吉神煞/彭祖百忌未建模——这些是「老师傅手感」的硬缺口。
4. 案例库隔离、口径诚实、机械归代码三条铁律总体合规；六爻仍有部分中文判据散落 .py。

---

## [S1] Problem

需要回答三个问题：

1. 项目认知是否完整、架构与铁律是否自洽？
2. 四科（六爻/梅花/小六壬/择吉）作为占卜 skill 是否齐全，能否到「老师傅」水准？
3. 能否用古书真实案例做黑箱测试？模型与工作流 harness 到什么水平？

## [S2] Design / 结论

### 2.1 项目定位（一句话）

中国传统术数统一工程：只做**命**（四柱）与**卜**（六爻/梅花/小六壬/择吉），一份内核 + 学科适配 + 合参层；相科明确不做。差异化在多科对齐与冲突裁决，不在「算得准」的营销口径。

### 2.2 架构

```
SKILL.md（路由） → disciplines/<科>（chart→analyze→narrate→render）
                        ↓ schema
                   synthesis（person / normalize / cross_rules / guidance）
                        ↓
                   core/yishu_core（唯一真值源 + eval + report）
```

铁律：机械运算归代码；案例库物理隔离；对齐分 ≠ 预测率。

### 2.3 完备性总表（老师傅标准）

| 科 | 完备性 | 流程契约 | 机械深度 | 案例/黑箱 | 老师傅级？ |
|---|---|---|---|---|---|
| 六爻 | **~78%** | 最严 | 22 格局+五步链 | 强（42+35+2） | **助手级，未到人师** |
| 梅花 | **~55%** | 完整 | 体用互变+数应 | 薄（holdout=3） | 否 |
| 小六壬 | **~50%** | 完整 | 六宫查表 | 薄（断法浅） | 否 |
| 择吉 | **~48%** | 完整 | 三因子裁决 | 非古书占验例 | 否 |
| 命·四柱 | **骨架** | — | 仅表未推演 | — | 未建 |

### 2.4 黑箱实测（2026-09-26，strict）

| 集合 | n | 对齐分 | 备注 |
|---|---|---|---|
| 六爻 tune | 20 | **93.7%** | 低于基线 94.2，门禁未过 |
| 六爻 holdout | 12 | **84.8%** | 未参与调参 |
| 六爻 wikisource_holdout | 35 | **56.3%** | 最保守，永不调参 |
| 六爻 yingqi_holdout | 2 | 89.3% | n 过小仅参照 |
| 六爻黑箱回归 | 18 | **13/18** | 基线 11/18 |
| 金标准指纹 | 288 | **已漂移** | 行为变更未锁 |
| 梅花 all | 13 | 100% | holdout=3，同源自洽 |
| 小六壬 all | 15 | 100% | 起课真值+诀句对照 |
| 择吉 all | 15 | 100% | 历法规则自洽，非古书断验 |

应期判别力（六爻）：top-1 tune 35.3% / holdout 25.0% / wikisource 20.0%；随机期望约 33–38% → **应期弱于或贴随机，不可用**。

### 2.5 各科距老师傅的硬缺口

- **六爻**：病药（0 实现）、星煞（0 实现）、应期收敛、断语仍散落 py（约 494 处 CJK）
- **梅花**：万物类象、多爻动、应期年月维度、holdout 扩样（现 3）
- **小六壬**：邻宫速断、方位/五行综合断、古籍纵深（现源为近现代手册）
- **择吉**：天德/月德/冲煞/彭祖百忌/时辰入裁决、通书古例真黑箱
- **命科**：推演引擎整段缺失，合参规则 5 常态降级「未参评」

### 2.6 Harness 水平评级

| 能力 | 水平 |
|---|---|
| 古书案例一键黑箱 | **能**（六爻最强；三科同构但样本薄） |
| tune/holdout 分列 | **能** |
| 口径诚实（对齐分≠预测率） | **能且是亮点** |
| 判别力体检（应期 vs 随机） | **能（六爻独有）** |
| 新鲜度守卫（防旧分冒充） | **能** |
| 统一仓级 eval 入口 | **缺**（仅 check/demo/install） |
| holdout 独立性 | **弱**（HO 与 tune 同书；词典同源） |
| 基线棘轮 | **锁死过拟合风险** |

**综合判断**：工程契约与评估纪律达到可审计水准；断法深度距真正老师傅仍有系统差距。六爻约「可上岗助手」；后三科是「合格骨架 + 浅断法」。综合完成度约 **65–70%**。

## [S3] Out of Scope

- 不改引擎/规则/案例（本次纯审计）
- 不做相科、紫微
- 不把对齐分解释为现实预测率

## [S4] Verification（实跑命令）

```
cd disciplines/liuyao && python scripts/evaluate.py --split all
# → strict 73.9% (n=74), 5 例引擎报错 ZS021–025

cd disciplines/liuyao && python scripts/evaluate.py --split tune
# → strict 93.7% / legacy 97.3%

cd disciplines/liuyao && python scripts/evaluate.py --split holdout
# → strict 84.8% / legacy 90.9%

cd disciplines/liuyao && python tools/check.py
# → 金标准指纹漂移；tune 93.7 < 94.2；回归 13/18；其余门过

cd disciplines/meihua && python scripts/evaluate.py --split all   # 100% n=13
cd disciplines/xiaoliuren && python scripts/evaluate.py --split all # 100% n=15
cd disciplines/zeji && python scripts/evaluate.py --split all       # 100% n=15
```

## Tasks

- [x] T1: 全量阅读与项目认知重建 — acceptance: 架构/铁律/四科/评估/教训可复述 (covers: S1)
- [x] T2: 四科老师傅完备性分析 — acceptance: 每科缺口清单+百分比 (covers: S2, S2.3, S2.5)
- [x] T3: 古书案例黑箱实测 harness — acceptance: 实跑读数+缺陷列表 (covers: S2.4, S2.6, S4)
