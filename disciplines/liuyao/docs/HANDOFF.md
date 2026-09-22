# 六爻 · 现状交接

> 易 v0.0.1

> 取代原 `BLIND_EVAL_HANDOFF_V8.md`（该文档报的 100.0% 已不可复现，且引用了一批已删除的脚本）。
> 分数口径的逐次变化一律查 `docs/CHANGELOG.md`；本文件只写"现在是什么、怎么跑、还欠什么"。

## 一、现在能不能信

| 事项 | 状态 |
|---|---|
| 装卦排盘（纳甲/世应/六亲/六神/旬空/变卦） | 可信。历法内核自检 16 项全绿，288 例金标准可复现 |
| 干支历（年界立春、月界十二节、日界夜子时） | 可信。自求节气，不查近似表 |
| 用神取法 | tune 100%、holdout 91.7%，但仍靠问题词典，未见过的问法会退化 |
| 吉凶方向 | tune 95%、holdout 75% —— 未参与调参的集合上只有 3/4 |
| **应期** | **尚不可用**。主应期命中 29.4%（随机基线 8.3%），有信号但远不够 |
| 现实世界命中率 | **无法评估**。仓库内所有分数都是古籍案例对齐分，见 `AGENTS.md` 铁律三 |

当前分数（strict 口径，`python tools/check.py` 可复现）：tune 93.7%（n=20，参与过调参）、
holdout 78.7%（n=12，未参与调参）。**对外应引用 holdout，并同时给 n。**

## 二、怎么跑

```bash
pip install -e .                          # 无必需第三方依赖
python tools/check.py                     # 六道质量门（历法/冒烟/用例/回归/对齐分/应期判别力）

python scripts/liuyao_engine.py --mode coin --question "所占之事"                 # JSON
python scripts/liuyao_engine.py --mode coin --question "所占之事" \
       --format html --save-html outputs/report.html                              # 一条命令出报告
python scripts/evaluate.py --split holdout --save                                 # 评测
python scripts/build_portal_assets.py --run-eval                                  # 重建门户
```

流派开关（默认值即上表所依据的口径，改动会让分数不可比）：

- `YI_GANZHI_BOUNDARY=day|instant`：交节"当日即换"还是"精确到时刻"。默认 `day`。
- `--distinguish-zi-hour` + `--zi-hour-type late`：夜子时按换日派起盘。默认不作次日。

## 三、这一轮（M0–M3 首批）改了什么

1. **历法内核**（`core/yishu_core/`）：自求节气，修掉四处真错——年柱不判立春（236 天错）、
   月建用固定近似日（44 天错）、五鼠遁 `%12` 写错、夜子时把日辰推到翌日。
2. **唯一评分器**（`scripts/evaluate.py`）：旧评分器已被删且 `score.py` 读错字段白送分；
   现在 strict/legacy 双口径同时打印，差值即口径水分。
3. **案例时刻还原**（`scripts/case_runner.py`）：不再把古籍案例塞进 2024-06-01 并用
   `"甲"+月支` 造干支（那会让旬空直接算错）；由内核反查真实公历日期，32/32 成功。
4. **规则表合一**（`core/yishu_core/symbols.py`）：15 张象数基元表删除 38 处本地副本；
   顺带修兑宫世次排错。`tools/golden.py` 288 例证明零行为漂移。
5. **应期择优**：由并集收集（平均 11.1/12 支）改为按用神状态取主/次应期并附法则。
6. **展示层**：报告加主/次应期表（应支＋法则＋日历日）；门户分数改从评测结果取，
   不再硬编满分；修「打开完整样例报告」死链；`visualize_shap.py` → `factor_waterfall.py`。

## 四·〇、P0：爻序约定（**已修**，2026-09-22）

**现象**：`BAGUA[*]["lines"]` 存的是**上爻在前**（震 [0,0,1] 实为艮之象），而
`build_hexagram_result(yao_values, …)` 把 `yao_values[0:3]` 当作**下卦**（初、二、三爻）。
两个约定混在一处，结果是：**按 SKILL.md 与 CLI 帮助所说"从下往上"手工喂六爻，会得到错的卦**。

复现（标准雷风恒自下而上＝阴阳阳阳阴阴）：

```bash
python -c "import sys;sys.path[:0]=['scripts','core'];import liuyao_engine as e; print(e.build_hexagram_result([8,7,7,7,8,8],'占','manual',2024,6,1,10)['original_hexagram']['name'])"
# 期望：恒　实际：损（山泽损）
```

**为什么案例评测没暴露它**：`case_runner.hex2yao()` 用同一批镜像表生成爻值，
错处两下相消，所以 42 例案例内部完全自洽（23/23 变卦可对上）。
金标准也测不出——它是同一套约定下的自比较。
能露馅的只有 ZS005：古籍注"戌土财爻（上六）动化巳"，而管线把动爻摆在第四爻（午）。

**影响面**：凡铜钱/手动/外部 JSON 入口，只要含 震·艮·巽·兑（非回文卦），
卦名、卦宫、世应、六亲、六神、动爻全部错位。案例库走的是内部自洽路径，故现有分数暂不受污染。

**为什么没有当场修**：这不是改一行的事——引擎与 `hex2yao` 是一对互相补偿的镜像，
单独修任何一侧都会让另一侧失配、42 例全部重排。正确做法是在内核定死"爻位自下而上"一个约定、
两侧同时改、并重跑金标准与全部门槛；这会合理地改变所有分数，需要单开一次施工做。

## 四、还欠什么（按优先级）

0. **P0 爻序约定统一**（见上节）：内核定死自下而上，引擎与 hex2yao 同时改，重捕金标准。


1. **M2.4 外部效度**：n=17 的应期样本撑不起任何结论。先扩未参与调参的古籍案例，
   再建实占结果回收（`logs/divination_events.jsonl` 已有 300KB 素材，但没有对错回填）。
   **在扩样之前继续调应期法则＝案例特判，禁止。**
2. **M2.1 用神取法决策表**：`_QUESTION_USE_GOD_MAP` 207 项问题词典是硬编码，
   SKILL.md 里"LLM 交叉校验用神"那段本质上是在替代码兜底。
3. **M1b 巨石拆分**：`thinking_chain.py` 6150 行、`classical_analysis.py` 4200 行、
   `liuyao_engine.py` 3670 行，1500+ 断语字面量仍在代码里，应外置 `data/verdicts.json`。
   日破/绝处逢生/回头克 三处判据仍双写，尚未收敛到单点。
4. **M3 剩余**：三套呈现合一（门户 / `build_html_report.py` / `visualization.py`）；
   卦盘仍是 CSS 色块条而非 SVG；MCP 只暴露到排盘＋思维链，未含正文与报告导出。
5. **M4 并入易**：迁到 `Yi/disciplines/liuyao/`，通用内核上收 `Yi/core/`。
