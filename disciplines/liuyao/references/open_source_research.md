# 开源六爻项目研究报告

> 调研日期：2026-09-18
> 调研来源：GitHub、GitLab、Gitee、CSDN、公开技术博客
> 目的：提取各项目的算法创新点，识别我们项目的缺失项

---

## 一、调研项目清单

### 1.1 六爻专项项目（按工程完整度排序）

| # | 项目名 | 平台 | 语言 | 类型 | Stars | 关键特性 |
|---|--------|------|------|------|-------|----------|
| A | [baiyanwu/liuyao-skill](https://github.com/baiyanwu/liuyao-skill) | GitHub | Python | CLI + Agent Skill | - | 完整八步装卦、JSON输出、Hermes Agent兼容、可复现种子 |
| B | [bopo/najia](https://github.com/bopo/najia) | GitHub | Python | PIP Package | - | 纳甲六爻排盘、MIT许可、Python包封装 |
| C | [clider0915/divination-skills](https://github.com/clider0915/divination-skills) | GitHub | Python | AI Skill包 | - | 六爻+占星+九型人格+梅花易数、时间起卦+六爻断卦变体 |
| D | [SmallTeddyGames/divination-liuyao](https://github.com/SmallTeddyGames/divination-liuyao) | GitHub | TypeScript | Next.js Web App | - | 现代前端、组件化布局、CI/CD集成 |
| E | [0xfnzero/YiSphere](https://github.com/0xfnzero/YiSphere) | GitHub | Python | AI对话应用 | - | 易经/八字/六爻/择日/AILLM对话/多角色/本地记录 |
| F | [ChesterRa/mingpan](https://github.com/ChesterRa/mingpan) | GitHub | TypeScript | MCP Server | - | MCP协议、多术数(八字/六爻/紫微/奇门)、转盘+用神分析+择日 |
| G | [WHQAQ11/Bu_D](https://github.com/WHQAQ11/Bu_D) | GitHub | - | Web App | - | DeepSeek AI集成、每日一卦、掷币AI解读 |
| H | [deepseek7878/i-ching-divination](https://github.com/deepseek7878/i-ching-divination) | GitHub | - | Web App | - | 64卦完整解读、三语支持(中英繁)、历史记录 |

### 1.2 日历/时间底座项目（历法基础设施）

| # | 项目名 | 平台 | 语言 | 特性 |
|---|--------|------|------|------|
| I | [6tail/lunar-javascript](https://github.com/6tail/lunar-javascript) | GitHub | JavaScript | 50KB核心、节气(定气法)、朔望月、生肖、彭祖百忌、宜忌、星宿、纳音 |
| J | [6tail/tyme4ts](https://github.com/6tail/tyme4ts) | GitHub | TypeScript | lunar升级版、节气第几天、鸿蒙兼容、更优扩展性 |
| K | [6tail/lunar-python](https://github.com/6tail/lunar-python) | GitHub | Python | Python版lunar |
| L | [jiqi1314/cnlunar](https://github.com/jiqi1314/cnlunar) | GitHub | Python | 《钦定协纪辨方书》为核心、香港天文台数据(不用寿星通式)、建除十二神、港式八字月柱算法 |
| M | [sxtwl_cpp](https://gitcode.com/gh_mirrors/sx/sxtwl_cpp) | Gitee | C++/Python绑定 | 寿星天文历C++实现、BC722年起、节气精确到分钟、Python/Java/C#/Lua绑定 |
| N | [isee15/Lunar-Solar-Calendar-Converter](https://github.com/isee15/Lunar-Solar-Calendar-Converter) | GitHub | 多语言(JS/C#/Java/Python等) | 1900-2100转换、农历日期精确 |

### 1.3 泛术数整合项目（含六爻模块）

| # | 项目名 | 平台 | 特性 |
|---|--------|------|------|
| O | [kentang2017/ichingshifa](https://github.com/kentang2017/ichingshifa | GitHub | Python周易筮法、大衍之数、六十四卦、京房易、爻辞 |
| P | [marsguo](https://github.com/marsguo/) | GitHub | 融合六爻+奇门+八字+AI、lunar-javascript/tyme4ts封装 |
| Q | [ml8s/liki](https://github.com/ml8s/liki) | GitHub | Go语言、命理Skill标准版、排盘走天文历算引擎、断语附经典出处、结论可验证 |
| R | [Brhiza/mingyu](https://github.com/Brhiza/mingyu) | GitHub | TypeScript、一站式玄学工具包、公开API/MCP Server |
| S | [tradecatlabs/fatecat](https://github.com/tradecatlabs/fatecat) | GitHub | Python、可重现Bazi/Ziwei计算、证据导向报告 |
| T | [Purple-Star-Astrology](https://github.com/topics/ziwei-doushu) | GitHub | TypeScript、紫微斗数排盘、四化系统、格局知识库、古籍原文 |

### 1.4 AI + 六爻融合项目

| # | 项目名 | 特性 |
|---|--------|------|
| U | [1688.monster](https://1688.monster/) | 第一性原理、真随机起卦、规则+本地大模型双引擎、Hexagram relations、Historical cases |
| V | [YIXIN AI](http://yxai21.com/) | AI解读I Ching、可复现的回溯测试、Relation database + change algorithms |
| W | [Horace-Maxwell/horosa-skill](https://github.com/Horace-Maxwell/horosa-skill) | 硬编码problem-logging协议、Codex/Cursor/Claude/OpenClaw兼容 |

---

## 二、核心算法对比表

| 算法领域 | 本项目 (liu-yao) | baiyanwu/A | clider0915/C | cnlunar/L | sxtwl/M | 备注 |
|----------|-------------------|------------|---------------|-----------|---------|------|
| **起卦方式** | 铜钱/数字/时间/手动 | 铜钱/给定/随机/种子 | 时间起卦(梅花)+纳甲 | N/A | N/A | C项目将梅花时间起卦与六爻纳甲融合 |
| **纳甲装卦** | 完整(口诀+查表) | 完整+内外卦防错 | 基本 | N/A | N/A | A特别强调内外卦地支起点不同(最易犯错处) |
| **八宫归属** | 完整 | 完整(惠栋易汉学) | 简化 | N/A | N/A | A引用惠栋八宫卦次图 |
| **世应定位** | 八宫代数+歌诀 | 同 | 同 | N/A | N/A | 一致 |
| **六亲配置** | 五行生克基准 | 同 | 同 | N/A | N/A | 一致 |
| **六神装配** | 日干起例 | 同 | 同 | N/A | N/A | 一致 |
| **空亡推算** | 旬空 | 旬空自动推算 | 简化 | N/A | N/A | A自动推算 |
| **月破判断** | 月建冲爻 | 月建冲爻 | 基本 | N/A | N/A | — |
| **三合局** | 申子辰等 | 同 | 同 | N/A | N/A | — |
| **三刑** | 完整四类 | 同 | 简化 | N/A | N/A | — |
| **进退神** | 有 | 同 | 简化 | N/A | N/A | — |
| **反吟伏吟** | 有 | 同 | 无 | N/A | N/A | — |
| **伏藏飞伏** | 本宫首卦取伏 | 飞伏神得出/不得出四法 | 简化 | N/A | N/A | A的飞伏得出四法更精细 |
| **暗动量化** | 70%/30%分级 | 同 | 无 | N/A | N/A | — |
| **随官入墓** | 完整 | 同 | 无 | N/A | N/A | — |
| **用神多现** | 五法取舍 | 同 | 简化 | N/A | N/A | — |
| **卦身法** | 有(阳世子起) | 同 | 无 | N/A | N/A | — |
| **六亲持世** | 有(五亲分论) | 同 | 无 | N/A | N/A | — |
| **旺衰评分** | 月建5级+日辰修正+特殊乘数 | 无(LLM解读) | 无 | N/A | N/A | 本项目独特设计 |
| **综合评分** | 加权评分+格局调整+六级结论 | 无 | 无 | N/A | N/A | 本项目独特设计 |
| **日历计算** | 自建(近似) | 自建(近似) | 自建(近似) | 香港天文台数据 | 寿星天文历(722BC起) | **本项目最大短板** |
| **节气精度** | 近似/查表 | 近似/查表 | 近似/查表 | 天文台精确 | 天文算法到分钟 | — |
| **农历转换** | 自建简化 | 自建简化 | 自建简化 | 精确(天文台) | 精确 | — |
| **应期推断** | 口诀表+法则 | 无(LLM判断) | 无 | N/A | N/A | — |
| **AI辅助** | 无(LLM做象数解读) | 无(LLM+Skill) | 无(LLM) | N/A | N/A | V/U项目有本地LLM双引擎 |
| **历史案例库** | 有(黑箱测试) | 无 | 无 | N/A | N/A | — |
| **可复现性** | 无种子控制 | `--seed`可复现 | 无 | N/A | N/A | A项目种子控制适合测试 |
| **数据输出** | JSON结构化 | JSON(可选) | 文本 | JSON | 多种格式 | — |
| **MCP协议** | 无 | 无 | 无 | N/A | N/A | F项目(Mingpan)用MCP |

---

## 三、我们尚未吸收的关键功能

### P0 — 关键缺失（必须补齐）

#### 3.1 高精度日历底座（最大技术债）

**现状**：本项目 `liuyao_engine.py` 使用自建的简化农历转换和节气算法，精度低，可能产生月建、日辰、空亡的错误推算（特别是节气交接日）。

**对标方案**：
- sxtwl_cpp：基于寿星天文历的C++实现，节气精确到分钟，BC722年起
- cnlunar：使用香港天文台数据，不用[Y*D+C]-L近似公式
- 6tail/lunar系列：完整24节气、朔望月、闰月规则

**具体影响**：
- 月建定错 → 旺衰判断全盘错误
- 节气交接日定错 → 月柱干支错误
- 空亡定错 → 用神力量判断失真

#### 3.2 真太阳时校正

**现状**：项目未考虑真太阳时与平太阳时的差异。出生在经度差异大的地区（如新疆 vs 上海），时辰干支可能不同。

**对标方案**：
- cnlunar、lunar-javascript、tyme4ts 均支持真太阳时换算
- mingyu (Brhiza) 排盘走天文历算引擎

**算法**：`真太阳时 = 平太阳时 + 时差`，时差由经度差（每度4分钟）和均时差（equation of time，由地球轨道偏心率与黄赤交角引起）共同决定。

#### 3.3 格局自动识别系统

**现状**：本项目未自动识别特殊格局（从格、化格、专旺、两神成象等）。

**需补充的核心格局**：

| 格局 | 识别条件 | 古籍出处 |
|------|---------|---------|
| **从格(从强/从弱)** | 日主无根无气，纯受其克 | 子平法借入 |
| **化格(化合)** | 六合/三合成化，日主从他 | 同上 |
| **专旺格(曲直/炎上/润下/从革/稼穑)** | 一方五行独旺 | 同上 |
| **两神成象** | 两气相成像，不战 | 同上 |
| **白虎/青龙会局** | 六神+地支特殊配置 | 六爻独有 |
| **反吟伏吟** | 已存在，但格局化处理不足 | 卜筮正宗 |
| **六合卦/六冲卦** | 已存在 | 卜筮正宗 |

### P1 — 重要缺失（建议补齐）

#### 3.4 卦身暗动量化体系

**现状**：暗动量化已存在(70%/30%)，但缺乏卦身暗动的完整处理——卦身暗动往往代表事物的潜在本体运作，不在明面。

**补充建议**：
```python
# 卦身暗动 = 卦身地支被日辰冲 + 月建旺相 → 有暗动之象
# 卦身暗动 >= 明动卦身的影响力 * 0.5
```

#### 3.5 跨时辰早晚子时处理

**现状**：时柱换算未区分早子时(0:00-0:59)和晚子时(23:00-23:59)。

**易错点**：传统命理学中晚子时时柱算法与常规不同（日柱不变/日柱+1两种流派），sxtwl已内置处理。

#### 3.6 三命通会/渊子平体系的部分借用

部分高级排盘系统借用了八字体系的格局法（从格、化格）来辅助六爻的深层分析，特别是用神极弱或极旺的特殊场景。

#### 3.7 六兽(追加六神)分阴阳

**现状**：已有六位六神，但部分体系在六兽基础上还有"阳龙阴虎"等细分——阳日六神力重，阴日六神力轻。

#### 3.8 纳音系统

**现状**：未纳入纳音（海中金、炉中火等）。

**对标方案**：6tail/lunar系列完整支持纳音。纳音在《黄金策》中有部分应用，可用于取象补充。

### P2 — 改进建议

#### 3.9 MCP Server 协议支持

对标 mingpan (ChesterRa/mingyu)、liki、fatecat。MCP 让六爻排盘能力可被任意 AI 客户端调用。

#### 3.10 可复现性种子控制

对标 baiyanwu/A 项目的 `--seed` 参数。实现后可用于：
- 自动化测试
- 案例库的精确复现
- 调试

#### 3.11 经典文本数字化检索

本项目有大量分散的注释文本（najia_rules.md、classical_synthesis.md），但未建立可检索的结构化知识库。

**对标方案**：
- 《卜筮正宗》可编码为 18论 + N个案例 的结构化形式
- 《黄金策》千金赋可编码为规则触发条件 → 断言 的形式

#### 3.12 "应期计算"精度提升

现状有应期口诀，但未实现以下算法：
- 逢值逢冲的精确日历映射（如"寅日应"→ 找出下一个寅日具体日期）
- 旬空出空的具体日期计算
- 月破填实日期

#### 3.13 交互日志/持久化

对标 SmallTeddyGames/divination-liuyao 的 OAuth2 + Prisma + 历史记录 + 分享功能。

---

## 四、可吸收的具体代码/算法建议

### 4.1 日历底座替换（优先级最高）

**建议方案：引入 sxtwl 或 lunar-python 作为日历底座**

```python
# 当前方案（自建简化）的弱点：
# 1. 节气基于固定日期偏移，实际节气在1-2天范围内浮动
# 2. 闰月规则简化，19年7闰仅是近似
# 3. 不支持真太阳时

# 替换为 sxtwl：
# from sxtwl import Lunar
# lunar = Lunar()
# day = sxtwl.fromSolar(year, month, day)
# year_gz = day.getYearGZ()  # 自动以立春为界
# month_gz = day.getMonthGZ()  # 以节气分月
# has_jieqi = day.hasJieQi()  # 当日是否有节气
# jieqi_name = day.getJieQi()  # 节气名称

# 或替换为 lunar-python（6tail）# pip install lunar-python
# from lunar_python import Solar, Lunar
# solar = Solar.fromYmd(year, month, day)
# lunar = solar.getLunar()
# day_ganzhi = lunar.getDayInGanZhi()
```

**影响范围**：`liuyao_engine.py` 中的 `get_month_branch`、`get_day_stem_branch`、`get_hour_stem_branch` 三个函数需要重构。

### 4.2 格局检测函数

建议在 `classical_analysis.py` 中新增：

```python
def detect_special_god_pattern(result_dict):
    """检测特殊格局"""
    patterns = {}
    
    # 1. 用神极衰检测
    if 用神克月建 and 用神克日辰 and 无元神发动:
        patterns['极衰'] = '用神极弱，虽生扶不起（增删易"枯木难生"）'
    
    # 2. 用神极旺检测
    if 用神临月建 and 用神生日辰 and multiple_同气:
        patterns['极旺'] = '用神极旺需泄（旺极宜泄不宜克）'
    
    # 3. 六冲变六合
    if 本卦六冲 and 变卦六合:
        patterns['冲合'] = '先散后聚，先苦后甜'
    
    # 4. 六合变六冲
    if 本卦六合 and 变卦六冲:
        patterns['合冲'] = '先聚后散，先合后散'
    
    # 5. 六冲变六冲
    if 本卦六冲 and 变卦六冲:
        patterns['冲冲'] = '反复不定，动荡不安'
    
    return patterns
```

### 4.3 真太阳时计算

```python
def calculate_true_solar_time(latitude, longitude, standard_longitude=120.0):
    """
    计算真太阳时修正值
    中国标准时间以东经120度为准
    """
    # 经度差每度 = 4分钟
    longitude_offset = (longitude - standard_longitude) * 4  # 分钟
    
    # 均时差 (Equation of Time) - 需查表或用公式
    # eot 约在 -14分钟 到 +16分钟 之间波动
    eot = get_equation_of_time(day_of_year)
    
    return longitude_offset + eot  # 分钟
```

### 4.4 六兽阴阳力重

```python
# 在 classical_analysis.py 中，六神辅助评分的修正
def six_spirit_weight(day_stem, spirit):
    """
    六兽分阴阳日：阳日六神力重、阴日六神力轻
    甲乙丙丁戊 = 阳日前半（力较重）
    己庚辛壬癸 = 阴日前半（力较轻）
    
    此规则出自部分高阶体系，仅供参考
    """
    yang_stems = {'甲', '乙', '丙', '丁', '戊'}
    base_weight = 0.3 if day_stem in yang_stems else 0.2
    return base_weight
```

### 4.5 应期精准日期映射

```python
def calculate_response_date(current_date, method, target_branch=None):
    """
    将应期断语转为具体日期
    method: '逢值' | '逢冲' | '出空' | '填实'
    target_branch: 用神地支
    """
    branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    clash_map = {'子':'午', '丑':'未', '寅':'申', '卯':'酉', '辰':'戌', '巳':'亥',
                 '午':'子', '未':'丑', '申':'寅', '酉':'卯', '戌':'辰', '亥':'巳'}
    
    if method == '逢值':
        # 找下一个target_branch日
        ...
    elif method == '逢冲':
        # 找下一个冲target_branch之日
        target = clash_map[target_branch]
        ...
```

---

## 五、各平台项目索引

### 5.1 Python 项目

| 项目 | URL | 特点 |
|------|-----|------|
| baiyanwu/liuyao-skill | github.com/baiyanwu/liuyao-skill | 完整八步装卦、JSON输出、种子可复现 |
| bopo/najia | github.com/bopo/najia | PIP包封装、纳甲排盘 |
| clider0915/divination-skills | github.com/clider0915/divination-skills | AI技能包、多术数融合 |
| 0xfnzero/YiSphere | github.com/0xfnzero/YiSphere | AI对话、多角色、全栈 |
| 6tail/lunar-python | github.com/6tail/lunar-python | 农历日历、节气、纳音 |
| jiqi1314/cnlunar | github.com/jiqi1314/cnlunar | 钦定协纪辨方书、天文台数据、港式算法 |
| OPN48/cnlunar | github.com/OPN48/cnlunar | cnlunar原始版 |
| kentang2017/ichingshifa | github.com/kentang2017/ichingshifa | 周易筮法、大衍之数、京房易 |
| tradecatlabs/fatecat | github.com/tradecatlabs/fatecat | 可复现计算、证据导向 |

### 5.2 JavaScript / TypeScript 项目

| 项目 | URL | 特点 |
|------|-----|------|
| 6tail/lunar-javascript | github.com/6tail/lunar-javascript | 最完整JS农历库、50KB |
| 6tail/tyme4ts | github.com/6tail/tyme4ts | TS升级版、节气第几天 |
| marsguo/lunar-javascript | github.com/marsguo/lunar-javascript | 6tail封装fork |
| ChesterRa/mingpan | github.com/ChesterRa/mingpan | MCP Server、多术数API |
| SmallTeddyGames/divination-liuyao | github.com/SmallTeddyGames/divination-liuyao | Next.js、现代化前端 |
| Brhiza/mingyu | github.com/Brhiza/mingyu | MCP + API结构化 |

### 5.3 C++ 项目

| 项目 | URL | 特点 |
|------|-----|------|
| sxtwl_cpp | gitcode.com/gh_mirrors/sx/sxtwl_cpp | 寿星天文历、高精度节气 |
| heqiao2010/LunarCalendar | github.com/heqiao2010/LunarCalendar | C++/Qt版、跨平台 |

### 5.4 中国术数传统特有项目

| 项目 | 体系 | 特点 |
|------|------|------|
| kentang2017/ichingshifa | 周易筮法 | 京房易体系 |
| Purple-Star-Astrology | 紫微斗数 | 四化系统、格局知识库、古籍原文数据 |
| learnwithu/mingli-master | 紫微斗数 | 可视化HTML命盘 |
| SylarLong/iztro | 紫微斗数 | TypeScript轻量星盘库 |
| destiny-core | 命理核心 | Go语言、八字/紫微 |
| ziwei-chat | 紫微斗数 | AI Agent、证据对话 |

### 5.5 本项目应优先对接的项目

1. **6tail/lunar-python** 或 **sxtwl_python** — 直接替换日历底座
2. **jiqi1314/cnlunar** — 如需黄历宜忌等扩展功能
3. **baiyanwu/liuyao-skill** — 参考其可复现种子设计
4. **6tail/tyme4ts**的节气算法 — 研究其[LEAP月数据编码](https://github.com/6tail/tyme4ts/blob/master/lib/index.ts#L1167-L1175)

---

## 六、总结与行动建议

### 最大缺口排序

1. **日历精度** (P0) — 自建日历是最大技术债，所有旺衰判断依赖精确的月建日辰节气。直接影响预测质量底线。
2. **真太阳时** (P0) — 时辰定错会导致时柱错误（影响空亡、暗动等）。
3. **格局识别** (P0) — 特殊格局（从格/化格）会让旺衰全盘反转，不识别就会断错。
4. **种子可复现** (P1) — 对自动化测试和案例库验证至关重要。
5. **纳音系统** (P2) — 对断象补充价值。

### 本项目的优势（值得保持）

- **思维链架构**：五步思维链(观局→定用→断旺→察变→综合)是独特设计，不属于任何开源项目
- **加权评分体系**：量化旺衰+格局调整+六级结论，目前是独一份
- **四大经典融合注释**：najia_rules.md + classical_synthesis.md 的深度远超多数开源项目
- **"机械运算归代码，象数解读归人"**原则 — 严格的防LLM幻觉设计
- **案例黑箱测试**：用历史案例验证思维链推理（非模式匹配）

---

*本报告基于 2026-09-18 时点的公开信息整理，项目状态可能随时间变化。*
