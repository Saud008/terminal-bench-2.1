# Cache contract

The server caches `GET /resource/{id}` responses in memory for the process lifetime.

## Cache key

The key must incorporate the request path and the raw negotiation header values:

- raw `Accept` header value (empty string when absent)
- raw `Accept-Language` header value (empty string when absent)
- raw `Accept-Charset` header value (empty string when absent)

Different header combinations for the same path are distinct cache entries.

## Accounting

`GET /cache/stats` returns monotonic `hits` and `misses` counters for the process lifetime.

- `X-Cache: MISS` on a lookup that stores a new entry (including `406` responses)
- `X-Cache: HIT` on a lookup that reuses a stored entry (including cached `406` responses)

`POST /admin/catalog` clears cached entries and resets hit/miss counters to zero.
