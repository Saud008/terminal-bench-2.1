# Client and server role detection

For each session quad, examine frames in sequence order.

The first frame with `direction = client` identifies the client IPv4 as the first four bytes of `session_quad`.

The server IPv4 is the second four bytes of `session_quad`.

`role_map` keys are dotted-quad strings. Values are exactly `client` or `server`.

When at least one frame in the session has `direction = client`, `role_map` must include both endpoints: the client IPv4 marked `client` and the server IPv4 marked `server`.

When no frame has `direction = client`, `role_map` contains only the client IPv4 (first quad octets) marked `client`. Do not add a server entry in that case.
