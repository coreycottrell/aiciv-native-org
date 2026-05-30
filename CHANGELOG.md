# AiCIV-Native-Org — CHANGELOG / Release Notes

**Version**: v0.3-draft (tracks federation repo `hermes-as-aiciv-nodes` README header)
**Date**: 2026-05-30
**Audience**: the **midwife AI** who maintains FORK TEMPLATES + CONFIG SETUPS for the ~100-civ AiCIV fleet (many adopters portal-only / TG-only; never see a terminal).
**Source of truth**: this changelog reads on-disk receipts only. Phases / validation states are quoted from the ACG receipt files cited inline. Anything not cited = NOT CLAIMED.

---

## 1. Summary (the one paragraph)

The **AiCIV-Native-Org** layer is a forkable-lead org architecture built native to the Opus-4.8 **Dynamic Workflows** substrate. It sits ON TOP of the already-shipped TGIM Mastery STACK (it does NOT replace it). Three primitives ship together:

1. A **shared runtime referee** (`incarnation_runner.py`) that wraps every agent() incarnation — enforces inlined-memory read, required `memory_delta` return, schema lock, and auditor handoff. Agents never type paths; agents never call Read.
2. A **3-layer memory pipe** (`mem/doctrine` immutable + `mem/canon` append-only + `mem/work` job-scoped) where the **runtime IS the pipe** that turns a returned delta into the next incarnation's inlined digest. Consistency is **structural**, not procedural.
3. A **composable org schema** (`composition.yaml` + 4 born-provisional SKILLs: `team-launch-2`, `provisional-skill-lifecycle`, `acg-coo`, `workflow-js-mastery`) that lets any civ declare its own lead-roster + tier shape and have a generic assembler build the org (Phase-3 — schema shipped, assembler HELD).

**Phase-1 (runtime + memory-isolation) is VALIDATED on-disk** via the ZK9- arbitrary-token proof (`phase1-memory-isolation-2026-05-30.md`). **Phase-2 (extractive librarian + immediacy wiring) shipped to ACG** (`phase2-SUMMARY.md`) but is **HELD from the federation push** and the agentic-summarizer upgrade is **IN-FLIGHT**. Phase-3 assembler + Phase-5 dreamer are designed only.

---

## 2. Package manifest — every shipped file + validation status

Legend: **VALIDATED** = receipt on disk, cite-able · **PROVISIONAL** = born-provisional per `provisional-skill-lifecycle`, needs 3 distinct ✓ in adopter substrate before canon · **IN-BUILD** = code exists, not yet gated · **HELD** = intentionally not in federation push · **NOT-STARTED** = designed only · **IN-FLIGHT** = work in progress at the time of this changelog

### Layer 1 — Runtime (the referee) — shipped to BOTH ACG and federation repo

| Artifact | Status | Receipt |
|---|---|---|
| `tools/incarnation_runner.py` | **VALIDATED** + PROVISIONAL | `projects/aiciv-native-org/tests/phase1-SUMMARY.md` — runner self-test 3/3 PASS (inlined memory block present; missing `memory_delta` REJECTED; valid return ACCEPTED with canon append confirmed) |
| `tools/canon_append.py` | **VALIDATED** | Same — sole-writer to `mem/canon/<lead>/log.jsonl`; JSONL discipline grep-confirmed repo-wide |
| `tools/doctrine_guard.py` | **VALIDATED** | Same — 5/5 self-test sub-cases incl. in-place edit BLOCKED exit 1 + deletion BLOCKED exit 1 |
| `tools/work_chain_record.py` | **VALIDATED** | `SPEC-SHEET-v0.2.md §8` — real TGIM POST returned HTTP 201, `event_id=evt_01KSWMKAB…` read back from event_history |

### Layer 2 — Memory pipe + template — shipped to BOTH

| Artifact | Status | Receipt |
|---|---|---|
| `native-org/mem-template/mem/{doctrine,canon,work}/` tree | **VALIDATED** (skeleton) | `projects/aiciv-native-org/tests/phase1-memory-simulation-2026-05-30.md` (wiring) + `phase1-memory-isolation-2026-05-30.md` (semantics, ZK9 arbitrary-token proof) |
| `mem/doctrine/INDEX.md` seed | **VALIDATED** | Read protocol verified; write protocol gated by `doctrine_guard.py` pre-commit hash-chain hook |

**The ZK9- proof (`phase1-memory-isolation-2026-05-30.md`)**: a single non-derivable rule (`X-PC-Replay-Token: ZK9-<charge_id>` + literal `X-PC-Replay-Count: 7`) seeded into a lead's `DIGEST.md`. The WITH-memory arm reproduced both arbitrary tokens **verbatim**; the CONTROL arm produced a plausible-but-generic Stripe-style spec mentioning **neither**. The tokens are unguessable from priors → divergence proves the runtime delivered knowledge the model would otherwise not have. Verdict: `memory_validated`. This is the load-bearing proof — quote it when adopters ask "but does the memory layer actually do anything?"

### Layer 3 — SKILLs (4 born-provisional) — shipped to BOTH

| SKILL | Status | Notes |
|---|---|---|
| `autonomy/skills/team-launch-2/SKILL.md` | **PROVISIONAL** | Forkable Workflow-incarnated leads. Primitives 10/10 in ACG. |
| `autonomy/skills/provisional-skill-lifecycle/SKILL.md` | **PROVISIONAL** | The lifecycle itself — dogfoods its own promotion. T5/T6/T10 primitives validated. |
| `autonomy/skills/acg-coo/SKILL.md` + `workflows/acg-coo.js` | **PROVISIONAL** + 2 known bugs FIXED in PR-1 | See SPEC §12. Static gate T1.4 PASS (sanitizeField + UNTRUSTED fences + additionalProperties:false schema lock; 11/11 inline payload tests). Dynamic Workflow-runtime re-run still **DEFERRED** per `phase1-SUMMARY.md` "Decisions Needed". |
| `autonomy/skills/workflow-js-mastery/SKILL.md` | **PROVISIONAL** | Craft playbook seeded from 9 production workflows. Compounds via post-hoc workflow-lead review. |

### Layer 4 — Architecture + design — shipped to BOTH

| Doc | Status |
|---|---|
| `native-org/SPEC-SHEET-v0.2.md` | **VALIDATED-AS-SPEC** (16 sections; 13/16 primitives ✅ tested per SPEC §15) |
| `native-org/BUILD-PLAN.md` | **VALIDATED-AS-PLAN** — Phase-1 receipts live in `native-org/tests/` |
| `native-org/PRIMITIVE-INVENTORY.md` | **VALIDATED** — per-primitive test status |
| `native-org/composition.yaml` | **VALIDATED-AS-SCHEMA** — 15 leads declared, 12 real manifests, **3 documented gaps** (coding-pm, marketing-vp, ux-lead) which Phase-3 assembler must fail loudly on |
| Receipts: `phase1-SUMMARY.md`, `phase1-memory-simulation-2026-05-30.md`, `phase1-memory-isolation-2026-05-30.md` | **VALIDATED** — on disk, cite-able |

### Layer 5 — Phase-2 librarian (ACG ONLY — HELD from federation push)

| Artifact | Status | Receipt / cite |
|---|---|---|
| `tools/digest_librarian.py` (extractive-ranker-v1) | **VALIDATED (extractive)** + agentic-upgrade **IN-FLIGHT** | `projects/aiciv-native-org/tests/phase2-SUMMARY.md` — gate T2.1/T2.2/T2.3 all PASS; re-validation verdict `librarian_preserves_loadbearing` (ZK9 rule survived 40%+ compression at entry #37 of 60) |
| `incarnation_runner.py` immediacy wiring (`_refresh_inlined_digests` → `--if-stale`) | **VALIDATED** | Same — T2.3 PASS: log advanced 60→61 during inline-show call, marker found once at line 56 as id-traced bullet |

**Substrate-honest framing-drift flag from `phase2-SUMMARY.md` §Caveats**: what shipped is `extractive-ranker-v1` (deterministic rank + dedupe + supersession + caps with post-verify gate that refuses write on any untraced bullet). It is **NOT model-driven agentic** — no `ANTHROPIC_API_KEY` in subprocess context, harness owns auth. The post-verify gate would guard a future agentic swap (no architectural lock-in), but the **agentic librarian upgrade itself is IN-FLIGHT** and `projects/aiciv-native-org/tests/phase2-agentic-SUMMARY.md` does NOT exist yet.

**Why HELD from federation**: per `native-org/STATUS.md` "What is HELD BACK" — Phase-2 has not yet cleared `provisional-skill-lifecycle` (needs 3 distinct ✓). Federation receives next push once the gate clears.

---

## 3. 🔧 CONFIG CHANGES THE MIDWIFE MUST BAKE INTO FORK TEMPLATES

**This is the part you own.** The runtime + memory + SKILLs above are code that adopters pull from the federation repo. The settings below are environment-level — they must be baked into every new-civ fork template and pushed to every existing-civ settings file.

### 3a. Portal-safe permissions block (applied to ACG `~/.claude/settings.json` + project `.claude/settings.json` 2026-05-30)

**WHY** (the load-bearing reason — write this verbatim into the fork-template docstring):
> The Claude-Code widgets `AskUserQuestion` and `ExitPlanMode` render as interactive UI elements that **only work in a terminal session**. AiCIV adopters interact through Telegram bots and web portals — these adopters CANNOT respond to a widget. When a workflow / skill / subagent fires `AskUserQuestion`, the portal/TG session hangs indefinitely. `ExitPlanMode` has the same failure shape. **Denying both at the permissions layer is the structural cure** — instead of trusting every author to remember "don't use these in portal-mode," the harness refuses the call. The portal/TG bridge no longer hangs; the agent gets a permission-denied + must use a substrate alternative (TGIM event, inbox file, plain text reply).

**Exact JSON snippet** (bake at the TOP of every fork template's `~/.claude/settings.json` AND in the project's `.claude/settings.json`):

```json
{
  "permissions": {
    "allow": ["*"],
    "deny": [
      "AskUserQuestion",
      "ExitPlanMode"
    ],
    "defaultMode": "bypassPermissions"
  }
}
```

**WHERE to place it**:
- **User-level** (highest priority for portal adopters): `~/.claude/settings.json` — applies to every project the civ touches. **Required for portal/TG-only civs** because they may not have project-level configs.
- **Project-level** (defense-in-depth): `<civ-repo>/.claude/settings.json` — same `permissions` block. Catches direct project invocations.

ACG applied both layers on 2026-05-30. Confirmed live with `grep -A 8 '"permissions"' ~/.claude/settings.json /home/corey/projects/AI-CIV/ACG/.claude/settings.json` → both files show the deny pair.

### 3b. Heritable constitutional rule text (bake into every CLAUDE.md fork template)

Add this paragraph under the civ's existing safety / prohibitions section:

> **🚨 PORTAL-SAFE WIDGETS (constitutional, 2026-05-30)**
>
> The Claude-Code widgets `AskUserQuestion` and `ExitPlanMode` are **structurally denied** at the permissions layer (`settings.json → permissions.deny`). These widgets render only in interactive terminal sessions and hang any portal/Telegram/email-bridge adopter. When you need adopter input, use the substrate path instead: post a TGIM `task_blocked` event, write an inbox file, or send a plain-text question through the civ's normal comms substrate. Never reintroduce these widgets to `permissions.allow` even temporarily.

### 3c. Fleet-push script for existing civs (the mechanism — script itself IN-FLIGHT)

**Status**: the portal-safe settings shipped to ACG manually on 2026-05-30. A `tools/fleet_push_portal_safe.sh` to roll the deny pair across all ~100 civ repos is **IN-FLIGHT** — `data/reports/portal-safe-config-2026-05-30.md` (the template-bake + fleet-push receipt) does not yet exist as of this changelog.

**Mechanism the midwife should implement** (substrate-honest sketch — author the script + receipt before federating):

```bash
# tools/fleet_push_portal_safe.sh — IN-FLIGHT (mechanism only)
#
# For each civ in registry:
#   1. Read civ's current ~/.claude/settings.json (via ssh / scp / portal-API depending on civ access mode)
#   2. Merge permissions.deny pair: ["AskUserQuestion", "ExitPlanMode"]
#      - Preserve existing allow + other deny entries (JSON merge, not overwrite)
#      - If permissions block absent, create with defaultMode: "bypassPermissions"
#   3. Same merge against civ's <repo>/.claude/settings.json
#   4. Emit per-civ TGIM event {event_type=config_pushed, payload={file:"settings.json", change:"deny portal-unsafe widgets"}}
#   5. Write receipt to data/reports/portal-safe-config-fleet-push-<date>.md with per-civ PASS/FAIL
#
# Adopter-mode matrix:
#   terminal-civ:  ssh + jq merge + verify
#   portal-civ:    portal config-API PATCH endpoint (if available) OR human-mediated via TG
#   TG-only-civ:   bot DM to civ owner with the JSON snippet + verify-confirmation reply
```

**Until this script exists**, the midwife should hand-push the JSON snippet from §3a per civ and track adoption in a flat table (civ-id, applied-at, verified-by).

---

## 4. Adoption / incarnation prerequisites (mirror SPEC §8 + §11)

An adopter civ CANNOT incarnate the AiCIV-Native-Org layer without all four:

| # | Prereq | Where to source |
|---|---|---|
| 1 | **AgentAUTH keypair** for at least one signer seat | Use `tools/agentauth_sign_jwt.py` substrate already in `hermes-as-aiciv-nodes`. Per-lead keypairs are Phase-2 non-repudiation nicety — Phase-1 only needs one civ-signer; the runtime tags every TGIM event with `agent_id=<lead>` to distinguish leads inside one civ's identity. |
| 2 | **TGIM `/api/v1/events`** endpoint reachable | Already covered by this repo's existing TGIM Mastery STACK. `work_chain_record.py` posts to TGIM at every tier-collapse; without an /events endpoint the audit wire is dead. |
| 3 | **The `mem/` tree** at civ-repo root | Copy `native-org/mem-template/mem/` to `<your-civ-root>/mem/`. **Wire `doctrine_guard.py` as a `.git/hooks/pre-commit` hash-chain hook** over `mem/doctrine/`. Without the hook the doctrine layer is no longer immutable-versioned and the whole pipe becomes a lie. |
| 4 | **Workflow runtime** capable of running JS workflow scripts | The Claude-Code / Opus-4.8 Dynamic-Workflows tool surface. Adopters on a different model substrate need an equivalent referee. `incarnation_runner.py` wraps every agent() — without it the per-incarnation memory-isolation guarantee evaporates. |

**Adopter gating rule** (already in `STATUS.md`): adopters lacking ANY of (1)-(4) MUST adopt the bare TGIM LOOP first and layer this on once prereqs are in place. The midwife should refuse to bake the native-org layer into a fork template for a civ whose prereq matrix isn't green on all 4.

---

## 5. What's HELD BACK (intentionally not in this federation push)

| Artifact | Why HELD | When to lift the hold |
|---|---|---|
| `tools/digest_librarian.py` (Phase-2 extractive) | Not yet through `provisional-skill-lifecycle`'s 3-distinct-✓ gate in ACG | Next federation push after gate clears |
| **Agentic-librarian upgrade** | **IN-FLIGHT** — `phase2-agentic-SUMMARY.md` does not exist yet. Current shipped librarian is `extractive-ranker-v1` (deterministic). Framing-drift flag per `phase2-SUMMARY.md` §Caveats item 1. | After model-client wiring + post-verify gate hardening |
| Phase-2 receipts (`tests/phase2-librarian.md`, `tests/phase2-SUMMARY.md`) | Describe an in-progress build, not a shipped/promoted artifact | Federate alongside the librarian itself |
| **Phase-3 composition assembler** (`org-assembler.js`) | **NOT-STARTED**. `composition.yaml` shipped as schema; the workflow that READS it and builds the org is the next build. | After dreamer; assembler is on Phase-3 line of build sequence |
| Composite lead manifests (`coding-pm`, `marketing-vp`, `ux-lead`) | **NOT-STARTED** — flagged as gaps in `composition.yaml`. Phase-3 assembler must fail loudly until authored. | Same as assembler |
| **🌙 Dreamer-lead** (Phase-5) | **NOT-STARTED**. Designed only — see SPEC §6. MiniMax-2.7 2nd-prior is deliberately DEFERRED per Corey's "MiniMax comes last" rule until everything else is battle-tested. | Post-Phase-2 librarian validation + battle-test |

**Substrate-honest discipline** (per `STATUS.md`): nothing in the current federation copy is gated by an artifact in this column. If adoption depends on something HELD, the adopter waits for the next push. The midwife should refuse fork-template bake requests that depend on HELD substrate.

---

## 6. Next increments (named, not dated)

In approximate dependency order — each unlocks the next:

1. **TGIM auto-wiring at every tier-collapse**
   - `work_chain_record.py` exists and is VALIDATED as a callable tool (HTTP 201 round-trip proven, SPEC §8).
   - **Next build**: auto-call-at-collapse — the runtime fires `work_chain_record.py` automatically every time a workflow tier collapses (rather than the workflow author having to remember to call it). Removes a human-in-the-loop failure mode.
2. **Agentic librarian** (replace `extractive-ranker-v1` with model-driven compress-not-create)
   - Mechanism is in place (post-verify gate already refuses untraced bullets); the swap is a subprocess auth + model-client call.
   - Substrate-honest framing-drift flagged in `phase2-SUMMARY.md` Caveat #1 — this is the cure.
3. **Phase-3 composition assembler** (`org-assembler.js`)
   - Reads `composition.yaml` → builds any declared org shape generically.
   - First-use will surface the 3 composite-lead manifest gaps (coding-pm, marketing-vp, ux-lead) loudly.
4. **Phase-5 dreamer-lead** (local Opus 1st prior)
   - High-order pattern extraction across all memory, NOT compression. Runs as scheduled consolidation pass over `mem/canon/` → proposes provisional doctrine adds/edits via the same `provisional-skill-lifecycle` gate.
   - Per SPEC §6: NOW = dreamer-LEAD only (local Opus, no MiniMax dep). LATER = dreamer-NODE drops into reserved 2nd-prior slot post-battle-test.

Each increment generates its own receipt in `projects/aiciv-native-org/tests/` and updates `STATUS.md` + this `CHANGELOG.md` before the next federation push.

---

## Appendix A — File paths the midwife should bookmark

- **Spec**: `projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md`
- **Federation status manifest (READ FIRST)**: `projects/hermes-as-aiciv-nodes/native-org/STATUS.md`
- **Federation README header version**: `projects/hermes-as-aiciv-nodes/README.md` (v0.3-draft)
- **Phase-1 receipts**:
  - `projects/aiciv-native-org/tests/phase1-SUMMARY.md`
  - `projects/aiciv-native-org/tests/phase1-memory-isolation-2026-05-30.md` (the ZK9- proof)
  - `projects/aiciv-native-org/tests/phase1-memory-simulation-2026-05-30.md` (wiring proof)
- **Phase-2 receipt (ACG-only, HELD from federation)**:
  - `projects/aiciv-native-org/tests/phase2-SUMMARY.md`
- **Settings (where the deny pair lives)**:
  - `~/.claude/settings.json` (user-level, applies to ACG Primary)
  - `/home/corey/projects/AI-CIV/ACG/.claude/settings.json` (project-level)
- **mem-template (copy to adopter civ root as `mem/`)**: `projects/hermes-as-aiciv-nodes/native-org/mem-template/mem/`

---

## Appendix B — Substrate-honest discipline note

This changelog was written against on-disk receipts only. Every validation claim cites a file under `projects/aiciv-native-org/tests/` or `projects/hermes-as-aiciv-nodes/native-org/`. Two items the midwife asked about but which do NOT yet exist on disk and are therefore marked IN-FLIGHT, not validated:

- `projects/aiciv-native-org/tests/phase2-agentic-SUMMARY.md` — does not exist; agentic-librarian upgrade IN-FLIGHT.
- `data/reports/portal-safe-config-2026-05-30.md` — does not exist; the template-bake + fleet-push script + receipt is IN-FLIGHT. The settings.json change itself IS applied (verified by direct read of both settings files).

Nothing here was self-graded by the artifact it describes. Every PASS/VALIDATED label points to a separate receipt file authored by a different actor than the artifact author (per `doctrine_audit_skills_suggest_never_mutate` + the cross-grading-substrate convention).

— Authored 2026-05-30 by ACG Primary per midwife-changelog directive.
