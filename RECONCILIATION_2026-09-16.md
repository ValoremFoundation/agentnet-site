# AgentNet Runtime↔Catalog Reconciliation — 2026-09-16

## O1 version (resolved)
- **Code actually running = v0.4.5** (9 fast suites, 131/131 pass; `gate100` peak concurrent leases = 8).
- Evidence: `o1/evidence/o1_complete_freeze_2026-09-06.md`, `o1/tests/v045_late_result_race.mjs`, `o1/db/V005_cost_one_resolution_corrected.sql`.
- README "v0.2.0" + `package.json` "0.2.0" are **stale metadata** (not updated after the v0.4/v0.4.5 freeze).
- O1 orchestrator process is **not currently running** (was for the OX1 canary; now idle). Reuse its work-unit/dependency/lease/event machinery for the Director.

## Live service map (probed 2026-09-16)
| Service | Port | Route | Status |
|---|---|---|---|
| agentnet-marketplace | 8402 | /api/v1/capabilities | 61 active/LIVE rows |
| agentnet-gateway | 8646 | /agent/v1/rpc, /.well-known/x402, /agent/v1/health, /dedup/health | live; JSON-RPC works; x402 v2 requires payment only for `submit_bundle` |
| agentnet-adapter | 8647 | (rbuilder path pending) | up |
| agentnet-facilitator | 8096 | Base RPC + signer 0x467032…49Db | live |
| agentnet-fulfillment-signer | 9083 | socket-activated | up |
| agentnet-streams | 8750 | /v1/stream/{cap} | up but **unknown_stream** (no streams registered) |
| engineA-signer | 8760 | /opt/engineA-signer/signer.mjs | up (unrelated to AgentNet) |
| 8741/8744/8745/8746/8747/8748/8751/8752 | — | — | **TCP DOWN** (entire catalog "127.0.0.1:87xx" scheme is stale) |

## Scoreboard (105 records, all preserved)
- **Before:** GREEN 67 / UPSTREAM_BLOCKED 3 / NOT_SELLABLE 35 (summary block was **stale** — records computed to 67/35, summary said 66/36).
- **After reconciliation:** GREEN **59** / UPSTREAM_BLOCKED 3 / NOT_SELLABLE **43**.
- Summary `canonical_states` recomputed from records (fixes the 66-vs-67 stale block).

## 8 demoted records (was GREEN → NOT_SELLABLE/Planned)
Evidence: dead endpoint **and** no active marketplace commerce row.
| capability_id | endpoint | probe |
|---|---|---|
| mev.accuracy_archive | mev.advalorem.io/intelligence/accuracy-archive | 410 Gone |
| mev.daily_report | mev.advalorem.io/intelligence/daily-report | 410 Gone |
| mev.opportunity_feed | mev.advalorem.io/intelligence/feed | 410 Gone |
| mev.builder_recommendation | mev.advalorem.io/intelligence/builder-recommendation | 410 Gone |
| mev.liquidation_waves | mev.advalorem.io/intelligence/liquidation-waves | 410 Gone |
| mev.searcher_leaderboard | mev.advalorem.io/intelligence/searcher-leaderboard | 410 Gone |
| builder.bundle_submission | builder.advalorem.io/agent/v1/rpc | 405 |
| builder.private_orderflow | builder.advalorem.io/rpc | 405 |

These are the "previously demoted MEV records" — the stale catalog export had re-promoted them to GREEN. Stale exports must not silently promote: the catalog now carries a `reconciled_at` stamp + per-record `_reconcile_note`.

## Genuinely invokable today (59 GREEN)
- **Gateway-routed (8646):** `ai.classify` (+ any gateway-routed capability) — JSON-RPC live, x402 contract present.
- **O1-dispatch (no direct HTTP route):** 8 `agentnet.*` orchestration + 7 `mev.*` feed/intel + `search.web` + 3 `perplexity.*` (pay_to) — deliverable via O1 worker dispatch, not a direct route.
- **Streams (8750):** 7 `*.stream.*` — route exists, currently `unknown_stream` (streams not registered).
- **Marketplace-DB rows on dead ports:** the remaining marketplace rows point at 8741/8744/8745/8746/8748/8752 (DOWN). These are DB commerce rows awaiting their backend services — they retain an active commerce record but **cannot be invoked until the port is up**.

## Enforcement
- Demoted pages: JSON-LD `canonical_state`=NOT_SELLABLE, `availability_label`=Planned, `schema.org/availability`=Discontinued, visible badge=NOT-SELLABLE.
- These records cannot accept payment (no live endpoint + not sellable).
- Catalog + 8 pages patched on EC2 (`/var/www/agentic.advalorem.io` + `/var/www/agentic-static`).
