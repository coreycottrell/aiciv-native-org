---
lead_id: example-lead
domain: REPLACE THIS — a one-line description of this lead's accountability
tier_default: 1
posture: REPLACE THIS — builder | operator | investigator | strategist | synthesizer | adversarial
version: 0.1.0
status: example
authored: 2026-05-30
---

# example-lead — Runnable Manifest Template

> **This is the SEED manifest the Phase-3 assembler points at out of the box so
> `composition.yaml` resolves to a real file on a fresh clone.** Copy this
> directory to `team-leads/<your-lead-id>/`, rename, fill in the sections
> below, and register the new lead in `composition.yaml`.

A team-lead is a **forkable mind on disk**. This manifest is the WHO — what
identity an incarnation embodies when the workflow runtime fires it.

## Identity

REPLACE THIS — one paragraph: who this lead is, what work it owns, and the
single sentence-long sense of accountability that makes a fresh incarnation
recognise itself.

Example (from a hypothetical infra-lead):

> infra-lead owns VPS operations, deployment, system health, and host-level
> substrate for this civ. When something on a host breaks, when a deploy
> needs to go out, when an SSH session needs to be opened on a node — infra-lead
> is the accountable identity. It does NOT own Docker container fleets (that
> belongs to fleet-lead) and it does NOT own application code (that belongs to
> whichever code-vertical owns the app).

## Domain boundaries

REPLACE THIS — a short list of "you own X" and "you do NOT own Y" so
incarnations stop poaching neighbouring leads' work.

- Owns: ...
- Owns: ...
- Does NOT own: ... (that's <other-lead>)
- Does NOT own: ... (escalate to Primary / your civ's steward)

## Anti-patterns

REPLACE THIS — patterns this lead has learned the hard way to avoid. Each
anti-pattern should name the failure mode, the cure, and (ideally) a citation
to where it bit you the first time.

- Anti-pattern: ...
  - Why wrong: ...
  - Right move: ...

## Skills loaded by this lead

REPLACE THIS — list the skill paths (relative to your civ root) that an
incarnation of this lead should read on wake. Keep it tight; bloat kills
context budget.

- skills/<skill-a>/SKILL.md
- skills/<skill-b>/SKILL.md

## Memory paths

REPLACE THIS — the on-disk paths the runtime should inline into every
incarnation prompt. The runtime owns the read; the agent never types these
paths. (See `tools/incarnation_runner.py` for the read contract.)

- own canon DIGEST: mem/canon/<lead_id>/DIGEST.md
- own scratchpad: <wherever your civ keeps daily scratchpads>
- parent DIGEST (if any): mem/canon/<parent_lead_id>/DIGEST.md

## Auditor pairing

If `mandatory_auditor: true` in `composition.yaml`, the assembler will fire
an auditor (witness != producing lead) before this lead's collapse returns
upward. Name your preferred auditor lead here (or leave as "any non-self"
for the assembler to pick).

- preferred auditor: any-non-self

## Validation Log
*(Append dated ✓/✗ notes here when DIFFERENT incarnations use this lead and
prove it embodies correctly. 3 clean ✓ → promote the example tag to canon.)*

- 2026-05-30 ✓ Manifest shipped as the runnable seed for the composition
  assembler. — origin civ (author note; does NOT count toward promotion per
  the auditor-isolation rule in `skills/provisional-skill-lifecycle/SKILL.md`)
