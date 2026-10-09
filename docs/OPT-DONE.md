# 已落实优化项台账（2026-10-07）

> 本文件记录 318 条 OPT（`docs/OPT-LEDGER.md` 表内实数，见该文件顶部口径横幅；
> 本文原写「319 条」与两处行数打架，已订正）中**已逐条实测并落实**的条目。判定口径见各条说明；
> 每条落实后单独跑 `tools/eval.py` 与 `tools/check_source_readings.py`，全库读数持续与基线一致（零回归）。
> 剩余待办见 `docs/source-readings/INDEX.md`。

> **计数与覆盖面（2026-10-09 实测登记，不改历史条目）**：
> - 本文件表内**只有 7 行**（`grep -c "^| OPT-" docs/OPT-DONE.md` = 7），
>   是 `docs/OPT-LEDGER.md` §一「已落实」29 行的**摘录**，**不是**已落实项的全集；
>   把这 7 行当全集会低估落实面。
> - 已落实项的**机器可读全集**是 `data/sources/opt_status.json` 的 `done` 数组，现值 **115** 条；
>   本文件 7 行全部落在这 115 条内（实测：7/7 命中 `done`，0 命中 `archived`／`rejected`）。
>   三者是**包含关系**（7 ⊂ §一 29 ⊂ done 115），不是三个可互相换算的读数。
> - 本文件 7 行的落点**全部现存**（六爻 6 行涉《卜筮全书》《卜筮正宗》《易林补遗》《易隐》4 部、
>   命科 1 行涉《滴天髓闡微》1 部，均在 `works_registry.json` 现登记的 27 部之内），
>   故无「已随两科收缩删除」标注；§一 里那 11 条已删落点见 `docs/OPT-LEDGER.md`。

| OPT ID | 原优先级 | 落实内容 |
|---|---|---|
| OPT-bushi_quanshu_dz-01 | P1 | 暗动口径双源并注（并填补registry"暗动定义正文缺书源"缺口） |
| OPT-bushi_quanshu_dz-02 | P1 | 神煞歌例使用审计（final_score 12项无神煞，旁参不进主分） |
| OPT-bushi_zhengzong_dz-02 | P1 | fanyin_fuyin locator补行号+provenance登记伏吟章缺段 |
| OPT-bushi_zhengzong_dz-03 | P1 | 重复块登记（推翻"逐字全同"，定位圆神/圆通神讹字并存） |
| OPT-ditian_sui_chanwei_dz-01 | P1 | 新增滴天髓任注本分支7条判据+撤销"原书未入库"失效前提 |
| OPT-yilin_buyi_dz-01 | P1 | 坟墓族新增已葬/安葬/下葬/伏尸→官鬼（书L368用神反转二分） |
| OPT-yiin_dz-02 | P1 | 伏飞四态补《易隐》原词与出处（引擎五态早已落地） |
