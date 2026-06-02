# Alignment Notes: ACG Canonical vs TB From-Scratch

> ⚠️ **THIS IS A WORKED EXAMPLE, NOT A TEMPLATE.** This file is a one-time diff between ACG's canonical substrate and True Bearing's from-scratch artifacts — it records *another civ's* adoption decisions and is full of ACG/TB-specific identity. **DO NOT copy this into your civ.** Read it as a reference for the *kind* of decision you'll face, then make your own. See the repo-root `ADAPTING.md`.

**Date**: 2026-05-31
**Author**: Fleet Management Lead (True Bearing)
**Purpose**: Diff between ACG's gate-passed canonical substrate and True Bearing's independently-built migration artifacts. Determines what to ADOPT from ACG, what to KEEP from ours, and what needs Corey's call.

---

## Executive Summary

ACG's canonical substrate is architecturally superior for the core orchestration identity and runtime infrastructure. Our from-scratch work is superior for fleet-facing operational guidance and historical accuracy. The two are complementary, not competing. The recommended path: ADOPT ACG's canonical skills + tools + workflows (after fixing the 2 JS blockers), KEEP our Fleet Migration Kit + Audit Verdict + sprint-mode conversion, and present our constitutional drafts as starting points that ACG's canonical now informs but does not replace.

---

## File-by-File Alignment

### 1. conductor-of-conductors SKILL.md

| Dimension | ACG Canonical (v2.1) | TB From-Scratch | Verdict |
|-----------|---------------------|-----------------|---------|
| **Identity framing** | VP-org language per Corey directive. Primary = CEO, direct reports = domain-area VPs. "Synthesized firewall" RETIRED from identity layer. 14 sections covering the full org model. | Workflow-first migration focus. Two Rules + Core Mechanism + patterns. Migration guide old-to-new. | **ADOPT ACG** |
| **Memory pipe** | Full memory-pipe doctrine: incarnation_runner + canon_append + memory_delta = VP compounds every run. This IS the civilization thesis. | Mentioned (incarnation preamble with manifest + memory + scratchpad) but not codified as the compounding mechanism. No mention of canon_append or memory_delta. | **ADOPT ACG** |
| **COO pattern** | Integrated: COO is one of 3 relationships Primary holds. coo.js is the reference implementation. | Not present. Our conductor skill has no COO concept. | **ADOPT ACG** |
| **Decision tree** | Single-mode: "find the VP who owns it." No exceptions. 5 routing questions. | Two Rules format. Less prescriptive on routing. | **ADOPT ACG** |
| **Migration guide** | Not included (assumes clean adoption, not migration). | Full migration guide: old pattern to new pattern, single-lead and multi-lead examples, deleted failure classes. | **KEEP OURS as supplementary** |
| **Clarifying questions** | Not present (our audit flagged this as a gap in our version; ACG's doesn't have it either, but their VP model is more self-documenting). | Not present (our audit flagged it as dropped). | **Neither has it. Low priority.** |
| **"The hole"** | Not present. No undefined escape hatches. | Present and undefined. Our audit flagged it as smuggled policy. | **ACG is correct to omit it. DROP "the hole" from all our assets.** |
| **Parameterization** | Properly parameterized: `${CIV_NAME}`, `${HUMAN_NAME}` throughout. | Hardcoded "Corey" in 2 places. Our audit flagged this. | **ADOPT ACG** |
| **Auditor-isolation gate** | Dedicated section. Links to provisional-skill-lifecycle. Structural enforcement via skill_validate_append.py. | Not addressed. | **ADOPT ACG** |
| **Known gaps / refinement log** | Validation log with dated entries. Pending witness signatures. | Known gaps section + refinement log with historical entries (2026-02-19, 2026-05-30, 2026-05-31). | **KEEP OURS as supplement (historical entries are TB-specific)** |

**DECISION: ADOPT ACG's conductor-of-conductors v2.1 as the canonical skill. Supplement with our migration guide and historical refinement log as a fleet-facing adoption appendix.**

---

### 2. team-launch / team-launch-2

| Dimension | ACG Canonical | TB From-Scratch | Verdict |
|-----------|--------------|-----------------|---------|
| **team-launch (tombstoned)** | Preserved in-place per OWNER-OR-TOMBSTONE doctrine. Narrow live-steer-VP niche acknowledged. Full forkable-mind content. | Deprecation banner + comparison table + collapsed historical details block. | **ADOPT ACG** (tombstone is cleaner, live-steer niche is honest) |
| **team-launch-2** | Full skill: forkable-mind primitive, single-writer rule, self-evolution, honest gaps (7 unproven items). Validation log with empirical receipts. | No team-launch-2 equivalent (our conductor skill absorbed the Workflow pattern inline). | **ADOPT ACG** |
| **"~1000 concurrent" claim** | Present in team-launch-2 description line 3: "scalable to ~1000 parallel incarnations". | Present in our deprecated team-launch comparison table line 39 (flagged by our audit as smuggled). | **Flag for both. The claim is unverified. Fleet docs should say "scale ceiling removed (Workflow-based)" not cite a specific number.** |

**DECISION: ADOPT ACG's team-launch (tombstoned) and team-launch-2. Remove the "~1000 concurrent" claim from both when distributing.**

---

### 3. sprint-mode SKILL.md

| Dimension | ACG Canonical | TB From-Scratch (v3.1.0) | Verdict |
|-----------|--------------|--------------------------|---------|
| **Content** | ACG's own BOOP injection: tmux send-keys, hermes-ops owned. Not TB-specific. | TB's full BOOP protocol (3.1.0): counter, haiku, drift, wheel. Step 6 Drift spawn converted to Workflow. Our audit passed it. | **KEEP OURS** |
| **Drift conversion** | Not applicable (ACG's sprint-mode is a different beast). | Step 6 properly converted: Task(subagent_type="boop-watcher") replaced with Workflow-incarnated Drift. DRIFT_SCHEMA firewall. Validated BOOP 579. | **KEEP OURS** |

**DECISION: KEEP our sprint-mode v3.1.0. ACG's sprint-mode is their injection mechanism, not a fleet-distributable BOOP protocol. Each civ has its own BOOP.**

---

### 4. coo (COO firewall) — NEW from ACG

| Dimension | ACG Canonical | TB Equivalent | Verdict |
|-----------|--------------|---------------|---------|
| **Skill** | Full COO skill: intent-in/synthesis-out contract, anti-patterns, when-to-use-which. | No equivalent. | **ADOPT ACG** |
| **Workflow (coo.js)** | Production-quality: sanitization, prompt-injection defense (UNTRUSTED fences), schema-locked returns, `additionalProperties:false` + `maxLength`. | No equivalent. | **ADOPT ACG (after fixing line 93 CIV_NAME blocker)** |
| **Org-assembler (org-assembler.js)** | Generic declarative assembler: reads composition.yaml, incarnates any org shape. Multi-tenancy proven (T3.2). | No equivalent. | **ADOPT ACG (after fixing lines 82/179/349 blockers)** |
| **Digest-librarian (digest-librarian.js)** | Agentic file-IO: compress-not-create, importance-not-recency, verify agent. | No equivalent. | **ADOPT ACG (after fixing line 79 blocker)** |

**DECISION: ADOPT all 3 ACG workflow scripts + the COO skill. These are the crown jewels of the substrate. Fix the JS blockers first.**

---

### 5. workflows-master — NEW from ACG

| Dimension | ACG Canonical | TB Equivalent | Verdict |
|-----------|--------------|---------------|---------|
| **Content** | Full engineering-craft skill: parallel vs pipeline, schema-forced returns, firewall return pattern, nesting budget, resource discipline, production failure catalog. v0.2.0 (provisional). | No equivalent. Our conductor skill had inline code examples but no dedicated craft doctrine. | **ADOPT ACG** |

**DECISION: ADOPT. This is the builder-layer companion to the identity-layer conductor skill.**

---

### 6. provisional-skill-lifecycle — NEW from ACG

| Dimension | ACG Canonical | TB Equivalent | Verdict |
|-----------|--------------|---------------|---------|
| **Content** | 4 rules: born provisional with proof, use logs dated note, 3 clean checkmarks to canon, provisional always surfaced. Auditor-isolation gate. Backed by primitive test receipts. | No equivalent. | **ADOPT ACG** |

**DECISION: ADOPT. This is the immune system against fabrication amplification at scale.**

---

### 7. Runtime Tools (Python)

| Tool | ACG | TB | Verdict |
|------|-----|-----|---------|
| incarnation_runner.py | Full runtime referee: inline-memory assembly, validate-return, canon write. CLI: --self-test, --check-stale, --show-inline. | We have this already (adopted during native-org integration). | **Already adopted. Verify versions match.** |
| canon_append.py | Sole append-only writer. Boss-attributed. | Already adopted. | **Already adopted.** |
| doctrine_guard.py | Pre-commit hash-chain guard. | Already adopted. | **Already adopted.** |
| skill_validate_append.py | Structural auditor-isolation gate. | Already adopted. | **Already adopted.** |

**DECISION: Tools are already adopted from TB's native-org integration. Verify the genericized versions match what we have.**

---

### 8. composition.yaml

| Dimension | ACG Canonical | TB Equivalent | Verdict |
|-----------|--------------|---------------|---------|
| **Content** | 15 leads: 2 composite VPs (coding-pm, marketing-vp) + 11 real verticals + 2 Tier-2 specialists. ACG manifest paths (autonomy/team-leads/). | Our composition.yaml from native-org adoption (TB-specific paths, .claude/team-leads/). | **KEEP OURS (our paths are correct for our directory structure). Use ACG's as reference for the composite VP pattern.** |

---

### 9. Constitutional Drafts (CLAUDE.md, CLAUDE-OPS.md)

| Dimension | ACG Canonical | TB From-Scratch Drafts | Verdict |
|-----------|--------------|------------------------|---------|
| **CLAUDE.md** | ACG has `review/drafts/CLAUDE-md-proposed-changes.md` and `CLAUDE-md-workflows-first-v2.md` — these are ACG's OWN proposed changes to ACG's constitution, not fleet-distributable. | Our v3.7.0-fork draft: 10 sections rewritten. 4 defects flagged by our audit (Task(project-manager) self-contradiction, unflagged history, orphaned content, undefined "the hole"). | **KEEP OURS as the starting point for TB's constitution. Fix the 4 audit defects. ACG's drafts inform but do not replace — they target ACG's constitution, not ours.** |
| **CLAUDE-OPS.md** | No equivalent in the substrate bundle. | Our draft: 3 sections rewritten. 4 defects flagged (smuggled verticals, aspirational code refs, wisdom nuance, cosmetic creep). | **KEEP OURS. Fix the 4 audit defects. Remove the 5 smuggled verticals — propose them separately.** |

**DECISION: Constitutional docs are civ-specific. Our drafts are the right starting point for TB. ACG's conductor-of-conductors v2.1 now provides the identity-layer doctrine that our drafts should reference rather than re-derive.**

---

### 10. settings.json

| Dimension | Our Staged Config | Live Config | Verdict |
|-----------|------------------|-------------|---------|
| **Workflow permission** | Added correctly. | Not present (pre-migration). | **ADOPT the Workflow addition.** |
| **SendMessage/TeamCreate/TeamDelete** | Added (our audit flagged as CRITICAL regression). | NOT present in live config. | **DO NOT ADD. Our audit is correct: adding banned patterns to the allow list is a regression.** |

**DECISION: Add ONLY `Workflow` to `permissions.allow`. Do NOT add SendMessage, TeamCreate, TeamDelete.**

---

### 11. Fleet Migration Kit (TB-only)

| Asset | Status | Verdict |
|-------|--------|---------|
| FLEET-MIGRATION-KIT.md | TB-authored. Step-by-step adoption checklist, gotcha catalog, rollback plan. | **KEEP. This is fleet-facing operational guidance that ACG's substrate does not provide.** |
| AUDIT-VERDICT.md | TB-authored. 7-file audit with defect-level findings. | **KEEP. This is the quality gate for the distribution.** |
| migrate-civ.workflow.js | TB-authored. Parameterized migration workflow. | **KEEP. Useful for fleet automation.** |

---

## Summary: Adopt vs Keep vs Drop

### ADOPT from ACG (supersedes our from-scratch equivalents)

1. **conductor-of-conductors v2.1** — supersedes our v1 conductor skill (but keep our migration guide + refinement log as supplement)
2. **coo skill + coo.js** — entirely new capability we lack
3. **org-assembler.js** — entirely new capability we lack
4. **digest-librarian.js** — entirely new capability we lack
5. **team-launch-2** — supersedes our inline Workflow pattern in conductor
6. **team-launch (tombstoned)** — supersedes our deprecated team-launch
7. **workflows-master** — entirely new capability we lack
8. **provisional-skill-lifecycle** — entirely new capability we lack
9. **workflow-args-defensive-parse** — auto-promoted canon, new capability

### KEEP from TB (ACG does not provide equivalents or ours are civ-specific)

1. **sprint-mode v3.1.0** — our BOOP protocol, civ-specific
2. **FLEET-MIGRATION-KIT.md** — fleet operational guidance
3. **AUDIT-VERDICT.md** — quality gate
4. **migrate-civ.workflow.js** — fleet automation
5. **Constitutional drafts (CLAUDE.md, CLAUDE-OPS.md)** — civ-specific, but now informed by ACG's canonical identity layer
6. **composition.yaml (TB version)** — our paths, our vertical structure
7. **native-org README (TB additions)** — Two Inviolable Rules section, adoption prereqs

### DROP (our audit found them defective; ACG canonical supersedes)

1. **"The hole" escape hatch** — undefined, smuggled, not in ACG's canonical. Drop from all our assets.
2. **"~1000 concurrent" performance claim** — unverified in both ACG and our files. Replace with defensible statement.
3. **SendMessage/TeamCreate/TeamDelete in settings.json** — our audit correctly flagged this as a regression.

### SUPERSEDED (our from-scratch files that ACG's canonical replaces)

| Our File | Superseded By | Action |
|----------|--------------|--------|
| `converted/conductor-of-conductors/SKILL.md` | ACG `autonomy/skills/conductor-of-conductors/SKILL.md` v2.1 | Archive ours. Deploy ACG's. |
| `converted/team-launch/SKILL.md` | ACG `autonomy/skills/team-launch/SKILL.md` (tombstoned) | Archive ours. Deploy ACG's. |
| (no equivalent) | ACG `autonomy/skills/team-launch-2/SKILL.md` | Deploy ACG's as new. |
| (no equivalent) | ACG `autonomy/skills/coo/SKILL.md` + `workflows/coo.js` | Deploy ACG's as new. |
| (no equivalent) | ACG `autonomy/skills/workflows-master/SKILL.md` | Deploy ACG's as new. |
| (no equivalent) | ACG `autonomy/skills/provisional-skill-lifecycle/SKILL.md` | Deploy ACG's as new. |

---

## Decisions Requiring Corey

1. **Constitutional authority**: Our CLAUDE.md and CLAUDE-OPS.md drafts are the only artifacts that modify the constitution. They require 90% vote + Corey approval per Article IX. ACG's conductor-of-conductors v2.1 now provides the identity doctrine these drafts should encode — does Corey want us to revise the drafts to align with ACG's VP-org framing before presenting them?

2. **"The hole" question**: ACG's canonical does not define or reference "the hole." Our from-scratch work introduced it as an undefined escape hatch. Should there be ANY exception to the no-stateless-work rule, or is the answer simply "no exceptions" (which is what ACG's canonical implies)?

3. **License for fleet distribution**: Neither ACG's raw bundle nor the genericized version includes a LICENSE file. Fleet distribution to non-AiCIV-Inc entities needs a license decision.

4. **JS blocker fixes — who owns them**: The 3 workflow scripts need `process.env.CIV_NAME` / `process.env.CIV_ROOT` fixes. Should TB fix and redistribute, or should ACG fix upstream and re-ship?

5. **Residual leak scrubbing vs exclusion**: 42 ACG-specific strings in the research/test/review docs. Scrub them for fleet distribution, or exclude those files from the fleet bundle entirely?

6. **Composite VP adoption**: ACG's composition.yaml defines 2 composite VPs (coding-pm, marketing-vp) that TB does not have. Should we adopt these as part of the substrate, or are they ACG-specific org topology?

---

*Alignment Notes v1.0.0 — Fleet Management Lead, True Bearing — 2026-05-31*
