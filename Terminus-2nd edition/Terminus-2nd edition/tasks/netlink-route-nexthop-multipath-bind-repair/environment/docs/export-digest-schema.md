# Export schema



Exported JSON must be deterministic and canonical for identical dump inputs. Use the exact field set below with no additional keys. Values and array ordering must follow the rules in this document so repeated decode runs on the same dump path produce byte-identical export files.



```json

{

  "pipeline_version": 1,

  "seed": "nl-seed-6",

  "routes": [

    {

      "family": "inet4",

      "table": 254,

      "dst": "10.0.0.0/8",

      "priority": 100,

      "nexthops": [

        {

          "id": 1,

          "ifindex": 2,

          "weight": 17,

          "gateway": "192.168.1.1",

          "metrics": {"mtu": 1500}

        }

      ]

    }

  ],

  "export_digest": "a1b2c3..."

}

```



| Field | Meaning |

|-------|---------|

| `pipeline_version` | Always `1` |

| `seed` | UTF-8 seed from the dump header |

| `routes` | Final export rows after stage 2a nexthop normalization |

| `export_digest` | Lowercase SHA-256 hex digest binding the staged pipeline (below) |



Stage 2b (`export.rs`) must read the NH snapshot from stage 2a (`/app/docs/nh-stage-artifact.md`) and must not re-open the dump, re-run bind, or re-read the bind snapshot for route assembly. The legacy helper in `route_table_digest.rs` is not on the `nlctl decode` hot path.



## Row shape



- `family` is `inet4` or `inet6`.

- `table` is the bound route table id.

- `dst` is `address/prefix` using the IPv4 or IPv6 textual rules in `/app/docs/nexthop-bind-contract.md`.

- `priority` is omitted when absent in the dump.

- Each nexthop includes `id`, `ifindex`, and `weight`. Omit absent optional keys (`gateway`, empty `metrics`) from JSON objects.



## Nexthop ordering



Stage 2a (`export_nh.rs`) sorts each route's `nexthops` array by ascending `id` before writing the NH snapshot. Route row ordering for export JSON follows dump message order through stage 2b (`export.rs`).



## export_digest



Compute `export_digest` from the NH snapshot fields used at export time:



1. `snapshot_routes` — bind-order route rows **before** stage 2a nexthop sorting (copied into the NH snapshot).

2. `routes` — export-ready route rows **after** stage 2a nexthop sorting.

3. `source_dump` — absolute `--dump` path string stored in the bind/NH snapshots.



### Route flattening (`route_row_lines`)



Flatten a route list into a linear string sequence used by the digest. For **each route** in list order, append:



1. `family`

2. `table` as decimal string

3. `dst`

4. `priority` as decimal string, or `"-"` when absent

5. For **each nexthop in array order** (after stage 2a sorting):

   - `id`, `ifindex`, `weight` as decimal strings

   - `gateway` string, or `"-"` when absent

   - For each metrics entry in **ascending key order**: `key:value` (colon separator, e.g. `advmss:1440`, `mtu:1500`)



### Digest payload



```text

snapshot_fp = lowercase_hex(SHA-256( join(snapshot_routes flatten lines, "\n") ))

parts = [

  "1",

  seed,

  source_dump,

  snapshot_fp,

  decimal_string(len(export routes)),

  ...export routes flatten lines...

]

export_digest = lowercase_hex(SHA-256( join(parts, "\n") ))

```



Rules:



- Join digest components with `\n` only (no trailing newline after the final component).

- `snapshot_fp` fingerprints bind-order rows before nexthop id sorting.

- Metric pairs in flattening use `key:value`, not `key=value`.

- Use the same flattening for `snapshot_routes` and final export `routes`; only the route/nexthop content differs between the two lists.

