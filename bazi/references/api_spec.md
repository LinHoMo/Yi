# 八字科 API

四段契约与 `SKILL.md` 描述一致。输出机械因子与推演标签，**无命运断言**。

## chart

| 参数 | 类型 | 说明 |
|------|------|------|
| `--datetime` | str | 出生公历 `YYYY-MM-DD HH:MM` |
| `--gender` | str | 男/女（大运顺逆） |
| `--longitude` | float | 可选经度 |
| `-o` | path | chart JSON |

输出：`pillars`（四柱干支/纳音/天干十神）、`factors`（藏干十神）、`shensha`、`ming_shen_gong`、`xunkong`。

## analyze

输入 chart JSON → `chart_summary` + `conclusion`：

- `strength` / `strength_score` / `pattern` / `useful_gods` / `taboo_gods`
- `dayun`：8 步（干支、起止岁、**运干十神**、`approximate`）
- `liunian`：流年干支×十神对照（不批吉凶）
- `verdicts[]`：机械标签，各带 `basis`
- `方向` 恒为空；`应期` 恒为空

## narrate / render

因子正文与报告；结尾保留「非宿命论、重大决策以专业意见为准」。

## 边界

不产出命运断言；从格已按《滴天髓》分级判（真从/假从/从旺/从强/从气/从势，
`from_kind`／`from_type`），只有灰区例保留 `tentative_special` 标注；起运岁标注 approximate。

## 命令示例（自仓库根执行）

| 段 | 命令 |
|---|---|
| chart | `python bazi/scripts/chart.py --datetime "1990-05-20 12:00" --gender 男 -o /tmp/chart.json` |
| analyze | `python bazi/scripts/analyze.py /tmp/chart.json -o /tmp/analyze.json` |
| narrate | `python bazi/scripts/narrate.py /tmp/analyze.json` |
| render | `python bazi/scripts/render.py /tmp/analyze.json` |

不带 `-o` 时各段把结果打到 stdout。回归指纹复现：`python bazi/dev_tools/golden.py verify`。

## 四段职责（判据本体见根 `CONTRACT.md`）

| 段 | 只出 | 不许出 |
|---|---|---|
| chart | 四柱、藏干、纳音、神煞、旬空、命身宫 | 吉凶措辞、格局、喜用 |
| analyze | 强弱、格局、喜忌、大运流年、机械标签 | 成段人话、案例类比 |
| narrate | 因子正文、引文、象层素材、边界声明 | 新结论、内部量化暴露 |
| render | Markdown/HTML 报告骨架与免责提示 | 改写 analyze 的任何键 |

机械结论一律由 Python 产出，LLM 不得心算（AGENTS.md §一.1）；解析失败须如实报「排盘异常」，不得手动替代。

## 数据真源（改文案改这里，不改 py）

- 格局顺逆与引文：`bazi/data/verdicts.json`；调候引文：`bazi/data/tiaohou_quotes.json`
- 十神取象／作用：`bazi/data/liushen_image.json`、`bazi/data/shi_shen_actions.json`
- 纳音性质名：`bazi/data/nayin_quxiang.json`；象层映射与出处：`bazi/data/xiang_layer.json`
- 交付边界声明：`bazi/data/narrative_templates.json`（539 批从 `narrate.py` 原样外置，措辞未改、输出不变）

## 口径

仓内一切分数都是**古籍案例对齐分**（引擎输出与古籍案例要点的吻合度，回归审计用），
不是现实命中率；现实侧样本为零。医疗、法律、投资与重大决策请以专业意见为准。

---

## 相关文档

- 本篇在知识库中的位置与「什么时候读」见 [知识库导览](../../kb/INDEX.md)。
- 同科其他判据：
  - [bazi_shishen_terminology](bazi_shishen_terminology.md)
  - [bazi_nayin_shiyi](bazi_nayin_shiyi.md)
  - [bazi_yue_shi_ge](bazi_yue_shi_ge.md)
  - [bazi_tiaohou](bazi_tiaohou.md)
  - [bazi_liuqin_gongwei](bazi_liuqin_gongwei.md)
  - [bazi_jibing_tizhi](bazi_jibing_tizhi.md)
  - [bazi_qianshi_yanpan](bazi_qianshi_yanpan.md)

> 本文为八字模块接口速查，非预测内容；能力读数与口径以 `CAPABILITY.md` 为准，引用时连同 commit 一起引用。
