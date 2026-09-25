#!/usr/bin/env bash
# Drive letter validation.

validate_drive_letter() {
  local drive="$1"
  if [[ ${#drive} -ne 1 ]]; then
    return 1
  fi
  if [[ ! "$drive" =~ ^[A-Z]$ ]]; then
    return 1
  fi
  return 0
}
