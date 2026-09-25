# Member cap accounting

Each party has `max_members` set at creation.

**Effective occupancy** for cap checks:

```
connected_members + pending_invites_not_yet_expired
```

Where:

- `connected_members` = member rows with `status = connected`.
- `pending_invites_not_yet_expired` = invite rows with `status = pending` **and** `expires_mono_ms > now_mono_ms`.

Expired `pending` rows still in the database before sweep **must not** consume cap slots.

New invites and accepts are rejected with **409** when effective occupancy would reach or exceed `max_members`.

When validating **accept**, treat the invite being accepted as converting from pending to connected: do not count that invite row as an occupied pending slot in the cap check (only other connected members and other non-expired pending invites count).
