# Cluster graph schema

minclus group writes /app/work/cluster-graph/<run-id>.json with run_id, jaccard_floor, group_generation, cluster_run_id, and clusters array.

group_generation starts at one on first group for a run id and increments by one on each regroup.

cluster_run_id equals grp- followed by the first twelve hex chars of SHA256 of run_id colon group_generation.
