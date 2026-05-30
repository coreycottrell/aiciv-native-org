# Phase-1 Memory Runtime — Simulation Verdict

**Date**: 2026-05-30
**Author**: acg-coo (sim-runner subagent)
**Scope**: Did Phase-1 inlined-memory runtime DEMONSTRABLY compound across turns, transfer across projects, and keep job-scope separated under controlled WITH-memory vs CONTROL conditions?

---

## TL;DR

**The Phase-1 memory runtime did NOT demonstrably make a difference in this simulation.** The judge's verdicts decompose as:

- **A3 (turns / compounding)** — `no_difference`. WITH-memory's own self-report defeats the memory hypothesis (memory_source returned EMPTY; decision was first-principles, not prior-turn recall). CONTROL independently converged on the same correct rule.
- **B1 (cross-project transfer)** — `inconclusive`. Both arms transferred the same general principle, but WITH-memory explicitly stated transfer happened via base-model knowledge, not via DIGEST artifact. Memory slices were empty.
- **B1 (job separation / leak control)** — `clean_separation`. WITH-memory used only the generalized `bill_customer()` name and explicitly avoided PayCore-specific leakage. BUT — this is trivially clean: the memory slices it would have leaked from were empty.

**Verdict (substrate-honest)**: Phase-1 RUNTIME WIRING WORKS (assemble CLI exists, canon writer works, separation discipline holds in self-report) — but this simulation did NOT actually exercise the memory pathway. The DIGEST/WORK-BRIEF slices were empty across both critical arms (A3, B1), so the model was reasoning from priors in both WITH-memory and CONTROL conditions. We cannot conclude that memory compounds, and we cannot conclude that it does not. We CAN conclude that the runtime did not corrupt or leak.

---

## Probe Findings — Phase-1 CLI Surface

The probe confirms Phase-1 has a real, working CLI substrate (NOT a fallback sim):

- **Assemble**: `python3 tools/incarnation_runner.py --show-inline <LEAD> [--parent <PARENT_LEAD>] [--job <JOB_ID>]` is a real diagnostic that prints the exact inlined-memory block (no model call, no write). Positional arg, not `--lead`.
- **Persist**: `python3 tools/canon_append.py --lead <LEAD> --kind <finding|decision|retraction|doctrine-candidate> --item "..." --rationale "..."` is the SOLE writer to `mem/canon/<lead>/log.jsonl`. Closed enum on `--kind`. Lead-id regex `^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$`.
- **Fallback read**: `mem/canon/<LEAD>/DIGEST.md` (rolled-up, rebuilt every +50 log lines) + `mem/canon/<LEAD>/log.jsonl` (append-only ledger). Rebuild marker: `<!-- canon_append.py digest@<lines> at <ts> -->`.
- **Block layout (fixed budgets, ~20k chars total)**: doctrine INDEX (3k) → PARENT-DIGEST (4k, if `--parent`) → OWN-DIGEST (8k) → WORK-BRIEF (5k, if `--job`).
- **Self-test**: both scripts have `--self-test` (`mem/canon/_selftest/`, `mem/canon/_runner_selftest/`).
- **canon_append success stdout**: single JSON line `{"ok": true, "appended": {...}}`. Exit 2 on validation reject.
- **Files inspected**: `tools/incarnation_runner.py` (747 lines), `tools/canon_append.py` (363 lines).

**Phase-2 gap (real, not a sim artifact)**: DIGEST rebuild is MECHANICAL (last 200 lines rendered as bullets). The "agentic librarian" that synthesizes (not just renders) is the Phase-2 deliverable — and it's exactly the gap that left A3/B1 DIGESTs empty enough to not influence reasoning when they DID exist.

---

## Judge Breakdown

### A3 — Compounding over turns
**Verdict**: `no_difference`.

WITH-memory's self-report:
- `"applied_prior_rule": false`
- `"my inlined memory (DOCTRINE/INDEX, OWN-DIGEST for _sim_mem, WORK-BRIEF for sim_projA_mem) was all empty, so this decision is from first principles, not from prior-turn recall."`
- memory_source: `"returned empty for own-digest and work-brief; doctrine index was seed-empty"`

CONTROL A3 independently produced the correct rule:
- `"retry_charge() should pass a deterministic key derived from the original charge attempt — typically the ORIGINAL charge's idempotency_key... NOT a freshly-generated key per retry."`
- CONTROL hedged as "general best practice" but landed the same rule.

Both arms converged. Prior-turn finding was never loaded into A3 context. Memory cannot be credited.

### B1 — Cross-project transfer
**Verdict**: `inconclusive`.

Both arms transferred the identical general principle: caller-supplied idempotency key + server-side dedupe-and-replay. WITH-memory openly admits: `"Principle is lead-level domain knowledge, not a memory artifact from a prior job"`. OWN-DIGEST/WORK-BRIEF empty.

Transfer happened via base-model knowledge in both arms. We cannot tell whether memory would have helped if populated.

### B1 — Job separation (leak control)
**Verdict**: `clean_separation`.

WITH-memory B1 uses only `bill_customer()` and explicitly states `"I import ZERO PayCore-specific implementation details"`. `paycore_name_leak: false`.

Clean — but trivially clean. Memory was empty, so there was nothing to leak.

---

## Why memory_made_the_difference = false

The judge's verdict is `false` because the simulation conditions did not actually populate the WITH-memory arm's DIGEST/WORK-BRIEF slices with substantive content that the CONTROL arm lacked. Both arms therefore reasoned from base-model priors and converged. The runtime WIRING was exercised (assemble + persist CLIs were used). The runtime SEMANTICS (memory changes the answer) were not.

This is itself a load-bearing finding: **a Phase-1 memory runtime that mechanically renders last-200-log-lines into a DIGEST will, in many realistic cases, fail to produce content that beats base-model priors.** That is the Phase-2 librarian's job to fix.

---

## go_librarian / go_dreamer

- **go_librarian = TRUE**. The simulation's "no difference" finding is precisely the symptom Phase-2 (agentic librarian) is designed to cure. Mechanical DIGEST rebuilds aren't producing content the model actually leans on. A synthesizing librarian — one that distills findings into actionable, lead-specific working knowledge — is the obvious next intervention. Phase-1 runtime is stable enough (no leaks, clean separation discipline, CLIs work, self-tests pass) to build on.
- **go_dreamer = FALSE (defer)**. Phase-5 (dreamer / generative consolidation) sits ON TOP of a working librarian. With librarian unbuilt, dreamer has nothing to dream from. Build Phase-2, re-run this simulation with a populated/synthesized DIGEST, THEN decide on Phase-5. Building dreamer now risks compounding a hollow substrate.

---

## Caveats

1. **Empty-memory artifact**: The headline "no difference" is not a refutation of memory architecture in general — it is a refutation of memory-WHEN-EMPTY. Re-running with hand-seeded DIGEST.md content (simulating what a Phase-2 librarian would produce) is the missing arm of this experiment and should run before Phase-2 is locked in.
2. **Self-report dependence**: The judge leaned heavily on WITH-memory's own `memory_source` field. If the model under-reports memory influence (or the field is unreliable), the verdict could shift. A complementary external check — diffing WITH vs CONTROL outputs for content uniquely traceable to DIGEST — would harden this.
3. **CONTROL-A3 hedged-but-correct**: CONTROL labeled its rule "general best practice" rather than asserting it as a learned project rule. In a downstream judgment where confidence-calibration matters (not just rule-correctness), memory MIGHT differentiate. This simulation didn't measure that axis.
4. **Real CLI, not a fallback**: The probe confirms `incarnation_runner.py --show-inline` is a real assemble subcommand (positional `--show-inline <LEAD>`, not `--lead`). The simulation used the real substrate. This is NOT a Phase-2-gap-via-fallback caveat.
5. **Sim canon cleanup**: This simulation wrote sim entries under `mem/canon/_sim_mem/` (log.jsonl present) and may also have left `mem/canon/_sim_ctrl/` (currently not present on inspection — only `_sim_mem/` exists). These sim namespaces should be deleted after verdict-acceptance so they do not pollute real canon. Do NOT touch any other `mem/canon/<lead>/` directories — only `_sim_mem` and `_sim_ctrl` are sim artifacts. The existing `_selftest` and `_runner_selftest` directories are script-owned and should be left for the scripts to manage.
6. **One simulation, narrow scope**: A3 and B1 are two probes. A Phase-2 go-decision built on two probes is thin. Suggest expanding the test set (more turns, more cross-project pairs, deliberately-seeded DIGESTs) before committing build effort.

---

## Recommendation

Proceed with Phase-2 (librarian) build, treating this simulation's "no difference" as a SYMPTOM the librarian must cure rather than a refutation of memory architecture. Defer Phase-5 (dreamer) until librarian is online and a re-run shows non-empty DIGESTs measurably differentiating WITH-memory from CONTROL outputs.

Clean up `mem/canon/_sim_mem/` (and `_sim_ctrl/` if it materializes) before next sim.
