#!/usr/bin/env python3
"""
incarnation_runner.py — THE runtime referee for the AiCIV-Native Org.

Part of the Phase-1 foundation (SPEC §5 + §9, BUILD-PLAN Phase 1 item 1).
This is the ONE shared runtime that wraps every agent incarnation. It:

  1. READ   — assembles the inlined-memory block (~5k token budget) =
              doctrine INDEX + own lead DIGEST + parent DIGEST (if any)
              + work brief (mem/work/<job>/brief.md if any). This block is
              PASTED INTO the agent prompt. The agent gets NO Read tool
              for memory (memory consistency is STRUCTURAL, not procedural).

  2. VALIDATE-RETURN — rejects any agent return missing the REQUIRED field
              `memory_delta:{canon_appends:[...], rationale}`. No write-skip
              loophole; validator-step IS the win (SPEC §7).

  3. WRITE  — for each `canon_appends` item, calls `tools/canon_append.py`
              (the SOLE writer). Agents NEVER write to mem/. The runtime
              owns ALL paths (kills the inbox-path-drift bug class).

Single-writer discipline: only this runtime invokes canon_append.py from
inside an incarnation. Other CLIs may run canon_append.py for bootstrap.

CLI (Phase-1):
    python3 tools/incarnation_runner.py --self-test
        Builds an inline block for a fake lead, logs the assembled prompt
        to a file, exercises VALIDATE-RETURN with a return MISSING
        memory_delta (must REJECT) and one WITH it (must ACCEPT and trigger
        canon_append).

The actual model-invocation seam is intentionally abstracted: tests inject
a callable `model_fn(prompt:str)->str`. PR-1 ships the referee shape; later
phases bolt real model adapters onto the seam.

SPEC refs:
  - §5  memory pipe (READ→APPEND→DIGEST→INLINE→READ loop)
  - §7  trust / structural independence (validator-step)
  - §9  one shared runtime (Corey: "absolutely one runtime")
  - §11 build sequence — this is PR-1's keystone
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Repo root is the parent of tools/ (this file lives in tools/).
REPO_ROOT = Path(__file__).resolve().parent.parent
MEM_DIR = REPO_ROOT / "mem"
MEM_DOCTRINE = MEM_DIR / "doctrine"
MEM_CANON = MEM_DIR / "canon"
MEM_WORK = MEM_DIR / "work"

CANON_APPEND_SCRIPT = REPO_ROOT / "tools" / "canon_append.py"
# Phase-2 librarian (Option B, COMPRESS-NOT-CREATE). The runtime invokes
# this with --if-stale before READ assembles the inline block, so a DIGEST
# lagging its log can never be silently inlined (short-horizon findings
# would be invisible to the next incarnation otherwise — the immediacy gap).
DIGEST_LIBRARIAN_SCRIPT = REPO_ROOT / "tools" / "digest_librarian.py"

# ~5k token budget (SPEC §5). 1 token ~= 4 chars heuristic → ~20_000 chars
# is a safe ceiling. We truncate sections (doctrine + parent DIGEST first,
# own DIGEST + work brief last) when over budget — own DIGEST is highest
# value, never trim it before the lower-value slices.
INLINE_BUDGET_CHARS = 20_000

# Section caps (chars). Sum ≈ budget; own DIGEST gets the largest share.
SECTION_CAPS = {
    "doctrine_index": 3_000,
    "parent_digest": 4_000,
    "own_digest": 8_000,
    "work_brief": 5_000,
}

# Sentinel header used in the assembled prompt — tests grep for this to
# confirm the inline block was injected.
INLINE_HEADER = "===== INLINED MEMORY (assembled by incarnation_runner.py) ====="
INLINE_FOOTER = "===== END INLINED MEMORY ====="

# Closed enum mirrored from canon_append.py (kept in sync intentionally;
# importing it would couple module-loading to file location semantics).
ALLOWED_KINDS = frozenset({
    "finding",
    "decision",
    "retraction",
    "doctrine-candidate",
})

# Where prompt logs land for offline inspection (self-test greps these).
PROMPT_LOG_DIR = REPO_ROOT / ".claude" / "logs" / "incarnation_runner"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class IncarnationSpec:
    """Everything the runtime needs to wrap a single agent invocation."""

    lead: str                          # own lead id (e.g. "web-lead")
    task: str                          # the actual instruction for the agent
    parent_lead: Optional[str] = None  # the boss whose DIGEST to inline (if any)
    job_id: Optional[str] = None       # mem/work/<job_id>/brief.md if any
    schema_hint: Optional[str] = None  # short return-shape reminder for the agent
    extra_context: Optional[str] = None  # ad-hoc context (rarely used; visible in log)


@dataclass
class IncarnationResult:
    """What the runtime returns after wrapping one agent invocation."""

    ok: bool
    lead: str
    appended: list[dict] = field(default_factory=list)
    rejection_reason: Optional[str] = None
    raw_return: Optional[str] = None
    prompt_log_path: Optional[Path] = None
    inline_block_chars: int = 0


# ---------------------------------------------------------------------------
# Read step — assemble inlined memory
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Immediacy gap cure — DIGEST freshness gate
# ---------------------------------------------------------------------------
#
# Phase-1 shipped a MECHANICAL placeholder digest rebuilt by canon_append.py
# only on +50-line bumps. That left a window where a short-horizon finding
# could land in the log but stay invisible to the next incarnation
# (own DIGEST.md lagging the ledger). The next incarnation would inline a
# STALE digest and never see the just-written line — the immediacy gap.
#
# Phase-2 cure: before READ assembles the inline block, invoke the librarian
# in --if-stale mode for every DIGEST we're about to inline (own + parent).
# --if-stale is cheap: it reads the existing DIGEST's frontmatter
# `ledger_lines_at_rebuild:` and only triggers rebuild if it does not match
# the current line count. Idempotent; no-op when fresh.
#
# Failure mode: librarian failure (verify error, missing log, etc.) is
# logged to stderr but does NOT block the incarnation — we'd rather inline
# a stale DIGEST than fail-closed and refuse to run. The librarian's own
# verify gate prevents writing invented content, so "stale" is the only
# degraded mode we tolerate.

def _now_iso_for_librarian() -> str:
    """Best-effort ISO-Z stamp passed to digest_librarian --now. Subprocess
    clock access is sometimes unreliable inside sandboxes; the runtime owns
    the stamp so the librarian doesn't have to re-derive it."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rebuild_digest_if_stale(lead: str) -> dict:
    """Invoke `digest_librarian.py --lead <lead> --if-stale --json` in-band.

    Returns a small dict describing the outcome (for caller logging):
        {"lead": ..., "skipped_fresh": bool, "rebuilt": bool,
         "verify_errors": [...], "error": str|None}

    Never raises — failures degrade to "kept stale DIGEST" (logged to stderr).
    """
    summary: dict = {
        "lead": lead,
        "skipped_fresh": False,
        "rebuilt": False,
        "verify_errors": [],
        "error": None,
    }
    if not DIGEST_LIBRARIAN_SCRIPT.exists():
        summary["error"] = f"digest_librarian.py missing at {DIGEST_LIBRARIAN_SCRIPT}"
        sys.stderr.write(f"incarnation_runner: {summary['error']}\n")
        return summary

    # No log → nothing to rebuild from. Don't even invoke; cheap short-circuit.
    log = MEM_CANON / lead / "log.jsonl"
    if not log.exists():
        summary["skipped_fresh"] = True  # treat absent as "trivially fresh"
        return summary

    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(DIGEST_LIBRARIAN_SCRIPT),
                "--lead", lead,
                "--if-stale",
                "--now", _now_iso_for_librarian(),
                "--json",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        summary["error"] = f"librarian invocation failed: {exc}"
        sys.stderr.write(f"incarnation_runner: {summary['error']}\n")
        return summary

    # Always try to parse stdout (best-effort) — librarian emits JSON when
    # --json is set; non-zero exit + verify errors come back on stderr.
    payload = None
    if proc.stdout.strip():
        try:
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
        except (json.JSONDecodeError, IndexError):
            payload = None

    if payload:
        summary["skipped_fresh"] = bool(payload.get("skipped_fresh"))
        summary["verify_errors"] = list(payload.get("verify_errors") or [])
        summary["rebuilt"] = (not summary["skipped_fresh"]) and proc.returncode == 0

    if proc.returncode != 0:
        summary["error"] = (
            f"librarian exit {proc.returncode}: stderr={proc.stderr.strip()!r}"
        )
        sys.stderr.write(
            f"incarnation_runner: digest rebuild for {lead!r} failed "
            f"(degrading to stale DIGEST): {summary['error']}\n"
        )
    return summary


def _refresh_inlined_digests(spec: "IncarnationSpec") -> list[dict]:
    """Run --if-stale rebuilds for every DIGEST about to be inlined.

    Order: own first (highest value, always present), then parent (if any).
    Returns list of librarian summaries for caller logging.
    """
    summaries: list[dict] = []
    summaries.append(_rebuild_digest_if_stale(spec.lead))
    if spec.parent_lead:
        summaries.append(_rebuild_digest_if_stale(spec.parent_lead))
    return summaries


def _read_or_empty(path: Path, cap_chars: int) -> str:
    """Read up to cap_chars from path; return '' if absent. Truncate with marker."""
    if not path.exists() or not path.is_file():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) > cap_chars:
        text = text[:cap_chars] + f"\n…[truncated to {cap_chars} chars by incarnation_runner]\n"
    return text


def _doctrine_index_text() -> str:
    return _read_or_empty(MEM_DOCTRINE / "INDEX.md", SECTION_CAPS["doctrine_index"])


def _lead_digest_text(lead: str, cap_key: str) -> str:
    return _read_or_empty(MEM_CANON / lead / "DIGEST.md", SECTION_CAPS[cap_key])


def _work_brief_text(job_id: Optional[str]) -> str:
    if not job_id:
        return ""
    return _read_or_empty(MEM_WORK / job_id / "brief.md", SECTION_CAPS["work_brief"])


def _section(name: str, body: str) -> str:
    """Wrap a section in clear delimiters so the agent can parse it."""
    body = body.strip()
    if not body:
        body = f"(empty — no {name} on disk)"
    return f"\n--- BEGIN {name} ---\n{body}\n--- END {name} ---\n"


def assemble_inline_block(spec: IncarnationSpec) -> str:
    """Build the full inlined-memory block for an incarnation.

    Order matters — doctrine first (immutable ground), then parent DIGEST
    (upstream context), then own DIGEST (load-bearing for THIS lead),
    then work brief (job-scoped).

    Phase-2 immediacy cure: BEFORE reading any DIGEST, refresh any DIGEST
    that lags its log via the librarian (`digest_librarian.py --if-stale`).
    This guarantees a freshly-appended canon line is visible to the next
    incarnation in the same process; closes the "short-horizon findings
    invisible to --show-inline" gap. Cheap (--if-stale is a no-op when fresh).
    """
    _refresh_inlined_digests(spec)
    parts = [INLINE_HEADER]

    parts.append(_section(
        "DOCTRINE/INDEX.md",
        _doctrine_index_text(),
    ))

    if spec.parent_lead:
        parts.append(_section(
            f"PARENT-DIGEST ({spec.parent_lead})",
            _lead_digest_text(spec.parent_lead, "parent_digest"),
        ))

    parts.append(_section(
        f"OWN-DIGEST ({spec.lead})",
        _lead_digest_text(spec.lead, "own_digest"),
    ))

    if spec.job_id:
        parts.append(_section(
            f"WORK-BRIEF ({spec.job_id})",
            _work_brief_text(spec.job_id),
        ))

    parts.append(INLINE_FOOTER)
    block = "\n".join(parts)

    # Enforce the ~5k token budget (chars proxy). If still over, hard-trim
    # the tail (own_digest already capped; this is a last-resort guard so
    # we never inject an unbounded blob).
    if len(block) > INLINE_BUDGET_CHARS:
        block = block[:INLINE_BUDGET_CHARS] + (
            f"\n…[hard-trimmed to {INLINE_BUDGET_CHARS} chars]\n{INLINE_FOOTER}\n"
        )
    return block


def assemble_prompt(spec: IncarnationSpec) -> str:
    """Build the full agent prompt: inline block + task + return contract."""
    inline = assemble_inline_block(spec)

    return_contract = (
        "REQUIRED RETURN SHAPE (validator REJECTS any return missing this):\n"
        '  {"memory_delta": {\n'
        '     "canon_appends": [ {"kind": "finding|decision|retraction|doctrine-candidate",\n'
        '                          "item": "<short claim>",\n'
        '                          "rationale": "<why it matters; trace to evidence>"} ],\n'
        '     "rationale": "<one-line why these appends"\n'
        '  },\n'
        '   "result": <your task output>\n'
        "  }\n"
        "Return ONLY valid JSON. canon_appends MAY be [] but the key MUST be present.\n"
    )

    schema_hint = ""
    if spec.schema_hint:
        schema_hint = f"\nRETURN-SHAPE HINT:\n{spec.schema_hint}\n"

    extra = ""
    if spec.extra_context:
        extra = f"\nADDITIONAL CONTEXT:\n{spec.extra_context}\n"

    prompt = (
        f"# Incarnation: lead={spec.lead} parent={spec.parent_lead} job={spec.job_id}\n"
        f"# Assembled at {_now_iso_utc()} by incarnation_runner.py\n"
        f"# YOU HAVE NO Read TOOL FOR MEMORY — memory is INLINED below.\n"
        "\n"
        f"{inline}\n"
        "\n"
        "## TASK\n"
        f"{spec.task.strip()}\n"
        f"{schema_hint}"
        f"{extra}"
        "\n"
        "## RETURN CONTRACT\n"
        f"{return_contract}"
    )
    return prompt


# ---------------------------------------------------------------------------
# Validate-return step
# ---------------------------------------------------------------------------

class ValidationError(ValueError):
    """Raised when the agent's return fails the memory_delta contract."""


def _parse_return(raw: str) -> dict:
    """Tolerantly parse the agent return — strict JSON, surfaces a clean error."""
    if raw is None:
        raise ValidationError("agent return is None (no output)")
    text = raw.strip()
    if not text:
        raise ValidationError("agent return is empty")
    # If the model fences with ```json ... ```, strip the fence before parsing.
    if text.startswith("```"):
        # remove first line (``` or ```json) and trailing ```
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"return is not valid JSON: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValidationError(
            f"return must be a JSON object, got {type(obj).__name__}"
        )
    return obj


def validate_return(raw: str) -> dict:
    """Enforce the memory_delta contract. Returns the parsed dict on success.

    Required shape:
      {
        "memory_delta": {
            "canon_appends": [ {"kind": ..., "item": ..., "rationale": ...} , ...],
            "rationale": "<str>"
        },
        ...
      }
    canon_appends MAY be [] (no learnings this turn) but the KEY MUST be present.
    """
    obj = _parse_return(raw)

    if "memory_delta" not in obj:
        raise ValidationError(
            "missing required field 'memory_delta' (validator rejects)"
        )
    md = obj["memory_delta"]
    if not isinstance(md, dict):
        raise ValidationError(
            f"'memory_delta' must be an object, got {type(md).__name__}"
        )

    if "canon_appends" not in md:
        raise ValidationError(
            "missing required field 'memory_delta.canon_appends'"
        )
    appends = md["canon_appends"]
    if not isinstance(appends, list):
        raise ValidationError(
            "'memory_delta.canon_appends' must be a list"
        )

    if "rationale" not in md or not isinstance(md["rationale"], str) \
            or not md["rationale"].strip():
        raise ValidationError(
            "missing/empty required field 'memory_delta.rationale' (str)"
        )

    # Validate each append shape (kind enum + non-empty item + non-empty rationale).
    for i, entry in enumerate(appends):
        if not isinstance(entry, dict):
            raise ValidationError(
                f"canon_appends[{i}] must be an object, got {type(entry).__name__}"
            )
        for key in ("kind", "item", "rationale"):
            if key not in entry:
                raise ValidationError(
                    f"canon_appends[{i}] missing required key {key!r}"
                )
            if not isinstance(entry[key], str) or not entry[key].strip():
                raise ValidationError(
                    f"canon_appends[{i}].{key} must be a non-empty string"
                )
        if entry["kind"] not in ALLOWED_KINDS:
            raise ValidationError(
                f"canon_appends[{i}].kind {entry['kind']!r} not in "
                f"{sorted(ALLOWED_KINDS)}"
            )

    return obj


# ---------------------------------------------------------------------------
# Write step — drive canon_append.py (the SOLE writer)
# ---------------------------------------------------------------------------

def _invoke_canon_append(
    lead: str,
    kind: str,
    item: str,
    rationale: str,
) -> dict:
    """Shell out to tools/canon_append.py for each append.

    Subprocess (not in-process import) intentionally — keeps canon_append.py
    as the SOLE writer per single-writer discipline, and means a buggy
    runtime can't bypass canon_append.py's validation.
    """
    if not CANON_APPEND_SCRIPT.exists():
        raise RuntimeError(f"canon_append.py not found at {CANON_APPEND_SCRIPT}")

    proc = subprocess.run(
        [
            sys.executable,
            str(CANON_APPEND_SCRIPT),
            "--lead", lead,
            "--kind", kind,
            "--item", item,
            "--rationale", rationale,
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"canon_append.py failed (exit {proc.returncode}): "
            f"stderr={proc.stderr.strip()!r}"
        )
    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise RuntimeError(
            f"canon_append.py produced unparsable stdout: "
            f"{proc.stdout!r} ({exc})"
        ) from exc
    appended = payload.get("appended")
    if not isinstance(appended, dict):
        raise RuntimeError(
            f"canon_append.py output missing 'appended' object: {payload!r}"
        )
    return appended


def _apply_memory_delta(lead: str, parsed_return: dict) -> list[dict]:
    """Walk memory_delta.canon_appends and invoke canon_append.py for each."""
    appends = parsed_return["memory_delta"]["canon_appends"]
    written: list[dict] = []
    for entry in appends:
        written.append(_invoke_canon_append(
            lead=lead,
            kind=entry["kind"],
            item=entry["item"],
            rationale=entry["rationale"],
        ))
    return written


# ---------------------------------------------------------------------------
# Prompt-log step (for offline inspection + self-test grep)
# ---------------------------------------------------------------------------

def _now_iso_utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_prompt_log(spec: IncarnationSpec, prompt: str) -> Path:
    PROMPT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = f"{stamp}-{spec.lead}-{uuid.uuid4().hex[:8]}.prompt.txt"
    p = PROMPT_LOG_DIR / fname
    p.write_text(prompt, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Orchestrator — wrap one agent invocation end-to-end
# ---------------------------------------------------------------------------

def run_incarnation(
    spec: IncarnationSpec,
    model_fn: Callable[[str], str],
) -> IncarnationResult:
    """READ → invoke `model_fn(prompt)` → VALIDATE → WRITE.

    `model_fn` is the seam: in production it bridges to a real agent
    invocation; in tests it's a deterministic stub. The runtime owns
    everything around it.
    """
    prompt = assemble_prompt(spec)
    log_path = _write_prompt_log(spec, prompt)
    inline_chars = len(assemble_inline_block(spec))

    raw = model_fn(prompt)

    try:
        parsed = validate_return(raw)
    except ValidationError as exc:
        return IncarnationResult(
            ok=False,
            lead=spec.lead,
            rejection_reason=str(exc),
            raw_return=raw,
            prompt_log_path=log_path,
            inline_block_chars=inline_chars,
        )

    appended = _apply_memory_delta(spec.lead, parsed)
    return IncarnationResult(
        ok=True,
        lead=spec.lead,
        appended=appended,
        raw_return=raw,
        prompt_log_path=log_path,
        inline_block_chars=inline_chars,
    )


# ---------------------------------------------------------------------------
# Self-test — exercises the runtime WITHOUT calling a real model
# ---------------------------------------------------------------------------

def run_self_test() -> int:
    """Three subtests:
      ST1. Build the inline block for a fake lead; log the assembled prompt
           to disk; grep-confirm the inline-header AND a known section line
           landed in the prompt file.
      ST2. Run VALIDATE-RETURN on a return MISSING `memory_delta` → MUST
           be REJECTED.
      ST3. Run end-to-end with a return WITH `memory_delta` → MUST be
           ACCEPTED and trigger canon_append.py (line count grows on
           mem/canon/_runner_selftest/log.jsonl).

    Exit 0 = all pass; 1 = any fail. Prints a one-line verdict per subtest.
    """
    fake_lead = "_runner_selftest"
    parent_lead = "_runner_selftest_parent"
    job_id = "_runner_selftest_job"

    failures: list[str] = []

    # Pre-seed: Phase-2 wires the librarian into assemble_inline_block, so
    # a pre-written DIGEST gets OVERWRITTEN if it lags its log. Seed the
    # marker via the LOG (canon_append), then let the librarian render the
    # DIGEST from it — that's the librarian-correct path. (Pre-Phase-2 this
    # block wrote the DIGEST directly; that contradicted librarian freshness
    # and is why this test now seeds the log instead.)
    own_digest_marker = f"OWN-DIGEST-MARKER-{uuid.uuid4().hex[:8]}"
    parent_digest_marker = f"PARENT-DIGEST-MARKER-{uuid.uuid4().hex[:8]}"
    brief_marker = f"BRIEF-MARKER-{uuid.uuid4().hex[:8]}"

    for lead_id, marker in (
        (fake_lead, own_digest_marker),
        (parent_lead, parent_digest_marker),
    ):
        (MEM_CANON / lead_id).mkdir(parents=True, exist_ok=True)
        _invoke_canon_append(
            lead=lead_id,
            kind="finding",
            item=f"runner-selftest seed {marker}",
            rationale=(
                "Phase-1/2 runner self-test: seed a canon line so the "
                "librarian renders a fresh DIGEST containing the marker "
                "(immediacy-wiring verification)."
            ),
        )
        # Drop any stale DIGEST so the freshness gate triggers a rebuild;
        # without this the test could pass against a leftover DIGEST.
        stale_digest = MEM_CANON / lead_id / "DIGEST.md"
        if stale_digest.exists():
            stale_digest.unlink()

    (MEM_WORK / job_id).mkdir(parents=True, exist_ok=True)
    (MEM_WORK / job_id / "brief.md").write_text(
        f"# fake brief\n\n- {brief_marker}\n",
        encoding="utf-8",
    )

    spec = IncarnationSpec(
        lead=fake_lead,
        parent_lead=parent_lead,
        job_id=job_id,
        task="Self-test: do not call a real model. Echo the contract back.",
    )

    # ---------------- ST1: inline-block assembled + logged ----------------
    prompt = assemble_prompt(spec)
    log_path = _write_prompt_log(spec, prompt)

    on_disk = log_path.read_text(encoding="utf-8")
    st1_checks = [
        (INLINE_HEADER, "inline header"),
        (INLINE_FOOTER, "inline footer"),
        (own_digest_marker, "own DIGEST marker"),
        (parent_digest_marker, "parent DIGEST marker"),
        (brief_marker, "work-brief marker"),
        ("YOU HAVE NO Read TOOL FOR MEMORY", "no-read-tool banner"),
        ("REQUIRED RETURN SHAPE", "return-contract banner"),
    ]
    st1_missing = [label for needle, label in st1_checks if needle not in on_disk]
    if st1_missing:
        failures.append(f"ST1 missing in prompt log: {st1_missing}")
        print(f"FAIL ST1 inline-block: prompt log @ {log_path} missing {st1_missing}")
    else:
        print(f"PASS ST1 inline-block: prompt log @ {log_path} contains all markers")

    # ---------------- ST2: VALIDATE-RETURN rejects missing memory_delta ----
    bad_return = json.dumps({"result": "I forgot the memory_delta field"})

    def bad_model_fn(_p: str) -> str:
        return bad_return

    bad_result = run_incarnation(spec, bad_model_fn)
    if bad_result.ok:
        failures.append("ST2 should have REJECTED missing memory_delta")
        print("FAIL ST2 reject: a return without memory_delta was ACCEPTED")
    elif "memory_delta" not in (bad_result.rejection_reason or ""):
        failures.append(
            f"ST2 reject reason should mention memory_delta, got "
            f"{bad_result.rejection_reason!r}"
        )
        print(
            f"FAIL ST2 reject: rejection reason did not mention memory_delta: "
            f"{bad_result.rejection_reason!r}"
        )
    else:
        print(
            f"PASS ST2 reject: missing memory_delta REJECTED — "
            f"{bad_result.rejection_reason!r}"
        )

    # ---------------- ST3: ACCEPT + trigger canon_append.py ----------------
    log_jsonl = MEM_CANON / fake_lead / "log.jsonl"
    pre_lines = _count_lines(log_jsonl)

    st3_item_marker = f"runner-selftest-{uuid.uuid4().hex[:8]}"
    good_return = json.dumps({
        "result": "self-test result payload",
        "memory_delta": {
            "canon_appends": [
                {
                    "kind": "finding",
                    "item": f"incarnation_runner self-test {st3_item_marker}",
                    "rationale": (
                        "Phase-1 build gate ST3 — proves end-to-end loop: "
                        "assemble → validate → canon_append.py writes."
                    ),
                },
            ],
            "rationale": "ST3 of incarnation_runner --self-test",
        },
    })

    def good_model_fn(_p: str) -> str:
        return good_return

    good_result = run_incarnation(spec, good_model_fn)
    post_lines = _count_lines(log_jsonl)

    if not good_result.ok:
        failures.append(f"ST3 should have ACCEPTED, got rejection: "
                        f"{good_result.rejection_reason}")
        print(f"FAIL ST3 accept: REJECTED — {good_result.rejection_reason!r}")
    elif post_lines != pre_lines + 1:
        failures.append(
            f"ST3 line count expected {pre_lines + 1}, got {post_lines}"
        )
        print(
            f"FAIL ST3 accept: log lines went {pre_lines} -> {post_lines} "
            f"(expected {pre_lines + 1})"
        )
    else:
        # Also verify the appended entry has our marker and the runtime
        # returned the canonical 'appended' record from canon_append.py.
        last = log_jsonl.read_text(encoding="utf-8").splitlines()[-1]
        try:
            parsed_last = json.loads(last)
        except json.JSONDecodeError as exc:
            failures.append(f"ST3 last log line not valid JSON: {exc}")
            print(f"FAIL ST3 accept: last log line not valid JSON: {exc}")
        else:
            if st3_item_marker not in parsed_last.get("item", ""):
                failures.append("ST3 marker not in appended item")
                print(
                    f"FAIL ST3 accept: marker {st3_item_marker!r} missing from "
                    f"{parsed_last!r}"
                )
            elif not good_result.appended or \
                    good_result.appended[0].get("id") != parsed_last.get("id"):
                failures.append("ST3 runtime appended record id mismatch")
                print(
                    "FAIL ST3 accept: runtime-returned appended id does not "
                    "match on-disk id"
                )
            else:
                print(
                    f"PASS ST3 accept: end-to-end loop wrote to {log_jsonl} "
                    f"({pre_lines} -> {post_lines}); appended id="
                    f"{parsed_last.get('id')}"
                )

    if failures:
        print(f"\nSELF-TEST FAILED ({len(failures)} subtest(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(
        "\nSELF-TEST PASSED — runtime referee shape is intact "
        "(inline-block assembled+logged, validator rejects missing "
        "memory_delta, accepts well-formed, canon_append wrote)."
    )
    return 0


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return n


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="incarnation_runner.py",
        description=(
            "The ONE shared runtime referee for AiCIV-Native Org agent "
            "incarnations (Phase-1, SPEC §5 + §9). Assembles inlined memory, "
            "validates memory_delta on return, drives canon_append.py "
            "(single-writer) for canon updates."
        ),
    )
    p.add_argument(
        "--self-test",
        action="store_true",
        help=(
            "Run the self-test (no real model call): assemble + log a "
            "prompt, exercise validate-return with a return MISSING "
            "memory_delta (must reject) and one WITH it (must accept + "
            "trigger canon_append.py). Exit 0 pass / 1 fail."
        ),
    )
    p.add_argument(
        "--show-inline",
        metavar="LEAD",
        help=(
            "Diagnostic: print the inlined-memory block that WOULD be "
            "assembled for LEAD (no model invocation, no write)."
        ),
    )
    p.add_argument(
        "--parent",
        metavar="LEAD",
        help="Optional parent lead id (used with --show-inline).",
    )
    p.add_argument(
        "--job",
        metavar="JOB_ID",
        help="Optional job id (used with --show-inline).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if args.show_inline:
        spec = IncarnationSpec(
            lead=args.show_inline,
            parent_lead=args.parent,
            job_id=args.job,
            task="(diagnostic — no task)",
        )
        # assemble_inline_block() internally fires _refresh_inlined_digests
        # (--if-stale librarian rebuild) for own + parent DIGESTs BEFORE
        # reading them, so a freshly-appended canon line is never invisible
        # to a --show-inline diagnostic. (Phase-2 immediacy cure.)
        sys.stdout.write(assemble_inline_block(spec) + "\n")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
