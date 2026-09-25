# borderdocctl CLI surface

Binary path: /app/bin/borderdocctl

## import-manifest

```
borderdocctl import-manifest --scenario SCENARIO [--fixture-dir D]
```

Default fixture root is /app/fixtures. Loads passports, visas, stamps, rules, and holds into /app/state/border-validity.db. Writes manifest snapshot to /app/state/manifest-snapshot.json.

## score-validity

```
borderdocctl score-validity --scenario SCENARIO
```

Requires prior import-manifest for the same scenario id. Computes decisions at the scenario reference_date and writes /app/output/validity-decisions.json. Increments eval_pass in /app/state/eval-pass.json.

## commit-ledger

```
borderdocctl commit-ledger --scenario SCENARIO [--output PATH]
```

Requires eval_pass positive. Appends ledger rows in a replay-stable manner for the current eval_pass. Default manifest path is /app/output/ledger-manifest.json.
