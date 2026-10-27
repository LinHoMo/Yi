# Yi · 能力声明（CAPABILITY.md）

> **本文件是什么**：对外出示的一页能力边界文书——回答「这套系统做到了什么、量化到什么程度、
> 哪些永远不许说」。每个数字带批次与文件回指；每层声称附复现命令。**版本锚定**：全绿与读数
> 只对声明时的 git revision 成立（AGENTS.md 范围条款），引用本文件请连同 commit 一起引用。
> 生成于第一百九十七批（2026-10-21），此后每次能力面变动须回改本文件（§六.2）。第两百一十四批起
> 本文件关键计数（288/40/23/5/9/33 与各集读数）逐项进入 `liuyao/dev_tools/readout_ledger.py`
> 重放断言——对外文书的数字由机器盯着继续为真，不再只靠回改纪律。第两百二十二批：本文件全部
> 15 条复现命令逐字实跑 15/15 通过（0-1 秒级快为引擎毫秒级使然，快结果亦抽验过产物——不是没跑）。

## T1 确定性排盘与推演 —— **已验证**

四柱/纳甲/装卦/世应/六亲/六神/旬空/月破/六十四卦/干支历换算全部由代码完成，LLM 禁止心算（AGENTS.md §一.1）。
- 六爻：288 例行为指纹（机械层 `4ceef1eed62dafe2`／措辞层 `405bc8e03a6a99e0`（308 批实测，原登记 b716/a46f），自第一百九十三批起
  **含 analyze.conclusion 键集与内容哈希**）；确定性证据面＝**分析链零随机**（step\*/思维链/analyze/
  经典层无随机源，账台逐跑核该计数）＋起卦层带种可复现（`--seed`）；爻序 23 断言 P0 看门狗。
  （原写「三 seed（门 [23]）」系跨科串号——三 seed 属八字门 [23]，第一百七十二…第两百一十六批间
  由第两百一十七批查实更正。）
- 八字：40 例结论级指纹（机械 `fda7482656967518`／措辞 `3512deff79fa1f72`（308 批实测，原登记 2a4c/1a0f））＋5 例机械回归＋九场景评测器校准。
- 复现：`python liuyao/dev_tools/golden.py verify && python bazi/dev_tools/golden.py verify`

## T2 古籍忠实复原 —— **已量化（含上限）**

所有分数是**古籍案例对齐分**（AGENTS.md §一.3 口径诚实），衡量「引擎与书载要点吻合」，不衡量现实。

**六爻**（分母均注 n，未调参集加 ⚗）：

| 读数 | 值 | 出处 | 复现（自仓库根） |
|---|---|---|---|
| tune / holdout 对齐 | 97.9%（n=20）／90.2%（n=12） | 172 批口径 | `python liuyao/scripts/evaluate.py --split tune`（同 `--split holdout`） |
| 外部 ⚗ wikisource 对齐 | **75.8%**（n=50；308 批实测，原登记 62.4）；direction 子集 76.6%（n=31） | README 表 | `python liuyao/scripts/evaluate.py --split wikisource_holdout` |
| 外部 ⚗ zengshan_dz 对齐 | **61.5%**（n=21；308 批实测，原登记 53.4） | 同上 | `python liuyao/scripts/evaluate.py --split zengshan_dz_holdout` |
| 主应期 top-1 ⚗ | **31.8%**／33.3%（308 批实测，原登记 27.3），CI[20.0, 46.6]／[17.2, 54.6]；k=1 随机 8.3% | 181 批→308 批 | `python liuyao/dev_tools/window_report.py` |
| top-3 窗 ⚗ | **61.4%**／57.1%（308 批实测，原登记 52.3／47.6；信息在窗不在点→193 批 `应期窗口` 键） | 181/192/193 批→308 批 | 同上（`window_report.py` 一张表含 k=1..5） |
| 版本冲突上限 | 卦面分歧 0/47、判词分歧 1/37→判词保真天花板 ≈98.6%（等权估计式） | 185 批 | `python liuyao/dev_tools/version_collate.py` |
| 规则边际 | 33 条全扫：无一单点显著（11 条有影响全 p≥0.375、top-1 零不一致）；信号在择支/日月/阶梯三底座 | 182/186 批 | `python liuyao/dev_tools/ablation.py --sweep`（分钟级） |
| 名次键 | 四个预声明重排键全部不胜现行序；#33 排序问题按预注册结案 | 190 批 | `python liuyao/dev_tools/rank_experiment.py` |
| 流派裁决 | **27 项**分歧点：5 照书执行／1 用户裁定冻结／**20 项 open_conflict**／1 项 `settled`（词汇表外，待裁）——分歧表自 248 批起扩容，原登记「7 项／1 open_conflict」少报一个数量级（308 批更正） | 188 批→308 批 `liuyao/data/rules/adjudications.json` | `python liuyao/dev_tools/build_adjudications.py --selftest` |

**八字**：holdout **99.5%**（n=278，308 批实测，原登记 97.6）**由历法与定义维抬起**，判断维单列——
tiaohou 96.2% vs 常数基线 17.0%（配对 b=42 c=0 p<0.001，**表忠实复原坐实**）；
pattern **100.0%（36/36）** vs 常数『定答成格』75.0%（配对 b=9 c=0 **McNemar p=0.004，已显著优于常数**——
187 批登记时是 80.6%／p=0.727「未证明赢过常数」，308 批按实测**翻转**）；
cong_ge 86.7% 但类分布 15/15 退化，且常数『定答从』100.0% **高于**引擎（p=0.500）——
**本维未过「不劣于常数回答」的最低门槛，不可作任何判别声称**；shensha 5 例／dayun 0 例／女命 0 例——证据边界。〔187 批→308 批更正〕
⚠ **tune 集已 100.0% 满分饱和**（60/60，min=max）：按 AGENTS.md §三.4 自引口径，该集**已丧失区分能力**，
只能当回归哨兵，**不得作为能力证据引用**。
复现：`python bazi/scripts/evaluate.py --split holdout`、`python bazi/dev_tools/baselines.py --split holdout`、
`python bazi/scripts/evaluate.py --split external_holdout`、`python bazi/dev_tools/check_dim_lock.py`。

## T3 现实预测能力 —— **不可测，不声称**

没有任何现实结果进入过评测（`prospective` 在册 **0** 条，复现：`python liuyao/dev_tools/prospective.py list`；
现实反馈三通道职责已划界、机件就绪、
按用户决定不真实运行——第一百九十六/一百七十七批）。**本仓任何人（含 LLM）不得把 T2 的任何
数字转述为命中率、预测率或断事能力**。若将来晋升 T3，门槛已写死为规则而非愿望：
预测先封存（哈希链）、口径先冻结（SCORING_RULE sha，复现：`python liuyao/dev_tools/readout_ledger.py --quick`
之「口径sha」行）、判卷只追加、删失显形、
**n≥30 才许出命中率且必带 Wilson CI**（`outcome.MIN_N_FOR_CONCLUSION`）、与随机/频率零模型对照才算「分离」，
与基线的比较须配对检验（190 批预注册流程是模板）。

## 禁止清单（对两科所有输出）

- ❌ 「预测准确率/预测率/断事如神」及任何把对齐分改姓的表述；❌ 命/绝/注定式终极断语；
- ❌ holdout 冒充独立（内部集仅未参与**本轮**调参，同源自证结构见 181-186 批注记）；
- ❌ 医疗/法律/投资场景不给专业意见提示；❌ 引用本文件不附 commit 版本。

## 已知欠账（如实，不掩）

① 六爻自注毕业流（现状第两百零四批）：63 partial 已分诊＝15 验支候选＋35 结案候选＋8 真分歧＋5 噪声；
18 restorable 经双解析器复核＝10 共识＋8 待裁；共识 10 条已生成标准盘形草稿（去重后净 6 案，
`restorable_candidates.json`）——**人工动作已降级为逐条签字**，签署后并入外部集另批走 §四
（189/201/202/204 批沿革）；② ~~八字 golden 未纳入 conclusion
层~~ **系虚构欠账，第一百九十八批查实更正**：八字 `golden.py` 自始以 `conclusion_sha`（整个
conclusion 的规范化哈希）归入机械层覆盖全部结论字段（docstring 明载＋`golden_kit.split_rows`
实核），193/197 批的登记未经实搜即录入——「登记欠账」本身也是须可回指的声称；③ 现实侧永久
悬置除非用户重启（机件保留即为此）；④ 版本冲突率仅《增删》两抄本对过，其余底本未测（185 批边界）。
