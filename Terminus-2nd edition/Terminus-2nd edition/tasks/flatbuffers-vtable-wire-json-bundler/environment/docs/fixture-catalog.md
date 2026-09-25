# Fixture catalog

Bundled buffers under `/app/fixtures/buffers/`:

| File                 | Root type | Notes                                      |
|----------------------|-----------|--------------------------------------------|
| `shallow.bin`        | Scene     | Basic entity with metrics                  |
| `nested-chain.bin`   | Scene     | Three-level parent chain                   |
| `tags-mixed.bin`     | Scene     | Tags on root; parent without tags          |
| `struct-pad.bin`     | Scene     | Long name forces Vec3 alignment padding    |
| `deep-nest.bin`      | Scene     | Four-level parent chain                    |
| `many-tags.bin`      | Scene     | Six tag entries in vector                  |
| `metrics-defaults.bin` | Scene   | Metrics with default flag_count            |
| `long-name-nest.bin` | Scene     | Nested parent with long-name padding       |
| `tags-order.bin`     | Scene     | Tag vector in non-alphabetical key order   |
| `combo-nest-tags.bin`| Scene     | Nested chain, padding, tags, and metrics   |
| `truncated.bin`      | Scene     | Truncated copy of shallow.bin              |

All fixtures use `/app/schema/scene.fbs` as the agent schema contract. Verifier flatc parity uses the immutable copy at `/opt/verifier-schema/scene.fbs`. The schema file under `/app/schema/` must not be modified.

## Fixture SHA-256 digests

| Relative path | SHA-256 |
|---------------|---------|
| fixtures/buffers/shallow.bin | e8f4964f01a701fae4678d2b874b4a1585622eb993cfa0ba00e7444a8158445c |
| fixtures/buffers/nested-chain.bin | 81415c86c2595d3a501c7bf13f788fc393666e9af6b282a1e6e7dc010d667d81 |
| fixtures/buffers/tags-mixed.bin | 7e2a6a08343e4f4123fec97edc5675baceffbbf7a87b1956fa3bb344b65cd128 |
| fixtures/buffers/struct-pad.bin | 35e1c5a17713a1bda4d065bc376590094f424032cd4091f897abb66f44b7c3b4 |
| fixtures/buffers/deep-nest.bin | 7efbe23423f109e3deb534835ed215bad9bcbd6c9bb56c104c763bb5d42a9140 |
| fixtures/buffers/many-tags.bin | 4821d8c721041ec4d6437fe92433346ac73ad7fed598389917436a6914cffd72 |
| fixtures/buffers/metrics-defaults.bin | 03635dd599f9097e14aad92726815c3020b014e86503d495de3b4d835846b4bb |
| fixtures/buffers/long-name-nest.bin | ed375e68d380a38102a223518f24fcb51211d344dd601ba1fbca69dc5630eac7 |
| fixtures/buffers/tags-order.bin | d513bd9429439c3de45bdd21794ad3fbcb791a986578d6f688a80cb2cac87c7d |
| fixtures/buffers/combo-nest-tags.bin | 691ef74d199161b4aa0b8c23339c53a26bb9946b9d7d69eee8e10c205bc20df0 |
| fixtures/buffers/truncated.bin | 8c5b726477ef2f2aeb80c8330a4f8bc42c57d78e4af47d6eda3a7780a024b80c |

Use `/app/scripts/wire_hash_helper.py` for SHA-256 over fixture bytes. Sixteen-hex digest strings use charset `0123456789abcdef`.

## Verifier seeds

| Name | Value |
|------|-------|
| default | fb-vtable-seed-7 |
| procedural | fb-matrix-13, fb-matrix-42, fb-matrix-88, fb-matrix-101, fb-matrix-204 |

Environment variable VERIFIER_SEED overrides the default procedural seed.

## State and verifier paths

| Path | Role |
|------|------|
| /app/state/decode.snapshot.json | Wire snapshot envelope |
| /app/state/decode.ledger.jsonl | Decode journal lines |
| /opt/verifier-broken-fbdecode | Broken module snapshots for partial-fix probes |
| /tmp/procedural-scene.bin | Procedural buffer scratch path |

## Hidden verifier buffers

Procedural scratch files may use names such as procedural-scene.bin under /tmp/procedural-scene.bin.

Hidden trap buffers include hidden-absent-tags.bin, hidden-absent-tags-stage.bin, hidden-tag-order.bin, hidden-deep-parent.bin, and hidden-combo-trap.bin.

## Verifier helper paths

Pytest may reference bundled verifier trees under tests/fault_lib and tests/verifier_ref_lib. Harness scripts include scripts/reset-state.sh and scripts/verifier-rebuild.sh. Rust modules under src/ include cv20.rs, ft26.rs, hn55.rs, je67.rs, kx42.rs, mp93.rs, qg71.rs, rw14.rs, st38.rs, ul82.rs, yl49.rs, and zq81.rs.

