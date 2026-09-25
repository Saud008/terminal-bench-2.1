# Platform rubric — bash-kernel-kconfig-fragment-attestor

**Task folder:** tasks/bash-kernel-kconfig-fragment-attestor/

Agent implements kcfgattest compile-stage staging with correct fragment basename ordering, +3
Agent applies dependency requires and implies closure to after_deps symbols, +3
Agent applies selects closure when parent symbols are enabled, +3
Agent scans forbidden_if_set and required_n policy constraints on merged symbols, +2
Agent emits manifest from kcfg-stage.json after_deps without re-reading bundle files, +3
Agent computes reproducible manifest_digest from sorted symbol rows, +2
Agent records stage_digest over run_id bundle fragment_order and symbol_count, +2
Agent parses unset kconfig lines as disabled symbol values, +1
Agent leaves decoy sort helper off compile and emit hot path, +1
Agent uses subprocess CLI invocation in verifier tests, +1
Agent ignores wrong fragment sort direction during merge, -3
Agent skips policy scan for modular forbidden symbols, -3
Agent rebuilds export from live defconfig instead of stage snapshot, -5
Agent omits requires promotion when inet symbols are enabled, -3
Agent drops hidden TB3 select trap for CRC32 implied symbol, -5
