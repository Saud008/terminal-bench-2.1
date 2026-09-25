# Suppression windows

Suppression tickets may scope by rule_name and optionally asset_id and sample_sha256.
Empty asset_id or sample_sha256 acts as a wildcard for that dimension.

A ticket suppresses an event when:

- ticket.rule_name equals event.rule_name
- ticket.asset_id is empty or equals event.asset_id
- ticket.sample_sha256 is empty or equals event.sample_sha256
- start_ms <= detected_ms <= end_ms (inclusive end)

Suppressed incidents set suppressed true, actionable false, and suppression_reason to suppression_ticket:TICKET_ID.
