# 灵棋经（lingqi）· 学科规程

铁律、目录契约、口径纪律一律引 `AGENTS.md`（仓库根），本文件不复制。

## 定位

- 起课=三部掷数（上/中/下 各 0..4 面数，全零不成课，共 **124 课**），
  **查表即断**——课名/象/卦注/**卦宫**/标注组全部逐字来自
  `data/ketables.json`（书源 `data/sources/ling-qi-jing.wikitext.txt` 逐字提取，
  铁律三可回指）；
- 标注组（`notes`）为**有序组**，各带书源原文的标注名：象曰（124 组）/詩曰（123 组）/
  又（41）/又曰（1）/許曰（1），共 **290 组**——书源把注名写作「，」「；」的课照收，
  不为凑格式改写原文；
- 卦宫（`gong`）取卦注末段（如「乾天西北」），书源共 9 串、**八卦齐**
  （「兌」两见「兌澤正西」「兌金正西」，异文照录）；本仓不另立卦宫表；
- 书末非课标题章节（`==純陰饅==`，全陰不成课）登记在 `appendix`，按原文存档、
  不参与查表——**不得静默并入相邻课**；
- 本仓不做任何书外发挥：narrate 只编排书源原文；解读结合求测语境；
- core 零增补（NEW-DISCIPLINES 备选一预期兑现）。

## 通道覆盖

本地 CLI、通道 A 网页（GitHub Pages + Pyodide，零凭证）、通道 B 云端 Actions 三路皆通，
**八科全挂载**；科 × 通道的**权威矩阵见仓库根 `llms.txt`「能力矩阵」，本文件只引用不复制**。
网页深链 `?d=lingqi&up=…&mid=…&down=…&q=…&auto=1`，触发与取回报告见 `docs/AI-SOP.md`。

口径红线（不因挂载而变）：**灵棋经只做书源逐字直录《靈棋經》原文断语，无书外发挥。**

## 命令

```bash
python scripts/chart.py --up 4 --mid 3 --down 2 --question "占谋事" [-o out.json]
python scripts/analyze.py chart.json [-o analyze.json]
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md
python dev_tools/build_ketable.py           # 课表重建（默认 dry-run，--write 落盘）
python dev_tools/check.py        # 质量门（课表完整性 + [1c] 引文可回指 + 全课查表 + 金标准）
python dev_tools/golden.py verify
```
