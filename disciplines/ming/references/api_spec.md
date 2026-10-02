# 命科 API

四段契约与 `docs/CONTRACT.md` 一致。输出机械因子与推演标签，**无命运断言**。

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

不产出命运断言；从格仅 tentative；起运岁标注 approximate。



