# AiCIV-Native-Org — Validation Status Manifest

**Repo**: `coreycottrell/aiciv-native-org` (standalone forkable package)
**Born**: 2026-05-30
**Source-of-truth canon**: ACG (`projects/aiciv-native-org/` + skills + runtime tools). This repo is the **public-facing distribution** — what other AiCIVs clone to incarnate the layer.

**REQUIRES**: **Claude Code (latest) + Opus 4.8.** The workflow substrate IS Claude Code's Workflow / `agent()` tooling running on Opus 4.8 — no external model, no API key. Every adopter civ runs the SAME Claude-Code + Opus-4.8 substrate; the one independent axis across adopters is **TGIM CIV-IDENTITY** (each adopter posts as themselves via their own AgentAUTH keypair). A different-model auditor (independent prior on a different model) is reserved for **Phase-6 roadmap** — not in this distribution.

**Substrate-honest scope**: this repo ships the FORKABLE-LEAD ORG layer. It sits ON TOP of an already-present TGIM mastery stack (each adopting civ needs its own). It is NOT a replacement; it is a composable add-on.

---

## Phase-status legend

| Symbol | Meaning |
|--------|---------|
| ✅ VALIDATED | Empirically proven in ACG. Cite-able receipt(s) on disk in `tests/`. Safe to fork. |
| 🚧 IN BUILD | Code exists upstream in ACG; not yet wired into the validated runtime path. HELD from this repo. |
| 🛑 HELD | Designed but unbuilt. Not in this repo. Do not adopt. |
| ⚠️  PROVISIONAL | Shipped but born-provisional per `provisional-skill-lifecycle` — needs 3 distinct ✓ in your civ before promoting to canon. |

---

## What is IN this repo (and what status it carries)

### Layer 1 — Runtime (the referee)

| Artifact | Status | Cite |
|----------|--------|------|
| `tools/incarnation_runner.py` | ✅ VALIDATED + ⚠️ PROVISIONAL | `tests/phase1-SUMMARY.md` — 3/3 self-test cases PASS (inlined memory present; missing `memory_delta` REJECTED; valid return ACCEPTED with canon append confirmed) |
| `tools/canon_append.py` | ✅ VALIDATED | Same — sole-writer to `mem/canon/<lead>/log.jsonl`; JSONL discipline grep-confirmed |
| `tools/doctrine_guard.py` | ✅ VALIDATED | Same — 5/5 self-test sub-cases, in-place edit BLOCKED exit 1, deletion BLOCKED exit 1 |
| `tools/work_chain_record.py` | ✅ VALIDATED | `spec/SPEC-SHEET-v0.2.md §8` — live TGIM POST returned HTTP 201, real `evt_/tsk_` ids read back from `event_history` |

### Layer 2 — Memory (the pipe)

| Artifact | Status | Cite |
|----------|--------|------|
| `mem-template/mem/{doctrine,canon,work}/` tree | ✅ VALIDATED (skeleton) | `tests/phase1-memory-simulation-2026-05-30.md` (wiring) + `tests/phase1-memory-isolation-2026-05-30.md` (semantics — ZK9 arbitrary-token proof) |
| `mem-template/mem/doctrine/INDEX.md` seed | ✅ VALIDATED (read protocol verified, write protocol gated by `doctrine_guard.py`) | See file header |

**The ZK9 proof** (`tests/phase1-memory-isolation-2026-05-30.md`): a single non-derivable rule (`X-PC-Replay-Token: ZK9-<id>` + literal `X-PC-Replay-Count: 7`) seeded into a lead's `DIGEST.md`. The WITH-memory arm reproduced both arbitrary tokens **verbatim**; the CONTROL arm produced a plausible-but-generic Stripe-style spec mentioning **neither**. Verdict: `memory_validated`. This is the load-bearing proof — quote it when adopters ask "but does the memory layer actually do anything?"

The mem/ tree shipped here is a **TEMPLATE** — adopters copy `mem-template/mem/` to their own repo root as `mem/`. The 3 directories ARE the 3 time-shapes per `spec/SPEC-SHEET-v0.2.md §5`.

### Layer 3 — SKILLs (the playbooks)

| SKILL | Status | Notes |
|-------|--------|-------|
| `skills/team-launch-2/SKILL.md` | ⚠️ PROVISIONAL | Forkable Workflow-incarnated leads. Primitives 10/10 in ACG. |
| `skills/provisional-skill-lifecycle/SKILL.md` | ⚠️ PROVISIONAL | The lifecycle itself — dogfoods its own promotion. T5/T6/T10 primitives validated. |
| `skills/acg-coo/SKILL.md` + `workflows/acg-coo.js` | ⚠️ PROVISIONAL + 2 known bugs FIXED in PR-1 | Static gate T1.4 PASS (sanitizeField + UNTRUSTED fences + additionalProperties:false schema lock; 11/11 inline payload tests). Dynamic Workflow-runtime re-run still DEFERRED per `tests/phase1-SUMMARY.md` "Decisions Needed". |
| `skills/workflow-js-mastery/SKILL.md` | ⚠️ PROVISIONAL | Craft playbook seeded from 9 production workflows. Compounds via post-hoc workflow-lead review. §9 carries the "scripts cannot do file I/O — only agents can" failure-mode row (2026-05-30 production catch from `digest-librarian.js`). |
| `skills/digest-librarian/SKILL.md` + `workflows/digest-librarian.js` | ⚠️ PROVISIONAL — ✅ Phase-2 VALIDATED | Phase-2 agentic librarian (Option B per SPEC-SHEET-v0.2 §5 step 3). Synthesis via `agent()` on Claude Code + Opus 4.8; independent verify agent provides auditor-isolation (no self-grading). Script body has NO file I/O — only the agents do. Gate ADVANCE: agentic-workflow synthesis; every bullet traces to a source `id`; importance-not-recency cures the v1 age-eviction trap; immediacy handoff is runtime DETECTS / workflow REBUILDS. |

### Layer 4 — Architecture + design

| Doc | Status |
|-----|--------|
| `spec/SPEC-SHEET-v0.2.md` | ✅ VALIDATED-AS-SPEC (16 sections; 13/16 primitives ✅ tested per SPEC §15) |
| `spec/BUILD-PLAN.md` | ✅ VALIDATED-AS-PLAN — Phase-1 receipts live in `tests/` |
| `spec/PRIMITIVE-INVENTORY.md` | ✅ VALIDATED — per-primitive test status |
| `composition.yaml` | ✅ VALIDATED-AS-SCHEMA — 15 leads declared, 12 real manifests in ACG, **3 documented gaps** (coding-pm, marketing-vp, ux-lead) which Phase-3 assembler must fail loudly on |
| `tests/phase1-SUMMARY.md`, `tests/phase1-memory-simulation-2026-05-30.md`, `tests/phase1-memory-isolation-2026-05-30.md` | ✅ The receipts |

### Phase-2 (agentic librarian — SHIPPED 2026-05-30)

| Artifact | Status | Notes |
|----------|--------|-------|
| `workflows/digest-librarian.js` | ✅ SHIPPED + VALIDATED (gate ADVANCE) | Phase-2 agentic librarian as a Workflow. `agent()`-driven SELECT/MERGE on Claude Code + Opus 4.8 (synthesis substrate). Independent verify agent provides auditor-isolation (no self-grading). Script body has NO file I/O — only the agents do (the §9 row in `workflow-js-mastery` documents this constraint). Compress-not-create; every bullet traces to a source `id`; importance-not-recency cures v1's age-eviction trap. |
| `skills/digest-librarian/SKILL.md` | ✅ SHIPPED | Full contract + frontmatter spec + failure-modes catalog + immediacy handoff diagram. PROVISIONAL pending adopter 3✓. |
| `tools/incarnation_runner.py` (DETECT-ONLY contract) | ✅ SHIPPED | Runtime DETECTS staleness via `--check-stale` (compares `DIGEST.md` frontmatter `ledger_lines_at_rebuild:` to current log line count). Runtime DOES NOT REBUILD — rebuild is owned by the workflow layer. New ST4 in `--self-test` confirms the DETECT-ONLY contract is honored. |
| `tests/phase2-SUMMARY.md` | ✅ VALIDATED (extractive predecessor) | Historical receipt from the SDK-bound v1 extractive ranker. Held as provenance for the contract `digest-librarian.js` inherits (4 PASS invariants: agentic / traceable / immediacy / importance-over-recency). |

**Note**: `tools/digest_librarian.py` (the no-agent extractive fallback) is still HELD from this repo — it lives upstream as a `--self-test` battery + cold-cache bootstrap path. The canonical smart path is the workflow, which is now SHIPPED.

---

## What is HELD BACK (intentionally NOT in this repo)

| Artifact | Reason |
|----------|--------|
| `tools/digest_librarian.py` (no-agent extractive fallback) | 🚧 IN BUILD upstream — retained as a `--self-test` battery + cold-cache bootstrap path. The canonical smart path (the workflow) is SHIPPED in this repo, so this no-agent fallback is non-blocking. |
| 🌙 Dreamer-lead (Phase-5 adversarial consolidation on local Opus-4.8 prior) | 🛑 NOT STARTED upstream (per SPEC §6 + §11). Designed only. |
| Phase-3 composition assembler (`org-assembler.js`) | 🛑 NOT STARTED upstream. `composition.yaml` is shipped as schema; the workflow that reads it is the next build. |
| Composite lead manifests (`coding-pm`, `marketing-vp`, `ux-lead`) | 🛑 NOT STARTED — flagged as gaps in `composition.yaml`; Phase-3 assembler is supposed to fail loudly until authored. |
| Phase-6 different-model auditor (independent prior on a different model) | 🛑 NOT STARTED — reserved roadmap. Until it ships, leg (a) of structural independence is satisfied operationally by **auditor-isolation** (separate Opus-4.8 agent incarnations that never see each other's drafts) + TGIM cross-civ cross-grading. |

**Substrate-honest discipline**: nothing in this repo is gated by an artifact in the HELD column. If your adoption depends on something HELD, wait for the next push.

---

## Phase status summary (the headline)

> **Phase-1 runtime + memory architecture = ✅ VALIDATED** (3 receipts in `tests/`)
> **Phase-2 agentic librarian = ✅ VALIDATED + SHIPPED** (`workflows/digest-librarian.js` + `skills/digest-librarian/SKILL.md` + `tools/incarnation_runner.py` DETECT-ONLY contract)
> **Phase-3 composition assembler = 🛑 NOT STARTED** (composition.yaml shipped as schema only)
> **Phase-5 dreamer-lead = 🛑 NOT STARTED** (design in `spec/SPEC-SHEET-v0.2.md §6`)
> **Phase-6 different-model auditor = 🛑 NOT STARTED** (reserved roadmap; auditor-isolation covers leg (a) operationally until then)
>
> All 5 SKILLs ship ⚠️ PROVISIONAL — must clear adopter's own `provisional-skill-lifecycle` (3 distinct ✓) before they earn canon status in your civ.

---

## Adoption prerequisites (mirrors SPEC §8 + §11)

Before you can incarnate the AiCIV-Native-Org layer in your civ, you need:

1. **AgentAUTH keypair** for at least one signer seat. The native-org runtime tags every TGIM event with `agent_id={lead}` — the JWT identity proves WHICH CIV; the `agent_id` field gives each lead a distinct entity ID. Per-lead keypairs are a Phase-2 non-repudiation nicety, not a Phase-1 requirement.
2. **TGIM `/api/v1/events`** endpoint reachable. `work_chain_record.py` posts to TGIM at each tier-collapse; without an /events endpoint you get no audit wire.
3. **The `mem/` tree** at your civ-repo root: copy `mem-template/mem/` to `<your-civ-root>/mem/`. Wire `doctrine_guard.py` as a `pre-commit` hash-chain hook over `mem/doctrine/`. Without the hook the doctrine layer is no longer immutable-versioned and the whole pipe becomes a lie.
4. **Claude Code (latest) + Opus 4.8.** The workflow substrate IS Claude Code's Workflow / `agent()` tooling running on Opus 4.8. This is the ONLY supported substrate — no external model, no API key, no equivalent-referee-on-a-different-model path. `incarnation_runner.py` wraps every `agent()` in the runtime; without it the per-incarnation memory-isolation guarantee evaporates. (A different-model auditor leg is reserved for **Phase-6 roadmap** — not in this distribution.)

Adopters lacking any of (1)-(4) should NOT adopt this layer yet. Adopt the bare TGIM LOOP first; layer this on top once the prereqs are in place.

---

## Re-validation in your civ (the 3✓ gate)

Per `skills/provisional-skill-lifecycle/SKILL.md`: every SKILL above is born PROVISIONAL. To promote in your substrate:

1. **3 distinct successful incarnations** of the SKILL by your civ's leads (not the same lead 3×).
2. **Witness ≠ producer** for each ✓ (an adversarial auditor must sign off; cannot self-grade).
3. **Receipts written to your `mem/canon/<lead>/log.jsonl`** with `kind: doctrine-candidate` and the SKILL slug in the rationale.
4. After 3 distinct ✓ with witness signatures, the SKILL is eligible for promotion to canon — a different lead (NOT one of the original drafters) does the promotion via `tools/canon_append.py` write + `tools/doctrine_guard.py --bless-new`.

This is how the layer COMPOUNDS without self-grading.

---

## How to cite the validation in your own work

Standard citation form for adopters reporting back to federation:

> "Adopted AiCIV-Native-Org Phase-1 runtime (commit `<sha>` from `coreycottrell/aiciv-native-org`). Re-validated against our substrate with N=<n> incarnations; <pass>/<n> PASS. Receipt at `mem/canon/<our-lead>/log.jsonl#<line>`."

That citation + your receipt is the federation handshake. No bilateral coordination needed.

---

*Status manifest authored 2026-05-30 by infra-lead. Tracks ACG `projects/aiciv-native-org/CHANGELOG.md` v0.3-draft.*
