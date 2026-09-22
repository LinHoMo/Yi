# 六爻 · 纳甲断卦引擎

易项目的第一个学科（卜）。装卦排盘由代码完成，象数解读交给 LLM——机械运算与判断分离，
是这套代码的根本约束（见 `../AGENTS.md`）。

方法论依《火珠林》《黄金策》《卜筮正宗》《增删卜易》，体系为汉代京房纳甲。

## 装与跑

```bash
pip install -e .                    # 无必需第三方依赖，纯标准库
python tools/check.py               # 一条命令跑全部质量门（历法/冒烟/用例/回归/对齐分）
```

起一卦：

```bash
python scripts/liuyao_engine.py --mode coin --question "所占之事"
python scripts/liuyao_engine.py --mode manual --yao "7,8,9,7,6,8" \
       --datetime "2026-09-22 10:30" --format text
python scripts/thinking_chain.py <上一步的 json 文件>     # 五步思维链
```

评测（分数是**古籍案例对齐分**，衡量与古籍案例要点的一致性，不是现实预测命中率）：

```bash
python scripts/evaluate.py --split tune            # 参与过调参的 20 例
python scripts/evaluate.py --split holdout --save  # 未参与调参的 12 例
```

## 现在的真实水平（2026-09-22，strict 口径）

| 集合 | 对齐分 | n |
|---|---|---|
| tune | 97.1% | 20 |
| holdout | 86.2% | 12 |

分维度（holdout）：用神六亲 91.7% / 用神地支 91.7% / 吉凶方向 75.0% / 格局 91.7% / 应期 83.3%。

**应期仍不具备判断力**：引擎声明的"重点应期"平均覆盖 11.1/12 个地支，
而随机列出同样多候选即全覆盖的期望就有 91.7%；真正有区分度的 top-1 命中只有 12.5%。
旧口径把这一项记成 100%，是因为它按全文词面匹配算分。详见 `docs/CHANGELOG.md`。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 给 LLM 的执行规程（起卦流程、解读骨架、强制叙事要素、自检清单） |
| `core/yishu_core/` | 历法与干支内核：自求节气、立春定年界、儒略日定日柱，含 16 项自检 |
| `scripts/liuyao_engine.py` | 装卦排盘（唯一排盘入口）：纳甲、世应、六亲、六神、旬空、变卦 |
| `scripts/classical_analysis.py` | 22 类动变关系检测：伏藏、暗动、月破、三合、进退、反吟伏吟… |
| `scripts/thinking_chain.py` | 五步思维链：现状 → 取用神 → 旺衰 → 动变 → 综合 |
| `scripts/human_narrative.py` | 唯一交付正文（师傅口吻），不做"人话/古典"两张皮 |
| `scripts/visualization.py`、`build_html_report.py` | HTML 报告（两套并行，待 M3 合一） |
| `scripts/mcp_server.py` | JSON-RPC stdio 服务：divinate / quick_reading / validate_hexagram … |
| `references/` | 纳甲规则、断卦方法论、十二格局、四大经典综合、案例库（黑箱用） |
| `data/cases/` | 古籍案例 42 例 + tune/holdout/excluded 分层 |
| `docs/` | CHANGELOG（分数口径史）、规划交接 |

## 四条不可协商的规则

1. **排盘只能由代码做**。LLM 不得心算卦宫、纳甲、世应、六亲、旬空、变卦。
2. **案例库与预测过程隔离**。`data/cases/` 与 `references/case_library.md` 只用于测试与事后校验。
3. **一卦一事**。换实质角度就另起一卦，不在原卦里延伸硬推。
4. **口径诚实**。不得把对齐分说成预测率；医疗、法律、投资一律提示以专业意见为准。

## 已知待修

历法与评分已重建（M0 完成）。剩下的按优先级：三处双写的规则表合一（M1）→
应期法则与用神取法决策表（M2）→ 三套呈现合一与一键报告（M3）。
详见仓库外的 `../docs/LIUYAO-PLAN.md`。
