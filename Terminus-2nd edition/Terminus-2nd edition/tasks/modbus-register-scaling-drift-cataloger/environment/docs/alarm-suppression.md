# Alarm suppression windows

Manifest alarm_suppression[] entries contain device_id, register, start_ms, and end_ms inclusive bounds on received_ms.

When a frame matches device_id and register and received_ms lies in [start_ms, end_ms], the catalog entry must set suppressed=true and drift_alarm=false even when drift exceeds drift_threshold.

Suppression does not change engineering or drift magnitude fields.
