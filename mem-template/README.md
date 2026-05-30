# `mem/` Tree — Template

This directory is a **template**. Copy `mem/` to your civ's repo root (NOT into `native-org/`) and wire `tools/doctrine_guard.py` as a `pre-commit` hash-chain hook over `mem/doctrine/`.

## Layout

```
mem/
├── doctrine/        Layer 1 — immutable versioned, hash-chain gated. INDEX.md seeded; doctrine entries land here as <slug>-vN.md once promoted from canon.
├── canon/           Layer 2 — append-only per-lead logs. Sole writer: tools/canon_append.py. Each <lead>/log.jsonl is the lead's proof-of-work substrate.
└── work/            Layer 3 — ephemeral per-job working space. Cleaned aggressively. Briefs land here as <job>/brief.md.
```

The 3 layers map to 3 time-shapes (immutable / append-only / ephemeral) per `native-org/SPEC-SHEET-v0.2.md §5`. Read that section before adopting.

## Why STRUCTURAL not procedural

The incarnation runtime (`tools/incarnation_runner.py`) inlines the relevant doctrine slice into every agent's prompt at incarnation time. Agents do NOT call the Read tool to fetch doctrine; the harness pastes it in. This is the **structural consistency** claim — it sticks where MEMORY.md didn't because there's no per-agent discipline to forget.

## What ships in this template

- `mem/doctrine/INDEX.md` — the seed file (empty index; entries land here at promotion time).
- `mem/canon/.gitkeep`, `mem/work/.gitkeep` — directory placeholders only; populated at runtime.

Doctrine `.hashes.json` is NOT shipped — `doctrine_guard.py` regenerates it on first commit.

— Templated from ACG `/mem/` snapshot on 2026-05-30.
