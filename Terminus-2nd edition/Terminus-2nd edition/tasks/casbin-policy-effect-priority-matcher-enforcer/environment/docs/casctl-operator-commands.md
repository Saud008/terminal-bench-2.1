# casctl attestation operator commands

casctl is installed at /usr/local/bin/casctl for offline access-decision attestation runs.

## enforce

Attest an access-request batch against configured policy bundles and publish a witness-bound report:

```
casctl enforce --config <path> --requests <path> --output <path>
```

Required flags:

| Flag | Purpose |
|------|---------|
| --config | JSON config path (default workspace: /app/config/casctl.json) |
| --requests | JSONL batch of sub, dom, obj, act access tuples |
| --output | Enforcement report JSON destination |

Exit code 0 on successful attestation. Non-zero on config, fixture, or witness export errors.

The command stages /app/state/casctl/policy-snapshot.json before evaluating requests and writes the enforcement report including audit_digest per /app/docs/report-schema.md and /app/docs/policy-trust-contract.md.
