Build wtstatus-export, a worktree porcelain status export bundler on the working Bash baseline under /app. The tool admits Git status --porcelain=v2 -z byte streams from catalog fixtures, classifies ordinary/rename/copy/unmerged/untracked/ignored records under export-config score gates and submodule gitlink detection, then publishes a deterministic sealed JSON export at the caller-provided path. There is no remote Git host or CI cluster. This is a build-and-dependency-management host-local status-export bundler; keep porcelain admission, rename-score gates, and sealed export aligned. It is not a generic service repair exercise.

Install wtstatus-export at /app/bin/wtstatus-export with:

wtstatus-export parse --porcelain PATH --config PATH --export PATH

Exit 0 on success. Non-zero when the porcelain stream or config cannot be read or parsed.

Catalog scenarios use synthetic streams from:

/app/scripts/gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH

Record shapes, field meanings, export schema, and filtering rules are defined in /app/docs/porcelain-v2-format.md, /app/docs/export-schema.md, and /app/docs/contract.md. Implement porcelain admission and classification in /app/lib/parse_porcelain.sh and /app/lib/classify.sh so sealed exports match those contracts. Keep /app/bin/wtstatus-export executable.

Do not edit /app/docs/, /app/fixtures/, /app/config/export.json, or files under /tests/. The environment has no outbound network access.
