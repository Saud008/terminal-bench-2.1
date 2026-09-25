#!/usr/bin/env bash
# Delivery environment variables and rc SET handling.
# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

ENV_HOST=""
ENV_HOSTNAME=""
ENV_ORGMAIL=""

env_load_meta() {
  local suite="$1"
  ENV_HOST="$(jq -r '.host // ""' "${suite}/suite.meta.json")"
  ENV_HOSTNAME="$(jq -r '.hostname // ""' "${suite}/suite.meta.json")"
  ENV_ORGMAIL="$(jq -r '.orgmail // ""' "${suite}/suite.meta.json")"
}

env_apply_set() {
  local line="$1"
  [[ "$line" == SET\ * ]] || return 0
  local pair="${line#SET }"
  local name="${pair%%=*}"
  local val="${pair#*=}"
  name="$(pm_trim "$name")"
  val="$(pm_trim "$val")"
  case "$name" in
    HOST) ENV_HOST="$val" ;;
    HOSTNAME) ENV_HOSTNAME="$val" ;;
    ORGMAIL) ENV_ORGMAIL="$val" ;;
  esac
}

env_match_var_cond() {
  local token="$1"
  local headers="$2"
  local needle=""
  token="${token#\?}"
  token="$(pm_trim "$token")"
  case "$token" in
    '$HOSTNAME') needle="$ENV_HOST" ;;
    '$HOST') needle="$ENV_HOST" ;;
    *) return 1 ;;
  esac
  [[ -n "$needle" && "$headers" == *"$needle"* ]]
}
