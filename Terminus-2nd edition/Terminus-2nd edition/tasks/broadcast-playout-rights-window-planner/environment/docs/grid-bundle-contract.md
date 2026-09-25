# Schedule bundle contract

Each scenario directory contains bundle.json with keys: seed, channel, region, programs, rights, blackouts, ad_markers, feeds, policies.

Programs include program_id, feed_id, start_utc, duration_sec, title.

Bundle lineage is anchored by seed plus stable program_id values. import-grid normalizes fixture paths into active-grid state without mutating constraint topology.

Anti-hardcoding: build_scenarios.py randomizes display titles and contract labels using seed but preserves constraint topology via stable program_id values in bundle.json.
