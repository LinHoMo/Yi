/**
 * 随包判据知识库的**登记表**（全仓唯一真源，构建与自检共用）。
 *
 * 305 批前，这份表在 `dsh-plugin/scripts/build-skills.mjs` 与
 * `yan-plugin/scripts/kb-docs.mjs` 各存一份，靠 yan 侧自检 [2.4] 机械对拍防漂移——
 * **那是补丁，不是解法**：两份真源迟早会分叉，而门只能事后报警。
 * 现在合成一份，对拍门随之删除。
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
  ['bazi/bazi_shishen_terminology.md', '十神术语释义'],
  ['bazi/bazi_nayin_shiyi.md', '纳音释义'],
  ['bazi/bazi_yue_shi_ge.md', '月支与格局'],
  ['bazi/api_spec.md', '八字模块接口速查'],
])
