# 灵棋经（lingqi）· 学科规程

铁律、目录契约、口径纪律一律引 `AGENTS.md`（仓库根），本文件不复制。

## 定位

- 起课=三部掷数（上/中/下 各 0..4 面数，全零不成课，共 **124 课**），
  **查表即断**——课名/象/卦注/象曰/詩曰全部逐字来自
  `data/ketables.json`（书源 `data/sources/ling-qi-jing.wikitext.txt` 逐字提取，
  铁律三可回指）；
- 本仓不做任何书外发挥：narrate 只编排书源原文；解读结合求测语境；
- core 零增补（NEW-DISCIPLINES 备选一预期兑现）。

## 命令

```bash
python scripts/chart.py --up 4 --mid 3 --down 2 --question "占谋事" [-o out.json]
python scripts/analyze.py chart.json [-o analyze.json]
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md
python dev_tools/check.py        # 质量门（课表 124 课完整性 + 全课查表 + 金标准）
python dev_tools/golden.py verify
```
