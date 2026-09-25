Worktree inventory administrators run the host-local wtstatus-export inventory control plane at /app/bin/wtstatus-export to produce sealed inventory atlases from offline depot streams. Each offline ops pass ingests depot inventory stream fixtures from the catalog into staging gates, enforces rename-score admission and gitlink hold barriers, then must publish sealed inventory atlas JSON only from gated entries. There is no remote depot host or CI cluster. This is a system-administration host-local worktree inventory ops control plane; keep admission gates, score barriers, and sealed atlas export aligned. It is not a generic service repair exercise.

Read the ops contracts under /app/docs/ before changing behavior: overview.md for the control-plane charter, inventory-ops-workflow.md for admit and seal stages, contract.md for admission and export obligations, inventory-stream-format.md for NUL record shapes, export-schema.md for sealed atlas fields, fixture-catalog.md for catalog scenarios, and cli-reference.md for verbs and flags.

wtstatus-export parse --porcelain PATH --config PATH --export PATH must admit one inventory stream, apply /app/config/export.json rename-score and gitlink gates, and write sealed atlas JSON at the caller-provided --export path. Exit 0 on success. Non-zero when the stream or config cannot be admitted.

Catalog scenarios synthesize streams via /app/scripts/gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH.

Align admission and gate modules under /app/lib/ with those contracts so sealed atlases match. Keep /app/bin/wtstatus-export executable. Do not edit /app/docs/, /app/fixtures/, /app/config/export.json, or files under /tests/. The environment has no outbound network access.
