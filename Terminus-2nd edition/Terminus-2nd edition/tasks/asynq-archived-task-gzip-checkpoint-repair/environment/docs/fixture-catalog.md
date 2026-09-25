# Fixture catalog

Scenarios under /app/fixtures/scenarios/:

baseline-tasks — simple unique ids
duplicate-ids — same id repeated across JSONL lines for archive spread
priority-mismatch — retry and priority differ by design
partial-member — second member truncated in bundled fixture for index offset tests
retention-skew — archived_at_ms values around a fixed cutoff

Seeds listed in /app/fixtures/seeds.json namespace task ids when loading.

Hidden verifier scenarios may appear under TB3_ARCHIVE_FIXTURES when set to an absolute directory path.
