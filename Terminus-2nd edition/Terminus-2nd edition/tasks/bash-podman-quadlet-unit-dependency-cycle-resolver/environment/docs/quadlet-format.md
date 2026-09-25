# Quadlet container file format

Quadlet sources use systemd INI sections. The resolver understands `[Unit]`, `[Service]`, and `[Container]` for `.container` files and drop-in fragments under `NAME.container.d/*.conf`.

## Discovery

Recursively find every `*.container` file under the `--tree` directory. Each base file `NAME.container` defines unit `NAME.service`. Optional drop-ins live in `NAME.container.d/` beside the base file.

## Drop-in merge order

Merge the base file first, then every file in `NAME.container.d/` sorted by **basename** (lexicographic ascending). Never use directory iteration order alone.

## List-valued keys

These keys accumulate across fragments (later values append; duplicates removed while preserving first-seen order):

- `[Unit]`: `Wants=`, `Requires=`
- `[Service]`: `EnvironmentFile=`

Scalar keys in a later fragment replace the value from earlier fragments.

## Unit dependency merge phases

`After=` uses a **separate phase** from `Wants=` / `Requires=`:

1. Merge all `Wants=` and `Requires=` entries from every fragment (base then sorted drop-ins).
2. Only after step 1 completes, merge all `After=` entries from every fragment in the same order.

Applying `After=` from an earlier fragment before `Wants=` from a later fragment is invalid.

## Parse output

`quadlet-resolver parse --tree DIR --out FILE` writes JSON:

```json
{
  "tree": "/app/fixtures/stack",
  "units": {
    "api.service": {
      "source": "/app/fixtures/stack/api.container",
      "unit": {"After": ["..."], "Wants": ["..."], "Description": "..."},
      "service": {"EnvironmentFile": ["..."], "Restart": "always"},
      "container": {"Image": "..."}
    }
  }
}
```

Keys under `unit`, `service`, and `container` are the merged result after drop-ins. Every discovered unit must appear exactly once.

The surface parser at `/app/tools/quadlet_parser.py` tokenizes individual files; call it for each fragment path (records paths in `/app/output/.parser-touch`).
