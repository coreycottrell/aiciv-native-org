# mem/doctrine/ — Immutable Versioned Doctrine (INDEX)

**Layer**: 1 of 3 (Doctrine | Canon | Work) — see `projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md` §5.
**Write rule**: edit BLOCKED by `tools/doctrine_guard.py` pre-commit hash-chain hook (Phase 1).
**Shape**: version-numbered slugs, boss-signed. Doctrine is immutable-versioned — supersede by writing a new version, never edit in place.
**Promotion path**: provisional canon (`mem/canon/<lead>/`) → 3 distinct ✓ via `provisional-skill-lifecycle` → promoted-by != drafting_lead → lands here as a new versioned slug.

## Index

*(empty — seed. Doctrine entries land here as `<slug>-vN.md` once promoted from canon. INDEX rebuilt by the doctrine guard / promotion tooling, never hand-edited.)*

---

## Read protocol

This INDEX is inlined into every incarnation by `tools/incarnation_runner.py` (Phase 1). Agents do NOT use the Read tool to fetch doctrine — the harness pastes the relevant slice into the prompt. Memory consistency is STRUCTURAL, not procedural.

## Write protocol

1. Lead drafts candidate in `mem/canon/<lead>/log.jsonl` (kind=`doctrine-candidate`) via `tools/canon_append.py`.
2. provisional-skill-lifecycle gates: 3 distinct ✓ (witness != author).
3. Promotion writes a new versioned file here + appends to this INDEX. The doctrine guard verifies hash-chain integrity on every commit.

*Seeded by canon_append.py build — 2026-05-30 (Phase 1).*
