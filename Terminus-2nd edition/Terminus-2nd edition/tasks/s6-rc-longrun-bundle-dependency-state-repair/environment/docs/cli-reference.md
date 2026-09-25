CLI entrypoint: /app/bin/s6-bundle-resolver

ingest --tree DIR --out PATH writes full ingest JSON.

validate --tree DIR --bundle NAME checks hard-dep DAG acyclicity.

plan --tree DIR --bundle NAME --out PATH writes plan JSON.

ready --tree DIR --bundle NAME --state-dir DIR --out PATH writes ready JSON against rc state.

apply --tree DIR --bundle NAME --bundle-id ID --state-dir DIR runs mock s6-rc transitions.

export --tree DIR --bundle NAME --out PATH writes export graph JSON.

All paths are absolute under /app unless overridden by --state-dir.
