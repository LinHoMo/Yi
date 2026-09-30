# 紫微斗数 SKILL

**状态：机械排盘已立（非命运断言）。** 输入出生公历时刻 + 性别，输出派盘 JSON、格局、四化、大限表；
**不做**"一生定论"、"某年必如何"、现实预测命中率承诺。

## 意图路由（根 SKILL）

- 问「事业方向 / 财帛格局 / 感情模式 / 一生大势」→ 本层给机械因子与格局骨架；解读归 LLM 转述，禁止宿命断言。
- 问具体一日一事 → 走卜科（六爻/梅花/小六壬/择吉），不越位。

## 能力

| 命令 | 作用 |
|---|---|
| `scripts/chart.py` | 出生公历时刻 → 紫微斗数排盘 JSON（12宫星曜、四化、紫微天府定位） |
| `scripts/analyze.py` | 格局 / 四化入宫 / 大限（阳男阴女顺行） |
| `scripts/narrate.py` | 因子正文（明确非命运断言） |
| `scripts/render.py` | 因子报告 |
| `dev_tools/check.py` | 契约完整性 + 冒烟 + 金标准 |

## 数据契约

```json
{
  "chart": "{discipline:'ziwei', birth:{datetime, gender}, pillars:{year,month,day,hour},
             wuxing_ju, ju_name, ming_gong, ziwei, tianfu,
             palaces:{命宫:{branch, main_stars, aux_stars, sihua}, ...},
             sihua:{禄,权,科,忌}, sihua_list}",
  "analyze": "{chart_summary:{命宫主星, 格局, 四化影响, 大限位序},
               conclusion:{命宫主星, 格局, 四化影响, 方向, 说明, dayun}}"
}
```

## 排盘内核

- 紫微定位：`紫微pos = (局数 + (生日-1)×局数) % 12`
- 天府对宫：`天府pos = (紫微pos + 6) % 12`
- 紫微星系6星逆布、天府星系7星顺布
- 四化由年干定（《紫微斗数全书》通行版口诀）
- 大限：起运年龄 = 五行局数，阳男阴女顺行

## 禁止

- LLM 心算星曜位置、格局名目（铁律一）
- 在 narrate 里编"命定""必如何""绝无可能"类断言
- 把机械推演说成现实预测命中率或"命已算准"
