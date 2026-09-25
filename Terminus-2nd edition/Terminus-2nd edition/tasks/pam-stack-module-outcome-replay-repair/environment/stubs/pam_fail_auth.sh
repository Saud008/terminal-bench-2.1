#!/usr/bin/env bash
if [[ "${PAM_PHASE:-}" == "auth" ]]; then
  exit 1
fi
exit 0
