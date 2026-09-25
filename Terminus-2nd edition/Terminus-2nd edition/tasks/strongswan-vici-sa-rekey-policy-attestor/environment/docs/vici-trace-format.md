VICI trace format

Each trace is a UTF-8 JSONL file at any absolute path on disk. Bundled samples live under /app/fixtures/traces/. Blank lines and lines starting with # are ignored. Each other line is one JSON object with:

log_seq — strictly increasing integer across the full trace (see /app/docs/event-sequence-policy.md)
offset_ms — milliseconds from trace start
type — one of: ike_up, ike_down, child_up, child_delete_request, child_delete_response, child_rekey, child_rekey_done
ike_unique_id — IKE_SA unique-id (required on ike_up, ike_down, child_up when parent IKE is known)
child_unique_id — CHILD_SA unique-id (required on child events)
req_id — correlates delete request/response pairs
spi_in, spi_out — uint64 SPI values on child_up and child_rekey_done
local_ts, remote_ts — string arrays of CIDR selectors

The trace_id in snapshots is the filename without .jsonl extension.
