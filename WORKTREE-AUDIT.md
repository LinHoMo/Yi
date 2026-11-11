# 历史 worktree 清点与可回流项裁决（552 批）

> **本文件是什么**：对 `git worktree list` 里 8 个历史对拍工作树的一次性清点——
> 逐个核对它们停在哪个提交、工作区是否干净、内容是否已在主线、里面还有没有值得
> 回流到 `main` 的改进点。**结论先行：8 个全部是 `main` 的祖先，零独有提交、
> 零脏改动，无需任何补丁回流；3 项残留（1 份被删审计、1 个 stash、3 条旧分支）
> 已逐条裁决，均为「不回」并给出理由。**
>
> 状态：**归档留证**。结论入 `liuyao/docs/CHANGELOG.md` 第 552 批；本文件不再更新
> （下次清点另立批次），`REPO-HYGIENE.md` §四 的删除判据以本文实测为依据。

## 一、怎么核的（可复现）

| 判据 | 命令 | 通过标准 |
|---|---|---|
| 是否有独有提交 | `git rev-list --count main..<rev>` | 0 = 内容全在主线 |
| 工作区是否干净 | `git -C <path> status --porcelain` | 空 = 没有未提交改动 |
| 是否藏了暂存 | `git stash list` | 仅 `stash@{2026-10-14}`（仓库级，非 worktree 私有） |
| 内容是否真在主线 | 对每个快照末次提交的 `+` 行抽最长探针，`git grep -F` 扫 `main` 树 | 命中或能指明后续迁移/改写 |
| 引用是否过期 | `git worktree prune --dry-run -v` | 空 = 8 条注册都指向现存目录 |

实测（2026-11-11）：8 个 worktree 的 `ahead` 全为 0、`status` 全空、`prune` 无候选；
每个约 21 MB，合计约 168 MB，全部位于系统临时目录，不占仓库体积。

## 二、逐个结论

| worktree | 停在 | 日期 | 内容主题 | 主线归宿 | 裁决 |
|---|---|---|---|---|---|
| `w_356115f` | `356115f` | 11-03 | T29 设计：verdict 拆段渐进式方案 ＋ T30 完成/T31 前两步状态更新（只改 `RULE-ENGINE-REFACTOR-PLAN.md`） | 该文档仍在，510 批降为「结案记录」；T29 落成 `liuyao/engine/pipeline/step5.py` 的 `present_verdict`/`rescue_verdict` 键 | 已吸收，方案细目按 510 决策删除，正文在 git 历史 |
| `w_961528c` | `961528c` | 11-02 | D4：ZD017 开铺面用神取妻财 ＋ 鬼持世不抬吉（艮之明夷） | `liuyao/rules/rule_engine.py` 保留「铺/店/门面」开店经营族谓词；登记数据迁入 `data/rules/domain/` | 已吸收 |
| `w_9f497de` | `9f497de` | 11-03 | REFACTOR-PLAN：T29 三批全部完成标记（1 行） | 同上，510 批结案记录覆盖 | 已吸收 |
| `w_pre501` | `c818a46` | 11-02 | 第 500 批 ZD214 建器串味修册：expected 应期从错配的坎之井改回离之旅 | `zengshan_dz_cases.json` 的 ZD214 现为「寅日云、卯日大雨、辰日大晴」并带 498 批修正注记（后续批次再校） | 已吸收且有后续修订 |
| `yi43` | `43dfde6` | 11-03 | 文档收口：CHANGELOG 138→10 批（319KB→约 8KB） | 现为 15 批窗口 ＋ 历史索引（510／523／544 批三次收紧） | 已被更严口径取代 |
| `yi505` | `8b37efb` | 11-03 | 505 批：D2 `data/rules/` 分区 ＋ D4 classical_enhancements 族收编（64 文件，纯搬迁） | 现落 `liuyao/engine/classical/`（508 批二次升格） | 已吸收且已二次迁移 |
| `yi506` | `6101072` | 11-04 | 506 批：D3 step1~5 迁 `engine/pipeline` ＋ `engine.py` 折叠为 `_core` | `liuyao/engine/pipeline/` 十件齐全，`_core.py`、`__main__.py` 均在（`python -m engine` 可用） | 已吸收 |
| `yi506b` | `41986c7` | 11-04 | 506 批补登记 ＋ 分区后文档路径收口（纯文档，11 文件） | 路径又随 508 升格回改（`liuyao/SKILL.md` 现写 `cd <skill-path> && python -m engine`） | 已吸收且路径已更新 |

抽查方法举例：`yi506` 快照里 57 条探针有 28 条能在 `main` 直接检索到，其余 29 条全部
指向后来被改写/搬迁的语句（如 `scripts/engine/pipeline/` → `engine/pipeline/`、
`cd <skill-path>/scripts && python -m engine` → `cd <skill-path> && python -m engine`），
逐条都能点名归宿，**没有一条是「主线丢了」**。

## 三、可回流项逐条裁决

### A. `docs/C2_classical_enhancements_audit.md`（961528c 快照在册，**已删除**，提交 `2d8ee3f`）

- **内容**：为什么不把 `classical_enhancements.py`（90KB/1910 行）硬迁进 `registry_v2` 的
  `score_delta`，列了 3 处真改分点（绝处逢生 `analyze_desperate_relief`、三合格破局
  `analyze_triple_combo`、`effects.py` 的 `score_modifier`）及其消费方与行号。
- **裁决：不回流正文。** 505 批已把整族搬进 `engine/classical/`——不是「不迁」，而是
  「整族搬走」，该文的核心结论已被后续决策取代；把作废结论搬回来会误导读者。
- **可保留的部分**：那 3 个改分点仍是排查分值归属的线索。本文登记这一条，等于给
  将来「分数为什么变」的排查留了指路，不必再把被删文档恢复成活文档。

### B. stash `slim-down-wip`（2026-10-14，7 文件，+94/−5207）

- **内容**：删 `liuyao/docs/CASE-LIBRARY-AUDIT-YINGQI.md`（−48 行）、CHANGELOG 大瘦身
  （−5234 行）、`qianjin_fu_map.json`／`rule_registry.json`／`evaluate.py` 小改。
- **主线现状**：那份审计文档**仍在册**（stash 的删除从未落地）；`qianjin_fu_map.json`
  与 `rule_registry.json` 已迁 `data/rules/domain/`、原挂 `scripts/evaluate.py`，506 批已迁 `eval/`；
  CHANGELOG 精简已由 510／523 批按另一形态完成。
- **裁决：不回流，stash 可丢。** 六个文件没有一个是「主线缺、stash 有」。

### C. 分支 `feat/internal-depth-pack`（75 提交，2026-09-27，与 main 无 merge base）

- **内容**：219 个 `main` 没有的路径，主体是扁平化前的 `disciplines/meihua/**`（梅花，
  四科布局）、`docs/samples/*.html` 与旧 `core/yishu_core/`。
- **裁决：不回流。** 166 批重建后本仓只保留两科，梅花已正式移除且不预留目录；
  这个分支是**另一种架构形态**，不是「同一形态下的改进」。
- **已执行（2026-11-12）**：实测 `git merge-base --is-ancestor` 表明它的 75 个提交**已是**
  `history/pre-squash-2026-10-09` 与 `backup/scope-reduction-9a61b25` 的祖先，删除分支不减少
  任何可达对象，故直接 `git branch -D`（未打额外 tag：两条备份分支已是副本）。
  另两条 `backup/scope-reduction-9a61b25`／`history/pre-squash-2026-10-09` 均 ahead 226，
  是 squash 前历史的**唯一副本**，删除会让这 226 个提交不可达——保留，不删。

## 四、回流到主线的**唯一**改动：删除判据

清点没产出代码补丁，但产出了一条可复用的判断规则，已写进 `REPO-HYGIENE.md` §四：
历史 worktree／分支从「一律需人工决定」细化为**三条可判定条件**——① `main..<rev>` 为 0；
② 工作区干净；③ 内容能在主线点名归宿（迁移/改写均可）。三条同时满足 → 标「可安全删」，
仍由人执行删除（本仓不自动删历史工作树）。

本次 8 个 worktree 三条全满足，**已于 2026-11-12 执行删除**：逐个 `git worktree remove`，无一需要 `--force`；`git worktree prune` 后 `git worktree list` 只剩 `main`，释放约 168 MB。8 个提交仍可用 `git cat-file -t <rev>` 解析（均为 `main` 祖先，删工作树不丢历史）；三条备份分支按 §三.C 保留未动。命令留档：

```bash
# 公共父目录按 `git worktree list` 实取（本次 8 个都在系统临时目录下）
WT_ROOT="<8 个工作树的公共父目录>"
for w in w_356115f w_961528c w_9f497de w_pre501 yi43 yi505 yi506 yi506b; do
  git worktree remove "$WT_ROOT/$w"
done
git worktree prune
```

以后再清同类工作树：先按上面三条判据复核，再执行；删除前如需留证，`git show <rev> > /tmp/<rev>.patch` 或 `git tag archive/<rev> <rev>`。
