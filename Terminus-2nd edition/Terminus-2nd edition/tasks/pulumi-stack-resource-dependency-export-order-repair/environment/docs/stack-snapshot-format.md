# Pulumi stack snapshot format

Stack checkpoints are JSON files under `/app/fixtures/stacks/`.

```json
{
  "stack": "dev",
  "version": 3,
  "deployment": {
    "resources": [
      {
        "urn": "urn:pulumi:dev::acme::pulumi:providers:aws::default",
        "type": "pulumi:providers:aws",
        "parent": "urn:pulumi:dev::acme::pulumi:stack$acme/dev"
      }
    ]
  }
}
```

Each resource entry may include:

| Field | Meaning |
|-------|---------|
| `urn` | Stable resource identity |
| `type` | Pulumi type token (`pulumi:providers:*` marks provider nodes) |
| `parent` | Parent URN (implicit containment edge) |
| `provider` | Provider URN (must export before custom resource) |
| `dependencies` | Explicit `dependsOn` URNs (directed prerequisite edges) |
| `deleteBeforeReplace` | Replacement deletes old instance first |
| `replaces` | Prior URN being replaced when `deleteBeforeReplace` is true |
| `component` | Component resource wrapping nested children |

A missing or unreadable stack path causes `order` to exit `2`.

Malformed snapshots (missing `stack`, empty `resources`, invalid JSON) cause `order` to exit `3`.
