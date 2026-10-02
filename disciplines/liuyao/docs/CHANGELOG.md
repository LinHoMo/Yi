# 六爻 CHANGELOG

当前版本 **易 v0.0.1**（2026-09-22 起统一编号；此前文档里的 v6/v7/v8/M3 是各文档自造的代号，不再是版本号）

分数口径变化必须在此登记，否则 tune/holdout 数字不可比（`AGENTS.md` §四.4）。

## 2026-10-01o 语料占位空壳切除 + "消失的 40 叶子"复核（第三方验证订正）

第三方验证在你的写域查到两处事：一处**真 AI 痕迹**（已删），一处"结构性存疑"经复核
**判定为零引用死条目、不恢复**。

### 1. 切除 `verdict_texts.json` 末尾的 `chain_support_notes` 占位空壳

验证者发现 `data/rules/verdict_texts.json` 末尾是：

```json
 "chain_support_notes": {
  "temp": "x"
 }
```

`{"temp": "x"}` 是临时占位；该节**既无 loader 也无任何消费者**——全仓 420 个文本文件里，
`chain_support_notes` 只出现在该 JSON 自身与 `docs/CHANGELOG.md` 的记述里
（`tools/scratch/`、`.git/`、`site/` 镜像已排除）。处置：**整节切除**。

- 手术：逐行切除（`tools/scratch/vt-audit/cut_stub.py`），保留原 EOL（CRLF）、无 BOM；
  末行顶层 `}` 保留，前一行 `},` → `}` 去尾逗号；
- 结果：顶层节 24 → 23，叶子 892 → 891，49,777 → 49,730 字节
  （sha256 `7f9ffd7d1b139bd8` → `3e632a7596dd4636`）；严格 `json.loads` 通过；
- 该节原有的 6 条实文本（`fei_missing` / `fu_suppressed` / `fu_hidden_cap` /
  `fu_hidden_info_lack` / `fu_element_unknown` / `fei_unknown`）连同它的 loader，早在本批
  之前的减法里已按"死语料"删除（`docs/CHANGELOG.md` 2026-10-01 段记："六爻死语料 20 条
  删除（classical_interpretations 9、step5_yingqi_texts 5、chain_support_notes 6+loader）"）；
  本次只清掉残留的空壳。

### 2. 复核"相对 HEAD 少 40 个叶子"：全部零引用，**不恢复**

验证者按归一口径比对 HEAD，发现本文件少 40 个叶子（`"basis"` 由 251 降至 231）。
逐条复核结论：**40 叶子 = 20 条目 × (text + basis)，全部零引用，无一条承重**。四条判据：

1. **数量与分布和既有记载精确吻合**：消失的 20 条 =
   `classical_interpretations` 9 + `step5_yingqi_texts` 5 + `chain_support_notes` 6，
   与 `docs/CHANGELOG.md` 2026-10-01 段记载的 9 / 5 / 6（+loader）**逐位一致**；
   且本次比对 **changed = 0**——保留条目取值一处未改，属纯减法。
2. **静态检索零命中**（`tools/scratch/vt-audit/vt_consumers.py`）：对 20 个键名
   （`fei_missing` `fu_suppressed` `fu_hidden_cap` `fu_hidden_info_lack` `fu_element_unknown`
   `fei_unknown` `day_he_ji` `day_he_use` `jue_chu_no_source` `jue_wait_source`
   `month_day_he_use` `month_he_ji` `month_he_use` `no_moving_no_fanyin` `no_officer_tomb`
   `change_hui_tou_sheng` `speed_fast_label` `speed_medium_label` `speed_slow_label`
   `use_hidden_wait`）在 420 个仓库文本文件（`.py/.json/.md/.txt/.js/.html`）中检索，
   **全部 0 命中**。
3. **A/B 反向实验（决定性）**：静态 grep 查不出"动态拼装键"（本仓既有 `base_{强弱}` 一例），
   故把 **HEAD 版语料整份放回**再跑一遍，与在盘版对比（`tools/scratch/vt-audit/ab_reversal.py`）：
   - `dev_tools/golden.py verify` → 机械 `eb9977f62de4653f`、措辞 `ede6f855568a66a1`、
     异常 0 条，**两态完全相同**；
   - `dev_tools/check.py` 14 项读数（288 例指纹 / 段落 36 / 用例 12 / 回归 12 /
     tune 95.0·58.8·1.93 / holdout 89.7·50.0·1.6）**逐位相同**。

   即：把这 40 个叶子放回去，对输出**零影响**——含 `.get()` 式静默降级也不成立
   （任何一次真读都会改变渲染文本，从而改变措辞指纹）。实验后文件已**按字节还原**
   （sha256 校验一致）。
4. **消费口径旁证**：把 HEAD 版放回后跑 `tools/verdict_consumption.py`，liuyao 由
   `814 条语料 / 零消费 709` 变为 `821 / 716`——**新增的 7 条可计语料全部落在"零消费"**
   （其余 13 条因不足 8 汉字或与既有串重复而不进统计）。

**处置：一条不恢复。** 若将来要复活这些判定句，正确顺序是**先接线、再补数据**，
而不是把语料放回去等它被消费。

### 3. 验收（改动后实测，五项全 exit 0）

| 检查 | 实测输出 |
|---|---|
| `dev_tools/golden.py verify` | 288 例｜机械 **eb9977f62de4653f**｜措辞 **ede6f855568a66a1**｜异常 0｜√ 与基线一致 |
| `dev_tools/check.py` | 14 项全绿（288 指纹一致 / 段落 36 / 用例 12 / 回归 12 / tune 95.0·58.8·1.93 / holdout 89.7·50.0·1.6） |
| `tools/verdict_audit.py --strict` | exit 0：合计疑似未外置断语 **0 句** |
| `tools/verdict_consumption.py` | exit 0：liuyao **814 条语料 / 零消费 709**（与改动前一致） |
| `tools/check.py --full` | exit 0：**仓库级质量门全部通过**（含六爻黑箱回归 12/18，基线 11/18） |

**机械层与措辞层均零漂移**，未重新 capture。

### 4. 顺带记录：整文件重写的真实成因（本轮未动）

该文件相对 HEAD 呈**整文件级重写**（difflib 独立口径：+1755 / −1838 行，在盘 1781 行 vs
HEAD 1864 行），但**语义差异只有"40 叶子 + 空壳"**（逐叶子 JSON 比对：missing 40 /
added 1 / **changed 0**）。成因是两个纯格式变量：

| 变量 | HEAD | 在盘 |
|---|---|---|
| 缩进 | 2 空格 | 1 空格 |
| 行尾 | LF | CRLF（git 提示 "CRLF will be replaced by LF"） |

二者叠加使几乎每一行都不相等，`git diff` 因此失去可读性——**真正的语义改动被淹没在噪声里**，
这正是评审最易漏看真问题的地方（本次第三方验证正是靠"归一后比叶子"才抓到那 40 条）。
本轮切壳**沿用在盘的 1 空格 + CRLF**，不制造新的格式变更；是否把缩进/行尾归一回 HEAD 口径
（可把该文件 diff 从 ~3600 行压到 ~45 行）属仓库级决定，**本轮未动**。

## 2026-10-01n 注释减法 + 真死代码清零 + 学科质量门 `--only` 假绿修复

**本轮不改推演、不改计分口径**——tune/holdout 与各集分数、金标准指纹、回归/用例计数
全部持平（见下"验收数字"），故上面的分数仍可比。两类改动：① 删注释与真死代码；
② 修 `dev_tools/check.py` 的 `--only` 选择器语义。

### 1. 注释减法（六爻 7 个脚本，删 35 行注释）

另有 5 行注释（`liuyao_step4.py` 死块内 3 行、`liuyao_step2.py` 2 行）随 §2 的死代码一并删，
本轮注释合计 **40 行**、死代码语句 **7 行**、恒真表达式简化 **1 行**（合计 48 处改动）。

判据：**删掉后读者无法从代码本身恢复该信息 → 保留**；能恢复 → 删；不确定 → 不删、登记存疑。
带古籍出处/卷篇、口径依据、真值源指针（如 `（_BRANCH_CLASH_MAP 由 core 派生）`、
`真值源在内核 TOMB_MAP`）、阈值来源、算法契约（四段契约字段/边界条件/`tuple` 结构）的
注释**一律保留**；三段式分节注释（`# ---------- 3.10b: 暗动检测 ----------`）是 37 个
超大 `.py` 的唯一结构线索，**一律保留**。

| 文件 | 删 | 删掉的注释原文 |
|---|---|---|
| `effects.py` | 9 | `# Build bidirectional 六合 lookup`／`# Extract 用神 branch…`／`# Also check step3 which has use_god_branch explicitly`／`# Extract 忌神 positions/branches from step2`／`# Also check fu_cang`／`# Build summary`／`# Also match by branch if step3 has it`／`# Check vs 日辰`／`# 检查是否涉及世爻` |
| `liuyao_step3.py` | 5 | `# Extract yuan_shen/ji_shen elements…`／`# Check if this hidden-moved yao is the use god`／`# Skip explicit moving yao (already 明动)`／`# Check 六冲 relationship: day_branch clashes with yao_branch`／`# Determine the role for reporting` |
| `liuyao_step4.py` | 13 | `# Find the actual yao…`／`# Apply greedy harmony adjustment…`／`# Build greedy harmony description…`／`# Check if use god is combined by day or month`／`# Check for 六合/六冲 in hexagram name…`／`# Normalize score to float`／`# Check if yuan_shen has any moving line support`／`# Check no major attacking in moving lines`／`# Determine the branch to check for harmony:`＋`# Use the original branch if static/hidden-moved…`（两行）／`# Check 合 with 日辰`／`# Classify by role`／`# Check 合 with 月建` |
| `liuyao_step5.py` | 4 | `# Get 原神 branches`／`# Sort by date`／`# Determine overall speed`／`# Build summary` |
| `liuyao_narrate.py` | 2 | `# Determine strength from element_strength if available`／`# Detect question scenario for contextual interpretation` |
| `engine_calendar.py` | 1 | `# Handle rollover` |
| `classical_enhancements.py` | 1 | docstring `"""判断两地支是否六冲"""`（与函数名 `is_ba_zu_chong` 同义；同文件 `"""获取地支五行"""` **保留**，它锚定 `未知` 兜底约定） |

两类"删得有理"的特例，单列以免下棒误当误删：`# Check vs 日辰`（下一行循环同时遍历
`日`/`月`，注释只写日辰）、`# Check for 六合/六冲 in hexagram name`（实际查的是
`hex_type` 而非"卦名"）、`liuyao_step4.py` 的
`# Determine the branch to check for harmony:` 两行（实际是"本卦支+变卦支两支都查"，
注释却写成静/动二选一）——**这三处是与行为不符/容易误导的过期注释**。

### 2. 真死代码（3 处，均先全仓 grep 调用点）

| 位置 | 内容 | 判据 |
|---|---|---|
| `liuyao_step4.py` 旧 :617–:622 | `orig_branch = detail.get(...)`／`chg_branch = detail.get(...)`／`if chg_branch:` → 只有 `pass` | 两个局部变量在本函数内取完即弃（函数末尾即 `return rules`），分支体为空 |
| `liuyao_step4.py` 旧 :744–:747 | `div_time = step3_data.get("divination_info", {})`／`if not div_time:` → 只有 `pass` | 该 `div_time` 在本函数内无任何后续使用；空分支内注释"Try hex_result"没有任何实现 |
| `liuyao_step2.py` 旧 :695–:697 | `# 判断伏神是否得出`＋《增删卜易》引文＋`can_emerge = fei_shen is None or True  # 默认可出` | 表达式恒为 `True`（`fei_shen is None` 是死分支）→ 改为 `can_emerge = True`，并把注释换成**指向真正判据**的诚实指针：`本层不做判定：真正判据在 classical_enhancements._evaluate_hidden_spirit_emergence`。注意：`"fei_shen": fei_shen` 仍写入结果字典、被 `liuyao_step3.py` 读取，**不可删** |

**等价性证据**：`can_emerge` 恒真表达式的真值表不变（`fei_shen` 为 `dict`/`None` 两种取值
下结果都是 `True`）；两处空 `pass` 分支删除不改变任何控制流；`git` 之外无 `__all__`
或字符串形式的引用（全仓 grep）。运行层证据见 §4。

### 3. `dev_tools/check.py` 的 `--only` 假绿（与仓库级 `tools/check.py` 同类缺陷）

旧实现 `selected = set(args.only or [...])`＋逐门 `if "x" in selected`：**没有未知门校验**，
而 docstring 旧示例又写 `--only eval,calendar`（逗号）——名字整串对不上任何门时，所有
`if` 全假、一门不跑，却在末尾打印"质量门全部通过（或不低于基线）。"并 `return 0`。

修法（语义照抄仓库级 `tools/check.py`，**判定语义未动**）：逗号与空格等价；名字就地登记
（`want()`，可用名字的唯一真值源 = 各门调用点）；零命中或部分未命中 → 打印
`--only 用法错误：…`、列出可用门名、**退出码 2**，绝不打印"全部通过"。
本文件 docstring 示例同步改为空格形式并写明该语义。

### 3b. 金标准指纹显示 `?`（显示层缺陷，同批次一并修掉）

`liuyao`／`meihua`／`xiaoliuren` 三科门的金标准指纹行打出 `?`，例如
`√ 288 例指纹 ? 与基线一致`——**一个显示不出自己基线的门，读数就不可信**，故本轮一并修掉。

- 成因：三科用内核共享壳 `core/yishu_core/golden_kit.py`，壳的实文是
  `用例 N 条｜机械 <16hex>｜措辞 <16hex>｜异常 0 条`，而三科只写了
  `re.search(r"指纹 ([0-9a-f]{16})", out)` → 永不命中。同族的 `zeji/dev_tools/check.py:199`
  多带一个 `机械` 兜底，所以只有它显示得出指纹。
- 修法（三科各一行，**与 `zeji:199` 同构；判定语义未动**）：
  `d = re.search(r"指纹 ([0-9a-f]{16})", out) or re.search(r"机械 ([0-9a-f]{16})", out)`
  —— 落在 `liuyao/dev_tools/check.py:249`、`meihua/dev_tools/check.py:231`、
  `xiaoliuren/dev_tools/check.py:222`。
- **先证伪"是不是真取不到"**：三科的 `dev_tools/golden.py` 现场输出都含 16 位机械指纹
  （`liuyao` `eb9977f62de4653f`／`meihua` `2c9c810d8a265180`／`xiaoliuren` `9fd0de627fb787a5`），
  修前修后**一字未变**——换的只是"显示"，不是"读数"；该门的通过与否本来就只看 `rc`
  （`if rc != 0: failures.append(...)`），指纹比对由 `dev_tools/golden.py` 执行。
- 修后显示行：

| 科 | 修前 | 修后 |
|---|---|---|
| `liuyao` | `√ 288 例指纹 ? 与基线一致` | `√ 288 例指纹 eb9977f62de4653f 与基线一致` |
| `meihua` | `√ 案例指纹 ? 与基线一致` | `√ 案例指纹 2c9c810d8a265180 与基线一致` |
| `xiaoliuren` | `√ 15 例指纹 ? 与基线一致` | `√ 15 例指纹 9fd0de627fb787a5 与基线一致` |

八科门输出逐行 diff 后**只有上面这三行不同**（其余读数、异常数、对齐分全部持平），
`tools/check.py --full` 仍 exit 0。历史条目里记的一直是 16 位 hex（如 2026-09 的
`0e2bb128bfefe831`），可见"显示指纹"本来就是这个门的设计，`?` 是显示层回归。

### 3c. 硬编码用例数 → 从壳输出读（同一行内一并修掉）

同三科门的指纹行里还印着**硬编码**的用例数：`liuyao` 写死 `288 例`、`xiaoliuren` 写死
`15 例`、`meihua` 干脆只写"案例指纹"。权威值就在壳输出里（`用例 N 条`，`zeji:200` 就是这么取的）
——**语料一旦增长，门会印一个错误的数字却仍显示 √**，属静默说谎，故一并修掉。

- 修法（三科各一行；**判定语义未动**，通过与否仍只看 `rc`）：

  ```python
  # 用例数只认壳输出（唯一真值源）；取不到就如实说未知，不回落到自写常量。
  n = re.search(r"用例 (\d+) 条", out)
  cnt = f"{n.group(1)} 例指纹" if n else "指纹（用例数未知）"
  ```
  —— 落在 `liuyao/dev_tools/check.py`、`meihua/dev_tools/check.py`、
  `xiaoliuren/dev_tools/check.py` 的金标准段。
- **证伪"是不是常量"**（临时把本科 `dev_tools/golden.py` 换成打印假壳输出的 stub，跑完即还原并校验 sha256）：

| 科 | 未动 | stub 壳输出写 `用例 1234 条` | 还原后 |
|---|---|---|---|
| `liuyao` | `√ 288 例指纹 eb9977f62de4653f 与基线一致` | `√ 1234 例指纹 deadbeefdeadbeef 与基线一致` | `√ 288 例指纹 eb9977f62de4653f 与基线一致` |
| `meihua` | `√ 23 例指纹 2c9c810d8a265180 与基线一致` | `√ 1234 例指纹 deadbeefdeadbeef 与基线一致` | `√ 23 例指纹 2c9c810d8a265180 与基线一致` |
| `xiaoliuren` | `√ 15 例指纹 9fd0de627fb787a5 与基线一致` | `√ 1234 例指纹 deadbeefdeadbeef 与基线一致` | `√ 15 例指纹 9fd0de627fb787a5 与基线一致` |

  数字跟着壳输出变（`288`→`1234`→`288`）＝它真的在读数，不是常量；
  `liuyao` 另做"壳输出里没有 `用例 N 条`"变体 → `√ 指纹（用例数未知） deadbeefdeadbeef 与基线一致`
  ——**取不到就如实说未知，不回落到硬编码**。三次替换的 `golden.py` 均按字节还原、
  sha256 校验一致（**本工作流对 `golden.py` 零改动**：工作树 vs 暂存区为空；
  这三个文件相对 HEAD 的已暂存改动——改委托 `yishu_core.golden_kit`、-201/+23 行——是别的工作流的，与本轮无关）。
- 修后三科正常路径显示行：`liuyao` = `√ 288 例指纹 eb9977f62de4653f 与基线一致`、
  `meihua` = `√ 23 例指纹 2c9c810d8a265180 与基线一致`、
  `xiaoliuren` = `√ 15 例指纹 9fd0de627fb787a5 与基线一致`。
  与 §3b 的修后行**逐字相同**（因为解析出来的用例数与原来硬编码的数值相等），
  即这次改动**不改变任何正常路径的文字**，只在"数字与指纹不符/缺字段"时才显示差异。

### 4. 验收数字（与 2026-10-01m 基线逐项对照，全部持平）

- `dev_tools/check.py` 全跑：历法自检 16、爻序断言 23、金标准 288 例指纹**与基线一致**、
  段落冒烟、思维链用例 12、古籍回归 12、tune **95**、holdout **89.7**，
  `yingqi/wikisource/huozhulin` 外部集同前——**改动前后逐行一致**。
  （范围限定：这里指 §1／§2／§3 那次改动集。同批次追加的 §3b"`?` 显示修复"与
  §3c"用例数改为从壳输出读"都只改了三科门的**同三行显示文字**（`?` → 真实 16 位指纹；
  硬编码例数 → 壳输出的 `用例 N 条`），故八科门输出的准确表述是
  **"除那三行显示文字外逐行一致"**；机械层指纹、各集读数一字未变。
  证据：`before/` vs `after3/` 的逐行 diff = 恰 3 行差异；`--full` 全文只差
  `[0b] 读数锚点`的自指工作树计数那一行。）
- `--only` 证伪：`--only golden,calendar` 真跑两门、退出 0；`--only bogus` 与 `--only ""`
  均退出 2、列出 10 个可用门名、无"通过"字样。
- `python tools/check.py --full` 全绿（八科行为指纹 √ ×8）。

### 5. 本轮"刻意不动"（记此以免下一棒重复劳动）

- **注释**：`classical_enhancements.py:1888 # Compute combined strength (first match is
  enough — they share element)`（理由在括号里，属"为什么"）；`liuyao_step4.py` 的
  `# Check for 暗动 even in "static" hexagrams`、`# Also include 暗动 lines for greedy
  harmony check`、`# Also check: 用神被日月生合为凶`；`liuyao_step5.py`
  `# Use divination date as base for scanning forward`、`# Collect all 应期: list of
  (rule_str, date_or_None, branch, description_parts)`（`tuple` 结构契约）、
  `# Build a synthetic result dict…`＋`# Ensure thinking_chain structure exists…`；
  `liuyao_step4.py:866` 的 `（_BRANCH_CLASH_MAP 由 core 派生）`；以及**存疑未删**的
  `classical_enhancements.py:157` `"""判断两地支是否六合"""`——它与本轮删掉的 `:165` 六冲版同型
  （函数名已同义），只因"六合/六冲两版要一起裁决、不单独删一个"而留下，下一棒若要动手请两版同删。

  （更正：本条曾把 `liuyao_step3.py` 旧 `:376` 的 `# Skip explicit moving yao (already 明动)`
  也列入"刻意不动"，与本轮 §1 的删除记录自相矛盾——该行**确已删除**，现从本条移除。
  `liuyao_step3.py` 现已无任何"明动"字样。）
- **`generation → 世爻位` 有 5 份副本**：权威表 `scripts/chart_tables.py::WORLD_POSITION`，
  `effects.py` 两份就地重定义（缺省 `1` / `0`）、`dev_tools/fetch_*_cases.py` 两份。
  `core` **没有**该数值表（`symbols.EIGHT_PALACES` 只有世代字符串标签，
  `najia.response_position()` 是"由世位推应位"，语义不同），故"唯一真值源"在此不成立；
  改它要新建 core 表、属行为敏感改动，**本轮不做**。
- `# 检查连续三爻动`（`effects.py`）措辞：函数在 `len(moving) < 2` 就早退，严格说该块
  语义是"至少三爻且连续"，但改动太微妙，**不动**。

## 2026-10-01m 六爻整顿：减法做对 + 《卜筮正宗》书源结论

**本轮只做质量，不给六爻加语料。** 书源事实进 `references/source_ledger.md`，本条目只记结果。

### 1. 减法：重做上一棒的半成品（先查调用点，再删）

上一棒删了 `classical_enhancements.py` 的三个包装函数却没清调用点，`effects.py` 5 处与
`classical_enhancements.py:1340` 调到未导入的名字 → `NameError` → 段落 36→31、
古籍回归 12→10、tune 95→93.3、金标准指纹不一致。本轮按"**全仓 grep 调用点 → 改 → 立刻跑门**"
重做，并把被删函数的**唯一实现上收到更低层 `narrative_utils`**、保留 `__all__` 再导出，
消费方（`effects` / `classical_analysis` / 六爻门自身）**零改动**：

| 收敛项 | 处置 | 等价性证据 |
|---|---|---|
| `element_strength_text` | 删（纯转发壳 `s = f(...); return s`） | 全仓 grep 无调用点；从 `__all__` 同步移除 |
| `g_day_cn` | 删（纯 `return element` 壳），2 处调用改为直接传元素名 | 语义零变化 |
| `get_changed_hexagram_branch` | 两份合一（`classical_enhancements` 是 `return najia_branch(...)` 壳，`narrative_utils` 是自写循环） | 对 core `HEXAGRAM_TRIGRAMS` 全 64 卦 × 6 爻逐爻比对，**diffs = 0** |
| `element_strength_in_month` | 删本模块副本，改从 `narrative_utils` 导入 | 两份逐语句相同 |
| `_combined_strength` | 本模块与 `liuyao_step3._combined_strength_for_hm` **逐字相同** → 单一实现移入 `narrative_utils`；分值表改用既有 `strength_to_score` | 阈值 9/7/5/3 与分值表逐字相同；step3 以别名导入，调用点与 `__all__` 不动 |
| `_EFFECTS_REEXPORT` | 11 个名字原在文件里写两遍（`__all__` 字面量 + `frozenset`）→ 收敛为 `__all__` **之前**的一处 tuple，`__all__` 用 `*_EFFECTS_REEXPORT` 展开 | PEP 562 `__getattr__` 链路不变 |
| `najia_branch` 导入 | 随壳删除变为未用 → 删 | 先确认全仓无 `from classical_enhancements import najia_branch` |

**等价性证据全量复现**（`tools/scratch/liuyao_equiv_verify.py`，非抽样）：
`get_changed_hexagram_branch` 64 卦 × 6 爻 = **384 例 diffs=0**；
`element_strength_in_month` 5×5 = **25 例 diffs=0**；
`_combined_strength` 5×5×5 = **125 例 diffs=0**；空元素态（`""`）行为不变（`未知` / `衰`）；
`ce.get_changed_hexagram_branch is nu.get_changed_hexagram_branch` → **True**。
两个被删的壳已不在 `__all__` 且取不到；三个收敛项仍可按 `__all__` 取到，消费方零改动。

**清点后决定"不动"的两处**（记此以免下一棒重复劳动）：

- **死代码 0 个**：保守判据（私有名 + 不在本模块 `__all__` + 全仓任何 `.py` 里连**字符串形式**
  都不出现）全扫，命中 0。六爻已无可静态判定的死代码。
- `classical_enhancements` 末尾 **PEP 562 惰性再导出的 11 个 `analyze_*`**：`effects.py` 里
  那 9 个"本模块不用、外部也无 `from effects import`"的函数**不是死代码**——纯静态分析
  看不见这条再导出链路，**不得删**。

### 2. 《卜筮正宗》书源：维基文库**没有正文**（结论，不是抓取失败）

按 `tools/fetch_source.py` 的管线重抓（`--force`）：落盘 2,796B 并写 provenance。
但**四次独立探测**证明这就是上限：维基文库可得内容只有总页（目录 + PD 声明）与
`/卷前`（張景崧《敘》），总页列出的 `/卷01`–`/卷14` **全是红链**。
缺口性质是"**未数字化**"，重复重抓不会有新内容。

连带把三件事钉死（详见 `references/source_ledger.md`）：

1. **外部验证集被卡住**：`case_splits.json` 预留的 `bushi_zhengzong_holdout` 条目数为 **0**
   ——缺口不只是少一本书，而是让一个已立项的独立验证集无从建立。
2. **两份旧 provenance 的 `sha256` 与在盘文件不一致**，原因查明并复现：它是对
   **LF 归一文本**取的哈希，而在盘文件是 **CRLF**（文本模式写盘时 `\n`→`\r\n`）。
   `lf_text == 原 sha256` 为 **True**；两种口径已写进 provenance。
3. **`quote_database` 有 18 条署名《卜筮正宗·…》的引文**（共 49 条），该书正文不在库、
   维基文库也无 → **在库无源可核验**。本轮**不动**：改它要动 `verdicts.json` 结构或
   49 处 `source` 字面量，并把 `source` 带进渲染文案，须按"措辞层漂移"重新 capture，
   属独立一批。

《火珠林》原本**缺 provenance**，本轮按在盘文件实测补写；抓取时刻与子页清单当时
未留痕，**如实标"未知"，不编造**。

### 3. 书源双份（`archive/AUDIT.md` S-D10）已处理

`bushi_卜筮正宗_河潞武子龄校本_*.wikitext.txt` 两份重名副本，**先逐行证明其内容全部
被 `bushi_zhengzong.wikitext.txt` 包含**（缺 0 行）后删除；六爻下 3 个 `__pycache__`
一并清除。`archive/sources/meihua_*` 是同一挂账项的另一半，在只读作用域内，**未动**。

### 4. 瘦身：< 15,000 行**本轮做不到**（给证据与剩余计划）

行数 **18,560 → 18,117**（−443，−2.4%），全部来自上面两类减法。

用 tokenize 实测的分母：18,117 行里**含中文的只有 4,865 行**
（字符串 3,698 + 注释 1,167），且叙事断语**大部分早已外置**
（`data/narrative_templates.json`、`data/rules/verdict_texts.json`、`data/verdicts.json`）。
即便把全部中文串搬走也只到约 14.4k，可其中相当部分是 docstring 与**带古籍出处/口径
的注释**——后者是承重证据链，按用户口径不得删。

**结论：< 15,000 无法用"把可外置叙述逻辑移进 `data/`"单一手段达成**，因为 18k 行主体是
`AGENTS.md` 铁律一要求必须留在 Python 的机械推演（装卦/纳甲/旺衰/格局/应期/评分/渲染），
不是叙述。剩余可选路径都需挂账决策：① 合并/裁撤分析域（**改行为**，须重跑三集并重新
capture 金标准）；② 逐行清"复述代码"的注释（不改行为，需人工判读，粗估 −400~−900 行）；
③ 换度量——看**门面 API 表面积**（`liuyao_analyze.__all__` 条目数、叶子模块数）而非裸 LOC。
本条目倾向 ③ + ②，**但不擅自改挂账项口径**。

### 5. 口径与复跑

本轮只改结构与数据，**不改判定**；金标准机械层要求零漂移。复跑
`cd disciplines/liuyao; python dev_tools/check.py` 全绿，与改动前逐位一致：

- 金标准 **288 例指纹与基线一致**（机械层零漂移，未重新 capture）；
- 段落产出 36（≥36）、思维链 12（≥8）、古籍回归 12（≥11）；
- **tune** 对齐分 95.0 / 主应期 58.8 / 应支平均名次 1.93（集合 `tune`，n=20，**非 holdout**）；
- **holdout** 对齐分 89.7 / 主应期 50.0 / 应支平均名次 1.6（集合 `holdout`，n=12，**holdout**）；
- 外部集（只报数、不设门槛）：`wikisource_holdout` 56.3（n=35）、`wikisource_direction` 72.2（n=36）、
  `yingqi_holdout` 87.9（n=2）、`huozhulin_holdout` 13.1（n=2）。

分数一律是**古籍案例对齐分**（引擎输出与古籍案例要点的吻合度），
**不是现实预测命中率**；n 越小越只能当参照。

## 2026-10-01k 问题词典补天气占（186→195 键）

- 新增两族：**雨→父母**（5 键）、**晴→子孙**（4 键）；引文「占雨用父爻」「占晴用子孫爻」
  逐字取自 `data/sources/zengshan_buyi.wikitext.txt` 占雨占晴章，构建器 locate 核验通过。
- 动因：关系法则层与旧词典均不覆盖天气问，占雨类问题此前落到世爻兜底（取用错误，
  《增删卜易》明文父母主雨）。
- 追加在 FAMILIES 尾部，既有 186 键插入顺序未动（tie-break 不受影响）。
- **复跑三集**：tune 95.0 / holdout 89.7 / wikisource_holdout 57.1，与基线逐位一致。
  `EXPECTED_KEYS` 搬移基线同步 186→195。

## 2026-09-26e 仓库整洁（死代码/文档）

- **删除**：`factor_waterfall.py`、`engine_legacy.py`、`hallucination_guard.py`；
  `liuyao_engine` 仅 `coin|time|number|manual`；`visualization` 收敛为 SVG 卦盘。
- **删除过期研究稿**：`references/precision_gaps.md`、`regression_failure_analysis.md`、`open_source_research.md`（历史见 git）。
- **文档**：双 HANDOFF 合并至根 `docs/HANDOFF.md`；`LIUYAO-PLAN` 收为路线表。
- **分数/指纹**：无变化（tune 93.9 / holdout 85.7 / 金标准 `65e8331c80c4f06a`）。
- 历史条目里对 `visualize_shap`→`factor_waterfall` 的记载仍保留；后者本轮已删。

## 2026-09-26m chain_step4 拆分 + 择吉破日黑箱

- chain_step4.py（1313 行）→ 门面 + chain_step4_{changes,patterns}.py；金标准不变。
- 择吉：ZJ022 补「破」日规则应用黑箱（期望由 verdicts 宜忌表独立推出）；holdout 100%（n=6）。

## 2026-09-26l chain_step5 按职责拆分（零漂移）

- chain_step5.py（1949 行）→ 门面 step5_synthesize + chain_step5_{dates,timing,conf,yp}.py。
- 对外 API（thinking_chain 调 step5_synthesize）不变；金标准 5c6e77ee253b0ddd 不变。

## 2026-09-26k M1b 收尾：classical_rules 按域拆分（零漂移）

- `classical_rules.py`（3091 行）→ 门面 + `classical_rules_{hidden,patterns,effects}.py`。
- 对外 API 不变（`classical_analysis` 仍 from classical_rules import …）。
- 金标准指纹 `5c6e77ee253b0ddd` **不变**；tune/holdout/外部集读数不变。
- 根 `tools/check.py` 结构门新增巨石看门狗（单文件 >2200 行即失败）。

## 2026-09-26j 金标准补 narrate 文案门 + 应期绝对日窗

- **金标准**：抽样子集（每 24 卦静盘）记 `narrate_sha`/`narrate_len`，堵「文案搬家全盲」缺口；
  新指纹 `5c6e77ee253b0ddd`（含文案哈希）。纯结构改动若改正文会被拦住。
- **应期**：`yingqi_windows.py`——基准为次日/当日/年内/月余且案例有公历锚日时，
  换算绝对日窗比对 `yingqi_dates`；无锚日仍走 RHYTHM 语义。holdout 87.5 不变。

## 2026-09-26i 应期相对窗语义对齐（strict 口径）

- **口径变动**：strict 下基准无地支（`次日`/`年内`/`月余`/`当日`…）时，由「字面命中否则 0」改为：
  字面命中→满分；`RHYTHM_PAIRS` 节奏语义对齐→0.7×权重；否则 0。
  旧口径把相对表述当「未对齐」，低估引擎；**与此前 strict 分数不可比**。
- **读数**：holdout 对齐分 **85.7→87.5**（n=12）；tune 93.9、wikisource 57.3/72.2 不变。
- 仍不做「次日→绝对日」换算（缺事件锚日时不造假）。

## 2026-09-26h 外部集扩样：wikisource_direction（有吉凶无验期）

- `fetch_wikisource_cases` 新增**仅方向集**：无可靠验期但吉凶明确的 36 例（`WSD001–036`），
  expected.yingqi 留空 → evaluate 该维 **N/A**，不造假基准。
- 分数：`wikisource_direction` strict 对齐分 **72.2%**（n=36，verdict 26/36）；
  应期维全 N/A。与 `wikisource_holdout`（n=35，应期 top-1 20%）分列，永不调参。
- 口径：方向维与应期维分开报 n；禁止把无验期例当应期考卷。

## 2026-09-26g 病药进 step5（有界加减）+ 否证记录

- `chain_step5` 调用 `evaluate_bing_yao`，按 illness/medicine 码有界加减：
  重病无药 −0.4、有病无药 −0.2、有药无病 +0.15；不改主判阈值。
- **否证**：把药码（fill_void/heal_break/out_of_hiding）写入应期主排序 →
  tune top-1 升至 64.7，但 holdout top-1 **50→37.5**、名次 1.6→1.8，
  属过拟合 tune。**已回退药码进排序**；解除障碍之期仍由空/破/伏/化出通则覆盖。
- 回退后 tune/holdout/wikisource 与 26e 基线持平（93.9/85.7/57.3）。
- 金标准因新增 `bing_yao` 因子贡献条目而 capture 新指纹。
- 星煞仍不进 step5 主分（仅 narrate 旁参），与原口径一致。

## 2026-09-26f classical_rules 可交付断语外置

- `data/rules/verdict_texts.json#classical_rules_notes`：51 条 summary/reasons 完整句（空态说明、伏神飞神判据、格局名等）。
- `classical_rules.ctext(key)` 经 `chain_verdicts.CLASSICAL_RULES_NOTES` 加载；代码只留算法与键名。
- 地支/五行等象数符号、f-string 运算符字、docstring 留在代码（非断语）。
- **文本一字未改**，金标准指纹 `65e8331c80c4f06a` 与 tune/holdout/回归读数全部持平。
- 仍有拼装句用 f-string 组合；下一步可按模板键继续外置。

## M2.1（第三批·词典层）问题词典结构化进 data/ + 取用神四层来源标注（2026-09-24）

**改了什么**
- `tools/build_question_use_gods.py`（新）：186 键 `_QUESTION_USE_GOD_MAP` 按 64 事项族外置成
  `data/rules/question_use_gods.json`，逐族带取舍依据——38 引文族（《增刪卜易》逐字引文+offset，
  构建器 `locate()` 定位，`--check` 复验 **59/59** 命中）、26 推断族（写明"无逐条出处"的理由）。
  引文一律写 **為** 不写 **爲**、保留原竖标点，与 `build_use_god_rules.py` 同 locate 口径。
  键序与取值零漂移：外置前后 186 键逐键逐值比对一致（顺序参与打分 tie-break，禁止重排）。
- `chain_tables._load_question_use_gods()` 装载器替代字面量；装载失败抛 RuntimeError
  **不降级**（缺词典会把取用神静默退化成一律世爻，按铁律一宁可报排盘异常）。
- `chain_step2._decide_use_god()`：取用神决策返回 (类别, meta)，meta.source ∈
  法则|覆盖|词典|兜底，四层顺序与重构前逐字一致；`_determine_use_god_category` 变薄包装取 `[0]`。
  `_use_god_basis(question_category, question_text, chosen)` 四态文案：
  法则/词典有据＝「《增刪卜易》：…」（词典带族标签）、带引文覆盖层＝「覆盖规则「…」·《增刪卜易》：…」、
  无引文覆盖层＝「覆盖规则「…」（消歧层，无逐字引文）」、词典推断＝「问题词典推断（族名·无古籍
  逐条出处）」、兜底＝原默认文案。覆盖层展示引文集中于 JSON `layer_citations`（出行/功名/见贵/
  占子/胎孕/自占病/文书 7 类，逐字核验）；《卜筮正宗》《黄金策》归属改为"书名归属，原文未入库"。
- `tools/use_god_coverage.py`：classify 改直接消费 `_decide_use_god` 的 meta——**修覆盖层误报
  缺陷**（旧版复刻判断，覆盖层命中无 dict key → 报兜底）；docstring 里过时的"190 条无出处"同步。

**口径变动登记（AGENTS.md §四.4）**
- `_use_god_basis` 文案两态→四态；`use_god_coverage` 矩阵分类 法则|词典|兜底 →
  法则|覆盖|词典|兜底（词典再分 有据/推断）。**旧矩阵数字与新矩阵不可比**：
  新数＝92 问法中 法则 29、覆盖 14、词典 35（有据 23/推断 12）、兜底 14，有古籍逐字依据 63；
  旧数记 29 法则/48 词典/15 兜底。单字键问法 40 条（旧记 47，计数口径同为"含单字键的问法条数"，
  差异来自删键与分类修正，非分数）。
- `use_god_relations.json` 仅 `_meta.usage` 措辞更新（先过本表 → 再依次过覆盖层与问题词典），
  15 条规则内容未动，`--check` 15/15 命中。

**验收数字（strict，与基线逐集对照）**
- tune **94.5**（n=20，基线 94.5）／holdout **84.8**（n=12，基线 84.8）／
  wikisource_holdout **56.3**（n=35，基线 56.3）——三集全部持平，无回归。
- 金标准 288 例指纹 `0e2bb128bfefe831` 不变、异常 0；黑箱回归 11/18 持平；
  新旧 `_determine_use_god_category` 465 条问法对拍输出全同；`tools/check.py --full` 全绿。

## v0.0.1（2026-09-23）四段契约薄适配层 + Python 3.10 兼容修复

**新增：四段契约入口**（`scripts/chart.py` / `analyze.py` / `narrate.py` / `render.py`）。
包装既有引擎（`build_hexagram_result` / `thinking_chain` / `advice_framework`），
**不触碰推演逻辑**，金标准指纹不变（`tools/check.py --only golden,smoke` 复验绿）。
- `chart.py`：起卦 → 排盘 JSON（coin/time/number/manual + 早晚子时口径）。
- `analyze.py`：排盘 → analyze JSON，装配 `conclusion`（方向/说明/置信度/应期/所本）与
  `chart_summary`（卦名/干支/旬空/动爻/用神/旺衰），可直接喂合参层 `normalize_liuyao`。
- `narrate.py` / `render.py`：薄装配，正文一律走 `format_reading_output`。

**修复：Python 3.10 兼容**（此前 `tools/check.py` 在 3.10 下直接崩，等于质量门不可用）：
- `tools/check.py` 的版本检查依赖 `tomllib`（3.11+），改为零依赖最小 TOML 解析
  （只读 `[project]` 的 name/version/dynamic），不再需要 tomli。
- `scripts/visualization.py` 的 f-string 表达式内含 `"\\n"`（3.12 前语法错误），
  换行改为 `_nl` 变量；产物 HTML 结构不变，指纹未漂移。

**分数核对**（strict，未重新调参）：tune 94.5%（n=20，基线 94.2）、holdout 84.8%
（n=12，基线 78.3）——两者均高于基线，未动用 `--raise`。

## M2.2/M2.4（续三）应期日/月/年分级预算 + 评分单位感知（2026-09-23）

上一条记的否证结论是"缺的不是法则次序，是**分开的日/月两级预算**"。这一条把它做完了，
并且发现评分器本身还有一个**送分洞**，两者必须一起改，否则只做前一半就是虚高。

**改动一：候选池按单位分列**（`thinking_chain._predict_timing`）。旧实现把所有法则产出的
候选塞进一个 `ranked` 列表再 `[:5]` 截断，而候选的单位是混的（`未日`/`辰月`/`辰年`）。
后果是月级、年级候选占掉日级名额，日级答案又盖住月级——两个单位互相饿死。
现改为 `UNIT_BUDGET = (日5, 月3, 年2)`，各单位各自有序、各自封顶，输出
`yingqi_days` / `yingqi_months` / `yingqi_years` 三个分列（`key_branches` 即日级列，旧消费方不断）。
月级阶梯按「遠則應月﹐近則應日」（norm@79289）把同一套"解除障碍之期"在月单位上另排一遍：
冲空/实破/冲墓/冲开合住/冲飞得出/逢冲逢合/值月/生旺之月。**没有为此新造任何法则**，
只是把已有法则换个单位重排，所以不构成上一条警告的"拿外部集试次序"。

**改动二：评分改单位感知**（`evaluate.py`，**口径变更，分数与上一条不可直接比**）。
旧 strict 口径 `needed = [c for c in DAY_CHARS if c in x_yq]` 只抽地支字符、完全不看单位，
于是**基准写「未月」而引擎答「未日」也判为主应期命中**。这是白送分，和 §0 记的
`score.py` 读错字段送分同一类病。现在从基准里正则抽"支+单位"，只在**同单位**的候选池里排名次；
`yingqi_discrimination` 同步改为单位感知，并新增 `by_unit` 分级明细与
"同单位候选池为空＝算失败而非从分母消失"（否则答不出的单位会悄悄退出统计，n 变小分数变好看）。

**顺带修一处字段漂移**：`case_runner.py` 读 `timing["yingqi_dates"]`，而引擎实际把
`yingqi_dates` 放在 `step5_synthesis` 顶层（`thinking_chain.py:4423`），故该字段一直取空、
legacy 口径的日历日期比对从未生效。改为从 `s5` 读。

**金标准漂移已逐字段证明只落在应期上**：288 例中 102 例变化，变化字段**全部**是
`['yingqi_branches']`，结构字段（pillars/lines/palace/empty/changed/use_god/strength/
verdict/score/adv_keys/adv_summary/patterns）**0 处漂移**、0 异常。
基线 `bb23797bf6044b95 → 0e2bb128bfefe831`，理由与证据已随基线入库（`data/golden/digest.json`
新增 `drift_log`；`tools/golden.py capture` 现**强制要求填理由**，不给理由退出码 2 不落盘）。

**三集实测（strict）**：

| 集合 | 对齐分 | 主应期命中 | 应支平均名次 | 可定位 |
|---|---|---|---|---|
| tune (n=20，参与调参) | 94.2 → **94.5** | 29.4 → **35.3%** | 2.19 → **2.0** | 16 |
| holdout (n=12，未参与) | 85.1 → **84.8** | 25.0 → **25.0%** | 2.5 → **2.2** | 5 |
| wikisource (n=35，从未参与) | 56.7 → **56.3** | 17.1 → **20.0%** | 2.37 → **2.0** | 16 |

**两个下降必须解释清楚，不许含糊**：holdout −0.3、wikisource −0.4 的对齐分下降，
来自改动二收回的假分——原先靠"月/日单位互相顶替"拿到的应期分现在拿不到了。
这是**尺子变准**，不是引擎变差：同一批案例的判别力指标（主应期命中、平均名次）在三个集合上
**全部改善或持平**，而判别力才见真章（本节开头那句"只看召回会被候选集大小骗过去"）。
按 `AGENTS.md` §四.4 登记口径变更；门槛基线未下调（holdout 对齐分门槛仍是 78.3）。

**分级明细暴露的真实短板**（wikisource，此前被单位混算掩盖）：
日级 n=17 命中 17.6%／平均名次 2.3；月级 n=9 命中 22.2%／名次 1.75；年级 n=6 命中 33.3%／名次 1.0。
月级与年级可定位数仍少（4/9、2/6），说明"应支根本不在候选池"那一类（HANDOFF 记 15 例）
还没解决——那是本条改动一/二**没有**触碰的部分，属于下一步"解除障碍之期优先"的阶梯实现。
**本条只做了 HANDOFF 四·2.5 的步骤①，步骤②未做**；因为评分已改单位感知，
①不会像上一条警告的那样虚高（日级答案无法再去顶替月级基准）。

## M2.4（续二）外部集标签锚定 + 一次应期否证 + 样式层合一（2026-09-22）

**外部集口径变更（分数不可比，必须记）**：应期抽取从"整句扫（干）支+日月年、日级优先"改成
**只认紧跟應/果/期/驗的那一期**。旧写法把机制句当成了答案：

| 例 | 原文 | 旧抽取 | 应为 |
|---|---|---|---|
| WS005 | 應未月者﹐土爻未土乃世爻之墓﹐**丑日**沖開 | 丑日 | **未月** |
| WS020 | 應**子年**者﹐占時原有**子日**沖其午火 | 子日 | 子年 |
| WS018 | 應辰**時**者（时级，引擎不产时级候选） | 戌日 | 剔除 |

同时把**月建缺失**的例剔掉（无月令则旺衰/月破/生扶全无依据，评的不是引擎的分）：
n 39 → 35，strict 47.6% → **56.7%**（用神 4/4、吉凶 13/16=81.2%、主应期 6/35=17.1%）。
涨的分里有 4 个假标签被剔的功劳，也有分母变化的算术——所以只报"改了多少"不报"为什么变"就是耍赖。

**一次否证（照书重排应期阶梯）**：外部集失败集中在"应支在候选但名次靠后"(14) 与"根本不在候选"(15)，
看着像次序问题。书里确有阶梯，且两章各写一遍足以证明是通则：
「衰者宜生旺之日﹔旺而靜者﹐逢值沖之日﹔動而逢值逢合之日﹔空與入墓﹐必待沖開﹔破與旬空﹐須期塡實」
（發案持榜章，norm@59438）；「遠則應月﹐近則應日。子孫動者逢合逢值﹐靜者逢值逢沖﹐空者沖空實空之日」
（norm@79289）。照此改完**三个集合同时下降**：tune 94.2→93.6、holdout 85.1→84.8、外部 56.7→54.9，
可定位数 19→18。已回滚。根因是**主应期只有 5 个日级名额**，塞进月级候选就把正确的日支挤出去了——
真正的下一步是"日/月两级分列预算"（要改 `timing` 输出契约与评分取支逻辑，属口径变更），不是次序。
顺带记下文献矛盾：动爻"逢值逢合"（發案持榜）与"逢合逢值"（嬰章）两说，不拿外部集试出来挑一个。

**用神层补强**：法则表 14 → 15 条（新增"宅/房/屋 → 父母"，引文「父旺持世﹐此處淸安宜久住」
盖造买宅賃宅章，norm@96246）；删掉词典里 4 条单字键（子/见/回/期——"占买房子"的"子"曾被命为子孙）。
三集分数不变（tune 94.2 / holdout 85.1 / 外部 56.7），因为这三条键原本没承担对的案例，只是不再误导。
新工具 `tools/use_god_coverage.py` 给出**来源矩阵**：92 条问法里法则 29（31%）、词典 48、兜底 15，
其中 47 条靠单字键子串命中——"用神 100%"从此必须分开说"对"与"有据"。

**样式层合一 + 外观回归门**：两套 CSS（排盘报告 / 解读报告）合成 `assets/report.css` 一份，
`visualization.py` 与 `build_html_report.py` 同源读取。合并第一版只搬"看起来像图形"的 12 条规则，
排盘报告 29 个类没了定义、当场散架；于是加质量门 `[2.5] tools/style_check.py`（核对交付文档里
用到的类名是否都有定义，定义域含页面样式层与各 SVG 自带内嵌样式——只看 report.css 会误报 22 个）。
顺手补了一个悬空多年的 `.serif-title`（挂在 h2 上但从没被定义过）。八道门全绿。

---
## M2.1（第一批）取用神加"关系优先"层，法则逐条带原文引文（2026-09-22）

**动因是外部集给的证据**：`wikisource_holdout` 上原文明写用神的 4 例，引擎一例都没取对——
女家占婚取了妻财（书里明写"女家占男，皆以官為用"）、占伯取了子孙、占夫取了世爻。
`_QUESTION_USE_GOD_MAP` 那 190 条现代问法词典补不出这些：它缺的不是词，
是**关系优先于事项**这一层，以及每条规则该有出处。

**做了什么**
- 新增 `tools/build_use_god_rules.py` → `data/rules/use_god_relations.json`（14 条）。
  规则表落 data/ 而不是堆在 .py 里（AGENTS.md §三），且**引文必须在原文里逐字找到，
  找不到就不出表**——`--check` 会逐条回查 `data/sources/zengshan_buyi.wikitext.txt`。
  匹配时忽略标点（刻本用 ﹐U+FE10 而非 ，），落盘时回填逐字原文与偏移量。
- `thinking_chain` 取用神顺序改为：异体归一 → 剥卦名尾巴 → 关系法则层 → 原词典层；
  step2 多输出 `use_god_basis`（"《增刪卜易》：…" 或 "问题词典默认…"），
  报告里第一次能说出"这一爻是按哪句原文取的"。
- SKILL.md 删掉"LLM 对照总表交叉校验用神，冲突时以指南为准"那段——那是让语言模型
  推翻代码的象数结论，违反铁律一。改成：缺性别/身份就补输入重跑，
  所本为"词典默认"时如实说明是默认取法。

**质量门在改动过程中抓出的两处通用缺陷**（都不是为过某个案例）
1. 卦名混进问事文本："占投资经营，益之小畜"里"畜"命中"凡占六畜皆以子孫為用"，
   把占投资判成占牲口（HO006/HO009 同时中招）。修法是匹配前先剥卦名与"X之Y"尾巴，
   并把 畜/孫 这类单字触发词禁掉——**用神只由问的事决定，不由起的卦决定**。
2. "久病"当触发词时，"占子久病"被"自占病，世為用神"抢走（reg_08 用神当场翻脸）。
   该书此句只讲自占，故触发词收回为 自占病/自病/我病 等自指字样。

**三集并报（strict 口径，`python tools/check.py` 可复现）**

| 集合 | 改前 | 改后 | 用神维 |
|---|---|---|---|
| tune（n=20，参与过调参） | 94.2% | 94.2% | 20/20 → 20/20 |
| holdout（n=12，未参与调参） | 78.3% | **85.1%** | 11/12 → **12/12**（应支名次 2.6 → 2.5） |
| wikisource_holdout（n=39，从未调参） | 47.6% | **55.7%** | 0/4 → **4/4**（主应期 13.5% → 17.9%） |

**金标准基线搬家并补盲区**：`tools/golden.py` 的比对基线原先只写在 gitignore 的
`scratch/golden_before.json`——等于只有开发机上有看门狗。现改为入库
`data/golden/digest.json`（只存 16 位指纹与用例数，288 例逐字段快照仍留在本地），
并把它加成质量门 `[1.6]`。题面原来六种问法（求财/病/行人/婚姻/讼/失物）**全都不触发
新加的关系法则**，等于给那层留盲区，已补 占父病/占夫外出/占妻胎安否/占伯何日回/
占子久病 与两条繁体问法（占升遷、占候文書）。基线随之内核重拍为
`bb23797bf6044b95`（旧 `07ca1df40523d167` 因题面变化不可比）。

**已知残留**：`占买房子` / `占购房产` 仍取子孙（应为父母；书有"占宅以父母为用"，
`占宅` 一条是对的）。这是词典层的老问题，不在本批范围，已记 HANDOFF 四·2。

## M2.4（续）原文抓取打通：第一个真正的未调参外部集（2026-09-22）

**做了什么**：`tools/fetch_wikisource_cases.py` 从维基文库《增刪卜易》拉整书 wikitext
（123,927 字，sha256 `897f963b938e…`，重跑取回同一串，provenance 落在 `data/sources/`），
字符级解析出 253 幅爻图，与内核逐爻比对后成集。**全程不经过语言模型转写**——
`case_library.md` 那 14 例动爻自相矛盾就是转写造出来的，见 `docs/CASE-LIBRARY-AUDIT.md`。

**装卦层首次拿到外部确认**（这才是本次最硬的结论）：

| 比对项 | 分母 | 与原本不合 |
|---|---|---|
| 纳甲地支 | 822 爻 | **0** |
| 卦变（○ㄨ 位次 vs 本卦⊕變卦差集） | 105 例 | **0** |
| 世位 / 应位 | 各 120 例 | **0** |

内核的纳甲表、八宫世应、爻序约定与清刻本原书一致。顺带在工具里复现了一次
"世+2 当应位"的镜像错误（当场错出 38 处不合）——应位规则已收进
`yishu_core.najia.response_position()` 单一真值源，`thinking_chain` 与抓取工具共用。

**外部集成绩**：`wikisource_holdout` strict **47.6%（n=37）**，其中吉凶方向 12/17=70.6%、
主应期命中 13.5%、基准应支平均名次 2.22（18 例可定位）；
**原书写明用神的 6 例，引擎一例都没取对**（多半回退成"世爻"）——M2.1 的账，
外部集第一次把它量了出来。对照内部 holdout 的 78.3% / 25.0%，
**此前那两个数偏乐观**，未经调参的真实差距更大。

**一个差点混过去的静默漏抽**：刻本通篇用异体 爲(U+7232，625 次)，
而我的正则写的是 為(U+70BA)/为——"以父母爲用神"一条也抽不到，用神那一维 37 例全记 N/A，
报表上看着完全正常。补了关键字覆盖体检才发现。故整书先做一次等长异体归一
（`norm_text`，长度不变所以 provenance 偏移量仍对得上），词条也只保留原文里真出现的字。
教训：**只报"不合 0 处"是不够的，必须同时报分母**——分母为 0 的"全对"就是没测。

**口径变化（影响分数可比性）**：基准缺某维信息时，strict 改记 N/A（该维权重退出分母），
不再判 0。新增两处：用神六亲（基准未取用）、吉凶方向（古籍只记验期不记验事）。
legacy 口径不动（空白基准仍给满分），所以 strict/legacy 差被拉大到 18.5 分——
这正是"空白基准白送分"的量。tune/holdout 未受影响（实测 94.2% / 78.3% 不变）。

**漏斗（为什么只有 37 例）**：253 幅图中 93 幅是法例配图无日辰、112 例验期不可检
（"次日""七月""果於申時"这类相对/数字/时辰表述）；入集的 37 例里 20 例只断不验（只有验期、
没有吉凶对照），该维记 N/A。
数字月换算成月支要靠"夏正正月建寅"的读法，读错就是给引擎假基准，故宁缺不接。

## M2.2（第二批）补三条应期法则 + M3 展示层（2026-09-22）

**应期法则补全**：从 4 例"完全没给出基准应支"的案例里抽出三条被漏掉的古籍法则——
① 动而化回头生，期于生我之日（ZS005/ZS019：戌财空而化巳火回头生，次日巳日）；
② 空亡之支出空值日，不限于用神（ZS010：应于旬空之寅日）；
③ 动变所化之支逢空，迟者应于其年（ZS008：丙午年填空）。
候选上限 4→5。效果：可定位案例 12 → 15（n=17），tune 对齐分 92.4 → 93.7；
top-1 命中持平 29.4%，平均名次 1.67 → 2.13（新覆盖的 3 例命中在 3–5 位，是覆盖换名次的正常代价）。
**到此收口**：n=17 的集合上继续逐例调法则就是 `AGENTS.md` 禁止的案例特判，
下一分力气应花在 M2.4 扩外部样本，而不是把 29.4% 抬到 35%。

**M3 展示层**：
- 报告新增「主/次应期表」：应支 + **所本法则** + 最近日历日，并声明应期是观察窗口非倒计时。
  此前报告有应期时间线 SVG 却没有一句"凭什么"。
- `build_portal_assets.py` 重写：分数一律从 `evaluate.py --save` 的落盘结果读取，
  **不再硬编 100.0**（上一版把 v8 的满分写死在脚本里，引擎改了门户照旧）；
  样例报告写入 `outputs/reports/`；并把 portal-data 内嵌回 index.html（原 `embed_portal_data.py`
  已删而无人补）。
- 门户看板：头部改显示 **holdout 分 + 样本量**（此前是硬编 100%）；逐例格子显示真实案例 ID 与分数
  （此前 `ZS{i+1}` 与 20 个 100）；新增应期判别力行（top-1 / 平均名次 / 候选集 / 随机期望）。
- 修死链：「打开完整样例报告」原先 `window.open('sample_report_ZS001.html')`，该文件早已被清，
  点击即 404；改为用页内数据在新窗口渲染完整报告，不再依赖预生成文件名。
- `visualize_shap.py` → `factor_waterfall.py`：它不是机器学习 SHAP 归因，只是把
  `factor_contributions` 手画成条形图，蹭名词会被内行一眼看穿。
- 浏览器实测 `file://` 直开：holdout 78.7% (n=12)、逐例分数、应期行均正确渲染，控制台无报错。

## M2.2（第一批）应期改为法则驱动的主/次应期（2026-09-22）

**引擎侧** `thinking_chain._predict_timing`：旧实现是并集收集器——动爻、变爻、用神之冲与合、
原神旺日四支、伏神、飞神、旬空二支、日辰、月建、合局冲开全部 `_push` 进 `key_branches`，
平均 **11.1/12** 个地支，再截前 8 个显示。这不是判断，是把可能的支都念一遍。

现按用神状态择优（《增删卜易》应期诸法，"解除障碍之期"优先）：
旬空→冲空/出旬填实；月破→出月逢值/逢合；伏藏→冲飞神得出/伏神值日；入墓→冲墓；
被日月合住→冲开；发动→逢合/值日；安静→逢冲/值日；休囚→旺相之日与月。
`key_branches` 取前 4，长列表改名 `candidates_all` 只作备查；新增 `timing_rules`
（每个候选附其所本法则，报告与正文可回溯"为什么是这一天"）。

顺带修 `_chong`/`_he` **单向查表**：六合六冲每对只登记一次，旧写法查 `丑` 查不到 `子`，
凡从反向支求冲求合皆落空。改为双向。

**指标侧**（口径变化，前后分数不可直接比）：strict 的应期维度由"成员制"（候选里有没有提到）
改为**按名次给分**（主应期满分 / 次应期 0.8 / 第 3–4 位 0.55 / 只在依据句里出现 0.35 / 没给 0）。
原因：成员制**奖励骑墙**——候选铺到 11/12 支即可白拿 15 分，历史上"应期 100%"就是这么来的。

| 指标 | 改前 | 改后 |
|---|---|---|
| 应期候选集平均大小 | 11.1 / 12 | **3.2 / 12** |
| 随机列同样多候选即全覆盖的期望 | 92.6% | **26.5%** |
| 主应期(top-1)命中 tune | 11.8% | **29.4%** |
| 主应期(top-1)命中 holdout | 12.5% | **25.0%** |
| 基准应支平均名次 tune / holdout | 4.69 / 5.50 | **1.67 / 2.00** |
| tune 混合分 strict | 97.1% | 92.4% |
| holdout 混合分 strict | 86.2% | 78.0% |

**混合分下降不是退步**：真判别力（top-1 与名次）提升 2–3 倍，而旧混合分里那部分
"提到就算对"的水分被指标改造挤掉了。主应期命中 29.4% 对随机 8.3% 仍是约 3.5 倍，
但离可用还远——这正是 M2 剩余项目（用神取法决策表、应期法则补全、外部效度扩样）的靶心。

`tools/check.py` 相应增门：top-1 命中与应支平均名次纳入"只准前进不准后退"基线。

## M2.4 外部效度尝试 + 结果回填链路（2026-09-22）

**夹具重推**：`case_03` / `reg_03` 的动变净效应由 neutral 改为 positive，依据是
坤宫三爻甲辰兄弟土动、兄弟即子孙金之原神、原神发动生用 ⇒ 净效应为正；
辰化丑属化退、日月合绊稍减其力，不改总体有助。基线 chain 8/12、regression 11/18。
顺带订正夹具自相矛盾的旧注释（原写丁卯日／回头生，实为乙酉日／化退比和）。

**外部验证集尝试（结论为负）**：`tools/build_yingqi_set.py` 六道门抽 `case_library.md`，
扫描 29 例 **仅 2 例可用**；14 例动爻与卦变矛盾、11 例应验句无可检验干支。
逐例原因落在 `docs/CASE-LIBRARY-AUDIT.md`。因此**不设 yingqi_holdout 门槛**，
质量门 [6] 只报数；要建真外部集需可靠整理本原文，重跑工具即成。

**过程中修掉三个我自己的抽取错误**（都属"给自己打假分"方向）：
① 应期正则在整块文本里搜，把 `### 时间` 的占测日干支当成答案（案例三真应期未日被抽成卯日）；
② 正则要求全干支（丁未日），而古籍多写裸支（未日），会漏掉真答案；
③ 把静卦（六爻皆不动）当缺项剔除，实为合法卦型。
另：`use_god` / `verdict` 未抽取，会让两维直接判 0、得出比真实水平更低的假分——已补。

**结果回填链路**：`event_logger` 现在落盘 `yingqi_main/yingqi_rule/yingqi_alt/yingqi_window_days`
（窗口对齐主应期那一支的日历日，不取 dates[0]）；新增 `tools/outcome.py`
（list / record / stats，统计给 n 与 Wilson 95% 区间，n<30 明确拒出结论）。
端到端自测时，回填守卫当场指出"应验日日支为申、与主应期巳日不合"——正是要的行为。
自测事件已从 `logs/divination_events.jsonl` 清除（6 条），保留真实记录 621 条。

**当前应期能力（三个层次要分清）**：tune 主应期命中 29.4%（n=17，参与过法则调参）、
holdout 25.0%（n=8）、真正未调参外部集 n=2 不足以说明任何问题。
**所以"应期可用"目前不成立**，缺的是样本，不是再调一条法则。

## P0 爻序统一 + 仓库统一于 Yi（2026-09-22，易 v0.0.1）

**爻序（P0，已修）**：震·巽·艮·兑四个非回文经卦曾在**四处**各存一份"上爻在前"的镜像编码
（引擎 `BAGUA.lines`、`case_runner`、已删的 `batch_round3_direct`、`data/hexagrams.json` 的 `binary`），
而所有消费代码按"自下而上"解读，后果是每个经卦内部三爻位次整体颠倒。

- 真值源收进内核 `symbols.BAGUA_LINES`（自下而上，附 `trigram_lines()/yao_values()`），
  其余三处删除或由此派生；`case_runner.hex2yao()` 改为"本卦与变卦逐位比差异"得动爻位。
- 新增 `tools/hexagram_check.py` 23 项断言作看门狗：卦象常识（震仰盂/艮覆碗/巽下断/兑上缺）、
  六十四卦全量自洽、位次与爻名逐一对上、`恒之鼎必须动在上六且化巳`（《增删卜易》ZS005 明载）。
  已接入 `tools/check.py` 为 `[1.5]` 门。
- 修正前：按文档"从下往上"喂真实恒卦 → 引擎判"山泽损"；恒之鼎被算成第四爻午动。
  修正后：判恒、动在上六戌、化出巳——"动而化回头生"这条应期法则**第一次真正触发**
  （ZS005 应期候选此前无"巳"，现有）。
- 夹具迁移：三套测试里 61 个爻数组由"意图卦名 + 作者本意动爻位次"经内核重新编码，
  不再靠镜像表凑。代价：chain case_03 与 reg_03 的期望值本是在镜像位次上标定的，
  现各失 1 例（基线 8→7、11→10，理由写进 check.py 注释），待按古籍重推，不许改回镜像凑数。

**分数影响（几何修正后）**：tune 93.6 → **94.2**、tune 应支平均名次 2.27 → **2.19**；
holdout 78.3、top-1 29.4/25.0 不变。对齐分上升说明此前错位在拖累判断，不是中性的。

**评测完整性**：`tools/check.py` 加新鲜度守卫——先删旧落盘文件、评测非零退出即判失败。
起因很讽刺：修 P0 过程中 `case_runner` 被我删了常量而报错，门却报"分数一位不动"，
实为读了上一次的 `eval_tune.json`。**没有这道守卫，任何"分数没变"都不可信。**

**仓库结构**：六爻完整历史（11 提交）经 `git subtree` 并入 Yi 单仓为 `disciplines/liuyao/`；
内核上收为 `Yi/core/yishu_core/`；新增 `scripts/kernel_path.py` 以向上搜索取代 11 处写死层级的
`parents[1]/"core"` 算式；pyproject 合并为仓库根一份（包名 `yishu-core`），并加门禁止学科根再放第二份。

**范围收窄**：相科（面相、手相、堪舆）明确不做，全部文档已清除相关目录、里程碑与合参行；
合参按命·卜两科成立。

## M1（第一批）象数基元合一（2026-09-22）

新增 `core/yishu_core/symbols.py`（245 行）为**唯一真值源**：
HEAVENLY_STEMS / EARTHLY_BRANCHES / STEM_ELEMENTS / BRANCH_ELEMENTS / SHENG_CYCLE / KE_CYCLE /
HE_PAIRS / CHONG_PAIRS / BREAK_PAIRS / TOMB_MAP / ADVANCE_PAIRS / RETREAT_PAIRS /
NAJIA_BRANCHES / HEXAGRAM_TRIGRAMS / EIGHT_PALACES，共 15 张表；
三个源文件里的 **38 处本地副本全部删除**（含 `thinking_chain` 的 `BRANCHES` 别名副本）。
`liuyao_engine.py` 4042 → 3670 行，`classical_analysis.py` 4318 → 4200 行，
`thinking_chain.py` 6396 → 6150 行。

搬动前用 `scratch/dup_table_audit.py` 逐条目比对取值：**14 张表三份完全一致**，合一无行为风险。

### 顺带修掉的两个真问题

1. **EIGHT_PALACES 三份不一致**：`thinking_chain` 副本把兑宫世次排错——
   `蹇(四世) 小过(五世) 归妹(游魂) 谦(归魂)`，正法为
   `蹇(四世) 谦(五世) 小过(游魂) 归妹(归魂)`。今天只有 `order[0]` 被读到，故是**潜伏缺陷**：
   一旦有人用这张表判游魂/归魂，兑宫 谦/小过/归妹 三卦的世应就会错。已统一取 engine 副本。
2. **`get_palace_first_hexagram` 的兼容分支写反了**：
   原逻辑 `if not data and not name.endswith("宫"): try name + "宫"` —— 传入 `"兑宫"` 时
   永远不会去查带宫后缀的键。现由 `symbols.palace_of_key()` 归一化，`"艮"` 与 `"艮宫"` 都能查到。

### 护栏

新增 `tools/golden.py`：64 卦 × 3 种爻型 × 3 个时刻（含立春边界内外与夜子时）共 288 例，
对四柱、六爻纳甲六亲六神、世应、旬空、变卦、用神、旺衰、verdict、评分、应期候选、
22 个分析段输出做全字段指纹。本次重构前后**指纹完全一致**
（`147d57e8d06b0418`），证明是纯结构搬动、无判断漂移。

`python tools/golden.py capture|verify` 今后是任何引擎改动的第二道门。

## M0.5 / M0.6 工程底座（2026-09-22）

- **`tools/check.py`** 一条命令跑六个质量门（历法自检 / 段落冒烟 / 思维链用例 / 古籍回归 /
  tune / holdout）。前两项必须全绿；后四项按**只准前进不准后退**的基线比较，
  基线即本次实测值（chain 7/12、regression 10/18、tune 97.1、holdout 86.2），
  改进后用 `--raise` 抬高。全部通过才退出码 0。
- **`coverage_test.py` 更名 `smoke_test.py`**：它验的是"各分析段有没有产出"，
  与代码覆盖率无关，报"Coverage 100%"属误导性命名。改为"产出率"并说明它不是正确性指标；
  门槛由 90% 改为 100%（少一段即响）。
- **`thinking_chain_tests.py` 从 0/12 修回 7/12**：此前全FAIL 不是用例期望过期，
  而是测试自己读错了层级——`run_thinking_chain()` 返回补全后的整份结果，
  五步链在 `"thinking_chain"` 子键下，测试直接按步骤名取值于是全部拿到空 dict。
  剩 5 例是真实分歧（吉凶区间、动变净效应），留作 M2 的靶子。
- **退出码**：`regression_test.py` 原先无论过不过都退出 0，现按通过数决定；三个测试脚本
  统一由 `tools/check.py` 调度。
- **Windows 控制台**：新增 `yishu_core.runtime.force_utf8_stdio()`，
  engine / mcp_server / 三个测试 / evaluate / calendar_check 入口全部接入。
  此前中文输出在 GBK 控制台乱码，`✓/✗` 与"※"直接抛 UnicodeEncodeError。
- 新增 `pyproject.toml`（无必需依赖；lunar-python/matplotlib 列为可选 extras）与 `README.md`。
- 回归报告默认输出目录由 `scripts/` 改为 `outputs/`（生成物不再污染源码目录）。
- 删除 `liuyao_engine.py` 中两处从不生效的 `king_wen_sequence` 静默 import（前一条提交已记）。

## M0.2 / M0.3 唯一评分器与真基线（2026-09-22）


**新增** `scripts/evaluate.py`（唯一评分入口）与 `scripts/case_runner.py`
（由 `run_blind_v5.py` 更名重写，去掉 CLI 手解 `sys.argv` 与占位日期）。**删除** `scripts/score.py`
（与已丢失的 `blind_eval_split.py` 重复，且读的是引擎根本不输出的字段
`yingqi_summary`/`composite_score`，读不到即送分）。

### 真基线（首次可复现；两集合分别出分，n 为样本量）

| 集合 | strict | legacy | n |
|---|---|---|---|
| tune（ZS001–020，参与过调参） | **97.1%** | 98.0% | 20 |
| holdout（HO001–012，未参与调参） | **86.2%** | 86.9% | 12 |

维度分解（strict）：

| 维度 | tune | holdout |
|---|---|---|
| 用神六亲 | 100% | 91.7% |
| 用神地支 | 100%（4 例基准未记 → N/A） | 91.7% |
| 用神爻位 | 基准全无记录 → 该维度不参与 | 同 |
| 吉凶方向 | 95% | 75.0% |
| 格局覆盖 | 100% | 91.7% |
| 应期 | 95% | 83.3% |

### 最重要的一条：应期分是假的

引擎声明的"重点应期"平均列出 **11.1/12** 个地支；随机列同样多候选即全覆盖的期望是
**92.6%**（tune）/ **91.7%**（holdout），而召回打分是 95%/83.3%。
换句话：**旧口径下"应期 100%"与瞎蒙的差距不到 3 个百分点。**
真正有区分度的两个指标：top-1 命中 11.8%（tune，随机基线 8.3%）、基准应支平均排在第
4.69 位（12 支中）。**结论：应期目前不具备判断力，M2.2 是这一轮的主战场。**

### 口径变化明细

- strict：基准未记录的维度记 N/A 并从**分母**剔除；应期只认引擎自己声明的重点应期
  （不再把"依据"整句里顺带出现的地支算作命中）；取消应期 8/15 保底；用神爻位不再白送 5 分。
- legacy：逐条复刻 2026-09-20 之前 `blind_eval_split.py` 的口径（N/A 按满分、应期有保底、
  全文匹配），使历史 100% 可复现、可对照。**两个数同时打印，差值即口径水分。**
- 权重单一真值源：`evaluate.py::WEIGHTS`（六亲15/支10/位5/吉凶40/格局15/应期15）。
  案例文件里的 `scoring` 权重块（0.4/0.3/0.2/0.1，各例还不一致）从未被任何代码读取，属死数据，
  留待 M1 一并清理。

### 评测输入去伪

案例通常只记"巳月戊戌日占求财"。旧管线一律塞进 **2024-06-01 10 时**，并用
`"甲" + 月支` / `"甲" + 日支` 造干支串——旬空取决于日柱所在旬，"甲X"几乎必错
（丙辰日被写成甲辰日，旬空由子丑变成寅卯），应期日历日期也全落在假日期上。
现在由 `gc.find_solar_date()` 反查满足该月令与该日柱的**真实公历日期**，
32/32 例还原成功、0 例报错。古籍未记时辰者按 12 时并标 `hour_assumed`（不再假装 10 时）。

## M0.4 历法内核（2026-09-22）


**新增** `core/yishu_core/`：`ganzhi_calendar.py`（太阳视黄经求十二节交节时刻 → 定月令、
以立春定年界、以儒略日定日柱）、`calendar_check.py`（16 项自检，全绿）、
`runtime.py`（Windows GBK 控制台 UTF-8 适配）。

**修掉四个真实错误**（此前依赖是否安装而表现不同）：

| # | 缺陷 | 影响（实测 2020-01-01…2026-12-31，2557 天） |
|---|---|---|
| 1 | 未装 lunar-python/sxtwl 时 `get_year_stem_branch` **完全不判立春** | 年柱错 **236 天**（约 9.4%，全在 1 月—立春前）。时间起卦/梅花以年支取数 → 卦本身会起错 |
| 2 | 月支用固定近似日（Feb 4 交立春等） | 月建错 **44 天**（1.7%）。月建是旺衰第一权，直接改变用神强弱判定 |
| 3 | 五鼠遁写作 `(start + branch) % 12` 再判 ≥10 减 10 | 戊/癸日辰时之后时柱错（如戊日辰时 甲辰 → 应为 丙辰） |
| 4 | `handle_zi_hour` 在 `hour == 0` 返回**翌日**日柱 | 00:00–00:59 起卦者日辰整体后移一天，且早/夜子时命名颠倒 |

**删除**：`SOLAR_TERM_DATES` 近似表及其 fallback 分支、`liuyao_engine` 顶部已失效的
lunar-python/sxtwl 探测块、两处 `from king_wen_sequence import ...`（模块已不存在却被
`except ImportError: pass` 静默吞掉，从不生效；原文留在 `scratch/legacy_eval/` 备查，
恢复与否待用户定）。

**行为变更**：无。默认交节口径 `boundary="day"`（交节当日即换月/换年），与旧近似表一致；
精确到时刻走 `boundary="instant"`（可用环境变量 `YI_GANZHI_BOUNDARY` 切换）。
夜子时默认不作次日，采换日派需显式 `--zi-hour-type late`。

**指标影响**：以上 1、2 会改变既有案例的月建/年柱，故此前所有分数（tune 100%、holdout 97.7%）
自本条起**作废**，待 M0.2/M0.3 重建评分器后重测真基线。

## M0.1 仓库卫生（2026-09-22）

生成物（`outputs/`、`logs/`、盲评中间产物、报告 HTML）出库；删除 55 个 `_debug_*/_patch_*`
与已被取代的 v2–v5 盲评/补丁脚本；旧评分器另存 `scratch/legacy_eval/` 作重写参照。
