# Cargo.lock parsing

Parse Cargo.lock format version 3 using [[package]] stanzas.

Each stanza yields name, version, and optional source fields. Preserve every stanza even when the same package name appears with different versions (duplicate version detection depends on full enumeration).

Sort packages by name ascending, then version ascending, before staging.

The lock-metadata.json file at the workspace root lists declared_license per name@version key from the compliance baseline registry.
