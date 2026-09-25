Mesh files are JSON objects with mesh_id, survey_id, deadline_ms, default_ttl_ms, topology, and events.

Each event has offset_ms and type. Types: start, ballot, pipe_drained, reconnect, deadline, close.

Ballot events include respondent, vote, and header_hex. The header is documented in /app/docs/message-header-layout.md.

Topology kind star includes hub and edges as pairs of node names. Edges may list both directions between hub and spoke.

Events are processed in ascending offset_ms order. Duplicate offset_ms preserve file order.
