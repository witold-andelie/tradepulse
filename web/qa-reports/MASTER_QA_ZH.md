# TradePulse 十一种语言独立验收总报告

日期：2026-10-26（Asia/Shanghai）。**结论：可提交负责人技术审阅；不批准合并或发布。** 已授权的局部修复和本轮回归完成。十一语言各有独立报告、42 个实际页面组合和十二维评价，英语也未豁免语言审校。

## 版本、安全和授权范围

起点：`3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`。本地隔离修复分支：`b/global-i18n-acceptance-repairs-20261026`。最终提交：`cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`，工作树干净。

只修改 `web/` 的 23 个文件：新增 2、修改 21。无后端、契约、共享 fixture、API 客户端、金融 lib、依赖或已有单元测试变更。保留全部原有分支引用；未 push、建改 PR、合并或部署。

只读远端核对：原始功能分支仍为 `3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`；main 仍为 `c69e3d7642295b609f7db22c2079769d5d2e4b82`。main 尚无全局 `web/src/i18n` 功能。

本次依最新上传任务修复并本地提交；早先“只读审计”请求不代表本轮代码未更改。用户最新授权允许此隔离修复。报告、日志、截图和导出物保存在仓库外，不混入源代码提交。

## 十一种语言独立结论

技术 PASS 仅覆盖本轮 Chromium 技术检查，不能代替语法、自然度、金融编辑、真实发音、辅助技术或合并后验收。以下每种语言均为 **EDITORIAL REVIEW PENDING + DEVICE AUDIO TEST PENDING**。

| 语言 | 独立技术结果 | 标准矩阵 / 状态组 | 语言审校结果 | 独立报告 |
|---|---|---|---|---|
| en（英语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_en](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_en.md) |
| zh-CN（简体中文） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_zh-CN](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_zh-CN.md) |
| zh-TW（繁体中文） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_zh-TW](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_zh-TW.md) |
| es（西班牙语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 存在已确认的 Optional 单复数错误；其他母语审校待办 | [QA_es](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_es.md) |
| fr（法语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 存在已确认的 Optional 单复数错误；其他母语审校待办 | [QA_fr](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_fr.md) |
| de（德语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 存在已确认的 Optional 单复数错误；其他母语审校待办 | [QA_de](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_de.md) |
| pt-BR（巴西葡萄牙语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 存在已确认的 Optional 单复数错误；其他母语审校待办 | [QA_pt-BR](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_pt-BR.md) |
| ja（日语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_ja](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_ja.md) |
| ko（韩语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_ko](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_ko.md) |
| cs（捷克语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 存在已确认的 Optional 单复数错误；其他母语审校待办 | [QA_cs](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_cs.md) |
| ar（阿拉伯语） | TECHNICAL PASS（已测范围） | 42/42；16/16 | 母语与金融编辑待办 | [QA_ar](/workspace/work/tradepulse-full-locale-qa-20261026/reports/QA_ar.md) |

## 测试结果与证据

以下均在最终 cd2b610 的源树上重新执行，未以旧提交通过结果替代。命令、cwd、退出码和日志名完整记录于 [suite-exits.json](/workspace/work/tradepulse-full-locale-qa-20261026/verified-validation/suite-exits.json)。浏览器使用 `/usr/bin/chromium` 154.0.8037.57，fixture 预览端口 5215，API 模拟预览端口 5216；均为本地预览。

| 检查 | 结果 | 退出码 |
|---|---|---|
| `npm test` | 100/100；15 个测试文件 | 0 |
| `npm run check:contracts` | RunOutput fixture + 19 条 trace 全部合法 | 0 |
| `node scripts/check-i18n.cjs` | 601 个应用键 ×11；参数／非空一致；523 个显式 UI 调用位置 | 0 |
| `npm run build -- --outDir …/validation-dist --emptyOutDir` | 生产构建通过；独立输出目录 | 0 |
| `git diff HEAD^ HEAD --check`；另对完整基线至 HEAD 检查 | 均通过 | 0 |
| Original browser acceptance（Pro preload） | 17/17 | 0 |
| Simple/Pro redesign acceptance | 18/18 | 0 |
| Global i18n acceptance | 84/84 | 0 |
| API-state acceptance | 5/5 | 0 |
| 迁移后的 Agent research acceptance | 15/15；保留原有证据、财务、取消及键盘断言 | 0 |
| 既有 accessibility-check | 14 个路线／视图检查；记录的对比度、小目标、无名称控件失败均为 0 | 0 |
| 全语言矩阵 | 462/462 页面组合；另 11 组文字放大和 3 组控制台，共 476/476 组 | 0 |
| 每语言状态／失败／语音模拟 | 176/176（16×11） | 0 |
| 独立数据及展开内容校验 | 57/57 | 0 |
| 补充键盘／表格／符号几何／捷克计数 | 25/25 | 0 |
| 每语言 Factor Lab + 键盘表格额外探针 | 11/11；99 个 pool/status 选择 | 0 |
| 实际 ECharts tooltip 渲染 | 六类×11 =66/66；额外 detail 数值探针11/11 | 0 |

构建体积仍值得优化：本轮入口约 988.85 kB（gzip 351.28 kB），ChartEngine 约 627.87 kB；属于 Optional 性能事项，没有添加依赖。

浏览器命令为 `node web/scripts/browser-acceptance.cjs`（加 `--require ./web/scripts/pro-view-preload.cjs`）、`redesign-acceptance.cjs`、`global-i18n-acceptance.cjs`、`global-i18n-api-acceptance.cjs`、`agent-research-acceptance.cjs`、`accessibility-check.cjs`，均在仓库根目录以 `TRADEPULSE_PREVIEW_URL` 指向上述本地预览执行。新矩阵脚本命令为 `node web/scripts/full-locale-acceptance.cjs matrix`，分别以三个 locale 分组运行；状态命令为同脚本 `states`。环境已有 Playwright 通过 NODE_PATH 使用，未添加依赖。

## 实际图像审阅范围

十一语言 ×七路线 ×1440/768/320 ×Simple/Pro，共 462 个实际渲染组合。文件名为 `verified-matrix-{a,b,c}/cd2b610/<locale>/<route>/<width>/<mode>.png`；另存 `.full.png` 与 `.business.png`，窄屏 Pro 另有图表及语音面板。

**实际看图与仅生成图分开计数：** 已实际打开并审阅 77 张六案例业务视口拼图，覆盖 462 个业务视口；最终 cd2b610 的这 462 张业务视口与已审阅版本逐像素全部一致，因此继承的是精确图像审阅。另在最终提交直接打开 11 张 Discover 首屏拼图（66 个首屏）及 11 张六图表 tooltip 拼图（66 个图表），每种语言同样深度。

这属于 AI 图像审阅，拼图按显示分辨率检查；**未声称 462 张全页长图已逐像素、逐句由母语人工验收**。长页面深层证据另以展开 DOM、逐记录比较、图表和错误场景检查覆盖。无穷组合与浏览器／设备差异未穷尽。

[462 张逐像素核对](/workspace/work/tradepulse-full-locale-qa-20261026/verified-pixel-comparison.json)；[77 张实际业务图审阅记录](/workspace/work/tradepulse-full-locale-qa-20261026/final-reviewed-sheets.json)；[22 张最终直接图像审阅记录](/workspace/work/tradepulse-full-locale-qa-20261026/verified-extra-image-manifest.json)。每语言报告链接本语言的业务、首屏及 tooltip 图。

## 已复现并修复的问题

原提交证据：[I1–I3、U1、U2、O1 原始复现](/workspace/work/tradepulse-full-locale-qa-20261026/original-reproductions.json)；旧 Agent 脚本在原始提交为7/15（8组失败），完整日志保留于 `legacy-before/`。

| ID / 严重度 | 原提交复现与修复 | 最终位置 / 回归 |
|---|---|---|
| I1 / Important | ar→Pro榜单→行业表与shortlist，有符号值继承RTL。现以Canonical/BDI隔离，数值不变 | `web/src/pages/Leaderboard.jsx:74`、`:75`；实际Range几何和全语言数据校验 |
| I2 / Important | 切非英语后 regime 徽章 tone 取翻译字符串，退回 muted。现从原始enum取严重度 | `web/src/pages/Leaderboard.jsx:71`；11语言×3池样式一致 |
| I3 / Important | 展开业务表，region有名称但table无caption。现补本地化caption，保留既有caption及scope | `web/src/components/ui.jsx:54`；表可访问树及单测 |
| I4 / Important | 旧Agent脚本只认guide语言控件；8组失败。现迁移全局selector和pref，不削弱原有记录／控制断言 | `web/scripts/agent-research-acceptance.cjs:94`；最终15/15 |
| U1 / Important | detail指南标题至朗读面板相距约783px，没有邻近入口。现有可见按钮并移焦既有控制器，不自动播放 | `web/src/components/agentResearch/GuidedResearch.jsx:35`；11语言实际Tab/Enter |
| U2 / Important、设备验证仍开放 | 有界枚举重试、voiceschanged、脚本／地域匹配、手动刷新、声音数和安装限制提示；暂停引擎在显式Play时恢复 | `…/useReadAloud.js:16`、`…/speech.js`、`…/GuidedResearch.jsx:66`；模拟通过，真实Edge问题未宣称已彻底解决 |
| I5 / Important | Factor Lab快速连续改pool/status，旧URL更新丢一项，错误显示3或11卡而非crypto ACTIVE2卡；同步提交搜索参数 | `web/src/pages/Factors.jsx:19`；11语言快速筛选 +99组合 |
| I6 / Important | pt-BR Discover 768px、200%文字时按钮使页面宽约801px。允许收缩与换行后为768px | `web/src/index.css:258`；11语言七路线CSS文字放大 |
| I7 / Important | 仅summary给出弃权原因且没有failed-check明细时，旧帮助错误声称无具体原因。现保留原始summary并明确缺的是检查明细；不朗读源叙述 | `…/summary.js:10`、`…/GuidedResearch.jsx:41`、`…/messages.js`；11语言API场景+单测 |
| L1 / Important | ja/ko的elevated短标签可能被理解为行情上涨，改为明确警戒度／风险上升 | `web/src/i18n/locales/ja.json:94`、`ko.json:94`；enum未变 |
| L2 / Optional | cs主要计数标签避免固定词尾，de弃权短标签与ar命中率短标签澄清；不替代母语签字 | `web/src/i18n/locales/cs.json:549`、`de.json`、`ar.json`；cs0/1/2/4/5/21/100实际浏览器展示 |
| O1 / Optional | rich badge将文字节点分成flex项，英文stressed regime缺词间空格。增加内层普通span | `web/src/components/ui.jsx:19`；实际文本/样式及单测 |

## 仍开放的缺陷、限制和发布门槛

**Blocker（发布／合并门槛）：** 最新main与修复HEAD有12个文件冲突；多语言与仓库English-only规则的例外、共享前端变更及集成方案均需负责人批准。没有合并后集成测试，不能批准直接合并或发布。

**Important：** 全部11语言均缺独立母语金融编辑批准；真实Windows Edge声音枚举／安装与发音待验，不能宣称U2设备问题闭环。NVDA／VoiceOver、真实原生200%浏览器缩放尚未执行。API无真实后端服务，失败／缺失数据由明确标记的浏览器拦截模拟。

**Optional、已确认未修复 E-count-01：** es/fr/de/pt-BR/cs 的 Factor Lab `1d` tooltip 固定使用复数，分别为“1 días / 1 jours / 1 Tage / 1 dias / 1 dní”。正确单数候选为“1 día / 1 jour / 1 Tag / 1 dia / 1 den”。源：`web/src/i18n/locales/<locale>.json:169`；调用：`web/src/pages/Factors.jsx:35`。复现：切该语言→Factor Lab→Pro→悬停第一个1d柱。截图：`verified-tooltip-review/<locale>-factors.png`。这些语言报告的语法维度明确为FAIL，其他语言编辑维度仍待人审。最小后续修复可用单复数选择或统一技术单位d，须保留原值。此项不改变金融数值，也不作为全面语言通过隐藏。

其他Optional：es正式／非正式称呼不统一；fr不换行标点；de复合词硬断行；pt-BR200%放大下长词碎行；zh-TW/ja/ko的地区金融用词；cs单字母介词后不可断空格；ar长标签自然度；en专业词的普通用户理解。每种语言报告有自己的具体例句、文件位置和审校笔记。窄屏treemap和长轴标签有意省略，完整名称可通过tooltip及表格获取。

## 数据和 Agent 不变量

每种语言独立比较620条榜单（520美股+50ETF+50crypto）、30条解释，合计6,820条榜单呈现和330条解释呈现；另覆盖NO_CALL、缺解释、缺证据、未知资产及summary-only弃权。核对rank/score/tier/edge/alpha/coverage/return，以及verdict、claim状态、ID、哈希、source text、params、as_of和相关测量。语言切换不改算金融结果。

SYN369保持第4/520名、score1.3884（显示+1.39）、STRONG_OVERWEIGHT研究立场、abstained解释；最大贡献pv_mom_1m=0.779566。fixture JSON Pointer `/recommendations/3`、`/explanations/3`。

`exp-us_equity-syn369-c1`仍verified、`exp-us_equity-syn369-c2`仍rejected；证据ID `ev-exp-us_equity-syn369-1` / `…-2` 及两个SHA-256未变。两条factor_contributions / factor_value引用来自通用合成生成器，不证明供应链事件。`cause_before_move`缺实际事件日期和行情变动日期；as_of、run时间和trace时间不能填补它们。本次没有伪造日期或纠正共享fixture。

源位置：`contracts/fixtures/run_output.fixture.json`；生成器 `contracts/fixtures/make_fixtures.py:185`（通用factor引用），`:56`（ID派生哈希）。原始叙述仍以source边界呈现，不把其翻译或朗读成新证据。1,808 vs1,200计数、trace时间跨度与reported duration、regime记录来源的不一致保持披露。所有研究结果是SYNTHETIC，未验证真实投资表现。

数字、百分比、bp和ISO日期刻意保留B1源格式；这保证可比性，但并未实现每种语言的本地小数逗号／日期惯例，须由团队确认策略。

## 声音与无障碍证据边界

真实Chromium语音API存在，但声音数量为0；**未听到实际音频**。每种语言均独立模拟有效声音、无声音、仅中文声音、API不支持、延迟枚举及voiceschanged；测试Play/Pause/Resume/Stop、暂停后重新播放、报错、语言／路线切换取消和no-autoplay。模拟声音不是已安装声音，也不是发音接受证据。

zh-Hans-CN/zh-Hant-TW、pt-BR/pt-PT分离，es接受es-ES/es-MX；缺匹配声音时不悄悄换语言。真实Edge仅中文可能涉及OS语言包、浏览器服务或枚举时机，此环境不能确定其根因。

实际Tab/Enter、控件名称、table caption、header scope、RTL逻辑顺序、数值LTR隔离、减少动画及基础对比度检查通过。未运行NVDA/VoiceOver、axe或Lighthouse，未执行原生浏览器200%缩放；本轮200%是CSS文字放大。无WCAG认证声明。

## main 集成风险

仅以 `git merge-tree --write-tree` 检查对象，无分支／工作树合并；exit1表示发现冲突。具体证据：[12个冲突文件](/workspace/work/tradepulse-full-locale-qa-20261026/verified-main-conflicts.json)、[完整只读合并诊断](/workspace/work/tradepulse-full-locale-qa-20261026/verified-main-merge-tree.txt)。

需负责人逐项解决以下文件，同时保留main的数据、安全、CI、依赖及无障碍改动；不能把本分支较旧依赖直接覆盖main。

- `web/AGENT_ACCESSIBILITY_DEMO.md`
- `web/scripts/agent-research-acceptance.cjs`
- `web/src/App.jsx`
- `web/src/components/ResearchGuide.jsx`
- `web/src/components/agentResearch/GuidedResearch.jsx`
- `web/src/components/agentResearch/messages.js`
- `web/src/components/agentResearch/speech.js`
- `web/src/components/agentResearch/summary.js`
- `web/src/components/agentResearch/useReadAloud.js`
- `web/src/pages/Detail.jsx`
- `web/src/pages/Trace.jsx`
- `web/src/pages/TrackRecord.jsx`

## 文件变更、交接和证据位置

精确清单（均相对3d2ae4f）：

- `M	web/scripts/agent-research-acceptance.cjs`
- `A	web/scripts/full-locale-acceptance.cjs`
- `M	web/src/components/agentResearch/GuidedResearch.jsx`
- `A	web/src/components/agentResearch/acceptanceRepairs.test.js`
- `M	web/src/components/agentResearch/messages.js`
- `M	web/src/components/agentResearch/speech.js`
- `M	web/src/components/agentResearch/summary.js`
- `M	web/src/components/agentResearch/useReadAloud.js`
- `M	web/src/components/ui.jsx`
- `M	web/src/i18n/en.json`
- `M	web/src/i18n/locales/ar.json`
- `M	web/src/i18n/locales/cs.json`
- `M	web/src/i18n/locales/de.json`
- `M	web/src/i18n/locales/es.json`
- `M	web/src/i18n/locales/fr.json`
- `M	web/src/i18n/locales/ja.json`
- `M	web/src/i18n/locales/ko.json`
- `M	web/src/i18n/locales/pt-BR.json`
- `M	web/src/i18n/locales/zh-CN.json`
- `M	web/src/i18n/locales/zh-TW.json`
- `M	web/src/index.css`
- `M	web/src/pages/Factors.jsx`
- `M	web/src/pages/Leaderboard.jsx`

仓库外已生成完整binary unified patch和仅23个变更源文件ZIP。临时Git index从3d2ae4f载入，patch `--cached --check`、实际cached apply后write-tree与HEAD整个树完全相同，含两个新文件；检查未改真实工作树。无node_modules、build、cache、env、凭据文件；已执行常见凭据模式扫描，无命中（不作为绝对无泄漏认证）。

[修复patch](/workspace/work/tradepulse-full-locale-qa-20261026/acceptance-repairs-3d2ae4f-cd2b610.patch)；[仅变更源ZIP](/workspace/work/tradepulse-full-locale-qa-20261026/acceptance-repairs-changed-source.zip)；[SHA-256和干净应用验证](/workspace/work/tradepulse-full-locale-qa-20261026/handoff-verification.json)。这些是本任务本地文件链接，**不宣称已经上传成可下载附件或保存到GitHub**；当前工具没有通用附件上传能力。

复核证据根目录：`/workspace/work/tradepulse-full-locale-qa-20261026`。最终证据只认 `verified-*`；原始复现和中间失败保留供追溯。中间曾发现测试定位歧义及预览输出目录被重建引起404，已隔离不可变预览并重新执行最终提交；未把它们伪装为产品成功。

## 负责人审阅建议

建议现在审阅本地修复与十一份语言报告。合并前先解决12个集成冲突、确认多语言及源格式策略、完成母语金融编辑和目标设备语音／辅助技术检查，并修正E-count-01等明确文案缺陷后重跑受影响回归。所有当前可运行的强制技术套件通过；**不授予整体发布批准**。
