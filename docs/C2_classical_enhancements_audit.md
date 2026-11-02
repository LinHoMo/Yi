# C2: classical_enhancements.py 收编调研

## 结论：不硬迁

classical_enhancements.py（90KB / 1910 行）**不完全是纯标签**。大部分函数只标象不改分（score_adjustment=0），但有两个函数确实改分，且改的是跨步骤的复杂分数修正，不适合直接塞 registry_v2 的 score_delta（单值、单规则）。

## 改分点清单

### 1. analyze_desperate_relief（绝处逢生）
- 位置：classical_enhancements.py L2048-2073
- 改分：score_modifier = 2.0 / 0.5 / 0.2 / -0.8
- 消费方：step3.py L210 `effective_score += desperate_relief_modifier`
- 语义：用神绝处逢生（月绝得日生、日绝得月生、动而化绝得变爻生等）按强弱加 2.0/0.5/0.2，绝而不逢生减 0.8
- 为何不迁：条件是"绝+逢生"的复合判断（两步以上），不是单谓词；改在 step3 的 effective_score 里，不在 step5 的 final_score 链

### 2. analyze_triple_combo（三合格破局）
- 位置：classical_enhancements.py L1589-1765
- 改分：combo_score_mod（值由 _broken["score_mod"] 决定）
- 消费方：step5.py combo_break_adjustment
- 语义：三合成局被破（冲克/空亡）时按破局程度加减分
- 为何不迁：combo_score_mod 是动态计算的（根据破局类型/程度），不是固定值

### 3. effects.py 里的 score_modifier
- analyze_day_month_bonding / six_breaks / officer_tomb
- 被 step5.py 读进 final_score
- 同样是动态计算，不是固定值

## 纯标签函数（不改分）

以下函数只返回 has_xxx / details / summary，score_adjustment=0：
- analyze_hidden_spirits（伏神）
- analyze_monthly_break（月破）
- analyze_wandering_returning_soul（游魂/归魂）
- analyze_grand_opposition（大反吟）
- analyze_small_opposition（小反吟）
- 等等（约 15+ 个函数）

## 建议

1. **短期**：保持现状。这两个改分函数逻辑复杂、动态计算，不适合 registry_v2 的单值 score_delta。
2. **长期**：如果要迁，需要先把 registry_v2 的 score_delta 扩展成支持动态求值（eval_expr 或 predicate 链），再把绝处逢生/三合格破局的复合谓词拆出来。这是后续优化方向，不在本次 C2 范围内。
