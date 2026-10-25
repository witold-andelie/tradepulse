# Dependency and tool policy

Security maintenance: 25 October 2026. The official npm registry audit reported 15 package
findings before the upgrade: two critical, five high and eight moderate. After the upgrade,
the full locked dependency graph reports zero findings. That is a dated registry audit,
not a guarantee that no vulnerability exists or will be reported later.

## Pinned application and build versions

| Library | Before | After |
| --- | --- | --- |
| React Router DOM | 6.28.0 | 7.18.4 |
| ECharts | 5.5.1 | 6.1.0 |
| echarts-for-react | 3.0.2 | 3.0.6 |
| Vite | 5.4.11 | 7.3.7 |
| React Vite plugin | 4.3.4 | 5.2.0 |
| Vitest | 2.1.8 | 4.1.12 |
| Ajv | 8.17.1 | 8.20.0 |
| PostCSS | 8.4.49 | 8.5.31 |
| Tailwind CSS | 3.4.17 | 3.4.19 |

React and React DOM remain 18.3.1. No new direct application dependency was added. The
PostCSS selector parser is overridden to 7.1.7 throughout the existing dependency tree to
address its parsing-complexity advisory while retaining Tailwind 3's configuration and CSS
pipeline. Do not remove that override without rerunning the audit and CSS/browser checks.

The existing router already enabled the v7 future behavior. Routing, keyboard navigation,
Back behavior, query filters and view persistence are checked by the unchanged original
browser suites. ECharts 6 changes some defaults; chart interactions, numeric alternatives,
reflow, rendering and console output are included in the maintenance checks. The largest
production chunk is 672.22 kB, below the task's 1 MB ceiling.

Use a supported Node line: `^20.19.0`, `^22.12.0`, or `>=24.0.0`. The local check used Node
24.18.0; the Docker frontend uses Node 22. Use `npm ci` for reproducible installs from the
committed lockfile. Do not use `npm audit fix --force` to select major upgrades automatically.

```powershell
npm ci
npm audit --registry=https://registry.npmjs.org
npm test
npm run check:contracts
npm run build
```

The audit was checked against the official registry with actual network access; an offline
or restricted tool's empty response is not accepted as security evidence. Full before/after
reports and regression scope are in [maintenance evidence](../docs/validation/maintenance-2026-10-25/README.md).

## Python lint policy

The development extra pins Ruff 0.17.2. `pyproject.toml` explicitly selects the project's
pre-0.16 rules (`E4`, `E7`, `E9`, `F`) plus `RUF100` for unused suppressions. This preserves
the original checks, including `E731`, instead of inheriting a much larger moving default
set. The existing lambda test's `noqa: E731` remains meaningful and unchanged. Four
non-enabled `BLE001` suppressions in ingestion were replaced with their explanatory comments;
execution behavior is unchanged. Both Ruff 0.15.20 and 0.17.2 pass the same explicit policy.

No given test or assertion was edited. Changing to Ruff's expanded default policy would be
a separate refactoring task, rather than an implicit rewrite of all original tests.

## Primary references

- [React Router v6-to-v7 migration](https://reactrouter.com/7.18.4/upgrading/v6)
- [ECharts 6 upgrade guide](https://echarts.apache.org/handbook/en/basics/release-note/v6-upgrade-guide/)
- [Ruff 0.16 default-rule change](https://astral.sh/blog/ruff-v0.16.0)
- [Vitest maintainer security advisory](https://github.com/vitest-dev/vitest/security/advisories/GHSA-5xrq-8626-4rwp)

Individual advisories, affected ranges and dependency identities are retained in the audit
report; no audit findings are hidden with an ignore list or omitted dependency class.
