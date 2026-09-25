Supply-chain security operators need a host-local TUF metadata trust-admission control plane at `/app/bin/tufctl`. The plane admits offline signed root, targets, and snapshot metadata from a directory, stages a tamper-evident delegation snapshot at `/app/state/tuf-staging.json`, evaluates threshold-signature authenticity and rotation linkage at a caller-supplied epoch, and publishes a digest-bound delegation decision attestation to `/app/output/delegation-report.json` with companion rejected-target evidence at `/app/output/rejected-targets.jsonl`—without a live repository mirror or outbound network step. This is a security metadata-attestation and rotation-admission workflow: keep canonical signed-byte authenticity, threshold quorum counting, key temporal validity, delegated path-scope admission, snapshot-to-targets version coupling, root-key reuse bans on targets signatures, and sealed report export aligned. It is not a generic Rust CLI engineering, cargo rebuild, or CI tooling exercise.

Security contracts under `/app/docs/`: `canonical-json.md` for signed-byte authenticity; `threshold-signatures.md` for quorum trust counting; `key-expiry-epochs.md` for temporal key validity at the verification epoch; `delegation-paths.md` for delegated path-scope admission; `snapshot-version-link.md` for snapshot-to-targets version coupling; `key-reuse-ban.md` for root-role keyid reuse bans on targets signatures; `delegation-report-schema.md` for sealed attestation shape and rejected-target evidence.

`tufctl` must expose:

```text
tufctl ingest <metadata-dir>
tufctl verify rotation --epoch <n> [--staging <path>]
tufctl export report
```

`ingest` must normalize admitted metadata into `/app/state/tuf-staging.json` with metadata versions, flattened keys, delegations, targets, and `ingest_seq` monotonic across repeated ingest calls. `verify rotation` must write `/app/state/verify-result.json` with `rotation_ok`, `epoch`, and per-metadata signature authenticity outcomes. `export report` must read staging and verify-result only, then seal `/app/output/delegation-report.json` and companion rejected-target evidence at `/app/output/rejected-targets.jsonl` per the report-schema contract.

Bundled fixtures live under `/app/data/metadata` without extra path suffixes. When hidden verifier fixtures supply additional metadata trees, admit from those roots. When `TB3_EPOCH_BIAS` is set, verification epoch offset uses that bias. After authenticity-policy edits under `/app/src/`, leave `/app/bin/tufctl` current. Do not edit `/app/docs/`, `/app/data/`, or `/tests/`.
