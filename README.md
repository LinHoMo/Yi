# 易（Yi）

> 六爻纳甲与八字四柱的**确定性排盘引擎**。本仓库作**云端备份**用：保留完整源码、数据、
> 判据与质量门，clone 后可离线运行；不提供在线服务、不发布插件、不承载协作
> （GitHub Issues / PR 仅作备份与留档用途）。

## 目录

| 路径 | 内容 |
|---|---|
| `liuyao/` | 六爻纳甲：`engine/` 推演、`rules/` 规则、`data/` 数据、`references/` 判据、`eval/` 评测、`dev_tools/` 门、`tests/` |
| `bazi/` | 八字四柱：同上结构 |
| `kernel/` | 两科共用内核的**唯一真源**（同步生成各科 `core/yishu_core/`） |
| `devkit/` | 门禁内核：`shared/` 共享门真源（分发到各科 `dev_tools/`） |
| `AGENTS.md` | 三条铁律与目录/依赖契约（改代码前必读） |
| `CONTRACT.md` | 四段契约 `chart → analyze → narrate → render` 的判据本体 |
| `CAPABILITY.md` | 能力边界与全部读数（每行带集合名、n 与出处） |

两科相互独立、零耦合，不存在合参层。各科 `core/` 与 `dev_tools/` 里的共享件是**生成产物**：
改内核改 `kernel/`，改共享门改 `devkit/shared/`，再跑同步脚本，不要手改产物。

## 快速校验

```bash
python liuyao/dev_tools/check.py     # 六爻质量门
python bazi/dev_tools/check.py       # 八字质量门
python -m pytest -q                  # 全仓测试
```

可选：`python kernel/sync_kernel.py --check`、`python devkit/sync_devkit.py --check`
（验证生成物与真源逐字节一致）。

## 口径

机械运算（起局、装卦、纳甲、世应、六亲、六神、旬空、旺衰、应期、格局）**只能由代码产生**，
语言模型只做解释；案例库与解读物理隔离；所有分数都是**古籍案例对齐分**（回归审计用），
**不是现实命中率**，现实侧样本为 0。现实预测不可测、不声称；医疗、法律、投资、重大决策
请以专业意见为准。
