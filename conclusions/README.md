# 结论库（conclusions/）

> **这一层是什么**：4 条**固定输入**的渲染结论 + 一个索引。只存**人能读、AI 能吃的 Markdown 报告**，
> **不存 JSON 快照**——JSON 按每条报告里的命令随时可逐字节重跑，存它只会多出不可读的 diff。
>
> 定位（555 批定）：它是「AI 可直接消费的产物」里的一环，不是主角。主角是整条
> `llms.txt → KNOWLEDGE.md → conclusions/INDEX.md` 链路；人审靠代码、契约与门禁。

## 目录

```
conclusions/
├── INDEX.md                 # 唯一入口：输入 → 报告 → 引擎输出 sha256
├── liuyao/<id>.md           # 六爻结论（渲染报告）
└── bazi/<id>.md             # 八字结论（渲染报告）
```

每份报告抬头固定写：学科、输入、复现命令、引擎输出 sha256、同源复验命令、口径脚注。
**没有 JSON 文件**——报告正文就是结论本身，JSON 只作为可重跑的中间产物。

## 生成与复验

```bash
python outreach/build_outreach.py --write    # 重生成 4 份报告 + 索引（连同 llms/KNOWLEDGE/kb.INDEX）
python outreach/build_outreach.py --check    # 逐字节复验（CI 挂此，漂移即红）
python outreach/build_outreach.py --selftest
```

新增一条：在 `outreach/build_outreach.py` 的 `CONCL_CASES` 加一行，跑 `--write`，同批登记 `CHANGELOG`。

## 覆盖范围（先读这一条）

只覆盖 `CONCL_CASES` 里的固定输入，**不是"任意时间、任意问题都能查"**。未收录的三种合规处理：

1. 本地跑引擎（命令见每条报告抬头），把输出贴给 AI；
2. 装 skills / DSH 插件，导出结构化报告；
3. 在 `CONCL_CASES` 加一条并重跑——这是"扩充库"的唯一方式。

**禁止**：拿 A 条的结论回答 B 条；用样例拼"新盘"；手改报告。

## 三条铁律怎么守

- **§一.1 机械运算归代码**：报告由引擎实跑后渲染；`--check` 逐字节比对，手改即红。
- **§一.2 案例库隔离**：输入全是新造中性问句（`示例：…`），构建器不读 `data/cases/`。
- **§一.3 口径诚实**：每份带"对齐分 ≠ 命中率、非预言、专业意见优先"脚注。

## 网页版 AI 怎么用

先读 `INDEX.md`：

1. 输入与某条**完全一致** → 读该条 `.md`，按五段格式转述，注明条目 ID 与 sha256 前 8 位；
2. 不完全一致 → 说"未收录"，给本地跑法；
3. 不得用库里的样例拼新盘。

协议全文见 `outreach/WEB-AI-PROMPT.md` 第七节。
