#!/usr/bin/env python3
"""
canon_append.py — SOLE append-only writer to mem/canon/<lead>/log.jsonl.

Part of the AiCIV-Native Org Phase-1 foundation (SPEC §5: WRITE step of the
memory pipe). Agents NEVER write directly; the incarnation_runner calls this.

Closed enum for `kind`:
    finding | decision | retraction | doctrine-candidate

Behavior:
  - Append EXACTLY ONE JSON line per invocation.
  - On append, if log grew +50 lines since the last DIGEST rebuild, write a
    MECHANICAL placeholder DIGEST.md = last-200-lines of the log (one line per
    canon entry, rendered as compact markdown bullets).
    Phase 2 replaces this placeholder with the agentic librarian (Option B).

CLI:
    python3 tools/canon_append.py --lead <id> --kind <enum> \\
        --item "<short claim>" --rationale "<why it matters>"

Self-test:
    python3 tools/canon_append.py --self-test
    # Appends to mem/canon/_selftest/log.jsonl and verifies the line landed.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Resolve repo root from this file's location (tools/ is a child of repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
MEM_CANON = REPO_ROOT / "mem" / "canon"

ALLOWED_KINDS = frozenset({
    "finding",
    "decision",
    "retraction",
    "doctrine-candidate",
})

# Digest-rebuild trigger: per SPEC §5 ("at +50 lines runtime rebuilds DIGEST.md").
# This is a placeholder threshold per OQ-4; revisit with production data.
DIGEST_TRIGGER_DELTA = 50

# Mechanical placeholder digest target length (Phase 1).
# SPEC §5: DIGEST.md ≤200 lines.
DIGEST_TAIL_LINES = 200

# Restrict lead ids to a safe charset so we cannot path-traverse out of mem/canon.
# Also covers the reserved _selftest lead (leading underscore allowed).
LEAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")

DIGEST_MARKER_PREFIX = "<!-- canon_append.py digest@"  # used to read back ledger_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso_utc() -> str:
    """RFC-3339 UTC timestamp, second resolution + 'Z' suffix."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_lead(lead: str) -> str:
    if not LEAD_ID_PATTERN.match(lead):
        raise ValueError(
            f"invalid --lead {lead!r}: must match {LEAD_ID_PATTERN.pattern}"
        )
    return lead


def _validate_kind(kind: str) -> str:
    if kind not in ALLOWED_KINDS:
        raise ValueError(
            f"invalid --kind {kind!r}: allowed = {sorted(ALLOWED_KINDS)}"
        )
    return kind


def _lead_dir(lead: str) -> Path:
    d = MEM_CANON / lead
    d.mkdir(parents=True, exist_ok=True)
    return d


def _log_path(lead: str) -> Path:
    return _lead_dir(lead) / "log.jsonl"


def _digest_path(lead: str) -> Path:
    return _lead_dir(lead) / "DIGEST.md"


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return n


def _read_digest_ledger_lines(digest: Path) -> int:
    """Parse the marker we embed in DIGEST.md so we know when last rebuild was."""
    if not digest.exists():
        return 0
    try:
        with digest.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith(DIGEST_MARKER_PREFIX):
                    # marker shape: <!-- canon_append.py digest@<lines> at <ts> -->
                    try:
                        chunk = line.split("digest@", 1)[1]
                        n_str = chunk.split(" ", 1)[0]
                        return int(n_str)
                    except (IndexError, ValueError):
                        return 0
    except OSError:
        return 0
    return 0


def _maybe_rebuild_digest(lead: str) -> bool:
    """Rebuild MECHANICAL placeholder digest if log grew +DIGEST_TRIGGER_DELTA lines.

    Returns True if a rebuild occurred. Phase 2 swaps this for the agentic
    librarian; the trigger condition stays the same.
    """
    log = _log_path(lead)
    digest = _digest_path(lead)
    current = _count_lines(log)
    previous = _read_digest_ledger_lines(digest)

    # Trigger on first-ever digest too (previous==0 and current>=DIGEST_TRIGGER_DELTA),
    # or any growth beyond the threshold since last rebuild.
    if (current - previous) < DIGEST_TRIGGER_DELTA:
        return False

    # MECHANICAL placeholder: last-DIGEST_TAIL_LINES of the log, one bullet each.
    tail: list[str] = []
    with log.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()
    for raw in lines[-DIGEST_TAIL_LINES:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
            ts = obj.get("ts", "?")
            kind = obj.get("kind", "?")
            item = obj.get("item", "")
            tail.append(f"- `{ts}` **{kind}** — {item}")
        except json.JSONDecodeError:
            tail.append(f"- (unparsable) {raw[:200]}")

    marker = f"{DIGEST_MARKER_PREFIX}{current} at {_now_iso_utc()} -->"
    body = "\n".join([
        f"# mem/canon/{lead}/DIGEST.md",
        "",
        marker,
        "",
        f"**Mode**: MECHANICAL placeholder (last-{DIGEST_TAIL_LINES} canon lines).",
        "**Replaced by**: Phase-2 agentic librarian (`workflows/digest-librarian.js`).",
        f"**Ledger lines at rebuild**: {current}",
        "",
        "## Recent canon",
        "",
        *tail,
        "",
    ])
    digest.write_text(body, encoding="utf-8")
    return True


def append_canon(
    lead: str,
    kind: str,
    item: str,
    rationale: str,
    *,
    writer: str = "canon_append.py",
    extra: dict | None = None,
) -> dict:
    """Append exactly one JSON line to mem/canon/<lead>/log.jsonl and return it.

    Raises ValueError on invalid lead/kind/empty fields.
    """
    lead = _validate_lead(lead)
    kind = _validate_kind(kind)
    if not item or not item.strip():
        raise ValueError("--item must be a non-empty string")
    if not rationale or not rationale.strip():
        raise ValueError("--rationale must be a non-empty string")

    entry = {
        "ts": _now_iso_utc(),
        "id": uuid.uuid4().hex,
        "lead": lead,
        "kind": kind,
        "item": item.strip(),
        "rationale": rationale.strip(),
        "writer": writer,
    }
    if extra:
        # Don't let extras shadow load-bearing fields.
        for k, v in extra.items():
            if k not in entry:
                entry[k] = v

    line = json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
    log = _log_path(lead)
    # Atomic-enough append: open in "a", write once. Single-writer discipline
    # (only this script writes to mem/canon/<lead>/log.jsonl) is the contract;
    # POSIX append is atomic for write() <= PIPE_BUF for single small lines.
    with log.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass  # tmpfs etc; the write hit the page cache, good enough

    _maybe_rebuild_digest(lead)
    return entry


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def run_self_test() -> int:
    """Append to mem/canon/_selftest/log.jsonl and verify the line landed.

    Exit 0 = pass, 1 = fail. Prints a one-line verdict.
    """
    lead = "_selftest"
    log = _log_path(lead)
    pre_count = _count_lines(log)

    marker = f"selftest-{uuid.uuid4().hex[:8]}"
    try:
        entry = append_canon(
            lead=lead,
            kind="finding",
            item=f"canon_append.py self-test {marker}",
            rationale="Phase-1 build gate — proves single append + JSONL parses + line count grew by exactly 1.",
            writer="canon_append.py --self-test",
        )
    except Exception as exc:
        print(f"FAIL self-test: append raised {type(exc).__name__}: {exc}")
        return 1

    post_count = _count_lines(log)
    if post_count != pre_count + 1:
        print(
            f"FAIL self-test: line count went {pre_count} -> {post_count} "
            f"(expected {pre_count + 1})"
        )
        return 1

    # Verify the last line parses and contains our marker
    with log.open("r", encoding="utf-8") as fh:
        last = fh.readlines()[-1].strip()
    try:
        parsed = json.loads(last)
    except json.JSONDecodeError as exc:
        print(f"FAIL self-test: last line is not valid JSON: {exc}")
        return 1

    if marker not in parsed.get("item", ""):
        print(f"FAIL self-test: marker {marker!r} not found in last entry")
        return 1
    if parsed.get("id") != entry["id"]:
        print("FAIL self-test: returned entry id != id on disk")
        return 1
    if parsed.get("kind") not in ALLOWED_KINDS:
        print(f"FAIL self-test: kind {parsed.get('kind')!r} not in closed enum")
        return 1

    print(
        f"PASS self-test: appended id={entry['id']} to {log} "
        f"(lines {pre_count} -> {post_count})"
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="canon_append.py",
        description=(
            "Sole append-only writer to mem/canon/<lead>/log.jsonl "
            "(AiCIV-Native Org Phase 1, SPEC §5)."
        ),
    )
    p.add_argument("--lead", help="Lead identity id (e.g. 'web-lead').")
    p.add_argument(
        "--kind",
        choices=sorted(ALLOWED_KINDS),
        help="Closed enum: finding | decision | retraction | doctrine-candidate.",
    )
    p.add_argument("--item", help="Short claim (single-line preferred).")
    p.add_argument("--rationale", help="Why this matters; trace to evidence.")
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Run the self-test against mem/canon/_selftest/ and exit.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    missing = [
        name
        for name in ("lead", "kind", "item", "rationale")
        if getattr(args, name) is None
    ]
    if missing:
        parser.error(
            "missing required arguments: " + ", ".join(f"--{m}" for m in missing)
        )

    try:
        entry = append_canon(
            lead=args.lead,
            kind=args.kind,
            item=args.item,
            rationale=args.rationale,
        )
    except ValueError as exc:
        print(f"reject: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({"ok": True, "appended": entry}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
