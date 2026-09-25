# Systemd unit emission contract

`quadlet-resolver render` writes one `.service` file per unit under `--out`, using parse output and topological order from `/app/docs/dag-contract.md`.

## Required sections

Each generated unit includes:

```ini
[Unit]
Description=...
After=...
Wants=...

[Service]
EnvironmentFile=...
Restart=...
ExecStart=/usr/bin/podman run ...

[Install]
WantedBy=multi-user.target
```

## Field sources

| Generated key | Source |
|---------------|--------|
| `[Unit]` keys | Merged `[Unit]` from parse output |
| `EnvironmentFile=` | Merged `[Service]` only — never omit when present in parse |
| `Restart=` | Merged `[Service]` only — **ignore** `[Container]` `Restart=` |
| `ExecStart=` | Synthesized as `podman run --name UNIT_BASENAME IMAGE` using merged `[Container]` `Image=` |

Emit units in topological order (dependencies first). On cycle, exit 2 like `order`.

## Render command

```text
quadlet-resolver render --tree /app/fixtures/stack --out /app/output/units
```

Generated files must pass `systemd-analyze verify` when checked from the output directory. The runtime image provides a minimal `/usr/bin/podman` stub so verify can check unit syntax without a real container engine.

## Render side effects

`render` does not modify the fixture tree. Output paths are `{out}/{unit-name}` (for example `api.service`).
