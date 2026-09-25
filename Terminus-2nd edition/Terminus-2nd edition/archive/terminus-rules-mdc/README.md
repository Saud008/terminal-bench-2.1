# Archived Terminus rule sources (edit here)

**Canonical edit location** for full Snorkel/Terminus policy text.

After editing any file here, rebuild the 7 Cursor bundles:

```bash
python3 scripts/build_consolidated_rules.py
```

That writes `.cursor/rules/engines/ENGINE_*.mdc` (verbatim merge, `alwaysApply: false`).

**Do not** put 100+ files back under `.cursor/rules/` — conflicts come from many `alwaysApply: true` files, not from having full rules.
