#!/usr/bin/env bash
# Scaffold: implement per /app/docs/release-policy.md

ledger_already_released() {
  return 1
}

attempt_release() {
  local qid="$1"
  local qclass="$2"
  DUPLICATE_SKIPPED=0
  RELEASE_OK=0
  return 1
}
