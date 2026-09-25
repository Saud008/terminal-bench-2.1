# Platform rubric — payment-terminal-batch-reversal-settler

**Task folder:** tasks/payment-terminal-batch-reversal-settler/
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent compiles terminal transcripts into batch journal staging at /app/state/batch-journal.jsonl, +3
Agent normalizes auth codes to lowercase before reversal pairing keys, +3
Agent pairs reversals on terminal_id auth_code and links_sale_id with matching amount, +3
Agent pairs linked reversals without requiring sale-before-reversal array or event_ms order, +3
Agent includes transactions at cutoff_event_ms inclusive per cutoff-window-contract, +3
Agent assigns one global seq counter across merchants in the journal, +3
Agent includes merchant_id in normalized_digest line hash input, +3
Agent finalizes captured sales to settled state before journal emission, +3
Agent seals settlement-bundle.json with journal_digest and net_amount_cents, +3
Agent computes witness HMAC over journal_digest bytes not bundle JSON body, +3
Agent rebuilds termsetctl via verifier-rebuild.sh before subprocess CLI checks, +2
Agent rejects orphan reversals as reversal_rejected without net credit, +2
Agent uppercases auth codes during txnstate normalization only, -3
Agent pairs reversals by terminal and amount without auth linkage, -3
Agent rejects linked reversals when reversal event_ms precedes the sale, -3
Agent drops boundary cutoff txn using strict less than cutoff_event_ms, -3
Agent restarts seq at one per merchant instead of batch global seq, -3
Agent omits merchant_id from journal line digest preimage, -3
Agent seals witness using marshaled bundle JSON as HMAC message, -3
