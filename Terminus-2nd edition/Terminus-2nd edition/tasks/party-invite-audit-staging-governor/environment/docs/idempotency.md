# Idempotency

Accept requires header `Idempotency-Key`.

The service stores `(idempotency_key, status_code, response_json)` after the first successful accept attempt completes.

## Retry semantics

On retry with the same key:

1. Return the stored HTTP status and JSON body.
2. Do not insert duplicate members.
3. Do not change invite status again.

The idempotency lookup must happen **before** any accept-side mutation. Keys are scoped globally per daemon instance (single SQLite file).

Failed accepts (**409**) are **not** cached unless the failure happened after a successful prior accept with the same key.
