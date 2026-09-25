# Evaluation trace schema

`bundlectl eval` evaluates the `policy` package `allow` rule against bundle `data/data.json` and `--input` JSON.

## Command

```text
bundlectl eval --bundle <dir> --seed <seed> --input <path> --export <path>
```

## Supported Rego subset

- `package policy`
- `default allow = false`
- `allow { <expr> }` with a single comparison expression
- References: `data.<name>`, `input.<field>`
- Operators: `>=`, `>`, `==`, `!=`, `<=`, `<`

Apply seed substitution to the `--input` JSON before evaluation (see `/app/docs/bundle-contract.md`). When the template uses `"__THRESHOLD__"` inside quotes, `input.threshold` in `bindings` must be the substituted JSON **string** (for example `"204"`), not a JSON number. Load `data/data.json` as stored in the bundle.

## Result JSON

```json
{
  "allow": true,
  "trace": {
    "bindings": [
      {"ref": "data.foo", "value": <json>},
      {"ref": "input.threshold", "value": <json>}
    ],
    "steps": ["load_data", "eval_expr", "decision"]
  }
}
```

Every `data.*` identifier referenced in the evaluated expression must appear in `bindings` with the resolved JSON value (after seed substitution). Missing bindings fail verification even if `allow` is correct.

## Go package layout

The `Trace` and `Binding` types are defined in `/app/internal/eval/engine.go` alongside `EvalResult`. `/app/internal/eval/trace.go` implements `BuildTrace` and lookup helpers only. Do not move or duplicate those types into `trace.go`; partial test stubs replace `trace.go` alone and still compile when types remain in `engine.go`.

After each successful eval, write `/app/state/eval-audit.json` with the bundle path, seed, allow outcome, and binding count.

## Export file

`--export` writes the same JSON object.
