#!/usr/bin/env bash
if [[ "${PAM_PHASE:-}" == "account" ]]; then
  exit 1
fi
exit 0
