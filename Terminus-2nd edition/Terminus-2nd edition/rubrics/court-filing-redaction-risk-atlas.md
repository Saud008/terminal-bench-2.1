# Platform rubric — court-filing-redaction-risk-atlas

**Task folder:** tasks/court-filing-redaction-risk-atlas/

Agent binds filing bundle into bundle-staging.json with docket-inclusive fingerprint, +3
Agent expands party alias reachability across indirect alias edges, +3
Agent parses exhibit sub-references such as Exhibit 12-A, +3
Agent normalizes sealed terms with case fold and hyphen collapse, +3
Agent records page-line citation anchors with non-zero line numbers, +3
Agent selects canonical docket rows over latest filed duplicates, +3
Agent blocks emit-atlas when index_revision is zero, +2
Agent sorts atlas findings by finding_id ascending, +2
Agent produces byte-identical atlas on idempotent second emit, +2
Agent reads TB3 hidden fixtures for alias cycle and nested sealed traps, +2
Agent rebuilds filingatlas via verifier-rebuild.sh before pytest, +1
Agent leaves telemetry decoy off atlas export hot path, +1
Agent resolves only direct aliases skipping reachability expansion, -3
Agent matches sealed terms case-sensitively without hyphen fold, -3
Agent emits findings with line zero when text matches a known line, -3
Agent keeps wrong docket when canonical duplicate exists, -3
Agent exports atlas before index-parties increments revision, -3
Agent uses non-canonical Dockerfile base image, -5
