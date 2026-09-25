# Platform rubric — go-envoy-xds-route-snapshot-differ

**Task folder:** tasks/go-envoy-xds-route-snapshot-differ/

Agent implements ingest-pair staging with correct left and right snapshot labels, 3
Agent canonicalizes route match precedence with longer prefix winning per cluster, 3
Agent normalizes cluster endpoint weights to sum 100 using largest remainder, 3
Agent orders listener filter chains with network filters before http filters, 2
Agent canonicalizes SDS secret references to lowercase secret/ prefixed ids, 2
Agent increments normalize_revision before publish-diff is allowed, 2
Agent emits diff report changes sorted by path ascending, 2
Agent produces byte-identical report on idempotent publish-diff replay, 2
Agent honors TB3_WEIGHT_SCALE override on hidden weight-trap fixture, 2
Agent leaves internal/wrap decoy module off export hot path, 1
Agent swaps left and right snapshots during ingest-pair load, -3
Agent uses indented JSON for staging digest hash, -3
Agent selects lowest route precedence score per cluster, -3
Agent blocks publish-diff when normalize_revision is zero, -2
Agent sorts diff report paths in descending order, -2
Agent ignores TB3 hidden fixture directory overrides, -2
