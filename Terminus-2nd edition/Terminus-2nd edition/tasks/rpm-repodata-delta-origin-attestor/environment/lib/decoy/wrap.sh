#!/usr/bin/env bash
# Decoy attestation helper — not referenced by rpm-repo-attest ingest or export hot path.
merge_decoy_digest() {
  printf '%s' "$2"
}
