# Platform rubric — bash-steamcmd-workshop-dependency-toposort-repair

**Task folder:** tasks/bash-steamcmd-workshop-dependency-toposort-repair/

Agent implements numeric semver comparison in deps.sh not ASCII ordering, +3
Agent writes parsed-manifest.tsv and staging-meta.json with matching sha256 digest, +3
Agent builds required-edge graph dependency to dependent for Kahn sort, +3
Agent emits contract cycle path following first outgoing adjacency edge, +3
Agent validates staging digest in export_plan.sh before writing plan JSON, +3
Agent maintains run-seq.json with input fingerprint across reruns, +2
Agent applies layer-by-layer Kahn batch sort with ASCII tie breaks, +2
Agent routes ingest through manifest_ingest.sh staging commit on hot path, +2
Agent ignores decoy legacy_mount and decoy_topo modules off workshop-plan path, +1
Agent patches only topo.sh while leaving deps semver ASCII broken, -3
Agent fixes cycle path but skips staging digest validation on export, -3
Agent trusts contradictory cycle example over dependency-first adjacency contract, -2
Agent reverses mount_order topological direction for dependency-first output, -2
Agent writes staging artifacts under /app/output instead of /app/state, -2
