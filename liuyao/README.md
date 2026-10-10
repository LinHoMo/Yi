# 六爻 · 纳甲断卦引擎

> 易 v0.0.1（版本号唯一真值源在 `core/yishu_core/__init__.py`）

六爻（卜）是本项目的两门独立学科之一。装卦排盘由代码完成，象数解读交给 LLM——机械运算与判断分离，
是这套代码的根本约束（完整规程见 `SKILL.md`）。

方法论依《火珠林》《黄金策》《卜筮正宗》《增删卜易》，体系为汉代京房纳甲。
**纯标准库、零第三方依赖**，无需安装，从学科目录直接跑。

## 装与跑

```bash
python dev_tools/check.py       # 一条命令跑全部质量门（历法/爻序/金标准/用例/回归/对齐分）
```

起一卦（一条命令出单文件报告）：

```bash
python scripts/yi_liuyao.py "所占之事" --when "2026-09-22 10:30" -o outputs/report.html
```

四段契约入口（chart→analyze→narrate→render，与八字科同构；薄适配层，不引入新断法）：

```bash
python scripts/chart.py   --mode time --datetime "2026-09-18 14:30" --question "所占之事" -o scratch/chart.json
python scripts/analyze.py scratch/chart.json  -o scratch/analyze.json    # 推演（含 conclusion）
python scripts/narrate.py scratch/analyze.json -o scratch/正文.md
python scripts/render.py  scratch/analyze.json -o outputs/report.md
```

评测（分数是**古籍案例对齐分**，衡量与古籍案例要点的一致性，**不是现实预测命中率**）：

```bash
python scripts/evaluate.py --split tune       # 参与过调参的 20 例
python scripts/evaluate.py --split holdout    # 未参与调参的 12 例
```

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
| `SKILL.md` | 给 LLM 的执行规程（起卦流程、解读骨架、强制叙事要素、自检清单） |
| `core/yishu_core/` | 学科私有内核副本：干支历法、纳甲、六十四卦表、旺衰等（与八字科各自独立、互不 import） |
| `scripts/engine.py` | 装卦排盘聚合入口：纳甲、世应、六亲、六神、旬空、变卦 |
| `scripts/chart.py`·`analyze.py`·`narrate.py`·`render.py` | 四段契约薄适配层（包装既有引擎） |
| `scripts/step1.py`…`step5.py`·`analysis_steps.py` | 五步思维链实现与 facade：现状 → 取用神 → 旺衰 → 动变 → 综合 |
| `scripts/classical_analysis.py` | 22 类动变关系检测：伏藏、暗动、月破、三合、进退、反吟伏吟… |
| `scripts/narrate_core.py` | 叙述层实现：思维链格局标签 / 推理链 / 解读正文生成 |
| `scripts/visualization.py` | SVG 组件库：卦盘、应期时间线、五行雷达 |
| `data/cases/` | 古籍案例 + tune/holdout/excluded 分层 |
| `data/rules/`·`data/sources/` | 判据表与古籍底本（引文逐字可回查书源） |
| `dev_tools/` | 质量门与数据构建工具（`check.py` 一条命令跑全部） |
| `tests/` | 思维链用例、古籍回归、冒烟（由 `check.py` 调度） |
| `references/` | 纳甲规则、断卦方法论、十二格局、四大经典综合、案例库（黑箱用） |
| `docs/` | `docs/CHANGELOG.md`（现行口径登记）、`docs/CASE-LIBRARY-AUDIT.md` |

## 四条不可协商的规则

1. **排盘只能由代码做**。LLM 不得心算卦宫、纳甲、世应、六亲、旬空、变卦。
2. **案例库与预测过程隔离**。`data/cases/` 与 `references/case_library.md` 只用于测试与事后校验。
3. **一卦一事**。换实质角度就另起一卦，不在原卦里延伸硬推。
4. **口径诚实**。不得把对齐分说成预测率；医疗、法律、投资一律提示以专业意见为准。