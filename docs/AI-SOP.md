# AI-SOP · 网页端 AI 取用 Yi 报告的标准操作手册

本手册写给**网页端 AI 助手**（能力假设：能读取公开网页/文本、能发 HTTP 请求、
能拼 URL；**不能**在用户机器上 clone 仓库或运行 Python）。照本手册操作，只需
"GitHub 仓库链接 + 起卦/排盘所需信息"，即可拿到 Yi 的分析报告（Markdown 与 HTML）。

仓库作者与维护者：把本文件与 `.github/workflows/report.yml`、`.github/workflows/pages.yml`
一并放在默认分支即可，无需自建服务器、无需托管密钥（GitHub 自动签发的
`GITHUB_TOKEN` 已够用）。

---

## 0. 一句话原理（先理解，再操作）

把流程拆成两半：

| 半场 | 是否需要凭证 | 说明 |
|---|---|---|
| **触发**（让某处跑起引擎） | **取决于通道** | 云端通道是写操作，需要 Token 或由人点一下链接；**纯前端通道零凭证**（浏览器内跑） |
| **读取**（取回报告） | **公开仓库完全不需要 Token** | 报告提交到 `reports` 分支，用 `raw.githubusercontent.com` 匿名 GET；issue 评论也可匿名读 |

**两条通道，按你手上的条件选**：

| 通道 | 触发 | 需要什么 | 适合谁 |
|---|---|---|---|
| **A. 纯前端页面**（GitHub Pages + Pyodide） | 拼一条**深链 URL**，用户点开即出报告 | 只要仓库链接；**零凭证、零后端、零人工触发** | 网页端 AI 的首选；用户不想登录 GitHub 时 |
| **B. 云端 Actions** | 预填 issue 链接（用户点提交）／`workflow_dispatch` API（需 Token） | 通道 A 之外：需要 GitHub 账号或 Token | 要**留档**、要把报告提交进仓库、要 issue 回评时 |

两条通道跑的是**同一份 Python 引擎、同一条四段契约**（`chart→analyze→render`），
产出同源；仓库根 `tools/verify_web_parity.py` 就是这条同源性的自动验收。

> 关键设计：云端报告**落进仓库文件（reports 分支）**，而不是只留在 Actions Artifact。
> Artifact 下载**必须登录**，不适合作为 AI 的主通道；它只保留为人工下载的补充。

---

## 1. 起卦/排盘需要哪些字段

不同学科必填项不同。字段名用英文，值里中文照写。

| 学科 `discipline` | 必填 | 常用可选 |
|---|---|---|
| `liuyao` 六爻 | `discipline`，`question`（所问之事） | `datetime`（给定则按时间起卦，格式 `YYYY-MM-DD HH:MM`；不给则随机摇钱）、`mode`（coin/time/number/manual）、`numbers`（数字起卦 `a,b,c`）、`yao`（manual 模式 6 个爻值 `7,8,9,7,6,8`）、`longitude` |
| `ming` 四柱八字 | `discipline`，`datetime`（出生公历 `YYYY-MM-DD HH:MM`），`gender`（男/女） | `longitude`（真太阳时）、`question` |
| `ziwei` 紫微斗数 | `discipline`，`datetime`，`gender` | `longitude` |
| `meihua` 梅花易数 | `discipline`，`question` | `datetime`（不给则用当前时间）、`way`（datetime/numbers/lunar/two_numbers/manual）、`numbers`（way=numbers 时按"年数,月数,日数"） |
| `xiaoliuren` 小六壬 | `discipline`，`question` | `datetime`、`way`（datetime/numbers/lunar/month_day_hour）、`numbers`、`activity`（事类）、`hour_branch`、`direction`（目标方位） |
| `zeji` 择吉 | `discipline`，`date`（`YYYY-MM-DD`，也接受 `2026/09/30`），`activity`（如 开市/嫁娶） | `question`、`hour_branch`（时支） |

> 一卦一事：同一问题不重复占卜；用户换实质角度（换用神、换层面、比较两人、
> 假设未来）应建议另起一次，不要在原报告里硬推。

> 表外取值会被**明确拒绝**（报错退非 0），不会静默改方式。若你给的 `way`/`mode`
> 不在上表，请照上表改正后重试，不要反复重发同一个请求。

---

## 2. 通道 A：纯前端页面（零凭证，推荐给纯网页 AI）

### 2.1 深链协议（你只需要会拼 URL）

页面地址（把 `{PAGES}` 换成仓库的 Pages 地址，如
`https://<owner>.github.io/<repo>/`）后面接查询参数：

| 短名 | 含义 | 例 |
|---|---|---|
| `d` | 学科（必填） | `liuyao` |
| `q` | 所问之事 | `占本周面试能否通过`（URL 编码） |
| `dt` | 起算/出生时间 | `2026-09-30 10:30` |
| `g` | 性别 | `男` / `女` |
| `mode` | 六爻起卦方式 | `time` / `coin` / `number` / `manual` |
| `way` | 梅花/小六壬方式 | `datetime` / `numbers` |
| `num` | 数字（逗号分隔） | `3,5,7` |
| `yao` | 六爻 manual 的 6 个爻值 | `7,8,9,7,6,8` |
| `date` | 择吉日期 | `2026-09-30` |
| `activity` | 事类 | `开市` |
| `yb` | 时支 | `酉` |
| `dir` | 目标方位 | `东` |
| `auto` | `1` = 打开即自动推演 | `1` |

**一条链接直接出报告**（六爻占求职）：

```
https://<owner>.github.io/<repo>/?d=liuyao&q=%E5%8D%A0%E6%9C%AC%E5%91%A8%E9%9D%A2%E8%AF%95&dt=2026-09-30%2010:30&mode=time&auto=1
```

把这条链接发给用户，用户点开即可看到报告（可在页面里下载 MD / HTML）。
用户也可以只把信息交给你、由你拼链接；**你不需要任何 Token**。

### 2.2 拼链接的注意点

- 所有值做**完整 URL 编码**（`encodeURIComponent` / `quote(v, safe="")`）；空格 `%20`，
  中文按 UTF-8 百分号编码。
- 时间里的空格必须编码（`2026-09-30%2010:30`），否则可能被截断。
- `auto=1` 会立刻开始推演；首次访问需在浏览器里下载 Python 运行时（约 10 MB，
  来自公开 CDN），之后同一浏览器走缓存。**不要**在用户没要求时无脑加 `auto=1`。
- 页面不上传任何输入，计算全在浏览器进程内。

### 2.3 页面不可用时的降级

若仓库未启用 Pages，改用通道 B；若两者都不可用，**不能**靠"AI 自己推算"产出盘面
（违反铁律一：机械运算归代码）。此时只能如实告知无法出盘。

---

## 3. 通道 B：云端 Actions

### 3.1 通道 B-1：预填 issue 链接（无 Token）

你只负责**拼出链接并交给用户**；用户点击 → GitHub 已替他填好标题与正文 →
用户按"Submit new issue" → 工作流自动运行 → 报告以**评论**形式回到该 issue，
同时存入 `reports` 分支。

issue 正文用 `字段: 值` 的行（也支持 ```json 代码块）。例如：

```
discipline: liuyao
question: 占买房子何时有结果
datetime: 2026-09-30 10:30
```

标题建议以 `[yi]` 开头（便于识别；正文里只要有 `discipline` 也能触发）。

拼法（基址 `https://github.com/{OWNER}/{REPO}/issues/new`，查询参数 `title`、`body`）：

```python
from urllib.parse import quote
title = "[yi] 六爻 · 占买房子何时有结果"
body  = "discipline: liuyao\nquestion: 占买房子何时有结果\ndatetime: 2026-09-30 10:30"
url = ("https://github.com/OWNER/REPO/issues/new?title=" + quote(title, safe="")
       + "&body=" + quote(body, safe=""))
print(url)
```

JavaScript：`"https://github.com/OWNER/REPO/issues/new?title=" + encodeURIComponent(title) + "&body=" + encodeURIComponent(body)`。

### 3.2 已在 issue 里的追加请求（评论触发）

让用户在已有 issue 下评论一行 `/yi` 命令即可复跑：

```
/yi discipline: ming
datetime: 1990-05-20 10:30
gender: 男
```

也支持同一行多组：`/yi discipline=liuyao question=占求财 mode=time`。

> **权限**：只有仓库 OWNER / MEMBER / COLLABORATOR 的 `/yi` 评论会被执行
> （公开仓库里任何人都能评论，不设限等于把 Actions 分钟与 bot 提交能力开放给全网）。
> 维护者可用仓库变量 `YI_ALLOW_ASSOCIATIONS` 放开名单。被拒时 `should_run=false`，
> 不会消耗 runner。

### 3.3 通道 B-2：workflow_dispatch API（需 Token，全程自动）

```
POST https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/report.yml/dispatches
```

请求体必含 `ref`（默认分支名，如 `main`），`inputs` 为字段对象：

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/report.yml/dispatches \
  -d '{"ref":"main","inputs":{
        "discipline":"liuyao",
        "question":"占买房子何时有结果",
        "datetime":"2026-09-30 10:30",
        "commit_branch":true}}'
```

- 成功通常返回 **204 No Content**（部分网关/版本为 200）。这一步**不直接返回 run id**。
- Token 权限：Fine-grained PAT 需 **Actions: Write**；Classic PAT 需 `repo` 作用域。
- ⚠️ **表单只有 10 个字段**（GitHub 对 `workflow_dispatch.inputs` 的硬上限），
  暴露的是 `discipline/question/datetime/gender/mode/way/numbers/date/activity/commit_branch`。
  `yao`、`hour_branch`、`direction`、`longitude` 等高级字段走 issue 正文或
  `repository_dispatch`（见 3.4）。
- PowerShell 发 curl 时引号易被改写：把 JSON 先存 `body.json`，再用 `-d "@body.json"`。

### 3.4 通道 B-3：repository_dispatch（需 Token，传结构化 JSON）

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{"event_type":"yi-report","client_payload":{
        "discipline":"ming","datetime":"1990-05-20 10:30","gender":"男"}}'
```

`event_type` 必须是 `yi-report`；`client_payload` 即字段对象（字段名同上表）。

---

## 4. 轮询与取回报告

### 4.1 固定链接：不需要 run id（**主通道**）

报告会同时写到两个位置：

```
reports/{discipline}/latest.md          ← 该科最近一次（URL 固定）
reports/{discipline}/latest.html
reports/{discipline}/{name}-{run_id}/report.md   ← 逐次留档
reports/index.json                      ← 各科最近一次的时间/run/相对路径
```

所以你**不需要**知道 run id：

```bash
BASE="https://raw.githubusercontent.com/OWNER/REPO/reports"
curl -s "$BASE/liuyao/latest.md"                 # 六爻最近一次报告
curl -s "$BASE/liuyao/latest.html" -o report.html
curl -s "$BASE/index.json"                       # 六科各自最近一次
```

`raw.githubusercontent.com` 是静态 CDN，**不占 REST API 额度**、无需 Token。
轮询技巧：先反复 GET `latest.md`（或 `index.json` 里的 `updated` 字段），
看到时间戳更新即说明本次已完成，比查 run 状态更省额度。

### 4.2 从 issue 评论匿名取回（通道 B-1）

```bash
curl -s "https://api.github.com/repos/OWNER/REPO/issues/{ISSUE_NUMBER}/comments"
```

评论内含固定链接、本次留档链接、Artifact 页面，并折叠内联了报告正文。公开仓库无需 Token。

### 4.3 查运行状态（需要时）

```bash
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/OWNER/REPO/actions/runs?per_page=5"
```

**退避策略**：未认证 REST 限流约 **60 次/小时·IP**，认证 5000 次/小时。
从 **15 秒**一次起、指数退避到 **60 秒**封顶。**不要每秒轮询**；能读 raw 就别读 API。

### 4.4 Artifact（需 Token，人工/备用）

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/runs/{RUN_ID}/artifacts
curl -sL -H "Authorization: Bearer $TOKEN" -o yi-report.zip \
  https://api.github.com/repos/OWNER/REPO/actions/artifacts/{ARTIFACT_ID}/zip
```

zip 内为 `report.md` + `report.html`；默认保留约 90 天。

---

## 5. 端到端最小范例

### 5.1 零凭证（通道 A）

1. 收集信息：六爻，问"占本周面试能否通过"，按给定时间起卦。
2. 拼深链：

```
{PAGES}/?d=liuyao&q=%E5%8D%A0%E6%9C%AC%E5%91%A8%E9%9D%A2%E8%AF%95&dt=2026-09-30%2010:30&mode=time&auto=1
```

3. 把链接给用户；用户点开即得报告，可下载 MD/HTML。

### 5.2 要留档（通道 B）

1. 拼预填 issue 链接并交给用户 → 用户提交。
2. 轮询 `GET .../issues/{n}/comments`（15–60 秒退避），直到出现"Yi 报告已生成"评论。
3. 或直接 GET `reports/{discipline}/latest.md`（看到 `updated` 变化即完成）。

---

## 6. 两条通道的能力边界（诚实口径）

| | 通道 A 纯前端 | 通道 B 云端 |
|---|---|---|
| 需要凭证 | 否 | 触发需要 Token，或由人点一次 issue 链接 |
| 需要后端 | 否（浏览器内跑） | 用 GitHub 提供的 runner |
| 首屏开销 | 首次约 10 MB 运行时（之后缓存） | 无（在云端跑） |
| 留档 | 用户自行下载 | 提交进 `reports` 分支，有固定链接 |
| 可否被 AI 匿名取回 | 报告在用户浏览器里 | 是（raw 固定链接） |
| 离线 | 运行时已缓存后可离线 | 否 |

**不存在**"AI 全程零凭证、零人工、纯 HTTP 让 GitHub 云端跑完并把报告递回"的组合——
触发半场的写操作这一前提无法绕过。但**纯前端通道把"零凭证出报告"变成了现实**：
引擎在浏览器里跑，不涉及任何触发写操作。

---

## 7. 错误码与降级

| 现象 | 含义 | 处理 |
|---|---|---|
| 页面提示"读不到 manifest.json" | 没经 HTTP 访问（直接双击本地文件） | 用 Pages 地址，或本机 `python tools/serve_web.py` |
| 页面报 `取文件失败 404` | 站点镜像不完整 | 维护者重跑 Pages 工作流 |
| 404（Actions） | 工作流不在默认分支 / 仓库私有 / 文件名错 | 核对分支与文件名 |
| 401 | Token 无效/过期 | 换 Token，或改走通道 A |
| 403 | Token 作用域不足，或触发限流 | 补 `Actions: Write`；读 `x-ratelimit-remaining` 后退避 |
| 422 | `inputs` 字段与工作流定义不符 | 对照 §1 字段名（注意表单只有 10 个字段） |
| `should_run=false` | 未识别 discipline，或评论者不在允许名单 | 检查请求写法 / 权限；维护者可设 `YI_ALLOW_ASSOCIATIONS` |
| 报告里报"表外取值" | `mode`/`way` 不在白名单 | 按 §1 表改正后重发 |
| Artifact 410 | 产物已过期 | 改读 `reports` 分支固定链接 |

---

## 8. 口径（AI 在转述报告时必须保持）

- 排盘、装卦、旺衰、应期、格局识别全部由代码完成，AI 不自行推算。
- 报告中的分数是**古籍案例对齐分**（回归审计用），**不是现实命中率**；
  不得说"预测准确率""断事如神"。
- 凶吉为**条件化倾向**（"偏向 / 有…信号 / 结构上"），不是"注定 / 一定 / 绝无可能"。
- 医疗、法律、投资及重大人生决策，提示以专业意见为准。
- 引用分数时必带：集合名 + 样本量 n + 是否参与调参。
