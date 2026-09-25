# Platform rubric — go-nomad-allocation-volume-affinity-reporter

**Task folder:** tasks/go-nomad-allocation-volume-affinity-reporter/

Agent increments ingest_seq on repeat nomrep ingest for the same staging path, 3
Agent joins CSI mounts using namespace/volume_id keys with optional TB3_NAMESPACE_SALT, 3
Agent filters hard node.class constraints before affinity soft ranking, 3
Agent suppresses stale allocations by modify_index cutoff and superseded_by, 3
Agent sums reschedule_attempts only when reschedule_failed is true, 2
Agent replaces the active allocation index row when curating a later scenario for the same seed, 2
Agent exports audit_digest with sorted volume_keys and placement_ranks canonical JSON, 3
Agent rebuilds nomrep after Go source edits, 2
Agent uses ingest curate index export hot path without decoy placement scorer, 1
Agent ranks placements before applying hard node class constraints, -3
Agent uses create_index instead of modify_index for stale suppression, -3
Agent joins volumes on bare volume_id without namespace prefix, -2
Agent counts all reschedule attempts regardless of reschedule_failed flag, -2
Agent leaves ingest_seq fixed at one on repeat ingest, -2
