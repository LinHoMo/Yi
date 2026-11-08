#!/usr/bin/env node
/**
 * 交付包排除名单 —— 单一真源（第五百三十九批）。
 *
 * 为什么单独一个文件：`build.mjs` 用它排除 `scripts/` 下的评测入口，
 * `selftest.mjs` 的 [2] 段又拿同名清单验「产物里没有这些文件」。539 批前两边各存
 * 一份手工清单（与 528 批 G11 的双份门号表同型）——改一边忘另一边，构建与自检
 * 照样全绿。仿 `kb-docs.mjs` 的登记表范式抽成第三处真源，两处 import 同一份。
 *
 * **名单语义（521 批后已变，勿按旧注释理解）**：356/359 批把两科评测实现迁到
 * `eval/` 时，`scripts/` 下留过同名兼容 shim；521 批已把这些 shim **全部删除**。
 * 因此本名单现在不是「排除现存文件」，而是**防复活哨兵**：若日后有人把评测入口
 * 放回 `scripts/`，构建会自动把它挡在包外，[2] 段同步验产物里没有它——
 * 因为交付包不含 `eval/`，带上就会 `import eval` 失败。
 *
 * 改本文件 = 改交付口径：同批登记 `plugins/CHANGELOG.md` 并跑
 * `node plugins/scripts/build.mjs && node plugins/scripts/selftest.mjs`。
 */
export const DEV_ONLY = {
  liuyao: ['evaluate.py', 'case_runner.py', 'build_portal_assets.py'],
  bazi: ['evaluate.py'],
}
