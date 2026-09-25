# Verifier fixture catalog

Bundled timer bundles live under /app/fixtures/seed/.

Additional timer bundles may appear under /opt/verifier-fixtures/systemd-timer/ during verification. These follow the same bundle layout as seed fixtures but use different timezone, persistent, and monotonic combinations.

Default plan context path: /app/context/default.json

Default export path for worked examples: /app/output/drift-report.json

Staging manifests live under /app/stage/manifests/BUNDLE_BASENAME.json where BUNDLE_BASENAME is the final path segment of the bundle directory.

Seed bundle merged fields after drop-in precedence include Timezone America/Chicago, RandomizedDelaySec 300, and Persistent true.
