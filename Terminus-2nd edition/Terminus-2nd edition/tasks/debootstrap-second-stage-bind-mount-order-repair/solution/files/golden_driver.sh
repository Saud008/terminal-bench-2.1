#!/usr/bin/env bash

s2_post_gate_pipeline() {
  local rootfs="$1"
  s2_apply_mount_markers "$rootfs" "$S2_SNAPSHOT_PATH"
  export S2_COMMITTED=1
  s2_run_stage2_hooks "$rootfs" "$S2_HOOKS_JSON"
}
