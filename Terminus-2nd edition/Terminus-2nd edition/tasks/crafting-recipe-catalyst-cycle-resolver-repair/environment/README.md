# Crafting workstation

Local recipe preview and commit tool backed by SQLite inventory storage.

- Contract: `/app/docs/crafter-contract.md`
- Recipe syntax: `/app/docs/recipe-format.md`
- Inventory tables: `/app/docs/inventory-schema.md`
- Cycle rules: `/app/docs/cycle-detection.md`
- Substitute map: `/app/docs/substitute-rules.md`
- Export JSON: `/app/docs/export-schema.md`

Rebuild after Rust edits:

```
cargo build --release --locked -p craft-cli
install -m 0755 /app/target/release/crafter /usr/local/bin/crafter
```
