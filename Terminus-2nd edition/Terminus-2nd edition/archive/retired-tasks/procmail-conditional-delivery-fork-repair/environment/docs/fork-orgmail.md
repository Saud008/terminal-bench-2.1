# Fork and ORGMAIL fallback

Nested blocks `{` … `}` fork delivery logic for the current message.

When a nested block finishes and no inner recipe performed a delivery for that message during the block, deliver once to ORGMAIL using reason `orgmail_fork_fallback`.

If any inner recipe delivered, ORGMAIL is not used for that block instance.

The snapshot lists ORGMAIL fallbacks in `deliveries` with field `reason` set to `orgmail_fork_fallback`.

Counter `stats.orgmail_fallbacks` counts those deliveries.
