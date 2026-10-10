# 六爻 · 纳甲断卦引擎

> 装卦排盘由代码完成，象数解读交给 LLM —— 机械运算与判断分离是这套代码的根本约束。
> 完整规程（起卦流程、解读骨架、强制叙事要素、自检清单、案例库隔离协议）见同目录 `SKILL.md`。

方法论依《火珠林》《黄金策》《卜筮正宗》《增删易》，体系为汉代京房纳甲。
**纯标准库、零第三方依赖**。

## 现在的真实水平（2026-10-10 实测，strict 口径）

| 集合 | 对齐分 | n | 主应期 top-1 |
|---|---|---|---|
| tune（参与过调参） | 97.2% | 20 | 64.7% |
| holdout（未参与调参） | 90.2% | 12 | 50.0% |

思维链用例 9/12、古籍回归 9/18；金标准指纹锁定 288 例（行为漂移看门狗）。
分数口径与逐次变化见 `docs/CHANGELOG.md`。

## 目录

| 路径 | 内容 |
|---|---|
| `core/yishu_core/` | 学科私有内核副本：干支历法、纳甲、六十四卦表、旺衰等（与八字科各自独立、互不 import） |
| `scripts/engine.py` | 装卦排盘聚合入口：纳甲、世应、六亲、六神、旬空、变卦 |
| `scripts/chart.py`·`analyze.py`·`narrate.py`·`render.py` | 四段契约薄适配层（包装既有引擎） |
| `scripts/thinking_chain.py` | 五步思维链聚合入口 |
| `scripts/step1.py`…`step5.py`·`analysis_steps.py` | 五步思维链实现：现状 → 取用神 → 旺衰 → 动变 → 综合 |
| `scripts/classical_analysis.py` | 22 类动变关系检测：伏藏、暗动、月破、三合、进退、反吟伏吟 |
| `data/cases/` | 古籍案例 + tune/holdout/external_holdout 分层 |
| `data/rules/`·`data/sources/` | 判据表与古籍底本（引文逐字可回查书源） |
| `dev_tools/` | 质量门（`check.py` 一条命令跑全部） |
| `tests/` | 思维链用例、古籍回归、冒烟（由 `check.py` 调度） |
| `references/` | 纳甲规则、断卦方法论、格局、经典综合、书源台账、案例库（黑箱用） |
| `docs/CHANGELOG.md` | 现行口径登记与指标读数 |

## 参考文档

| 文件 | 内容 |
|---|---|
| `references/najia_rules.md` | 纳甲装卦完整规则（八宫次序、纳支口诀、世应定位、六亲六神推演、旬空、十二长生） |
| `references/interpretation_guide.md` | 断卦方法论详解（用神取法、旺衰体系、动变规则、应期推断） |
| `references/pattern_reference.md` | 十二大经典格局速查 |
| `references/classical_synthesis.md` | 六爻四大经典综合 |
| `references/source_ledger.md` | 在库书源实测状态（可得性 / 哈希 / 行数） |
| `docs/CASE-LIBRARY-AUDIT.md` | 案例库应期抽取审计 |
