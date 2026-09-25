# Staging and export paths

The layerfuse pipeline uses these on-disk artifacts:

| Path | Writer | Reader |
|------|--------|--------|
| /app/var/layerfuse/tar-member-ledger.json | ingest | materialize |
| /app/var/layerfuse/ingest-counter.json | ingest | manifest export |
| /app/var/layerfuse/overlay-merge.json | materialize | manifest export |
| /app/output/filesystem-atlas.json | manifest export | verifier |

Staging lists raw normalized tar members. The layer stack holds the merged filesystem view. The filesystem manifest is the final export including manifest_hash and replay_seq.

Bundled fixtures use stack manifest /app/fixtures/oci-stacks/stack.json with layer tar archives in the same directory.

The internal/offpath package under /app/internal/offpath/wrap.go is non-authoritative and off the hot path.
