#!/bin/bash
# Export reproducible load-plan JSON from staging.
set -euo pipefail

read_staging_section() {
  local file="$1" section="$2"
  local -n out_lines="$3"
  out_lines=()
  local in_section=0 line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${line}" == "[${section}]" ]]; then
      in_section=1
      continue
    fi
    if [[ "${line}" =~ ^\[.*\]$ ]]; then
      in_section=0
    fi
    if [[ "${in_section}" -eq 1 && -n "${line}" ]]; then
      out_lines+=("${line}")
    fi
  done < "${file}"
}

staging_field() {
  local file="$1" key="$2"
  grep "^${key}=" "${file}" | head -1 | cut -d= -f2- || true
}

plan_digest() {
  local canonical="$1"
  printf '%s' "${canonical}" | sha256sum | awk '{print $1}'
}

write_load_plan_json() {
  local staging="$1" out="$2"
  local -a unload_lines load_lines mutation_lines
  read_staging_section "${staging}" unloads unload_lines
  read_staging_section "${staging}" loads load_lines
  read_staging_section "${staging}" path_mutations mutation_lines
  local schema catalog_digest seq
  schema="$(staging_field "${staging}" schema_version)"
  catalog_digest="$(staging_field "${staging}" catalog_digest)"
  seq="$(staging_field "${staging}" sequence)"
  mkdir -p "$(dirname "${out}")"
  mapfile -t unload_lines < <(printf '%s\n' "${unload_lines[@]-}" | LC_ALL=C sort -u)
  mapfile -t load_lines < <(printf '%s\n' "${load_lines[@]-}" | LC_ALL=C sort -u)
  local mut_json="["
  local i line var op val
  for i in "${!mutation_lines[@]}"; do
    line="${mutation_lines[$i]}"
    IFS='|' read -r var op val <<< "${line}"
    [[ "${i}" -gt 0 ]] && mut_json+=","
    mut_json+=$(printf '{"var":"%s","op":"%s","value":"%s"}' "${var}" "${op}" "${val}")
  done
  mut_json+="]"
  local unload_json load_json
  unload_json="$(printf '%s\n' "${unload_lines[@]-}" | jq -R . | jq -s -c 'sort')"
  load_json="$(printf '%s\n' "${load_lines[@]-}" | jq -R . | jq -s -c 'sort')"
  local body
  body=$(jq -n -c \
    --argjson schema "${schema}" \
    --arg catalog_digest "${catalog_digest}" \
    --argjson sequence "${seq}" \
    --argjson unload_sequence "${unload_json}" \
    --argjson load_sequence "${load_json}" \
    --argjson path_mutations "${mut_json}" \
    '{catalog_digest:$catalog_digest, load_sequence:$load_sequence, path_mutations:$path_mutations, schema_version:$schema, sequence:$sequence, unload_sequence:$unload_sequence}')
  local digest
  digest="$(plan_digest "${body}")"
  jq --arg d "${digest}" '. + {plan_digest: $d}' <<< "${body}" > "${out}"
}
