Release-approval operators run the host-local twctl witness ledger ops desk at /app/bin/twctl. Each offline ops pass admits a release bundle, stages a normalized approval snapshot, applies round quorum and signer-window gates, then publishes a sealed release-witness ledger only from that staging snapshot and quorum verdict. There is no remote signing service and no outbound network. This is a system-administration host-local release-approval ops desk (admit -> gate -> seal). It is not a security product audit, cryptographic library rewrite, debugging exercise, or software-engineering module-repair task.

Primary artifacts:

  /app/state/tw-approval-stage.json - staging snapshot written by load
  /app/state/quorum-verdict.json - round gate result written by check
  /app/output/release-witness-ledger.json - sealed export written by emit

Runtime paths are fixed in /app/docs/runtime-paths.md. Build /app/bin/twctl from the workspace root:

  twctl load <bundle-dir>
  twctl check --epoch <n> [--staging <path>]
  twctl emit

load admits one bundle directory and writes /app/state/tw-approval-stage.json with bundle_dir, policy quorum, keys, revocations, witness rows, artifact digest from bundle bytes, ingest_seq incremented each load, and replay_deduped from the latest merge.

check reads staging and writes /app/state/quorum-verdict.json with quorum_met, round, valid_witness_count, replay_deduped, provenance_ok, and per-witness outcomes at the effective verification round including TB3_EPOCH_BIAS when set.

emit reads staging and quorum-verdict only. It never re-reads witness JSON from the bundle directory. It writes /app/output/release-witness-ledger.json per /app/docs/ledger-export-schema.md.

Ops contracts under /app/docs/ state the enforceable invariants: canonical-message-binding.md, quorum-policy.md, revocation-epochs.md, witness-provenance.md, replay-idempotency.md, and ed25519-threshold-witness-contract.md.

The wrap merge helper under src/wrap is not on the load or emit hot path. The decoy_bundle_hash module is diagnostic-only.

Bundled fixtures: /app/data/bundles/release-alpha (see /app/docs/fixture-catalog.md). Hidden bundles: /opt/verifier-fixtures/witness-bundles

Verifier tests import tw1_independent_math.py for independent PyNaCl TW1 math using hashlib and nacl modules. Do not edit /app/docs/, files under /app/data/, or files under /tests/.
