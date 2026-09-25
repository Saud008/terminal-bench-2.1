# Exposure ledger schema

exposure-ledger.json fields:

- bundle_id: string copied from waiver-snapshot.json
- export_digest: sha256 hex over canonical impact bytes
- impacts: array sorted by binary asc, then package_purl asc, then vuln_id asc

Each impact row:

- binary: deployed binary name
- package_purl: norm_purl of reachable package
- vuln_id: vulnerability identifier string
- effective_status: string from VEX precedence
- reachable: always true for emitted rows
- waiver: null or object with statement_id and optional expires_at when not_affected or fixed wins

Roll-up must read waiver-snapshot.json only. Bundle capture must never embed impact rows inside the snapshot fingerprint input.
