# I1–I4 详细复现与修复索引

此文为导出导航补充；原始完整报告保持逐字不变。复现步骤描述已完成的审计，不表示本轮重新执行。基线 `3d2ae4ff1a74837b9dd41bfe8d505ca2f0861584`；修复及最终验收 `cd2b610049424fd6b3b7c8c169a9e2e426acc1b1`。

## I1 — Arabic financial sign direction

严重度：Important；最终状态：已修复（已测浏览器范围）。

复现：On ar /pool/us_equity in Pro, open sector values and inspect shortlist. Original sector mean +0.18 inherited RTL with no BDI.

修复位置：`web/src/pages/Leaderboard.jsx:74; web/src/pages/Leaderboard.jsx:75`。

修复：Canonical/BDI LTR isolation for signed values; original financial values unchanged.

现有证据：

- [before-I1.png](../before-I1.png)
- [after-I1-ar.png](../after-I1-ar.png)
- [after-I1-shortlist.png](../after-I1-shortlist.png)
- [verified-validation/signed-geometry.json](../verified-validation/signed-geometry.json)

## I2 — Translated enum changes status severity

严重度：Important；最终状态：已修复（已测浏览器范围）。

复现：Switch locale on /pool/us_equity (and other pools). Original badge tone was computed from translated text and fell back to muted.

修复位置：`web/src/pages/Leaderboard.jsx:71`。

修复：Compute tone from summary.regime_state, translate display text only.

现有证据：

- [before-I2.png](../before-I2.png)
- [after-I2-en.png](../after-I2-en.png)
- [verified-validation/supplemental-results.json](../verified-validation/supplemental-results.json)

## I3 — Business tables have no accessible names

严重度：Important；最终状态：已修复（已测浏览器范围）。

复现：Use Pro, open measurement disclosures and chart data tables. Inspect accessibility tree: a named wrapping region does not give its table a name.

修复位置：`web/src/components/ui.jsx:54`。

修复：Add localized caption only when a direct table lacks one; preserve existing captions and header scope.

现有证据：

- [original-reproductions.json](../original-reproductions.json)
- [verified-validation/table-en.yml](../verified-validation/table-en.yml)
- [verified-validation/table-ar.yml](../verified-validation/table-ar.yml)
- [verified-validation/independent-results.json](../verified-validation/independent-results.json)

## I4 — Obsolete guide-only browser acceptance

严重度：Important；最终状态：已修复（已测浏览器范围）。

复现：At original 3d2ae4f run the old Agent research acceptance. It targets the removed guide language selector/preference; historical result 7/15, eight failures. This is an audit finding, not a command rerun during export.

修复位置：`web/scripts/agent-research-acceptance.cjs:94`。

修复：Migrate to #app-language and global locale persistence; preserve financial/evidence/speech/cancellation/keyboard assertions and expand all-locale responsive checks.

现有证据：

- [legacy-before.log](../legacy-before.log)
- [legacy-before/results.json](../legacy-before/results.json)
- [verified-validation/final-agent.log](../verified-validation/final-agent.log)
- [verified-validation/final-agent/results.json](../verified-validation/final-agent/results.json)
