# 结论库索引（易 / Yi）

> 固定输入的引擎结论快照：**只存渲染报告，不存 JSON**（体积小、diff 可读；JSON 按各条命令随时重跑）。
> 服务两类读者：人审查（输入／命令／哈希齐全）与语言模型取用（命中即引用，未命中不得套用）。
> 共 4 条；未收录的输入请本地跑引擎，或按 [`outreach/WEB-AI-PROMPT.md`](../outreach/WEB-AI-PROMPT.md) 的三条路径处理。

| ID | 学科 | 输入 | 结论报告 | sha256（引擎输出） |
|---|---|---|---|---|
| `ly-coin-2026-01-15` | 六爻 | mode=coin，question=「示例：某合作项目下月能否顺利推进」，datetime=2026-01-15 10:30，seed=42 | [`ly-coin-2026-01-15.md`](ly-coin-2026-01-15.md) | `cd3ca18333d5d6dc` |
| `ly-time-2026-03-18` | 六爻 | mode=time，question=「示例：某岗位竞聘在本季度是否值得投入」，datetime=2026-03-18 14:00 | [`ly-time-2026-03-18.md`](ly-time-2026-03-18.md) | `7050224e0d66a89b` |
| `bz-1990-05-20-male` | 八字 | question=「示例：命局结构说明」，datetime=1990-05-20 10:30，gender=男 | [`bz-1990-05-20-male.md`](bz-1990-05-20-male.md) | `aec7f5e3c893bfe6` |
| `bz-1985-11-03-female` | 八字 | question=「示例：命局结构说明」，datetime=1985-11-03 08:15，gender=女 | [`bz-1985-11-03-female.md`](bz-1985-11-03-female.md) | `6e1ca5806f784e4c` |

## 覆盖范围（重要）

- 只覆盖上表 4 条**固定输入**，不是「任意时间、任意问题都能查」。
- 新增一条：在 `outreach/build_outreach.py` 的 `CONCL_CASES` 加一行，跑 `--write`，同批登记 `CHANGELOG`。
- 产物由 `--check` 逐字节复验；引擎或输入漂移即判红。

## 口径

所有结论都是引擎输出的原文快照；分数是**古籍案例对齐分**，不是现实命中率，现实侧样本为 0。
