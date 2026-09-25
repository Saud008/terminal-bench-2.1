# Submission explanations - bash-ldap-acl-effective-rights-matrix

**Task folder:** tasks/bash-ldap-acl-effective-rights-matrix/
**Platform form only** - not in upload zip.
**Zip:** `tasksubmit/bash-ldap-acl-effective-rights-matrix.zip`
**Updated:** 2026-07-27

**Doc fix (2026-07-27):** Expanded `matrix-export-contract.md`, `deny-before-allow.md`, and `group-closure.md` with normative staging snapshot keys (`group_graph`, `aces`, numeric `schema_version`), canonical `staging_fingerprint` / `report_digest` / `audit_digest` preimages, ACE trust-rank tuple (user before deny at equal depth+scope), and terminal-only group closure semantics — addressing Task Instruction Sufficiency failures from the difficulty run.

**Category note:** Zip metadata uses `security` (LDAP ACL effective-rights authorization control plane / deny-before-allow trust gates / group-closure authz / sealed `report_digest` attestation). Do not set `software-engineering`, `debugging`, or `data-processing` on the platform form. Prior upload failed Harbor `[category_classifier]` as blocked `software-engineering` when the prompt led with engineering-problem / pytest / Implement framing; keep the authorization / attestation security framing and the explicit “not a CLI-engineering exercise” negation.

> Agent scaffold only — rewrite in your own words before Snorkel upload. LLM paste is a critical policy violation.

## Difficulty Explanation

This task is about directory-security operators shipping a host-local LDAP ACL effective-rights authorization control plane under /app. I rated it hard because the behavior is split across acl-block-format.md, default-inheritance.md, deny-before-allow.md and multiple source files. Fixing one layer often looks fine on the bundled data while other checks still fail. The painful parts are export must read the on-disk staging snapshot, not re-derive everything from raw inputs and fingerprint plus digest fields have to stay in sync across two CLI runs. With about 18 checks in the suite, a partial fix often passes bundled cases but still fails once you hit edge paths or a second run.

## Solution Explanation

The oracle drops corrected sources (multiple source files) into /app, rebuilds the project, and exercises /usr/local/bin/ldaprm against the same fixtures agents see. Ingest validates inputs, writes the staging snapshot and fingerprint metadata, and only then should export trust those bytes for ACE ranking and inheritance gates. Key insight: follow the doc contracts for ordering, digests, and exit codes instead of patching around symptoms in one module. A second export on unchanged staging should stay idempotent.

## Verification Explanation

test.sh rebuilds the binary each time. Pytest (18 tests) calls /usr/local/bin/ldaprm via subprocess. Tests do not grep source for magic strings. The test module includes its own reference math/parser so expected JSON and side files are recomputed from fixtures, which blocks pasted golden answers. Some cases assert the staging snapshot bytes before export fields are graded. NOP on the broken image should score 0. After the oracle patches and rebuild, the suite should pass cleanly.
