# Export schema

job-activation-export.json fields:

process_id string, partition_id integer, activation_sequence array of objects with job_key, activated_at_ms, deadline_ms, barrier, sequence_no integer starting at 1.

boundary_events array with boundary_id, attached_element, fired_at_ms, interrupting boolean.

variable_snapshot object with working map and resolved_outputs map.

duplicate_activations_skipped integer.

deadline_clock_source string process.
