# Yi DSH 插件（dsh-yi-divination）

DeepSeek Harness（DSH）插件：**六爻纳甲与八字四柱的确定性排盘与解读**。
内置 Python 引擎，装了即用，无需 clone 仓库或手敲命令。

> **版本锚定**：本 Release 的 tag 与 `dsh-plugin/package.json` 的 `version` 由
> `.github/workflows/release.yml` 对账，不一致即判红；tgz 由该流程现场
> `build → selftest → check → pack` 生成，`prepack` 保证 `engine/`、`skills/`、`src/` 不缺件。
> **能力口径以仓库 [`CAPABILITY.md`](https://github.com/LinHoMo/Yi/blob/main/CAPABILITY.md) 为准**，
> 每个读数只对声明时的 git revision 成立。

## 这是什么

- **四个工具**：`yi_liuyao`（起卦·装卦·纳甲·世应·应期）、`yi_bazi`（四柱·十神·旺衰·格局·大运流年）、
  `yi_kb`（判据知识库检索）、`yi_report`（单文件 HTML/MD 排盘报告）。
- **机械排盘归代码**：起局、装卦、判旺衰、算应期全部由 Python 引擎完成，模型只做解读——同一输入永远同一输出。
- **判据随包可查**：知识库文档内置，检索即可回指书源。
- **代码产出的结论样例**：仓库 [`examples/`](https://github.com/LinHoMo/Yi/tree/main/examples) 下三份
  固定输入实跑生成的完整报告（六爻纳甲、六爻时间起卦、八字命局）；网页端 AI 可读
  [`llms.txt`](https://raw.githubusercontent.com/LinHoMo/Yi/main/llms.txt)、
  [`KNOWLEDGE.md`](https://raw.githubusercontent.com/LinHoMo/Yi/main/KNOWLEDGE.md)
  与[判据索引离线镜像](https://linhomo.github.io/Yi/kb/INDEX.html)。

## 安装 / 卸载

```bash
dsh plugin --profile <你的profile> install ./dsh-yi-divination-<版本>.tgz
dsh preset --profile <你的profile> apply yi-divination   # 可选
dsh plugin --profile <你的profile> remove dsh-yi-divination
```

从源码使用（无需插件）：`python liuyao/scripts/chart.py --mode coin --question "某事如何" --seed 42`；
完整成文报告用两科 `scripts/render.py`。从源码装 DSH 插件前**必须先跑**
`node plugins/scripts/build.mjs` 生成构建产物。通用 skill 安装：
`node outreach/install-skill.mjs --target ~/.claude/skills/yi-divination`。

## 口径诚实声明（请务必读完）

- 本仓库**所有分数都是「古籍案例对齐分」**（引擎输出与古籍案例要点的吻合度，用于回归审计），
  **不是现实命中率**；现实世界命中样本为 **0**，无任何准确率数据。
- **外部集不是独立验证集**：六爻外部集在 181–309 批已用于调参取舍，属**开发集口径**，
  不得称作「未参与调参」或 holdout。
- 主应期 top-1（开发集）：**31.8%（n=44，308 批实测）**，Wilson 95% CI **[20.0, 46.6]**；
  k=1 随机 8.3%，但**低于全池随机 34.1%**（池均值 4.1/12）——样本小、区间宽，不构成判别能力声称。
- 其余分集读数均带集合名、n 与出处，见 `CAPABILITY.md`；n<30 只报逐例红绿，不报率值、不作能力声称。
- 本插件是**象征推演与排盘参考工具，不是预言**；凶象只用「偏向／有…信号／结构上」，
  不用「注定／一定」。医疗、法律、投资、重大决策请以专业意见为准。
- 本包**不含**案例库（AGENTS.md §一.2 铁律二：案例库与解读物理隔离），断卦不存在「背案例」通道。

## 已知限制

- 需要 DSH 自带 Python 运行时（3.12）或系统 Python 3.10+；Node ≥22 由 DSH 提供。
- 报告写入系统临时目录（`%TEMP%/yi-reports/` 或 `os.tmpdir()/yi-*`），可手动清理。
- 八字出生时间按输入的本地钟表时直接排盘，不做时区换算；`longitude` 只做真太阳时经度校正。
- 现实占断反馈在册 0 条；本插件没有任何现实命中率数据。

## 源码与治理

引擎源码与全部质量门见 https://github.com/LinHoMo/Yi · 批次流水见两科 `docs/CHANGELOG.md` · MIT License
