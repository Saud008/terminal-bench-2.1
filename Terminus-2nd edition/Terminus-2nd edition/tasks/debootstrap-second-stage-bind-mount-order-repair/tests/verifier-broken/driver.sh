#!/usr/bin/env bash
# Broken: chroot hooks run before mount commit flag and markers exist.

s2_post_gate_pipeline() {
  local rootfs="$1"
  s2_run_stage2_hooks "$rootfs" "$S2_HOOKS_JSON"
  export S2_COMMITTED=1
}
