# Transcript vault snapshot

Path: /app/state/transcript-vault.json

Fields: engine, scenario, timeline, tokens, policy, transcript_digest.

Each verification decision includes token_id, verdict (accept or reject), and reason_code per governance-report-contract.md.

transcript_digest is SHA-256 hex of stable JSON object with keys policy, scenario, timeline, tokens sorted at root using compact separators.

## Timeline epoch sequence

load-transcript must normalize jwks_timeline.jsonl into ascending epoch order (lowest epoch first) before writing transcript-vault.json.

The timeline array stored in transcript-vault.json must remain in ascending epoch order.

transcript_digest must hash the timeline array in that same ascending epoch order. Input file line order does not affect the digest; only the normalized ascending epoch sequence is hashed.

Hydrate-cache walks timeline events in ascending epoch order when building the cache snapshot.
