#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOD="${ROOT_DIR}/files/modules"

install -d -m 0755 /app/lib/nsio /app/lib/imgref /app/lib/leaseio /app/lib/snapgc /app/lib/planemit

cp -f "${MOD}/ctgc-ns-filter.sh" /app/lib/nsio/meta_loader.sh
cp -f "${MOD}/ctgc-dangling-ref.sh" /app/lib/imgref/manifest_index.sh
cp -f "${MOD}/ctgc-lease-shield.sh" /app/lib/leaseio/lease_shield.sh
cp -f "${MOD}/ctgc-ancestor-keep.sh" /app/lib/snapgc/ancestor_keep.sh
cp -f "${MOD}/ctgc-resolve-emit.sh" /app/lib/planemit/topo_order.sh

chmod +x /app/lib/nsio/meta_loader.sh \
  /app/lib/imgref/manifest_index.sh \
  /app/lib/leaseio/lease_shield.sh \
  /app/lib/snapgc/ancestor_keep.sh \
  /app/lib/planemit/topo_order.sh

_ctgc_verify_layout() {
  grep -q '_filter_ns_assets' /app/lib/nsio/meta_loader.sh
  grep -q 'find_dangling_images' /app/lib/imgref/manifest_index.sh
  grep -q '_descendants_of' /app/lib/leaseio/lease_shield.sh
  grep -q '_ancestors_of' /app/lib/snapgc/ancestor_keep.sh
  grep -q 'resolve_gc_eligibility' /app/lib/planemit/topo_order.sh
}
_ctgc_verify_layout

bash /app/scripts/rebuild-ctrgc.sh

ctgc_wipe() { rm -f /app/state/gc_snapshot.json /app/state/eligibility.buffer /app/output/namespace_gc_plan.json /app/state/revision.seq; }
ctgc_wipe

/bin/bash /app/lib/cli.sh scan-meta --meta-root /app/fixtures/meta-basic --namespace k8s.io --out /app/state/gc_snapshot.json
/bin/bash /app/lib/cli.sh resolve --gc-snapshot /app/state/gc_snapshot.json --now 2000000000 --out /app/state/eligibility.buffer
/bin/bash /app/lib/cli.sh emit-plan --eligibility-buffer /app/state/eligibility.buffer --out /app/output/namespace_gc_plan.json

_ctgc_assert_plan_shape() {
  jq -e '.schema_version == 1 and .mode == "dry-run"' /app/output/namespace_gc_plan.json >/dev/null
  jq -e '.actions | type == "array"' /app/output/namespace_gc_plan.json >/dev/null
  jq -e '.plan_digest | type == "string" and length > 0' /app/output/namespace_gc_plan.json >/dev/null
  jq -e '.resolve_digest | type == "string" and length > 0' /app/state/eligibility.buffer >/dev/null
}
_ctgc_assert_plan_shape

test -s /app/output/namespace_gc_plan.json
echo "ctrgc oracle smoke ok"
