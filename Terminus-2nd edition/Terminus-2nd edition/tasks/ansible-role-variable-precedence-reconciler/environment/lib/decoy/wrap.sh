#!/usr/bin/env bash
# Decoy merge helper — not referenced by ansible-var-merge resolve hot path.
merge_shallow_decoy() {
  printf '%s' "$2"
}
