/**
 * 随包判据知识库的**登记表**（全仓唯一真源，构建与自检共用）。
 *
 * 497 批起只保留 DSH 一个宿主（claude/codex/gemini/yan 已删除），
 * 此表是全仓唯一一份登记表真源。
 *
 * 每一篇必须登记「什么时候读」：构建时生成 `references/INDEX.md`，
 * 自检时双向对账（漏登记 / 登记了不存在的文件 → 判红）。
 *
 * 539 批两条口径：① 描述里的**篇目规模/格局数等会变的数字不得手钉**
 * （`najia_rules.md` 的 KB 数、`pattern_reference.md` 的格局数都曾与正文分家；
 * INDEX.md 的文件大小由 `build.mjs` 现场算，是真值源）；本表原写「十二大」
 * 而正文标题是「六爻十五大经典格局参考」、DOCS.md 也写十五大，本批按正文更正。
 * ② 改描述＝改随包知识库的导览口径，同批跑 build + selftest 并登记 CHANGELOG。
 * ③ 541 批补：同一条规矩也适用于技能正文真源 `plugins/SKILL.md`——539 批清掉了
 *    手钉的「47KB」，却漏掉相邻一行「8KB，短」（当时实盘确为 8KB，但仍是会变的数）。
 *    541 批把该行也改为回指 `references/INDEX.md`，至此真源与登记表都不再钉篇目大小。
 *
 * **552 批：解析契约（新增条目必读）**。本表是唯一真源，两个消费者的读法不同——
 * `build.mjs` 直接 `import` 本模块（JS 真相）；`outreach/build_outreach.py` 按行解析，
 * 且是 **fail-closed**：块内每一非空、非注释行都必须是单行
 * `['<科>/<篇>.md', '<描述>']` 字面量（单引号、一条一行），认不出即带行号判红。
 * 旧版用全文件宽松正则，双引号或换行的条目会被**静默跳过**，对外层少一篇而四门全绿。
 * 因此：新增条目照现有格式一行一条；描述里不要出现竖线或换行（会撑坏对外表格）；
 * 两科篇目不得同名（对外层按 basename 展示）。`--check` 另把 Python 解析结果与本表
 * `import` 出的 `KB_DOC` 逐条比对，两侧不一致即红。
 */
export const KB_DOC = new Map([
  ['liuyao/najia_rules.md', '需要核对纳甲装卦规则：八宫次序、纳支口诀、世应定位、六亲六神推演、旬空'],
  ['liuyao/interpretation_guide.md', '需要查用神取法、旺衰体系、动变规则、应期推断'],
  ['liuyao/pattern_reference.md', '判断十五大经典格局（先查这篇，短且直接可用）'],
  ['liuyao/classical_synthesis.md', '需要理论深度：四经典综合、虚空月破墓绝刑冲'],
  ['liuyao/source_ledger.md', '需要确认某条判据的书源出处'],
  ['liuyao/odd_questions.md', '奇问杂占（失联寻宠、怪梦、异象"有没有东西"、越界提问）：取到用神之后怎么读、什么不该答'],
  ['bazi/bazi_shishen_terminology.md', '十神术语释义'],
  ['bazi/bazi_nayin_shiyi.md', '纳音释义'],
  ['bazi/bazi_yue_shi_ge.md', '需要核对推月推时：五虎遁（年上起月）、五鼠遁（日上起时）歌诀与引擎对源'],
  ['bazi/bazi_tiaohou.md', '需要取用神的气候一路（调候）：某月某日干先取什么、次取什么，及调候的边界'],
  ['bazi/bazi_liuqin_gongwei.md', '问父母/配偶/子女/家人关系、家庭氛围：宫位与星双参，含不断生死与不数人数的边界'],
  ['bazi/bazi_jibing_tizhi.md', '问体质、身体哪一路要留心：五行配脏腑、虚实、取伤重，含不诊断的硬边界'],
  ['bazi/bazi_qianshi_yanpan.md', '用户问"你先说我以前"、或出生时辰不确定要校盘：定时辰与已过往运反推'],
  ['bazi/api_spec.md', '八字模块接口速查'],
])
