# Invite lifecycle

Statuses: `pending`, `accepted`, `expired`, `revoked`.

## Creation

Invites start `pending` with `expires_mono_ms = now_mono_ms + ttl_ms`.

## Expiry

An invite is expired when `now_mono_ms >= expires_mono_ms`. Expired invites:

- Cannot be accepted (**409**).
- Do **not** count toward member cap occupancy (see `/app/docs/member-cap.md`).
- Are marked `expired` by the sweeper or lazily during accept/cap checks.

## Leader disconnect

When the party leader disconnects, all `pending` invites become `revoked`. Accept attempts after that must fail and must not insert members.

## Accept

Accept is atomic: validate party active, leader connected, invite pending and not expired, cap has a free slot — then insert member and mark invite `accepted` in one transaction. Failed validation must leave no partial membership rows.
