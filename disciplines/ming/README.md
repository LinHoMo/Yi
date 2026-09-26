# 命 · 四柱骨架（M5）

> **本轮只立契约与机械因子，不做命理推演**（`docs/YI-PLAN.md` M5、`AGENTS.md` 范围）。
> 干支/藏干/十神/纳音/神煞来自内核 `yishu_core.ming_tables` / `ganzhi_calendar`。
> 合参层只吃 `analyze` 输出的结构化因子；**不产出格局断语、大运流年吉凶**。

## 四段契约

| 段 | 入口 | 输出 |
|---|---|---|
| chart | `scripts/chart.py` | 出生时刻 → 四柱、藏干十神、纳音、神煞、命宫身宫（纯机械） |
| analyze | `scripts/analyze.py` | 因子清单 + `verdicts: []`（空）+ 所本说明 |
| narrate | `scripts/narrate.py` | 明示「命科推演未实现」的占位正文 |
| render | `scripts/render.py` | Markdown：因子表 + 正文 |

## 怎么跑

```bash
cd disciplines/ming
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男 -o scratch/chart.json
python scripts/analyze.py scratch/chart.json -o scratch/analyze.json
python scripts/narrate.py scratch/analyze.json
python tools/check.py
```

## 边界

- 机械运算归代码；本层不写吉凶断语。
- 分数/命中率口径见根 `AGENTS.md` 铁律三（本轮无案例评测集）。
