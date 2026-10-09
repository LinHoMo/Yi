# 阴阳㝃组附录独立 key 核查登记（OPT-lingqijing_dz-02）

> ⚠️ **历史留档（2026-10-09 订正）**：本报告的落点学科**灵棋经（lingqi）已随 2026-10-09 两科收缩
> 整科删除**（commit `60b2403`）。实测现状：`ls disciplines/` 只剩 `liuyao`、`ming`，
> `disciplines/lingqi/data/ketables.json` **不存在**（`test -e` 返回假）。
> 因此本文 §二 全部核查表**不可复跑**，是 2026-10-07 八科时期的历史证据，**不得当作现行能力引用**。
> 现行范围真值源见 `AGENTS.md` §二；OPT 台账同口径处理见 `docs/OPT-LEDGER.md`。

| 字段 | 值 |
|---|---|
| OPT ID | OPT-lingqijing_dz-02 |
| 优先级 | P2 |
| 核查日期 | 2026-10-07 |
| 核查人 | 妙手 (CatPaw) |
| 裁定 | **已独立，登记即可，无需代码改动** |

## 一、目标

确认 `disciplines/lingqi/data/ketables.json` 中 124 纯组合与附录阴阳㝃是否已分离为独立 key。
（2026-10-09 订正：该路径所指文件与整个 `disciplines/lingqi/` 目录已不存在，见顶部横幅。）

## 二、核查结果

### 2.1 顶层结构

ketables.json 顶层 keys：
```
schema, _comment, problems, gongs, courses, appendix
```

### 2.2 courses — 124 纯组合

| 验证项 | 结果 |
|---|---|
| 课程数量 | 124 |
| key 格式 | `上-中-下` 各部面数 `0..4`（如 `4-4-4`） |
| 是否含附录 | ❌ courses 内无阴阳㝃条目 |

### 2.3 appendix — 阴阳㝃独立 key

| 验证项 | 结果 |
|---|---|
| 独立 key | ✅ `"appendix"` 数组 |
| 条目数 | 1 |
| 内容 | `純陰饅` → `陰饅卦`（无形之象） |
| 是否含 notes | ✅ 象曰 + 诗曰（完整原文） |
| 是否参与查表 | ❌ `_comment` 与条目 `note` 均注明 "不成课，不参与查表" |

### 2.4 文档与注释

`_comment` 数组 L6 明确记载：
> "appendix = 书源内非课标题章节（全陰不成课），存档不参与查表。"

appendix 条目自身的 `note` 字段也注明：
> "书源非课标题章节，按原文存档；不成课（三部皆无面），不参与查表"

## 三、结论

ketables.json 已满足以下契约：
1. ✅ `courses` 为 124 纯组合（不含阴阳㝃）
2. ✅ `appendix` 独立 key，不与 courses 混合
3. ✅ `check.py` 门（如 `[1c]` 结构门）不会把 appendix 当 courses 报错
   （2026-10-09 订正：此处 `[1c]` 指**已删学科灵棋经自己的** `disciplines/lingqi/dev_tools/check.py`
   里的「逐字回指门＋附录校验」（该文件已删，取历史版本核对：`git show HEAD~1` 加同名路径，L68-103），
   该文件与学科目录一并随 `60b2403` 删除，今不存在；根 `tools/check.py` 的 `[1c]` 是「断语外置取证」，
   与本题无关，未登记过该附录门）

**无需代码改动，仅登记核查结论。**

## 四、验收

- [x] ketables.json 124 纯组合 + appendix 单独 key
- [x] 核查报告落档：`docs/audits/lingqi_yin_yang_mo_appendix_key_2026-10-07.md`
