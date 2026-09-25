# Trust bind policy

cipgate binds each Cosign-style attestation envelope to Fulcio-style trust roots before any authz gate may admit it.

## Trust root fields

Each root under the configured trust-roots directory provides:

- `root_id` — stable identifier
- `issuer_glob` — full-string anchored glob (`*` wildcard segments)
- `subject_glob` — full-string anchored glob

## Bind rule

An envelope **binds** a root when both `issuer_glob` and `subject_glob` match the envelope `issuer` and `subject` respectively. Matching is full-string anchored (not substring). An envelope may bind multiple roots; any successful bind counts as trusted.

## Digest normalization

Strip an optional `sha256:` prefix and lowercase hex before comparing subject digests or image digests.

The image digest for a pull is the substring after the final `@` in the `image` reference, then normalized.
