export const meta = {
  name: 'digest-librarian',
  description: 'AGENTIC digest librarian (Option B per SPEC-SHEET-v0.2 §5 step 3) implemented as a Workflow. SUBSTRATE-INDEPENDENT — synthesis + ALL file I/O run through agent() on the Claude-Code workflow runtime (Opus 4.8 default). The script body cannot do file I/O (sandboxed JS context); only the agent can. The model SELECTS / MERGES / WRITES; the verify agent DISPOSES via auditor-isolation. Compress-not-create, importance-not-recency.',
  phases: [
    { title: 'Validate' },
    { title: 'Librarian' },
    { title: 'Verify' },
  ],
}

// =============================================================================
// SPEC anchors (do not weaken):
//   §5 step 3  COMPRESS-NOT-CREATE — every digest line traces to a log line.
//              The librarian SELECTS / MERGES / DROPS existing log entries.
//              Cannot invent. Derived, never authored-from-scratch.
//   §5 caps    ≤200 lines AND ≤8000 chars of body (hard).
//   §5 rank    LOAD-BEARING importance, NOT recency (cures v1 age-eviction).
//   §6         Distinct from the DREAMER (dreamer = high-order pattern-draw
//              across all memory; librarian = low-order compression).
//   §7         Validator-step is the win. Post-verify gate makes agentic safe.
//   §9         ONE shared runtime (Claude Code on Opus 4.8). Substrate-independent
//              ACROSS ADOPTERS — every adopter civ runs the SAME Claude Code +
//              Opus 4.8 substrate; the only independent axis is TGIM CIV-IDENTITY
//              (each adopter posts as themselves via their own AgentAUTH keypair).
//
// 🚨 RUNTIME CONSTRAINT (caught in production 2026-05-30):
//   Workflow SCRIPTS run in a sandboxed JS context with NO filesystem access.
//   There are no read/write/fs globals available to the script body. ONLY
//   agents (via their Read/Write/Bash tools) can touch files. So this workflow
//   is structured as:
//     - SCRIPT: validate args, invoke agent()s, return synthesis
//     - LIBRARIAN AGENT: reads log.jsonl, drafts digest, writes DIGEST.md
//     - VERIFY AGENT: independent auditor re-checks every line traces (no invention)
//   See skills/workflow-js-mastery/SKILL.md §9 for the failure-mode row.
//
// CONTRACT WITH THE RUNTIME (tools/incarnation_runner.py):
//   Runtime DETECTS staleness via --check-stale (compares DIGEST.md frontmatter
//   ledger_lines_at_rebuild to current log line count). REBUILD is owned here
//   in the workflow layer: the org-assembler / parent workflow invokes
//   workflow('digest-librarian', {lead, now}) for each stale lead BEFORE
//   assembling memory into the next incarnation's inline block.
//
// CALLER CONTRACT (args):
//   args.lead       (required, str)   the lead id whose DIGEST to rebuild
//   args.now        (required, str)   ISO-Z timestamp stamped into frontmatter;
//                                     callers OWN the clock — we do not call it.
//   args.repo_root  (optional, str)   absolute path to the civ-repo root that
//                                     houses the mem/ tree. Defaults to the
//                                     workflow runtime's working directory.
//                                     Adopters who incarnate this workflow from
//                                     a non-repo-root cwd MUST pass repo_root.
//   args.cap_chars  (opt, int)        body char cap; default 8000 (SPEC §5).
//   args.cap_lines  (opt, int)        body line cap; default 200 (SPEC §5).
//
// RETURNS (firewall-tight synthesis, NEVER raw log content beyond pointers):
//   { ok, lead, digest_path, ledger_lines_at_rebuild,
//     body_lines, body_chars, mechanism: 'agentic-workflow',
//     kept_ids_count, dropped_untraced_ids_count, verify_errors,
//     fallback_reason | null }
// =============================================================================

// ---- INPUT VALIDATION (caller-supplied; treat as untrusted) ----
const LEAD_RE = /^[A-Za-z0-9_][A-Za-z0-9_.\-]{0,63}$/
const ISO_Z_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/
// Repo root must be an absolute POSIX path (no traversal, no shell metas).
const REPO_ROOT_RE = /^\/[A-Za-z0-9_./\-]{1,400}$/

phase('Validate')

const lead = String((args && args.lead) || '').trim()
const now = String((args && args.now) || '').trim()
if (!LEAD_RE.test(lead)) {
  return {
    ok: false,
    error: `invalid args.lead ${JSON.stringify(lead)} — must match ${LEAD_RE.source}`,
  }
}
if (!ISO_Z_RE.test(now)) {
  return {
    ok: false,
    error: `invalid args.now ${JSON.stringify(now)} — caller MUST pass ISO-Z timestamp (YYYY-MM-DDThh:mm:ssZ); workflow does not call the clock`,
  }
}

const CAP_CHARS = Math.max(500, Math.min(20_000, Number((args && args.cap_chars) || 8_000)))
const CAP_LINES = Math.max(10, Math.min(1_000, Number((args && args.cap_lines) || 200)))

// Substrate-independent repo-root resolution. Adopters who run this workflow
// from inside their civ-repo's working directory get the default; adopters who
// fork the workflow runtime from elsewhere MUST pass `args.repo_root` so the
// librarian can locate `mem/canon/<lead>/`. No hardcoded civ path.
let REPO_ROOT = String((args && args.repo_root) || '').trim()
if (!REPO_ROOT) {
  // Fall back to the workflow runtime's cwd. The script can't call process
  // directly in every sandbox, but the runtime injects cwd into the librarian
  // agent's tool calls — we pass an explicit instruction below to use Bash
  // `pwd` if no repo_root was supplied.
  REPO_ROOT = '<cwd>'
}
if (REPO_ROOT !== '<cwd>' && !REPO_ROOT_RE.test(REPO_ROOT)) {
  return {
    ok: false,
    error: `invalid args.repo_root ${JSON.stringify(REPO_ROOT)} — must be an absolute POSIX path matching ${REPO_ROOT_RE.source}`,
  }
}

const LOG_REL = `mem/canon/${lead}/log.jsonl`
const DIGEST_REL = `mem/canon/${lead}/DIGEST.md`
const LOG_ABS = REPO_ROOT === '<cwd>' ? `\${PWD}/${LOG_REL}` : `${REPO_ROOT}/${LOG_REL}`
const DIGEST_ABS = REPO_ROOT === '<cwd>' ? `\${PWD}/${DIGEST_REL}` : `${REPO_ROOT}/${DIGEST_REL}`

log(`Lead ${lead}: rebuilding DIGEST at ${DIGEST_REL} (caps: ${CAP_LINES} lines / ${CAP_CHARS} chars; now=${now}; repo_root=${REPO_ROOT})`)

// =============================================================================
// PHASE 2 — LIBRARIAN AGENT (does ALL file I/O the script cannot do)
// =============================================================================
phase('Librarian')

const LIBRARIAN_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    ok: { type: 'boolean' },
    log_existed: { type: 'boolean' },
    ledger_lines_at_rebuild: { type: 'integer', minimum: 0 },
    body_lines: { type: 'integer', minimum: 0 },
    body_chars: { type: 'integer', minimum: 0 },
    kept_ids_count: { type: 'integer', minimum: 0 },
    dropped_superseded_count: { type: 'integer', minimum: 0 },
    dropped_duplicate_count: { type: 'integer', minimum: 0 },
    digest_written: { type: 'boolean' },
    digest_path: { type: 'string', maxLength: 400 },
    notes: { type: 'string', maxLength: 800 },
    error: { type: 'string', maxLength: 800 },
  },
  required: ['ok', 'log_existed', 'ledger_lines_at_rebuild', 'digest_written'],
}

const repoRootInstruction = REPO_ROOT === '<cwd>'
  ? (
      `# Resolving paths\n` +
      `The caller did NOT pass args.repo_root, so resolve paths relative to YOUR\n` +
      `current working directory. Run Bash \`pwd\` ONCE at the start; treat that\n` +
      `as <REPO_ROOT>. The log lives at <REPO_ROOT>/${LOG_REL} and the DIGEST at\n` +
      `<REPO_ROOT>/${DIGEST_REL}. If <REPO_ROOT>/mem/canon/ does not exist, the\n` +
      `caller invoked this workflow from outside a civ-repo root — return\n` +
      `ok=false with error="repo_root unresolved" and do NOT create directories.\n`
    )
  : (
      `# Resolving paths\n` +
      `The caller passed args.repo_root=${REPO_ROOT}. Use these absolute paths:\n` +
      `  log:    ${LOG_ABS}\n` +
      `  digest: ${DIGEST_ABS}\n`
    )

const librarianPrompt =
  `You are the AGENTIC DIGEST LIBRARIAN for lead \`${lead}\`. You COMPRESS the canon\n` +
  `log into a small, load-bearing DIGEST. You are the only one in this workflow who can\n` +
  `touch the filesystem — the calling script has NO file I/O capability.\n` +
  `\n` +
  repoRootInstruction +
  `\n` +
  `# Your task (in order)\n` +
  `\n` +
  `1. READ the log file (path resolved above).\n` +
  `   - Use your Read or Bash tool. The file is JSONL (one JSON object per line).\n` +
  `   - If the file does NOT exist: set log_existed=false, write an empty stamped DIGEST\n` +
  `     (instructions below in step 5), set ledger_lines_at_rebuild=0, return.\n` +
  `   - Each line is a canon entry: \`{id, ts, lead, kind, item, rationale, ...}\`.\n` +
  `     Possible kinds include: decision, doctrine-candidate, finding, retraction.\n` +
  `   - Count the non-empty lines: that is \`ledger_lines_at_rebuild\` (REQUIRED for\n` +
  `     the frontmatter — the staleness gate compares it to live line count).\n` +
  `\n` +
  `2. PRE-FILTER (structural, deterministic — do this faithfully):\n` +
  `   a. SUPERSESSION: any entry of kind=\`retraction\` may carry a field named\n` +
  `      \`superseded_id\` or \`retracts_id\` or \`target_id\` pointing at another id.\n` +
  `      DROP that targeted id from the pool. Keep the retraction entries themselves\n` +
  `      for the annotations section below.\n` +
  `   b. DEDUPE by normalized \`item\` text (trim+lowercase+collapse-whitespace) —\n` +
  `      keep the NEWEST \`ts\`. This kills repeats of the same essential claim.\n` +
  `\n` +
  `3. COMPRESS-NOT-CREATE (the load-bearing job):\n` +
  `   - RANK by LOAD-BEARING IMPORTANCE, NOT recency. An OLD load-bearing entry\n` +
  `     (decision, doctrine-candidate, high-stakes operational gotcha) MUST survive\n` +
  `     over a recent trivial finding. The age-eviction trap from v1 is exactly what\n` +
  `     you exist to fix. KEEP OLD LOAD-BEARING ENTRIES.\n` +
  `   - DROP entries that are clearly trivial / superseded by content (even if no\n` +
  `     retraction line exists), or duplicates of higher-ranked entries.\n` +
  `   - MERGE related entries into one synthetic bullet when the synthesis is more\n` +
  `     load-bearing than the parts. When you merge, cite ALL source ids in the bullet.\n` +
  `   - Kind priority order: decision > doctrine-candidate > finding > retraction.\n` +
  `   - CAPS (hard): <=${CAP_LINES} bullets in the Canon section AND <=${CAP_CHARS}\n` +
  `     chars of body total. Stop before overflow.\n` +
  `\n` +
  `4. NO-INVENTION GATE (self-check before write):\n` +
  `   - EVERY bullet you write MUST trace to >=1 real source log line.\n` +
  `   - After drafting, re-scan EVERY bullet. For each one, locate the source\n` +
  `     entry(ies) in the log by id. If you cannot point at a real source line\n` +
  `     whose \`item\` or \`rationale\` text supports the bullet's prose, DROP that\n` +
  `     bullet. The verify agent in the next phase will run an independent check\n` +
  `     and refuse to confirm if any bullet is un-traceable — don't ship a\n` +
  `     bullet you can't defend.\n` +
  `\n` +
  `5. WRITE the DIGEST file (path resolved above).\n` +
  `   - Use your Write tool (or Bash with a heredoc if Write is unavailable).\n` +
  `   - The file format is:\n` +
  `     \`\`\`\n` +
  `     ---\n` +
  `     last_rebuilt_at: ${now}\n` +
  `     ledger_lines_at_rebuild: <N>\n` +
  `     lead: ${lead}\n` +
  `     source_log: ${LOG_REL}\n` +
  `     mechanism: agentic-workflow\n` +
  `     body_lines: <count>\n` +
  `     body_chars: <count>\n` +
  `     ---\n` +
  `     ## Canon (load-bearing first — agentic-workflow)\n` +
  `     \n` +
  `     - \`id=<id1>\` \`<ts>\` **<kind>** — <prose>\n` +
  `     - \`id=<id2> id=<id3>\` \`<newest-ts>\` **<kind>** — <merged prose>\n` +
  `     ...\n` +
  `     \n` +
  `     ## Retractions (annotations)\n` +
  `     \n` +
  `     - \`id=<retraction-id>\` \`<ts>\` **retraction** -> \`<target-id>\` — <item>\n` +
  `     \`\`\`\n` +
  `   - The frontmatter fields above are MANDATORY (mechanism='agentic-workflow',\n` +
  `     last_rebuilt_at='${now}', ledger_lines_at_rebuild=<N you counted>).\n` +
  `   - If the log file did not exist (step 1), write a minimal valid DIGEST with\n` +
  `     ledger_lines_at_rebuild=0 and body \`(empty — no canon entries on disk)\`.\n` +
  `\n` +
  `6. RETURN the StructuredOutput with the counts you observed:\n` +
  `   - ok=true if you successfully wrote the DIGEST, false on any error\n` +
  `   - log_existed=true/false from step 1\n` +
  `   - ledger_lines_at_rebuild=<integer count of non-empty log lines>\n` +
  `   - body_lines/body_chars from what you actually wrote\n` +
  `   - kept_ids_count = number of unique source ids cited across all bullets\n` +
  `   - dropped_superseded_count = how many supersession drops in step 2a\n` +
  `   - dropped_duplicate_count = how many dedupe drops in step 2b\n` +
  `   - digest_written=true if the file is on disk, digest_path='${DIGEST_REL}'\n` +
  `   - notes: brief one-line summary of what you did (e.g. "kept 47 / 312, capped at lines")\n` +
  `   - error: empty string unless ok=false\n` +
  `\n` +
  `Return the structured librarian-report.`

let librarian = null
let librarianError = null
try {
  librarian = await agent(librarianPrompt, {
    label: `librarian-${lead}`,
    phase: 'Librarian',
    schema: LIBRARIAN_SCHEMA,
  })
} catch (e) {
  librarianError = `librarian agent threw: ${String(e)}`
}
if (!librarian) {
  return {
    ok: false,
    lead,
    digest_path: DIGEST_REL,
    error: librarianError || 'librarian agent returned null (StructuredOutput not called)',
    mechanism: 'agentic-workflow',
  }
}
if (librarian.ok === false || librarian.digest_written === false) {
  return {
    ok: false,
    lead,
    digest_path: DIGEST_REL,
    ledger_lines_at_rebuild: librarian.ledger_lines_at_rebuild || 0,
    mechanism: 'agentic-workflow',
    error: librarian.error || 'librarian reported failure',
    librarian_notes: (librarian.notes || '').slice(0, 400),
  }
}

log(`Lead ${lead}: librarian wrote DIGEST (${librarian.body_lines || 0} lines / ${librarian.body_chars || 0} chars; kept ${librarian.kept_ids_count || 0} ids; ledger=${librarian.ledger_lines_at_rebuild})`)

// =============================================================================
// PHASE 3 — VERIFY AGENT (auditor-isolation: independent NO-INVENTION re-check)
// =============================================================================
phase('Verify')

const VERIFY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    ok: { type: 'boolean' },
    bullets_checked: { type: 'integer', minimum: 0 },
    untraced_bullets: {
      type: 'array',
      maxItems: 50,
      items: { type: 'string', maxLength: 300 },
    },
    frontmatter_ok: { type: 'boolean' },
    frontmatter_issues: {
      type: 'array',
      maxItems: 20,
      items: { type: 'string', maxLength: 200 },
    },
    summary: { type: 'string', maxLength: 400 },
  },
  required: ['ok', 'bullets_checked', 'untraced_bullets', 'frontmatter_ok'],
}

const verifyRepoRootInstruction = REPO_ROOT === '<cwd>'
  ? `Resolve paths relative to YOUR current working directory (Bash \`pwd\`). The DIGEST is at <PWD>/${DIGEST_REL} and the log at <PWD>/${LOG_REL}.\n`
  : `The librarian wrote to ${DIGEST_ABS}; the source log is at ${LOG_ABS}.\n`

const verifyPrompt =
  `You are an INDEPENDENT VERIFY AUDITOR for the digest-librarian workflow. You did NOT\n` +
  `write the digest — you check it. Auditor-isolation: you do not modify, only judge.\n` +
  `\n` +
  verifyRepoRootInstruction +
  `\n` +
  `# Your task\n` +
  `\n` +
  `1. READ the freshly written DIGEST (path above).\n` +
  `2. READ the source log (path above) — may not exist — in that case the digest\n` +
  `   should be the empty-stamped form with ledger_lines_at_rebuild=0.\n` +
  `3. FRONTMATTER CHECK — confirm all of these are present and correct:\n` +
  `   - mechanism: agentic-workflow\n` +
  `   - last_rebuilt_at: ${now}  (exact match)\n` +
  `   - ledger_lines_at_rebuild: <integer matching count of non-empty log lines>\n` +
  `   - lead: ${lead}\n` +
  `   If any are missing/wrong, set frontmatter_ok=false and list issues.\n` +
  `4. NO-INVENTION CHECK — for EVERY bullet line in the digest body (lines\n` +
  `   starting with \`- \` containing \`id=<value>\` tokens):\n` +
  `   a. Parse out every \`id=<value>\` token.\n` +
  `   b. For each id, locate the matching log entry (by exact id).\n` +
  `      If any cited id does NOT appear in the log, the bullet is UNTRACED — add\n` +
  `      its first ~80 chars to \`untraced_bullets\`.\n` +
  `   c. For the bullet's prose, confirm it semantically traces to the cited entries'\n` +
  `      \`item\` or \`rationale\` text. The simplest test: does the prose share\n` +
  `      meaningful tokens (>=2 distinct >=4-char words) with at least one cited\n` +
  `      entry, OR does it verbatim-substring-include one? If neither, treat as\n` +
  `      UNTRACED (laundering — invented prose with a valid id attached) and add\n` +
  `      to \`untraced_bullets\`.\n` +
  `5. RETURN:\n` +
  `   - ok = true ONLY if frontmatter_ok=true AND untraced_bullets is empty\n` +
  `   - bullets_checked = total bullet lines you examined in the Canon section\n` +
  `   - untraced_bullets = list (may be empty)\n` +
  `   - frontmatter_ok + frontmatter_issues\n` +
  `   - summary: one-line judgement (e.g. "47 bullets, all traced, frontmatter clean")\n` +
  `\n` +
  `Do NOT modify the digest. Do NOT rewrite anything. You are a judge, not a librarian.\n` +
  `Return the structured verify-report.`

let verify = null
let verifyError = null
try {
  verify = await agent(verifyPrompt, {
    label: `verify-${lead}`,
    phase: 'Verify',
    schema: VERIFY_SCHEMA,
  })
} catch (e) {
  verifyError = `verify agent threw: ${String(e)}`
}

const verify_errors = []
if (!verify) {
  verify_errors.push(verifyError || 'verify agent returned null (StructuredOutput not called) — could not confirm no-invention')
} else {
  if (!verify.frontmatter_ok) {
    for (const issue of (verify.frontmatter_issues || []).slice(0, 20)) {
      verify_errors.push(`frontmatter: ${issue}`)
    }
  }
  for (const utb of (verify.untraced_bullets || []).slice(0, 50)) {
    verify_errors.push(`untraced: ${utb}`)
  }
}

const verifyOk = !!(verify && verify.ok && verify_errors.length === 0)

log(`Lead ${lead}: verify ${verifyOk ? 'PASSED' : 'FLAGGED'} — ${verify_errors.length} errors (${verify ? verify.bullets_checked : 0} bullets checked)`)

// FIREWALL: small synthesis return only. NO raw bullet text, NO log content —
// pointers + counts + verify-error sample only.
return {
  ok: verifyOk,
  lead,
  digest_path: DIGEST_REL,
  ledger_lines_at_rebuild: librarian.ledger_lines_at_rebuild,
  body_lines: librarian.body_lines || 0,
  body_chars: librarian.body_chars || 0,
  mechanism: 'agentic-workflow',
  kept_ids_count: librarian.kept_ids_count || 0,
  dropped_untraced_ids_count: verify ? (verify.untraced_bullets || []).length : 0,
  dropped_superseded_count: librarian.dropped_superseded_count || 0,
  dropped_duplicate_count: librarian.dropped_duplicate_count || 0,
  verify_errors: verify_errors.slice(0, 20),
  fallback_reason: librarian.log_existed === false ? 'no log entries on disk' : null,
  librarian_notes: (librarian.notes || '').slice(0, 400),
  verify_summary: verify ? (verify.summary || '').slice(0, 400) : 'verify agent failed',
}
