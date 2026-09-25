# Workspace-root Cursor bridge

This folder wires Cursor (workspace root) to the Terminus repo in `Terminus-2nd edition/`.

| Path | Purpose |
|------|---------|
| `hooks.json` | Points hooks at `Terminus-2nd edition/.cursor/hooks/*.py` |
| `rules/` | Junction → `Terminus-2nd edition/.cursor/rules/` |

**Healthcheck:** from inner repo run `python scripts/terminus_engine_healthcheck.py`

Restart Cursor after hook changes.
