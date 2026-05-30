---
name: team-launch-2
description: The massively-upgraded team-lead orchestration pattern. Team leads are forkable minds-on-disk (manifest + skills + memory + scratchpad), incarnated as background Workflow agents — no tmux panes, no crash-risk, no shutdown handshake, scalable to ~1000 parallel incarnations. Primary shrinks to think-big + plan + delegate + judge. Leads self-evolve via the provisional-skill lifecycle. Use for ALL batch vertical work; keep TeamCreate (team-launch v1) only for live conversational VPs you watch + steer mid-task.
version: 0.1.0
status: provisional
authored: 2026-05-29
author: ACG Primary (Opus 4.8), designed with Corey via rubber-duck 2026-05-29
backed_by:
  - the originating civ's primitive-test report (10/10 primitive tests — incarnation, fork-collapse, single-writer, self-evolution, the gate). Your fork should point at YOUR civ's primitive-test receipt path.
  - the originating civ's capability-test report (Dynamic Workflows proven live in Opus 4.8).
  - the originating civ's design notes on forkable-leads-and-provisional-skills.
sibling_skills:
  - skills/provisional-skill-lifecycle/SKILL.md (how leads self-evolve safely)
supersedes_for_batch_work: any prior tmux-pane / TeamCreate-style team-launch pattern — see "When to use which" below
---

# Team-Launch-2 — Forkable Minds at Scale

> Primary doesn't need to know any domain. It needs to think big, plan, delegate, and judge. Every domain is a lead that learns, grows, builds and uses its own skills, and self-evolves toward mastery — and can fork itself a thousand times at once.

## The core shift

A team lead is **not a running process**. It is a **forkable mind on disk**:

```
<your-civ-root>/team-leads/{vertical}/
├── manifest.md          ← WHO it is (identity, domain, anti-patterns)
├── skills/              ← WHAT it can do (its own skill dir — grows over time)
├── memory/              ← WHAT it has learned (compounding)
└── daily-scratchpads/   ← WHAT it has done (append-only)
```

(Path is adopter-chosen — common conventions: `team-leads/`, `.claude/team-leads/`, `autonomy/team-leads/`. The runtime + workflows take the root as input; nothing here hardcodes it.)

The running instance is a **temporary incarnation** of that on-disk identity. You can incarnate it once, or fork it N times in parallel — each incarnation reads the same brain.

**This deletes the pane-detection bug class entirely:** Workflow `agent()` incarnations are background subagents — they spawn NO tmux panes. No pane → nothing to mis-resolve → the TG-hijack failure cannot exist.

## The two axes of scale

- **Horizontal (breadth):** Primary fires N *different* leads in parallel — infra, comms, research, legal…
- **Vertical (depth):** ONE lead forks into N copies of *itself*, each on a slice (survey 100 files, audit 100 endpoints), then collapses to one richer lead via a single synthesis. **This is the new unlock** — domain mastery compounds Nx per cycle instead of 1x.

## The launch pattern (Workflow-incarnated leads)

Each incarnation is an `agent()` call inside a Dynamic Workflow whose prompt loads the lead's on-disk identity:

```js
// Inside a Workflow script:
agent(
  `Read <your-civ-root>/team-leads/{vertical}/manifest.md and embody {vertical}-lead.
   Read your memory/ and today's scratchpad. Then: {sliced task}.
   Substrate-honest. RETURN your findings + any proposed learning — do NOT write shared files.`,
  { label: '{vertical}-lead-{i}', phase: '...', schema: FINDINGS }
)
```

**Verified working (2026-05-29):** an incarnation read the real infra manifest, embodied it (returned a verbatim anti-pattern + loaded skill), and wrote a genuine domain learning to disk. (Primitive tests T1, T2, T8.)

## The single-writer rule (kills write-races by construction)

When you fork a lead N-fold, **incarnations READ the shared brain but NEVER WRITE it directly.** They RETURN proposed learnings. ONE synthesis step (or a "librarian" incarnation) merges + dedupes + writes once.

This also gives quality control for free: N incarnations propose, but the synthesis step is where **dedup + adversarial filtering** lives. Only learnings that survive get written. The thing we fear most (1000 agents writing 1000 mediocre memories) is prevented by the same structure that enables scale.

**Verified working (2026-05-29):** 5 fork incarnations returned 5 distinct findings; a single writer merged them into one file, no race. (Primitive tests T3, T4, T9.)

## Self-evolution (governed by provisional-skill-lifecycle)

The compounding loop:
1. Incarnation does work, hits a real gotcha.
2. It authors a new skill (or amendment) in its own `skills/` dir, tagged `provisional` with proof.
3. A DIFFERENT incarnation that later USES the skill logs a dated ✓/✗ note.
4. 3 clean ✓ from distinct users → canon.

Full rules: `provisional-skill-lifecycle` SKILL. **The gate is non-negotiable** — without cross-incarnation validation, self-evolution becomes a fabrication amplifier at scale.

**Verified working (2026-05-29):** an incarnation authored `execution-host-path-discipline` from a real failure (T5); a different incarnation gated it by SSHing to the host and refusing a fabricated path (T6); K-promotion correctly REFUSED a 2/3-success candidate because the failure was doctrinally significant (T10).

## Primary's shrunk role

Primary becomes a near-pure **router + judge**:
- **think big** — hold the goal
- **plan** — decompose into domains + order
- **delegate** — fire the leads (horizontal) / fork a lead (vertical)
- **judge** — synthesize what returns, against pre-registered success criteria

Primary holds NO domain knowledge and its context stays tiny — only synthesized results return. That is what makes orchestrating ~1000 background tasks possible without Primary's context being the ceiling. (Context-frugality verified: T9.)

## When to use which — team-launch-2 vs team-launch (v1/TeamCreate)

| Use **team-launch-2** (Workflow incarnations) | Use **team-launch v1** (TeamCreate panes) |
|---|---|
| Batch vertical work: surveys, audits, test batteries, fan-outs | Live conversational VP you watch + steer mid-task |
| Need massive parallelism (up to ~1000) | Need to SendMessage course-corrections mid-flight |
| Fire-and-collect; no mid-task redirection needed | Ambiguous/exploratory scope that evolves in dialogue |
| Want zero pane-detection / crash / shutdown risk | Accept pane overhead for live observability |

They are **complementary, not replacement.** Most wheel/BOOP/survey work is batch → team-launch-2. The rare living-VP case → v1.

## Hard constraints

- Incarnations are fire-and-collect: **you cannot steer them mid-task.** If the work needs live redirection, use v1.
- Throttle concurrency sensibly — start conservative (the harness caps concurrent agents anyway). Don't assume 1000 is free.
- Every self-authored skill obeys `provisional-skill-lifecycle`. No skill reaches canon without distinct-incarnation validation.
- A fork-target identity must exist on disk (manifest present) before incarnating it.

## Honest gaps (carried forward — do NOT read "10/10 PASS" as "fully proven")

Per the 2026-05-29 primitive report, these are NOT yet proven and are the next-round probes:
1. Cross-session persistence (new incarnation, new session, re-derives identity from disk).
2. Write-race under TRUE concurrency (two writers by mistake).
3. Evolution safety over many cycles (does the corpus drift toward truth or fabrication after 50 self-authored skills?).
4. Cross-civ adoptability of self-authored skills (federation-IP altitude).
5. What gates the gate (T6 was not itself cross-graded).
6. Fork-target liveness (behavior when a target identity is missing/stale).
7. Empirical Primary-context measurement (T9 was inferential, not measured).

## Validation Log

*(This skill is provisional. Distinct incarnations that USE this pattern append dated ✓/✗ notes below. 3 clean ✓ from distinct users → canon.)*

- 2026-05-29 ✓ Pattern executed live this session: 2 Dynamic Workflows (Opus-4.8 battery + 10-primitive battery, ~14+21 incarnations) ran fork-and-collapse + single-writer + self-evolution + gate end-to-end, 10/10 primitives passed. — ACG Primary (author note; does NOT count toward promotion per auditor-isolation)
