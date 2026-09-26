# 六爻 · 路线

> 现状与读数见 `docs/HANDOFF.md`（六爻节）与本目录 `HANDOFF` 归并后的根交接。
> 口径变更见 `disciplines/liuyao/docs/CHANGELOG.md`。过程诊断与已完成施工叙事已删。

## 里程碑状态

| 阶段 | 内容 | 状态 |
|---|---|---|
| M0 止血 | 唯一评分器、案例时刻还原、历法自检、git 卫生 | ✅ |
| M1 内核合一 | 15 表合一、巨石拆成 chain_*/classical_*/engine_*、卦辞上收 `hexagram_texts` | ✅ |
| M1b 断语外置 | `verdicts.json` / `verdict_texts.json` / 问题词典 | 🔶 chain_step5 已外置；`classical_rules` 残余字面量仍在 |
| M2.1 用神 | 关系法则 + 覆盖 + 186 键词典 + 世爻兜底 | ✅ |
| M2.2 应期 | 单位分列候选池；通用古例排序（化空/回头生/飞克伏/先值后合） | ✅ 判别力已立；wikisource 仍弱 |
| M2.4 外部集 | 维基文库《增刪卜易》253 图三方校验；`wikisource_holdout` n=35 | ✅ 集已立，泛化未证明 |
| M3 呈现 | `render` 单一出口 + SVG 卦盘 + 一键 `yi_liuyao` + 黄金样例 | ✅ |
| M4 并入易 | 迁入 `disciplines/liuyao/`，内核上收 `core/` | ✅ |

## 仍开放（详见 HANDOFF「还欠什么」）

1. wikisource top-1 泛化（换书扩样或真实反馈 n≥30；禁止考卷上调参）
2. `classical_rules` 残余断语外置
3. 病药/星煞进入 step5 加权与评分维度
4. 应期日/月两级预算的「解除障碍之期」外推
5. 报告内容合一（排盘图 + 正文 + 应期表一份交付）与 MCP 正文/导出

## 明确不做

- 宣称现实预测命中率
- case-specific 断语 / 私有别名
- 拿外部集试规则再挑一个（考卷 tuning）
- 相科内容
