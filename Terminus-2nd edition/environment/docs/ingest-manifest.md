# Ingest manifest

After ingest_scenario, /app/state/spool-manifest.json lists every message copied from the fixture:

```json
{
  "messages": [
    {"quarantine_id": "...", "stored_class": "spam|virus", "spool_subdir": "spam|virus", "bytes": 0}
  ]
}
```

stored_class comes from each meta.json class field. Reconcile must write this manifest before processing release requests.
