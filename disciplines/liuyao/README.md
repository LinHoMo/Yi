# 六爻 · 纳甲断卦引擎

> 易 v0.0.1（版本号唯一真值源在 `core/yishu_core/__init__.py`）

易项目的第一个学科（卜）。装卦排盘由代码完成，象数解读交给 LLM——机械运算与判断分离，
是这套代码的根本约束（见 `../../AGENTS.md`）。

方法论依《火珠林》《黄金策》《卜筮正宗》《增删卜易》，体系为汉代京房纳甲。

## 装与跑

```bash
pip install -e .                    # 无必需第三方依赖，纯标准库
python tools/check.py               # 一条命令跑全部质量门（历法/冒烟/用例/回归/对齐分）
```

起一卦（一条命令出单文件报告）：

```bash
python scripts/liuyao_engine.py --mode coin --question "所占之事"
python scripts/liuyao_engine.py --mode manual --yao "7,8,9,7,6,8" \
       --datetime "2026-09-22 10:30" --format text
python scripts/thinking_chain.py <上一步的 json 文件>     # 五步思维链
python scripts/liuyao_engine.py --mode coin --question "所占之事"        --format html --save-html outputs/report.html       # 直接出报告
python scripts/build_portal_assets.py --run-eval          # 重建门户与样例报告
```

评测（分数是**古籍案例对齐分**，衡量与古籍案例要点的一致性，不是现实预测命中率）：

```bash
python scripts/evaluate.py --split tune            # 参与过调参的 20 例
python scripts/evaluate.py --split holdout --save  # 未参与调参的 12 例
```

## 现在的真实水平（2026-09-22，strict 口径）

| 集合 | 对齐分 | n |
|---|---|---|
| tune（参与过调参） | 93.7% | 20 |
| holdout（未参与调参） | 78.7% | 12 |

分维度（holdout）：用神六亲 91.7% / 用神地支 91.7% / 吉凶方向 75.0% / 格局 91.7%。

**应期看的是判别力，不是召回率。** 旧版把动爻、变爻、用神之冲合、原神四支、伏飞神、
旬空、日月全部并集当"重点应期"报出来（平均 11.1/12 支），召回率 100% 却与瞎蒙无异。
M2.2 改为按用神状态择优后：主应期(top-1)命中 29.4%（随机基线 8.3%）、
候选集 4.4/12 支、基准应支平均名次 2.13/12。仍不够可用，但至少是个能改进的数。
2026-09-23 起评分改**单位感知**（基准写「未月」而引擎答「未日」不再算命中）后当前读数：
tune 主应期命中 35.3%（平均名次 2.0）、holdout 25.0%（2.2）、外部集 20.0%（2.0）；
与 29.4% 等旧读数**不可直接比**。
口径与逐次变化见 `docs/CHANGELOG.md`。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 给 LLM 的执行规程（起卦流程、解读骨架、强制叙事要素、自检清单） |
| `core/yishu_core/` | 历法与干支内核：自求节气、立春定年界、儒略日定日柱，含 16 项自检 |
| `scripts/liuyao_engine.py` | 装卦排盘（唯一排盘入口）：纳甲、世应、六亲、六神、旬空、变卦 |
| `scripts/classical_analysis.py` | 22 类动变关系检测：伏藏、暗动、月破、三合、进退、反吟伏吟… |
| `scripts/thinking_chain.py` | 五步思维链：现状 → 取用神 → 旺衰 → 动变 → 综合 |
| `scripts/human_narrative.py` | 唯一交付正文（师傅口吻），不做"人话/古典"两张皮 |
| `scripts/yi_liuyao.py` | 一键闭环（M3.2）：`python scripts/yi_liuyao.py "问题" --when "..."` → 单文件报告 |
| `scripts/render.py` | 报告渲染单一出口（M3）：analyze JSON → Markdown / 单文件 HTML |
| `scripts/visualization.py` | SVG 组件库：卦盘（爻线/六亲/六神/世应/空破/动变）、应期时间线、五行雷达 |
| `scripts/build_portal_assets.py` | 门户与样例报告构建，分数从评测结果取，不写常量 |
| `scripts/mcp_server.py` | JSON-RPC stdio 服务：divinate / quick_reading / validate_hexagram … |
| `references/` | 纳甲规则、断卦方法论、十二格局、四大经典综合、案例库（黑箱用） |
| `data/cases/` | 古籍案例 42 例 + tune/holdout/excluded 分层 |
| `docs/` | CHANGELOG（分数口径史）、规划交接 |
| `docs/samples/` | 黄金样例与样例报告（M3.4/3.5）：`感情卦_巽之涣.html` 为唯一模板，报告须过六项验收清单（六神临用/持世/卦身/格局详释/公历应期/边界克制） |

## 四条不可协商的规则

1. **排盘只能由代码做**。LLM 不得心算卦宫、纳甲、世应、六亲、旬空、变卦。
2. **案例库与预测过程隔离**。`data/cases/` 与 `references/case_library.md` 只用于测试与事后校验。
3. **一卦一事**。换实质角度就另起一卦，不在原卦里延伸硬推。
4. **口径诚实**。不得把对齐分说成预测率；医疗、法律、投资一律提示以专业意见为准。

## 已知待修

历法与评分已重建（M0 完成）。剩下的按优先级：三处双写的规则表合一（M1）→
应期法则与用神取法决策表（M2）→ 呈现层（M3，已完成：单一 HTML 出口 + SVG 真卦盘 +
一键闭环 `yi_liuyao.py` + 门户修伤 + 黄金样例模板 `docs/samples/感情卦_巽之涣.html`）。
详见仓库外的 `../docs/LIUYAO-PLAN.md`。
