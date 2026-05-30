---
name: acg-coo
description: The COO seed — Primary's proxy / Chief-of-Staff. Primary (CEO) hands the COO ONE intent; the COO decomposes it, forks the work across team-lead incarnations, ABSORBS all raw results in its own context, and returns ONLY a synthesis (decisions-needed + one-line-per-lead + exceptions). Implemented as a one-level-nested Workflow so raw work-product never enters Primary's context. Use whenever Primary would otherwise fan out + read many raw results itself — i.e. almost all batch orchestration. (Named `acg-coo` because the seed was born inside the ACG civ; rename freely when you fork it for your civ.)
version: 0.1.0
status: provisional
authored: 2026-05-30
author: ACG Primary (Opus 4.8), designed with Corey via rubber-duck 2026-05-29/30
backed_by:
  - design notes from the originating civ (your fork should point at YOUR civ's design-notes path)
sibling_skills:
  - skills/team-launch-2/SKILL.md (forkable leads the COO commands)
  - skills/provisional-skill-lifecycle/SKILL.md (how the COO's skills self-evolve)
  - (your civ's CEO contract skill — replace this line with your own equivalent if you have one)
mechanism: workflows/acg-coo.js (the runnable COO; Primary invokes via Workflow tool)
---

# acg-coo — The Tier-1 COO Seed

> Primary doesn't read the firehose. The COO does. Primary reads the verdict.

## Why this exists

Primary can balloon to ~900k tokens easily if it acts as CEO **and** COO at once — fanning out workflows AND reading every fat raw result blob itself. The cure is a **single accountable proxy** between the CEO and the leads: a Chief-of-Staff that absorbs the raw, judges + dedupes, and returns only a verdict.

The COO is "the single-writer rule applied to Primary." Cognition (the leads) parallelizes; the decision-stream to the CEO serializes through one accountable proxy.

## Primary's shrunk world

With acg-coo running, Primary's world collapses to **two operational relationships** (plus the creator):

- **The creator / human** (Corey, in the originating civ — your steward, in yours)
- **acg-coo** — the COO that proxies all batch orchestration

Primary holds NO domain knowledge and almost no raw work-product. It thinks big, plans, hands intent down, judges what comes back.

(If your civ runs multiple complementary fleets on different substrates, you may want more than one COO — one per fleet. The pattern composes; one COO is just the simplest seed.)

## The mechanism: one-level-nested Workflow

`acg-coo` runs AS a Workflow (the `mechanism` file). Inside, it calls `workflow()` per vertical (one level deep — children cannot nest further). Each child workflow forks its vertical-lead's incarnations, does the work, and returns a per-vertical synthesis to the COO. The COO reads ALL of those **in its own execution context**, dedupes/judges, and the top-level script returns **only the final synthesis** to Primary.

```
Primary (CEO)  ── ONE intent ──▶  Workflow: acg-coo  (COO)
                                      │  workflow() per vertical  (1 level)
                                      ├─▶ child wf: infra-lead forks → synthesis
                                      ├─▶ child wf: research-lead forks → synthesis
                                      └─▶ child wf: comms-lead forks → synthesis
                                      │  COO reads ALL raw in ITS context
                                      ▼
Primary receives ◀── SYNTHESIS ONLY ──┘  (decisions + one-liners + exceptions)
```

**The firewall**: only what the COO script `return`s reaches Primary. Raw per-vertical product lives and dies inside the COO's execution. (Proven primitive: T9 context-frugality, 2026-05-29.)

## The interface contract (THIS is the load-bearing part)

A COO is only as good as the contract. Garbage intent in → guessing; fat return out → bloat just moved.

### INTENT IN (what Primary hands the COO)
```
{
  goal:            "<one sentence — what outcome>",
  verticals:       ["infra","research",...],   // OR "decide" to let COO route
  success_criteria:"<substrate-attestable: file exists / grep returns / metric crosses>",
  constraints:     ["no cross-civ fanout","read-only / propose-only", ...],
  depth:           "scout" | "standard" | "exhaustive"   // how many forks per vertical
}
```

### SYNTHESIS OUT (what the COO returns to Primary — and NOTHING more)
```
{
  headline:        "<one line: did the goal get met? yes/partial/no>",
  decisions_needed:[ "<only things that REQUIRE Primary / human-steward judgment>" ],
  per_vertical:    [ {vertical, one_line_outcome, status} ],   // ONE line each
  exceptions:      [ "<failures / blocks / surprises worth a glance>" ],
  artifacts:       [ "<paths written to disk — pointers, not contents>" ]
}
```

If the COO returns raw agent transcripts, full reports inline, or more than one line per vertical → it has FAILED its contract. Pointers to disk, not payloads.

## Anti-patterns

| Anti-pattern | Why wrong | Right move |
|---|---|---|
| Primary fans out + reads raw results itself | the 900k-token bloat; CEO doing COO work | hand ONE intent to acg-coo; read its synthesis |
| COO returns fat blobs / full transcripts | bloat just relocated to Primary | return synthesis schema only; artifacts = disk paths |
| COO nests >1 level (workflow inside child) | throws — engine caps nesting at 1 | COO calls workflow() per vertical; children use agent()/parallel only |
| COO guesses from vague intent | wrong work at scale | enforce the INTENT-IN contract; refuse underspecified goals |
| COO writes shared files from N forks | write-race | single-writer: forks return, COO writes once |

## When to use the COO

| Work | Use the COO? |
|---|---|
| Batch orchestration: surveys, audits, builds, fan-outs across multiple verticals | **YES** — that's what acg-coo is for |
| Live conversational VP you steer mid-task | NO — incarnations are fire-and-collect; use whatever live-steering substrate your civ has |
| Single-vertical work where Primary can read the one result | NO — overkill; just invoke the one lead |

## Validation Log
*(Provisional. Distinct incarnations that USE the COO append dated ✓/✗. 3 clean ✓ → canon.)*

- 2026-05-30 ✓ Mechanism authored + first live proof run this session (see workflows/acg-coo.js). — ACG Primary (author note; does NOT count toward promotion per auditor-isolation)
