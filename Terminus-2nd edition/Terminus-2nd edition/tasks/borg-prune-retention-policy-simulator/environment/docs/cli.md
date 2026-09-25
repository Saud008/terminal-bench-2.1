# borg-prune-sim CLI

```
borg-prune-sim ingest --list <path> --repo-id <id>
borg-prune-sim evaluate --list <path> --policy <json> --holds <json> --now <iso>
borg-prune-sim export --list <path> --out <json>
```

Staging path is always dirname(list)/borg.stage.json.

evaluate writes the evaluation block; export reads it and must fail if evaluation is missing.
