# Host-local sledtool pagestore staging ops control plane

Policy modules under `/app/lib/sled/` implement batch admission, publish barriers, page-registry checksums, split-journal ordering, compaction pin gates, and sealed export. The CLI wrapper is `/app/scripts/sledtool` → `python3 -m sled.cli`.
