# Declarative ingest

`internal/ingest` loads YAML decks described in `/app/docs/declarative-deck.md`.

Ingest is **atomic**:

1. Validate every service plugin name, route plugin name, and route→service reference.
2. Reject the entire deck on any validation error with HTTP **422** and `ok:false`.
3. On success, replace the in-memory route/service/consumer tables in one step.

A failed ingest must leave **zero** routes loaded:

- Do **not** mutate the store while validation is still running (no partial route rows mid-validation).
- On any validation failure, **clear** all in-memory routes, services, and consumers so the proxy has no loaded deck until the next successful ingest.
- The ingest report field `routes_loaded` must be **0** on failure, including when the process already held routes from an earlier successful load (for example startup reload of `/app/fixtures/deck-bundled.yaml` followed by a rejected admin ingest).
- Do not preserve or report the count from a previously loaded deck when the current ingest fails.

The CLI `kongadmit ingest --deck PATH` uses the same validation semantics and exits non-zero on failure.
