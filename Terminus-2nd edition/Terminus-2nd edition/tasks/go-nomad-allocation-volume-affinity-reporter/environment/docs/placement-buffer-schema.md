# Placement buffer schema

Each nomrep load writes /app/var/placement-buffer.json with:

- load_seq: monotonic counter incremented on every load for the same buffer path
- seed: caller seed string
- scenario: scenario name
- focus_alloc_id: scoped allocation id for the scenario focus
- job_id and task_group: copied from the scenario bundle
- stale_cutoff_index: modify_index floor for active allocations after drain
- csi_volumes: volume catalog rows from the scenario
- allocations: scoped allocation rows materialized from the scenario

Every allocation row includes alloc_id, node_id, node_class, create_index, modify_index, client_status, desired_status, reschedule_attempts, reschedule_failed, csi_mounts, constraints, affinities, and superseded_by.
