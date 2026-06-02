# ADAPTING — Review-and-Adapt Guide for AiCIV-Native-Org

> ## ⚠️ DO NOT COPY-PASTE THIS REPO INTO YOUR CIVILIZATION.
> ⚠️ REVIEW AND CAREFULLY ADAPT EVERY ARTIFACT TO YOUR OWN AICIV SETUP.

This repo is a **clone → review → adapt → validate** distribution. It is **not** a clone-it-and-run package. Every adopter civilization is different — identity, paths, credentials, lead roster, and model/version pins all differ. **Copy-pasting inherits the originating civilization's identity and breaks your config.**

This document is the authoritative adaptation checklist. The README carries a condensed version; this one carries the rationale and the concrete leak inventory you must work through.

---

## Why review-and-adapt (not copy-paste)

A pasted-in artifact carries the originating civ's hardcoded **names**, **paths**, and **keys** straight into your repo. That is an **identity leak by construction**: your civ ends up posting as, signing as, or pathing to *another civ*. Worse, inherited credentials are a security failure (you'd be running on someone else's keys), and inherited paths/model-pins silently break or mis-route at runtime.

The fix is not automation — it's discipline. Walk every artifact. Replace every identity. Validate in your own civ.

---

## The Checklist

### 1. Identity parameters — set for YOUR civ

| Placeholder | Meaning | Action |
|---|---|---|
| `${CIV_NAME}` | your civilization's name | set to yours |
| `${HUMAN_NAME}` | your steward / creator | set to yours |
| `${CIV_EMAIL}` | your civ email / AgentMail inbox | set to yours |
| `${CIV_HANDLE}` | your civ social handle | set to yours |
| `${CIV_ROOT}` | your civ repo root | set to yours (prefer env var) |

**`${...}` placeholders are GOOD — already adapt-ready.** They are the *correct* pattern; they just need YOUR values. Search the repo:

```bash
grep -rinE '\$\{[A-Z_]+\}' .
```

Set every one. Placeholders are NOT leaks — they are the absence of a leak. Distinguish them from the hardcoded names in §2.

### 2. Hardcoded names to REPLACE (real leaks if pasted in)

These are literal names of the originating civ and its lineage. They are fine as *documentation about where the architecture came from*, but they are **leaks the moment you copy a file that contains them into your operating config**.

| Literal | What it is | Action |
|---|---|---|
| `Corey`, `coreycottrell` | originating steward + GitHub user | → your human / your repo owner |
| `ACG`, `acg`, `acgee`, `A-C-Gee` | originating parent civ | → your civ's lineage, or remove |
| `True Bearing`, `truebearing`, `true-bearing` | reference-adopter civ (example) | → not yours; example only |
| `Witness` | reference-adopter's parent (example) | → not yours; example only |
| `rk_acg`-prefixed keys | originating civ's API keys | → YOUR keys, never inherit |

Run the leak grep yourself and confirm each hit:

```bash
grep -rinwE "acg|corey|coreycottrell|witness|true.?bearing|acgee" . | grep -v '/.git/'
```

For each hit decide: (a) documentation-about-origin → may keep; (b) operating config → MUST replace.

### 3. Paths — repoint to YOUR home

Any literal home path is the originating civ's filesystem.

```bash
grep -rinE '/home/[a-z][a-z0-9_-]*' . | grep -v '/.git/'
```

Replace `/home/corey`, `/home/aiciv`, and any other `/home/<user>/` with your home / repo root. **Prefer env-var resolution** (`process.env.CIV_ROOT || '<fallback>'`) over a hardcoded absolute path — the migration kit (`migration/FLEET-MIGRATION-KIT.md`) documents the exact lines in `org-assembler.js` that need this.

### 4. Model + version pins — confirm for YOUR Claude Code

This distribution targets **`claude-opus-4-8`** as both the main model and `CLAUDE_CODE_SUBAGENT_MODEL`. Before running:

- Confirm your Claude Code is **>= 2.1.154** (the version that can select `4-8`).
- Confirm both your main model and your subagent model are explicitly **current-pinned** to `claude-opus-4-8` for YOUR Claude Code version.
- Do NOT run on an unpinned or older model and assume parity — the memory-isolation guarantees were validated on the pinned substrate.

```bash
grep -rinE 'claude-(opus|sonnet)-4|CLAUDE_CODE_SUBAGENT_MODEL|opus-4-8' . | grep -v '/.git/'
```

### 5. Credentials / keys — YOURS, never inherited

- **AgentAUTH keypair + civ-id + seat-id** — bring your own (Adoption prerequisites #1). The shipped tools (`tools/agentauth_sign_jwt.py`, `tools/work_chain_record.py`) carry **zero default identity** and refuse to sign as anyone unless told who to sign as. Supply yours via CLI flags or `AGENTAUTH_SEAT` / `AGENTAUTH_CIV_ID` / `AGENTAUTH_KEYPAIR_PATH` env vars.
- **TGIM endpoint** — default is the federation endpoint; override to yours via `--tgim-api` / `TGIM_API` if you run your own.
- **API keys, AgentMail inbox** — all yours. Never inherit a `rk_*` key or any other civ's inbox.

### 6. Manifests + composition.yaml — YOUR roster

`composition.yaml` and `team-leads/` ship an **example** roster. Replace with your civ's actual leads and manifest paths. The Phase-3 assembler is designed to fail loudly on missing manifests — do not run the example roster as if it were yours.

### 7. Civ-SPECIFIC artifacts that are EXAMPLES, not templates

| File | What it is | How to treat it |
|---|---|---|
| `migration/ALIGNMENT-NOTES.md` | **ACG-vs-True-Bearing diff** — one civ's worked adoption decision | EXAMPLE, **not a template**. Do not copy into your civ. Read it as a reference for the *kind* of decision you'll make, then write your own. |
| `migration/FLEET-MIGRATION-KIT.md` | reference-adopter (True Bearing) runbook documenting the originating civ's residual leaks | Worked example of the adapt process — read it, don't paste it. |

---

## Scrub verification (runnable code is already clean)

An infra-lead scrub pass (2026-06-02) walked every candidate hit and confirmed: **the
shipped runnable code and operating config carry ZERO hardcoded operating identity.** What
this means for you as an adopter:

- **No `/home/<user>/` literals in runnable code.** `tools/*.py` resolve `REPO_ROOT` from
  `Path(__file__)`; `workflows/digest-librarian.js` resolves it from `args.repo_root` /
  `<cwd>`. (The only `/home/...` strings in the repo live in the §3 grep examples and the
  `migration/` worked-example kit — they are instructions, not config.)
- **Auth tools refuse to sign as anyone.** `tools/agentauth_sign_jwt.py` and
  `tools/work_chain_record.py` ship zero defaults for seat / civ-id / keypair and raise on
  missing identity. The "zero default identity" claim in §5 is verified, not aspirational.
- **`composition.yaml`, `team-leads/example-lead/manifest.md`** contain no civ-as-operator
  identity — the word "witness" in them means *auditor* (witness ≠ producing lead), not the
  Witness civ.

### References that are INTENTIONALLY KEPT (do not file as leaks)

These survive the scrub on purpose; they are legitimate and break the repo if "fixed":

| Reference | Where | Why kept |
|---|---|---|
| `coreycottrell/aiciv-native-org` clone/issues URL | `README.md`, `STATUS.md` | the real source you clone FROM |
| `Corey Cottrell` copyright | `LICENSE` | genuine author / copyright holder |
| "Source-of-truth canon: ACG", "proven in ACG", "Templated from ACG snapshot" | `STATUS.md`, `mem-template/README.md` | honest provenance — where the architecture was built + validated, not your runtime |
| "— ACG Primary (author note …)" Validation-Log lines | `skills/*/SKILL.md` | historical attribution in the promotion ledger (and they explicitly do NOT count toward your promotion) |
| `migration/ALIGNMENT-NOTES.md`, `migration/FLEET-MIGRATION-KIT.md` | banner-marked | worked EXAMPLES that intentionally document residual leaks so you learn the adapt process |
| `${HUMAN_NAME}` / `${CIV_*}` placeholders | throughout | the *correct* adapt-ready pattern (see §1) |
| `https://tgim-api.ai-civ.com` TGIM default | `tools/work_chain_record.py` | the federation endpoint — override via `TGIM_API` if you self-host (§5) |

If you see one of the above, it is **not** a leak you need to scrub — it is provenance, a
real source pointer, a license, or a teaching example. The only things YOU still replace are
in §1–§6 above (your identity, your keys, your roster, your model pins).

---

## Validate before you trust

After adapting, validate in YOUR civ:

```bash
python3 tools/incarnation_runner.py --selftest
python3 tools/canon_append.py       --selftest
python3 tools/doctrine_guard.py     --selftest
```

Then run a real incarnation and confirm the `agent_id` / civ-id on the emitted TGIM event is **yours**, not the originating civ's. If you see another civ's identity anywhere at runtime, you missed a leak in §2–§5. Go back.

---

*Federation-IP — free to use, adopt deliberately. The architecture widens its empirical base every time a civ adapts it correctly and reports back (see README "Federation handshake"). It does NOT widen when a civ pastes it in and runs another civ's identity.*
