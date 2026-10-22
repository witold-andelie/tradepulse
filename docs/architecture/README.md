# Architecture

The system is modelled with **OPM** (Object-Process Methodology, ISO/PAS 19450). The diagrams are
written in Graphviz DOT, so they can be diffed and reviewed like code. Every diagram has an OPL
(text) twin in [`opm/OPL.md`](opm/OPL.md). The rendered SVGs live in `opm/svg/`.

| diagram | scope | owner colours |
|---|---|---|
| [legend](opm/svg/legend.svg) | notation and owner colours | — |
| [SD0](opm/svg/SD0_system.svg) | system diagram: customer, sponsors, main processes | all |
| [SD1](opm/svg/SD1_recommending.svg) | Recommending in-zoomed: one `/run`, 8 subprocesses | lead |
| [SD1.2](opm/svg/SD1.2_settling.svg) | Settling past recommendations | lead + C |
| [SD1.3](opm/svg/SD1.3_extracting_linking.svg) | Extracting events and linking the relation graph | lead |
| [SD1.4](opm/svg/SD1.4_researching_factors.svg) | Researching factors: gates G1–G5 | lead + C |
| [SD1.5](opm/svg/SD1.5_regime_ranking.svg) | Assessing regime and ranking | lead + C |
| [SD1.7](opm/svg/SD1.7_explaining.svg) | Explaining with a bounded verify loop | lead |
| [SD2](opm/svg/SD2_acquiring.svg) | Acquiring the data lake | A |
| [SD3](opm/svg/SD3_browsing.svg) | Browsing the web app | B |

Supporting specs:

- [factors.md](factors.md): factor catalogue, gates, scoring and tiers, regime monitor
- [data-sources.md](data-sources.md): sources by pool, point-in-time rules, sponsor routing
- [decisions.md](decisions.md): decision log and open items

## Editing a diagram

1. Edit the `.dot` file and the matching OPL sentences in the same PR.
2. Re-render with `py -3 scripts/render_opm.py`. It needs Graphviz (`dot`) on PATH.
3. Commit the `.dot` and `.svg` files together.
