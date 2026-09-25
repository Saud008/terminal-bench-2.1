# Fixture board catalog

Bundled playtest boards live under `/app/fixtures/boards/`:

| board_id | role |
|----------|------|
| plains-01 | open flats, scout vision |
| ridge-02 | elevation ridge + equal-elev peek |
| tower-03 | tower class radius |
| multi-04 | multi-unit union vision (includes class `militia`) |

Inventory JSON: `/app/fixtures/board_catalog.json`.

Hidden verifier boards copy to `/opt/verifier-fixtures/fogpf/boards/` (includes board_id `tb3-ridge`). When `TB3_BOARD_DIR` is set, board path resolution for bundled names uses that directory instead of `/app/fixtures/boards/`.

## CLI flags

- `load-board`: `--run-id`, `--board` (path to board JSON)
- `place-units`: `--run-id`
- `resolve-los`: `--run-id`
- `reveal-fog`: `--run-id`
- `seal-atlas`: `--run-id`

## Release build

From `/app` run `cargo build --release --locked` and copy `target/release/fogpf` to `/app/bin/fogpf`.

The `scout_decoy` module is a pathfinding sandbox and is **not** on the load-board → place-units → resolve-los → reveal-fog → seal-atlas hot path.
