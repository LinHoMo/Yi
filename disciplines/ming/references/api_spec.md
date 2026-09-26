# 命科 API（骨架）

四段契约与 `docs/CONTRACT.md` 一致。本轮只暴露机械因子。

## chart

| 参数 | 类型 | 说明 |
|------|------|------|
| `--datetime` | str | 出生公历 `YYYY-MM-DD HH:MM` |
| `--gender` | str | 男/女（仅记录） |
| `--longitude` | float | 可选经度 |
| `-o` | path | chart JSON |

输出：`pillars`（四柱干支/纳音）、`factors`（藏干十神）、`shensha`、`ming_shen_gong`。

## analyze

输入 chart JSON → `chart_summary` + `conclusion{verdicts: [], 说明, 所本}`。无吉凶断语。

## narrate / render

占位正文（明示推演未实现）与因子报告。

## 边界

不实现格局、大运、流年推演；不产出命运断言。
