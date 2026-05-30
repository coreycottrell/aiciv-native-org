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

DIGEST REBUILD CONTRACT (2026-05-30 detect-only split):
  - This runtime DETECTS digest staleness (--check-stale + the warn-if-stale
    helper invoked from assemble_inline_block).
  - This runtime DOES NOT REBUILD.
  - REBUILD is owned by the WORKFLOW LAYER. The org-assembler (or any
    parent workflow that's about to incarnate a lead) invokes
        workflow('digest-librarian', { lead, now })
    for each stale lead BEFORE calling this runtime to assemble + run.
  - The digest-librarian WORKFLOW (workflows/digest-librarian.js) does
    agentic synthesis via agent() on the Claude-Code workflow runtime
    (Opus 4.8 default). NO direct-model-SDK call from the python layer.
    Federation-IP across any civ running the same Claude-Code + Opus-4.8
    substrate; the only independent axis is TGIM CIV-IDENTITY (each
    adopter posts as themselves via their own AgentAUTH keypair).
  - tools/digest_librarian.py is RETAINED ONLY as a no-agent extractive
    fallback (handy for --self-test and cold-cache bootstrap). The runtime
    no longer invokes it from inline-block assembly. There is intentionally
    NO direct-model-API agentic path in this python tool.
  - See: skills/digest-librarian/SKILL.md  (full contract +
    rationale + immediacy handoff diagram).

CLI:
    python3 tools/incarnation_runner.py --self-test
        Builds an inline block for a fake lead, logs the assembled prompt
        to a file, exercises VALIDATE-RETURN with a return MISSING
        memory_delta (must REJECT) and one WITH it (must ACCEPT and trigger
        canon_append).

    python3 tools/incarnation_runner.py --check-stale <lead> [--json]
        Report whether mem/canon/<lead>/DIGEST.md lags its log. Exit 0 +
        prints/JSON-emits {stale, log_lines, digest_ledger_lines, reason}.
        DOES NOT REBUILD. The workflow layer reads this and invokes
        workflow('digest-librarian', {lead, now}) when stale=true.

    python3 tools/incarnation_runner.py --show-inline <lead> [--parent X] [--job Y]
        Diagnostic — print the inline block that WOULD be assembled. If a
        digest is stale, emits the WARN to stderr (no rebuild).

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
# Phase-2 NOTE (substrate-independent rebuild contract — 2026-05-30):
# This runtime DETECTS digest staleness (see --check-stale CLI + _digest_is_stale
# below), but it DOES NOT REBUILD. Rebuild is owned by the WORKFLOW LAYER
# (org-assembler / parent workflow), which invokes the digest-librarian
# WORKFLOW (workflows/digest-librarian.js) for each stale lead BEFORE
# assemble_inline_block() reads the DIGEST. This split keeps the runtime
# substrate-independent (no model-API dependency in python) and routes all
# agentic synthesis through agent() on the workflow runtime's model — see
# SPEC-SHEET-v0.2 §5 + §9 and skills/digest-librarian/SKILL.md.
#
# tools/digest_librarian.py is retained ONLY as a no-agent extractive
# fallback (also useful for --self-test); the runtime no longer invokes it
# from inline-block assembly. If you need a one-shot rebuild outside a
# workflow context (cold cache, no workflow runtime up yet), run
# `python3 tools/digest_librarian.py --lead <id> --now <ISO-Z> --force-extractive`
# explicitly — the canonical smart path is workflow('digest-librarian').
DIGEST_LIBRARIAN_SCRIPT = REPO_ROOT / "tools" / "digest_librarian.py"  # legacy / no-agent fallback path only

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
# DIGEST FRESHNESS — DETECT ONLY (the runtime does NOT rebuild)
# ---------------------------------------------------------------------------
#
# Contract (2026-05-30, SPEC-SHEET-v0.2 §5 + §9):
#   - The runtime DETECTS staleness (helpers below + --check-stale CLI).
#   - The runtime DOES NOT REBUILD.
#   - REBUILD is owned by the WORKFLOW LAYER: the org-assembler (or any parent
#     workflow that's about to incarnate a lead) invokes
#         workflow('digest-librarian', { lead, now })
#     for each stale lead BEFORE this runtime's assemble_inline_block() reads
#     the DIGEST. The digest-librarian workflow does agentic synthesis via
#     agent() on the Claude-Code workflow runtime (Opus 4.8 default) — no
#     direct-model-SDK call from the python layer.
#   - See: workflows/digest-librarian.js  +  skills/digest-librarian/SKILL.md
#
# Why the split: the runtime is the REFEREE (rules unbreakable, narrow
# surface, no model-API dep). The workflow is the CONDUCTOR (decisions,
# model calls, decomposition). A python referee calling a model is the wrong
# layering — that's the SDK-bound history we're cutting. Detection here,
# rebuild in the workflow layer.
#
# Caller pattern (org-assembler or parent workflow):
#
#     for lead in leads_to_inline:
#         stat = json.loads(run([
#             'python3', 'tools/incarnation_runner.py',
#             '--check-stale', lead, '--json'
#         ]).stdout)
#         if stat['stale']:
#             await workflow('digest-librarian', { lead, now: iso_now() })
#     # ...now safe to invoke the runtime for assemble + run.
#
# Failure mode: if the caller forgets to rebuild a stale DIGEST, the runtime
# still inlines whatever's on disk and logs a stderr warning naming the
# stale lead — better to run with a stale digest than fail-closed. The
# warning is the only nudge; the workflow layer remains the rebuild owner.

# Sentinel + regex shared with the digest-librarian workflow's frontmatter.
_DIGEST_FRONTMATTER_RE = __import__("re").compile(
    r"^---\s*\n(?P<fm>.*?)\n---\s*\n", __import__("re").DOTALL
)
_FM_LEDGER_RE = __import__("re").compile(
    r"^ledger_lines_at_rebuild:\s*(?P<n>\d+)\s*$", __import__("re").MULTILINE
)


def _parse_digest_ledger_lines(digest_path: Path) -> Optional[int]:
    """Return the frontmatter `ledger_lines_at_rebuild:` value, or None if
    absent / malformed / DIGEST.md does not exist."""
    if not digest_path.exists():
        return None
    try:
        text = digest_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = _DIGEST_FRONTMATTER_RE.match(text)
    if not m:
        return None
    fm = m.group("fm")
    n = _FM_LEDGER_RE.search(fm)
    if not n:
        return None
    try:
        return int(n.group("n"))
    except (ValueError, TypeError):
        return None


def check_digest_stale(lead: str) -> dict:
    """Detect whether mem/canon/<lead>/DIGEST.md lags its log.

    Returns:
        {
          "lead": <id>,
          "log_lines": <int>,                   # current line count in log.jsonl
          "digest_ledger_lines": <int|None>,    # frontmatter value, or None if no digest
          "stale": <bool>,                      # True if needs rebuild
          "reason": <str>,                      # human-readable diagnostic
        }

    Staleness rules (in order):
      - no log + no digest               → not stale (nothing to inline)
      - no digest + log has lines        → stale (initial build needed)
      - digest exists but no frontmatter → stale (corrupt; rebuild)
      - digest_ledger_lines < log_lines  → stale (new entries appeared)
      - digest_ledger_lines > log_lines  → stale (log shrank? corrupt; rebuild)
      - equal                            → fresh
    """
    log_path = MEM_CANON / lead / "log.jsonl"
    digest_path = MEM_CANON / lead / "DIGEST.md"
    log_lines = _count_lines(log_path)
    digest_ledger = _parse_digest_ledger_lines(digest_path)

    if log_lines == 0 and not digest_path.exists():
        return {
            "lead": lead, "log_lines": 0, "digest_ledger_lines": None,
            "stale": False, "reason": "no log + no digest (trivially fresh)",
        }
    if not digest_path.exists():
        return {
            "lead": lead, "log_lines": log_lines, "digest_ledger_lines": None,
            "stale": True, "reason": "DIGEST.md does not exist; initial build needed",
        }
    if digest_ledger is None:
        return {
            "lead": lead, "log_lines": log_lines, "digest_ledger_lines": None,
            "stale": True,
            "reason": "DIGEST.md missing/malformed frontmatter `ledger_lines_at_rebuild:`",
        }
    if digest_ledger != log_lines:
        return {
            "lead": lead, "log_lines": log_lines, "digest_ledger_lines": digest_ledger,
            "stale": True,
            "reason": (
                f"DIGEST.md ledger_lines_at_rebuild={digest_ledger} != "
                f"current log_lines={log_lines}"
            ),
        }
    return {
        "lead": lead, "log_lines": log_lines, "digest_ledger_lines": digest_ledger,
        "stale": False, "reason": "frontmatter ledger matches current log line count",
    }


def _warn_if_stale_before_inline(spec: "IncarnationSpec") -> list[dict]:
    """Emit a STDERR warning for any DIGEST we're about to inline that is
    stale. The runtime DOES NOT rebuild — see module-level contract. The
    workflow layer is expected to have already invoked
    workflow('digest-librarian', {lead, now}) for each stale lead BEFORE
    calling the runtime. Returns the staleness reports for caller logging.
    """
    reports: list[dict] = [check_digest_stale(spec.lead)]
    if spec.parent_lead:
        reports.append(check_digest_stale(spec.parent_lead))
    for r in reports:
        if r["stale"]:
            sys.stderr.write(
                f"incarnation_runner: WARNING — DIGEST for lead {r['lead']!r} is "
                f"STALE ({r['reason']}). The workflow layer should have invoked "
                f"workflow('digest-librarian', {{lead: {r['lead']!r}, now: ...}}) "
                f"before this incarnation. Inlining whatever is on disk; "
                f"short-horizon findings may be invisible.\n"
            )
    return reports


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

    Immediacy contract (2026-05-30 substrate-independent rebuild):
    BEFORE reading any DIGEST we DETECT staleness (own + parent) and emit
    a STDERR WARNING if stale. The runtime DOES NOT REBUILD — that's the
    workflow layer's job. The org-assembler (or any parent workflow about
    to incarnate this lead) is expected to have invoked
        workflow('digest-librarian', { lead, now })
    for each stale lead BEFORE calling the runtime. See module docstring
    + skills/digest-librarian/SKILL.md for the full contract.

    Degraded mode: if the workflow layer forgot, we still inline whatever
    DIGEST is on disk (better stale than fail-closed) and the WARNING
    surfaces the lapse for the post-hoc auditor (workflow-lead) to file.
    """
    _warn_if_stale_before_inline(spec)
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
    """Four subtests:
      ST1. Build the inline block for a fake lead; log the assembled prompt
           to disk; grep-confirm the inline-header AND a known section line
           landed in the prompt file.
      ST2. Run VALIDATE-RETURN on a return MISSING `memory_delta` → MUST
           be REJECTED.
      ST3. Run end-to-end with a return WITH `memory_delta` → MUST be
           ACCEPTED and trigger canon_append.py (line count grows on
           mem/canon/_runner_selftest/log.jsonl).
      ST4. check_digest_stale() correctly DETECTS staleness — after ST3
           appended a line, frontmatter ledger_lines_at_rebuild no longer
           matches → stale=True with a sane reason. (Confirms the runtime
           does its DETECT-ONLY half of the workflow-layer rebuild contract.)

    Exit 0 = all pass; 1 = any fail. Prints a one-line verdict per subtest.
    """
    fake_lead = "_runner_selftest"
    parent_lead = "_runner_selftest_parent"
    job_id = "_runner_selftest_job"

    failures: list[str] = []

    # Pre-seed:
    # The runtime no longer rebuilds DIGESTs (that's the workflow layer's job
    # via workflow('digest-librarian')). So for the self-test we seed BOTH:
    #   - one canon line via canon_append (so log.jsonl has content)
    #   - a hand-rolled DIGEST.md with frontmatter matching log_lines=1 so
    #     it's "fresh" — ST1 then asserts the inline block carries the marker
    #     verbatim from that DIGEST.
    # This isolates the runtime from the librarian: ST1 tests inline-block
    # assembly + READ; the librarian's correctness is tested separately
    # (workflows/digest-librarian.js + tools/digest_librarian.py --self-test).
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
                "Runner self-test: seed a canon line and hand-write a "
                "matching DIGEST so the runtime's READ + warn-if-stale path "
                "can be exercised without depending on the librarian."
            ),
        )
        # Hand-roll a fresh DIGEST whose frontmatter matches the current
        # log_lines, so check_digest_stale() reports fresh and the inline
        # block injects the marker.
        digest_path = MEM_CANON / lead_id / "DIGEST.md"
        log_path = MEM_CANON / lead_id / "log.jsonl"
        log_lines = _count_lines(log_path)
        digest_path.write_text(
            (
                "---\n"
                f"last_rebuilt_at: {_now_iso_utc()}\n"
                f"ledger_lines_at_rebuild: {log_lines}\n"
                f"lead: {lead_id}\n"
                f"source_log: mem/canon/{lead_id}/log.jsonl\n"
                "mechanism: agentic-workflow\n"
                "---\n\n"
                "## Canon (load-bearing first — agentic-workflow)\n\n"
                f"- `id=selftest-seed` `2026-05-30T00:00:00Z` **finding** — runner-selftest seed {marker}\n"
            ),
            encoding="utf-8",
        )

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

    # ---------------- ST4: DETECT-ONLY staleness contract ----------------
    # After ST3, the DIGEST frontmatter ledger_lines_at_rebuild is stale
    # (still says 1, but log has post_lines=2). The runtime must REPORT
    # stale=True with a clear reason. It must NOT rebuild — that's the
    # workflow layer's job (workflow('digest-librarian', ...)).
    st4_report = check_digest_stale(fake_lead)
    if not st4_report.get("stale"):
        failures.append(
            f"ST4 expected stale=True after canon append, got {st4_report!r}"
        )
        print(f"FAIL ST4 detect: expected stale, got {st4_report!r}")
    elif "ledger_lines_at_rebuild" not in st4_report.get("reason", "") and \
            "missing" not in st4_report.get("reason", ""):
        failures.append(
            f"ST4 stale reason should mention ledger_lines_at_rebuild, "
            f"got {st4_report!r}"
        )
        print(f"FAIL ST4 detect: reason unexpected: {st4_report!r}")
    else:
        # Also verify the DIGEST.md was NOT rebuilt (runtime is DETECT-only).
        # We do that by re-reading the on-disk frontmatter and confirming
        # ledger_lines_at_rebuild is still the PRE-append value.
        on_disk_ledger = _parse_digest_ledger_lines(MEM_CANON / fake_lead / "DIGEST.md")
        if on_disk_ledger is None:
            failures.append("ST4 DIGEST.md frontmatter unreadable after detect")
            print("FAIL ST4 detect: DIGEST.md frontmatter unreadable")
        elif on_disk_ledger == post_lines:
            failures.append(
                f"ST4 runtime appears to have REBUILT the DIGEST "
                f"(frontmatter ledger={on_disk_ledger} == post_lines); "
                f"runtime must be DETECT-ONLY"
            )
            print(
                f"FAIL ST4 detect: runtime rebuilt DIGEST (ledger now "
                f"{on_disk_ledger}); workflow-layer contract violated"
            )
        else:
            print(
                f"PASS ST4 detect: stale correctly reported "
                f"(log_lines={st4_report['log_lines']}, "
                f"digest_ledger_lines={st4_report['digest_ledger_lines']}); "
                f"runtime did NOT rebuild (DETECT-ONLY contract honored)"
            )

    if failures:
        print(f"\nSELF-TEST FAILED ({len(failures)} subtest(s)):")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(
        "\nSELF-TEST PASSED — runtime referee shape is intact "
        "(inline-block assembled+logged, validator rejects missing "
        "memory_delta, accepts well-formed, canon_append wrote, "
        "staleness detected without rebuild)."
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
            "assembled for LEAD (no model invocation, no write). Emits a "
            "STDERR WARNING per stale DIGEST (own + parent); the workflow "
            "layer is expected to have already invoked "
            "workflow('digest-librarian', {lead, now}) for each stale lead."
        ),
    )
    p.add_argument(
        "--check-stale",
        metavar="LEAD",
        help=(
            "DETECT digest staleness for LEAD (no rebuild). Compares "
            "mem/canon/<LEAD>/DIGEST.md frontmatter `ledger_lines_at_rebuild:` "
            "against the current log line count. Exit 0 always; prints/JSON-emits "
            "{lead, log_lines, digest_ledger_lines, stale, reason}. The workflow "
            "layer reads this and invokes workflow('digest-librarian', {lead, now}) "
            "when stale=true."
        ),
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON (used with --check-stale).",
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

    if args.check_stale:
        report = check_digest_stale(args.check_stale)
        if args.json:
            sys.stdout.write(json.dumps(report) + "\n")
        else:
            sys.stdout.write(
                f"lead={report['lead']} stale={report['stale']} "
                f"log_lines={report['log_lines']} "
                f"digest_ledger_lines={report['digest_ledger_lines']} "
                f"reason={report['reason']!r}\n"
            )
        # Always exit 0 — staleness is informational, not an error condition.
        # The workflow layer interprets stale=true and invokes the rebuild.
        return 0

    if args.show_inline:
        spec = IncarnationSpec(
            lead=args.show_inline,
            parent_lead=args.parent,
            job_id=args.job,
            task="(diagnostic — no task)",
        )
        # assemble_inline_block() DETECTS staleness on own + parent and
        # emits STDERR WARN per stale DIGEST. It does NOT rebuild — that's
        # the workflow layer's job (workflow('digest-librarian', {lead, now})).
        # If a freshly-appended canon line is missing from this diagnostic,
        # the workflow-layer rebuild hasn't been wired into the caller yet.
        sys.stdout.write(assemble_inline_block(spec) + "\n")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
