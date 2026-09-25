# Patch source lineage

Read [patch.crates-io] tables from the workspace Cargo.toml. Each patched crate name maps to a path patch.

For every lock package whose name appears in the patch map, attach patch_lineage with patch_path, source_kind path, and registry_fallback registry+crates.io#name@version.

Emit a patched_crate finding for each package carrying patch_lineage during audit.
