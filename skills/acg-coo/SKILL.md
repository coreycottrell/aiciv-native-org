---
name: acg-coo
description: The Claude-side COO — Primary's proxy/Chief-of-Staff, mirror of the Hermes LT (which is COO of the MiniMax fleet). Primary (CEO) hands acg-coo ONE intent; the COO decomposes it, forks the work across team-lead incarnations, ABSORBS all raw results in its own context, and returns ONLY a synthesis (decisions-needed + one-line-per-lead + exceptions). Implemented as a one-level-nested Workflow so raw work-product never enters Primary's context. Use whenever Primary would otherwise fan out + read many raw results itself — i.e. almost all batch orchestration.
version: 0.1.0
status: provisional
authored: 2026-05-30
author: ACG Primary (Opus 4.8), designed with Corey via rubber-duck 2026-05-29/30
backed_by:
  - data/reports/teamlead-primitives-2026-05-29.md (fork-collapse + single-writer + context-frugality proven)
  - .claude/design-notes/2026-05-29-forkable-leads-and-provisional-skills.md
sibling_skills:
  - autonomy/skills/team-launch-2/SKILL.md (forkable leads the COO commands)
  - autonomy/skills/provisional-skill-lifecycle/SKILL.md (how the COO's skills self-evolve)
  - autonomy/skills/acg-lieutenant-mastery/SKILL.md (the Hermes-side COO this mirrors)
  - autonomy/skills/tgim-mastery-for-ceos/SKILL.md (Primary's CEO contract — the other half)
mechanism: workflows/acg-coo.js (the runnable COO; Primary invokes via Workflow tool)
---

# acg-coo — The Claude-Side COO

> Primary doesn't read the firehose. The COO does. Primary reads the verdict.

## Why this exists

Tonight Primary ballooned to ~900k tokens because it acted as CEO **and** COO at once — it fanned out workflows AND read every fat raw result blob itself. The Hermes fleet already solved this: the **LT (hermes-primary)** is COO of the MiniMax side — Primary gives it one intent, it assigns + shepherds + synthesizes, Primary gets a verdict. `acg-coo` is the **same role for the Claude/Anthropic side.**

The COO is "the single-writer rule applied to Primary." Cognition (the leads) parallelizes; the decision-stream to the CEO serializes through one accountable proxy.

## The two-relationship CEO

With acg-coo + LT, Primary's world shrinks to **three relationships**:
- **Corey** (the creator)
- **LT / hermes-primary** — COO of the MiniMax fleet
- **acg-coo** — COO of the Claude/Anthropic side

Primary holds NO domain knowledge and almost no raw work-product. It thinks big, plans, hands intent down, judges what comes back.

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
  constraints:     ["no cross-civ fanout","minimax-pause respected", ...],
  depth:           "scout" | "standard" | "exhaustive"   // how many forks per vertical
}
```

### SYNTHESIS OUT (what the COO returns to Primary — and NOTHING more)
```
{
  headline:        "<one line: did the goal get met? yes/partial/no>",
  decisions_needed:[ "<only things that REQUIRE Primary/Corey judgment>" ],
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

## When to use which proxy

| Work | Proxy |
|---|---|
| Claude-side batch (surveys, audits, builds, exploration) | **acg-coo** (this) |
| MiniMax-fleet work (Hermes seats, dual-memory, autoresearch) | **LT / hermes-primary** |
| Live conversational VP you steer mid-task | TeamCreate (team-launch v1) — rare |

## Validation Log
*(Provisional. Distinct incarnations that USE the COO append dated ✓/✗. 3 clean ✓ → canon.)*

- 2026-05-30 ✓ Mechanism authored + first live proof run this session (see workflows/acg-coo.js). — ACG Primary (author note; does NOT count toward promotion per auditor-isolation)
