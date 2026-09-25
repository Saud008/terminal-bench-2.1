# Scheduler contract

## Priority dequeue

Pending jobs with `available_at_ms <= now` are eligible. Select the job with the **lowest** numeric `priority` value (1 outranks 9). When priorities tie, choose the lexicographically **smallest** `id`.

## Attempt backoff

After `fail`, increment `attempts` and set `available_at_ms = now_ms + delay_ms`.

`delay_ms = backoff_base_ms * 2^attempts` where `attempts` is the post-increment attempt count. The exponent must depend only on `attempts`, never on wall-clock hour buckets or calendar time.

## Poison cap

When `attempts >= max_attempts` after a failure, set `state = poison` and do not requeue. Poison jobs never return to `pending`.

## Procedural seed

`POST /admin/seed` clears jobs and leases, then inserts catalog jobs mutated by the seed.

Derive one integer **offset** from the seed string:

1. `digest =` lowercase hex encoding of `SHA-256(seed)` (64 characters).
2. `offset = int(digest[0:8], 16) % 997` — the first eight hex characters are the first four hash bytes.

For each catalog row at zero-based **index**:

- `priority = catalog_priority + (offset % 7)`
- `payload = catalog_payload + ":" + seed + ":" + str(offset + index)`

Bundled catalog: `/app/fixtures/seed-catalog.json`.
