Museum accession vault playtest

Build the museum accession vault playtest, an offline gallery-curation playfield planner for archive admission traps, custody-lineage scoring, loan-window traps, rights-precedence shelves, restoration chronology, duplicate-accession gates, and sealed dossier win conditions on the working baseline under `/app`. The planner loads archive playfield packs, applies vault-load staging and compose-align gate scoring, then seals publish-dossier playtest exports when the dossier win condition is met. There is no live museum CMS and no outbound network. This is a games museum-accession playfield playtest and sealed-dossier win-condition workflow: keep archive admission, archive_seq monotonicity, compose-align register supersession, snapshot_digest freshness fences, custody/loan/rights/restoration/duplicate traps, and sealed dossier exports aligned. It is not a Python package rebuild, pytest harness, CI tooling drill, security product audit, system-administration ops desk, or data-processing pipeline.

`musdoss` is available at `/usr/local/bin/musdoss`. Playtest verbs:

```text
musdoss vault load --seed <seed> --archive <name>
musdoss compose align --seed <seed> --archive <name>
musdoss publish dossier --seed <seed> --archive <name> --output <path>
```

Playfield contracts under `/app/docs/` define the enforceable win-condition rules:

- `/app/docs/accession-ops-workflow.md` — admit → gate → seal playtest ladder
- `/app/docs/vault-snapshot-schema.md` — vault layout and `archive_seq` monotonicity
- `/app/docs/custody-lineage-contract.md` — transfer_date-ordered party-name custody chain
- `/app/docs/loan-window-policy.md` — missed-return and overlapping-loan trap rows
- `/app/docs/rights-precedence-rules.md` — stricter (lower) precedence among unexpired rights
- `/app/docs/restoration-timeline-order.md` — ascending restoration chronology
- `/app/docs/register-database-contract.md` — active-row `archive_seq` / `snapshot_digest` binding
- `/app/docs/dossier-publish-fields.md` — sealed dossier fields, summary shape, `audit_digest`
- `/app/docs/accession-problem-charter.md` — rejected incomplete playtest behaviors
- `/app/docs/archive-catalog.md` — bundled playfield pack inventory

`vault load` admits the named archive into `/app/state/accession-vault.json`. Vault field layout, `archive_seq` monotonicity, embedded archive-name checks, and incompleteness modes follow the vault and accession charter docs above.

`compose align` upserts the latest seed-scoped dossier row into `/app/work/register.db`. A subsequent align for that seed supersedes the previous active row even if the archive name changes. Register layout, `archive_seq` binding, and `snapshot_digest` freshness follow `/app/docs/register-database-contract.md`.

`publish dossier` joins the vault file with the active register row for the named seed and archive, then writes sealed dossier JSON at the caller-provided `--output` path only when that join succeeds. Published keys, conflict flags, chronology rules, and `audit_digest` composition follow `/app/docs/dossier-publish-fields.md`. The `custody_lineage` field is an ordered list of party name strings (earliest `from_party`, then each `to_party` by `transfer_date`; same-date rows keep archive input order). It is not `"A to B"` edge strings — see `/app/docs/custody-lineage-contract.md`.

The decoy helper under `musdoss.decoy` stays off the vault-load, compose-align, and dossier-publish playtest path. Fixture archives and seed pools live under `/app/fixtures/`. Runtime-supplied archive overlays follow the catalog schema. After playfield policy edits under `/app/lib/musdoss/`, leave `/usr/local/bin/musdoss` current for the graded playtest. Do not edit `/app/docs/`, `/app/config/`, or `/app/fixtures/`.
