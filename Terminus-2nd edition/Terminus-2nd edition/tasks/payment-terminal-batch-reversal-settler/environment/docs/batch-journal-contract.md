# Batch journal contract

Journal path: /app/state/batch-journal.jsonl
Metadata path: /app/state/journal-meta.json
## Journal lines

Each JSONL row contains seq, txn_id, terminal_id, merchant_id, txn_type, amount_cents, state, normalized_digest.

Rows are ordered by event_ms ascending then txn_id lexicographic after pairing and cutoff filtering. That sort order governs journal emission and seq assignment only; it does not change reversal pairing eligibility (see reversal-pairing-contract.md).

## Sequence guard

seq is a single global counter starting at 1 for the batch journal, not per merchant.

## Normalized digest

normalized_digest is lowercase hex SHA-256 over the pipe-joined fields:
batch_id|terminal_id|merchant_id|txn_id|auth_code_normalized|amount_cents|state

auth_code_normalized is lowercase per reversal-pairing-contract.

## Journal digest

journal_digest is lowercase hex SHA-256 over the compact JSON bytes of each journal line plus newline, in file order.

Metadata records engine termsetctl, scenario, batch_id, journal_digest, line_count.
