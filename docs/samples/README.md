# docs/samples 样例说明

本目录留存仓库的代表性生成样例，用于人工检视排版与叙事口径。所有文件均可由对应脚本重跑生成，**不入库版本比较**。

## 文件清单

| 文件 | 来源 | 说明 |
|------|------|------|
| `财运卦.html` | `disciplines/liuyao/scripts/render.py` | 六爻求财卦 HTML 报告样例 |
| `感情卦_巽之涣.html` | `disciplines/liuyao/scripts/render.py` | 六爻感情卦 HTML 报告样例（巽之涣） |
| `事业卦.html` | `disciplines/liuyao/scripts/render.py` | 六爻事业卦 HTML 报告样例 |
| `screenshot_golden.png` | 手工截图 | 门户黄金截图（对照 build_portal_assets 输出） |
| `DEEP-DIVE-PLAN.html` | `python tools/doc_html.py docs/DEEP-DIVE-PLAN.md` | **各科深度改造方案**单文件 HTML（表格多，便于直接给人看） |
| `NEW-DISCIPLINES.html` | `python tools/doc_html.py docs/NEW-DISCIPLINES.md` | **新门类立项论证**单文件 HTML |

重建规划类文档的 HTML：

```bash
python tools/doc_html.py docs/DEEP-DIVE-PLAN.md --outdir docs/samples
python tools/doc_html.py docs/NEW-DISCIPLINES.md --outdir docs/samples
```

## 口径提醒

- 样例中的断语和吉凶判断仅反映脚本在某次运行时的输出，不代表现实预测命中率。
- 案例均来自古籍（《增删卜易》《卜筮正宗》等），口径为**古籍案例对齐分**校验用。
- 规划文档里的任何分数同样是**古籍案例对齐分**，不是命中率；重大决策以专业意见为准。
