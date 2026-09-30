# 大六壬（liuren）· 学科规程

铁律、目录契约、口径纪律一律引 `AGENTS.md`（仓库根），本文件不复制。

## 定位

- 起课/排盘/三传/课体/天将 = **机械运算归代码**（`scripts/chart.py`）；
- LLM 只把结构化输出翻译成人话（`scripts/narrate.py`），**严禁心算**任何起例；
- 第一版**不出吉凶方向**：65 课目识别与《毕法赋》未落地（TECH-DEBT 登记），
  任何方向输出都属占位实现，禁止。

## 判据源

- 起例：`data/sources/liu-ren-da-quan.wikitext.txt` 卷一「入手法」（四库本，
  维基文库抓取，provenance 同目录）；
- 引文逐字存 `data/verdicts.json`，代码零字面量；
- 口径显式声明：月将=中气换将（`yuejiang_policy`）、昼夜贵人=卯酉分界、
  昴星阴俯/别责柔日前三合/涉害端点 等歧义读数 `verified=False` 登记。

## 命令

```bash
python scripts/chart.py --datetime "2024-02-20 10:30" --question "占求财" [-o out.json]
python scripts/analyze.py chart.json [-o analyze.json]
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md
python dev_tools/check.py        # 质量门（含 8640 例九宗门全枚举守门）
python dev_tools/golden.py verify
```
