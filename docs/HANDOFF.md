# 易 · 现状交接（2026-09-26）

> 取代口头交接。分数口径的逐次变化一律查 `docs/CHANGELOG.md`；
> 本文件只写「现在是什么、怎么跑、还欠什么」。
> **一切分数是古籍案例对齐分，不是现实预测命中率**（`AGENTS.md` 铁律三）。

---

## 一、这一轮做了什么（d351eb7 → 8c07eba）

主线：老师傅水准补强 + 古书案例黑箱 harness 实测 + 应期判别力突破。

| commit | 内容 |
|---|---|
| `010bcee` | 病药星煞 / 择吉神煞 / 梅花类象多爻动 / 小六壬邻宫综合断 |
| `5099e86` | 应期判别力第一轮（近病填实/久病冲空等） |
| `27bc352` | **应期 top-1 稳超随机 10pt+**（化空/回头生/飞克伏/先值后合） |
| `8c07eba` | chain_step5 断语字面量外置 + narrate 消费病药/星煞 |

审计全文：`docs/compose/spec/skills-maturity-audit.md`；补强规格：`docs/compose/spec/skills-maturity-boost.md`。

---

## 二、现在能不能信（按科）

### 六爻（disciplines/liuyao）— 可上岗助手

| 事项 | 状态 |
|---|---|
| 装卦/历法 | 可信（历法 16 项、爻序 23、金标准 288 例指纹 `65e8331c80c4f06a`） |
| 用神取法 | 四层：关系法则 → 代码消歧 → 186 键词典 → 世爻兜底 |
| 吉凶方向 | tune 95%、holdout 83%、wikisource 87%（strict） |
| **应期** | **首次具备判别力**：tune top-1 **58.8%**（随机~38，+20.8pt）；holdout **50.0%**（随机~36.5，+13.5pt）；名次 1.93/1.6 |
| 病药 | `bing_yao_shensha.py` 结构化 illness/medicine；narrate 已出「病药」短段 |
| 星煞 | core `ming_tables.shensha_at_branches` 安星；narrate 仅在临爻/临日旁参 |
| 断语治理 | `chain_step5`/`classical_rules` 字面量已入 `data/rules/verdict_texts.json`（`note_text()`）；`classical_rules` 仍有残余 CJK |
| 现实命中率 | **无法评估** |

**当前读数（strict，`python tools/check.py`）**：

| 集合 | n | 对齐分 | top-1 | 备注 |
|---|---|---|---|---|
| tune | 20 | **93.9** | 58.8% | 参与过调参 |
| holdout | 12 | **85.7** | 50.0% | 未参与调参 |
| wikisource_holdout | 35 | **57.3** | 20.0% | 永不调参，最保守 |
| yingqi_holdout | 2 | 87.2 | — | n 过小仅参照 |
| 黑箱回归 | 18 | 13/18 | — | 基线 ≥11 |

对外引用：优先 holdout/wikisource，必须带 n 与集合名。

### 梅花 — 骨架+浅断，holdout 已扩

- 万物类象入 `verdicts.json#bagua_analogies`；多爻动体用取舍（通行扩展口径，source 明示）
- holdout 3→**8**（MH014–018，manual 起卦与 tune 不同源）
- tune/holdout 对齐分 **100%**（n=10/8）——同源自洽，不证明泛化

### 小六壬 — 邻宫/方位已机械化

- 邻宫（进/退/临）速断 + 方位五行综合断；生克复用 `relations.wuxing_relation`
- tune/holdout 100%（n=10/5）；check 绿

### 择吉 — 神煞辅助已入裁决

- 天月德（+0.5）、冲肖煞方、彭祖百忌（-0.5）；不压黄黑道第一权
- tune/holdout 100%（n=10/5）；**仍是历法规则自洽，非古书占验黑箱**

### 命科 / 合参

- 命推演未建（仅 `ming_tables`/`relations` 表）；合参规则 5 常态「未参评」
- 合参 CLI / outcome-eval 可用；合成层自检绿

---

## 三、怎么跑

```bash
# 仓库级
python tools/check.py              # 结构/内核/四科/合参
python tools/check.py --full       # 加六爻黑箱回归与案例评测

# 六爻
cd disciplines/liuyao
python tools/check.py              # 八道质量门（含对齐分与应期判别力）
python scripts/evaluate.py --split tune|holdout|all
python scripts/evaluate.py --split holdout --verbose   # 逐例读数
python tools/golden.py verify|capture "理由"

# 其余三科
cd disciplines/{meihua,xiaoliuren,zeji}
python tools/check.py
python scripts/evaluate.py --split all
```

流派开关（改了分数不可比）：`YI_GANZHI_BOUNDARY=day|instant`、`--zi-hour-type late`。

---

## 四、应期规则（本轮核心资产）

位置：`disciplines/liuyao/scripts/chain_step5.py` → `_predict_timing` 排序。
**全部为通用古例归纳，禁止 case-specific**（`AGENTS.md` §四.3）。

优先级（高→低）：

1. **化出之支逢空** → 出空值日（扫全部化出支；ZS007/013）
2. **空而化回头生** → 不作空论，期于生我之日（ZS005；非空卦不前插，ZS009/020 仍逢值）
3. 用神旬空：日辰已冲→当日；久病→冲空；近病→填实；一般→填实+冲空
4. 伏藏：**飞克伏→先冲飞**；仅飞空得出→伏神值日
5. 月破/入墓/合住：填实、冲墓、冲开
6. 用神不空：**动爻先值日再逢合**；静爻值日再逢冲
7. 同五行空亡支出空 → 其他空亡出空 → 三合/原神/化出/旺相

否证记录（勿重复踩坑）：

- 把「病药应期」生硬插队 → tune 93.7→93.2、名次 2→2.38，**已回退**
- 按书序整体重排日级预算（舊 HANDOFF 四·7）→ 三集全降，**已回滚**
- 回头生全局前插 → ZS009/020 值日被挤掉，**改为仅空卦**

---

## 五、还欠什么（按优先序）

1. **wikisource 外部集** top-1 仍 ~20%（n=35）：泛化未证明；扩样路线见六爻 HANDOFF 四·三
2. **classical_rules.py** 仍有残余中文断语（`note_text` 未全覆盖）
3. **病药/星煞**尚未进 step5 加权与评分维度（只在 analyze/narrate）
4. **梅花**万物类象/多爻动的古书真案例黑箱（现 holdout 为构造校验例）
5. **择吉**通书古例真黑箱 + 彭祖百忌之外的三娘煞/杨公忌
6. **命科推演**（M5）——合参终局缺半边
7. 应期「次日/年内/月余」类相对表述仍无法机械评分（漏斗剔除）
8. 金标准指纹不含 narrate 文案（文案搬家需另设门）

---

## 六、口径与纪律（交接必读）

1. 对齐分 ≠ 预测率；禁止「准确率 X%」话术
2. 报分必带：集合名 + n + 是否调参
3. 改引擎：tune/holdout 分列；tune 无故跌破基线即回归；只改通用规则并给古籍出处
4. 口径变更（评分、单位、基线）必须记 `docs/CHANGELOG.md`，否则分数不可比
5. 案例库解读隔离；一卦一事
6. 金标准 `capture` 必须写理由；加性输出字段若不进指纹则无需 capture

---

## 七、工作树与分支

| 路径 | 分支 | 用途 |
|---|---|---|
| `.` | `main` @ `8c07eba` | 已合并全部本轮成果 |
| `.worktrees/skills-maturity` | `feat/skills-maturity` | 已合并，可删 |
| `.worktrees/opt234` | `feat/opt234` | 已合并，可删 |

清理：`git worktree remove .worktrees/skills-maturity` 等（确认无未提交文件后）。

---

## 八、验证记录（2026-09-26 实跑）

- 根 `tools/check.py`：结构契约/内核表/四科/合参 **全过**
- 六爻 `tools/check.py`：金标准/思维链 12/回归 13/tune 93.9/holdout 85.7/top-1 58.8&50 **全过**
- meihua/xiaoliuren/zeji `tools/check.py`：各全绿
- 金标准 288 例指纹 `65e8331c80c4f06a`（应期排序修订后 capture）
