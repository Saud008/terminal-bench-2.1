The sprite atlas packer at `/usr/local/bin/atlaspack` builds PNG atlases and JSON manifests from catalogs under `/app/fixtures/`, but its outputs disagree with `/app/docs/atlas-contract.md`, `/app/docs/manifest-schema.md`, and `/app/docs/exit-codes.md` for padding, UV sampling, rotation, scaling, checksum export, and CLI exit behavior.

Repair the Rust implementation under `/app/crates/` so `pack` and `probe` match those documents, including exit codes from `/app/docs/exit-codes.md`. Rebuild and reinstall the `atlaspack` binary from `/app` after source edits. Run `/app/scripts/reset-state.sh` before local checks.

Do not edit `/app/docs/`, `/app/fixtures/`, or `/tests/`.
