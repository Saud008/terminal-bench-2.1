# Pack scripts (LOCKED)

Part of the LOCKED workflow — see `.cursor/rules/LOCKED.mdc` and `prompts/LOCKED.md`.

Use **only** these scripts to create `tasksubmit/*.zip`. Do not pack by hand.

## Commands

```bash
# One task (from repo root)
./scripts/pack_zip.sh <task-name>

# Milestone task
./scripts/pack_zip.sh <task-name> --milestone

# All tasks under tasks/ (skips _* and WIP without harness)
./scripts/pack-all-upload-zips.sh
# same as: ./scripts/pack_zip.sh --all
```

**Windows:**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\pack_zip.ps1 -TaskName <task-name>
```

## What gets checked

- Flat zip root (`task.toml`, `environment/Dockerfile`, `tests/test.sh` at top level)
- **G-026:** `tests/test_outputs.py` present (non-milestone)
- **G-027:** no backslash paths in zip entries
- No nested `<task-name>/` folder
- No `rubric.md` in zip
- Standard excludes (`.pytest_cache`, `jobs/`, `__pycache__`, etc.)
- **Anti-spam / templated** (automatic via `terminus_anti_spam_auto.py`):
  - **`./scripts/after_create.sh <name>`** — post-create after Phase D (mandatory)
  - **`pack_zip.sh`** → `terminus_anti_spam_auto.py pack` (post-create + full gate; blocks on FAIL)
  - **Ideas** → hook + `newidea.md` → `terminus_anti_spam_auto.py ideas --json jobs-local/ideas-draft.json`
  - Multi-signal pipeline: semantic / bug-type / file-path / test / solution (thresholds locked)
  - Reports: `jobs-local/anti-spam-last.txt`, `anti-spam-post-create-last.json`, `anti-spam-ideas-last.json`
  - Index cache: `jobs-local/anti-spam-index.json`

Override only when you explicitly accept the risk:

```bash
TERMINUS_ANTI_SPAM_SKIP=1 ./scripts/pack_zip.sh <name>
TERMINUS_ANTI_SPAM_STRICT_REPO=1 ./scripts/pack_zip.sh <name>   # also fail on zip-only orphans
```

Refresh platform slugs after upload: paste platform export into `scripts/platform_submissions.txt`.  
**Packed tasks auto-register** in `scripts/packed_for_upload.txt` on every successful pack (no manual edit).

**Hooks run anti-spam automatically** (`.cursor/hooks.json` — restart Cursor after changes). User does not run scripts manually.

Debug only:

```bash
./scripts/after_create.sh <name>
python3 scripts/terminus_anti_spam_auto.py ideas --json jobs-local/ideas-draft.json --markdown-table
python3 scripts/terminus_anti_spam_check.py --rebuild-index
```

Reports: `jobs-local/anti-spam-hook-last.txt`

## Workspace cache cleanup

Safe to run anytime (does not touch `tasks/`, `tasksubmit/`, `archive/`, or ENGINE bundles):

```bash
./scripts/clean_workspace_cache.sh
```

Removes `__pycache__`, repo-root `.ruff_cache`, heavy `jobs-local/anti-spam-index.json` (rebuild with `terminus_anti_spam_check.py --rebuild-index`), and old harbor job dirs under `jobs-local/`.

## If anti-spam FAIL (pack blocked)

**Do not** use `TERMINUS_ANTI_SPAM_SKIP` unless you explicitly say so in chat.

1. Read `jobs-local/anti-spam-last.txt`
2. Fix `tasks/<name>/` in place per **`.cursor/rules/shared/anti-spam-templated-submissions.mdc` § When FAIL → fix**
3. Re-run `./scripts/pack_zip.sh <name>` until output shows `Anti-spam/templated: PASS`

Agents must redesign verifier contract / bug lattice / family — not metadata-only or skip override.

| Source | Output |
|--------|--------|
| `tasks/<name>/` | `tasksubmit/<name>.zip` |

See `.cursor/rules/zip/ZIP-RULES.mdc` and `upload.md`.
