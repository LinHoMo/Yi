# 大六壬（liuren）· 学科规程

铁律、目录契约、口径纪律一律引 `AGENTS.md`（仓库根），本文件不复制。

## 定位

- 起课/排盘/三传/课体/天将 = **机械运算归代码**（`scripts/chart.py`）；
- LLM 只把结构化输出翻译成人话（`scripts/narrate.py`），**严禁心算**任何起例；
- 本版**不出吉凶方向**：课目表（`data/kemu.json`）已全，其中一部分落机械判据
  （`scripts/kemu.py` 的 `IMPLEMENTED`，全部为纯结构条件）——**条数一律由该元组与
  `data/kemu.json` 运行时实算，文档不写死**（门 `[1c]` 会报出实算值）；《毕法赋》等吉凶诀未落地
  （TECH-DEBT 登记），任何方向输出都属占位实现，禁止。

## 判据源

- 起例：`data/sources/liu-ren-da-quan.wikitext.txt` 卷一「入手法」（四库本，
  维基文库抓取，provenance 同目录）；
- 引文逐字存 `data/verdicts.json`，代码零字面量；
- **同一事实只有一处权威源**：门类名单 = `scripts/jiuzongmen.py::MEN_ORDER`（门 `[1c]`/`[1d]`
  由它取名单与条数）；天将名单 = core `TIAN_JIANG_ORDER`；判据条数 = `scripts/kemu.py::IMPLEMENTED`；
  引文条数与逐字清单 = `dev_tools/check.py::verbatim_inventory`；课目表条数 = 书源卷一「课目」段
  实算（`check.py::book_kemu_count`，门 `[1c]` 比对）。文档与报告一律**引用**这些源，不另抄数字。
- **书源缺号已登记（不臆补）**：卷一「课目」段自编号 `一…六五`，实测**缺「五八」一条**，
  故段内实收 64 条 —— 缺号登记在门 `KEMU_NUMBERING_GAP`，由 `check.py::kemu_section_parse`
  按自编号逐行实算比对；将来若重抓补全或缺号变化，门 `[1c]` 立即判败，强制重新核对语料条数。
- **逐字口径（可机检）**：全部外置引文均为书源**去空白后的逐字子串**（字符级，保留标点
  与书名号）——
  ① `data/verdicts.json`：`men[*].basis` 诀文 + `tianjiang[*].verse` 乘临歌诀（门类名单的唯一
  真值源是 `scripts/jiuzongmen.py::MEN_ORDER`，天将名单是 core `TIAN_JIANG_ORDER`）；
  ② `data/kemu.json`：课目 `verse`（对卷一「课目」段）+ 课目 `note`（对卷七~十「课经集」）。
  照录范围含书源小字夹注（昴星「论初传也」、返吟「阳日用辰，阴日用日，辰上作中，日上作末」）
  与书名号（伏吟「《玉厯》」），异体字（夘/厯/圡/逰…）不归一。
  门 `[1d] 引文逐字门` 做**字符级**断言——与 `[1c]` 只比汉字的口径互补，后者滤掉《》与句读，
  故「去夹注/去书名号」在 `[1c]` 口径下不可见（本次 3 条漏检即出在此）。非逐字即判败，
  除非登记于 `data/verdicts.json#verbatim_policy.normalized`（每条须带 `rule` + `reason`）；
  登记与实测不符（含陈旧登记）同样判败。
  **条数不在此写死**：由 `dev_tools/check.py::verbatim_inventory` 运行时实算，门 `[1d]` 输出即
  实算结果（订正器 `dev_tools/fix_verbatim_basis.py` 与门共用这一处计算）。
  订正脚本 `dev_tools/fix_verbatim_basis.py`（默认 dry-run、已订正即幂等退出；`--write` 落盘）。
- 口径显式声明：月将=中气换将（`yuejiang_policy`）、昼夜贵人=卯酉分界、
  昴星阴俯/别责柔日前三合/涉害端点 等歧义读数 `verified=False` 登记。
- **课例集**（`data/cases/course_examples.json`）：由 `dev_tools/build_course_cases.py` 从
  书源（卷一 + 卷三~卷十二：起例/歌赋/课经集/《毕法赋》）按**严格唯一性口径**抽取
  （同句恰一日干支、恰一处「三传XYZ」、定位语须在「三传」之前且非传内关系语），
  expected 只有书上明写的三传、引文逐字可回指；**条数由该建器实算，文档不写死**。
  《毕法赋》在此**只供逐字课例**，其**吉凶诀义仍未落地**（见上「定位」）——
  抽取的是课式结构，不是断语。读数口径见 `scripts/evaluate.py`：**机械一致率**，
  并**按引擎自标 `verified` 分桶披露**（涉害等异说门单列），非对齐分、非预测率。

## 通道覆盖

本地 CLI、通道 A 网页（GitHub Pages + Pyodide，零凭证）、通道 B 云端 Actions 三路皆通，
**八科全挂载**；科 × 通道的**权威矩阵见仓库根 `llms.txt`「能力矩阵」，本文件只引用不复制**。
网页深链 `?d=liuren&q=…&dt=…&auto=1`，触发与取回报告见 `docs/AI-SOP.md`。

口径红线（不因挂载而变）：**大六壬是骨架科——只输出机械结构标签，无吉凶断语。**

- 结构标签三层：① 门类/课体（`jiuzongmen`）；② **日辰关系**（`analyze.py::_richen`，判据集与诀文
  取 `data/verdicts.json#richen`——《六壬大全》卷三「日辰」歌逐字，10 条：日上生干/日上克干/
  干生上神/干克上神/日上生辰/辰上生干/日上克辰/辰上克干/日辰俱受生/日辰俱受克）；
  ③ 课目（`kemu.py::IMPLEMENTED`）。三层一律只报结构命中 + 书源引文，不判吉凶。
  日辰关系的每条判据与门类/天将引文同受 `[1d] 引文逐字门` 约束，并在 720 课式全枚举中
  须至少触发一次（零触发即判败）。

## 命令

```bash
python scripts/chart.py --datetime "2024-02-20 10:30" --question "占求财" [-o out.json]
python scripts/analyze.py chart.json [-o analyze.json]
python scripts/narrate.py analyze.json
python scripts/render.py analyze.json -o report.md
python dev_tools/check.py        # 质量门（九宗门全枚举 + [1c] 课目引文可回指 + [1d] 引文逐字门；条数均实算）
python dev_tools/golden.py verify
```
