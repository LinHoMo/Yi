# gemini-plugin · Yi 术数的 Gemini CLI 扩展

把 [Yi](https://github.com/LinHoMo/Yi) 的两科术数引擎（六爻纳甲、八字四柱）包装成
**Gemini CLI 扩展**（`gemini-extension.json`）。装了即用：模型直接调
`yi_liuyao` / `yi_bazi` / `yi_kb` / `yi_report`。本机需有 **Python 3.10+**
（引擎是 Python）与 node（MCP 入口）。

> 口径提醒：一切分数都是**古籍案例对齐分**，不是现实命中率。它是排盘与推演参考工具，
> 不是预言；重大决策以专业意见为准。

## 结构

```
gemini-plugin/
├── gemini-extension.json   # 扩展清单（入库；mcpServers 用 ${extensionPath}）
├── GEMINI.md               # 上下文文件（入库；安装后作为入口说明注入）
├── README.md / CHANGELOG.md / LICENSE
├── skills/  src/  engine/  # 构建产物（由 plugins/scripts/build.mjs 分发）
```

**与其他宿主的差异**：Gemini CLI 没有 `skills/` 发现机制，入口说明走 `contextFileName`
（本扩展指向 `GEMINI.md`）。知识库仍随包分发在 `skills/yi-divination/references/`，
靠 `yi_kb` 定位后再读文件——这条差异已写进技能附加段与自检断言。

## 安装

```bash
node plugins/scripts/build.mjs
gemini extensions install ./gemini-plugin      # 本地安装（会复制一份）
gemini extensions link ./gemini-plugin         # 或软链，改代码即时生效（开发用）
```

> 从 GitHub 装（`gemini extensions install <url>`）需要产物已提交；
> 本仓库 `engine/`、`skills/`、`src/` 不入库，故 **GitHub 直装目前拿不到可用包**——
> 与其他宿主同一个限制，见 `plugins/CHANGELOG.md`。

## 已知边界

- **未在真机 Gemini CLI 里安装验证**（本机无该宿主）；断言是复刻其官方扩展规范的机械检查。
- `name` 需与扩展目录同名（本扩展为 `gemini-plugin`）。
- 需要 Python 与 node；找不到 Python 时工具如实报错并列出尝试过的路径。
- 完全离线：零网络请求、零凭据读取。
