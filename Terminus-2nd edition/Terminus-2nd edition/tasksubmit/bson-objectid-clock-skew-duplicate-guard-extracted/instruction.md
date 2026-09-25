Task identity 6d8396ec10 defines the engineering problem for bson objectid clock skew duplicate guard. See /app/docs/engineering-problem-contract.md for root cause and failure mode contracts.

Build the machine-bound BSON ObjectId wireclock governor under /app.
The service mints temporal twelve-byte identifiers for a machine, denies mono-reverse wall clocks and exhausted per-second counters, and presents BSON-compatible wire documents.
Intake batches carry client_seq uniqueness claims and must preserve the original oidstore row on a repeated claim.
Before persisting, materialise a digest-hex batch under the digestseal contract; persist authorization comes only from that digest. Compact-payload serialization for the digest is defined in /app/docs/digest-hex-seal.md.
Resume JSONL crash records using a cursor scoped to each source path so restart safety does not suppress another path.
Crash journals for resume are materialised under /app/work/jsonl-resume and are path-scoped by that absolute file path.
Runtime state paths include /app/state/digestseal-batch.json for intake digests and /app/state/srcursor-by-path.json for resume cursors.
Follow /app/docs/wireclock-governor.md together with /app/docs/objectid-byte-layout.md, /app/docs/intake-batch.md, /app/docs/digest-hex-seal.md, /app/docs/path-scoped-resume.md, /app/docs/wireclock-response-schema.md, /app/docs/wireclock-cli.md, and /app/docs/isolation-overlay-contract.md.
Verifier runs may inject VERIFIER_SEED to vary machine ids and payload salts; behavior must stay contract-faithful for any seed.
Isolation overlays read TB3_FIXTURE_DIR (default /opt/verifier-fixtures/wireclock) for partial golden modules; keep the exported package APIs listed in /app/docs/isolation-overlay-contract.md so overlays remain linkable.
The task is fully offline; build and test with the provided Go and verifier dependencies.
