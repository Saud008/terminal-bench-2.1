# Incident activation barrier

Jobs linked to an incident via incident.job_key must not appear in the activation sequence until the incident resolved marker is persisted on the partition log.

Use marker_persisted_at_ms, not resolved_at_ms alone. The activation timestamp for a gated job is the maximum of job intent_at_ms and marker_persisted_at_ms for its incident.

Jobs with no linked incident activate at intent_at_ms.

Each activation record includes barrier set to none when no incident applied, or incident_marker_persisted when gated.
