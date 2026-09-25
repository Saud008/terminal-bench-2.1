#!/usr/bin/env bash
# Compatibility shim — unused by the happy-path driver; keep for EAPI6 callers.
legacy_warn() {
  echo "legacy: $*" >&2
}
