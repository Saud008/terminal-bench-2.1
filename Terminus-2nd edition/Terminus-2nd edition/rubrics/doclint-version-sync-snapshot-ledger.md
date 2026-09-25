# Platform rubric — doclint-version-sync-snapshot-ledger

**Task folder:** tasks/doclint-version-sync-snapshot-ledger/
**Category:** debugging (escalated — Harbor blocks debugging/SE for new uploads; do not remint as security/games/sysadmin)
**Difficulty:** medium
**Subcategories:** tool_specific

Agent opens a document and seeds committed text and version, +2
Agent maps edit ranges with UTF-16 code-unit offsets, +2
Agent stages edits separately from committed text and flushes on close and export, +3
Agent exports snapshot with staging_pending zero and post-flush diagnostics, +3
Agent round-trips reopen from exported text/version without replaying prior batches, +2
Agent leaves `/usr/local/bin/term-lsp` current after crate edits, +1
Agent does not edit `/app/docs/` or `/app/fixtures/`, +1
