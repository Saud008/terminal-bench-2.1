#!/usr/bin/env bash
# Staging snapshot helpers for apply export admission.
tscn_staging_snapshot_path() {
  echo "${TSCN_APP_ROOT:-/app}/output/apply-staging-snapshot.json"
}
