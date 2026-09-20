# 六爻盲评优化 v6 → v7 Handoff

> 日期：2026-09-19
> 目标：盲评平均胜率 ≥ 90%
> 当前：62.5%（上次 46.9%）

---

## 一、已修改文件

### 1. `scripts/thinking_chain.py`

- **verdict 阈值收緊**（lines ~3432）：
  - `final_score >= 1.0 → 吉`（原 2.0）
  - `final_score < -2.0 → 大凶`（原 -3.0）
  - `final_score >= -0.5 → 平吉`（原 0.5）
  - 移除「平凶」档，提升吉凶分明度

- **fu_shen_adjustment 指向修正**（lines ~3412-3430）：
  - 从 `step2_data.get("summary_text")` 改为 `step3_data.get("summary_text")`
  - 此前永远为 0（因为伏神分析在 step3 完成）
  - 新权重：飞来生伏 +1.0；飞克伏 -1.0；伏泄气于飞 -0.5
  - 伏神得出伏（飞神在 empty_branches）→ +1.5

- **伏藏 selected_use_god 回填**（lines ~1160-1180）：
  - `has_fu_cang=True` 时从 `_check_fu_cang` 提取 `fu_shen.branch`
  - 修复 use_god_branch="?" 的 P0-A 问题

### 2. 数据/脚本未新增文件

- 运行入口：`python scripts/run_blind_v4.py`
- 输出文件：`data/cases/blind_engine_output_v4.json`
- 基准答案：`data/cases/classical_cases.json`（cases[0..19] = ZS001-ZS020）

---

## 二、当前盲评结果（v6, 平均分 62.5%）

| ID  | 得分 | ID  | 得分 |
|-----|------|-----|------|
|ZS001|  90  |ZS011|  68  |
|ZS002|  36  |ZS012|  40  |
|ZS003|  32  |ZS013|  78  |
|ZS004|  50  |ZS014|  36  |
|ZS005|  68  |ZS015|  36  |
|ZS006|  86  |ZS016|  43  |
|ZS007|  78  |ZS017|  72  |
|ZS008|  86  |ZS018|  83  |
|ZS009|  68  |ZS019|  80  |
|ZS010|  40  |ZS020|  80  |

---

## 三、根因聚类（5 类错误）

### P0-A：伏神地支检索失败（已修）

- **影响**：ZS003/ZS014/ZS015/ZS016 全部输出 `use_god_branch: "?"`
- **根因**：伏藏成功（`_check_fu_cang` 返回 results），但 `selected_use_god` 未被回填
- **状态**：已修复（step2 末尾新增 `elif has_fu_cang:` 分支）

### P0-B：两现用神优先级错（待修）

- **影响**：ZS005(恒→戌/丑)/ZS009(恒→戌/丑)/ZS011(巽→未/丑)
- **根因**：震宫/巽宫两个妻财（辰/未/丑）并存时未按动爻/回头生优先
- **预期**：舍静取动 + 化回头生优先于化回头克
- **修复位置**：`_use_god_priority` 函数（thinking_chain.py ~line 1146）

### P0-C：三大高级格局缺失（待修）

- **影响**：ZS010(坤+日双合→冲中逢合可解)/ZS012(否六合→合处逢冲)/ZS016(升→飞丑旬空→飞空得出)
- **根因**：`冲中逢合可解` 仅在 moving_lines 或非月合 condition 触发；`合处逢冲` 未独立实现；飞空得出伏已落地但单独案例未测
- **修复位置**：`_detect_special_pattern` 函数

### P0-D：近病逢合规则缺失（待修）

- **影响**：ZS002 "占岳父近病，辰日合酉用神 → 凶"
- **根因**：
  1. 引擎取用神戌土（应取父母酉金）— 取六亲关键词映射不完善
  2. "近病逢合为凶" 规则不存在
- **修复位置**：
  1. 六亲映射增加"岳父→父母"关键词
  2. `_detect_special_pattern` 增加"近病逢合为凶"分支

### P1：三刑严格验证不足（待修）

- **影响**：ZS004 同人卦无丑/戌/未，引擎错误扣 1.0 分
- **根因**：`_analyze_sanxing` 未要求"三个分支齐备"才扣
- **修复位置**：thinking_chain.py 中 `_analyze_sanxing` 增加完整三组验证

---

## 四、v7 修复顺序

1. **P0-A 验证**：重跑 `run_blind_v4.py` 确认 ZS003/14/15/16 上升
2. **P0-B 两现**：`_use_god_priority` 增加"动爻位置优先"（`is_moving` 权重应高于 `is_world`）
3. **P0-D 近病**：六亲映射强化 + 近病逢合规则
4. **P0-C 格局**：冲中逢合/合处逢冲/飞空得出完善
5. **P1 三刑**：严格丑戌未齐备验证

---

## 五、关键不变量（勿改错）

- `NAJIA_BRANCHES`（liuyao_engine.py）：
  - 震 inner=子寅辰 outer=午申戌
  - 巽 inner=丑亥酉 outer=未巳卯
  - 坎 inner=寅辰午 outer=申戌子
  - 离 inner=卯丑亥 outer=酉未巳
  - 艮 inner=辰午申 outer=戌子寅
  - 兑 inner=巳卯丑 outer=亥酉未

- `hex2yao()` 在 `run_blind_v4.py`：
  - 输入：本卦名 → 变卦名（可为 None）
  - 输出：bottom-to-top yao_values 列表（长度 6）
  - moving yao = 9（老阳）或 6（老阴）

- 用神六亲判断基于 `palace_element`：
  - 震宫木 → 土=妻财，水=父母，金=官鬼，木=兄弟，火=子孙
  - 坎宫水 → 火=妻财，金=父母，土=官鬼，水=兄弟，木=子孙

- 盲评规则（勿在本 thread 内评测）：
  - 每次评测必须用 `task` 工具起新 sub-agent
  - 不得窥探 classical_cases.json 内容后在本 thread 内评分

---

## 六、下次启动命令

```bash
cd C:\Users\Lin\.meituan-catpaw\4567030888\skills\liu-yao
python scripts/run_blind_v4.py
```

输出 → `data/cases/blind_engine_output_v4.json`

然后起子代理盲评（用 task 工具，不在此 thread 内做）：
> 对 blind_engine_output_v4.json 盲评，基准答案 classical_cases.json cases[0..19]，子代理不窥探。
