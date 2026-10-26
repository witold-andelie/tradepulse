# QA_ko — 韩语独立验收

日期：2026-10-26（Asia/Shanghai）。语言：`ko`。

本地修复分支：`b/global-i18n-acceptance-repairs-20261026`。最终 HEAD：`cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`。起点：`3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`。

应用修复提交：`cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`；最终 HEAD 包含本报告全部前端修复与验收脚本。`web/src` 树对象 `cf74e2f15b59e9a8dc5049c7ab96375324a6a762` 完全相同。矩阵、图像及 176 个状态场景均来自最终 HEAD。所有结果均为本轮新执行，未拿上一轮 3d2ae4f 的通过记录充当修复验收。

**独立语言结论：TECHNICAL PASS（已测浏览器技术范围）；EDITORIAL REVIEW PENDING；DEVICE AUDIO TEST PENDING。原生辅助技术验收仍待执行。不是该语言已全面发布批准。**

## 七路线与三宽度、双模式

| 页面 | 1440 Simple / Pro | 768 Simple / Pro | 320 Simple / Pro | 业务图像证据 |
|---|---|---|---|---|
| Discover | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-discover-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/discover` |
| Explore Markets / Leaderboard | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-leaderboard-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/leaderboard` |
| Ticker Detail / Agent Guide | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-detail-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/detail` |
| Factor Lab | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-factors-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/factors` |
| Market Regime | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-regime-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/regime` |
| Track Record | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-track-record-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/track-record` |
| Run Trace | PASS / PASS | PASS / PASS | PASS / PASS | [六案例图](/workspace/work/tradepulse-full-locale-qa-20261026/verified-business-review/ko-trace-six-cases.jpg)；原始截图目录 `verified-matrix-c/cd2b610/ko/trace` |

42 个组合均实际渲染并分别保存初始视口、全页与业务视口。77 张六案例业务图已经实际审阅；当前版本的 42 张业务视口与已审阅版本逐像素一致（逐个文件核对），不是单凭生成截图计作审阅。完整页面并未由母语人工逐像素签字，深层内容另有 DOM 检查与窄屏图表捕获。

本语言实际等价的展开 main 文本页面：/discover。其余页面的说明／指标／可视化密度可不同，底层记录没有改算。

额外直接图像复核：[Discover 六种首屏](/workspace/work/tradepulse-full-locale-qa-20261026/verified-header-review/ko.jpg)；[六类图表实际 tooltip](/workspace/work/tradepulse-full-locale-qa-20261026/verified-tooltip-sheets/ko.jpg)。本语言两张图均实际打开审阅；这不是音频或母语编辑验收。

## 十二个接受维度

| 维度 | 状态 | 理由与证据 |
|---|---|---|
| 翻译完整性 | **PASS** | 601 个应用键＋52 个兼容指南键均非空、参数一致；七路线实际渲染，无精确已登记英文 UI 残留。原始来源叙述、技术代码、bp 和 ISO 日期显式保留。 |
| 语法正确性 | **NEEDS HUMAN REVIEW** | 已对本语言独立进行 AI 文案检查；es/fr/de/pt-BR/cs 存在 E-count-01 固定复数错误（Optional），见复现与截图。所有语言均没有独立母语审稿人签字。 |
| 自然度与受众理解 | **NEEDS HUMAN REVIEW** | 检查导航、长解释、错误恢复及语音提示；真实受众理解和母语自然度不能由模型签完全接受。 |
| 金融术语准确性 | **NEEDS HUMAN REVIEW** | 逐项核对 research stance、expected/realized、coverage/confidence、NO_CALL/abstained 等边界；行业编辑仍须确认本语言术语。 |
| 金融与风险语义忠实度 | **NEEDS HUMAN REVIEW** | 技术字段／枚举／合成警告保持，未发现指令或收益方向翻转；完整语言层面的专业接受仍待母语金融编辑。 |
| 数值、百分比、日期、单位惯例 | **NEEDS HUMAN REVIEW** | 源值技术校验 PASS；有意沿用 B1 的 ASCII 有符号数值、小数点、bp、百分数及 ISO 日期，不宣称已采用本地小数／日期惯例。团队需确认这项源格式策略。 |
| 字形、标点和断行 | **NEEDS HUMAN REVIEW** | 三宽度、双模式业务截图已逐例审阅；未发现遮挡／缺字；紧凑图块会截断标签，完整名称在提示／表格。出版级标点和自然断词仍属编辑待审。 |
| 桌面、平板、手机和缩放 | **NEEDS HUMAN REVIEW** | 42/42 标准宽度场景 PASS；本语言七路线 200% CSS 文字放大 PASS。原生浏览器 200% 缩放 NOT TESTED，不能用 CSS 模拟冒充。 |
| 导航、交互与偏好持久化 | **PASS** | 独立初始载入、刷新、跨路由、Simple/Pro、搜索／筛选保留、空结果与恢复通过；全局选择器立即可用。 |
| 无障碍、键盘与读屏语义 | **NEEDS HUMAN REVIEW** | 语义／表格 caption／col scope／有名称控件、实际 Tab 顺序及 Enter 入口等技术检查 PASS。NVDA／VoiceOver／原生读屏和 axe／Lighthouse 未执行，不作 WCAG 认证。 |
| 语音可用性、控制与发音 | **NOT TESTED** | 真实声音／发音未测：本机 Chromium API 存在，原生声音列表为空，未听到音频。有效声音、缺声音、仅中文声音、延迟枚举及控制／取消均用明确标记的浏览器 API double 测试 PASS。 |
| Agent 与金融底层数据保持 | **PASS** | 本语言逐行比较 620 条榜单记录、30 条解释；原始 claim／verdict／ID／哈希／params／as_of 和金融值保持；SYN369 仍 abstained。 |

## 实际审阅的术语与 UI 例句

| 源键 | 本语言界面文本 | 精确源位置 |
|---|---|---|
| `Research stance` | 리서치 관점 | [ko.json:365](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:365) |
| `Factor Lab` | 요인 연구실 | [ko.json:139](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:139) |
| `Expected alpha` | 예상 알파 | [ko.json:119](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:119) |
| `Hit rate` | 적중률 | [ko.json:165](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:165) |
| `abstained` | 판단 보류 | [ko.json:536](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:536) |
| `Market Regime` | 시장 상태 | [ko.json:218](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:218) |
| `Coverage` | 커버리지 | [ko.json:70](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:70) |
| `Benchmark` | 벤치마크 | [ko.json:44](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:44) |
| `No call` | 판단 없음 | [ko.json:250](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:250) |
| `Strong overweight` | 강한 비중확대 리서치 관점 | [ko.json:444](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:444) |
| `Drawdown threshold / horizon` | 낙폭 임계값 / 기간 | [ko.json:92](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:92) |
| `Elevated lift` | 위험도 상승 상태 리프트 비율 | [ko.json:95](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:95) |
| `Mean score percentile` | 평균 점수 백분위 | [ko.json:228](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:228) |
| `Share beating benchmark` | 벤치마크 초과 비율 | [ko.json:413](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:413) |
| `Listen to this explanation` | 이 설명 듣기 | [ko.json:600](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json:600) |

长语句示例：리서치 관점은 자산군 내 상대적 위치이며 주문 지시가 아닙니다. 종합 점수는 가중 요인 측정을 결합합니다. 높은 점수가 낮은 위험이나 미래 수익을 입증하지 않습니다.

合成评价说明：합성 데모입니다. 생성된 평가는 과거 예측, 실행 거래 또는 실현 투자 성과가 아닙니다. 샘플 모드는 실시간 성과를 제공하지 않습니다.

## 本语言语法、自然度和领域检查记录

- 独立检查 리서치 관점、예상 알파、적중률、판단 없음 和 판단 보류。

- elevated 原简写상승可能被理解为行情上涨，已改为위험도 상승。

- 检查助词、空格、敬语、韩文字形及混排 IC / bp / ticker。

- 窄屏允许韩文音节处换行，没有看到缺字；自然分词和敬语仍需母语审校。

- 요인 연구실与팩터等行业惯用语的选择，和已完成评价的短标签需韩国金融编辑确认。

E-ko-01：韩文词内换行、요인／팩터和短标签语体属于待编辑检查项。

主要词库：[ko.json](/workspace/tradepulse-i18n-repair/web/src/i18n/locales/ko.json)；指南来源：[messages.js](/workspace/tradepulse-i18n-repair/web/src/components/agentResearch/messages.js)。这些是 AI 发现／建议，未冒充独立母语审校。

## 状态、失败和交互场景

| 本语言独立场景 | 结果 |
|---|---|
| initial load, persisted locale, navigation, filters and empty results | PASS |
| rapid Factor Lab pool and status changes retain both filters | PASS |
| SYN369 original verdict, source evidence, missing explanation and invalid ticker | PASS |
| keyboard Listen entry, all speech controls, stop recovery, error, route cancellation | PASS |
| reduced motion and keyboard disclosure/selector operability | PASS |
| voice availability {"unsupported":true} | PASS |
| voice availability {"empty":true} | PASS |
| voice availability {"chineseOnly":true} | PASS |
| voice availability {"delayed":true} | PASS |
| voice availability {"delayed":true,"eventless":true} | PASS |
| API loading | PASS |
| API HTTP503 | PASS |
| API malformed | PASS |
| API empty | PASS |
| API missing-evidence | PASS |
| API summary-only-abstention | PASS |

状态原始证据：[states-results.json](/workspace/work/tradepulse-full-locale-qa-20261026/verified-validation/final-states/states-results.json)。API 503、无效契约、空集合及缺失 evidence 是浏览器拦截模拟，不是真实后端服务通过。未改共享 fixture，也未静默补造结果。

## 声音、键盘及可访问语义

原生声音：0；发音与实际可听音频：NOT TESTED。有效声音 double：ko-KR。模型声音不是已安装声音；地域声音选择见每个可用性场景的 voices 数组。

Listen 入口在指南 h2 附近可见，键盘激活移焦到原朗读控制标题；不会自动调用 speak。Play／Pause／Resume／Stop、暂停后停止再播放、错误恢复、语言／路由切换取消均保持。无 API／无匹配声音仍能完整阅读。原生 Edge 仅中文声音的根因尚不能从 Linux Chromium 确定。

本语言 table 可访问树：[table-ko.yml](/workspace/work/tradepulse-full-locale-qa-20261026/verified-validation/table-ko.yml)；表格语义检查不是实际屏幕阅读器听测。

## 金融记录、证据和来源独立核对

榜单：620/620，三个池；解释：30/30。SYN369 原始 rank=4，资产池 520 条；score=1.3884，显示 +1.39；tier=`STRONG_OVERWEIGHT`，解释 verdict=`abstained`。最大贡献仍为 pv_mom_1m（0.779566）。

原始来源 `contracts/fixtures/run_output.fixture.json`，JSON Pointer `/recommendations/3`、`/explanations/3`。`exp-us_equity-syn369-c1` 保持 verified、`exp-us_equity-syn369-c2` 保持 rejected；证据 `ev-exp-us_equity-syn369-1` / `ev-exp-us_equity-syn369-2`、SHA-256、source text、query_template、source_table、params、as_of 均未翻译或改写。

cause_before_move 的实际 event / market-movement 时间戳原本缺失，仍然缺失。as_of 不是事件时间；没有补造时间或把拒绝改为支持。两条 factor_contributions / factor_value 引用及 ID 派生哈希只是通用合成 fixture，不能独立证明真实供应链因果。

逐记录证据：[independent-results.json](/workspace/work/tradepulse-full-locale-qa-20261026/verified-validation/independent-results.json)。免责声明、SYNTHETIC 来源、NO_CALL、缺解释及未知标的的独立场景均保留。计数 1,808 vs 1,200、trace timing 与 regime 来源差异仍显示。

## 修复、缺陷与回归依据

| 编号 | 严重度 | 修改／界限 | 文件 |
|---|---|---|
| I1 | Important | 阿语行业均分／shortlist 符号隔离 | `web/src/pages/Leaderboard.jsx:74` |
| I2 | Important | 原始 regime enum 决定 tone；翻译只决定文字 | `web/src/pages/Leaderboard.jsx:71` |
| I3 | Important | TableScroll 为缺少 caption 的表补本地化名称，保留既有 caption 与 scope | `web/src/components/ui.jsx:54` |
| I4 | Important | 迁移旧 Agent 测试至全局语言选择器；保留证据、数值、取消和键盘断言 | `web/scripts/agent-research-acceptance.cjs:94` |
| U1 | Important | 指南标题附近增加可见朗读入口，移焦到原控制器，不自动发声 | `web/src/components/agentResearch/GuidedResearch.jsx:35` |
| U2 | Important | 延迟枚举重试有界、voiceschanged、脚本子标签匹配、明确声音缺失原因；真实 Edge 仍待验证 | `web/src/components/agentResearch/useReadAloud.js:16` |
| I5 | Important | Factor Lab 连续 pool/status 筛选同步提交，避免 URL 条件丢失 | `web/src/pages/Factors.jsx:19` |
| I6 | Important | 200% 文字下候选按钮可收缩换行，修复 pt-BR Discover 801px 溢出 | `web/src/index.css:258` |
| L1 | Important | 日语／韩语 elevated 显式表示风险／警戒度，不暗示价格上涨 | `web/src/i18n/locales/ja.json:94` |
| I7 | Important | 保留仅有原始摘要的弃权原因，区分缺失检查明细；源摘要保持原文且不参与朗读 | `web/src/components/agentResearch/summary.js:10` |
| L2 | Optional | 捷克动态计数标签式表达；德语弃权及阿语命中率短标签澄清 | `web/src/i18n/locales/cs.json:549` |

## 本语言仍需人工确认

1. 独立母语金融编辑：语法、自然度、受众理解、术语和风险边界；英语同样需要。

2. 本语言真实可用设备声音与发音；Windows Edge／操作系统声音安装及在线语音限制。

3. NVDA／VoiceOver、原生 200% 浏览器缩放、axe／Lighthouse；不能拿 DOM 或 CSS 放大代替。

4. 团队确认源数值／ISO 日期格式策略、英文来源叙述保留策略，以及多语言相对仓库 English-only 规则的例外。

5. 负责人处理最新 main `c69e3d7642295b609f7db22c2079769d5d2e4b82` 的集成冲突并保留其数据、无障碍、依赖和集成修正；本分支没有做合并。

本报告只针对 `ko` 独立完成的技术场景和 AI 图文审阅，不以其他语言的检查代替本语言，也不宣称本语言已获母语或音频批准。
