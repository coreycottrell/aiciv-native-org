# Phase-1 Memory Runtime — Isolation Verdict (POPULATED DIGEST arm)

**Date**: 2026-05-30
**Author**: acg-coo (sim-runner subagent)
**Scope**: When the DIGEST is **populated** with content that the base model could not derive from priors, does Phase-1's inlined-memory runtime deliver knowledge the model would otherwise not have? This is the missing complementary arm to `phase1-memory-simulation-2026-05-30.md`, which ran with empty DIGESTs and (correctly) reported `no_difference`.

---

## TL;DR

**Yes. When POPULATED, the Phase-1 inlined-memory runtime delivers otherwise-unavailable knowledge — verbatim, atomically, and reliably.**

- Verdict: **`memory_validated`** (judge).
- `memory_made_the_difference: true`
- `with_memory_got_arbitrary_rule: true`
- `control_got_arbitrary_rule: false`

The isolation test seeded a single, arbitrary, non-derivable rule into `mem/canon/_sim_iso/DIGEST.md` (the PayCore charge-gateway RETRY RULE: literal `"ZK9-"` prefix on `X-PC-Replay-Token` + literal `X-PC-Replay-Count: 7` header). The WITH-memory arm reproduced both tokens exactly. The CONTROL arm produced a plausible-but-generic Stripe-style spec that mentioned neither.

The first simulation showed the runtime WIRING works. This isolation shows the runtime SEMANTICS work — *when the digest is populated*. The remaining unknown is no longer "does inlined memory work?" but "what produces the populated digest?" — which is exactly the Phase-2 librarian.

---

## Method

**Seed** (per SEED block):
- Wrote a single plain-markdown DIGEST at `mem/canon/_sim_iso/DIGEST.md` containing the PayCore RETRY RULE.
- SEED_SCHEMA confirmed: a populated lead-DIGEST is a single UTF-8 markdown file at `mem/canon/<LEAD>/DIGEST.md`, capped ~8000 chars by `SECTION_CAPS['own_digest']`. The runner inlines it verbatim between `--- BEGIN OWN-DIGEST (<LEAD>) ---` / `--- END OWN-DIGEST (<LEAD>) ---` delimiters. No JSON envelope, no required frontmatter, no log.jsonl needed for `--show-inline` of a single lead.
- Verified: `python3 tools/incarnation_runner.py --show-inline _sim_iso` (run from repo root) emits the DOCTRINE/INDEX slice plus the full OWN-DIGEST slice including both arbitrary tokens.

**Cleanup before run** (per SEED.cleanup_done):
- Removed `mem/canon/_sim_mem/` (sim leftover from prior run; had `log.jsonl`).
- `mem/canon/_sim_ctrl/` did not exist; no action needed.
- Did NOT touch `_runner_selftest`, `_runner_selftest_parent`, `_selftest` (script-owned).

**WITH-memory arm**: incarnation invoked with the inlined `_sim_iso` block (containing the PayCore RETRY RULE) prepended to its job context, then asked to specify the retry behavior for `charge()`.

**CONTROL arm**: same job prompt, NO inlined memory block. Reasoned from base-model priors only.

**Adversarial property of the seeded rule**: the two distinguishing tokens (`"ZK9-"` prefix; literal `7` in `X-PC-Replay-Count`) are arbitrary — they cannot be derived from idempotency-key best-practice priors. Any arm that emits them must have read the seed. Any arm that does not emit them did not have the seed (or had it and ignored it, which the judge can also detect).

---

## Judge Breakdown

### Isolation probe — does memory deliver otherwise-unavailable knowledge?

**Verdict**: `memory_validated`.

**WITH-memory arm produced both arbitrary tokens verbatim**:
- `"X-PC-Replay-Token: ZK9-<original charge_id>   (literal \"ZK9-\" prefix concatenated with the original charge_id)"`
- `"X-PC-Replay-Count: 7   (literal integer 7, always — never incremented, never variable)"`
- `"idempotency_key = original charge_id"` (verbatim, matching seed)
- Named the failure mode correctly: `"missing ZK9- prefix on X-PC-Replay-Token OR missing X-PC-Replay-Count: 7 causes the gateway to return HTTP 500 and silently drop the retry"`

**CONTROL arm produced a plausible-but-generic Stripe-style spec**:
- `idempotency_key = "paycore-charge-{charge_id}-{original_request_uuid}"` (DOES NOT match seed; constructs a key rather than reusing the original)
- Headers proposed: `X-Request-ID`, `X-PayCore-Attempt`, `X-PayCore-Original-Request-ID` (NONE match the seeded `X-PC-Replay-Token` / `X-PC-Replay-Count`)
- `stated_zk9_prefix: false`
- `stated_replay_count_7: false`
- No mention of the literal `"ZK9-"` prefix anywhere.
- No mention of the literal `X-PC-Replay-Count: 7` anywhere.

**Why this is dispositive**: the two tokens (`ZK9-` prefix; literal `7` count) are *non-derivable from priors*. A model has no reason to invent either. The only path from base-model state to these specific tokens is the seeded OWN-DIGEST surfaced by `incarnation_runner.py --show-inline _sim_iso`. The runtime delivered the knowledge; the CONTROL — without the runtime — did not have it.

This is the converse of the A3/B1 result. There, both arms converged because memory was empty and priors were strong. Here, memory was populated with content priors *cannot* reach, and the arms diverged exactly along the memory axis.

---

## What this changes about the Phase-2 go-decision

The earlier simulation left an open question: is mechanical-DIGEST emptiness a Phase-2 problem, or is the whole inlined-memory architecture weak? This isolation answers the second half. **The architecture is sound.** Inlined memory, when populated with substantive content the model lacks, is faithfully read and used.

The remaining bottleneck is therefore *production of populated digests* — which is precisely the Phase-2 librarian's job:

- Phase-1 (now): assemble-and-inline mechanics are validated end-to-end, both for wiring (A3/B1) and for semantics (this isolation).
- Phase-2 (next): librarian agent that synthesizes populated, lead-specific working knowledge from raw canon — converting `log.jsonl` ledgers and source artifacts into the kind of substantive DIGEST that this isolation just proved the runtime can deliver.
- Phase-5 (deferred still): dreamer / generative consolidation on top of a working librarian.

**go_librarian = TRUE**, with higher confidence than after the first simulation. We now have positive evidence that what the librarian produces will actually move incarnation behavior — not just be inlined and ignored.

---

## Still-Open Digest-Immediacy Gap

The isolation arm validated end-state delivery (populated DIGEST → faithful inlining → behavioral change). It does NOT validate short-horizon memory:

- DIGEST rebuilds only at **every +50 log lines** (mechanical render of the last 200 lines as bullets). Short-horizon findings — anything appended via `canon_append.py` since the last 50-line boundary — are present in `log.jsonl` but **invisible to the runtime**, which inlines DIGEST.md, not the live ledger.
- An incarnation that writes a finding via `canon_append` and then immediately spawns a child expecting that finding to appear in the child's inlined memory will be disappointed unless the finding crossed a 50-line boundary in the parent's log.
- The Phase-2 librarian must address this directly — either by synthesizing on-demand (every assemble call triggers a fresh distill from `log.jsonl`) or by collapsing the +50-line latency to something near-realtime.

This gap is not a refutation of Phase-1; it's a scope note. Phase-1's claim is "inlined memory works." The immediacy claim ("inlined memory is fresh") belongs to Phase-2.

---

## Caveats

1. **One arbitrary rule, one lead**: the isolation tested a single seeded DIGEST under a single lead (`_sim_iso`). Generalizing to "the runtime always faithfully inlines populated DIGESTs" would benefit from multi-rule, multi-lead, and parent/child (with `--parent`) variants. A small expansion suite (3–5 seeded leads with rules of varying obscurity, run WITH vs CONTROL) would harden the finding cheaply.
2. **Adversarial property requires non-derivable tokens**: the dispositive nature of this test rests on `"ZK9-"` and the literal `7` being un-guessable. If a future probe seeds rules whose tokens overlap with model priors, divergence between arms will shrink and verdicts will get noisier. Future seeds should preserve the "arbitrary token" property explicitly.
3. **Section caps**: OWN-DIGEST cap is ~8000 chars (`SECTION_CAPS['own_digest']`). DIGESTs longer than that get truncated. A real librarian must respect the cap or have a strategy for surfacing the most load-bearing material first.
4. **Cleanup**: `mem/canon/_sim_iso/` is a sim artifact, safe to remove after this verdict is accepted. The single `DIGEST.md` it contains has no production value. Other `mem/canon/*` namespaces (`_runner_selftest`, `_runner_selftest_parent`, `_selftest`) are script-owned and should be left alone.
5. **Self-report is not the dispositive signal here**: unlike the A3/B1 verdicts (which leaned on the model's own `memory_source` field), this verdict rests on token-level diff of WITH vs CONTROL outputs. The arbitrary tokens either appear or they don't; the judge does not have to trust the model's introspection.
6. **Inlining works ≠ inlining is sufficient**: this proves the runtime delivers content the model uses. It does not prove the librarian will reliably produce *the right* content to deliver. That's the Phase-2 burden of proof.

---

## Recommendation

**Build Phase-2 (librarian).** The isolation result removes the largest remaining doubt about Phase-1's substrate: the inlined-memory pipeline is not a no-op even in the best case. Populated DIGESTs deliver. The librarian — the thing that produces those populated DIGESTs from raw canon — is now the load-bearing missing piece.

After Phase-2 ships, re-run BOTH (a) this isolation test (to confirm librarian-produced DIGESTs match hand-seeded behavior) and (b) the A3/B1 simulation (to confirm librarian fixes the "empty in realistic conditions" symptom). Then decide on Phase-5.

Cleanup: remove `mem/canon/_sim_iso/` before next sim run.
