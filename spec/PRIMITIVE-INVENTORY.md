# AiCIV-Native Org — Primitive Inventory (tested vs not)

**As of**: 2026-05-30 ~14:30Z, before the primitive-test workflow runs.
**Rule**: a primitive is TESTED only with an on-disk receipt from a real run. "Sounds simple" ≠ tested.

| # | Primitive | What it is | Status | Evidence / gap |
|---|-----------|-----------|--------|----------------|
| P1 | **Incarnation** | agent() reads on-disk identity, embodies it, returns structured data | ✅ TESTED | 10-primitive T1/T8; COO run; embodied_proof verbatim from manifests |
| P2 | **Memory write-back** | incarnation writes a learning to disk | ✅ TESTED | 10-primitive T2 (1879-byte file written) |
| P3 | **Fork** | one lead → N incarnations on slices | ✅ TESTED | 10-primitive T3 (5 distinct slices); overnight 6-vertical |
| P4 | **Collapse / single-writer** | N forks → 1 synthesis, no write race | ✅ TESTED | 10-primitive T4 (5 proposals → 1 merge file) |
| P5 | **Firewall / compression** | only synthesis returns to caller; raw stays inside | ✅ TESTED | acg-coo (268k→400 tok); composable-proof (202k→250) |
| P6 | **Context frugality at Primary** | Primary receives only the verdict | ⚠️ INFERRED | T9 measured raw, asserted Primary delta — not directly measured |
| P7 | **Tier-1→Tier-2 nest** | Tier-1=workflow, Tier-2=agent(), 1 legal nest | ✅ TESTED | composable-proof (coding-PM → web+security) |
| P8 | **Mandatory auditor reflex** | adversarial check before passing up | ✅ TESTED | composable-proof auditor caught 2 real COO bugs |
| P9 | **Composability (shared lead, multi-boss)** | one identity serves 2+ bosses via own incarnations | ❌ UNTESTED | designed (boss-attributed canon); no 2-boss concurrent run yet |
| P10 | **Self-evolution loop** | incarnation authors skill from real catch | ⚠️ PARTIAL | T5 authored execution-host-path-discipline; full loop (use→✓→canon) not run |
| P11 | **The gate (cross-incarnation validation)** | DIFFERENT incarnation validates, not self | ✅ TESTED | T6 gate caught fabrication via SSH-verify |
| P12 | **Sybil-resistance (cross-VERTICAL validator)** | same-vertical clones rubber-stamp; cross-vertical catches | ❌ UNTESTED | Test 9 designed (predicted ~80% vs ~10%); NOT run |
| P13 | **One-level nesting budget** | workflow()→child OK; grandchild throws | ⚠️ ASSERTED | documented from tool spec; not empirically hit in our runs |
| P14 | **🚨 TGIM integration** | post work-chain/events to /events; external read | ❌ UNTESTED | "sounds simple" — tgim_event.py exists; NOT fired from a workflow this arc |
| P15 | **AgentAuth per-lead identity** | does each lead need own keypair for TGIM entity ID? | ❌ UNTESTED | HYPOTHESIS: no — one civ keypair + agent_id field gives attribution. MUST verify. |
| P16 | **Memory 3-layer r/w contract** | doctrine(immutable)/canon(append boss-attributed)/work(job-scoped) | ❌ UNTESTED | spec'd in natural-substrate-spec; no runtime built/run yet |
| P17 | **Structured-memory-delta enforcement** | validator rejects return without memory_delta | ❌ UNTESTED | the consistency mechanism; needs incarnation_runner.py |
| P18 | **Resource discipline (serialize renders)** | RAM-heavy leaves serialized | ✅ TESTED (the hard way) | RAM freeze 5/29→30 = parallel-render-class risk confirmed |

## Headline gaps (what step 6 must actually test)

1. **P14 TGIM integration** — the big "sounds simple, untested." Fire a real work-chain event from a workflow, read it back. PROVE the wire.
2. **P15 AgentAuth identity** — confirm one-keypair-+-agent_id gives distinct TGIM entity attribution (or discover we need per-lead keypairs).
3. **P9 Composability** — 2 bosses, same lead, concurrent, no collision.
4. **P12 Sybil** — cross-vertical validator actually outperforms same-vertical (the load-bearing trust claim).
5. **P16/P17 Memory contract** — needs the runtime; can prototype the read-inline/write-delta shape in a test even before full PR-1.

## Tested-confidence summary
- **Solid (✅): 8** — incarnation, memory-write, fork, collapse, firewall, nest, auditor, gate, resource.
- **Soft (⚠️): 4** — context-frugality (inferred), self-evolution (partial), nesting-budget (asserted).
- **Untested (❌): 6** — composability, sybil, TGIM, agentauth-identity, memory-contract, memory-delta-enforcement.
