#!/usr/bin/env python3
"""
work_chain_record.py — Post a work-chain record to TGIM /events at each
single-writer collapse.

Part of the AiCIV-Native Org Phase-1 foundation (PR-1).
See: projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md §8.

WHAT IT DOES
    At each tier's single-writer collapse point, the runtime calls
        record(task_id, work_chain, output_summary, tier, lead)
    which POSTs:
        {
          event_type:  "task_completed",
          source_civ:  "acgee",
          agent_id:    <lead>,           # the lead-identity reporting collapse
          task_id:     <task_id>,
          payload: {
              work_chain:     <list[str] | str>,   # chain of upstream task_ids / leads
              output_summary: <str>,               # firewall-compressed summary
              tier:           <int>,               # org-tier of the reporting lead
          }
        }
    to https://tgim-api.ai-civ.com/api/v1/events.

    JWT is signed via tools/agentauth_sign_jwt.py --seat hermes-primary.
    Per SPEC §8 + tgim-loop-discipline SKILL: CWD MUST = ACG root for the
    signer's per-seat keypair lookup to resolve.

WHY
    The work-chain stream is "leg b" of the 3-leg structural-independence
    cure (SPEC §7): every collapse is externally readable on TGIM, so an
    outside party (sister civ, Hermes node) can audit chain-of-custody
    without needing internal access. Write+readback proven in P14.

PROGRAMMATIC API
    from tools.work_chain_record import record
    result = record(
        task_id="tsk_acg_nativeorg_assemble_001",
        work_chain=["coding-pm", "infra-lead", "auditor-lead"],
        output_summary="3-tier assemble OK; 4 forks → 1 collapse → return.",
        tier=2,
        lead="coding-pm",
    )
    # result: {"ok": bool, "status": int, "task_id": str, "body": str}

CLI
    python3 tools/work_chain_record.py \\
        --task-id tsk_acg_foo_001 \\
        --lead coding-pm \\
        --tier 2 \\
        --work-chain "coding-pm,infra-lead,auditor-lead" \\
        --output-summary "Collapse OK; firewall held."

SELF-TEST
    python3 tools/work_chain_record.py --self-test
    Posts a real test record and confirms HTTP 201.

EXIT CODES
    0  success (HTTP 201)
    1  usage / argument error
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

# ─── Paths + constants ─────────────────────────────────────────────────────

ACG_ROOT = Path("/home/corey/projects/AI-CIV/ACG")
AGENTAUTH_SIGN = ACG_ROOT / "tools" / "agentauth_sign_jwt.py"
TGIM_API = "https://tgim-api.ai-civ.com"
EVENTS_ENDPOINT = f"{TGIM_API}/api/v1/events"
DEFAULT_SEAT = "hermes-primary"   # per SPEC §8: one civ keypair proves the civ
DEFAULT_SOURCE_CIV = "acgee"
DEFAULT_JWT_TTL = 1200


# ─── JWT signing (cwd-relative per SPEC §8 + tgim-loop-discipline) ─────────

def _sign_jwt(seat: str = DEFAULT_SEAT, ttl: int = DEFAULT_JWT_TTL) -> str:
    """
    Invoke tools/agentauth_sign_jwt.py with cwd=ACG_ROOT (REQUIRED — the signer
    resolves per-seat keypairs by walking from cwd). Returns the JWT string.

    Raises:
        RuntimeError: if signer exits non-zero or returns malformed JWT.
    """
    cmd = [
        sys.executable,
        str(AGENTAUTH_SIGN),
        "--seat", seat,
        "--ttl", str(ttl),
        "--print-jwt-only",
    ]
    result = subprocess.run(
        cmd,
        cwd=str(ACG_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"JWT sign failed (rc={result.returncode}): {result.stderr[:300]}"
        )
    # --print-jwt-only emits the JWT as the last line of stdout
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
    source_civ: str = DEFAULT_SOURCE_CIV,
    extra_payload: Optional[dict] = None,
) -> dict:
    """Build the canonical TGIM event body for a work-chain collapse."""
    # Normalize work_chain to a list (callers may pass str or iterable)
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
        # Caller-provided enrichment (e.g. parent_task_id, doctrine_anchor).
        # Does not override the three load-bearing keys above.
        for k, v in extra_payload.items():
            if k not in payload:
                payload[k] = v

    event = {
        "event_type": "task_completed",
        "source_civ": source_civ,
        "agent_id": lead,            # the reporting lead-identity
        "task_id": task_id,
        "payload": payload,
    }
    return event


# ─── HTTP post ──────────────────────────────────────────────────────────────

def _post_event(jwt: str, event: dict, timeout: int = 30) -> tuple[int, str]:
    """POST event to /api/v1/events. Returns (http_status, body_text).

    http_status == 0 indicates a network-layer failure (no HTTP response).
    """
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        EVENTS_ENDPOINT,
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
    source_civ: str = DEFAULT_SOURCE_CIV,
    seat: str = DEFAULT_SEAT,
    ttl: int = DEFAULT_JWT_TTL,
    extra_payload: Optional[dict] = None,
    timeout: int = 30,
) -> dict:
    """
    Post a work-chain collapse record to TGIM /events.

    Args:
        task_id:        Caller-side task identifier (REQUIRED, payload-shape rule).
        work_chain:     Chain of upstream leads/task_ids — str OR iterable of str.
        output_summary: Firewall-compressed summary of the collapsed work.
        tier:           Org-tier of the reporting lead (0=Primary, 1=COO/VP, 2=specialist...).
        lead:           agent_id — the lead-identity reporting collapse.
        source_civ:     Civ slug (default "acgee").
        seat:           AgentAuth seat for JWT signing (default "hermes-primary").
        ttl:            JWT TTL seconds (default 1200).
        extra_payload:  Optional dict merged into payload (e.g. parent_task_id).
        timeout:        HTTP timeout in seconds.

    Returns:
        dict {
            "ok":      bool,
            "status":  int,    # HTTP status (0 = network error)
            "task_id": str,    # the task_id submitted
            "body":    str,    # response body (truncated)
            "event":   dict,   # the event submitted (for caller logging)
        }

    Raises:
        ValueError:   for bad/missing arguments.
        RuntimeError: if JWT signing fails (signer subprocess error).
    """
    # Argument validation — fail loud, not silent.
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

    event = _build_event(
        task_id=task_id,
        work_chain=work_chain,
        output_summary=output_summary,
        tier=tier,
        lead=lead,
        source_civ=source_civ,
        extra_payload=extra_payload,
    )

    jwt = _sign_jwt(seat=seat, ttl=ttl)
    status, body = _post_event(jwt, event, timeout=timeout)

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

    Per SPEC §15 (substrate-honest): no mocks. Real write to the real /events
    endpoint, real readback expectation. Exits 0 only if HTTP 201 actually
    came back from TGIM.
    """
    print("[work_chain_record.py --self-test]")
    print(f"  endpoint:  {EVENTS_ENDPOINT}")
    print(f"  seat:      {DEFAULT_SEAT}")
    print(f"  cwd-check: {os.getcwd()} (should == {ACG_ROOT} for signer)")

    if Path(os.getcwd()).resolve() != ACG_ROOT.resolve():
        print(f"  WARN: cwd != ACG_ROOT — signer is invoked with cwd={ACG_ROOT} "
              f"explicitly, so this should still work, but note the SPEC §8 rule.")

    ts = int(time.time())
    task_id = f"tsk_acg_nativeorg_workchain_selftest_{ts}"

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
                "spec_anchor": "projects/aiciv-native-org/spec/SPEC-SHEET-v0.2.md#8",
            },
        )
    except (RuntimeError, ValueError) as e:
        print(f"  FAIL: pre-flight error: {e}", file=sys.stderr)
        return 2

    print(f"  task_id:   {result['task_id']}")
    print(f"  status:    HTTP {result['status']}")
    print(f"  body:      {result['body'][:300]}")

    if result["ok"]:
        print("  PASS: HTTP 201 — work-chain record landed on TGIM /events.")
        return 0
    elif result["status"] == 0:
        print("  FAIL: network error reaching TGIM.", file=sys.stderr)
        return 3
    else:
        print(f"  FAIL: TGIM returned HTTP {result['status']} (expected 201).",
              file=sys.stderr)
        return 4


# ─── CLI ───────────────────────────────────────────────────────────────────

def _cli() -> int:
    p = argparse.ArgumentParser(
        description="Post a work-chain collapse record to TGIM /events "
                    "(AiCIV-Native Org PR-1, SPEC §8)."
    )
    p.add_argument("--self-test", action="store_true",
                   help="Post a real test record and confirm HTTP 201, then exit.")
    p.add_argument("--task-id", help="Caller-side task_id (REQUIRED unless --self-test).")
    p.add_argument("--lead", help="agent_id — the reporting lead-identity (REQUIRED unless --self-test).")
    p.add_argument("--tier", type=int, help="Org-tier (int) of the reporting lead.")
    p.add_argument("--work-chain", help="Comma-separated chain of upstream leads/task_ids.")
    p.add_argument("--output-summary", help="Firewall-compressed summary of collapsed work.")
    p.add_argument("--source-civ", default=DEFAULT_SOURCE_CIV, help=f"source_civ (default {DEFAULT_SOURCE_CIV})")
    p.add_argument("--seat", default=DEFAULT_SEAT, help=f"AgentAuth seat for JWT (default {DEFAULT_SEAT})")
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
            source_civ=args.source_civ,
            seat=args.seat,
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
