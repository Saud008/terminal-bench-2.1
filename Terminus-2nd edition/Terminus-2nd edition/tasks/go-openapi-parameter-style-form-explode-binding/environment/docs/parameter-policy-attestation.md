# Parameter policy attestation

Paramgate is a host-local API-edge trust admission gate. Each inbound request is evaluated against the merged OpenAPI trust contract before a sealed response is emitted.

## Policy workflow

1. Load and merge base plus admin OpenAPI fragments at startup.
2. Bind query, path, header, and body fields per style and explode rules in `/app/docs/param-binding-contract.md`.
3. Canonicalize bound maps per `/app/docs/canonical-bind-order.md`.
4. Stage a witness snapshot at `/app/state/bind-snapshot.json` per `/app/docs/bind-snapshot.md`.
5. Emit HTTP responses from the staged witness, not from transient parser maps.

## Trust boundaries

Tampered or malformed client encodings are policy violations. Missing required parameters, bad content types, and invalid encodings must return HTTP 400 with a reason code. Unexpected internal faults return HTTP 500 only.

## Attestation artifact

The bind snapshot is the authoritative witness for successful policy evaluation. Response JSON must bind params (and optional body) to the staged snapshot contents.

See `/app/docs/bind-api.md` for HTTP surface details.
