# Subject matching for local sessions

Polkit distinguishes active and inactive local sessions.

When subject.local is true:

- subject.active true — apply the allow_active token from the matched rule or action default
- subject.active false — apply the allow_inactive token

When subject.local is false, remote subjects still use allow_active for active sessions and allow_inactive for inactive sessions using the same field names (no swap).

Rule blocks use a single result field instead of separate allow_active/inactive columns; action defaults use the two-field form described in /app/docs/action-registry.md.

Mapping from allow_active or allow_inactive tokens to decision tokens follows the global result vocabulary in /app/docs/polkit-evaluation.md.
