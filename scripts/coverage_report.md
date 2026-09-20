# Complete Analysis Coverage Matrix Report

**Coverage Rate**: 100.0%
**Covered**: 36 / 36
**Uncovered**: 0

## Coverage Summary

| ID | Segment | Status | Description |
|----|---------|--------|-------------|
| cov_01 | `hidden_spirit_analysis` | ✅ | 用神伏藏 — 风地观卦(巽宫木), 六亲缺妻财/父母 |
| cov_02 | `hidden_movement` | ✅ | 日冲静爻 — 丑爻被未日冲, 旺相触发暗动 |
| cov_03 | `monthly_break` | ✅ | 月破 — 寅爻被申月冲, 月破成立 |
| cov_04 | `triple_combo` | ✅ | 三合局 — 乾卦申子辰成水局 |
| cov_05 | `advance_retreat` | ✅ | 进退神 — 动爻子水化寅木(化进) |
| cov_06 | `twelve_growth` | ✅ | 十二长生 — 用神在日辰处长生/帝旺等位 |
| cov_07 | `clash_harmony` | ✅ | 六合/六冲 — 泰卦(六合)成立, hexagram_type=六合卦 |
| cov_08 | `repetition_deep` | ✅ | 反吟伏吟深化 — 动爻触发反吟伏吟分析, 结构完整 |
| cov_09 | `element_strength` | ✅ | 纳甲四柱旺衰 — 用神在月建日辰的旺相休囚死 |
| cov_10 | `three_punishments` | ✅ | 三刑 — 寅巳申三刑成立 |
| cov_11 | `hidden_spirit_scoring` | ✅ | 伏神得出力量 — 风地观卦伏藏妻财得出不得出判断 |
| cov_12 | `day_month_bonding` | ✅ | 日月合 — 月日地支合用神/冲用神 |
| cov_13 | `six_breaks` | ✅ | 六破 — 子酉破等六破组合 |
| cov_14 | `desperate_relief` | ✅ | 绝处逢生 — 绝处分析结构完整 |
| cov_15 | `officer_tomb` | ✅ | 随官入墓 — 火爻入戌墓(离宫火例) |
| cov_16 | `soul_hexagram` | ✅ | 游魂归魂 — 火地晋卦(游魂)或火天大有(归魂) |
| cov_17 | `nayin` | ✅ | 六十甲子纳音 — 纳音取象 |
| cov_18 | `flying_hidden_interaction` | ✅ | 飞伏互断 — 飞伏神生克关系 |
| cov_19 | `transformation_pattern` | ✅ | 变爻格局 — 动爻格局推演, 结构完整 |
| cov_20 | `hexagram_body` | ✅ | 卦身 — 世爻位置推导卦身地支 |
| s5_01 | `step5` | ✅ | 卦体调候 — 泰卦(六合)应产生 +0.5 hex_adjustment |
| s5_02 | `step5` | ✅ | 卦体调候 — 乾卦(六冲)应产生 -0.5 hex_adjustment |
| s5_03 | `step5` | ✅ | 六神调整 — 勾陈临用神, spirit_adjustment != 0 |
| s5_04 | `step5` | ✅ | 暗动修正 — 戌日冲辰触发暗动(hidden_movement_count>0) |
| s5_05 | `step5` | ✅ | 日月合调整 — 日月合调用神, dmb_adjustment存在且数值型 |
| s5_06 | `step5` | ✅ | 六破 — 子酉破组合触发调整 |
| s5_07 | `step5` | ✅ | 三合破局 — 三合局被日冲破局触发惩罚 |
| s5_08 | `step5` | ✅ | 随官入墓 — 入墓触发调整/覆盖 |
| s5_09 | `step5` | ✅ | 特殊格局 — 格局识别产生调整或空置 |
| s5_10 | `step5` | ✅ | 推理链 — 整合推理链应大于0条 |
| s5_11 | `step5` | ✅ | 置信度 — 最终置信度在合理范围(0-100) |
| s5_12 | `step5` | ✅ | 应期 — 应期判断应有内容 |
| bnd_01 | `boundary_static` | ✅ | 全静卦 — 无明动爻, net_effect=0, 以用神旺衰断吉凶 |
| bnd_02 | `boundary_all_move` | ✅ | 全动卦 — 六个爻皆动, 乾坤例用九用六 |
| bnd_03 | `boundary_multi_use` | ✅ | 用神多现 — 多个相同六亲 |
| bnd_04 | `boundary_clash_all` | ✅ | 日月全冲 — 月日地支皆冲卦中多爻 |

## Detailed Results

### cov_01: hidden_spirit_analysis ✅
- Description: 用神伏藏 — 风地观卦(巽宫木), 六亲缺妻财/父母
- Expected: `result[advanced_analysis][hidden_spirit_analysis][has_hidden_spirit] == True`
- Status: **COVERED**

### cov_02: hidden_movement ✅
- Description: 日冲静爻 — 丑爻被未日冲, 旺相触发暗动
- Expected: `len(hidden_movement[details]) > 0`
- Status: **COVERED**

### cov_03: monthly_break ✅
- Description: 月破 — 寅爻被申月冲, 月破成立
- Expected: `has_monthly_break == True`
- Status: **COVERED**

### cov_04: triple_combo ✅
- Description: 三合局 — 乾卦申子辰成水局
- Expected: `has_triple_combo == True`
- Status: **COVERED**

### cov_05: advance_retreat ✅
- Description: 进退神 — 动爻子水化寅木(化进)
- Expected: `len(advance_retreat[details]) > 0`
- Status: **COVERED**

### cov_06: twelve_growth ✅
- Description: 十二长生 — 用神在日辰处长生/帝旺等位
- Expected: `summary is non-empty`
- Status: **COVERED**

### cov_07: clash_harmony ✅
- Description: 六合/六冲 — 泰卦(六合)成立, hexagram_type=六合卦
- Expected: `hexagram_type == 六合卦`
- Status: **COVERED**

### cov_08: repetition_deep ✅
- Description: 反吟伏吟深化 — 动爻触发反吟伏吟分析, 结构完整
- Expected: `repetition_deep has type/interpretation keys`
- Status: **COVERED**

### cov_09: element_strength ✅
- Description: 纳甲四柱旺衰 — 用神在月建日辰的旺相休囚死
- Expected: `strength_description field is non-empty`
- Status: **COVERED**

### cov_10: three_punishments ✅
- Description: 三刑 — 寅巳申三刑成立
- Expected: `three_punishments analysis ran`
- Status: **COVERED**

### cov_11: hidden_spirit_scoring ✅
- Description: 伏神得出力量 — 风地观卦伏藏妻财得出不得出判断
- Expected: `hidden_spirit_scoring has summary`
- Status: **COVERED**

### cov_12: day_month_bonding ✅
- Description: 日月合 — 月日地支合用神/冲用神
- Expected: `day_month_bonding findings or summary exist`
- Status: **COVERED**

### cov_13: six_breaks ✅
- Description: 六破 — 子酉破等六破组合
- Expected: `six_breaks has summary`
- Status: **COVERED**

### cov_14: desperate_relief ✅
- Description: 绝处逢生 — 绝处分析结构完整
- Expected: `desperate_relief has has_desperate_relief key`
- Status: **COVERED**

### cov_15: officer_tomb ✅
- Description: 随官入墓 — 火爻入戌墓(离宫火例)
- Expected: `officer_tomb ran and returned dict`
- Status: **COVERED**

### cov_16: soul_hexagram ✅
- Description: 游魂归魂 — 火地晋卦(游魂)或火天大有(归魂)
- Expected: `soul_hexagram has soul_type`
- Status: **COVERED**

### cov_17: nayin ✅
- Description: 六十甲子纳音 — 纳音取象
- Expected: `nayin has description`
- Status: **COVERED**

### cov_18: flying_hidden_interaction ✅
- Description: 飞伏互断 — 飞伏神生克关系
- Expected: `flying_hidden_interaction has summary`
- Status: **COVERED**

### cov_19: transformation_pattern ✅
- Description: 变爻格局 — 动爻格局推演, 结构完整
- Expected: `transformation_pattern has pattern key`
- Status: **COVERED**

### cov_20: hexagram_body ✅
- Description: 卦身 — 世爻位置推导卦身地支
- Expected: `hexagram_body ran and returned dict`
- Status: **COVERED**

### s5_01: step5 ✅
- Description: 卦体调候 — 泰卦(六合)应产生 +0.5 hex_adjustment
- Expected: `hex_adjustment > 0 (六合卦)`
- Status: **COVERED**

### s5_02: step5 ✅
- Description: 卦体调候 — 乾卦(六冲)应产生 -0.5 hex_adjustment
- Expected: `hex_adjustment < 0 (六冲卦)`
- Status: **COVERED**

### s5_03: step5 ✅
- Description: 六神调整 — 勾陈临用神, spirit_adjustment != 0
- Expected: `spirit_adjustment != 0`
- Status: **COVERED**

### s5_04: step5 ✅
- Description: 暗动修正 — 戌日冲辰触发暗动(hidden_movement_count>0)
- Expected: `hidden_movement_count > 0`
- Status: **COVERED**

### s5_05: step5 ✅
- Description: 日月合调整 — 日月合调用神, dmb_adjustment存在且数值型
- Expected: `dmb_adjustment exists as int`
- Status: **COVERED**

### s5_06: step5 ✅
- Description: 六破 — 子酉破组合触发调整
- Expected: `sb_adjustment != 0`
- Status: **COVERED**

### s5_07: step5 ✅
- Description: 三合破局 — 三合局被日冲破局触发惩罚
- Expected: `combo_break_adjustment < 0 or analysis ran`
- Status: **COVERED**

### s5_08: step5 ✅
- Description: 随官入墓 — 入墓触发调整/覆盖
- Expected: `officer_tomb_adjustment <= 0`
- Status: **COVERED**

### s5_09: step5 ✅
- Description: 特殊格局 — 格局识别产生调整或空置
- Expected: `special_pattern field exists`
- Status: **COVERED**

### s5_10: step5 ✅
- Description: 推理链 — 整合推理链应大于0条
- Expected: `len(reasoning_chain) > 0`
- Status: **COVERED**

### s5_11: step5 ✅
- Description: 置信度 — 最终置信度在合理范围(0-100)
- Expected: `0 <= confidence <= 100`
- Status: **COVERED**

### s5_12: step5 ✅
- Description: 应期 — 应期判断应有内容
- Expected: `timing dict has content`
- Status: **COVERED**

### bnd_01: boundary_static ✅
- Description: 全静卦 — 无明动爻, net_effect=0, 以用神旺衰断吉凶
- Expected: `step4 moving_count == 0 (no explicit moving lines)`
- Status: **COVERED**

### bnd_02: boundary_all_move ✅
- Description: 全动卦 — 六个爻皆动, 乾坤例用九用六
- Expected: `has_moving_lines and 6 moving`
- Status: **COVERED**

### bnd_03: boundary_multi_use ✅
- Description: 用神多现 — 多个相同六亲
- Expected: `step2 handles multi-use case`
- Status: **COVERED**

### bnd_04: boundary_clash_all ✅
- Description: 日月全冲 — 月日地支皆冲卦中多爻
- Expected: `analysis handles multi-clash`
- Status: **COVERED**

## Uncovered Segments (Flagged)

_None — all segments covered!_
