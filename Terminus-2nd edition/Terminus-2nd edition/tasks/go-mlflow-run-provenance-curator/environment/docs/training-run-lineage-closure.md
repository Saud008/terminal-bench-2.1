# Run lineage closure

Given a focus model run id and the full experiment run catalog, build the ancestry chain from experiment root to the focus training run.

Walk parent_run_id links starting at focus_run_id. Stop when parent_run_id is empty. The closure list must be ordered root-first: the run with no parent appears first, the focus run appears last.

Each entry in the closure is the scoped run id for that run under the active seed. Do not include sibling runs or child runs of the focus run.

If a parent link is missing from the catalog, treat the current run as root for closure purposes.
