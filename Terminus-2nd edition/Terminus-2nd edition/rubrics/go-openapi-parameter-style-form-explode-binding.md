# Platform rubric — go-openapi-parameter-style-form-explode-binding

**Task folder:** tasks/go-openapi-parameter-style-form-explode-binding/

Agent implements OpenAPI form explode false query arrays with comma delimiter, +3
Agent implements form explode true query arrays with repeated keys, +3
Agent binds deepObject bracket notation using explode_policy defaults, +3
Agent binds form explode false objects from comma-separated key=value pairs, +3
Agent normalizes date query parameters to UTC calendar day, +2
Agent returns HTTP 400 missing_required for absent required parameters, +3
Agent canonicalizes top-level and nested object keys lexicographically, +3
Agent stages canonical witness bind snapshot at /app/state/bind-snapshot.json, +3
Agent publishes HTTP 200 params from staged witness via publish.go not memory, +3
Agent increments bind_seq monotonically across successful attestation, +2
Agent binds admin extension routes from merged OpenAPI fragment, +2
Agent transcodes latin1 JSON request bodies before policy evaluation, +2
Agent returns bad_content_type for non JSON POST content types, +2
Agent includes decoded JSON body in witness backed POST responses, +2
Agent fixes binder staging to persist canonical params not raw parser maps, +2
Agent leaves arrayJoinDelimiter as space for form explode false, -3
Agent uses wrong deepObject explode default in explode_policy.go, -3
Agent returns HTTP 500 for missing required client parameters, -3
Agent emits success payload from in-memory maps instead of witness snapshot, -3
Agent applies local timezone offset when normalizing date parameters, -2
Agent skips admin fragment routes and binds catalog only, -2
