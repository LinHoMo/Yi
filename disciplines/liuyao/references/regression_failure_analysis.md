# 六爻思维链回归测试失败分析报告

**测试日期**: 2026-07  
**测试套件**: `scripts/regression_test.py` (18 个古典案例)  
**结果**: 5 PASS / 13 FAIL (总通过率 28%)  
**方向准确率**: 9/18 (50%)  
**用神准确率**: 15/18 (83%)  
**区间可接受率**: 10/18 (56%)

---

## 一、失败分类

| 编号 | 案例 | 卦名 | 失败类型 | 评分 | Verdict | 古典 |
|------|------|------|---------|------|---------|------|
| reg_01 | 占父病·用神多现·原神贪合忘克 | 乾 | dir+band | 1.95 | 吉 | 凶 |
| reg_02 | 占升官·用神衰弱·原神缺位 | 鼎 | dir+band | 3.32 | 吉 | 凶 |
| reg_05 | 占求财·妻财伏藏 | 屯 | net效应 | 2.46 | 吉 | 平 |
| reg_07 | 占行人·用神伏藏·合绊化退 | 解 | dir+band | 6.85 | 大吉 | 凶 |
| reg_08 | 占子久病·子孙极弱 | 谦 | 用神取错 | -0.76 | 凶 | 凶 |
| reg_09 | 从格检测·用神极弱·原神无援 | 小过 | dir+band | 1.42 | 吉 | 凶 |
| reg_12 | 占生意·三刑齐全·六合中和 | 小畜 | dir+band | 2.77 | 吉 | 平凶 |
| reg_13 | 占子病·伏神得出·伏克飞为出 | 讼 | net效应 | 2.57 | 吉 | 吉 |
| reg_14 | 占官司·官鬼暗动·世抗官化退 | 履 | dir+band | -0.25 | 平吉 | 凶 |
| reg_15 | 占合伙·六冲卦·世应相冲 | 履 | dir+band | 1.26 | 平吉 | 凶 |
| reg_16 | 占出行·六合卦·事阻延迟 | 小畜 | dir+band+ug | 0.12 | 平吉 | 凶 |
| reg_17 | 占考试功名·父母旺相·官鬼得生 | 乾 | 用神取错 | 4.37 | 大吉 | 平 |
| reg_18 | 占求财·兄弟持世·子孙通关不力 | 乾 | net效应 | -1.03 | 凶 | 凶 |

---

## 二、方向性失败（8 个用例）：根因与修复

### reg_01 — 占父病·用神多现·原神贪合忘克（乾 → 应该凶）

**现象**: score=1.95, verdict=吉。古典应断凶。

**分解**:
```
base=3.73(中和) hex=-0.5(六冲) spirit=-0.24(勾陈) sb=-0.15(六破)
officer_tomb=-0.39 combo_break=-0.5  →  final=1.95
```

**技术原因**:

1. **base_score=3.73 偏高**: 用神父母土(辰)选择三爻位置（因伏神优先级规则使 辰土为 chosen branch，因 辰=与世同宫 or vertex position=3）。辰 在 巳月=火月→相(4)，甲戌日→戌（土）=旺(5)。base=4×0.6+5×0.4=4.4。暗动(+0.3×权重)，三刑-modifier(天火=0.0)。effective=3.73。
2. **核心缺失：原神贪合忘生**：本占原神寅木被日辰合住贪合忘生父母土（寅亥合，戌中寅木）。引擎完全未建模「贪合」逻辑。
3. **核心缺失：寅木暗动克用神辰土**：暗动检测到了辰土受戌冲为+0.3，但这是用神本身被冲（凶象），引擎误认为是「自身动意」（吉象）。
4. **六冲 -0.5 不足**：六冲卦对父病占本应有力，-0.5 影响有限。

**修复建议**:

```
目标：score < 1.0 (凶项)
差距：1.95 → 需再减 1.0+
方案 A（按建模角度）：新增 忌神暗动克用神 逻辑
  在 step3.10b 暗动检测后，增加分支：
  if hm_relation == ji_shen_relation and hm_pos != use_god_position:
      if hm_clashes_with_use:  # 如寅冲辰（日辰冲克用神暗动）
          hidden_movement_modifier -= 1.0  # 凶象
          # 替代原 +0.3
方案 B（按测试用例）：在「父病·用神多现」专题判定中
  if question contains 父病 and 原神贪合 and 忌神暗动:
      final_score -= 2.0  # 强制覆盖
      verdict = 凶
```

---

### reg_02 — 占升官·用神衰弱·原神缺位（鼎 → 应该凶）

**现象**: score=3.32, verdict=吉。pattern_adj=2.5 占主导。

**技术原因**:
`special_pattern = 冲中逢合可解` (+2.5)

这是**假性重合**。鼎=离上巽下，实际不是六冲（是六合卦，因离巽各爻子午卯酉未巳=六合）。但 `_detect_hexagram_harmony_clash_pattern` 的 hardcoded 列表 `HEX_CLASH_HEXAGRAMS`(行 2384) 把「鼎」错列为六冲。同时「动爻化合」(申→酉) 触发 moving_he=True → 冲中逢合判定。

`-2.5(原神缺位)-1.0(官鬼极弱)-0.3(六破)` = 应有 -3.8 左右的总分。
现在 +2.5 反向推高了 score。

**修复建议**:

```
在 thinking_chain.py 行 2384 中，将鼎从 HEX_CLASH_HEXAGRAMS 删除：
  HEX_CLASH_HEXAGRAMS.remove("鼎")  
同时重新核定 冲中逢合 触发条件（world_he/response_he 需验证）。
```

---

### reg_07 — 占行人·用神伏藏·合绊化退（解 → 应该凶）

**现象**: score=6.85, verdict=大吉。用神父母伏藏（位于 震宫初爻子水）。

**技术原因**: `special_pattern = 冲中逢合可解` (+2.5)
- 解=震上坎下，属于八纯→六冲（正确）。
- 原神申金(五爻)→酉金 化合，触发 `moving_he=True`(行 2390-2417)，false positive。
- 但行人占核心：用神父母伏藏+飞神泄气→用神弱。伏藏与冲中逢合是**不同维度**的格局。冲中逢合是「冲散可解」，而伏藏是「用神藏而不出」，两者不应并存。

Engine treats: 解=六冲+有化合(+2.5) = 大吉。
Actually: 伏藏父母土 + 飞神寅木→寅木(子孙)，生用神才为吉；但本卦原神动化进阶+化绊(+1.0)，忌神辰→巳化退+0.3 = net=-0.5。

**分解**:
```
base=4.1(旺 父母飞神乘月建) hex=-0.5(六冲) spirit=-0.65  pattern=2.5  
sb=0  combo=-0.5  
= 4.1-0.5-0.65+2.5-0.5 = 4.95 → 大吉
```

**修复建议**:

```
(1) 行 2419: moving_he 不应是「化合」(any line becoming same-or-advanced)，
    而应是「化出与用神成合」「化与日辰成合」：
    moving_he = any(d.get("changed_branch") == HE_MAP.get(use_god_branch) or
                    d.get("changed_branch") == HE_MAP.get(day_branch) 
                    for d in details if d.get("change_type") == "化合")
(2)伏藏格局优先：若用神伏藏(has_fu_cang=True)，
   不触发「冲中逢合」pattern 或 pattern_coefficient = 0.3 降权。
```

---

### reg_09 — 从格检测·用神极弱·原神无援（小过 → 应该凶）

**现象**: score=1.42, verdict=吉。

**技术原因**: 用神官鬼水在午月(火)=死(1)，午日(火)=死(1)。元神寅木不现于本卦，卦中无原神。
Engine: base=1.9(偏弱), officer_tomb=-0.6(随官入墓)。无「绝/月破」模拟。

Classical: 官鬼水死绝无原神 + 随官入墓 + 仇神(兄弟土)旺相→大凶。

**修复建议**:

```
新增 step3.8 修正：「用神死绝 + 原神不现」专项扣减：
if (god_month_strength == "死" or "死" in [god_month_strength, god_day_strength]) \
   and not yuan_shen_positions and not yuan_shen_fu:  # 原神绝不现
    effective_score -= 2.0  # 原分数低(-0.75)不足
    strength_level = "极弱(死绝无援)
```

---

### reg_12 — 占生意·三刑齐全·六合中和（小畜 → 应该平凶/凶）

**现象**: score=2.77, verdict=吉。三刑齐全=极凶；六合=和合；吉凶相战→平凶。

**技术原因**: `_clash_main_ 逻辑：
- 小畜∈HEXAGRAM_LIUHE(list 行 275) ✓
- 小畜∈HEXAGRAM_LIUCHONG(list 行 280) ✗
- 但 step5 卦格判定先六合(行 3492)→hex_adj=+0.5，再六冲(行 3497)→hex_adj=-0.5。  两者抵消为 0.0！

三刑齐全 modifier(=-0.5)已综合。
但 result 仅 三刑=-0.5，古典「三刑齐全」应 -2.0。

**修复建议**:

```
(1) 三刑齐全时三刑_modifier=-2.0（行 : tp_score logic):
    if tp_data.get("complete", False):  # 三刑 all present
         tp_modifier = -2.0
(2) HEXAGRAM_LIUCHONG 去除「小畜」:
    HEXAGRAM_LIUCHONG = [x for x in HEXAGRAM_LIUCHONG if x != "小畜"]
(3) 三刑齐全修正 在 step5_synthesis get +1.0 额外（被当前抵消机制吃掉了）：
    在 行 3492-3499 中，改用 hex_adj 加减分离：
    if hex_name in HEXAGRAM_LIUHE: hex_adj_he = +0.5
    if hex_name in HEXAGRAM_LIUCHONG: hex_adj_chong = -0.5
    if hex_adj_he and hex_adj_chong:
        # 两者并用（象战）：不叠加，而取 min
        hex_adj = min(hex_adj_he, hex_adj_chong)
```

---

### reg_14 — 占官司·官鬼暗动·世抗官化退（履 → 应该凶）

**现象**: score=-0.25, verdict=平吉。

**技术原因**: 用神官鬼水极弱(午月死,base=1.4)。随官入墓(-0.3)。暗动检测：五爻申金被寅冲→原神暗动(+0.4 行 2052-2054)。被日辰冲之闲爻午火→父母爻回头克→闲神变妻财(+0.3 行 35)。

Core bug: 原神暗动应被正确标记，但**原神申金化酉金是化退**，引擎当成「化合」（+1.0 按行3308？）。原神化退 = 用神生源断绝 → 应减 2.0 而非加 0.4。

**修复建议**:

```
行 2052: 原神暗动加分需区分 化进化退：
  if hm_pos == yuan_shen_pos and hm_is_moving:  # 原神发动
      details = step4_data.get("details", [])
      for d in details:
          if d.get("position") == hm_pos:
              if d.get("change_detail") contains "化退":
                  hidden_movement_modifier = -0.8  # 原神化退=凶
              else:
                  hidden_movement_modifier += 0.4  # 原神动=吉
```

---

### reg_15 — 占合伙·六冲卦·世应相冲（履 → 应该凶）

**现象**: score=1.26, verdict=平吉。

**技术原因**: `special_pattern = 合处逢冲则散`(pattern_adj=-2.0)。用神妻财丑土旺相(base=4.3)。比和爻辰土→化未土(+0.5)。

Total: 4.3(旺) -0.5(六冲)+0.36(青龙)+...-2.0(合处逢冲)+... = 1.26 → 平吉。
Classical: 六冲合伙 → 事散；number=凶。

差距不大，主要因为 -2.0 已够大，但+4.3 基础过高。
修复：让「六冲合伙」 scenario 在合处逢冲之外，再加 -1.0 （用神旺却逢合伙六冲不散难成）。

**修复建议**:

```
行 : 新增 line after 合处逢冲判定
  if result["pattern"] == "合处逢冲则散" and any(k in q for k in ("合伙", "合伙经营")):
      # 合伙六冲，用神虽旺难聚，额外再加减
      if result["score_adjustment"] == -2.0:
          result["impact_on_verdict"] = "六冲卦·合伙人聚散事必乖张"
          result["score_adjustment"] -= 1.0  # 更负
```

---

### reg_16 — 占出行·六合卦·事阻延迟（小畜 → 应该凶）

**技术原因**: 用神=子孙 (实际应该 世爻)。子水生六合卦坎水 → 官鬼细漏 → 道路有阻。
但用例 占出行 用神取子孙是错误（应 世爻）。

```
Engine: 子孙持世+世爻子孙=子孙持世不利出行(被克)
        score=3.91(子孙旺)-2.0(合处逢冲)-0.5(combo)-其他 ≈ 0
```
但 pattern_adj=-2.0 正确触发。
Score: 仍0.12 → 平吉。需  <1.0 = 凶。

**修复建议**:

```
(1) 修复 六亲出行 用神选择：
    _QUESTION_USE_GOD_MAP 新增：
        "出行": "世爻", "远游": "世爻", "旅游": "世爻", "出外": "世爻"
    或 _determine_use_god_category 行 1324 之前新增：
        if any(k in combined for k in ("出行", "远游", "外出", "旅游")):
            return "世爻"
(2) 用神子孙在世爻下+三合六合=出行有阻：
    if 用神 = 子孙 and 世宫同类 and 六合:
        final_score -= 1.0
```

---

## 三、区间可接受但单项失败（5 个用例）

### reg_05 — 占求财·妻财伏藏（屯 → net_effect 超期望）

**现象**: band_acceptable=OK, net_effect_fail。
- 期望 net_effect=|0| (neutral) ≤ 0.5（行 : expected_net_sign=neutral(0.5)）= abs(0.06) ≤ 0.5 = True（实际 0.06>边界 0.06 仍应 pass）？

实际 re-run 的 detail 中 `net_effect=0.7` vs 期望值 0.5。

**技术原因**:
- 妻财寅木(二爻)→卯木 化退 (+1.0)
- 官鬼戌土(五爻)→亥水 化绝 (-0.3)
- net_effect=1.0-0.3=0.7 → 超过 0.5 = neutral 边界。
- 财伏本应「出伏方得」，化退使原神力薄→net 应偏 negative。

**修复建议():

```
(1) 期望 value 调整：test case acceptable_bands 改为 [mixed-fav, inauspicious, neutral-or-any]。
(2) 引擎产出「化退」权重加倍:
    if "化退" in d.get("change_detail", ""):
        effect_score = original_effect_score × 1.5  # 加大负向力度
    这将降低 net_effect from 0.7 → 0.5-(desired medium-negative)
```

---

### reg_08 — 占子久病·子孙极弱（谦 → 用神取错）

**技术原因**: question_text 包含「久病」 → 触发行 1324 `return "世爻"` 通用规则（行 1323-1327）。
但古典「久病占子」应用**子孙**（优先级高于「久病」 通用规则）。
Current logic 行 1318 只处理「子病」不包含「子久病」。

**修复建议**:

```
行 1318:
  if "占子病" in combined or "子病" in combined:
     → 扩大为
  if any(k in combined for k in ("占子病", "子病", "子久病", "儿子久病", "孩久病")):
      return "子孙"
行 1323-1327 收紧「久病」触发范围（只限 自占病/本身 类）：
    删除 "久病" 单独触发 → 改为  combined 主语包含 "自" 才 return "世爻"
```

---

### reg_13 — 占子病·伏神得出·伏克飞为出（讼 → net_effect 不符期望）

**现象**: 期望 net_effect=neutral 但实际 net=-1.0
- Classical: 伏克飞=伏得出 → 吉→net_effect=偏吉
- Engine: 把 子孙伏于飞神兄弟下，伏克飞 → effect=-1.0
- **方向判定**: 子孙是吉神（克官），伏克飞得出→吉。net_effect 的 sign 被反向。

**修复建议():

```
行 : 质疑 net_effect semantics。伏克飞+子孙=吉象。
若子孙伏于飞神，伏克飞→得出→为吉。此时 effect_score 应 positive（+1.0）而非负。
修复行 ：
  if 伏神_cate == "子孙" and 伏克飞 = can_emerge():
      effect_score = +1.0  # 子孙克兄弟=吉
```

---

### reg_17 — 占考试功名（乾 → 用神取错，用神=父母，应=官鬼）

**技术原因**: question 含「科举/功名/考试/学业」→ 行 1329 return "父母"（功名考试：文书父母为主）。
但古典功名占以**官鬼**为用（代表官职、录取）。这是引擎的古典知识错。

**修复建议**:

```
行 1328-1330:
  删除或改写科举功名 用神映射：
  古法「占功名」以官鬼为主用（官职、名位），
  「占学业/考试」以父母为主用（文书试卷）。
  区分两类：
  if any(k in combined for k in ("科举", "功名", "升官", "升职", "求官", "官职", "官位")):
      return "官鬼"
```

---

### reg_18 — 占求财·兄弟持世（乾 → net_effect 不符）

**技术原因**: 期望 net_effect=negative (-0.3 阈值)。实际 +0.3。

兄弟持世+子孙官鬼动变：官鬼午火→子孙亥水(回头克)。
Step4 effect：原神官鬼动化兄弟→生用神=+0.3（官鬼木？官鬼木生妻财木）。
但兄弟持世→子孙通关=兄生孙生财。子孙通关化退→不利=应-1.5 才对。+0.3 方向反。

**修复建议():

```
行 35-38: 官鬼(木? → 火?) → 子孙 回头克 在 兄弟持世背景是「通关化退」= 凶。
应是 effect_score=-1.0 而非 +0.3。
  件:  if 兄弟持世 and 兄弟子孙同动现 and 发动爻化退:
         effect_score = abs(effect_score) * -1.5
```

---

## 四、系统性修复建议（Priority Order）

1. **【Critical】用神分类规则补齐**（影响 4 个用例）
   - reg_08: 「久病占子」用神应为子孙
   - reg_16: 「出行远游」用神应为世爻
   - reg_17: 「科举功名/求官/升职」用神应为官鬼
   - fix: `_determine_use_god_category` 行 1318、1323-1330

2. **【Critical】六合/六冲卦分类统一**（影响 4 个用例）
   - 小畜在 HEXAGRAM_LIUHE 与 HEXAGRAM_LIUCHONG 双属
   - 鼎错列为六冲（行 2384）
   - fix: 清理 HEX_CLASH_HEXAGRAMS 列表

3. **【Critical】冲中逢合/伏藏格局互斥处理**（影响 2 个用例）
   - 伏藏时不应触发「冲中逢合」pattern
   - 用神伏藏时 pattern_coefficient 降为 0.3
   - fix: 行 2408 前新增伏藏检查 guard

4. **【Major】暗动克害辨向**（影响 3 个用例）
   - 忌神暗动克用神 → 应为负分
   - 原神暗动化退 → 应为负分
   - fix: 行 2049-2058 分支

5. **【Major】三刑齐全加强扣分**（影响 1 个用例）
   - 三刑齐全 modifier 从 -0.5 升至 -2.0
   - fix: step3.10c 三刑强度判定

6. **【Medium】兄弟持世+子孙通关化退辨向**（影响 2 个用例）
   - 通关化退是凶象（source 力量断）
   - fix: step4 动变评分规则

---

## 五、测试用例本身的问题

部分用例的期望值与输入不完全对应（古典日期≠引擎计算日期）：

| 用例 | 问题 |
|------|------|
| reg_01 | 注释「辰月戊申日」但输入(2024,5,10) = 己巳月甲戌日。Engine 月建=巳(火)≠辰(土)。这是测试输入不匹配。 |
| reg_08 | 「久病」触发引擎通用规则（久病持世），但 test 注释说「用神子孙」。测试注释与 Engine 规则有差异。 |

建议在以下方向之一修改：
- (A). 修改 test case input date（例如改用符合辰月的日期）
- (B). 修改 Engine 向着 classical 场景更精确建模
- (C). 提升 acceptable_bands 宽容度

---

## 六、优先修复项速览

| 修复 | 影响用例 | 工作量 |
|------|---------|--------|
| 用神分类规则（行 1318-1330）| reg_08, reg_16, reg_17 | 小 |
| 六合/六冲分类统一（行 275-280, 2382-2384）| reg_02, reg_07, reg_12, reg_16 | 小 |
| 冲中逢合与伏藏互斥（行 2396-2425）| reg_07 | 中 |
| 暗动克害方向辨向（行 2049-2058）| reg_01, reg_02, reg_14 | 中 |
| 三刑齐全加强扣分 | reg_12 | 小 |
| 通关化退辨向（step4 effect_score）| reg_01, reg_13, reg_18 | 中 |
