# Signal routing

Signal delivery uses the workflow **pinned_version** from the scenario JSON. Do not route to the lexicographically greatest entry in `versions_registered`.

The routed version is stored in `/app/state/signal-snapshot.json` as `routed_version` before export.

Legacy route merging lives in `internal/router/wrap.go` and is not part of export.
