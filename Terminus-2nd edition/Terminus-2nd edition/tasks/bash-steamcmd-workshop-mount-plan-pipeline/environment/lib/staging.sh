#!/usr/bin/env bash
# Stage parsed manifest rows (legacy path; digest meta omitted).

staging_commit_parsed() {
  local parsed_file="$1"
  mkdir -p /app/output
  cp "${parsed_file}" /app/output/parsed-manifest.tsv
}
