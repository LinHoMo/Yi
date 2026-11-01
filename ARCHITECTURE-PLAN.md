# 易（Yi）· 架构整改完成记录

> **本文件是什么**：原 `ARCHITECTURE-PLAN.md`（25 张 TODO 卡的总方案）在第三百四十批
> **压缩成完成记录**——25 张卡已全部执行并验收，已修好的问题描述、逐卡步骤与派发提示词
> 不再留在正文里（它们已经变成历史，不是现状）。逐卡细节、负例输出与实测读数仍在
> `liuyao/docs/CHANGELOG.md`／`bazi/docs/CHANGELOG.md`／`plugins/CHANGELOG.md` 的
> 331–339 批，以及 `devkit/handoff/`（gitignore，27 份交接报告）。
>
> **派发件已删除**：`DISPATCH.md`（提示词 A／B 的唯一真源）随 340 批删除——26 个位全部
> 执行完毕，留着它只会让人以为还有任务可领。
>
> **效力**：与 `AGENTS.md`／`CONTRACT.md` 冲突时以那两份为准。本文件不写分数、
> 不写准确率（AGENTS.md §一.3）。

---

## 一、三个决策（2026-10-29 拍板，执行结果与决策一致）

| 决策 | 内容 | 落地结果 |
|---|---|---|
| **D1 = C** | 两科 `core/yishu_core/` 维持入库；CI 强制 `kernel/sync_kernel.py --check`；core 标 `linguist-generated`；新增 `--standalone <科>` | `.gitattributes` 已标；CI `kernel-sync` job 已挂；`--standalone` 实测可拷走并 `--help` rc=0 |
| **D2 = 复制分发** | `devkit/shared` 走 `sync_devkit.py --write/--check`，不用 import | 12 个共享件＋4 个变体分发两科（433 批新增 check_source_provenance）；`[37]` 字节比对门已挂 |
| **D3 = 中档** | 八字做到"受同等审计"，不克隆六爻 `step1–step5` 与 9 个 `classical_enhancements_*` | 八字补 `tests/`＋`[38]`；CHANGELOG 三件套；CONTRACT §六 八字审计 0 条新增欠账 |

## 二、最终形态（2026-10-29 收口实测）

```
Yi/
├── 根 7 份治理 md：AGENTS.md / CONTRACT.md / README.md / CAPABILITY.md /
│                   GOVERNANCE.md / DOCS.md / ARCHITECTURE-PLAN.md（本文件）
├── devkit/                     # 门禁内核真源（331–334 批）
│   ├── MANIFEST.json           # 12 共享件 + 4 变体 + 9 门编号
│   ├── sync_devkit.py          # --write / --check / --selftest
│   ├── shared/                 # 8 个单源 + variants/ 4 个学科专属实现
│   ├── root/                   # check_root_docs / check_docs_index / check_batch_num（不分发）
│   ├── pending/                # 登记暂存区（A2-B 合入 DOCS 后已空）
│   └── handoff/                # 27 份交接报告（gitignore，不入库）
├── kernel/                     # 引擎内核真源：common + variants（316 批起）
├── liuyao/                     # 六爻：core（产物）+ scripts + dev_tools + tests + data/cache
├── bazi/                       # 八字：core（产物）+ scripts + dev_tools + tests + data/cache
├── plugins/                    # 共享打包层（SKILL.md + mcp/ + scripts/）
├── 5 个宿主适配器              # dsh / claude / codex / gemini / yan
└── .github/workflows/ci.yml    # 六 job（361 批新增 min-python-smoke）：
                                #   root-gates / min-python-smoke / kernel-sync /
                                #   gates / ledger / plugin-gates
```

依赖方向（四条硬约束均已机检）：

```
kernel/  ─sync_kernel──▶  <科>/core/yishu_core   （产物，[35] 字节比对）
devkit/  ─sync_devkit──▶  <科>/dev_tools         （产物，[37] 字节比对）
<科>/scripts ─build.mjs─▶ plugins/engine/ ──▶ 5 宿主 src/（产物，不入库）
两科之间零 import、零跨科写（AGENTS.md §二）
```

## 三、完成台账（27 份 handoff 在 `devkit/handoff/`）

| 卡 | 批次 | 提交（短 hash） |
|---|---|---|
| A0-0 | 331 | `96ddd2b` |
| A0-1 | 331 | `209cd24` |
| A0-2 | 331 | `b8bbfbb` |
| A0-3 | 331 | `7f38f4c` |
| A0-5 | 331 | `fe7b5bd` |
| A0-4 | 331 | `623a05f` |
| A1-1-01/02/03 | 334 | `a1e68f2` |
| A1-1-04…11 | 332–334 | `377252f` |
| A1-2 / A1-3 | 334 | `7b5ffd7` |
| A2-A | 335 | `fe4f831` |
| A2-B | 336 | `83133a7` |
| A3-1 | 337 | `07880d8` |
| A3-2 | 337 | `28fd659` |
| A4-CI | 338 | `be60113` |
| A4-2 | 338 | `226531c` |
| A5-1 / A6-INT | 339 | `029d0a4` |
| 文档压缩（删 DISPATCH、本文件瘦身） | 340 | 本批提交 |

## 四、验收总账 V1–V15（收口实跑）

| # | 验收项 | 实测 |
|---|---|---|
| V1 | 两科门禁不低于基线 | `python liuyao/dev_tools/check.py` rc=0；`python bazi/dev_tools/check.py` rc=0 |
| V2 | 分发面不漂移 | `node plugins/scripts/build.mjs` + `selftest.mjs` rc=0（7 段全绿） |
| V3 | 根级文档无悬空引用 | `python devkit/root/check_root_docs.py` rc=0（7 份根级 md、0 死链；负例已做） |
| V4 | 文档索引对账 | `python devkit/root/check_docs_index.py` rc=0（51 份全部登记可达） |
| V5 | 门禁单一真源 | `python devkit/sync_devkit.py --check` rc=0（12 共享件 × 2 科；6 类负例） |
| V6 | 内核单一真源 | `python kernel/sync_kernel.py --check` rc=0（17/15 文件＋4 变体；CI `kernel-sync`） |
| V7 | 契约三件套同步 | 340 批未改键面/禁边；两科 `check_layer_contract.py --selftest` rc=0 |
| V8 | 两科形状对称 | 八字 `tests/`（smoke+regression）、CHANGELOG 三件套、CONTRACT §六 审计表在册 |
| V9 | CI 六 job | `root-gates` / `min-python-smoke`（361 批新增，声明最低版 3.10 的两科冒烟）/ `kernel-sync` / `gates` / `ledger`（344 批新增，full 账台）/ `plugin-gates`（五宿主 × 2 OS），无 `continue-on-error` |
| V10 | 门禁档位在册 | `governance_map.py --strict` rc=0（两科未分类 0；不降不删已具名） |
| V11 | 口径 | `selftest.mjs` [7] 段禁语扫描全绿；全部文字用"古籍案例对齐分/非预测命中率" |
| V12 | 登记 × 提交 | `readout_ledger.py --quick` rc=0（bad=0；收口时 39 项，344 批起 40 项；full bad=0/40，含"登记×提交在册"） |
| V13 | 并发合规 | 单 Agent 串行（偏差见 §五）；外部三命通会 327–329 批 6 路径已于 345 批补交；handoff 未入库 |
| V14 | handoff 齐备 | 27 份报告齐备，含实测输出片段 |
| V15 | 集成后全链 | 每批收口均跑两科 `check.py`＋`sync_devkit`＋`kernel`，最终 rc 全 0 |

## 五、执行偏差与已知欠账（诚实登记）

1. **单 Agent 串行**替代 25 条 `arch/*` worktree：没有分支合并链，改为主工作区逐批提交；
   每卡仍按批次号与独占写域落盘。外部三命通会会话的 7 个路径全程只读。
2. **A1-1 的 4 个逻辑不同项**（`check_source_readings`／`golden`／`baselines`／`feedback_store`）
   按 kernel 变体范式登记，而不是硬合成一份——理由见 `devkit/MANIFEST.json` 的
   `variant_reasons`。`files.shared` 仍为 11 项。
3. **A1-1-06** 以六爻 HEAD（已含 collation 豁免）为归并源；八字侧工作区改动等价落库，
   未替外部会话提交其它文件。
4. **A4-CI 实跑额外修复**：DSH `src/index.mjs` 只按 LF 找 frontmatter 定界，Windows CRLF
   工作树下解析失败——已修为读取端归一（`dsh-plugin/CHANGELOG.md` 具名）。
5. **已关闭（346 批）**：`devkit/root/check_batch_num.py` 已实现并挂进 CI `root-gates`；
   它从 `readout_ledger.py` 的 `SETTLED_ORPHANS` 单源读取允许名单（AST），不另抄一份；
   原「门未就位先记欠账」句已删除，不再是现状。
6. **未决外部项已关闭（345 批）**：三命通会会话的 6 个路径（3 modified + 3 untracked）
   已随 327–329 批补交入库；不再是未决项。

## 六、显式不做的事（原方案 §八，保留编号供引用）

1. **不合并两科**——零耦合是设计目标，不是待修的重复（AGENTS.md §二）。
2. **不复活 `synthesis` 合参层**——已移除且不得复活。
3. **不克隆六爻的推演链到八字**——形状对称 ≠ 规模对称（D3 中档）。
4. **不回填六爻门编号的 9 个空号**——墓碑不复用，新门从 `[37]` 续。
5. **不归并 `check.py` 与 `__init__.py`**——前者是各科编排器（本应不同），后者差异仅 docstring。
6. **不删两科 `scripts/` 下的四段同名入口**——那是契约要求的形状重复。
7. **不把两科 `core/` 加进 `.gitignore`**——D1=C。
8. **不把 `devkit/shared` 改成 import 共享**——会破坏单目录独立性（D2）。
9. **不为整洁而合并六份 CHANGELOG**——A4-2 已评估，结论维持现状。
10. **不改四段契约本体与三条铁律**——只动治理覆盖面，不动被治理的对象。
11. **不追求"门禁行数下降"这个数字本身**——瘦身判据是"门还在守什么"（GOVERNANCE 五档）。
12. **不触碰外部三命通会会话占用的 7 个路径**。
