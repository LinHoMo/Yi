# 六爻科 P0 静默缺陷盘点（2026-10-14 第一百七十四批）

> 目标：对两科做一次**全新** P0 静默全盲缺陷盘点（不依赖旧清单记忆），并对「用化用」
> 补做书载真例检索。结论：两科**已无活动性 P0 静默全盲**；仅固化一处潜在二次迭代隐患；
> 「用化用」仍无「用爻自化出之爻代用而验」真例，维持诚实登记。

## 一、复检范围与四类 P0 签名

| 类 | 签名（静默全盲模式） | 判据出处 | 复检手段 |
|----|----------------------|----------|----------|
| A | list 直接插进正则字符类（`[%s] % 列表`，未 `join`）→ 正则永不命中且无报错 | AGENTS.md §二 内核契约 / 166批 | grep 全部 `re.compile`、`%s` 拼接 |
| B | `Path.glob()` 真值误用 / 生成器被二次迭代（「扫了 0 份 ≠ 没文档」） | AGENTS.md §四.8 | grep `glob(`/`rglob(` + 逐处读消费次数 |
| C | 门内 `except` 静默吞异常 → coverage 造假（门绿但没真跑） | AGENTS.md §四.8 / CHANGELOG L1069 | 抽查 3 处 gate except 站点 |
| D | 新挂门无负例自证（恒绿门＝盲门） | AGENTS.md §四.8 | 列全部 27 门是否含 selftest/负例 |

## 二、逐类结果

### A 类（list-in-regex）—— 0 命中（全绿）
- 两科所有由 `HEAVENLY_STEMS`/`EARTHLY_BRANCHES`（list）构造正则处，均用 `"".join(...)` 展平：
  `liuyao/scripts/case_runner.py:55-56`、`build_yingqi_set.py:67`、`evaluate.py:59`、
  `check_case_selfconsistency.py:46-47`、`build_zengshan_dz_cases.py:91/95/97/135/137/138`、
  `bazi/dev_tools/check_pillar_laws.py`、`check_dayun_cases.py`、`audit_tiaohou_gap.py` 等。
- 166批命名的历史缺陷已无残留。

### B 类（glob 真值/二次迭代）—— 1 处潜在隐患，已固化
- 全树 `glob(`/`rglob(` 共 37 处，无 `if glob(...)` / `while glob(...)` 真值误用（B 类真值签名 0 命中）。
- **唯一隐患**：`liuyao/dev_tools/build_zengshan_dz_cases.py:76` 曾把
  `CASES_GLOB = (...).glob("*_cases.json")` 的**生成器**赋给模块全局，仅 L595 单次消费
  ——今日不报错，但若日后追加第二次扫描会**静默返回空**（即 §四.8 的「扫 0 份 ≠ 没文档」）。
- **本批已固化**：改为 `list(...)`；固化前/后 `--dry-run` 分段块数均为 **192**，rc=0，行为零变化。

### C 类（门内静默吞异常）—— 抽查 3 处均自报/跳过瞬时文件，无 coverage 造假
- `liuyao/dev_tools/check_source_readings.py:127`：provenance 解析失败 → `continue`（跳过单个坏文件，但其 title 缺失会使该底本在后续映射里落空并被判红，非静默吞绿）。
- `liuyao/dev_tools/check_doc_refs.py:108`：单个文档读不出 → `continue`（跳过瞬时不可读文件；该文件若为真实文档会在别处 doc-refs 路径校验暴露，非 coverage 造假）。
- `liuyao/dev_tools/check_rule_registry.py:152`：quote JSON 非法 → `problems.append(...)` 并 `continue`（**显式报错**，非静默）。
- 历史上的静默降级（`except Exception: witness = None`）已在 CHANGELOG L1069 取消。

### D 类（无负例自证门）—— 0 门（全绿）
- 两科共 **27** 门（liuyao 13 + bazi 14），**全部**含 `--selftest` 或 `负例` 自证逻辑：
  liuyao：`check_bing_yao / check_case_isolation / check_case_selfconsistency / check_cli_encoding /
  check_doc_refs / check_fangwei / check_fixture_invariants / check_rule_registry /
  check_source_readings / check_split_ledger / check_verdict_coherence / check_yingqi_information /
  check_yingqi_scoring`；bazi：同类 14 门齐备。
- 恒绿盲门风险已闭环。

## 三、「用化用」书载真例复检（并行子项）

- 检索 `liuyao/data/sources/*.dz.txt` / `*.wikitext.txt` 中「用化用 / 化出…验 / 用爻自化…验」。
- 命中点逐条定性：
  - `huangjince_dz.dz.txt:179-181`、`zengshan_buyi_dz.dz.txt:1639`（野鹤曰「此论非理…非也当删」）
    ——均为**注疏/评驳**，非「用爻自化出之爻代用而验」的占验实例；
  - `bushi_zhengzong_dz.dz.txt:2556/2574/3175/3504`、`zengshan_buyi_dz.dz.txt:539/2562` 等
    ——均为「化出**原神/忌神/财/墓**…应验」，机制与「化出之爻**代用神**」不同；
  - 未找到任何一条「占…得…卦，且**用爻自化出之爻代用神并应验**」的完整真例。
- ⇒ `qianjin_fu_map.json` 第39条「用化用」维持 **未实现 / 诚实登记不实施**（§四.3 前置＝书载真例仍缺）。本批未改其状态。

## 四、结论

- 两科**无活动性 P0 静默全盲缺陷**；A/D 类全绿、C 类抽查无 coverage 造假、B 类唯一隐患已固化。
- 本批仅做**一处防御性固化**（glob 生成器 → list），零引擎行为改动，故两科门禁读数不动属预期（§四.7）。
- 「用化用」仍诚实阻塞，等待书载真例，不强行实现。
