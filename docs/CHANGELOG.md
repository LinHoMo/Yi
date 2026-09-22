# 六爻 CHANGELOG

分数口径变化必须在此登记，否则 tune/holdout 数字不可比（`AGENTS.md` §四.4）。

## M0.4 历法内核（2026-09-22）

**新增** `core/yishu_core/`：`ganzhi_calendar.py`（太阳视黄经求十二节交节时刻 → 定月令、
以立春定年界、以儒略日定日柱）、`calendar_check.py`（16 项自检，全绿）、
`runtime.py`（Windows GBK 控制台 UTF-8 适配）。

**修掉四个真实错误**（此前依赖是否安装而表现不同）：

| # | 缺陷 | 影响（实测 2020-01-01…2026-12-31，2557 天） |
|---|---|---|
| 1 | 未装 lunar-python/sxtwl 时 `get_year_stem_branch` **完全不判立春** | 年柱错 **236 天**（约 9.4%，全在 1 月—立春前）。时间起卦/梅花以年支取数 → 卦本身会起错 |
| 2 | 月支用固定近似日（Feb 4 交立春等） | 月建错 **44 天**（1.7%）。月建是旺衰第一权，直接改变用神强弱判定 |
| 3 | 五鼠遁写作 `(start + branch) % 12` 再判 ≥10 减 10 | 戊/癸日辰时之后时柱错（如戊日辰时 甲辰 → 应为 丙辰） |
| 4 | `handle_zi_hour` 在 `hour == 0` 返回**翌日**日柱 | 00:00–00:59 起卦者日辰整体后移一天，且早/夜子时命名颠倒 |

**删除**：`SOLAR_TERM_DATES` 近似表及其 fallback 分支、`liuyao_engine` 顶部已失效的
lunar-python/sxtwl 探测块、两处 `from king_wen_sequence import ...`（模块已不存在却被
`except ImportError: pass` 静默吞掉，从不生效；原文留在 `scratch/legacy_eval/` 备查，
恢复与否待用户定）。

**行为变更**：无。默认交节口径 `boundary="day"`（交节当日即换月/换年），与旧近似表一致；
精确到时刻走 `boundary="instant"`（可用环境变量 `YI_GANZHI_BOUNDARY` 切换）。
夜子时默认不作次日，采换日派需显式 `--zi-hour-type late`。

**指标影响**：以上 1、2 会改变既有案例的月建/年柱，故此前所有分数（tune 100%、holdout 97.7%）
自本条起**作废**，待 M0.2/M0.3 重建评分器后重测真基线。

## M0.1 仓库卫生（2026-09-22）

生成物（`outputs/`、`logs/`、盲评中间产物、报告 HTML）出库；删除 55 个 `_debug_*/_patch_*`
与已被取代的 v2–v5 盲评/补丁脚本；旧评分器另存 `scratch/legacy_eval/` 作重写参照。
