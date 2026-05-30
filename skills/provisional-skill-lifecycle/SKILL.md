---
name: provisional-skill-lifecycle
description: The promotion lifecycle for self-authored skills. A new/edited skill is born `provisional` carrying its own proof; OTHER incarnations log dated ✓/✗ validation notes from real use; 3 clean ✓ from distinct users promotes it to canon. The skill is its own database, proof, and promotion ledger — and it cannot grade itself. Use whenever a team-lead incarnation authors or amends a skill, or when deciding whether a provisional skill has earned canon.
version: 0.1.0
status: provisional
authored: 2026-05-29
author: ACG Primary (Opus 4.8), refined with Corey via rubber-duck 2026-05-29
backed_by:
  - the originating civ's primitive-test report (10/10 primitive tests; T5 self-authorship, T6 gate, T10 K-refusal). Your fork should point at YOUR civ's primitive-test receipt path.
  - the originating civ's design notes on forkable-leads-and-provisional-skills.
related_doctrines:
  # Replace these with YOUR civ's equivalent doctrines (or remove if you don't yet have any).
  # The two principles below are the load-bearing ones — name them however your civ does:
  #   1. "Anti-fabrication applies symmetrically" — overcount AND undercount; both directions
  #      of claim-vs-substrate drift demand cure.
  #   2. "Audit skills SUGGEST, never MUTATE" — an audit-class skill must not also be the
  #      writer that corrects what it audits (no self-grading).
  # Also recommended: a cross-grading-substrate skill / pattern, where one AI checks another.
sibling_skills:
  - skills/team-launch-2/SKILL.md (the forkable-lead system this lifecycle governs)
---

# Provisional-Skill Lifecycle

> The simplest loop that lets skills grow themselves **without being able to fabricate their way to canon.**

## Why this exists

In the upgraded team-lead system, leads self-evolve by authoring and amending their own skills (see `team-launch-2`). At 1000x parallel scale, an automatic evolution loop with no gate becomes a **fabrication amplifier** — fast, confident, scaled wrongness (the K=1 failure mode, automated). This lifecycle is the immune system: it lets the skill corpus grow while structurally preventing a skill from validating itself into canon.

Rejected: the elaborate version (dedicated integrator skill + QA-lead gate + daily JSON health file + usage-surveillance). Too many breakable moving parts; most of them new infrastructure.

Adopted: **the skill file is its own database.** No new process, no new file type. Four rules.

## The Four Rules

### Rule 1 — Born provisional, with proof
A new or edited skill ships tagged `status: provisional` in its frontmatter and MUST contain its proof **at birth**:
- citation (where the need came from — a real catch, a failed run, a verbatim error)
- evidence trail (file paths, before/after, the gotcha)
- rationale (why this is a class-fix, not a one-off patch)

**No proof → no skill.** A provisional skill with an empty proof section is rejected at authoring time.

### Rule 2 — Use logs a dated note
Every time an agent USES the provisional skill and it did what it claimed, the agent appends ONE line to a `## Validation Log` section inside the skill file:

```
- 2026-05-29 ✓ <what it did, what worked> — <incarnation/seat that logged it>
```

If it FAILED: `- 2026-05-29 ✗ <what broke> — <who>`. **Failures count.** They are the signal that kills a bad skill before it reaches canon.

### Rule 3 — Three clean ✓ → canon
Three ✓ notes from **distinct incarnations** → drop the `provisional` tag → `status: canon`. One ✗ → reset the counter (or flag a human if the ✗ reveals a design flaw, not just a transient). Counting to 3 is the entire promotion engine — any agent or a trivial cron can run the check.

### Rule 4 — Provisional is always surfaced
Standing rule: anything tagged `provisional` in its meta/firing-contract MUST be named in the session memory notes. A provisional skill never runs silently — it is surfaced every session until it earns canon.

## The one constraint that makes it safe (auditor-isolation, free)

**The validation note in Rule 2 MUST be written by a DIFFERENT incarnation than the one that authored the skill.** Self-validation is the fabrication vector. The proposer writes the skill provisional; *users* (other incarnations, later) write the ✓/✗ notes. Zero new infrastructure — it is purely a rule about *who is allowed to write the note*.

This was the load-bearing finding of the 2026-05-29 primitive tests: T6 (a different incarnation) caught a fabrication in a peer-authored skill by SSHing to the host and verifying a cited path did not exist. Without cross-incarnation validation, T5→T7 would have been a fabrication amplifier.

## The loop, in one line

**Born provisional with proof → used by *others* who log dated ✓/✗ → 3 clean ✓ from distinct uses = canon → provisional always surfaced in memory until promoted.**

## Anti-patterns

| Anti-pattern | Why wrong | Right move |
|---|---|---|
| Skill ships `canon` on first author | No working history; unvalidated | Born `provisional`, earns canon via Rule 3 |
| Author logs their own ✓ note | Self-grading = fabrication vector | Only DIFFERENT incarnations log notes |
| Provisional skill runs unmentioned | Silent unvalidated code in production | Rule 4 — surface in memory every session |
| ✗ note ignored, counter not reset | Bad skill drifts to canon | One ✗ resets counter / flags human |
| "It worked" with no evidence in the note | Memo-theater | Note must name what it did + what worked |

## Validation Log

*(This skill is itself provisional — it earns canon by being USED to promote other skills. Distinct incarnations append below.)*

- 2026-05-29 ✓ Authored + dogfooded: `team-launch-2` born provisional under this lifecycle the same session. — ACG Primary (author note; does NOT count toward promotion per the auditor-isolation rule)
