#!/usr/bin/env python3
"""
work_chain_record.py — Post a work-chain record to TGIM /events at each
single-writer collapse. Substrate-INDEPENDENT (no civ identity hardcoded).

Part of the AiCIV-Native Org Phase-1 foundation (PR-1).
See: spec/SPEC-SHEET-v0.2.md §8.

WHAT IT DOES
    At each tier's single-writer collapse point, the runtime calls
        record(task_id, work_chain, output_summary, tier, lead, ...)
    which POSTs:
        {
          event_type:  "task_completed",
          source_civ:  <your-civ-slug>,        # REQUIRED — your civ's slug
          agent_id:    <lead>,                  # the lead-identity reporting collapse
          task_id:     <task_id>,               # caller-side task id
          payload: {
              work_chain:     <list[str] | str>,
              output_summary: <str>,
              tier:           <int>,
          }
        }
    to <TGIM_API>/api/v1/events (default: https://tgim-api.ai-civ.com).

BRING-YOUR-OWN-AGENTAUTH PATTERN (substrate-independence)
    This tool DOES NOT hardcode a seat, a civ-id, a keypair path, or any
    originating-civ identity. The adopter supplies:

        1. A signing seat       — your civ's AgentAUTH seat-id
        2. A civ-id              — your civ's identity slug
        3. A keypair JSON path   — path to YOUR civ's agentauth_keypair.json

    These can be passed as CLI flags, env vars, or kwargs to `record()`.
    Env vars (read in order: CLI flag > env > raise):

        AGENTAUTH_SEAT          your seat-id (free-form string)
        AGENTAUTH_CIV_ID        your civ-id (JWT issuer / sub)
        AGENTAUTH_KEYPAIR_PATH  absolute path to YOUR keypair JSON
        SOURCE_CIV              your civ slug for source_civ in the event
                                (defaults to AGENTAUTH_CIV_ID if unset)
        TGIM_API                TGIM API base URL (default https://tgim-api.ai-civ.com)
        JWT_SIGNER              path to the JWT signer script
                                (default: <this dir>/agentauth_sign_jwt.py)

    The companion signer `tools/agentauth_sign_jwt.py` (shipped in this repo)
    is itself generalized — no defaults for seat / civ / keypair, refuses to
    sign as anyone unless explicitly told who to sign as.

PROGRAMMATIC API
    from tools.work_chain_record import record
    result = record(
        task_id="tsk_mycivac_assemble_001",
        work_chain=["coding-pm", "infra-lead", "auditor-lead"],
        output_summary="3-tier assemble OK; 4 forks → 1 collapse → return.",
        tier=2,
        lead="coding-pm",
        seat="my-civ-signer",            # YOUR seat
        civ_id="mycivac",                # YOUR civ-id
        keypair_path="/path/to/your/agentauth_keypair.json",
        source_civ="mycivac",            # YOUR civ slug (often == civ_id)
    )

CLI
    python3 tools/work_chain_record.py \\
        --task-id tsk_mycivac_foo_001 \\
        --lead coding-pm \\
        --tier 2 \\
        --work-chain "coding-pm,infra-lead,auditor-lead" \\
        --output-summary "Collapse OK; firewall held." \\
        --seat my-civ-signer \\
        --civ-id mycivac \\
        --keypair /path/to/your/agentauth_keypair.json \\
        --source-civ mycivac

SELF-TEST
    python3 tools/work_chain_record.py --self-test
    Requires AGENTAUTH_SEAT + AGENTAUTH_CIV_ID + AGENTAUTH_KEYPAIR_PATH in env
    (or pass via flags). Posts a real test record and confirms HTTP 201.

EXIT CODES
    0  success (HTTP 201)
    1  usage / argument error (missing required identity, bad args)
    2  JWT signing failed (signer subprocess error)
    3  TGIM API unreachable (network)
    4  TGIM API returned non-201 (HTTP error)
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable, Optional, Union

# ─── Paths + constants (no civ identity hardcoded) ─────────────────────────

THIS_DIR = Path(__file__).resolve().parent
DEFAULT_JWT_SIGNER = THIS_DIR / "agentauth_sign_jwt.py"
DEFAULT_TGIM_API = "https://tgim-api.ai-civ.com"
DEFAULT_JWT_TTL = 1200


def _events_endpoint(tgim_api: str) -> str:
    return f"{tgim_api.rstrip('/')}/api/v1/events"


# ─── JWT signing (adopter brings their own identity) ───────────────────────

def _sign_jwt(
    seat: str,
    civ_id: str,
    keypair_path: str,
    ttl: int = DEFAULT_JWT_TTL,
    jwt_signer: Optional[str] = None,
) -> str:
    """
    Invoke the JWT signer script with the ADOPTER's identity. Returns the JWT string.

    Args:
        seat:         the adopter's seat-id (any string the adopter's civ uses).
        civ_id:       the adopter's civ-id (issuer/sub in the JWT).
        keypair_path: absolute path to the adopter's agentauth_keypair.json.
        ttl:          JWT TTL in seconds.
        jwt_signer:   optional override of the signer script path.
                      Defaults to <this dir>/agentauth_sign_jwt.py.

    Raises:
        ValueError:   if any of seat / civ_id / keypair_path is missing.
        RuntimeError: if signer exits non-zero or returns malformed JWT.
    """
    if not seat:
        raise ValueError("seat is required (no default — bring your own identity)")
    if not civ_id:
        raise ValueError("civ_id is required (no default — bring your own identity)")
    if not keypair_path:
        raise ValueError("keypair_path is required (no default — bring your own identity)")

    signer = Path(jwt_signer or os.environ.get("JWT_SIGNER") or DEFAULT_JWT_SIGNER)
    if not signer.exists():
        raise RuntimeError(f"JWT signer script not found: {signer}")

    cmd = [
        sys.executable,
        str(signer),
        "--seat", seat,
        "--civ-id", civ_id,
        "--keypair", keypair_path,
        "--ttl", str(ttl),
        "--print-jwt-only",
    ]
    # NOTE: cwd is no longer hardcoded. The signer is path-resolved by flag,
    # not by walking from a specific civ-root — so cwd doesn't matter for
    # keypair resolution.
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"JWT sign failed (rc={result.returncode}): {result.stderr[:300]}"
        )
    jwt = result.stdout.strip().split("\n")[-1].strip()
    if not jwt or len(jwt) < 100 or jwt.count(".") != 2:
        raise RuntimeError(f"JWT looks malformed (len={len(jwt)})")
    return jwt


# ─── Payload builder ───────────────────────────────────────────────────────

def _build_event(
    task_id: str,
    work_chain: Union[str, Iterable[str]],
    output_summary: str,
    tier: int,
    lead: str,
    source_civ: str,
    extra_payload: Optional[dict] = None,
) -> dict:
    """Build the canonical TGIM event body for a work-chain collapse."""
    if isinstance(work_chain, str):
        wc = work_chain
    else:
        wc = list(work_chain)

    payload = {
        "work_chain": wc,
        "output_summary": output_summary,
        "tier": int(tier),
    }
    if extra_payload:
        for k, v in extra_payload.items():
            if k not in payload:
                payload[k] = v

    return {
        "event_type": "task_completed",
        "source_civ": source_civ,
        "agent_id": lead,
        "task_id": task_id,
        "payload": payload,
    }


# ─── HTTP post ──────────────────────────────────────────────────────────────

def _post_event(jwt: str, event: dict, tgim_api: str, timeout: int = 30) -> tuple[int, str]:
    """POST event to /api/v1/events. Returns (http_status, body_text). 0 = network error."""
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        _events_endpoint(tgim_api),
        data=body,
        headers={
            "Authorization": f"Bearer {jwt}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        return e.code, err_body
    except urllib.error.URLError as e:
        return 0, f"network: {e}"


# ─── Public API ────────────────────────────────────────────────────────────

def record(
    task_id: str,
    work_chain: Union[str, Iterable[str]],
    output_summary: str,
    tier: int,
    lead: str,
    *,
    seat: Optional[str] = None,
    civ_id: Optional[str] = None,
    keypair_path: Optional[str] = None,
    source_civ: Optional[str] = None,
    tgim_api: Optional[str] = None,
    jwt_signer: Optional[str] = None,
    ttl: int = DEFAULT_JWT_TTL,
    extra_payload: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """
    Post a work-chain collapse record to TGIM /events.

    Identity resolution (bring your own AgentAUTH):
        Each of seat / civ_id / keypair_path falls back to an env var if not
        passed as a kwarg:
            seat         ←→ AGENTAUTH_SEAT
            civ_id       ←→ AGENTAUTH_CIV_ID
            keypair_path ←→ AGENTAUTH_KEYPAIR_PATH
            source_civ   ←→ SOURCE_CIV (defaults to civ_id if neither set)
            tgim_api     ←→ TGIM_API   (defaults to https://tgim-api.ai-civ.com)

        If ANY of seat / civ_id / keypair_path is unresolved → ValueError.
        This tool refuses to sign with a hardcoded identity.

    Args:
        task_id:        Caller-side task identifier (REQUIRED, payload-shape rule).
        work_chain:     Chain of upstream leads/task_ids — str OR iterable of str.
        output_summary: Firewall-compressed summary of the collapsed work.
        tier:           Org-tier of the reporting lead (0=Primary, 1=COO/VP, 2=specialist...).
        lead:           agent_id — the lead-identity reporting collapse.
        seat:           AgentAuth seat-id (or AGENTAUTH_SEAT env).
        civ_id:         JWT issuer/sub civ-id (or AGENTAUTH_CIV_ID env).
        keypair_path:   Absolute path to YOUR civ's agentauth_keypair.json
                        (or AGENTAUTH_KEYPAIR_PATH env).
        source_civ:     Civ slug for source_civ in the event (or SOURCE_CIV env;
                        defaults to civ_id).
        tgim_api:       TGIM API base URL (or TGIM_API env;
                        defaults to https://tgim-api.ai-civ.com).
        jwt_signer:     Path to the JWT signer script
                        (or JWT_SIGNER env; defaults to <this dir>/agentauth_sign_jwt.py).
        ttl:            JWT TTL seconds (default 1200).
        extra_payload:  Optional dict merged into payload.
        timeout:        HTTP timeout in seconds.

    Returns:
        dict {ok, status, task_id, body, event}

    Raises:
        ValueError:   for bad/missing arguments or unresolved identity.
        RuntimeError: if JWT signing fails (signer subprocess error).
    """
    if not task_id or not isinstance(task_id, str):
        raise ValueError("task_id must be a non-empty string")
    if not lead or not isinstance(lead, str):
        raise ValueError("lead must be a non-empty string")
    if output_summary is None:
        raise ValueError("output_summary is required (may be empty string)")
    if not isinstance(tier, int):
        try:
            tier = int(tier)
        except (TypeError, ValueError):
            raise ValueError(f"tier must be int-coercible, got {tier!r}")
    if work_chain is None:
        raise ValueError("work_chain is required (str or iterable of str)")

    # Identity resolution: kwarg > env > raise (NO defaults; no fallback to any
    # originating-civ identity).
    seat = seat or os.environ.get("AGENTAUTH_SEAT")
    civ_id = civ_id or os.environ.get("AGENTAUTH_CIV_ID")
    keypair_path = keypair_path or os.environ.get("AGENTAUTH_KEYPAIR_PATH")
    source_civ = source_civ or os.environ.get("SOURCE_CIV") or civ_id
    tgim_api = tgim_api or os.environ.get("TGIM_API") or DEFAULT_TGIM_API

    missing = []
    if not seat: missing.append("seat (or AGENTAUTH_SEAT)")
    if not civ_id: missing.append("civ_id (or AGENTAUTH_CIV_ID)")
    if not keypair_path: missing.append("keypair_path (or AGENTAUTH_KEYPAIR_PATH)")
    if missing:
        raise ValueError(
            "missing AgentAUTH identity — bring your own: "
            + ", ".join(missing)
            + ". This tool intentionally ships NO default civ identity."
        )

    event = _build_event(
        task_id=task_id,
        work_chain=work_chain,
        output_summary=output_summary,
        tier=tier,
        lead=lead,
        source_civ=source_civ,
        extra_payload=extra_payload,
    )

    jwt = _sign_jwt(
        seat=seat,
        civ_id=civ_id,
        keypair_path=keypair_path,
        ttl=ttl,
        jwt_signer=jwt_signer,
    )
    status, body = _post_event(jwt, event, tgim_api=tgim_api, timeout=timeout)

    return {
        "ok": status == 201,
        "status": status,
        "task_id": task_id,
        "body": body[:500],
        "event": event,
    }


# ─── Self-test ──────────────────────────────────────────────────────────────

def _self_test() -> int:
    """
    Post a real work-chain record to TGIM and confirm HTTP 201.

    Requires the adopter's AgentAUTH identity in env (or via CLI flags):
        AGENTAUTH_SEAT, AGENTAUTH_CIV_ID, AGENTAUTH_KEYPAIR_PATH

    Per SPEC §15 (substrate-honest): no mocks. Real write to the real /events
    endpoint, real readback expectation. Exits 0 only if HTTP 201 actually
    came back from TGIM.
    """
    print("[work_chain_record.py --self-test]")
    tgim_api = os.environ.get("TGIM_API") or DEFAULT_TGIM_API
    print(f"  endpoint: {_events_endpoint(tgim_api)}")

    seat = os.environ.get("AGENTAUTH_SEAT")
    civ_id = os.environ.get("AGENTAUTH_CIV_ID")
    keypair_path = os.environ.get("AGENTAUTH_KEYPAIR_PATH")
    if not (seat and civ_id and keypair_path):
        print(
            "  FAIL: self-test requires AGENTAUTH_SEAT + AGENTAUTH_CIV_ID + "
            "AGENTAUTH_KEYPAIR_PATH in env (this tool has NO default identity).",
            file=sys.stderr,
        )
        return 1

    print(f"  seat={seat} civ_id={civ_id} keypair={keypair_path}")

    ts = int(time.time())
    task_id = f"tsk_nativeorg_workchain_selftest_{ts}"

    try:
        result = record(
            task_id=task_id,
            work_chain=["work-chain-record-selftest", "tier-1-coo", "tier-2-specialist"],
            output_summary=(
                "Self-test: work_chain_record.py validates write path to TGIM /events. "
                "Posted from --self-test invocation; payload carries work_chain + "
                "output_summary + tier per SPEC §8 work-chain wiring contract."
            ),
            tier=2,
            lead="work-chain-record-selftest",
            extra_payload={
                "self_test": True,
                "spec_anchor": "spec/SPEC-SHEET-v0.2.md#8",
            },
        )
    except (RuntimeError, ValueError) as e:
        print(f"  FAIL: pre-flight error: {e}", file=sys.stderr)
        return 2

    print(f"  task_id: {result['task_id']}")
    print(f"  status:  HTTP {result['status']}")
    print(f"  body:    {result['body'][:300]}")

    if result["ok"]:
        print("  PASS: HTTP 201 — work-chain record landed on TGIM /events.")
        return 0
    elif result["status"] == 0:
        print("  FAIL: network error reaching TGIM.", file=sys.stderr)
        return 3
    else:
        print(f"  FAIL: TGIM returned HTTP {result['status']} (expected 201).", file=sys.stderr)
        return 4


# ─── CLI ───────────────────────────────────────────────────────────────────

def _cli() -> int:
    p = argparse.ArgumentParser(
        description="Post a work-chain collapse record to TGIM /events "
                    "(substrate-independent — adopter brings AgentAUTH identity)."
    )
    p.add_argument("--self-test", action="store_true",
                   help="Post a real test record and confirm HTTP 201, then exit. "
                        "Requires AGENTAUTH_SEAT + AGENTAUTH_CIV_ID + AGENTAUTH_KEYPAIR_PATH in env.")
    p.add_argument("--task-id", help="Caller-side task_id (REQUIRED unless --self-test).")
    p.add_argument("--lead", help="agent_id — the reporting lead-identity (REQUIRED unless --self-test).")
    p.add_argument("--tier", type=int, help="Org-tier (int) of the reporting lead.")
    p.add_argument("--work-chain", help="Comma-separated chain of upstream leads/task_ids.")
    p.add_argument("--output-summary", help="Firewall-compressed summary of collapsed work.")

    # Adopter identity (flag wins over env; no defaults).
    p.add_argument("--seat", help="AgentAuth seat-id for JWT (or AGENTAUTH_SEAT env). REQUIRED.")
    p.add_argument("--civ-id", help="JWT issuer/sub civ-id (or AGENTAUTH_CIV_ID env). REQUIRED.")
    p.add_argument("--keypair", dest="keypair_path",
                   help="Absolute path to YOUR agentauth_keypair.json (or AGENTAUTH_KEYPAIR_PATH env). REQUIRED.")
    p.add_argument("--source-civ",
                   help="source_civ slug in the event (or SOURCE_CIV env; defaults to --civ-id).")
    p.add_argument("--tgim-api",
                   help=f"TGIM API base URL (or TGIM_API env; default {DEFAULT_TGIM_API}).")
    p.add_argument("--jwt-signer",
                   help="Path to JWT signer (or JWT_SIGNER env; default <this dir>/agentauth_sign_jwt.py).")
    p.add_argument("--ttl", type=int, default=DEFAULT_JWT_TTL, help=f"JWT TTL seconds (default {DEFAULT_JWT_TTL})")
    p.add_argument("--parent-task-id", help="Optional parent_task_id for chain enrichment.")
    args = p.parse_args()

    if args.self_test:
        return _self_test()

    missing = [name for name, val in [
        ("--task-id", args.task_id),
        ("--lead", args.lead),
        ("--tier", args.tier),
        ("--work-chain", args.work_chain),
        ("--output-summary", args.output_summary),
    ] if val is None]
    if missing:
        p.error(f"missing required args: {', '.join(missing)} (or use --self-test)")

    work_chain = [s.strip() for s in args.work_chain.split(",") if s.strip()]
    extra = {"parent_task_id": args.parent_task_id} if args.parent_task_id else None

    try:
        result = record(
            task_id=args.task_id,
            work_chain=work_chain,
            output_summary=args.output_summary,
            tier=args.tier,
            lead=args.lead,
            seat=args.seat,
            civ_id=args.civ_id,
            keypair_path=args.keypair_path,
            source_civ=args.source_civ,
            tgim_api=args.tgim_api,
            jwt_signer=args.jwt_signer,
            ttl=args.ttl,
            extra_payload=extra,
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if result["ok"]:
        print(f"OK: work-chain record filed task_id={result['task_id']}")
        print(result["body"][:300])
        return 0
    elif result["status"] == 0:
        print(f"FAIL: network error: {result['body']}", file=sys.stderr)
        return 3
    else:
        print(f"FAIL: HTTP {result['status']}", file=sys.stderr)
        print(result["body"][:500], file=sys.stderr)
        return 4


if __name__ == "__main__":
    sys.exit(_cli())
