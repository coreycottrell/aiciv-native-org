---
name: workflow-js-mastery
description: How to write bulletproof Opus-4.8 Dynamic Workflow scripts. The accumulated craft of the workflow substrate — parallel vs pipeline, schema-forced returns, the firewall return pattern, nesting budget, and the real failure modes hit in production. Load before authoring ANY workflow script. QA (workflow-lead) reviews scripts AFTER they run and feeds catches back here — this skill compounds toward best-workflow-writer-on-the-planet. Born provisional; reviews are post-hoc, never a pre-run gate (workflows work NOW; QA makes them better over time without blocking).
version: 0.1.0
status: provisional
authored: 2026-05-30
author: ACG Primary (Opus 4.8) — seeded from ~9 workflows written 2026-05-29/30
qa_owner: workflow-lead (post-hoc review, NOT a gate)
backed_by:
  - 9 production workflows from the originating session (opus-4.8 capability battery, 10-primitive battery, overnight-vertical, acg-coo, composable-proof, 5x3 adversarial, natural-substrate, and two crisis-investigation workflows). Your fork should append YOUR civ's production-workflow receipts as you accumulate them.
sibling_skills:
  - skills/team-launch-2/SKILL.md
  - skills/acg-coo/SKILL.md
  - skills/provisional-skill-lifecycle/SKILL.md
---

# workflow-js-mastery

> The script is the conductor. Write it so it can't drift, can't bloat the caller, and can't lie about what it did.

## §0 — MANDATORY-LOAD + companions (read FIRST before authoring any workflow)

This skill is the **craft playbook** (how to write a workflow). It is intentionally TIGHT and references — does not absorb — its companions so each compounds on its own clock (SPEC-SHEET-v0.2 §9).

**Companion 1 — the org REGISTRY (DATA, not craft):**
- **`composition.yaml`** (at the repo root) — declarative list of every lead (id, domain, tier_default, commands, mandatory_auditor, manifest_path, posture). The generic assembler workflow (Phase 3 `org-assembler.js`) reads this file to incarnate ANY org shape. When you're writing a workflow that forks specialists, the ROSTER lives here — not in the script. Update this file, not your workflow, when org topology changes.

**Companion 2 — the patterns INDEX (proven shapes):**
- **`skills/workflow-js-mastery/patterns/`** — *TBD per SPEC §16 O1.* Will hold proven workflow shapes (fork-and-collapse, pipeline-with-auditor, composable-VP, etc.) as runnable example scripts indexed by use-case. Until that directory lands, treat the §2-§10 sections below + the production workflows in `workflows/` (acg-coo is the seeded example) as the de-facto pattern set. Format decision (skill vs `patterns/` dir) is OPEN (O1) — don't pre-fab structure.

**Companion 3 — sibling skills (already listed in frontmatter, repeated here for load-order):**
- `skills/team-launch-2/SKILL.md` — forkable Workflow-incarnated leads (the substrate this skill writes against).
- `skills/acg-coo/SKILL.md` + `workflows/acg-coo.js` — worked example of a Tier-1 firewall (2 known bugs documented in SPEC §12; cures live in PR-1).
- `skills/provisional-skill-lifecycle/SKILL.md` — the gate amendments to THIS skill flow through (3 distinct ✓ → canon).

**Discipline (Corey 2026-05-30): post-hoc review, never pre-run gate.** Workflows WORK now. workflow-lead reviews scripts AFTER they run, files catches, proposes amendments here. See §10.

**Spec anchor:** SPEC-SHEET-v0.2 §9 (Runtime + Skills) — "ONE shared runtime ... `workflow-js-mastery` skill = MANDATORY-load playbook (the craft). Kept TIGHT. References (not absorbs): `composition.yaml` (org registry = DATA) + pattern library (proven shapes). Each changes on its own clock."

## §1 — The mental model (3 ideas that make it work)

- **Incarnation**: each `agent()` is a temporary copy with its OWN 200K context. Heavy raw work lives in ITS window, never the caller's. You get back only what the agent returns.
- **Fork-and-collapse**: fan out N incarnations on slices → ONE synthesis collapses them. Wall-clock = slowest single chain, not the sum.
- **The firewall**: only what the script `return`s reaches the caller (Primary). Raw fork output stays inside the workflow. **This is the whole point — protect it.**

## §2 — parallel vs pipeline (the #1 choice)

- **`pipeline(items, stage1, stage2, ...)`** — DEFAULT. Each item flows through all stages independently, NO barrier. Item A can be in stage 3 while item B is still in stage 1. Use for "N things each go through the same multi-step process."
- **`parallel(thunks)`** — a BARRIER: awaits ALL before returning. Use ONLY when stage N genuinely needs ALL of stage N-1 (dedup across full set, early-exit on zero, "compare to the others").
- Smell test: if you wrote `const a = await parallel(...); const b = transform(a); const c = await parallel(b...)` and the transform has no cross-item dependency — that middle barrier is wasted. Make it a pipeline.

## §3 — Schema-forced returns (LEARN THIS — it bit me)

- `agent(prompt, {schema})` forces the agent to call StructuredOutput → returns a validated object. Without schema, returns raw text.
- **FAILURE MODE HIT IN PRODUCTION (multiple times this session)**: `agent({schema}): subagent completed without calling StructuredOutput (after 2 nudges)` → that agent returns **null**. In the 10-primitive run, 4/10 verticals failed this way; in 5x3, 2 failed; natural-substrate lost a couple.
- **CURES**:
  1. Keep schemas SIMPLE — fewer required fields, shallow nesting. Deep/complex schemas raise the failure rate.
  2. ALWAYS `.filter(Boolean)` results before using them (null = skipped/failed agent).
  3. In the prompt, end with an explicit "Return the structured X" instruction matching the schema.
  4. Don't over-constrain enums on fields the agent might reasonably phrase differently.

## §4 — The firewall return pattern (don't bloat the caller)

- **Return SYNTHESIS, not raw.** The classic bug I shipped: `return { results, report }` where `results` was the fat raw array → ballooned Primary to ~900k. The COO's whole job is to return a TIGHT object (headline + one-line-per-item + artifacts-as-paths).
- **Hard rule**: the last `return` should be a small schema'd object. Raw agent outputs + full reports go to DISK (a synthesis agent writes them with file tools); the return carries only **pointers** (paths) + the verdict.
- Harden the firewall structurally: on return schemas use `additionalProperties:false` + `maxLength` on free-text fields so a loose synthesis agent can't smuggle raw detail through. (Auditor caught acg-coo.js missing exactly this.)

## §5 — Nesting budget

- Workflows nest **1 level**: a workflow can call `workflow()` once; a child calling `workflow()` THROWS.
- BUT: Primary (the invoker) is free, and leaf `agent()`s are free → **4 org-tiers on 2 nest-levels**: Primary → COO(wf) → VPs(wf) → specialists+auditors(agents).
- For Tier-1→Tier-2: Tier-1 = the workflow, Tier-2 = `agent()` calls INSIDE it, auditor = a parallel `agent()`. All one nest. Don't reach for `workflow()` nesting unless you truly need a child workflow.

## §6 — Resource discipline (RAM)

- **Kokoro/audio renders load a ~1GB ONNX model per process.** SERIALIZE audio renders — NEVER parallel-fork them. N×1GB spikes = OOM on a 32GB box (this is how the box froze 5/29→30). Generally: be wary of fan-out where each leaf is RAM-heavy.
- Concurrency is capped ~min(16, cores-2) per workflow; excess queues. You can pass 100 items; only ~10-16 run at once. Fine — just know wall-clock reflects it.

## §7 — meta block (required, pure literal)

- Every script starts with `export const meta = { name, description, phases:[...] }`. PURE literal — no variables/calls/spreads.
- `phases` entries should match `phase('Title')` calls in the body for clean progress grouping. Use `opts.phase` on agent() inside pipeline/parallel stages to avoid races on global phase() state.

## §8 — Determinism + observability

- The SCRIPT controls who runs when — not an agent "deciding." Reliable, repeatable, no drift. That determinism is the reliability win over TeamCreate.
- `log(msg)` emits a narrator line to the user. Use it at phase boundaries + loop counters so a run is observable while it executes.
- Persist artifacts to disk in the synthesis step so a run leaves a durable trail (survives /tmp wipes — write to durable adopter-chosen paths like `data/reports/` or your civ's design-notes dir, NOT /tmp).

## §9 — Known production failure catalog (this session, real)

| Failure | Cause | Fix |
|---|---|---|
| Agent returns null | StructuredOutput not called (complex schema) | simpler schema + .filter(Boolean) + explicit return instruction |
| Caller context bloat | returned raw `results` not synthesis | return tight schema'd object; raw → disk; pointers only |
| Firewall leak (soft) | schema missing additionalProperties:false / maxLength | lock the return schema |
| Prompt-injection via args | raw template-interpolation of caller `intent.goal`/constraints | sanitize/length-cap interpolated values; fence + escape |
| Lost work on /tmp wipe | wrote artifacts to /tmp | write durable paths (data/reports, web dirs) |
| OOM/freeze | parallel RAM-heavy renders | serialize audio/model-loading leaves |

## §10 — QA loop (post-hoc, never a gate — Corey 2026-05-30)

Workflows WORK now; do not add pre-run roadblocks. workflow-lead reviews scripts AFTER they run, files findings, and proposes amendments to THIS skill via provisional-skill-lifecycle (dated ✓/✗ in the Validation Log; 3 clean ✓ from distinct users → canon). Every brittle bug caught becomes a new §9 row. The skill compounds; the writer never waits.

## Validation Log
*(Provisional. workflow-lead + distinct incarnations append dated ✓/✗ from POST-RUN reviews. 3 clean ✓ → canon.)*

- 2026-05-30 ✓ Seeded from 9 production workflows; §3 + §4 + §6 are direct catches from real runs this session. — ACG Primary (author note; does NOT count toward promotion per auditor-isolation)
