# 易（Yi）

本仓库只保留两个**相互独立、零耦合**的术数学科，各自携带一套完整可运行的实现：

| 目录 | 学科 | 说明 |
|------|------|------|
| `liuyao/` | 六爻（纳甲） | 六爻纳甲起卦、装卦、旺衰、应期、断语 |
| `bazi/`  | 八字（四柱） | 四柱排盘、格局、强弱、喜用、大运、流年 |

## 设计原则

- **无共享内核、无合参层**：两科之间没有任何相互 import，也不存在把六爻与八字整合分析的层（`synthesis` 已移除）。
- **各带私有引擎副本**：每一科目录下都有自己的 `core/yishu_core/`（干支、五行、纳甲、日历、神煞、表驱动判据等），因此两科可各自独立运行、独立优化，互不影响。
- **各自自包含**：每科目录内均有 `scripts/`（机械推演）、`data/`（案例、古籍底本、规则）、`references/`、`dev_tools/`、`docs/`，并自带 `README.md` 与 `SKILL.md`。**一处不一致要说清**：`tests/` 目前**只有六爻有**（`liuyao/tests/`）；八字侧**没有 `tests/` 目录**，其回归/冒烟/回验全部走 `bazi/dev_tools/`（`check.py` 的 `[0]–[21]`）。本行此前写作两科均有 `tests/`，与实际不符（2026-10-12 按 `ls -d bazi/tests` 实跑更正：`No such file or directory`）。

## 目录结构

```
Yi/
├── README.md          # 本文件
├── liuyao/            # 六爻（独立）
│   ├── core/yishu_core/   # 六爻私有的引擎副本
│   ├── scripts/ data/ references/ dev_tools/ docs/ tests/
│   └── README.md  SKILL.md
└── bazi/             # 八字（独立）
    ├── core/yishu_core/   # 八字私有的引擎副本
    ├── scripts/ data/ references/ dev_tools/ docs/   # 八字暂无 tests/（见上）
    └── README.md  SKILL.md
```

> 注：两科内部的 `core/yishu_core` 文件名相同，但内容各自独立；这是“零耦合、各自可独立运行”的刻意结果。引擎内部仍保留 `ming_tables` 等八字专用模块名，属内核命名，不影响学科独立性。

## 运行

直接进入对应学科目录运行其脚本即可，例如：

```bash
# 六爻：铜钱起卦
python liuyao/scripts/chart.py --mode coin --question "某事如何" --seed 42

# 八字：按出生时间排盘
python bazi/scripts/chart.py --datetime "1990-05-20 12:00" --gender 男
```

两科脚本各自通过“向上搜索 `core/yishu_core`”定位自己的私有内核，因此从任意位置调用都不会串到对方。
