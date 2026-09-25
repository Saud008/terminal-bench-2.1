# Submission explanations — netlink-rtnl-multipath-topology-witness

**Task folder:** tasks/netlink-rtnl-multipath-topology-witness/
**Platform form only** — not in upload zip.

## Difficulty Explanation


Agents must implement an offline RTNL dump decoder where multipath weight scaling, per-route nexthop id restart, IPv6 minimal text form, table override selection, and export_digest sealing interact across bind, stage-1b guard, NH normalization, and export stages. Partial fixes often produce a report that looks valid while bind or NH snapshots disagree with the sealed digest, or while export silently re-derives rows from the dump instead of the NH snapshot. Bundled dumps plus synthetic combined scenarios and mutation probes punish one-module patches that only pass the happy path.

## Solution Explanation


The oracle replaces the broken bind, decode, export, export_nh, and snapshot_guard implementations, then rebuilds nlctl. Correct binding assigns multipath ids 1.n per route with seed-scaled weights and never attaches route-level metrics to multipath hops. single-path hops keep RTA_NH_ID (or 0) and weight 1. Stage artifacts under /app/state/ must match export_digest, and export reads only the NH snapshot.

## Verification Explanation


test.sh rebuilds nlctl via verifier-rebuild.sh before pytest. The suite recomputes expected digests and address fields from the docs with hashlib, ipaddress, and struct, invokes /usr/local/bin/nlctl decode through subprocess, checks stage artifacts against the sealed report, and uses partial golden/mutated source overlays so fixing one stage alone still fails. NOP on the shipped broken image scores 0. the oracle path scores 1.
