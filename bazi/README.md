# 八字 · 四柱机械推演

> 本科只输出 `analyze` 的结构化因子（四柱、藏干、十神、强弱、格局、喜用神、大运 8 步、流年对照）；
> **不产出命运吉凶断语**。运行入口、意图路由、完整能力清单与铁律见同目录 `SKILL.md`。

## 口径（可回溯）

- **强弱**：藏干本/中/余气权重 1.0 / 0.5 / 0.25，叠加得令加权；取扶抑用神
- **格局**：月令本气十神 → 正格名；从格按《滴天髓》分级（真从/假从/从旺/从强/从气/从势），灰区例才留 `tentative` 标注
- **大运**：年干阴阳 × 性别定顺逆；顺行取下一节、逆行取上一节；三日 = 一年
- **十神**：运干/流年干对日主（`relations.ten_god`）
- **流年**：只给干支 × 十神对照，不批吉凶
- **纳音**与**神煞**：2026-09-29 自 `ming_tables` 按"两科共用"拆入 `symbols` / `shensha`（审计 B3）

## 引用文档

| 文件 | 内容 |
|---|---|
| `docs/EVAL-PLAN.md` | 评分口径与维度定义（pillars / tiaohou / cong_ge / pattern 等） |
| `references/api_spec.md` | chart / analyze / narrate / render 四段契约 API |
| `references/bazi_yue_shi_ge.md` | 五虎遁 / 五鼠遁歌诀与引擎表对源 |
| `references/bazi_shishen_terminology.md` | 十神术语古今映射（古籍用字 ↔ 引擎用字） |
| `references/bazi_nayin_shiyi.md` | 纳音释义逐句（书源《命理探源》） |

## 评测

```bash
python scripts/evaluate.py --split tune      # 参与过调参的 30 例
python scripts/evaluate.py --split holdout   # 未参与调参的 246 例
```

2026-10-10 实测：tune 100.0%（n=30，调候满分）｜ holdout 96.2%（n=246，四柱命中 100%）
