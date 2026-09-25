# Seal HMAC contract

Output paths:
- /app/output/settlement-bundle.json
- /app/output/settlement-witness.hmac

## Settlement bundle

Fields: engine, scenario, batch_id, terminal_key_id, journal_digest, net_amount_cents, settled_count, bundle_version.

net_amount_cents sums amount_cents for journal lines in state settled minus amount_cents for lines in state reversal_applied.

settled_count counts journal lines in state settled only.

journal_digest must match the digest in journal-meta.json.

## HMAC attestation

settlement-witness.hmac is lowercase hex HMAC-SHA256 where the key is the scenario terminal_key_hex decoded from hex and the message is the journal_digest string bytes.

The attestation must not be computed over the bundle JSON body.
