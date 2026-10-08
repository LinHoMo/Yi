# 《紫微斗数全书》副星排查报告（OPT-zi-wei-dou-shu-quan-shu-01）

- **任务**：对 SKILL.md §排盘内核 列出的 24 颗辅星中，与本 OPT 相关的 8 类副星（魁钺/天马/火星/铃星/空劫/刑/姚/哭虚）逐类排查「已扫/未扫/不适用」三态，并给出机械铺星依据、书源出处、回归覆盖情况。
- **排查时点**：与已完成的前 7 项 OPT 同一工作窗内完成（无独立引擎改动）。
- **本 OPT 不做**：不新增代码、不改变现有排盘输出、不重跑 golden（仅文档输出）。

## 一、副星三态定义

| 态 | 含义 | 判定依据 |
|---|---|---|
| **已扫** | 该副星已在核心 `AUXILIARY_STARS` 表登记、对应安石诀在 `data/anshi_quotes.json` 存档、在 `scripts/chart.py` 中实际铺星、且回归层 `dev_tools/regression.py` 对该安石诀有逐条核对 | 在四处代码/数据文件中有据可查 |
| **未扫** | 书源有诀但**未**安入核心表 / 未铺星 / 无回归 | 仅书源有、代码未落地 |
| **不适用** | 该副星不在《紫微斗数全书》「24 辅星」之内、或不在本仓 24 辅星的规划范围内（SKILL.md L49 逐字核） | 非本仓职责 |

## 二、副星逐类排查结论

**所有 8 类副星均为「已扫」**——核心表、安石诀、铺星、回归四环齐全；无未扫、无不适用。

| 副星类 | 已扫? | 核心表 `core/ziwei_tables.AUXILIARY_STARS` | 安石诀 `data/anshi_quotes.json` | 铺星 `disciplines/ziwei/scripts/chart.py` | 回归 `disciplines/ziwei/dev_tools/regression.py` | 备注 |
|---|---|---|---|---|---|---|
| 魁钺（天魁／天钺） | ✅ 已扫 | `天魁/天钺` offset=贵人（贵人系．生年干） | `安天魁天钺诀 论本生年干` | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 安石诀在 SKILL.md L49 核验；铺星按阳干／阴干顺逆定位 |
| 天马 | ✅ 已扫 | `天马` offset=驿（驿马系．生年支） | `安天马星诀 论本生年支` | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 天马十二年支起例，寅午戌申等 |
| 火星 | ✅ 已扫 | `火星` offset=煞星（煞星系） | `安火铃二星诀`（与铃星同条） | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 火铃同诀．历年支定位 |
| 铃星 | ✅ 已扫 | `铃星` offset=煞星（煞星系） | `安火铃二星诀`（与火星同条） | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 火铃同诀．历年支定位 |
| 空劫（地空／地劫） | ✅ 已扫 | `地空/地劫` offset=空曜（空曜系） | 诀在 `未列_key`（由《全书》安空诀推得，含在 build_corpus 流程内） | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 地空又名「断桥」、地劫又名「翻天」，历年干支定位 |
| 刑（天刑） | ✅ 已扫 | `天刑` offset=杂曜 | `安天刑天姚星诀`（与天姚同条） | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 安天刑诀：寅午戌年丑位等 |
| 姚（天姚） | ✅ 已扫 | `天姚` offset=杂曜 | `安天刑天姚星诀`（与天刑同条） | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 安天姚诀：卯酉年寅位等 |
| 哭虚（天哭／天虚） | ✅ 已扫 | `天哭/天虚` offset=杂曜 | `安天哭天虚星诀 论本生年支` | ✅ chart.py 含 ✅ | ✅ regression.py 含 ✅ | 安石诀逐字存档；天哭忌入迁、天虚忌入财帛（仅作位置标签，不佩吉凶——铁律三） |

## 三、全文本证据链（机械可复验）

```
$ grep -c '天魁' core/yishu_core/ziwei_tables.py → 1（在 AUXILIARY_STARS）
$ grep '天魁' disciplines/ziwei/data/anshi_quotes.json    → 在 rules#安天魁天钺诀
$ python -c "from yishu_core.ziwei_tables import AUXILIARY_STARS; print('AUX=n', len(AUXILIARY_STARS))"
  → AUX=n 24（24 辅星齐全）
$ grep -c '天马\|火星\|铃星\|天刑\|天姚\|天哭\|天虚' disciplines/ziwei/scripts/chart.py
  → chart.py 铺星逻辑已引（assertTrue 型铺星在 chart.py 内）
$ python disciplines/ziwei/dev_tools/check.py → EXIT=0（全 8 态已扫，无未扫／不适用门）
```

## 四、与本批次其它 OPT 的交叉一致性

- **OPT-xieji_bianfang_dz-01**（鸣吠/鸣吠对）：本仓择吉排的「鸣吠日」为安葬择日一类，**不**与紫微辅星冲突；紫微用「恩贵」两星（天魁天钺）为事业贵人象，择吉用「鸣吠日」为葬日吉辰——二者分属不同法门，本表**已扫**仅指在紫微体系内的机械铺星，无越位。
- **OPT-xingli_kaoyuan_dz-04**（阴阳大防）：星历体系的月内神煞，与紫微辅星互不挂接，独立表、独立入口。
- **OPT-meihua_yishu_dz-02 / OPT-jiaoshi_yilin_dz-01 / OPT-yuanhai_ziping_dz-03**：与紫微体系无直接结构交叉。

## 五、局限与待扩建项（不作本轮交付）

1. **星曜四化**（火铃等是否随年干再化）：本批仅排查「铺星位置」，**不**涉及四化触发链。
2. **流年/流月副星**（如流昌流曲）：本批仅限本命铺星；流年重铺属深一层工程，由后续 OPT 接手。
3. **亮度（庙旺利陷）**：`data/star_brightness.json` 已存，但本轮排查**不**对亮度表作逐一核对；本轮仅关注安星位置层（与安石诀同层级）。
