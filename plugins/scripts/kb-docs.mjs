/**
 * 随包判据知识库的**登记表**（全仓唯一真源，构建与自检共用）。
 *
 * 497 批起只保留 DSH 一个宿主（claude/codex/gemini/yan 已删除），
 * 此表是全仓唯一一份登记表真源。
 *
 * 每一篇必须登记「什么时候读」：构建时生成 `references/INDEX.md`，
 * 自检时双向对账（漏登记 / 登记了不存在的文件 → 判红）。
 */
export const KB_DOC = new Map([
  ['liuyao/najia_rules.md', '需要核对纳甲装卦规则：八宫次序、纳支口诀、世应定位、六亲六神推演、旬空'],
  ['liuyao/interpretation_guide.md', '需要查用神取法、旺衰体系、动变规则、应期推断'],
  ['liuyao/pattern_reference.md', '判断十二大经典格局（先查这篇，短且直接可用）'],
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
