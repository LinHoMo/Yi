# 六爻分析引擎精准度差距报告 (Precision Gap Report)

本文档识别 `classical_analysis.py` 与 `najia_rules.md` 第10-19节（新增经典规则）之间的精准度差距。
每个差距按影响优先级排序，包含：经典原文 → 代码现状 → 影响评估 → 修复建议。

---

## Gap 1: 回头合化（Return Harmony / Return Clash）未识别

### 经典规则
《黄金策》《卜筮正宗》云：
> "动爻变爻，有回头合者，谓之合住，事难解；有回头克者，谓之大凶。"

回头合：动爻变卦之地支与本卦动爻地支成六合（子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合），合住则事态胶着难解。
回头克：动爻被变爻五行所克（如寅木变申金），大凶之象。

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_advance_retreat()`（行1270-1350）

```python
if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
    advance_type = "化进"
elif RETREAT_PAIRS.get(orig_branch) == chg_branch:
    advance_type = "化退"
else:
    advance_type = "无进退"  # ← 这里漏掉了回头合/回头克！
```

当动爻变身既非进退时，代码将其归为"无进退"，完全忽略了六合（回头合）和五行相克（回头克）的判断。

### 影响
- **漏报凶象**：回头克被标为"不涉及进退神"，用户无法得知凶险
- **漏报合象**：回头合导致的"合住难解"完全缺失
- **类型分类错误**：所有非进退的变化都被打成同一类，失去细分

### 修复建议
```python
# 在 else 块中添加：
else:
    if is_ba_zu_he(orig_branch, chg_branch):
        advance_type = "回头合"
        desc = f"...合住，事态胶着"
    elif KE_CYCLE.get(BRANCH_ELEMENTS[chg_branch]) == BRANCH_ELEMENTS[orig_branch]:
        advance_type = "回头克"
        desc = f"...回头克，大凶之象"
    elif KE_CYCLE.get(BRANCH_ELEMENTS[orig_branch]) == BRANCH_ELEMENTS[chg_branch]:
        advance_type = "回头生"  # 回头生为吉
        desc = f"...回头生，有救济"
    elif SHENG_CYCLE.get(BRANCH_ELEMENTS[chg_branch]) == BRANCH_ELEMENTS[orig_branch]:
        advance_type = "化泄"  # 变爻泄本爻之气
        desc = f"...化泄，力量消散"
    else:
        advance_type = "无进退"
```

---

## Gap 2: 绝处逢生（Life at Dead End）条件缺失

### 经典规则
《卜筮正宗》云：
> "用神绝于日辰，若得原神发动来生，谓之绝处逢生，凶中反吉。"

绝处逢生的核心条件：
1. 用神在日辰处逢绝地（十二长生中"绝"位）
2. 原神（生用神之爻）发动来生
3. 或月建/日辰之原神生扶用神

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_twelve_growth()`（行1357-1464）

```python
is_weak_stage = stage in ("死", "墓", "绝")
```

代码只将"绝"标记为弱象，但不检查原神是否来生。整个引擎缺乏"原神→用神"的主动关系追踪。

### 影响
- **凶卦误判为吉**：绝处逢生的卦被判为大凶，错过反转信号
- **缺乏关键救援分析**：当用神绝地时，完全依赖十神旺衰机械判断，未结合原神动态
- **丢失经典精要**：绝处逢生是六爻最经典的"反转"格局之一

### 修复建议
新增函数 `analyze_desperate_relief()`：
```python
def analyze_desperate_relief(result):
    # 遍历所有在绝地/死地的爻
    # 检查是否有生扶它的原神（五行相生关系）在动
    # 若原神发动且旺相，标记为"绝处逢生"
    # 若原神休囚/空破，标记为"绝地无救"
```

---

## Gap 3: 随官入墓（Following Officer into Tomb）未实现

### 经典规则
《卜筮正宗》"随官入墓"歌诀：
> "随官入墓最凶凶，世用临之祸不轻。官鬼入墓身难保，病人入墓必归冥。"

随官入墓四种情形：
1. 世爻/用神与官鬼同墓（地支同属四墓之一）
2. 官鬼动而化墓，世/用亦值此墓
3. 世/用临墓库地支又临官鬼
4. 官鬼入墓于日/月，世/用也被牵入

### 代码现状
**文件**: `classical_analysis.py`
**函数**: 无对应函数

代码仅有 `TOMB_MAP` 常量（行190-196），在几个分析段中检查"入墓"状态，但：
- 从未识别"官鬼入墓"的专属格局
- 从未检查"世/用随官入墓"的凶象
- 没有将"官鬼"和"墓库"三者联动判断的逻辑

### 影响
- **重大凶象漏报**：占病遇随官入墓是极凶之象，代码只简单标记"墓"状态
- **无法区分**：官鬼入墓 vs 财爻入墓 vs 世爻入墓，吉凶完全不同
- **丧失专业深度**：这是《卜筮正宗》专门论述的格局，完全缺失影响专业性

### 修复建议
新增 `analyze_officer_tomb()` 函数：
```python
def analyze_officer_tomb(result):
    # 1. 找出卦中官鬼爻及其五行对应墓库
    # 2. 检查世爻/用神是否同临此墓（随官入墓）
    # 3. 检查官鬼动而化墓的情形
    # 4. 检查日/月官鬼入墓情况
    # 等级：官鬼入墓 < 随官入墓 < 随官入墓+世用临之
```

---

## Gap 4: 三刑（Three Punishments）检验不全——缺"三刑会局"定量

### 经典规则
《卜筮正宗》云：
> "三刑会合灾尤重，单见之中亦不良。"

三刑成立的条件分两类：
- **循环三刑**（无恩之刑寅巳申、恃势之刑丑戌未）：三字全见方为刑成，仅见二字视为"待刑"，逢月日补齐方成刑
- **互刑**（无礼之刑子卯）：两字相见即成刑
- **自刑**（辰午酉亥）：同一地支两见以上

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_three_punishments()`，常量 `THREE_PUNISHMENTS`（行199-204）

```python
"无恩之刑": [("寅", "巳"), ("巳", "申"), ("申", "寅")],
```

代码将三个循环刑拆成三对独立检查，任何一对出现立即上报"无恩之刑成立"。这意味着：
- 仅见寅巳（缺申）→ 仍判为无恩之刑
- 但经典法则：三字不全不成刑，单见只论"刑伤之象"而非完整"三刑"

### 影响
- **刑象过度报告**：寅巳相见但缺申时，判为"无恩之刑成立"过于严厉
- **缺少"待刑→应期"判断**：三字缺一时，应标为"待年月补齐方成刑"并给出应期
- **轻重不分**：完整三刑 vs 半刑的吉凶程度不同

### 修复建议
```python
# 区分完整三刑和待刑
def _check_punishment_complete(p_type, present_branches):
    if p_type == "无礼之刑":
        return len(present_branches) == 2  # 子卯相见即成
    elif p_type in ("无恩之刑", "恃势之刑"):
        required = set(["寅", "巳", "申"]) if p_type == "无恩之刑" else set(["丑", "戌", "未"])
        present = set(present_branches)
        if required.issubset(present):
            return "完整三刑"  # 极凶
        elif len(present) == 2:
            missing = required - present
            return f"待刑(缺{missing})"  # 待应期补齐
    return "无刑"
```

---

## Gap 5: 日辰/月建与用神合化无特殊效应报出

### 经典规则
《黄金策》《卜筮正宗》云：
> "用神与月建作合，谓之月合，事必成就；用神与日辰作合，谓之日合，切近有力。"

用神与月建/日辰之六合效应分级：
- 月建合用神：整个月内都有力（"事必成就"）
- 日辰合用神：当下切近有力（"切近得力"）
- 月建合用神且日辰合用神：大吉之极

### 代码现状
**文件**: `classical_analysis.py`
**函数分散**: 仅在 `analyze_hidden_spirits()` 和 `_evaluate_hidden_spirit_emergence()` 中检查了日/月与伏神的五行生克关系，但从未检查日/月用神是否形成**六合**关系。

六合和五行相生不同：
- 五行相生：木生火、火生土
- 六合：子丑合（水土合化土）、寅亥合（木水合化木）——不论五行生克，专论"合"的牵绊效应

### 的影响
- **关键效应漏报**：日/月合用神是六爻中"当下有力"的标志性信号，完全遗漏
- **牵绊效应缺失**：合意味着牵绊、停留、难动——与"生扶"的纯吉意义不同
- **断语偏差**：用户无法得知"月日合用神"这一强有效信号

### 修复建议
在 `enhance_reading()` 主函数中添加新分析段：
```python
def analyze_day_month_bonding(result):
    # 获取用神地支
    # 用神六合日辰 → "用神合日，事切近而成"
    # 用神六合月建 → "用神合月，事可成就"
    # 用神既合日又合月 → "月日同合用神，大吉"
    # 忌神合月日 → "忌神合月日，牵延难解"
```

---

## Gap 6: 六破（Six Breaks）完全缺失

### 经典规则
《卜筮正宗》论六破：
> "子酉破、午卯破、巳申破、寅亥破、辰丑破、戌未破。六破者，谓冲中有破，破中藏冲也，其力次于六冲。"

六破十二支对：子酉、午卯、巳申、寅亥、辰丑、戌未

注意：巳申既是六合又是六破，寅亥既是六合又是六破——称为"合中带破"，恩中有怨。

### 代码现状
**文件**: `classical_analysis.py`
**文件**: `liuyao_engine.py`
**现状**: 完全不存在六破的任何代码、常量、分析函数

仅有 `CHONG_PAIRS`（六冲对，行149-152）无 `BREAK_PAIRS`（六破对）。

### 影响
- **次级关系完全丢失**：六破效应虽次于六冲，但仍是有效的克害关系
- **合中带破漏报**：寅亥合+破、巳申合+破的微妙意义完全丧失
- **断卦精度下降**：遇到子酉、辰丑等关系时完全无法识别

### 修复建议
```python
# 新增常量
BREAK_PAIRS = [
    ("子", "酉"), ("午", "卯"), ("巳", "申"),
    ("寅", "亥"), ("辰", "丑"), ("戌", "未"),
]

# 新增分析函数
def analyze_six_breaks(result):
    # 检查各爻之间、爻与月日之间的六破关系
    # 特别标注"合中带破"的组合
    # 判断力量等级：破中带冲 > 纯破中带合 > 纯破
```

---

## Gap 7: 游魂归魂卦（Wandering/Returning Soul Hexagrams）无特殊断法

### 经典规则
《卜筮正宗》云：
> "游魂行无定，归魂回故乡。"
> "游魂卦主在外、不安、忧疑、反复。"
> "归魂卦主在内、有归、安定、终有所归。"

特殊断法：
- 游魂卦占出行：心不定、行无方、四处飘荡
- 游魂卦占居家：不安于室、迁居在即
- 归魂卦占出行：归期可定、终有所返
- 归魂卦占用忧：忧虑有解、心有归属

### 代码现状
**文件**: `classical_analysis.py`
**现状**: 完全没有游魂/归魂卦的特殊判读功能

`liuyao_engine.py` 中 `PALACE_LOOKUP` 确实存储了 "游魂"/"归魂" 世代信息，`EIGHT_PALACES` 中也有，但 `classical_analysis.py` 从未引用此数据进行断卦。

### 的影响
- **卦类特质完全丧失**：同为六世卦，游魂/归魂的析义与纯卦截然不同
- **出行断卦失效**：游魂归魂是出行类断卦的最重要信号之一
- **失经典要义**：这是八宫卦变系统专门设计的信息，被完全浪费

### 修复建议
```python
def analyze_wandering_returning_soul(result):
    palace = hex_info.get("palace", "")
    hex_name = hex_info.get("name", "")
    generation = PALACE_LOOKUP.get(hex_name, (None, None))[1]
    
    if generation == "游魂":
        return {
            "soul_type": "游魂",
            "meaning": "游魂行无定，事在外、忧疑、不安",
            "travel": "心不定、行无方",
            "residence": "不安于室"
        }
    elif generation == "归魂":
        return {
            "soul_type": "归魂", 
            "meaning": "归魂回故乡，事在内、有归、安定",
            "travel": "归期可定、终有所返"
        }
```

---

## Gap 8: 暗动力量层级不足——缺"休囚暗动=日破"的判断

### 经典规则
《增删卜易》云：
> "旺相之爻遇日冲，谓之暗动，其力与动爻相类。休囚遇冲，虽有暗动之意，其力甚微。若月内休囚又逢日冲，谓之日破，其爻无用。"

力量层级：
| 状态 | 力量比 | 性质 |
|------|--------|------|
| 旺相暗动 | ~70%明动 | 有力量，当月内有效 |
| 休囚暗动 | ~30%明动 | 力微，短暂 |
| 日破（月休囚+日冲） | 0% | 彻底破坏，不可用 |

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_hidden_movement()`（行862-952）

```python
overall = _combined_strength(elem, month_element, day_element)
if is_empty and day_branch:
    line_type = "冲空则实"
else:
    line_type = "暗动"  # ← 不论旺休，一律标为"暗动"
```

问题：所有被日冲且非旬空的静爻都被标记为"暗动"，但：
- 休囚被冲其实是"日破"而非"暗动"
- 代码未区分"旺相暗动"与"休囚暗动"的力量差异

### 影响
- **日破误判为暗动**：月休囚逢日冲之爻本应无用，代码却标为有动象
- **力量评估粗糙**：70% vs 30% vs 0% 三个层级被合并为一
- **决策误导**：用户可能误以为休囚暗动之爻仍有作为

### 修复建议
```python
if overall in ("旺", "相"):
    line_type = "暗动（旺相，七分布动）"
elif overall in ("中和",):
    line_type = "暗动（中和，三五分布动）"
else:  # "偏弱" or "衰"
    line_type = "日破（月休囚逢冲，此爻无用）"
    # 日破之爻叠加其他减益：不再有暗动效力
```

---

## Gap 9: 三合局——"破局"条件未检验

### 经典规则
《卜筮正宗》云：
> "三合局固喜齐全，然若有冲其中一字，则局破矣。"

三合局成立的三个条件：
1. 三字全现于卦中（或两字动+月日一字补）
2. 无一字被冲
3. 主动爻至少两个发动

三合局破的条件：
- 合局中有一字被日/月/动爻所冲 → 局破
- 合局中有一字入墓/逢绝 → 局力大减

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_triple_combo()`（行1099-1263）

代码只检查三合局**成立**条件，完全不检查**破局**条件：
```python
# 检查是否存在三合局...
# 但没有检查：
# - 合局中某字是否被日冲/月冲
# - 合局中某字是否入墓
# - 合局是否被破坏
```

### 影响
- **伪三合不破**：实际已破的三合局被报告为"完整"
- **合中带冲漏报**：三合中一字被冲，合力大减，代码未提示
- **错误的力量增强报告**：用户可能误信三合局力量已发动

### 修复建议
在 `analyze_triple_combo()` 中增加破局检查：
```python
# 在确认三合局成立后，检查破局条件
broken_by_day = any(is_ba_zu_chong(b, day_branch) for b in combo_branches_in_hex)
broken_by_month = any(is_ba_zu_chong(b, month_branch) for b in combo_branches_in_hex)
tomb_count = sum(1 for b in combo_branches_in_hex if b == TOMB_MAP.get(combo_element))

if broken_by_day or broken_by_month:
    completeness = "合局逢冲，局破"
elif tomb_count > 0:
    completeness = "合局入墓，局力不显"
else:
    completeness = "完整三合"
```

---

## Gap 10: 进退神量化粗糙——未纳入旺衰修正与数值评分

### 经典规则
《增删卜易》云：
> "进神者，木进寅卯、火进巳午...退神者，木退丑子、火退辰卯..."
> "然化进须看旺衰，旺进有力，休囚虽进而力微；化退亦论休囚，退而遇冲更凶。"

进退神的实际效力受四大因素调制：
1. **本爻在月建日辰的旺衰**：旺进有力，休进力弱
2. **变爻在月建日辰的旺衰**：变爻旺则力量传导强
3. **进退爻是否日冲/月冲**：逢冲则失衡
4. **进退原神是否生扶**：原神发动可增强

### 代码现状
**文件**: `classical_analysis.py`
**函数**: `analyze_advance_retreat()`（行1270-1350）

```python
if ADVANCE_PAIRS.get(orig_branch) == chg_branch:
    advance_type = "化进"
    desc = f"...化进神，力量递增，事态向前发展顺利"
# ← 无论旺休，描述完全相同
```

不区分：
- 旺相本爻化进（vs 休囚本爻化进）
- 变爻旺（vs 变爻休囚）
- 进退逢冲

### 影响
- **吉凶程度失准**：旺进应报"大吉顺遂"，休进应报"进而力微"
- **进退逢冲漏报**：化进逢冲是"进中受阻"的特定断语，完全无法报出
- **力量量化为空**：说明前进但无法量化前进了多少

### 修复建议
```python
def analyze_advance_retreat_v2(result):
    orig_strength = element_strength_in_month(orig_elem, month_elem)
    orig_day_strength = element_strength_in_month(orig_elem, day_elem)
    chg_strength = element_strength_in_month(chg_elem, month_elem)
    
    # 化进评分 +3 起评
    # 旺相 +2，中和 +1，休囚 -1
    # 变爻旺 +1，变爻囚 -1
    # 逢冲 -2
    score = 3  # 化进基本分
    if orig_strength in ("旺", "相"): score += 2
    elif orig_strength in ("囚", "死"): score -= 1
    if chg_strength in ("旺", "相"): score += 1
    if is_ba_zu_chong(orig_branch, day_branch) or is_ba_zu_chong(orig_branch, month_branch):
        score -= 2  # 进退逢冲，力量受损
    
    # 根据总分区间给出"大吉/吉/平/微进"等分级断语
```

---

## 汇总表

| # | 差距 | 影响 | 复杂度 | 影响卦类 |
|---|------|------|--------|---------|
| 1 | 回头合化未识别 | 严重（漏报吉凶） | 低 | 所有动爻卦 |
| 2 | 绝处逢生未实现 | 严重（漏报反转） | 中 | 用神绝地之卦 |
| 3 | 随官入墓未实现 | 严重（漏报大凶） | 中 | 占病/占讼 |
| 4 | 三刑定量不全 | 中度 | 低 | 多出现三刑关系 |
| 5 | 日月合用神未报 | 中度 | 低 | 半数以上起卦 |
| 6 | 六破完全缺失 | 严重 | 低 | 涉及破关系 |
| 7 | 游魂归魂无断法 | 中高度 | 低 | 每宫第7/8卦 |
| 8 | 日破误判为暗动 | 中度 | 低 | 所有静冲卦 |
| 9 | 三合破局未检验 | 中度 | 低 | 三合局卦 |
| 10 | 进退神量化粗糙 | 中度 | 中 | 所有化进退 |

**建议优先级**：Gap 1 → Gap 2 → Gap 3 → Gap 7 → Gap 5（五高），其次 Gap 6 → Gap 4 → Gap 8 → Gap 9 → Gap 10。
