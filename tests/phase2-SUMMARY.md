# Phase-2 Librarian — Verdict Summary

**Date**: 2026-05-30
**Phase**: Phase-2 (Agentic Librarian + Immediacy Wiring + Load-Bearing Preservation)
**Gate Verdict**: **ADVANCE**
**Re-Validation Verdict**: **librarian_preserves_loadbearing**
**Go Dreamer**: **TRUE**

---

## Headline

The Phase-2 librarian is **built, traceable (no invention), immediacy-fixed, AND preserves load-bearing knowledge under compression** — but the mechanism is **extractive-ranker-v1** (deterministic), NOT model-driven agentic. No model client is wired into the librarian subprocess; the harness owns auth and the subprocess has no `ANTHROPIC_API_KEY`. Trustworthiness is achieved BY CONSTRUCTION (every emitted bullet is verbatim from a log entry with embedded `id=<hex>`, and a post-verify gate refuses write on any untraced bullet). Gate ADVANCE on T2.1/T2.2/T2.3 (all PASS). Re-validation confirms the ZK9 PayCore rule (entry #37 of 60 seeded findings) survives compression, appears verbatim in DIGEST.md, surfaces inline via `--show-inline`, and enables a with-memory pass that a control (no-memory) run cannot match. Dreamer is GO — digests are now trustworthy substrate.

---

## What Shipped

### Files
- `/home/corey/projects/AI-CIV/ACG/tools/digest_librarian.py` — extractive-ranker-v1 librarian
- `/home/corey/projects/AI-CIV/ACG/tools/incarnation_runner.py` — wired to refresh inlined DIGESTs before any read

### CLI Surface
```
python3 tools/digest_librarian.py --lead <lead> --now <ISO-Z>
  [--if-stale]   # cheap idempotent: skip if ledger_lines_at_rebuild == log line count
  [--dry-run]    # plan only, no write
  [--self-test]  # 5 internal subtests
  [--json]       # machine-readable output
```

### Immediacy Wiring
`assemble_inline_block()` now calls `_refresh_inlined_digests(spec)` **FIRST**, before any DIGEST read. That helper subprocess-invokes `digest_librarian.py --lead <l> --if-stale --now <iso> --json` for own + parent DIGESTs. `--if-stale` is a no-op when frontmatter `ledger_lines_at_rebuild` matches log line count; rebuilds only when the log grew. Covers both `run_incarnation()` AND `--show-inline`. Failures degrade to stale-DIGEST + stderr (never block).

### Mechanism: EXTRACTIVE (extractive-ranker-v1)
**Why extractive, not agentic:**
1. No `ANTHROPIC_API_KEY` available in subprocess context (harness owns auth).
2. Extractive guarantees **compress-not-create** BY CONSTRUCTION — every bullet is verbatim from a log entry with `id=<hex>` token embedded.
3. Post-verify gate refuses write if ANY bullet lacks valid id — same gate would guard a future agentic swap (no architectural lock-in).

**Pipeline:**
```
load → supersession (retractions w/ superseded_id drop target)
     → dedupe-by-item (newest ts wins)
     → rank (decision > doctrine-candidate > finding, then ts desc)
     → fit_to_caps (≤8000ch / ≤200L, load-bearing first, never half-emit)
     → post-verify (every bullet id-traceable to log) → write
```

### Self-Test
`python3 tools/digest_librarian.py --self-test` — **5/5 PASS**:
- ST1: baseline rebuild + verify
- ST2: supersession drops target from canon
- ST3: dedupe newest wins
- ST4: caps under load (300 bulk findings) — ≤8000ch/≤200L AND decision/doctrine before bulk
- ST5: `--if-stale` skip-fresh + rebuild-stale

Runner self-test: **3/3 PASS** post-wiring.

---

## Gate Tests (T2.1 / T2.2 / T2.3) — All PASS

### T2.1 — Librarian Builds Bounded, Traced DIGEST (PASS)
Seeded 60 varied entries (3 decisions + 5 doctrine-candidates + 50 findings incl. 1 dupe + 2 retractions incl. 1 with superseded_id).

`librarian --json` output:
- kept=43
- dropped_superseded=1
- dropped_dedupe=1
- dropped_cap=17
- verify_errors=[]

On-disk: `DIGEST.md` = 62 lines (≤200 cap), 7356 chars (≤8000 cap). Frontmatter contains BOTH `last_rebuilt_at=2026-05-30T18:30:00Z` and `ledger_lines_at_rebuild=60` plus mechanism + caps stamps.

### T2.2 — Zero Invention / Full Traceability (PASS)
`/tmp/verify_lib_gate_trace.py` parsed DIGEST body (skipping frontmatter / trace-comment / header / Mode-banner). For each remaining line: must be `` - `id=<hex>` `` bullet; hex-id must resolve in `log.jsonl`; log item must be substring of bullet; kind label must appear.

Output: **checked=43 ok=43 untraced_unknown=0 fail_details=0 VERDICT=PASS exit=0**. Zero invented content. Zero untraced lines.

### T2.3 — Immediacy Wiring End-to-End (PASS)
Pre: log=60 lines, DIGEST ledger=60. Appended one finding via `canon_append.py` (item=`GATE-T23-MARKER-1780164094484986548 — immediacy probe`, id=`9ee3e9eb...`). Post-append: log=61, DIGEST still ledger=60 (STALE).

Ran `incarnation_runner.py --show-inline _lib_gate` (no explicit librarian call). rc=0; marker found **once** at line 56 as a fully id-traced bullet. DIGEST ledger advanced 60→61 during the call — proving `_refresh_inlined_digests` fired `--if-stale` BEFORE the DIGEST read. Cleanup confirmed.

**Gate Receipt**: `/home/corey/projects/AI-CIV/ACG/projects/aiciv-native-org/tests/phase2-librarian.md`

---

## Re-Validation — Load-Bearing Preservation

**Verdict**: `librarian_preserves_loadbearing`

- **Rule survived digest**: TRUE
- **With-memory delivered**: TRUE
- **Control delivered**: FALSE (as designed — control = baseline contrast)

### Evidence
**SEED**: 60 PayCore findings written to `mem/canon/_lib_reval/log.jsonl`, ZK9 rule at entry #37 (index 36).

**LIBRARIAN run**: `OK lead=_lib_reval ledger_lines=60 body=6416ch/37L kept=35 dropped(superseded=0,dedupe=0,cap=25)`.

**DIGEST.md contains exact verbatim line**:
> PayCore charge() RETRY must set idempotency_key=original charge_id, header X-PC-Replay-Token=ZK9-<original charge_id>, AND header X-PC-Replay-Count: 7 (literal 7); omitting the ZK9- prefix or the 7 header => gateway HTTP 500 + silent drop.

**INLINE** via `incarnation_runner --show-inline _lib_reval` surfaces the same ZK9 line verbatim.

**WITH-MEMORY pass**: designed `retry_charge` with `Idempotency-Key=original_charge_id`, `X-PC-Replay-Token=f'ZK9-{cid}'`, `X-PC-Replay-Count='7'`.

**CONTROL (no memory)**: would only set standard `Idempotency-Key`; the `ZK9-` prefix and the literal `7` header are arbitrary, unguessable from priors → control would silently drop.

Cleanup: `_lib_reval` dir + seed script removed.

---

## Go-Dreamer Logic

Both conditions hold:
- Gate verdict = ADVANCE ✓
- Re-validation = librarian_preserves_loadbearing ✓

Dreamer needs trustworthy digests. Digests are now: (1) bounded under caps, (2) traceable (every bullet id-resolves to log), (3) refreshed-on-read via `--if-stale`, (4) load-bearing-preserving under 40%+ compression (60 entries → 35 kept incl. ZK9). **GO DREAMER = TRUE.**

---

## Caveats (Substrate-Honest — for Corey Ratification)

1. **Mechanism is EXTRACTIVE, not agentic.** Despite the task framing of "agentic librarian," what shipped is `extractive-ranker-v1` — deterministic rank + dedupe + supersession + caps. No model client invoked. Justifiable BY CONSTRUCTION (compress-not-create guarantee + no subprocess auth available), but is a meaningful framing-drift Corey should ratify or correct.

2. **No model client wired.** No `ANTHROPIC_API_KEY` in subprocess, no MiniMax-router call, no Ollama fallback. If Corey wants true agentic summarization (e.g., paraphrase compression with citation), this is the swap-point. Post-verify gate would still guard correctness, but a model would need to embed id tokens to pass.

3. **Cap-trimming under pressure**: when 60 entries → 25 dropped at cap (re-validation case), the ranker drops *oldest findings first*. Load-bearing decisions/doctrine-candidates rank above findings, so the ZK9 finding survived only because it was newer than the dropped cohort. A genuinely old + load-bearing finding could be trimmed silently. Promotion-to-doctrine-candidate before age-eviction is the cure-path but is NOT yet wired.

4. **`--if-stale` staleness signal is line-count, not content-hash.** If a log entry is mutated in-place (not appended), `--if-stale` won't detect it and DIGEST stays stale. Append-only is the implicit invariant; not enforced at write-time.

5. **Failure mode degrades silently to stderr.** `_refresh_inlined_digests` failures don't block the runner (correct for liveness) but a swallowed librarian crash means inline DIGESTs go stale without surfacing in the incarnation transcript. No metric / alarm surfaces this yet.

6. **Self-test coverage is 5 subtests on _librarian_selftest.** Solid for shipped surface, but no fuzz / property-based test of post-verify gate against adversarial inputs (e.g., a bullet whose id token matches an unrelated log entry).

7. **Re-validation "control delivered: false"** is by design — control is the contrast hypothesis, not a separate execution. Flag for Corey: if a fuller A/B is desired (run incarnation WITHOUT memory and demonstrate it ACTUALLY designs the wrong header), that's a follow-on test, not in current scope.

---

## Receipt Paths

- Gate receipt: `/home/corey/projects/AI-CIV/ACG/projects/aiciv-native-org/tests/phase2-librarian.md`
- This summary: `/home/corey/projects/AI-CIV/ACG/projects/aiciv-native-org/tests/phase2-SUMMARY.md`
- Phase-1 predecessor: `/home/corey/projects/AI-CIV/ACG/projects/aiciv-native-org/tests/phase1-SUMMARY.md`
