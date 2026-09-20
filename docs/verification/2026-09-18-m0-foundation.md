# 2026-09-18 M0 foundation evidence

Scope: M0.1/M0.2 partial implementation and M0.3 typed preflight. All gameplay fixtures below are synthetic. No Minecraft game/server installation, account login, Codex model job, experiment, score or soak was run. All aggregate T01–T17 and G0–G5 results remain `not_run`.

Environment: Windows 11 Home, version 10.0.26200, build 26200; CPython 3.12.14 through uv 0.12.8; Node 24.19.0; npm 11.17.0. Python and npm dependencies are locked in `uv.lock` and `backends/mineflayer/package-lock.json`. Native Codex CLI candidate inspected: 0.154.0-alpha.6.2, SHA-256 `960c111d47afd61669954b9df9e56083e302edbfa3ef6962d81dcc14a30051dc`. Its exec-help digest was `0e82cfde0122715250e93dc65866caa956b2ac5b9d0b20ec4ad4f9e81486509e`.

| Executed check | Result | Evidence scope |
|---|---|---|
| `uv sync` with explicit installed Python path | pass | 19 locked Python packages installed; initial uv minor-alias creation failed after download and explicit interpreter selection resolved it |
| `npm install --ignore-scripts` in backend | pass | Pinned dependency resolution; no game installation |
| `uv run --frozen python tools/export_schemas.py` and backend `npm run generate` | pass | Three canonical public record schemas plus request envelope; generated TypeScript |
| `uv run --frozen pytest -q` | pass, 31 tests | SPEC game examples, strict/negative contract cases, artifact hash/release mismatches, complete E9E checklist, usage cursor deduplication and unknown metering |
| `uv run --frozen ruff check src tools tests` | pass | Python lint |
| backend `npm test` | pass, 17 tests | TypeScript build; persistent acceptance/deduplication; stale identity/epoch/lease/revision/observation/deadline/sequence rejection; one lane; cancellation/late completion; partial effects; restart unknowns and retained costs; executor lock; scalar primitive cap; disconnect fencing; snapshot age; auth/scope/settings rejection; real CLI subprocesses reaching a synthetic persistent backend; shared schemas; actual pinned pathfinder on a synthetic map; hidden-cell filtering |
| backend `npx tsc --noEmit --noUnusedLocals --noUnusedParameters` | pass | Additional compiler checks, also enabled in tsconfig |
| `mcbench doctor` | blocked, exit 2 as designed | Binary/version/help inspected without inference; plugin load, actual JSONL schema, isolation, all-call accounting, interrupt and resume remain unverified |
| `mcbench conformance preflight --target e9e` | blocked, exit 2 as designed | Exact candidate file IDs retained; no artifacts supplied; ten actual compact cases remain `not_run`; no compatibility claim |
| `node .../cli.js --help` / worker without config | pass / rejected as designed | Help runs without a grant; worker fails with `SCHEMA_UNSUPPORTED`, starts no bot |

Test sources: [Python contracts](../../tests/test_contracts.py), [operator tests](../../tests/test_operator.py), [action/gateway/CLI tests](../../backends/mineflayer/tests/actions.test.ts), [shared contracts](../../backends/mineflayer/tests/contracts.test.ts), [visibility](../../backends/mineflayer/tests/visibility.test.ts), [pinned planner](../../backends/mineflayer/tests/navigation.test.ts). Synthetic temporary journals/grants are deleted by the tests. Private runtime evidence is not committed.

An initial recovery test found that a rejected same-epoch journal constructor left its SQLite handle open. The constructor now closes the handle on failure; the recovery/exclusive-owner tests pass. Initial compilation exposed incompatible direct/transitive `vec3` declarations; the direct pin is now the compatible 0.1.10. These resolved failures are retained here rather than hidden.

Final reconciliation also found Python's literal-boolean validator accepted numeric `1`, unlike JSON Schema. An explicit pre-validator and negative test now reject it. Strict TypeScript, Python lint/format, all 31 Python and 17 Node tests, Markdown link/fence checks, full ledger-ID inventory and `git diff --check` passed after the relevant fixes. Every transitive npm package has a version and integrity digest in the lock.

Source checks: the installed pinned Mineflayer/pathfinder sources and [upstream API](https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md), [pathfinder](https://github.com/PrismarineJS/mineflayer-pathfinder), [official native JSONL documentation](https://learn.chatgpt.com/docs/non-interactive-mode) and [selected Dovetail manifest](https://github.com/OpenCnid/dovetail-codex/blob/15c306ccfef28eb5f616fadcd5fd8eac0663e361/.codex-plugin/plugin.json) were inspected. Package-lock bytes, not moving source pages, pin the implementation dependencies. The CLI documentation establishes a turn-usage format, not per-call or nested accounting; the reader explicitly declines those claims.

Dependency audit: `npm audit --json` reports six moderate findings through old transitive `uuid` dependencies in the authentication chain ([GHSA-w5hq-g745-h8pq](https://github.com/advisories/GHSA-w5hq-g745-h8pq)). No compatible upstream fix was selected and no forced downgrade was applied. Security owner must resolve or explicitly assess the pinned dependency/call-path risk before authenticated runtime qualification. This is a recorded dependency limitation, not an isolation pass.

Remaining: the real vanilla acquisition workflow and authenticated server; wider vanilla action set, signals/pagination/reconnect; exact E9E install/handshake/registries/recipes/machines; native Dovetail loading/helpers/full metering; Windows process/filesystem/network/credential isolation; complete settings extension; private telemetry/scorer; complete records/controller/snapshots/budgets; soaks/teams/probes/pilot. The bounded development profile is not a reduced MVP definition. No required feature or release gate was removed.
