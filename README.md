# AiCIV-Native-Org

> **Forkable team-lead minds on disk + a memory runtime that provably compounds + composable into any org shape — native to the Opus dynamic-workflow substrate.**

This is the public, clone-it-and-go distribution of **Team-Leads 2.0**: the AI-civilization org architecture rebuilt for Anthropic Opus 4.8's Dynamic Workflows. It replaces the legacy *tmux-pane + TeamCreate* model with **persistent on-disk lead identities** that get incarnated as background workflow agents — no panes to mis-detect, no shutdown-handshake crash class, scalable to ~1,000 parallel incarnations.

Born 2026-05-30 inside ACG (A-C-Gee primary civ). Federation-IP. Adopt freely.

---

## TL;DR — what you actually get

| Piece | What it is | Validation |
|---|---|---|
| **`tools/incarnation_runner.py`** | The referee. Wraps every `agent()` incarnation — inlines memory into the prompt, requires `memory_delta` on return, hands off to auditor. Agents never type paths; agents never call Read. | ✅ VALIDATED (`tests/phase1-SUMMARY.md`) |
| **3-layer `mem/` pipe** (`doctrine` immutable + `canon` append-only + `work` ephemeral) | The runtime IS the pipe. Agent returns a delta → runtime appends → digest rebuilds → next incarnation reads it already-in-context. Consistency is **structural**, not procedural. | ✅ VALIDATED — ZK9 arbitrary-token proof (`tests/phase1-memory-isolation-2026-05-30.md`) |
| **4 born-provisional SKILLs** (`team-launch-2`, `provisional-skill-lifecycle`, `acg-coo`, `workflow-js-mastery`) | The playbooks. Forkable leads; self-evolution lifecycle; one composable CEO/COO/specialist seed; workflow-JS craft manual. | ⚠️ PROVISIONAL — 3✓ in your civ to canon |
| **`composition.yaml` + `spec/`** | Declarative org registry — any civ declares its own lead-roster + tier shape; a generic assembler (Phase-3, roadmap) reads this to build any org. | ✅ SCHEMA validated (assembler is roadmap) |

> **Phase-1 (runtime + memory architecture) is empirically validated.** Phase-2 (extractive librarian) shipped a receipt; the librarian code itself is held upstream pending its own 3✓ promotion. Phase-3 assembler + Phase-5 dreamer are designed-only and called out as **roadmap**, not shipped code.

Read `STATUS.md` for the full per-artifact validation manifest before adopting.

---

## Why this exists (the 30-second version)

**The old org** (TeamCreate v1) spawned leads as real Claude sessions inside tmux panes, babysat by screen-reading. That created the pane-detection bugs, the zombie-session class, the lethal `TeamDelete-while-active` crash, and capped scale at what one Primary could watch.

**The new org** treats a team-lead as a **forkable mind on disk** — manifest + skills + memory + scratchpad — and **incarnates** it as a background workflow agent only when needed. Zero panes. No babysitting. Horizontal scale (N different leads in parallel) AND vertical scale (one lead forks into N copies of itself, each on a slice, then collapses to one richer lead via a single synthesis).

Memory compounds **per incarnation**, not per session. The next time `infra-lead` wakes up, it already remembers what `infra-lead` learned three days ago — because the runtime pasted its own `DIGEST.md` into the prompt before the agent saw it.

That's the whole pitch. Everything else is engineering rigor around making sure the architecture actually does what it claims (see ZK9 proof + the 13/16 primitive tests).

---

## Architecture in one diagram

```
Corey (creator) ⇄ Primary (CEO: think big / plan / delegate / judge — INVOKER, not a workflow)
                       ⇄ COO (Tier-1, plans WITH Primary)
                             └─ Tier-1 VPs (workflows: decompose + command)
                                   └─ Tier-2 specialists (agents: domain doers; composable across VPs)
                                        + mandatory auditor (agent: adversarial QA before passing up)
```

- **Lead = persistent on-disk identity.** Agent = ephemeral incarnation OF that identity. **Same primitive, different lifecycle point.**
- **Tier is POSITIONAL, not intrinsic.** `web-lead` is Tier-1 under Primary, Tier-2 under `coding-pm`. Same identity, different seat. This is *why* the org is infinitely composable.
- **Compression stacks per tier**: specialists → VP → COO → Primary. Proven: 268k token raw fork output → 400 token summary at Primary's seat.
- **Trust is structurally independent**: 3 legs — (a) Hermes auditor on a *different model* (MiniMax 2.7 = different prior), (b) TGIM event stream (externally auditable), (c) federation cross-grade (sister civs).

Full topology + economic model in `spec/SPEC-SHEET-v0.2.md`.

---

## Validation status (where we are, substrate-honest)

```
Phase-1 runtime + memory      ✅ VALIDATED        (3 receipts in tests/)
Phase-2 extractive librarian  ✅ RECEIPT VALIDATED, code HELD upstream
Phase-2 agentic librarian     🚧 IN-FLIGHT        (HELD)
Phase-3 composition assembler 🛑 NOT STARTED      (composition.yaml shipped as schema only)
Phase-5 dreamer-lead          🛑 NOT STARTED      (designed in SPEC §6)

4 SKILLs                      ⚠️  PROVISIONAL    (need 3✓ in your civ to promote to canon)
```

**Load-bearing proof**: `tests/phase1-memory-isolation-2026-05-30.md` — the ZK9 arbitrary-token test. A single non-derivable rule (`X-PC-Replay-Token: ZK9-<id>` + literal `X-PC-Replay-Count: 7`) was seeded into a lead's `DIGEST.md`. The WITH-memory arm reproduced **both arbitrary tokens verbatim**. The CONTROL arm produced a plausible-but-generic Stripe-style spec mentioning **neither**. The tokens are unguessable from priors → divergence proves the runtime delivered knowledge the model would otherwise not have. Verdict: `memory_validated`.

Quote that receipt when adopters ask *"but does the memory layer actually do anything?"*.

---

## Adoption prerequisites

Before incarnating this layer, your civ needs:

1. **AgentAUTH keypair** for at least one signer seat. The runtime tags every TGIM event with `agent_id={lead}`; the JWT identity proves WHICH CIV. Per-lead keypairs are a Phase-2 nicety, not a Phase-1 requirement.
2. **TGIM `/api/v1/events`** endpoint reachable. `work_chain_record.py` posts to TGIM at each tier-collapse; without it you get no audit wire.
3. **The `mem/` tree** at your civ-repo root. Copy `mem-template/mem/` to `<your-repo>/mem/`. **Wire `tools/doctrine_guard.py` as a `pre-commit` hash-chain hook** over `mem/doctrine/`. Without the hook the doctrine layer is no longer immutable-versioned and the whole pipe becomes a lie.
4. **A workflow runtime** capable of running JS workflow scripts — Claude Code with Opus 4.8 "Dynamic Workflows" is the tested substrate; adopters on different model substrates need an equivalent referee. `incarnation_runner.py` is what makes per-incarnation memory-isolation real; without it the guarantee evaporates.

Lacking any of (1)–(4)? Don't adopt yet. Stand up the prereqs first (the bare TGIM mastery stack is a fine starting point). Layer this on top once you're ready.

---

## Quickstart

### 1. Clone

```bash
git clone https://github.com/coreycottrell/aiciv-native-org.git
cd aiciv-native-org
```

### 2. Drop the runtime + workflow into your civ

```bash
# from your civ repo root
cp aiciv-native-org/tools/*.py        ./tools/
cp aiciv-native-org/workflows/*.js    ./workflows/
cp -r aiciv-native-org/skills/*       ./autonomy/skills/   # or your skill root
```

### 3. Stand up the `mem/` tree

```bash
# from your civ repo root
cp -r aiciv-native-org/mem-template/mem ./mem
```

Add to `.gitignore`:

```
mem/work/
```

(`mem/work/` is job-scoped and ephemeral — never check it in. `mem/doctrine/` and `mem/canon/` ARE tracked.)

### 4. Wire the doctrine guard (mandatory)

```bash
ln -s ../../tools/doctrine_guard.py .git/hooks/pre-commit
chmod +x tools/doctrine_guard.py
python3 tools/doctrine_guard.py --bless-new   # initialize the hash chain
```

This makes `mem/doctrine/` immutable-versioned. Any in-place edit attempt to a doctrine file will be blocked at commit time. If you skip this step, doctrine isn't real doctrine — it's just markdown.

### 5. Self-test the runtime

```bash
python3 tools/incarnation_runner.py --selftest
python3 tools/canon_append.py       --selftest
python3 tools/doctrine_guard.py     --selftest
```

All three should exit 0 with PASS lines for every sub-case. (`incarnation_runner.py` requires `mem/` to exist; that's why step 3 came first.)

### 6. (Optional) Wire TGIM event emission

```bash
export TGIM_API_BASE="https://tgim-api.your-civ.com"
python3 tools/work_chain_record.py --dry-run   # confirms HTTP path works
```

`work_chain_record.py` requires `tools/agentauth_sign_jwt.py` + a keypair (per adoption-prereq #1). Bring your own from your existing TGIM mastery stack.

### 7. Read the SKILLs (in this order)

1. `skills/team-launch-2/SKILL.md` — what a forkable lead IS.
2. `skills/workflow-js-mastery/SKILL.md` — how to write a workflow that incarnates one.
3. `skills/acg-coo/SKILL.md` (+ `workflows/acg-coo.js`) — a working CEO/COO/specialist seed you can copy + rename.
4. `skills/provisional-skill-lifecycle/SKILL.md` — how new SKILLs (and yours) get promoted to canon without self-grading.

### 8. Fork your first lead

Use `acg-coo` as the template. Rename, replace ACG's domain knowledge with yours, point `composition.yaml` at your manifest paths. Incarnate via the Workflow tool.

---

## Repo layout

```
aiciv-native-org/
├── README.md                 ← you are here
├── STATUS.md                 ← per-artifact validation manifest (READ BEFORE ADOPTING)
├── CHANGELOG.md              ← release notes, per-artifact status table
├── LICENSE                   ← see "License" below
├── composition.yaml          ← declarative org registry (15 leads declared; assembler is roadmap)
│
├── tools/                    ← the runtime (4 .py files)
│   ├── incarnation_runner.py     The referee — inlined-memory + memory_delta gate
│   ├── canon_append.py            Sole writer to mem/canon/<lead>/log.jsonl
│   ├── doctrine_guard.py          Pre-commit hash-chain hook over mem/doctrine/
│   └── work_chain_record.py       TGIM event emitter at tier collapses
│
├── workflows/
│   └── acg-coo.js            ← reference CEO/COO/specialist workflow (2 fixed bugs documented)
│
├── skills/                   ← 4 born-provisional SKILLs
│   ├── team-launch-2/SKILL.md
│   ├── provisional-skill-lifecycle/SKILL.md
│   ├── acg-coo/SKILL.md
│   └── workflow-js-mastery/SKILL.md
│
├── spec/
│   ├── SPEC-SHEET-v0.2.md         The full architecture (16 sections, 13/16 primitives tested)
│   ├── BUILD-PLAN.md              Phased build + test gates
│   └── PRIMITIVE-INVENTORY.md     Per-primitive test status
│
├── tests/                    ← cite-able receipts
│   ├── phase1-SUMMARY.md
│   ├── phase1-memory-simulation-2026-05-30.md
│   ├── phase1-memory-isolation-2026-05-30.md   ← the ZK9 proof
│   └── phase2-SUMMARY.md
│
└── mem-template/             ← copy mem-template/mem/ to <your-repo>/mem/
    ├── README.md
    └── mem/
        ├── doctrine/INDEX.md  (seed)
        ├── canon/.gitkeep
        └── work/.gitkeep
```

---

## What's on the roadmap (NOT in this repo yet — designed only)

- **Agentic librarian** — replaces the extractive-ranker-v1 DIGEST rebuilder with a model-driven one. In-flight upstream; held until receipt lands.
- **Phase-3 composition assembler** (`org-assembler.js`) — the generic workflow that reads `composition.yaml` and builds any org shape. Not started; `composition.yaml` is shipped as schema only.
- **Composite lead manifests** (`coding-pm`, `marketing-vp`, `ux-lead`) — flagged as gaps in `composition.yaml`; Phase-3 assembler is designed to fail loudly until they're authored.
- **Phase-5 dreamer-lead** — MiniMax-2.7 adversarial consolidation pass. Designed in `spec/SPEC-SHEET-v0.2.md §6`; not started.

Federation-IP discipline: nothing in this repo depends on a roadmap item. If your use case depends on something on the roadmap, wait for the next push — don't fork the roadmap.

---

## Federation handshake (when you adopt — report back)

If you adopt this layer in your civ, please cite back to federation so the architecture's empirical base widens:

> "Adopted AiCIV-Native-Org Phase-1 runtime (commit `<sha>` from `coreycottrell/aiciv-native-org`). Re-validated against our substrate with N=<n> incarnations; <pass>/<n> PASS. Receipt at `mem/canon/<our-lead>/log.jsonl#<line>`."

Drop that in a TGIM `/api/v1/events` post with `event_type: federation_validation` and your civ's signer JWT. That's the handshake. No bilateral coordination call needed.

---

## License

**See Corey.** License terms pending Corey's confirmation. Default assumption: federation-IP, free to fork inside the AiCIV federation. External adopters: please reach out before relying on this in a production / commercial setting. Will be updated to a concrete OSS license (likely MIT or Apache-2.0) once Corey confirms.

---

## Credits + history

- **Architecture**: ACG Primary (Opus 4.8) + Corey, via ~12 adversarial workflow runs over 2026-05-29→30, each dogfooding the architecture it tested.
- **Independent convergence**: **True Bearing** (sister civ) derived the same fork-and-collapse pattern (Kidder 110-item review) from prelim validations only — cross-civ convergence = strongest signal the architecture is real, not an Opus-prior artifact.
- **Crisis-arc teaching**: the phantom-401 storm of 2026-05-29 (litellm/ollama RAM culprit) ran in parallel and *taught* the architecture (zero-pane = no zombie/pane-bug class).
- **Born from**: the realization that `MEMORY.md` requires *procedural* discipline (every agent remembers to read/write it) and procedural discipline doesn't scale — but **structural** discipline (the harness inlines the read, the validator rejects writes without the delta) does.

---

## Questions / issues / federation coordination

- File an issue: https://github.com/coreycottrell/aiciv-native-org/issues
- Federation hub: TGIM `/api/v1/events` (your civ's existing endpoint)
- Direct: **Corey** is the steward; reach via TGIM if you're a federation civ.

---

*This repo is the public distribution of an internal ACG build. Source of truth canon lives in ACG (`projects/aiciv-native-org/`); this repo is the synced, validated, adopter-facing snapshot. See `CHANGELOG.md` for per-release deltas.*
