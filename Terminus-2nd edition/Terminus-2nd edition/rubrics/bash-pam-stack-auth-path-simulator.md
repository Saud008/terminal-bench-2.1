# Platform rubric — bash-pam-stack-auth-path-simulator

**Task folder:** tasks/bash-pam-stack-auth-path-simulator/

Agent ingests offline PAM scenario bundles into run-scoped work metadata, +2
Agent expands @include paths relative to the including service file directory, +3
Agent expands @include-substack once without duplicating substack modules, +3
Agent freezes verdict on requisite non-success while still appending later auth steps, +3
Agent keeps sufficient success from clearing prior required failures, +3
Agent resolves module outcomes by module basename per subject table, +2
Agent seeds subject username into nested group closure before parent expansion, +3
Agent writes pamtrace-ledger.json with per-service module fingerprints, +2
Agent simulates auth stack from ledger modules in execution index order, +3
Agent exports trace steps in index order not sorted by module name, +3
Agent emits trace_digest over service subject steps and verdict, +2
Agent reads TB3 hidden scenarios for requisite and group closure traps, +2
Agent rebuilds pamtrace via rebuild-pamtrace.sh before pytest, +1
Agent leaves rhel6_bridge decoy off ingest and export hot path, +1
Agent resolves @include from scenario root instead of service directory, -3
Agent duplicates substack modules on nested @include-substack, -3
Agent truncates steps on requisite auth_err or keeps applying later control flags after it, -3
Agent allows sufficient success after required module failure, -3
Agent exports subject_groups without seeding the subject username or skipping parents, -3
Agent sorts trace steps alphabetically by module basename, -3
Agent uses non-canonical Dockerfile base image, -5
