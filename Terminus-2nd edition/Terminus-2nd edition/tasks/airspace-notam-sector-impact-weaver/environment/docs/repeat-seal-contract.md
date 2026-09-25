# Repeat seal contract

Running `seal-atlas` twice without changing lab state must produce a byte-identical `/app/output/impact-closure-atlas.json`, including `atlas_digest`.

`fold-closure` must bump `seal_epoch` on every successful pass so that repeat sealing stays unblocked after the first fold.

Atlas row ordering and the digest key order must remain stable across repeated seals.
