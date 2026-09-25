# Model DAG traversal

Topological order applies to enabled models only.

Disabled models must not appear in model_order even if listed in the manifest. They may still appear in exposure_refs via the transitive exposure walk.

Dependencies may reference sources or other models. Only model nodes participate in model_order; source dependencies are ignored for ordering purposes.

Sort roots lexicographically by unique_id before DFS post-order append.
