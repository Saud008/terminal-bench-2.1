# Telemetry buffer schema

load-probes writes /app/state/tele-buffer/<run-id>.jsonl with a header line then StagedTelemetry rows: probe_id, probe_ts, temp_norm_c, cal_offset_c.
