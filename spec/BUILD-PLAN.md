# AiCIV-Native Org — Phased Build + Test Plan

**Author**: ACG Primary (Opus 4.8), 2026-05-30 ~15:00Z, pre-context-reset.
**Purpose**: a fresh post-reset session executes this COLD. Every phase = build steps (exact paths) + a TEST GATE that must pass before the next phase. No phase advances on a claim; only on an on-disk receipt.
**Read first**: `projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md` (the what + why) and `PRIMITIVE-INVENTORY.md` (tested vs not). This doc is the HOW + WHEN.
**Discipline**: substrate-honest. Each test writes a receipt to `projects/aiciv-native-org/tests/`. workflow-lead reviews scripts POST-HOC (never a pre-run gate). MiniMax/Hermes integration is DEFERRED to Phase 6+ (Corey rule: after everything else battle-tested).

---

## STATE AT PLAN-TIME (what already exists — do NOT rebuild)

ALREADY SHIPPED + ON DISK:
- Skills: `autonomy/skills/team-launch-2/SKILL.md`, `autonomy/skills/provisional-skill-lifecycle/SKILL.md`, `autonomy/skills/acg-coo/SKILL.md`, `autonomy/skills/workflow-js-mastery/SKILL.md`
- Mechanism: `workflows/acg-coo.js` (has 2 known bugs — fix in Phase 1)
- Project: `projects/aiciv-native-org/` with MISSION.md, spec/ (SPEC-SHEET-v0.2 + PRIMITIVE-INVENTORY + this), research/ (10 files), memory-design/, tests/ (primitive-tests-2026-05-30.md)
- TGIM tooling: `tools/tgim_event.py`, `tools/agentauth_sign_jwt.py` — TGIM write+readback PROVEN
- Email hook fixed: `.claude/hooks/block_direct_email.py` whitelists send_mom_email.py

ALREADY TESTED (13 primitives — don't re-test, see SPEC §15): incarnation, mem-write, fork, collapse, firewall, nest, auditor, gate, resource, TGIM, agentauth-identity, composability, memory-contract-shape.

---

## PHASE 0 — Cold-start grounding (every fresh session does this first)
**Build**: nothing. **Do**:
1. Read `projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md` fully.
2. Read this BUILD-PLAN.md.
3. Read `.claude/scratchpad-daily/<today>.md` for any state since this plan.
4. `git -C /home/corey/projects/AI-CIV/ACG log --oneline -10` to see what's landed.
**TEST GATE 0**: can state, in one paragraph, which phase is next + why. No build until grounded.

---

## PHASE 1 — The Runtime (the memory pipe) + COO hardening
**Goal**: `incarnation_runner.py` — the ONE shared referee that turns `memory_delta` → inlined memory. This IS the answer to "how does memory_delta become inlined memory." Everything bolts onto this.

**Build (exact files)**:
1. `tools/incarnation_runner.py` — wraps an agent invocation. Responsibilities:
   - READ: assemble inlined-memory block (doctrine INDEX + own `mem/canon/<lead>/DIGEST.md` + parent DIGEST + `mem/work/<job>/brief.md`), ~5k token budget. Paste into the agent prompt. (Agent gets NO Read tool for memory.)
   - VALIDATE-RETURN: reject any return missing the required `memory_delta:{canon_appends:[], rationale}` field.
   - WRITE: call `tools/canon_append.py` to append each canon item (runtime writes, not agent).
   - Single-writer: only this runtime writes to `mem/`.
2. `tools/canon_append.py` — SOLE writer to `mem/canon/<lead>/log.jsonl`. Append-only. Closed enum kind={finding|decision|retraction|doctrine-candidate}. After append, if log grew +50 lines since last DIGEST → trigger digest rebuild (Phase 2 owns the smart version; Phase 1 ships a MECHANICAL placeholder: last-200-lines).
3. `tools/doctrine_guard.py` — pre-commit hook (wire into `.git/hooks/pre-commit` or `.claude/hooks/`): blocks in-place edits to `mem/doctrine/*` (hash-chain check); doctrine is immutable-versioned.
4. Create the tree: `mem/doctrine/` (+ `INDEX.md`), `mem/canon/` (+ `.gitkeep`), `mem/work/` (+ `.gitkeep`). Add `mem/work/` to `.gitignore` (job-scoped, ephemeral).
5. FIX `workflows/acg-coo.js` 2 bugs (SPEC §12): (a) sanitize/length-cap `intent.goal`+`intent.constraints` before template interpolation (lines ~51-53, 69-72) — fence+escape; (b) add `additionalProperties:false` + `maxLength` to the return schema (lines ~74-80).
6. Add `§0 MANDATORY-LOAD + companions` header to `autonomy/skills/workflow-js-mastery/SKILL.md` pointing at `composition.yaml` (Phase 3) + a patterns index.

**TEST GATE 1** (write receipt `tests/phase1-runtime.md`):
- T1.1: run `incarnation_runner.py` on a trivial agent → confirm inlined-memory block was injected (grep the prompt log) AND return WITHOUT memory_delta is REJECTED, WITH is accepted.
- T1.2: confirm `canon_append.py` appended a line to `mem/canon/<testlead>/log.jsonl` AND nothing else wrote there (single-writer).
- T1.3: confirm `doctrine_guard.py` BLOCKS an in-place edit to a `mem/doctrine/` file.
- T1.4: re-run acg-coo via Workflow → confirm the 2 bugs are gone (try a malicious `goal` string that previously could override constraints → now neutralized; confirm schema rejects extra fields).
- ADVANCE only if T1.1–T1.4 all pass on-disk.

---

## PHASE 2 — The Digest Librarian (Option B, compress-not-create)
**Goal**: replace Phase-1's mechanical digest with the agentic librarian. Corey: "option b all day."

**Build**:
1. `workflows/digest-librarian.js` — a Workflow that, given a `mem/canon/<lead>/log.jsonl`, rebuilds `mem/canon/<lead>/DIGEST.md` (≤200 lines). CONSTRAINT (enforce in prompt + a post-check): every digest line must trace to a log line (compress-not-create; cannot invent). Frontmatter: `last_rebuilt_at`, `ledger_lines_at_rebuild`.
2. Wire `incarnation_runner.py`: when log lags DIGEST by >50 lines, call digest-librarian inline before the read completes (harness refuses stale DIGEST).

**TEST GATE 2** (receipt `tests/phase2-digest.md`):
- T2.1: seed a `log.jsonl` with 60 synthetic findings → run librarian → DIGEST.md ≤200 lines, frontmatter correct.
- T2.2: TRACEABILITY check — every line in DIGEST.md maps to a log entry (no invented content). Automated grep or a verifier agent.
- T2.3: stale-refusal — manually lag the DIGEST, run an incarnation → confirm runtime forces rebuild before read.

---

## PHASE 3 — Declarative Composition (composition.yaml + assembler)
**Goal**: build any org shape from manifest data, not hand-written scripts.

**Build**:
1. `projects/aiciv-native-org/composition.yaml` — the org registry. Per lead: `id`, `domain`, `tier_default`, `commands:[tier-2 ids]`, `mandatory_auditor:bool`, `manifest_path`, `posture`. Seed with: a coding-PM (commands web-lead, security-lead), a marketing-VP (commands web-lead, ux-lead), + the existing real leads.
2. `workflows/org-assembler.js` — generic Workflow: given a top lead id + intent, reads composition.yaml, incarnates that lead as a workflow, its `commands` as Tier-2 agents, fires the mandatory auditor if flagged, returns compressed synthesis. Uses incarnation_runner for every agent.

**TEST GATE 3** (receipt `tests/phase3-composition.md`):
- T3.1: assemble coding-PM from composition.yaml → it commands web+security + auditor fires → compressed return. (Generalizes the hand-built composable-proof.)
- T3.2: assemble marketing-VP → confirm web-lead is reused (own incarnation, boss-attributed) with NO collision vs T3.1's web-lead.
- T3.3: malformed composition.yaml (cycle / orphan / missing manifest) → assembler fails LOUDLY, not silently.

---

## PHASE 4 — Self-Evolution Loop (full, end-to-end)
**Goal**: prove a lead authors a skill from a real catch → distinct incarnation validates → 3✓ → canon. (Today only the partial loop ran.)

**Build**: mostly wiring existing skills (provisional-skill-lifecycle + incarnation_runner). Add:
1. `tools/skill_validate_append.py` — appends a dated ✓/✗ Validation-Log line to a provisional skill; ENFORCES witness != author (auditor-isolation); promotes to canon at 3 distinct ✓.

**TEST GATE 4** (receipt `tests/phase4-evolution.md`):
- T4.1: incarnation hits a real gotcha → authors a provisional skill stub with proof.
- T4.2: a DIFFERENT incarnation uses it → logs ✓ (and the tool REJECTS a ✓ from the author).
- T4.3: 3 distinct ✓ → auto-promote provisional→canon. Confirm on-disk frontmatter flip.

---

## PHASE 5 — The Dreamer (dreamer-lead, local Opus only)
**Goal**: living adversarial memory consolidation. (dreamer-NODE/MiniMax is Phase 6, deferred.)

**Build**:
1. `workflows/dreamer-lead.js` — scheduled consolidation pass: reads ALL `mem/canon/*/log.jsonl` + `mem/doctrine/` → draws cross-cutting patterns → checks vs current memory → proposes provisional adds/edits to `mem/doctrine/` (as candidates, NOT direct writes).
2. AUDITOR interrogation stage IN the same workflow: adversarially tests each dreamer proposal (real? useful? traces to evidence?). Survivors → provisional canon via provisional-skill-lifecycle gate.
3. Schedule: a wheel slot OR cron-fires-AI (NOT bash) — defer actual scheduling to Phase 7; for now runnable on-demand.

**TEST GATE 5** (receipt `tests/phase5-dreamer.md`):
- T5.1: seed mem/canon with 3 related findings across 2 leads → dreamer proposes the unifying principle.
- T5.2: plant a SEDUCTIVE-BUT-FALSE pattern in the corpus → auditor interrogation REJECTS the dreamer's bad proposal (adversarial-from-jump works).
- T5.3: confirm survivors land as PROVISIONAL (not auto-canon) + trace to evidence.

---

## PHASE 6 — DEFERRED: MiniMax/Hermes integration (only after Phases 1-5 battle-tested)
Per Corey: all Hermes/MiniMax comes last. Then:
1. dreamer-NODE on MiniMax 2.7 (2nd prior) into the reserved slot.
2. MiniMax-2.7 Hermes auditor (independence leg a) — closes the un-checkable-fab gap.
3. TGIM work-chain auto-posting from every collapse: `autonomy/workflow_runtime/work_chain_record.py` (or fold into incarnation_runner) → POST to /events at each single-writer step. (TGIM write already proven; this automates it.)
**TEST GATE 6**: cross-model auditor catches an un-checkable fab that same-model validators miss (the surviving R1 risk).

---

## PHASE 7 — DEFERRED: legacy retirement + scheduling
Retire SPEC §13 kill-list once the new system carries the load: tmux-pane coord, TeamCreate/TeamDelete, inbox .txt, 24-slot bash-wheel, hand-edited MEMORY.md, agent path-typing, cron-fires-bash, routing table, SendMessage lifecycle, shared-mutable writes. One at a time, each behind a test that the new path covers it.

---

## CRITICAL-PATH SUMMARY
Phase 1 (runtime/pipe) → 2 (digest) → 3 (composition) → 4 (evolution) → 5 (dreamer-lead) → [6 MiniMax, 7 legacy: deferred].
Each gate writes a receipt to `projects/aiciv-native-org/tests/phaseN-*.md`. No advance without on-disk pass.

## STANDING DIRECTIVES (carry into every phase)
- Substrate-honest: tested-or-flagged, never claimed.
- workflow-lead reviews scripts POST-HOC, never a pre-run gate.
- One shared runtime; TGIM = universal adapter.
- Memory consistency STRUCTURAL not procedural (no Read tool for memory; memory_delta required).
- Serialize RAM-heavy renders (no parallel model-loads).
- MiniMax/Hermes deferred to Phase 6+.
- Don't resurrect litellm/ollama (caused the 401 storm).
