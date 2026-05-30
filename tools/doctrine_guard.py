#!/usr/bin/env python3
"""
doctrine_guard.py — pre-commit guard for mem/doctrine/ immutability.

Doctrine is immutable-versioned (SPEC-SHEET-v0.2 §5):
  - new version = a NEW slug file (e.g., doctrine-foo-v1.md -> doctrine-foo-v2.md)
  - in-place edits to existing doctrine files are FORBIDDEN
  - brand-new doctrine files are ALWAYS allowed
  - deletions are FORBIDDEN (history-loss)

Mechanism:
  We maintain mem/doctrine/.hashes.json mapping each tracked doctrine file
  (path relative to repo root) -> sha256 of its bytes-at-time-of-commit.
  On run, we:
    1. Compute current sha256 for every file under mem/doctrine/ (excluding
       .hashes.json itself and any dotfile).
    2. Compare to the recorded hashes.
    3. EXIT NONZERO with a clear message if any tracked file's hash CHANGED
       (in-place edit) or any tracked file was DELETED.
    4. Print a one-line note for any brand-new files (allowed) and instruct
       the author how to bless the new file into the hashes ledger
       (--bless-new).

Modes:
  python3 tools/doctrine_guard.py            # check; nonzero on violation
  python3 tools/doctrine_guard.py --bless-new
                                             # add hashes for any NEW files
                                             # (does NOT update changed hashes;
                                             # changed = violation)
  python3 tools/doctrine_guard.py --self-test
                                             # run a sandboxed end-to-end
                                             # verification (no repo state
                                             # touched).
  python3 tools/doctrine_guard.py --rebless
                                             # ONE-TIME emergency: rebuild
                                             # hashes.json from current files
                                             # (e.g., after a sanctioned
                                             # doctrine retraction-by-deletion
                                             # has been approved). Loud
                                             # warning, requires --i-know.

Install as a pre-commit hook (DO NOT auto-install — install manually):

    # from repo root:
    cat > .git/hooks/pre-commit <<'HOOK'
    #!/bin/sh
    exec python3 tools/doctrine_guard.py
    HOOK
    chmod +x .git/hooks/pre-commit

Exit codes:
  0  OK (no doctrine changes, or only new files staged)
  1  VIOLATION (in-place edit or deletion of tracked doctrine)
  2  HASHES file malformed / IO error
  3  --self-test failed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple

# -- Configuration -----------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent  # ACG/
DOCTRINE_DIR = REPO_ROOT / "mem" / "doctrine"
HASHES_FILE = DOCTRINE_DIR / ".hashes.json"


# -- Core helpers ------------------------------------------------------------


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def list_tracked_files(doctrine_dir: Path) -> List[Path]:
    """All real doctrine files under doctrine_dir, recursive, excluding:
       - .hashes.json itself
       - dotfiles (.gitkeep, .gitignore, etc.)
       - anything that is not a regular file.
    """
    if not doctrine_dir.is_dir():
        return []
    out: List[Path] = []
    for p in sorted(doctrine_dir.rglob("*")):
        if not p.is_file():
            continue
        if p.name == ".hashes.json":
            continue
        # skip dotfiles AND anything inside a dot-directory under doctrine
        if any(part.startswith(".") for part in p.relative_to(doctrine_dir).parts):
            continue
        out.append(p)
    return out


def load_hashes(hashes_file: Path) -> Dict[str, str]:
    if not hashes_file.is_file():
        return {}
    try:
        with hashes_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(
            f"[doctrine_guard] ERROR: cannot read hashes file {hashes_file}: {e}",
            file=sys.stderr,
        )
        sys.exit(2)
    if not isinstance(data, dict) or "files" not in data:
        print(
            f"[doctrine_guard] ERROR: hashes file {hashes_file} malformed "
            f"(expected JSON object with 'files' key).",
            file=sys.stderr,
        )
        sys.exit(2)
    files = data.get("files", {})
    if not isinstance(files, dict):
        print(
            f"[doctrine_guard] ERROR: hashes file 'files' must be an object.",
            file=sys.stderr,
        )
        sys.exit(2)
    return {str(k): str(v) for k, v in files.items()}


def save_hashes(hashes_file: Path, files: Dict[str, str]) -> None:
    hashes_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_schema": "doctrine-hashes-v1",
        "_note": (
            "sha256 of every tracked file under mem/doctrine/. "
            "Doctrine is immutable-versioned: any change to a tracked hash is "
            "a violation. New files (new slugs) are allowed and must be "
            "blessed in via `python3 tools/doctrine_guard.py --bless-new`."
        ),
        "files": dict(sorted(files.items())),
    }
    # atomic write
    tmp = hashes_file.with_suffix(hashes_file.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=False)
        f.write("\n")
    os.replace(tmp, hashes_file)


def rel_from_repo(p: Path) -> str:
    return str(p.resolve().relative_to(REPO_ROOT))


# -- Check logic -------------------------------------------------------------


def check(
    doctrine_dir: Path | None = None,
    hashes_file: Path | None = None,
) -> Tuple[int, List[str], List[str], List[str]]:
    """Return (exit_code, changed, deleted, new_files).

    Defaults are resolved at call time (NOT at def time) so the self-test
    can hot-swap module globals to a sandbox without leaking onto the real
    repo's doctrine dir.

    exit_code:
      0 = OK (no violations; new files may exist, advisory only)
      1 = VIOLATION (changed or deleted)
    """
    if doctrine_dir is None:
        doctrine_dir = DOCTRINE_DIR
    if hashes_file is None:
        hashes_file = HASHES_FILE
    tracked_hashes = load_hashes(hashes_file)
    current_files = list_tracked_files(doctrine_dir)
    current_rel = {rel_from_repo(p): p for p in current_files}

    changed: List[str] = []
    new_files: List[str] = []
    for rel, p in current_rel.items():
        cur_hash = sha256_of(p)
        if rel in tracked_hashes:
            if tracked_hashes[rel] != cur_hash:
                changed.append(rel)
        else:
            new_files.append(rel)

    deleted = [rel for rel in tracked_hashes if rel not in current_rel]

    if changed or deleted:
        return (1, changed, deleted, new_files)
    return (0, changed, deleted, new_files)


def cmd_check() -> int:
    code, changed, deleted, new_files = check()
    if code != 0:
        print(
            "[doctrine_guard] VIOLATION: doctrine is immutable-versioned.\n"
            "  A new version of a doctrine = a NEW slug file (e.g., -v2.md),\n"
            "  NEVER an in-place edit of an existing one.\n",
            file=sys.stderr,
        )
        if changed:
            print("  In-place edits detected (FORBIDDEN):", file=sys.stderr)
            for r in changed:
                print(f"    - {r}", file=sys.stderr)
            print(
                "  Cure: revert the change, copy to a NEW slug "
                "(e.g., -v2.md), and bless it in via --bless-new.",
                file=sys.stderr,
            )
        if deleted:
            print(
                "\n  Deletions detected (FORBIDDEN — doctrine is history):",
                file=sys.stderr,
            )
            for r in deleted:
                print(f"    - {r}", file=sys.stderr)
            print(
                "  Cure: restore the file. Doctrine retractions are\n"
                "  themselves new doctrine versions, not deletions.",
                file=sys.stderr,
            )
        return 1

    if new_files:
        print("[doctrine_guard] OK. New doctrine file(s) detected (allowed):")
        for r in new_files:
            print(f"  + {r}")
        print(
            "  Bless them into the immutability ledger:\n"
            "    python3 tools/doctrine_guard.py --bless-new"
        )
    else:
        print("[doctrine_guard] OK. No doctrine changes.")
    return 0


def cmd_bless_new() -> int:
    """Add hashes for brand-new files. Refuse if any tracked file changed."""
    code, changed, deleted, new_files = check()
    if code != 0:
        print(
            "[doctrine_guard] REFUSING to --bless-new while violations exist:\n"
            "  changed (in-place-edit) or deleted files must be cured first.",
            file=sys.stderr,
        )
        return 1
    if not new_files:
        print("[doctrine_guard] Nothing new to bless.")
        return 0
    tracked = load_hashes(HASHES_FILE)
    for rel in new_files:
        p = REPO_ROOT / rel
        tracked[rel] = sha256_of(p)
        print(f"[doctrine_guard] blessed: {rel}")
    save_hashes(HASHES_FILE, tracked)
    return 0


def cmd_rebless(args: argparse.Namespace) -> int:
    """Emergency rebuild. Loud-fails without --i-know."""
    if not args.i_know:
        print(
            "[doctrine_guard] REFUSING --rebless without --i-know.\n"
            "  This DESTROYS the immutability ledger. Only use after an\n"
            "  approved doctrine retraction-by-deletion (rare).",
            file=sys.stderr,
        )
        return 1
    tracked: Dict[str, str] = {}
    for p in list_tracked_files(DOCTRINE_DIR):
        rel = rel_from_repo(p)
        tracked[rel] = sha256_of(p)
        print(f"[doctrine_guard] reblessed: {rel}")
    save_hashes(HASHES_FILE, tracked)
    print(
        f"[doctrine_guard] Wrote {len(tracked)} hashes to {HASHES_FILE}."
    )
    return 0


# -- Self-test ---------------------------------------------------------------


def cmd_self_test() -> int:
    """End-to-end sandboxed verification. Touches no real repo state.

    Builds a temp repo-shaped tree:
        <tmp>/mem/doctrine/doctrine-foo-v1.md
        <tmp>/mem/doctrine/.hashes.json   (seeded for foo-v1)
        <tmp>/tools/                       (we run check() against tmp)

    Then exercises:
      A) clean check       -> exit 0
      B) NEW file added    -> exit 0 (allowed)
      C) in-place edit     -> exit 1 (BLOCKED)  <-- the load-bearing case
      D) deletion          -> exit 1 (BLOCKED)
      E) --bless-new path  -> hashes grow; subsequent check is clean

    Returns 0 if all assertions pass, 3 otherwise.
    """
    import textwrap

    print("[doctrine_guard --self-test] starting...")
    tmp = Path(tempfile.mkdtemp(prefix="doctrine_guard_selftest_"))
    try:
        # Build sandbox
        sandbox_doctrine = tmp / "mem" / "doctrine"
        sandbox_doctrine.mkdir(parents=True)
        sandbox_hashes = sandbox_doctrine / ".hashes.json"

        foo_v1 = sandbox_doctrine / "doctrine-foo-v1.md"
        foo_v1.write_text(
            textwrap.dedent(
                """\
                # doctrine-foo v1
                Original sealed content. Do not edit in place.
                """
            )
        )

        # Seed hashes for foo_v1 only (so foo_v1 is "tracked").
        # Use a rel path computed against this sandbox so check() works
        # when we point REPO_ROOT at sandbox tmp.
        rel_foo = "mem/doctrine/doctrine-foo-v1.md"
        save_hashes(
            sandbox_hashes,
            {rel_foo: sha256_of(foo_v1)},
        )

        # Hot-swap module globals to the sandbox
        global REPO_ROOT, DOCTRINE_DIR, HASHES_FILE
        saved = (REPO_ROOT, DOCTRINE_DIR, HASHES_FILE)
        REPO_ROOT = tmp
        DOCTRINE_DIR = sandbox_doctrine
        HASHES_FILE = sandbox_hashes

        failures: List[str] = []

        # A) clean
        code, changed, deleted, new_files = check()
        if not (code == 0 and not changed and not deleted and not new_files):
            failures.append(
                f"A(clean): expected code=0 no diffs; "
                f"got code={code} changed={changed} deleted={deleted} new={new_files}"
            )
        else:
            print("  A) clean check                -> OK (exit 0)")

        # B) NEW file (allowed)
        foo_v2 = sandbox_doctrine / "doctrine-foo-v2.md"
        foo_v2.write_text("# doctrine-foo v2\nA proper new version.\n")
        code, changed, deleted, new_files = check()
        if not (code == 0 and not changed and not deleted and len(new_files) == 1):
            failures.append(
                f"B(new): expected code=0 + 1 new; "
                f"got code={code} changed={changed} new={new_files}"
            )
        else:
            print("  B) new-file (allowed)         -> OK (exit 0)")
        foo_v2.unlink()  # reset for next case

        # C) IN-PLACE EDIT (the load-bearing case — MUST block)
        original_bytes = foo_v1.read_bytes()
        foo_v1.write_text("# doctrine-foo v1\nMUTATED IN PLACE.\n")
        code, changed, deleted, new_files = check()
        if not (code == 1 and rel_foo in changed):
            failures.append(
                f"C(in-place-edit): expected code=1 with {rel_foo} in changed; "
                f"got code={code} changed={changed}"
            )
        else:
            print("  C) in-place edit              -> BLOCKED (exit 1)  ✓ load-bearing")
        foo_v1.write_bytes(original_bytes)  # restore

        # D) DELETION
        foo_v1.unlink()
        code, changed, deleted, new_files = check()
        if not (code == 1 and rel_foo in deleted):
            failures.append(
                f"D(delete): expected code=1 with {rel_foo} in deleted; "
                f"got code={code} deleted={deleted}"
            )
        else:
            print("  D) deletion                   -> BLOCKED (exit 1)")
        foo_v1.write_bytes(original_bytes)  # restore

        # E) --bless-new path
        foo_v2.write_text("# doctrine-foo v2\nAnother new version.\n")
        rc = cmd_bless_new()
        if rc != 0:
            failures.append(f"E(bless-new return): expected 0, got {rc}")
        else:
            # subsequent check should now be clean (foo_v2 tracked)
            code, changed, deleted, new_files = check()
            if not (code == 0 and not changed and not deleted and not new_files):
                failures.append(
                    f"E(post-bless check): expected clean; "
                    f"got code={code} changed={changed} new={new_files}"
                )
            else:
                print("  E) --bless-new then check     -> OK (exit 0)")

        # Restore globals
        REPO_ROOT, DOCTRINE_DIR, HASHES_FILE = saved

        if failures:
            print(
                "\n[doctrine_guard --self-test] FAILED:\n  - "
                + "\n  - ".join(failures),
                file=sys.stderr,
            )
            return 3
        print("\n[doctrine_guard --self-test] ALL PASS (5/5).")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# -- CLI ---------------------------------------------------------------------


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="doctrine_guard",
        description=(
            "Pre-commit guard: blocks in-place edits + deletions under "
            "mem/doctrine/. Doctrine is immutable-versioned."
        ),
    )
    g = ap.add_mutually_exclusive_group()
    g.add_argument(
        "--bless-new",
        action="store_true",
        help="Record hashes for brand-new doctrine files (allowed adds).",
    )
    g.add_argument(
        "--rebless",
        action="store_true",
        help="EMERGENCY: rebuild the whole hashes ledger. Requires --i-know.",
    )
    g.add_argument(
        "--self-test",
        action="store_true",
        help="Sandboxed end-to-end verification. No real repo state touched.",
    )
    ap.add_argument(
        "--i-know",
        action="store_true",
        help="Confirm destructive operations (paired with --rebless).",
    )
    args = ap.parse_args(argv)

    if args.self_test:
        return cmd_self_test()
    if args.bless_new:
        return cmd_bless_new()
    if args.rebless:
        return cmd_rebless(args)
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
