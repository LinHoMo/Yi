# 易 · 总路线

> 现状读数与「还欠什么」见 `docs/HANDOFF.md`；分数口径变更见 `docs/CHANGELOG.md`。
> 本文只保留定位、架构契约与里程碑状态——过程叙事已删（git 历史可查）。
> 相科（面相、手相、堪舆）明确不做。

## 定位

易是命·卜两科的统一 skill：一份内核 + 若干学科适配层 + 一个合参层。
差异化不在「算得准」，而在多科结论如何对齐、冲突如何裁决、如何落成可执行建议。

| | 输入 | 回答 | 时间尺度 |
|---|---|---|---|
| **命** | 出生时空 | 格局与趋势 | 一生 |
| **卜** | 一念之动（六爻） | 一事成败与应期 | 一事 |

## 架构契约

```
core/yishu_core/     唯一真值源（干支历、象数表、卦辞、评分、报告 kit）
disciplines/<科>/    四段契约：chart → analyze → narrate → render
synthesis/           合参：person 档案 + 跨科裁决 + 阶段指导
tools/               check / demo / install
docs/                路线、交接、口径、样例
```

四段硬边界见 `docs/CONTRACT.md`。依赖单向：`disciplines → core`，`synthesis → disciplines 的 schema`。

合参裁决：各守其位；同向则确；异向则回溯起局/边界/用神后并列倾向；禁止无据安慰叙事。

## 里程碑

| 阶段 | 目标 | 状态 |
|---|---|---|
| M0 底座 | 立规范、唯一评分器、历法自检、git 卫生 | ✅ |
| M1 内核合一 | 规则表单点化、巨石拆分、断语外置 | 🔶 拆分/上收已完成；`classical_rules` 残余断语仍在 |
| M2 卜科扩展 | 梅花 / 小六壬 / 择吉 | ✅（2026-09-29 还原，各科 `dev_tools/check.py` 全绿） |
| M3 呈现 | 单一 render、一键 CLI、门户、黄金样例 | ✅ |
| M4 合参雏形 | person + 跨科裁决 + 指导 | ✅ |
| M5 命科 | 机械推演（强弱/格局/喜用/大运/流年对照），不写命运断语 | ✅ 2026-09-26+ |
| M6 交付 | **给链接即出报告**：纯前端（零凭证）+ 云端固定链接双通道 | ✅ 2026-09-30d，见 `docs/AI-SOP.md` |
| 六爻效度 | 外部集泛化、应期日/月分列、病药星煞入评分 | 进行中，见 HANDOFF「还欠什么」 |
| 各科深度 | 六爻补缺失断卦环节；八字补调候/通关/病药与格局成败救应 | 待办，见 `docs/DEEP-DIVE-PLAN.md` |
| ~~新门类~~ | ~~大六壬 / 奇门遁甲（时家转盘）/ 七政四余~~ | 已正式从产品面移除（archive/NEW-DISCIPLINES.md 留档） |

## 交付通道（"给链接即出报告"）

两条通道，**同一份引擎、同一条四段契约**，产出由 `tools/verify_web_parity.py` 逐字节验收：

| | 通道 A · 纯前端 | 通道 B · 云端 Actions |
|---|---|---|
| 怎么触发 | AI 拼深链 URL，用户点开即出 | AI 拼预填 issue 链接（人点提交）或 `workflow_dispatch`（需 Token） |
| 需要什么 | 只要仓库链接；**零凭证、零后端** | GitHub 账号或 Token |
| 引擎在哪跑 | 用户浏览器内（Pyodide） | GitHub runner |
| 报告在哪 | 用户浏览器，可下载 MD/HTML | `reports` 分支固定链接 + 逐次留档 + issue 回评 |

## 验收（怎样算落地）

- `python dev_tools/check.py` 全绿，tune/holdout 分列出分
- `python tools/check.py --full` 全绿（含站点构建 + 站点自检 + 网页/本地同源验收）
- 内核规则表无第二份；断语不堆在 `.py`
- 请求→命令行参数的映射只有一份（`core/yishu_core/report/request.py`）
- 分数必带集合名 + n + 是否调参；不出现「现实预测命中率」

