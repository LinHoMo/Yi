# 命 · 四柱机械推演

> 干支/藏干/十神/空亡来自内核 `yishu_core.ming_tables` / `symbols` / `relations`；
> **纳音**归 `symbols`、**神煞**（`shensha_of_chart`）归 `yishu_core.shensha`——
> 两者 2026-09-29 自 `ming_tables` 按「命卜两科共用」拆出（审计 B3）。
> 合参层只吃 `analyze` 输出的结构化因子；**不产出命运吉凶断语**。

## 四段契约

| 段 | 入口 | 输出 |
|---|---|---|
| chart | `scripts/chart.py` | 出生时刻 → 四柱、藏干十神、天干十神、纳音、神煞、空亡、命宫身宫（纯机械） |
| analyze | `scripts/analyze.py` | 强弱/格局/喜用/大运 8 步/流年对照 + 机械 `verdicts`（均带 `basis`） |
| narrate | `scripts/narrate.py` | 因子正文；明确「非命运断言」 |
| render | `scripts/render.py` | Markdown：因子表 + 正文 |

## 怎么跑

```bash
cd disciplines/ming
python scripts/chart.py --datetime "1990-05-20 10:30" --gender 男 -o scratch/chart.json
python scripts/analyze.py scratch/chart.json -o scratch/analyze.json
python scripts/narrate.py scratch/analyze.json
python dev_tools/check.py
```

## 口径（可回溯）

- 强弱：藏干本/中/余气 1.0/0.5/0.25 + 得令加权；扶抑用神
- 格局：月令本气十神 → 正格名；从格仅 `tentative`
- 大运：年干阴阳×性别定顺逆；顺行取下一节、逆行取上一节；三日=一年
- 十神：运干/流年干对日主（`relations.ten_god`）
- 流年：只给干支×十神对照，不批吉凶

## 边界

- 机械运算归代码；本层不写吉凶断语。
- 分数口径见根 `AGENTS.md` 铁律三（古籍对齐分 ≠ 现实预测命中率）。
