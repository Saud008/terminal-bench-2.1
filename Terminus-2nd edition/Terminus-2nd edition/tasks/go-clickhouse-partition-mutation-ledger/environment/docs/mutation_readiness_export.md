# Mutation readiness export

Report JSON contains:

- mutations: array sorted by partition_id then mutation_version ascending
- totals: mutation_count, ready_count, suppressed_count, detached_count

readiness_state values: ready, suppressed, detached, pending

pending applies when partition is attached, lag is within threshold, but mutation version is not the partition maximum.

ready applies when attached, lag within threshold, and row is the highest mutation_version for its partition_id.

anchor timestamp from config anchor.txt is copied to report anchor_utc field unchanged.
