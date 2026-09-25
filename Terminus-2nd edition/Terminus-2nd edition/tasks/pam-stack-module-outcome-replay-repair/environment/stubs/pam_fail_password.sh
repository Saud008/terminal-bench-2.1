#!/usr/bin/env bash
if [[ "${PAM_PHASE:-}" == "password" ]]; then
  exit 1
fi
exit 0
