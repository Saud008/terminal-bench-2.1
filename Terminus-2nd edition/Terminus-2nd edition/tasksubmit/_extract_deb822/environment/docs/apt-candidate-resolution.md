# APT install candidate resolution

debpol answers which package version apt would select as the install candidate given deb822 sources, preferences pins, and offline index rows. Resolution is not a generic bundler pipeline: each candidate row carries package, version, arch, and origin_id from a specific index file.

Priority order for a query package:

1. Collect index rows from origins sorted by Default-Pin descending.
2. Drop rows whose arch is missing or mismatched against scenario target_arch.
3. Compute effective Pin-Priority from preferences for each remaining row.
4. Pick the row with highest effective priority; break ties with dpkg version compare.

The chosen row becomes chosen_version and origin_id in install_candidates with verdict selected. When no row survives filtering, verdict is none.

This workflow models apt policy resolution without invoking apt itself.
