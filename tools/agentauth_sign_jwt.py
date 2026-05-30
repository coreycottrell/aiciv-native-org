#!/usr/bin/env python3
"""
agentauth_sign_jwt.py — Sign a JWT using AgentAUTH Ed25519 keypair, generalized
for any civ (no hardcoded seat / civ identity / keypair path).

Usage
-----
    # Print a JWT only (default — what work_chain_record.py uses):
    python3 agentauth_sign_jwt.py \\
        --seat <your-seat-id> \\
        --civ-id <your-civ-id> \\
        --keypair <path-to-your-agentauth_keypair.json> \\
        --claim tgim-write \\
        --ttl 1200 \\
        --print-jwt-only

    # Issue a claim (full path):
    python3 agentauth_sign_jwt.py \\
        --seat <your-seat-id> \\
        --civ-id <your-civ-id> \\
        --keypair <path-to-your-agentauth_keypair.json> \\
        --claim tgim-write \\
        --ttl 3600

Configuration sources (in priority order)
-----------------------------------------
Every required identity field can be set via flag OR env var. Env var names
are documented next to each field. Flag wins over env. Defaults are NONE —
this tool refuses to sign with a hardcoded identity (substrate-independence
discipline).

    --seat       /  AGENTAUTH_SEAT          : your seat-id (any string your civ uses)
    --civ-id     /  AGENTAUTH_CIV_ID        : your civ-id (issuer/sub in the JWT)
    --keypair    /  AGENTAUTH_KEYPAIR_PATH  : abs path to your keypair JSON
    --aud        /  AGENTAUTH_AUDIENCE      : JWT audience (defaults below)
    --agentauth-url /  AGENTAUTH_URL        : AgentAUTH server URL for /claims/issue (optional)

Keypair file shape
------------------
Either of these JSON shapes is accepted (matches the AgentAUTH provisioning
convention):

    { "private_key": "<base64 or base64url 32-byte Ed25519 seed>",
      "civ_id":      "<your-civ-id>" }

If the file's `civ_id` differs from --civ-id, the flag wins (the file's
civ_id is used only as a fallback when --civ-id / AGENTAUTH_CIV_ID are
both absent).

Adopter-discipline (substrate-independence)
-------------------------------------------
This tool ships ZERO defaults for seat / civ-id / keypair path. The
adopter civ supplies its own identity. There is NO fallback to any
originating-civ identity. If you forget all three, the tool exits 1
with a helpful error — never silently signs as anyone.

Requires
--------
    pip install httpx cryptography
    (base58 is optional — only needed for one rare keypair encoding)
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
except ImportError:
    print("ERROR: cryptography not installed. Run: pip install cryptography", file=sys.stderr)
    sys.exit(1)


# ─── Defaults (NONE for identity — substrate-independence) ────────────────────

DEFAULT_AGENTAUTH_URL = os.environ.get("AGENTAUTH_URL", "")  # adopter sets this if using /claims/issue


# ─── Ed25519 helpers ───────────────────────────────────────────────────────────

def b64url_encode(data: bytes) -> str:
    """URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64_decode_loose(data: str) -> bytes:
    """Decode base64 with auto-padding; accept either standard or URL-safe."""
    pad = (4 - len(data) % 4) % 4
    try:
        return base64.b64decode(data + "=" * pad)
    except Exception:
        return base64.urlsafe_b64decode(data + "=" * pad)


def load_keypair(keypair_path: Path) -> tuple[str, str | None]:
    """
    Load a keypair JSON file. Returns (private_key_b64, civ_id_or_None).

    Raises:
        FileNotFoundError: if the path does not exist.
        ValueError:        if the file is not valid JSON or lacks `private_key`.
    """
    if not keypair_path.exists():
        raise FileNotFoundError(f"Keypair not found: {keypair_path}")

    try:
        with open(keypair_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Keypair file is not valid JSON: {e}")

    if "private_key" not in data:
        raise ValueError(f"Keypair file missing required field 'private_key': {keypair_path}")

    return data["private_key"], data.get("civ_id")


def sign_jwt_ed25519(
    private_key_b64: str,
    civ_id: str,
    audience: str,
    ttl_seconds: int,
    scope: str = "",
    kid: str | None = None,
) -> str:
    """
    Create and sign a JWT using Ed25519 (EdDSA algorithm).

    JWT (JWS compact serialization):
        header  : {"alg": "EdDSA", "typ": "JWT", "kid": <kid or civ_id>}
        payload : {iss, sub, civ_id, aud, iat, exp, actor_type, [scope, claims]}

    Args:
        private_key_b64: base64 / base64url-encoded 32-byte Ed25519 seed.
        civ_id:          the civ identity used in iss / sub / civ_id claims.
        audience:        the JWT `aud` claim (verifier-specific).
        ttl_seconds:     JWT lifetime in seconds.
        scope:           optional scope; also written to `claims: [scope]`.
        kid:             optional override for JWT header `kid`. Defaults to civ_id.

    Returns:
        the compact-serialized JWT string.
    """
    now = int(time.time())

    header = {"alg": "EdDSA", "typ": "JWT", "kid": kid or civ_id}
    header_b64 = b64url_encode(json.dumps(header, separators=(",", ":")).encode())

    payload = {
        "iss": civ_id,
        "sub": civ_id,
        "civ_id": civ_id,
        "aud": audience,
        "iat": now,
        "exp": now + ttl_seconds,
        "actor_type": "aiciv",
    }
    if scope:
        payload["scope"] = scope
        payload["claims"] = [scope]

    payload_b64 = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())

    signing_input = f"{header_b64}.{payload_b64}"

    # Decode key (standard or URL-safe base64; expect 32-byte Ed25519 seed).
    key_bytes = b64_decode_loose(private_key_b64)

    if len(key_bytes) == 44:
        # Some provisioning paths store as base58 — try decoding (optional dep).
        try:
            import base58
            key_bytes = base58.b58decode(key_bytes)
        except Exception:
            # Fall through; the from_private_bytes call below will try [:32].
            pass

    try:
        priv_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
    except Exception:
        # Tolerant fallback for keys stored with extra trailing bytes.
        priv_key = Ed25519PrivateKey.from_private_bytes(key_bytes[:32])

    signature = priv_key.sign(signing_input.encode("utf-8"))
    signature_b64 = b64url_encode(signature)

    return f"{signing_input}.{signature_b64}"


def issue_claim(jwt: str, agentauth_url: str, civ_id: str, claim: str, ttl_seconds: int = 3600) -> dict:
    """POST to <agentauth_url>/claims/issue with the signed JWT."""
    if not agentauth_url:
        return {"ok": False, "error": "AGENTAUTH_URL not set (use --agentauth-url or env var)"}

    expires_at = datetime.fromtimestamp(
        time.time() + ttl_seconds, tz=timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {"civ_id": civ_id, "claim": claim, "expires_at": expires_at}
    headers = {"Authorization": f"Bearer {jwt}", "Content-Type": "application/json"}

    with httpx.Client(timeout=15) as client:
        r = client.post(f"{agentauth_url}/claims/issue", json=payload, headers=headers)

    if r.status_code == 201:
        return {"ok": True, "claim": r.json()}
    elif r.status_code == 403:
        return {"ok": False, "error": "Not authorized to issue this claim", "detail": r.text}
    else:
        return {"ok": False, "error": f"HTTP {r.status_code}", "detail": r.text}


# ─── Main ─────────────────────────────────────────────────────────────────────

def _resolve_or_die(arg_value: str | None, env_name: str, label: str) -> str:
    """Flag-wins-over-env resolution. Exits 1 with a clear error if both are missing."""
    val = arg_value or os.environ.get(env_name)
    if not val:
        print(
            f"ERROR: missing {label} — pass --{label.replace('_', '-')} or set ${env_name}.\n"
            f"This tool intentionally ships NO default identity (substrate-independence).",
            file=sys.stderr,
        )
        sys.exit(1)
    return val


def main():
    parser = argparse.ArgumentParser(
        description="Sign JWT via AgentAUTH Ed25519 keypair (generalized — adopter brings identity)."
    )
    parser.add_argument("--seat", help="Your seat identifier (or set AGENTAUTH_SEAT). Free-form string.")
    parser.add_argument("--civ-id", help="Your civ identity for JWT iss/sub/civ_id (or set AGENTAUTH_CIV_ID).")
    parser.add_argument("--keypair", help="Absolute path to YOUR agentauth_keypair.json (or set AGENTAUTH_KEYPAIR_PATH).")
    parser.add_argument("--claim", default="tgim-write",
                        help="Claim to issue / scope to embed (default: tgim-write).")
    parser.add_argument("--ttl", type=int, default=3600, help="TTL in seconds (default: 3600).")
    parser.add_argument("--scope", default="",
                        help="JWT scope claim. Defaults to --claim value.")
    parser.add_argument("--aud", "--audience", dest="audience",
                        help="Override JWT aud claim. Default: tgim-read/tgim-write → https://tgim-api.ai-civ.com ; "
                             "other claims → AGENTAUTH_URL. Set AGENTAUTH_AUDIENCE to override globally.")
    parser.add_argument("--agentauth-url",
                        help="AgentAUTH server URL (or set AGENTAUTH_URL). Only required when ISSUING a claim "
                             "(not when --print-jwt-only).")
    parser.add_argument("--print-jwt-only", action="store_true",
                        help="Only print the JWT, do not issue a claim. (work_chain_record.py uses this.)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify JWT against AgentAUTH /verify-token endpoint.")

    args = parser.parse_args()

    # Resolve identity (flag > env). Refuse to sign without explicit identity.
    seat = _resolve_or_die(args.seat, "AGENTAUTH_SEAT", "seat")
    civ_id_flag = args.civ_id or os.environ.get("AGENTAUTH_CIV_ID")  # may fall back to keypair file
    keypair_path_str = _resolve_or_die(args.keypair, "AGENTAUTH_KEYPAIR_PATH", "keypair")
    keypair_path = Path(keypair_path_str)

    agentauth_url = args.agentauth_url or os.environ.get("AGENTAUTH_URL", DEFAULT_AGENTAUTH_URL)

    # Audience resolution: explicit flag > env > smart default by claim.
    audience_flag = args.audience or os.environ.get("AGENTAUTH_AUDIENCE")
    if audience_flag:
        jwt_audience = audience_flag
    elif args.claim in ("tgim-read", "tgim-write"):
        jwt_audience = "https://tgim-api.ai-civ.com"
    elif agentauth_url:
        jwt_audience = agentauth_url
    else:
        print(
            "ERROR: cannot resolve JWT audience.\n"
            "Pass --aud, set AGENTAUTH_AUDIENCE, or set AGENTAUTH_URL (used as default aud for non-tgim claims).",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.scope:
        args.scope = args.claim

    # Load keypair; let file civ_id be fallback only.
    try:
        private_key, file_civ_id = load_keypair(keypair_path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    civ_id = civ_id_flag or file_civ_id
    if not civ_id:
        print(
            "ERROR: civ_id missing — pass --civ-id, set AGENTAUTH_CIV_ID, or include 'civ_id' in your keypair file.",
            file=sys.stderr,
        )
        sys.exit(1)

    jwt = sign_jwt_ed25519(
        private_key_b64=private_key,
        civ_id=civ_id,
        audience=jwt_audience,
        ttl_seconds=args.ttl,
        scope=args.scope,
        kid=civ_id,
    )

    if args.print_jwt_only:
        # Clean single-line output for callers (e.g. work_chain_record.py).
        print(jwt)
        return

    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] "
          f"Signed JWT for civ_id={civ_id} seat={seat} aud={jwt_audience}")
    print(f"JWT: {jwt[:60]}...")

    if args.verify:
        if not agentauth_url:
            print("ERROR: --verify requires --agentauth-url or AGENTAUTH_URL.", file=sys.stderr)
            sys.exit(1)
        with httpx.Client(timeout=15) as client:
            r = client.post(f"{agentauth_url}/verify-token", json={"token": jwt})
        print(f"Verify: {r.status_code} {r.text[:200]}")
        return

    result = issue_claim(jwt, agentauth_url, civ_id, args.claim, args.ttl)

    if result["ok"]:
        claim_data = result["claim"]
        print("SUCCESS: claim issued")
        for k in ("claim_id", "civ_id", "claim", "issued_by", "issued_at", "expires_at"):
            print(f"  {k}: {claim_data.get(k)}")
    else:
        print(f"FAILED: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
