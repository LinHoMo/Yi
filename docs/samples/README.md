# docs/samples 样例说明

本目录留存仓库的代表性生成样例，用于人工检视排版与叙事口径。
**「可由脚本重跑生成」并非对所有文件成立**（2026-10-09 按实物订正，见下表「可否重生成」列）：
`EVAL-PLAN.html` 的源文档 `docs/EVAL-PLAN.md` 已不在库（实测 `test -e` 为假），**不可重生成**；
`screenshot_golden.png` 是手工截图，也非脚本产物。

## 文件清单

| 文件 | 来源 | 可否重生成 | 说明 |
|------|------|------|------|
| `财运卦.html` | `disciplines/liuyao/scripts/render.py` | ✅ | 六爻求财卦 HTML 报告样例 |
| `感情卦_巽之涣.html` | `disciplines/liuyao/scripts/render.py` | ✅ | 六爻感情卦 HTML 报告样例（巽之涣） |
| `事业卦.html` | `disciplines/liuyao/scripts/render.py` | ✅ | 六爻事业卦 HTML 报告样例 |
| `screenshot_golden.png` | 手工截图 | ❌ 非脚本产物 | 门户黄金截图（对照 `disciplines/liuyao/scripts/build_portal_assets.py` 输出） |
| `DEEP-DIVE-PLAN.html` | `python tools/doc_html.py docs/DEEP-DIVE-PLAN.md` | ✅ | **各科深度改造方案**单文件 HTML（表格多，便于直接给人看）；⚠️ 其中分科章节含已删六科，属历史方案 |
| `NEW-DISCIPLINES.html` | `python tools/doc_html.py archive/NEW-DISCIPLINES.md` | ✅（源在 `archive/`，HTML 留在本目录） | **已删六科的立项论证渲染快照——历史立项，不是现行能力面**（见下方「历史立项标注」） |
| `EVAL-PLAN.html` | 由已移除的 `docs/EVAL-PLAN.md` 生成 | ❌ 源文档已不在库 | **评测体系规划**单文件 HTML（存量样例，只读留档） |

> **2026-10-09 订正（本表原第 14 行与仓库相反）**：原写「~~`NEW-DISCIPLINES.html`~~ 已移至 archive/」，
> 实测 `git ls-files docs/samples` **仍含** `docs/samples/NEW-DISCIPLINES.html`，
> 而 `archive/` 下**一个 `.html` 都没有**（`find archive -name "*.html"` 零结果；
> 同目录只有 Markdown 版的 `archive/NEW-DISCIPLINES.md`）。两种修法里选「改措辞使其与实物一致」而不是删文件，理由：
> ① 该路径被两份**已入库**文档回指——`archive/NEW-DISCIPLINES.md:33`（「原始论证快照（HTML，
> 范围收缩前渲染）」）与 `docs/CHANGELOG.md:71`，删文件会在别人所有权的文件里制造死链/断证；
> ② 它是收缩前立项论证的**唯一渲染留档**，属 `AGENTS.md` §三 允许「进 `docs/samples/` 并说明」的样例；
> ③ 删除是不可逆的破坏性动作，本轮只做文档收尾。
>
> **历史立项标注（保留该样例的前提条件）**：`NEW-DISCIPLINES.html` 的内容是**紫微斗数、梅花易数、
> 小六壬、择吉、大六壬、灵棋经六科的立项论证**，该六科已于 2026-10-09 正式从产品能力面移除
> （commit `60b2403`，范围真值源见 `AGENTS.md` §二）。本文件**只作历史立项论证留档**，
> 不得当作路线图、能力清单或可行性结论引用；文中「拟新增」的科均不存在于现树。

重建规划类文档的 HTML：

```bash
python tools/doc_html.py docs/DEEP-DIVE-PLAN.md --outdir docs/samples
python tools/doc_html.py archive/NEW-DISCIPLINES.md --outdir docs/samples  # 已归档文档；HTML 落回本目录（现行能力面为两科，此件仅历史）
```

## 口径提醒

- 样例中的断语和吉凶判断仅反映脚本在某次运行时的输出，不代表现实预测命中率。
- 案例均来自古籍（《增删卜易》《卜筮正宗》等），口径为**古籍案例对齐分**校验用。
- 规划文档里的任何分数同样是**古籍案例对齐分**，不是命中率；重大决策以专业意见为准。
