#!/usr/bin/env bash

run_src_install() {
  local tree="$1"
  trace_reset
  trace_step "doins"
  doins_tree "${tree}"
  trace_step "qa_preflight"
  qa_run_preflight "${tree}"
  trace_step "normalize_d"
  normalize_d_tree
  trace_step "dosbin"
  dosbin_strip "${tree}"
  trace_step "fperms"
  apply_fperms "${tree}"
  trace_step "qa_postflight"
  qa_run_postflight "${tree}"
}

run_src_test() {
  local tree="$1"
  local kind path expect_exec msg
  kind="$(jq -r '.src_test.kind // "none"' "${tree}/manifest.json")"
  case "${kind}" in
    none) return 0 ;;
    path_test)
      path="$(jq -r '.src_test.path' "${tree}/manifest.json")"
      expect_exec="$(jq -r '.src_test.executable // false' "${tree}/manifest.json")"
      if [ ! -e "${D}/${path}" ]; then
        echo "src_test: missing ${path}" >&2
        return 1
      fi
      if [ "${expect_exec}" = "true" ] && [ ! -x "${D}/${path}" ]; then
        echo "src_test: not executable ${path}" >&2
        return 1
      fi
      ;;
    die_subshell)
      msg="$(jq -r '.src_test.message // "forced die"' "${tree}/manifest.json")"
      (
        ebuild_die "${msg}"
      )
      ;;
    forced_fail)
      echo "src_test: forced failure" >&2
      return 1
      ;;
    *)
      echo "unknown src_test kind ${kind}" >&2
      return 1
      ;;
  esac
}

run_full() {
  local tree="$1"
  local name
  name="$(jq -r '.name' "${tree}/manifest.json")"
  run_src_install "${tree}"
  if run_src_test "${tree}"; then
    merge_record_write "${tree}" "merged"
  else
    merge_record_write "${tree}" "failed"
  fi
}
