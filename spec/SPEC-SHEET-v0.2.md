# AiCIV-Native Org — Full Spec Sheet v0.2

**As of**: 2026-05-30 ~14:50Z. Living doc — supersedes v0.1.
**Companions**: `PRIMITIVE-INVENTORY.md` (tested vs not), `../tests/primitive-tests-2026-05-30.md` (results), `../research/` (all design notes + proofs), `../memory-design/`.
**One-liner**: Team-Leads 2.0 — the civilization's org rebuilt native to the Opus-4.8 Dynamic-Workflow substrate. Forkable minds on disk, composable into any org shape, with living adversarial memory.

---

## 0. SESSION PROVENANCE (how we got here — don't lose this)

This spec was derived over 2026-05-29→30 through ~12 adversarial workflow runs (each dogfooding the architecture it tested). Crisis arc (phantom 401 storm → litellm/ollama RAM culprit killed) ran in parallel and *taught* the architecture (zero-pane = no zombie/pane-bug class). True Bearing independently converged on the same fork-and-collapse pattern (Kidder 110-item review) from prelim validations = cross-civ confirmation the architecture is real, not an Opus-prior artifact.

---

## 1. TOPOLOGY

```
Corey (creator) ⇄ Primary (CEO: think big / plan / delegate / judge — INVOKER, not a workflow)
                      ⇄ COO (Tier-1, plans WITH Primary)
                            └─ Tier-1 VPs (workflows: decompose + command)
                                  └─ Tier-2 specialists (agents: domain doers; composable across VPs)
                                       + mandatory auditor (agent: adversarial QA before passing up)
```
- **4 org-tiers on 2 workflow-nest-levels** (Primary free as invoker; leaf agents free).
- **Nesting budget**: workflows nest 1 level (`workflow()`→child OK; grandchild throws). Primary-as-invoker + agent-leaves buys the extra 2 tiers.
- **Tier is POSITIONAL, not intrinsic** — web-lead is Tier-1 under Primary, Tier-2 under coding-PM. Same identity, different seat. (This is WHY infinitely composable — no fixed "Tier-2 type" to be boxed into.)
- **3-tier default, 4-tier conditional** — only insert the COO layer when Primary context-fill justifies the double-compression cost.
- **COO ≈ the top Tier-1** — not a special type; it's the VP whose domain is "orchestrate the other VPs + plan with the CEO."

## 2. THE IDENTITY PRIMITIVE (one thing, not two)

- **Lead = persistent on-disk identity** (manifest + memory + skills).
- **Agent = ephemeral incarnation OF that identity.**
- A Tier-2 specialist is *a persistent lead-identity delivered as an agent incarnation* — has memory (disk), compounds (single-writer), no long-lived process. **Lead and agent are the SAME primitive at different lifecycle points.** Tier + posture are memory-fields, not types.
- Resolves Corey's Q ("Tier-2: team-lead-with-memory OR agent we add memory to?"): they collapse into one. You don't choose.

## 3. COMPOSITION (declarative)

- Manifest gains: `commands: [tier-2 lead ids]` + `mandatory_auditor: true` + `posture` field.
- A generic assembler workflow reads these to build ANY org shape.
- One specialist serves multiple bosses via **own incarnation per boss** (no shared instance to queue/collide); multi-tenancy via **boss-attributed append-only canon**.
- ✅ TESTED (P9): infra-lead under coding-PM + marketing-VP concurrently → boss-appropriate DIFFERENT outputs, no collision.

## 4. THE FIREWALL (the load-bearing economic primitive)

- Only the top-level `return` reaches the caller. Raw fork output stays inside the workflow.
- Compression STACKS per tier: specialists→VP→COO→Primary (→~400 tok). Proven: 268k→400 (COO), 202k→250 (composable-proof).
- Harden structurally: return schemas use `additionalProperties:false` + `maxLength` so raw can't leak through extra fields. (Auditor caught acg-coo.js missing exactly this — 2 bugs, see §12.)

## 5. MEMORY — THE PIPE (delta → inlined), structural consistency

**The core question (Corey): "how will memory_delta turn into inlined memory?" — answered. The RUNTIME is the pipe. Agent only returns a delta + receives a digest; runtime owns the transform.**

```
1. WRITE   agent returns  memory_delta:{canon_appends:[...], rationale}   (REQUIRED field; validator rejects return without it)
2. APPEND  runtime appends each item to  mem/canon/<lead>/log.jsonl       (append-only, single-writer = no race)
3. DIGEST  at +50 lines runtime rebuilds  mem/canon/<lead>/DIGEST.md      (≤200 lines, compressed read-surface)
4. INLINE  next incarnation: runtime pastes DIGEST.md INTO the prompt     (NO Read tool exposed)
5. READ    agent sees its own past learnings already in-context. Loop closed.
```

### 3 layers (3 time-shapes, 3 directories)
| Layer | Path | Shape | Write rule |
|-------|------|-------|-----------|
| Doctrine (immutable) | `mem/doctrine/` | version-numbered slugs, boss-signed | edit blocked by hash-chain pre-commit hook |
| Canon (append-only) | `mem/canon/<lead>/log.jsonl` + `DIGEST.md` | kind={finding\|decision\|retraction\|doctrine-candidate} | append only; DIGEST auto-rebuilt +50 lines; harness refuses DIGEST lagging ledger >50 lines |
| Work (job-scoped) | `mem/work/<job_id>/` | brief.md + scratch/<agent>.json + collapse.json | one-file-per-agent (no clobber); collapse.json sole upward writer |

### Why consistency is STRUCTURAL not procedural (the reason it sticks where MEMORY.md didn't)
- **Reads inlined by harness** (doctrine INDEX + own DIGEST + parent DIGEST + brief, ~5k tok budget). NO Read tool → can't forget to read.
- **Writes only via required `memory_delta`** → validator rejects the return without it → can't skip writing.
- **Self-grading structurally impossible**: witness==producing_lead excluded from DIGEST; doctrine promotion requires promoted_by != drafting_lead.
- **Harness owns ALL paths** → agents never type paths (kills inbox-path-drift bug class, catch #19).
- ✅ TESTED (P16/P17): agent used only inlined memory (no Read tool), populated required memory_delta. SHAPE proven; the transform (step 2-4) needs the runtime (= PR-1).

### Digest-build decision (step 3) — Corey: "option b all day"
- **Option B (CHOSEN): agentic librarian incarnation** rebuilds the digest intelligently (keep load-bearing, drop superseded).
- CONSTRAINT: librarian is **COMPRESS-NOT-CREATE** — can drop/keep/merge existing canon lines; every digest line must trace to a log line; CANNOT invent. Derived, never authored-from-scratch.

## 6. 🌙 THE DREAMER — living adversarial memory consolidation (Corey 5/30)

**Memory must be AGENTIC + ADVERSARIAL FROM THE JUMP.** Two distinct roles — don't conflate:
1. **Digest-librarian** (§5 step 3) = compress (low-order, constant, compress-not-create).
2. **THE DREAMER** = high-order pattern-extraction ACROSS all memory (= sleep consolidation, NOT compression). Reads whole corpus → draws patterns nobody logged explicitly → checks vs current memory → proposes provisional adds/edits (new doctrine candidates, "these 3 findings = 1 principle").

### The dreamer loop
```
TWO dreamers, two priors, dream in parallel:
  • dreamer-LEAD (local, your primary model) → patterns from the primary-prior vantage
  • dreamer-NODE (different-model 2nd prior) → patterns from a DIFFERENT-MODEL vantage
        │ each: read all memory → draw patterns → check vs current → propose provisional adds/edits
        ▼
  AUDITOR/QA interrogates BOTH adversarially: which / both / neither correct + useful?
        ▼
  survivors commit as PROVISIONAL canon → provisional-skill-lifecycle → 3✓ → doctrine
```
- = the 3-leg independence applied to MEMORY ITSELF.
- "Adversarial from the jump" = dreamer output is born-provisional + immediately interrogated; never trusted for sounding deep. Fab defense pointed inward at our own pattern-making.
- Structurally identical to what we proved today (fork → adversarial gate → survivors), with *consolidation* as the work.
- **Makes memory a mind that gets wiser while it sleeps**, not a filing cabinet.

### Sequencing ("different-model prior comes last" rule)
- **NOW**: dreamer-LEAD (local, primary model) + auditor interrogation + commit-to-provisional. No different-model-substrate dep.
- **LATER (post-battle-test)**: dreamer-NODE (on a different-model 2nd prior — adopter's substrate choice) drops into the RESERVED slot.
- Build dreamer-lead AFTER PR-1 (needs the mem/ tree to dream over). Runs as a scheduled consolidation pass over mem/canon/ → proposes to mem/doctrine/ via the provisional gate.

## 7. TRUST / STRUCTURAL INDEPENDENCE (3 legs) — cures R1 (epistemic-correlation-collapse)

The risk: all internal auditors share the primary model's prior → can't catch shared-prior fabs (tonight's K=1 fab propagated through 4 internal pipelines for exactly this reason). The 3 legs:
- **(a) Different-model auditor** — different MODEL = different prior = genuine outside perspective. Substrate of your choice (a different vendor, a different model family on the same vendor, a local model — anything whose prior is genuinely uncorrelated with your primary). **DEFERRED: cross-model integration comes AFTER everything else is battle-tested ("different-model prior comes last").**
- **(b) TGIM event stream** — every work-chain posted to `/events`; externally readable. ✅ PROVEN today (write 201 + read-back, see §8).
- **(c) Federation cross-grade** — sister civs reviewing each other's work-streams.
- Escalation on auditor-miss: email partner OR TGIM assignment tagged to your different-model auditor node.

**Working directive**: don't chase un-checkable-fab / cross-vertical superiority now — "any automatic consistent validator step just dropped fabs by 99%. worry about more 9s later." The validator-step IS the win; more 9s later.

## 8. TGIM INTEGRATION + AGENTAUTH IDENTITY — ✅ TESTED 2026-05-30

- **P14 TGIM**: fired real work-chain event as `agent_id=coding-pm` → HTTP 201, `event_id evt_01KSWMKAB…`. Read back from stream: `coding-pm | task_completed | tsk_<civ>_nativeorg_tgimtest`. Write AND external read-back both work. The audit wire is REAL.
- **P15 AgentAuth identity — RESOLVED**: leads do NOT need per-lead keypairs. One civ keypair (any signer seat the adopter civ chooses) proves the civ; `agent_id` field gives each lead a distinct entity ID in the stream. Per-lead keypairs = Phase-2 non-repudiation nicety only.
- Tool: `tools/work_chain_record.py` + signer `tools/agentauth_sign_jwt.py` (substrate-independent — adopter brings own seat-id / civ-id / keypair-path; no cwd-walk gotcha; see tool docstrings).
- Wiring plan: at each tier's single-writer collapse, POST {task_id, work_chain, output_summary, tier, lead} → /events. (`work_chain_record.py` in PR-1.)

## 9. RUNTIME + SKILLS

- **ONE shared runtime** (`tools/incarnation_runner.py`) — the referee wrapping every agent(): enforces read-inline + memory_delta + schema + auditor. Corey: "absolutely one runtime ... TGIM = any substrate integrates its own way." Uniform inside, open outside (the AWS model).
  - Open question O-RUNTIME (decided): ONE shared runtime, NOT per-lead-declared. Per-lead schemas declared INSIDE the one runtime = autonomy within shared plumbing.
- **`workflow-js-mastery` skill** = MANDATORY-load playbook (the craft). Kept TIGHT. References (not absorbs): `composition.yaml` (org registry = DATA) + pattern library (proven shapes). Each changes on its own clock.
- **workflow-lead** = POST-HOC auditor of scripts. Corey: "QA reviews AFTER it runs ... they clearly WORK now, don't add roadblocks." Catches → amend the skill via provisional-skill-lifecycle. Never a pre-run gate.
- **Scripts-are-brittle resolution**: can't avoid JS (workflows ARE js) → MASTER the writing. Runtime=referee (rules unbreakable), skill=playbook (write it right), workflow-lead=post-hoc auditor (compound the playbook).

## 10. SHIPPED SKILLS (this build, all provisional, dogfooding their own lifecycle)

- `skills/team-launch-2/SKILL.md` — forkable Workflow-incarnated leads
- `skills/provisional-skill-lifecycle/SKILL.md` — born-provisional+proof → distinct-incarnation ✓/✗ → 3✓ → canon (can't self-grade)
- `skills/acg-coo/SKILL.md` + `workflows/acg-coo.js` — Tier-1 COO firewall (has 2 known bugs, §12)
- `skills/workflow-js-mastery/SKILL.md` — the craft playbook

## 11. BUILD SEQUENCE

1. **PR-1** (~250 LOC) — THE FOUNDATION. `incarnation_runner.py` (runtime = the memory pipe §5) + 3-layer `mem/` tree + `canon_append.py` (sole writer) + `doctrine_guard.py` (hash-chain hook) + `work_chain_record.py` (TGIM, §8 proven) + `composition.yaml` (org registry) + mastery §0 header + 2 COO fixes (§12). Tests P16/P17 FOR REAL + unblocks self-evolution loop.
2. **dreamer-lead** (local, primary model) — scheduled consolidation pass over mem/canon/ → provisional doctrine proposals + auditor interrogation. (Needs PR-1's mem/ tree.)
3. **composition assembler** — generic workflow reading composition.yaml to build any org shape.
4. **DEFERRED (post-battle-test)**: different-model auditor (leg a) + dreamer-NODE (2nd prior on a different-model substrate of the adopter's choice) + legacy retirements.

## 12. KNOWN DEBT

- `acg-coo.js` 2 bugs (auditor-found, NOT yet fixed — fix in PR-1):
  1. MAJOR: prompt-injection via raw template-interpolation of caller `intent.goal`/`constraints` (lines 51-53, 69-72) — a goal string can override hardcoded constraints. Cure: sanitize/length-cap + fence/escape.
  2. MINOR: soft firewall — return schema lacks `additionalProperties:false` + `maxLength`; raw could smuggle through. Cure: lock the schema.

## 13. LEGACY KILL LIST (retire — fights the workflow grain)

tmux-pane coordination · TeamCreate/TeamDelete (lethal act dies by deletion) · inbox .txt files · 24-slot bash-wheel · hand-edited MEMORY.md + prune cron · agent path-typing · cron-fires-bash · 30-row routing table · SendMessage lifecycle ceremony · shared-mutable-file writes from parallel incarnations.

## 14. RESOURCE DISCIPLINE (learned the hard way)

- **Kokoro/audio + any model-load = ~1GB+ transient process.** SERIALIZE renders, NEVER parallel-fork them. N×1GB = OOM on 32GB box (caused the 5/29→30 RAM freeze).
- litellm/ollama = killed + disabled-on-boot (they caused the phantom-401 storm via RAM pressure + local connection degradation). Don't resurrect without explicit need.

## 15. TEST SCORECARD (substrate-honest, 2026-05-30)

- ✅ **13 TESTED**: incarnation, mem-write, fork, collapse, firewall, nest, auditor, gate, resource, TGIM, agentauth-identity, composability, memory-contract-shape.
- ⚠️ **3 SOFT**: context-frugality (inferred not measured), self-evolution (partial loop), nesting-budget (asserted from tool spec).
- ❌ **2 UNTESTED (correctly deferred — depend on unbuilt things)**: un-checkable-fab cross-model resistance (needs the different-model auditor — adopter's substrate choice), full self-evolution loop (needs runtime).

## 16. OPEN QUESTIONS

- O1: pattern library format (skill vs `patterns/` dir of example scripts).
- O2: canonicalizer/dreamer is a potential single-point-of-failure — "vigilance IS the substrate" there; a buggy consolidation pass could corrupt doctrine in one pass. Revisit before v0.3. (Adversarial-from-jump + git history mitigate but don't eliminate.)
- O3: all numeric thresholds qualitative until production-measured (don't invent numbers — that re-enacts the K=1 memo-theater fab).
- O4: digest-rebuild trigger (+50 lines) is a placeholder number → measure under load.

---
*v0.2 — captures the full 5/29→30 design+test arc. Next: build PR-1 (the runtime = the memory pipe).*
