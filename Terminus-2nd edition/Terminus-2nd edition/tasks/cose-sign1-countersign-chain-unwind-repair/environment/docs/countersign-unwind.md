# Counter-signature unwind

Unwind walks the counter-signature array in **array index order** (creation order). Do not reorder by kid or alg before verification.

For each counter-signature entry:

1. Build Sig_structure per cose-sign1.md with empty payload.
2. Verify signature using the alg from that entry's protected headers against the trust anchor map bundled in the fixture metadata sidecar (embedded in payload JSON when payload decodes as UTF-8 JSON with a "anchors" object).
3. Record kid, alg, verify_ok, and index in the unwind trace.

Partial chains: if the outer Sign1 signature verifies but one or more counter-signatures fail, the chain entry must still appear in export with outer_ok true, countersign_ok false, and the unwind trace listing per-index results. Do not drop the entire entry.

Trust anchors map kid string to hex-encoded raw public key bytes (32 bytes Ed25519, 65 bytes uncompressed P-256).
