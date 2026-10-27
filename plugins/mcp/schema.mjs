/**
 * 参数 schema 转译：dsh 简写 → MCP 的 JSON Schema。
 *
 * 为什么需要这一层：两科插件的 1.0 冻结契约（`dsh-plugin/CHANGELOG.md` 277 批）
 * 冻结的是**工具名、参数集与输出 value 结构**，不是某一家的 schema 方言。
 * dsh 侧用 `{type, required, description, enum}` 简写，MCP 要的是标准 JSON Schema
 * `{type:'object', properties, required}`。本模块做**唯一一处**转译，
 * 让 `tools.mjs` 里的工具定义在两个宿主上保持逐字同源（不复制第二份定义）。
 *
 * 约定（转译规则显式，便于自检逐条断言）：
 *  · 属性上的 `required: true` **不进** properties（它不是 JSON Schema 关键字），
 *    改为收进顶层的 `required` 数组；
 *  · `description` / `enum` 原样保留；
 *  · 缺失 `type` 视为 `string`（引擎侧命令行参数最终都是字符串化，保守取 string）；
 *  · `additionalProperties` 显式为 `true`：模型偶发多给一个键时，多余键被忽略而不是
 *    让整次调用以「参数不符合 schema」失败——工具面以可用为先，参数集本身由
 *    `required` 与 `enum` 把关。
 */
/**
 * @param {Record<string, {type?: string, required?: boolean, description?: string, enum?: string[]}>} parameters
 * @returns {{ type: 'object', properties: Record<string, object>, required: string[], additionalProperties: boolean }}
 */
export function toJsonSchema(parameters = {}) {
  const properties = {}
  const required = []
  for (const [name, spec] of Object.entries(parameters ?? {})) {
    const out = { type: spec?.type ?? 'string' }
    if (spec?.description) out.description = spec.description
    if (Array.isArray(spec?.enum) && spec.enum.length) out.enum = spec.enum
    properties[name] = out
    if (spec?.required === true) required.push(name)
  }
  return { type: 'object', properties, required, additionalProperties: true }
}
