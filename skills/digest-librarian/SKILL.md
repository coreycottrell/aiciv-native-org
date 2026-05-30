---
name: digest-librarian
description: The AGENTIC digest librarian (Option B per SPEC-SHEET-v0.2 §5 step 3) implemented as a Workflow. Synthesis runs through agent() on the Claude-Code workflow runtime (Opus 4.8). The script body has NO file I/O — only the agent does. The python tool tools/digest_librarian.py is retained ONLY as a no-agent extractive fallback; the canonical smart path is workflows/digest-librarian.js. Requires Claude Code (latest) + Opus 4.8 (the substrate this layer is native to).
version: 0.1.0
status: provisional
authored: 2026-05-30
mechanism: workflows/digest-librarian.js (the runnable librarian; runtime invokes via Workflow tool)
backed_by:
  - spec/SPEC-SHEET-v0.2.md §5 (memory pipe step 3) + §6 (librarian vs dreamer separation) + §9 (one shared runtime — Claude Code + Opus 4.8)
  - tests/phase2-SUMMARY.md (4/4 PASS gate the v1 extractive librarian shipped against; the workflow rebuild preserves all four invariants — agentic, traceable, immediacy-via-runtime, importance-over-recency — without any direct-API SDK dependency in the python layer)
sibling_skills:
  - skills/workflow-js-mastery/SKILL.md (the craft playbook — load before authoring/editing this workflow)
  - skills/acg-coo/SKILL.md (sibling workflow; same firewall-tight-return pattern)
  - skills/provisional-skill-lifecycle/SKILL.md (how this skill amends + promotes)
spec_anchors:
  - SPEC-SHEET-v0.2 §5 — COMPRESS-NOT-CREATE; <=200 lines; <=8000 chars; importance-not-recency
  - SPEC-SHEET-v0.2 §6 — distinct from DREAMER (this is low-order compression; dreamer is high-order pattern-draw)
  - SPEC-SHEET-v0.2 §7 — validator-step IS the win; post-verify gate makes agentic safe
  - SPEC-SHEET-v0.2 §9 — ONE shared runtime (Claude Code + Opus 4.8); the only independent axis across adopters is TGIM CIV-IDENTITY (each adopter posts as themselves via their own AgentAUTH keypair)
---

# digest-librarian — Workflow-Native, Claude-Code-Substrate

> The model SELECTS / MERGES. The post-verify gate DISPOSES.
> Compress, never create. Importance, never recency.

## Substrate scope (read this first)

This workflow is native to **Claude Code (latest) running Opus 4.8 Dynamic Workflows**. Synthesis goes through `agent()` on the workflow runtime's model — no external API key, no direct-model-SDK call. Every adopter civ runs the SAME Claude-Code + Opus-4.8 substrate; the only independent axis is **TGIM CIV-IDENTITY** (each adopter signs/posts as themselves via their own AgentAUTH keypair).

A "different-model auditor" path (a second model with an independent prior) is intentionally deferred to Phase-6 per SPEC-SHEET-v0.2 §6 + §11 — until then, structural independence relies on auditor-isolation (separate agent incarnations of the same model) plus TGIM cross-civ cross-grading.

## The two artifacts

| Artifact | Role | Owns |
|---|---|---|
| `workflows/digest-librarian.js` | The runnable workflow | All paths (`mem/canon/<lead>/log.jsonl` and `mem/canon/<lead>/DIGEST.md`), the `agent()` call, the post-verify gate, the frontmatter, the firewall-tight return |
| `tools/digest_librarian.py` | **No-agent fallback only** (HELD from this repo; lives upstream) | Extractive v1 ranker (kind-then-recency + supersession + dedupe + cap-fill). Retained for `--self-test`, debug, and environments without a workflow runtime. NOT the canonical path. |

The canonical smart path = this workflow. The python tool stays as a fallback because (a) it has a solid `--self-test` battery that's still useful, (b) some bootstrap paths (cold-cache, no workflow runtime yet up) still call it, (c) deleting working code without need re-violates `system-over-symptom`.

## The contract (load-bearing — do not weaken)

### INPUT (args)

| field | required | shape | source |
|---|---|---|---|
| `args.lead` | yes | matches `^[A-Za-z0-9_][A-Za-z0-9_.\-]{0,63}$` | caller (org-assembler / parent workflow) |
| `args.now` | yes | ISO-Z (`YYYY-MM-DDThh:mm:ssZ`) | **CALLER OWNS THE CLOCK** — the workflow does NOT call the clock (sandbox clock can drift, and stamps must be deterministic across a multi-lead rebuild) |
| `args.repo_root` | recommended | absolute POSIX path to the civ-repo root that houses the `mem/` tree | caller. If omitted, the librarian agent uses Bash `pwd` and fails loudly if `<PWD>/mem/canon/` does not exist |
| `args.cap_chars` | no | int 500..20000 (default 8000 per SPEC §5) | caller override |
| `args.cap_lines` | no | int 10..1000 (default 200 per SPEC §5) | caller override |
| `args.candidate_cap` | no | int 20..2000 (default 400) | pre-filter window before the `agent()` call so a huge log still fits |

### OUTPUT (firewall-tight return — no raw log content)

```json
{
  "ok": true,
  "lead": "<lead>",
  "digest_path": "mem/canon/<lead>/DIGEST.md",
  "ledger_lines_at_rebuild": 142,
  "body_lines": 78,
  "body_chars": 6204,
  "mechanism": "agentic-workflow",
  "kept_ids_count": 41,
  "dropped_untraced_ids_count": 3,
  "verify_errors": ["drop: prose did not semantically trace to cited ids [...]"],
  "fallback_reason": null
}
```

### FRONTMATTER (written into DIGEST.md, drives the runtime freshness gate)

```yaml
---
last_rebuilt_at: <args.now>
ledger_lines_at_rebuild: <int>
lead: <id>
source_log: mem/canon/<id>/log.jsonl
mechanism: agentic-workflow
body_lines: <int>
body_chars: <int>
agentic_used: <bool>
fallback_reason: <str|absent>
---
```

`mechanism: agentic-workflow` is the stamp the runtime + auditors look for to confirm the canonical path ran. If a freshness check finds `mechanism: extractive-fallback` (the python tool), that's a signal an upstream substrate failed and the agentic path was bypassed — investigate, don't pile-on.

## The post-verify NO-INVENTION GATE (the structural cure)

This is what makes the model call SAFE. Two checks per bullet — both must pass or the bullet is DROPPED (and the rest of the digest still ships; partial trust):

1. **ID-GATE**: every cited `id=<hex>` token must resolve to an entry in the candidate set. Unknown id = "the model invented an id" = DROP.
2. **SEMANTIC-GATE**: bullet prose must either (a) verbatim-substring-match a cited entry's `item` or `rationale`, OR (b) share at least 2 distinct >=4-char tokens with at least one cited entry's `item`+`rationale`. Catches the laundering case where the model invents prose then tacks on a valid id.

If after both gates ZERO bullets survive, the workflow degrades to a substrate-honest in-band fallback (highest-priority deduped entries rendered as plain `- id=… **kind** — item _rationale_` bullets) so the runtime never inherits a stale DIGEST. `fallback_reason` records the why. This in-band fallback is NOT the python extractive ranker — it's a degraded-but-safe write the workflow does on its own, so the workflow remains the single substrate.

## Immediacy contract (runtime/workflow handoff)

The **runtime** (`tools/incarnation_runner.py`) **DETECTS** staleness via `--check-stale` (compares DIGEST.md frontmatter `ledger_lines_at_rebuild:` against the current log line count). The runtime DOES NOT REBUILD.

The **workflow layer** (the org-assembler / parent workflow) **INVOKES** `workflow('digest-librarian', { lead, now })` for each stale lead **BEFORE** the next incarnation's inline-memory block is assembled.

```
caller workflow (org-assembler or parent)
  └─ for each lead about to be inlined:
       ├─ runtime.check_stale(lead)              # detect only
       │    └─ stale? → workflow('digest-librarian', {lead, now: iso_now()})
       └─ runtime.assemble_inline_block(...)     # now inlines a fresh DIGEST
```

Why this split (per SPEC §9): the runtime is the **referee** (rules unbreakable, narrow surface, no model-API dep). The workflow is the **conductor** (decisions, decomposition, model calls). A python referee calling a model is the wrong layering — detection in the runtime, rebuild in the workflow.

## Failure modes + cures (logged for the §9 catalog of workflow-js-mastery)

| Failure | Cause | Cure |
|---|---|---|
| `agent()` returns null | StructuredOutput not called after nudges (workflow-js-mastery §3) | Schema kept simple (bullets array of {ids, kind, prose}); explicit "Return the structured bullets object" instruction at prompt end; in-band fallback if null |
| Model invents an id | Hallucinated hex / wrong format | ID-GATE drops bullet; `fallback_reason` records `n untraced` |
| Model invents prose | Plausible but not in source | SEMANTIC-GATE drops bullet (>=2 token overlap OR verbatim required) |
| Log over candidate cap | 10k+ entry log → prompt blowup | Pre-filter preserves ALL decisions + doctrine-candidates + retractions; fills with most-recent findings up to `candidate_cap` |
| Caller passes bad `args.now` | Wrong format / forgot | Workflow returns `ok:false` with a clear error before any work — no clock-fallback (deterministic-stamp discipline) |
| Stale DIGEST left in place after model failure | Old digest would re-inline | In-band degraded fallback ALWAYS writes a fresh frontmatter (`mechanism: agentic-workflow`, `agentic_used: false`, `fallback_reason: <why>`) |
| Adopter civ ran workflow from outside repo root | `args.repo_root` not passed AND `<PWD>/mem/canon/` does not exist | Librarian agent returns `ok:false` with `error="repo_root unresolved"` — does NOT create stray directories. Caller must re-invoke with `args.repo_root=<abs path>` |

## What this is NOT

- **NOT the DREAMER (§6).** This is low-order compression (drop superseded, dedupe, fit-to-cap, preserve load-bearing). The DREAMER is high-order pattern-draw ACROSS all memory (proposes new doctrine candidates from cross-lead patterns). They are distinct roles per SPEC §6 — do not conflate.
- **NOT a memory writer.** The librarian only writes `mem/canon/<lead>/DIGEST.md`. It never appends to `log.jsonl` (that's `canon_append.py`, the SOLE writer per single-writer discipline).
- **NOT a content-creator.** It can drop, keep, and merge existing log entries. It cannot invent. The gate enforces this structurally.

## Test path (when battery wiring lands)

The workflow's contract is testable through the same shapes the python `--self-test` already exercises:

1. **Cap + frontmatter** — seed N entries, rebuild, assert <=200 lines / <=8000 chars body, frontmatter has all required fields including `mechanism: agentic-workflow`.
2. **Traceability** — every bullet in output carries an `id=<hex>` resolving to a real log entry; prose semantically traces.
3. **Importance over recency** — seed an OLD load-bearing decision + 65 trivial newer findings; assert the OLD decision survives. (The v1 ranker drops it; the agentic path keeps it. This is the v1 cure.)
4. **Caller-clock** — call without `args.now`; assert `ok:false` with the expected error (no silent clock-fallback).
5. **Fallback honesty** — inject an `agent()` that returns null; assert the degraded fallback writes with `agentic_used: false` and `fallback_reason: <reason>`.
6. **No-invention** — inject an `agent()` that returns an unknown-id bullet AND an invented-prose-with-valid-id bullet; assert both DROPPED, valid bullets retained.

## Validation Log
*(Provisional. Distinct incarnations append dated ✓/✗ from POST-RUN reviews. 3 clean ✓ from distinct users → canon per provisional-skill-lifecycle.)*

- 2026-05-30 ✓ Authored: substrate-independent workflow built from the Phase-2 agentic contract; SDK dependency removed; in-band post-verify gate ported verbatim; runtime/workflow contract documented. — Originating civ (author note; does NOT count toward promotion per auditor-isolation)
- 2026-05-30 ✓ Phase-2 VALIDATED (gate ADVANCE; agentic-workflow synthesis via agent(); traceable / no-invention; age-eviction cured) — federation-IP repo SHIPPED.

## Cross-references

- Caller (immediacy): `tools/incarnation_runner.py` — DETECTS staleness only (--check-stale CLI); documents the workflow-layer rebuild contract in its module docstring.
- Sole canon writer: `tools/canon_append.py` (the librarian never appends).
- Sibling workflow shape: `workflows/acg-coo.js` (same firewall pattern; tight schema'd return; raw stays inside).
- Spec: `spec/SPEC-SHEET-v0.2.md` §5 + §6 + §9.
