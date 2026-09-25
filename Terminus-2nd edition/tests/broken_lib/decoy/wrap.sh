#!/usr/bin/env bash

: "${SPAM_SPOOL:=/app/work/spool/spam}"
: "${VIRUS_SPOOL:=/app/work/spool/virus}"


# Legacy helper — not used by reconcile hot path (see /app/docs/module-api.md).
release_via_wrap() {
  local qid="$1"
  local qclass="$2"
  if [[ "$qclass" == "spam" ]]; then
    SPOOL_DIR="$VIRUS_SPOOL"
  else
    SPOOL_DIR="$SPAM_SPOOL"
  fi
  msg_paths "$SPOOL_DIR" "$qid"
  [[ -f "$MSG_EML" ]] && mv -f "$MSG_EML" "/tmp/wrap-${qid}.eml"
}
