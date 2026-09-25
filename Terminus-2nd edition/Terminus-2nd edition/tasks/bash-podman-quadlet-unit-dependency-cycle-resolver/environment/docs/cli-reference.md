# CLI reference

All commands accept `--tree DIR` pointing at a quadlet fixture root.

| Command | Purpose |
|---------|---------|
| `quadlet-resolver parse --tree DIR --out FILE` | Emit merged unit JSON per `/app/docs/quadlet-format.md` |
| `quadlet-resolver order --tree DIR --out FILE` | Emit topological order or exit 2 on cycle |
| `quadlet-resolver render --tree DIR --out DIR` | Write systemd unit files per `/app/docs/emit-contract.md` |

Run `/app/scripts/reset-state.sh` before local checks. Rebuild is not required — Bash sources `/app/lib/` at runtime.

Exit codes: `0` success, `1` usage or I/O error, `2` dependency cycle (order/render only).
