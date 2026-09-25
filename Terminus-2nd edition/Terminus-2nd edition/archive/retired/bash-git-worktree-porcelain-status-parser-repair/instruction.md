The `wtstatus-export` CLI at `/app/bin/wtstatus-export` reads Git `status --porcelain=v2 -z` byte streams and writes normalized JSON exports, but exports produced from `/app/lib/` do not match `/app/docs/contract.md`.

## CLI

```
wtstatus-export parse --porcelain PATH --config PATH --export PATH
```

Exit `0` on success. Non-zero when the porcelain stream or config cannot be read or parsed.

Catalog scenarios use synthetic streams from:

```
/app/scripts/gen_porcelain_fixture.sh --scenario NAME --seed SEED --output PATH
```

Record shapes, field meanings, export schema, and filtering rules are defined in `/app/docs/porcelain-v2-format.md`, `/app/docs/export-schema.md`, and `/app/docs/contract.md`.

## Scope

Repair `/app/lib/parse_porcelain.sh` and `/app/lib/classify.sh`. Keep `/app/bin/wtstatus-export` executable.

Do not edit `/app/docs/`, `/app/fixtures/`, `/app/config/export.json`, or files under `/tests/`. The environment has no outbound network access.
