# Kconfig assignment syntax

kcfgattest reads defconfig and fragment files using Linux kconfig assignment lines.

Enabled symbols use CONFIG_NAME=y or CONFIG_NAME=m. Disabled explicit assignments use CONFIG_NAME=n. Unset symbols appear as hash CONFIG_NAME is not set and must be recorded as value n in parsed maps.

Blank lines and comment lines that are not unset markers are ignored. Only CONFIG_ prefixed symbols are parsed.

Each bundled scenario under /app/fixtures/bundles/ includes defconfig, fragments/, deps.json, policy.json, and bundle.json metadata.
