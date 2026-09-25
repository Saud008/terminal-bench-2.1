# Export report schema

`order --output` writes JSON matching this schema:

```json
{
  "stack": "dev",
  "order": [
    {
      "urn": "urn:pulumi:dev::acme::pulumi:providers:aws::default",
      "type": "pulumi:providers:aws",
      "component": false,
      "depth": 0
    }
  ],
  "stats": {
    "resources": 3,
    "provider_nodes": 1,
    "component_roots": 0,
    "delete_before_replace_pairs": 0
  }
}
```

| Field | Rule |
|-------|------|
| `order[].urn` | Matches snapshot URN |
| `order[].type` | Copied from snapshot |
| `order[].component` | Copied from snapshot `component` flag |
| `order[].depth` | Number of strict parent hops to a resource outside the parent chain (stack root breaks the walk) |
| `stats.provider_nodes` | Count of `pulumi:providers:*` types in `order` |
| `stats.component_roots` | Count of resources with `component: true` |
| `stats.delete_before_replace_pairs` | Count of resources with both `deleteBeforeReplace` and non-empty `replaces` |

Consumers compare the **full JSON object** to the contracts above — not a static export file baked into the image.

## Export module entry point

`replay.OrderStack` calls `export.BuildReport(snap, ledgerPath)` after writing `/app/state/dep-ledger.json`. Keep that **two-argument function name and signature** unchanged while fixing export behavior. Full stable-surface rules: `/app/docs/module-api-contract.md`.
