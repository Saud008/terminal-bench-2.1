# Platform rubric — go-mqtt-retained-message-session-curator

**Task folder:** tasks/go-mqtt-retained-message-session-curator/

Agent implements wildcard MQTT topic matching with plus and hash rules, +3
Agent applies retained overwrite and empty-payload delete semantics, +3
Agent tracks QoS1 and QoS2 inflight retry without duplicate offline rows, +3
Agent enforces session expiry before subscribe and delivery processing, +3
Agent emits subscription atlas sorted by client filter and topic, +2
Agent writes offline delivery ledger with monotonic delivery_seq, +2
Agent requires positive curator_seal before emit-atlas export, +3
Agent produces byte-stable atlas and ledger on idempotent replay, +3
Agent reads session expiry bias from TB3_SESSION_EXPIRY_MS when set, +2
Agent ignores events after connect_ms plus session_expiry_ms window, +2
Agent applies wildcard and retained rules per /app/docs/wildcard-match-contract.md and /app/docs/retained-store-contract.md, +2
Agent derives subscription atlas rows from reconciled staging snapshot bytes, +1
Agent mishandles hash wildcard as single-level only, -3
Agent drops retained delete on empty payload with retain flag, -3
Agent duplicates offline ledger rows on QoS retry before ack, -3
Agent exports atlas without curator seal increment, -3
Agent runs emit-atlas before merge-session writes positive curator seal, -3
