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
  grep "^${key}=" "${file}" | head -1 | cut -d= -f2-
}

plan_digest() {
  local canonical="$1"
  printf '%s' "${canonical}" | sha256sum | awk '{print $1}'
}

write_load_plan_json() {
  local staging="$1" out="$2"
  local -a unload_list load_list mutation_list
  read_staging_section "${staging}" unloads unload_list
  read_staging_section "${staging}" loads load_list
  read_staging_section "${staging}" path_mutations mutation_list
  local schema catalog_digest seq
  schema="$(staging_field "${staging}" schema_version)"
  catalog_digest="$(staging_field "${staging}" catalog_digest)"
  seq="$(staging_field "${staging}" sequence)"
  mkdir -p "$(dirname "${out}")"
  # Baseline: export JSON sequences not lexicographically sorted.
  local mut_json="["
  local i line var op val
  for i in "${!mutation_list[@]}"; do
    line="${mutation_list[$i]}"
    IFS='|' read -r var op val <<< "${line}"
    [[ "${i}" -gt 0 ]] && mut_json+=","
    mut_json+=$(printf '{"var":"%s","op":"%s","value":"%s"}' "${var}" "${op}" "${val}")
  done
  mut_json+="]"
  local unload_json unload_first=1
  unload_json="["
  for m in "${unload_list[@]}"; do
    [[ "${unload_first}" -eq 0 ]] && unload_json+=","
    unload_json+=$(printf '"%s"' "${m}")
    unload_first=0
  done
  unload_json+="]"
  local load_json load_first=1
  load_json="["
  for m in "${load_list[@]}"; do
    [[ "${load_first}" -eq 0 ]] && load_json+=","
    load_json+=$(printf '"%s"' "${m}")
    load_first=0
  done
  load_json+="]"
  local body
  body=$(cat <<EOF
{"schema_version":${schema},"catalog_digest":"${catalog_digest}","sequence":${seq},"unload_sequence":${unload_json},"load_sequence":${load_json},"path_mutations":${mut_json}}
EOF
)
  local digest
  digest="$(plan_digest "${body}")"
  printf '%s\n' "${body}" | jq --arg d "${digest}" '. + {plan_digest: $d}' > "${out}"
}
