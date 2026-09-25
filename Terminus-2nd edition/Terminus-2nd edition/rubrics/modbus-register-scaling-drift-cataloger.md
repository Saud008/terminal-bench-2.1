# Platform rubric — modbus-register-scaling-drift-cataloger

**Task folder:** tasks/modbus-register-scaling-drift-cataloger/

Agent rebuilds modbusctl with go build after internal package edits, +2
Agent implements modbusctl ingest to write poll-staging.json with frames_digest, +3
Agent decodes signed int32 register pairs with big-endian and little-endian word order, +3
Agent selects scale revision epoch using received_ms not device clock time, +3
Agent rejects poll frames whose device clock skew exceeds manifest clock_skew_ms, +2
Agent applies alarm suppression windows to force drift_alarm false during configured intervals, +3
Agent honors per-register manifest overrides for word order scale epoch and clock skew, +3
Agent validates staging digest and catalog generation before drift catalog export, +3
Agent writes rejected-frames.jsonl with stale_device_clock reason for skew violations, +2
Agent leaves decode decoy helpers off catalog export hot path, +1
Agent patches export sorting only while staging digest validation stays disabled, -3
Agent fixes word order decode but leaves scale epoch bound to device_clock_ms, -3
Agent edits decoy.go expecting drift catalog totals to change without catalog edits, -2
Agent accepts stale device clocks when skew exceeds manifest limit, -2
Agent skips go build after editing internal catalog or decode packages, -2
