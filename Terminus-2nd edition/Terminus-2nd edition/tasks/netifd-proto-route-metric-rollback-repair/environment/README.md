The netifd-style route harness under /app/bin/netifd-ctl applies fixture scenarios to a simulated veth stack, but teardown ordering, metric rollback, hotplug address handling, IPv6 prefix-delegation reload, and staged route snapshots disagree with the contracts in /app/docs/.

# netifd-ctl harness

Offline simulated netlink/route table for proto handler repair exercises.

Example:

/app/bin/netifd-ctl apply --scenario default-route --fixtures-root /app/fixtures/scenarios
/app/bin/netifd-ctl export --output /app/output/routes.json

Docs: /app/docs/proto-contract.md, /app/docs/route-rollback-contract.md, /app/docs/hotplug-contract.md, /app/docs/pd-lease-contract.md, /app/docs/staging-snapshot.md, /app/docs/export-schema.md
