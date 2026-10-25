# Runtime validation — 25 October 2026

These reports describe actual execution of the delivered real sample. They do not certify
live Zetaris, Meterless engines or hosted NIM answers.

| Evidence | Result | Artifact |
| --- | --- | --- |
| Empty-store startup with networking blocked | 616 records, 33 cards, nine abstentions; zero network attempts; cached run reused | [Startup JSON](sample-startup.json) |
| Actual local API browser journeys | 9/9 groups; Simple/Pro, nine routes, 1440/320 px; no normal console errors or fixture requests | [API browser JSON](real-api.json) |
| Fresh local Compose build and first boot | Core healthy, non-root storage writes, named volumes and nginx API proxy | [Container JSON](docker.json) |
| Corrected container frontend journeys | 9/9 groups, including honest REPLAY wording and a visible intentional 503 | [Container browser JSON](docker-browser.json) |
| Independent single-pool runs | Three real inputs/outputs with unchanged traces and zero network attempts | [Examples](../../examples/README.md) |

All browser counts come from the actual API response. Normal journeys do not intercept API
responses. The separate intentional 503 case is identified in each browser report; its
expected network error is excluded from the normal-console result. Run IDs and payload hashes
identify the different computations; creation times and trace durations naturally differ.

The local API report predates the final REPLAY wording correction; the container report
includes that correction. `web/scripts/real-api-acceptance.cjs` reproduces both environments.
Capture files for every route/view/width remain in the collector's private QA directory.
Selected actual captures and their hashes are in [the submission assets](../submission/assets/manifest.json).

The first container run used empty project-scoped volumes. Core has a 3 GiB memory cap and
web 256 MiB; existing unrelated containers were not modified. This is a core/web smoke and
browser acceptance, not a successful engines or full-model deployment.

The latest Python suite has 609 passing cases and 19 existing lxml warnings; the frontend has
89 passing cases, valid contract fixtures and a successful build. All original test
assertions and table/API schemas remain unchanged. Accessibility evidence and its separate
native-screen-reader limitation are in [the web report](../../web/ACCESSIBILITY_ACCEPTANCE.md).
