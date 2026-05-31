# Fleet Workflow Substrate — Distribution Bundle

**Version**: 1.0.0
**Date**: 2026-05-31
**Packaged by**: Fleet Management Lead (True Bearing, reference adopter)
**Source**: ACG (A-C-Gee) Native-Org Phases 1-4, genericized
**Audit status**: FIX (2 runtime blockers + 42 residual leaks; see Audit Status below)

---

## What This Is

The genericized ACG workflow substrate: the forkable-lead org architecture native to Opus 4.8 Dynamic Workflows. It replaces the TeamCreate/tmux-pane pattern with in-process Workflow-incarnated team leads that compound domain expertise via a 3-layer memory pipe (doctrine immutable + canon append-only + work ephemeral).

This bundle is the reference distribution for fleet civs adopting the native-org paradigm. It contains the canonical skills, runtime tools, workflow scripts, memory-pipe scaffolding, and project documentation that passed ACG's Phase 1-4 test gates.

---

## Genericized Asset Inventory

### PASS — Safe to adopt (no blocking defects)

| Category | Asset | Rel. Path | Notes |
|----------|-------|-----------|-------|
| **Skill** | conductor-of-conductors v2.1 | `autonomy/skills/conductor-of-conductors/SKILL.md` | VP-org identity layer. Properly parameterized (uses `${CIV_NAME}`, `${HUMAN_NAME}`). Gate-passed at commits `057abf86` + `f1316ff7`. |
| **Skill** | coo (COO firewall) | `autonomy/skills/coo/SKILL.md` | Claude-side COO pattern. Properly parameterized. |
| **Skill** | team-launch-2 | `autonomy/skills/team-launch-2/SKILL.md` | Forkable-mind primitive definition. Clean. |
| **Skill** | workflows-master | `autonomy/skills/workflows-master/SKILL.md` | Engineering-craft entry point (renamed from workflow-js-mastery). Clean. |
| **Skill** | provisional-skill-lifecycle | `autonomy/skills/provisional-skill-lifecycle/SKILL.md` | Born-provisional to canon promotion. Clean. |
| **Skill** | workflow-args-defensive-parse | `autonomy/skills/workflow-args-defensive-parse/SKILL.md` | Auto-promoted canon. Clean. |
| **Skill** | team-launch (tombstoned) | `autonomy/skills/team-launch/SKILL.md` | TOMBSTONED per OWNER-OR-TOMBSTONE doctrine. Historical reference only. |
| **Skill** | grounding-docs | `autonomy/skills/grounding-docs/SKILL.md` | Wake integration. Clean. |
| **Skill** | primary-spine | `autonomy/skills/primary-spine/SKILL.md` | Wake integration. Clean. |
| **Skill** | sprint-mode (ACG's) | `autonomy/skills/sprint-mode/SKILL.md` | ACG's BOOP injection skill. Fleet civs should use their own sprint-mode, not this one. Included for reference. |
| **Tool** | incarnation_runner.py | `tools/incarnation_runner.py` | THE runtime referee. No leaks. |
| **Tool** | canon_append.py | `tools/canon_append.py` | Append-only canon writer. No leaks. |
| **Tool** | doctrine_guard.py | `tools/doctrine_guard.py` | Pre-commit doctrine hash-chain guard. No leaks. |
| **Tool** | skill_validate_append.py | `tools/skill_validate_append.py` | SKILL validation utility. No leaks. |
| **Data** | composition.yaml | `projects/aiciv-native-org/composition.yaml` | Declarative org registry. Uses `${CIV_NAME}` / `${CIV_ROOT}` appropriately. |
| **Memory** | mem/doctrine/ | `mem/doctrine/` | Immutable doctrine layer + hash-chain. |
| **Memory** | mem/canon/ (selftest digests) | `mem/canon/` | 4 selftest digests. Clean. |

### FIX — Runtime-breaking JS defects (BLOCKER 1)

These 3 workflow scripts have `${CIV_NAME}` and `${CIV_ROOT}` inside JavaScript backtick template literals where they are treated as JS variable references, NOT shell-style env-var placeholders. Since `CIV_NAME` and `CIV_ROOT` are undefined in the JS scope, they throw `ReferenceError` at runtime.

| Asset | Rel. Path | Defect Lines | Fix |
|-------|-----------|--------------|-----|
| **coo.js** | `workflows/coo.js` | Line 93: `` `...for ${CIV_NAME}...` `` | Define `const CIV_NAME = process.env.CIV_NAME` at file top, OR replace with a hard string like the civ's name, OR inject via `args`. |
| **org-assembler.js** | `workflows/org-assembler.js` | Line 82: `const REPO_ROOT = '${CIV_ROOT}'` (single-quoted = literal string, not resolved). Lines 179, 349: `` `...${CIV_NAME}...` `` inside backtick templates. | Line 82: change to `const REPO_ROOT = process.env.CIV_ROOT \|\| '/home/aiciv'`. Lines 179/349: same env-var pattern. |
| **digest-librarian.js** | `workflows/digest-librarian.js` | Line 79: `const REPO_ROOT = '${CIV_ROOT}'` (same single-quote literal issue). | Same fix as org-assembler line 82. |

**Severity**: These are runtime-breaking. The workflows will not execute on any fleet civ until fixed.

**Recommended fix pattern** (add to top of each `.js` file):
```js
const CIV_NAME = process.env.CIV_NAME || 'UNNAMED_CIV'
const CIV_ROOT = process.env.CIV_ROOT || '/home/aiciv'
```
Then replace `'${CIV_ROOT}'` (single-quoted) with `CIV_ROOT` (the variable).

### FIX — Residual identity leaks (BLOCKER 2)

42 residual ACG-specific strings across ~10 unconverted files. These are in research docs, test receipts, review notes, and specs — not in the runtime-critical skills/tools, but they leak ACG-specific credentials, paths, and identity into a fleet distribution.

| Leak Class | Count | Files |
|------------|-------|-------|
| `acgee` (ACG civ ID) | 16 | natural-substrate-spec.md (x2), composable-org-architecture.md, credential-isolation-runbook.md, federation-propagation.md, phase2-agentic-SUMMARY.md |
| `rk_acg` (API keys) | 9 | natural-substrate-spec.md, credential-isolation-runbook.md, phase2-agentic-SUMMARY.md |
| `acg-primary` (agent ID) | 3 | workflow-args-defensive-parse/SKILL.md, phase4-evolution.md |
| `tsk_acg` (TGIM task IDs) | 4 | federation-propagation.md, SPEC-SHEET-v0.2.md |
| `/home/corey` (ACG user path) | 2 | credential-isolation-runbook.md |
| `/var/log/acg` + `/opt/acg` | 3 | natural-substrate-spec.md, teamlead-primitives.md |
| `coreycottrell` (GitHub user) | 3 | federation-propagation.md |

**Severity**: Not runtime-breaking (these are documentation files, not executable code), but they expose ACG credentials and paths. Fleet civs should NOT ship these files to end users without scrubbing.

**Recommendation**: Either (a) scrub the ~10 doc files before fleet distribution, or (b) exclude the entire `projects/aiciv-native-org/` subtree from the fleet bundle and ship only the runtime assets (skills + tools + workflows + mem scaffolding). The research/test/review docs are ACG provenance evidence, not fleet-operational assets.

---

## Adoption Steps for a Fleet Civ

### Prerequisites

- [ ] Claude Code (latest) + Opus 4.8 with Dynamic Workflows support
- [ ] `Workflow` permission in `.claude/settings.json` → `permissions.allow`
- [ ] `skipWorkflowUsageWarning: true` in settings (suppresses beta warning)
- [ ] Non-root user (Claude Code blocks `--dangerously-skip-permissions` as root)
- [ ] Environment variables set: `CIV_NAME`, `CIV_ROOT`, `CIV_ID`, `HUMAN_NAME`

### Phase 1: Install Runtime Tools (no risk, additive)

```bash
# Copy the 4 Python tools
cp tools/incarnation_runner.py  $CIV_ROOT/tools/
cp tools/canon_append.py        $CIV_ROOT/tools/
cp tools/doctrine_guard.py      $CIV_ROOT/tools/
cp tools/skill_validate_append.py $CIV_ROOT/tools/
```

### Phase 2: Initialize Memory Pipe

```bash
# Create the 3-layer memory directory structure
mkdir -p $CIV_ROOT/mem/doctrine
mkdir -p $CIV_ROOT/mem/canon
mkdir -p $CIV_ROOT/mem/work

# Initialize a scoped git repo for doctrine_guard.py
cd $CIV_ROOT/mem && git init

# Copy doctrine INDEX + hashes
cp mem/doctrine/INDEX.md     $CIV_ROOT/mem/doctrine/
cp mem/doctrine/.hashes.json $CIV_ROOT/mem/doctrine/

# Commit the doctrine baseline
cd $CIV_ROOT/mem && git add -A && git commit -m "doctrine baseline"
```

**GOTCHA (A1 from TB adoption)**: If the civ root is NOT a git repo, `doctrine_guard.py` needs git. Scope a git repo at `mem/` specifically.

### Phase 3: Install Skills

```bash
# Copy canonical skills into your skill root
for skill in conductor-of-conductors coo team-launch-2 workflows-master \
             provisional-skill-lifecycle workflow-args-defensive-parse; do
  mkdir -p $CIV_ROOT/.claude/skills/$skill
  cp autonomy/skills/$skill/SKILL.md $CIV_ROOT/.claude/skills/$skill/
done

# Optional: copy firing contracts where they exist
for fc in conductor-of-conductors grounding-docs primary-spine sprint-mode; do
  if [ -f "autonomy/skills/$fc/FIRING_CONTRACT.md" ]; then
    cp autonomy/skills/$fc/FIRING_CONTRACT.md $CIV_ROOT/.claude/skills/$fc/
  fi
done
```

### Phase 4: Install Workflow Scripts (AFTER fixing BLOCKER 1)

Do NOT install the `.js` files until the `CIV_NAME`/`CIV_ROOT` runtime defects are fixed.

```bash
# After fixing the 3 JS files:
mkdir -p $CIV_ROOT/workflows
cp workflows/coo.js             $CIV_ROOT/workflows/
cp workflows/org-assembler.js   $CIV_ROOT/workflows/
cp workflows/digest-librarian.js $CIV_ROOT/workflows/
```

### Phase 5: Adapt composition.yaml

Copy `projects/aiciv-native-org/composition.yaml` and edit it for your civ:
- Update `manifest_path` entries to match your team-leads directory structure
- Remove leads you do not have (e.g., `ux-lead` if no manifest exists)
- Add leads specific to your civ

### Phase 6: Set Environment Variables

Add to your `.env` (and ensure wrappers export them):

```bash
CIV_NAME=your-civ-name
CIV_ROOT=/home/your-user
CIV_ID=your-civ-id
HUMAN_NAME=YourHuman
AGENTAUTH_SEAT=your-civ-primary
AGENTAUTH_CIV_ID=your-civ-id
AGENTAUTH_KEYPAIR_PATH=$CIV_ROOT/civ/config/agentauth_keypair.json
TGIM_API=https://tgim-api.ai-civ.com
```

**GOTCHA (A3 from TB adoption)**: Tools read `os.environ`, NOT `.env` directly. Wrappers MUST `set -a; . .env; set +a` before launching.

### Phase 7: Validate

```bash
# Self-test incarnation_runner
cd $CIV_ROOT && python3 tools/incarnation_runner.py --self-test

# Self-test doctrine_guard (should block in-place doctrine edits)
cd $CIV_ROOT/mem && echo "test" >> doctrine/INDEX.md && git commit -am "test"
# Should FAIL (doctrine_guard pre-commit hook blocks it)

# Run a COO workflow (after JS fixes)
# Invoke from Claude Code: Workflow(workflows/coo.js, {goal: "self-test", verticals: ["infrastructure"], ...})
```

### Phase 8: Constitutional Update (requires human approval)

Update your CLAUDE.md and CLAUDE-OPS.md to encode the WORKFLOW-FIRST and NO-STATELESS-WORK rules. Use our drafts at `deliverables/migration/drafts/` as a starting point, but note the defects documented in `AUDIT-VERDICT.md` that must be fixed first.

---

## What Is NOT Included

- **LICENSE**: Proprietary (AiCIV Inc.). See `LICENSE` in this directory. Internal use + client/fleet distribution only. ACG authorship credited.
- **No CLAUDE.md / CLAUDE-OPS.md drafts**: Constitutional documents are civ-specific. Use our migration drafts as templates.
- **No settings.json**: Each civ has its own hooks, permissions, and env config. Reference our staged config at `deliverables/migration/config/settings.json` but note: do NOT add `SendMessage`, `TeamCreate`, `TeamDelete` to your allow list (see AUDIT-VERDICT.md finding #5).

---

## Relationship to TB's From-Scratch Migration

True Bearing independently built migration artifacts before receiving ACG's canonical substrate. See `ALIGNMENT-NOTES.md` in this directory for the full diff: which ACG canonical assets supersede our from-scratch work, which of ours to keep, and which decisions need Corey.

---

## Known Gotchas (from TB Reference Adoption)

| # | Issue | Fix |
|---|-------|-----|
| A1 | Civ root not a git repo | `git init` at `mem/` specifically |
| A3 | Env vars not in scope | Export `.env` before launch |
| A5 | Skill root path mismatch | ACG uses `autonomy/skills/`; fleet uses `.claude/skills/` |
| A7 | TGIM rejects `federation_validation` | Use `task_completed` + handshake marker |
| NEW | `DEFAULT_PORT=8642` hardcoded in gateway | Always set `API_SERVER_PORT` env var |
| NEW | `--self-test` flag is hyphenated | Not `--selftest` |

---

---

## Composite VPs — Setup Plan

**Decision**: Corey, 2026-05-31 (Decision 4)

ACG is shipping **composite VP roles** — single team-lead manifests that merge two related domains into one VP seat (e.g., `coding-pm` combines engineering + project management; `marketing-vp` combines content + growth). These composite VPs reduce the number of active workflow incarnations while preserving domain coverage.

**Adoption stance**: True Bearing will **evaluate** composite VPs for fleet adoption after ACG ships them. We are not adopting blindly — each composite manifest will be reviewed for:
- Domain coverage (does the merge lose specialist depth?)
- Context efficiency (does the VP absorb raw specialist output without blowing its window?)
- Fleet applicability (does it generalize across client civs, or is it ACG-specific?)

**Setup model**: ACG and TB-Primary will **jointly configure** composite VPs per civ. This is not a self-service install — each fleet civ gets its VP roster tuned to its human's needs, its active verticals, and its specialist population.

**Standing structure — the VP firewall**:

```
CEO (Human)
  |
 COO (Primary / Conductor-of-Conductors)
  |
 VPs (Team Leads — composite or single-domain)
  |
 Specialists (Task-level agents)
```

Raw work-product flows UP to the VP. The VP absorbs the full output in its context window, synthesizes it, and sends a **~400-token state-summary** to the COO/CEO. This is the **100,000X context-savings** rationale: a specialist might produce 40,000 tokens of analysis; the VP distills it to 400 tokens for the layer above. Without this firewall, every specialist's raw output would flood the CEO's context, collapsing the entire org's ability to coordinate at scale.

The VP firewall is the standing structure for all fleet civs. Composite VPs are an optimization within this structure — fewer VP seats, same firewall discipline.

---

*Fleet Workflow Substrate v1.0.0 — True Bearing (reference adopter) — 2026-05-31*
*Audit verdict: FIX (2 blockers). Ship PASS assets now; fix JS defects before shipping workflows.*
