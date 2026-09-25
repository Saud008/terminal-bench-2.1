# Route decode and bind contract



Parse dumps per `/app/docs/nldm-dump-wire.md`. Bind raw routes into export-shaped rows and write stage artifacts under `/app/state/` as described in `/app/docs/bind-stage-artifact.md`, `/app/docs/stage1b-guard.md`, `/app/docs/nh-stage-artifact.md`, and `/app/docs/export-digest-schema.md`.



Binding must preserve dump message order. Multipath and single-path routes follow different nexthop id and metrics attachment rules; the bundled catalog and combined scenarios in dump-catalog.md exercise both.



export_digest must be assembled from NH snapshot fields as defined in export-digest-schema.md. Bind validation runs after the bind snapshot is written and before NH normalization. An export document that looks correct in isolation is still invalid when bind or NH staging snapshots disagree with export_digest or when the export stage re-derives rows from the dump instead of the NH snapshot.



## Route table selection



Use `RTA_TABLE` when present; otherwise use the message `table_id` field.



## Nexthop binding



### Multipath (`RTA_MULTIPATH` present)



- Assign nexthop `id` values **1, 2, 3, …** in multipath blob order.

- **Restart** the id sequence at **1 for every route** in the dump.

- Ignore any route-level `RTA_NH_ID` hint for multipath id assignment.

- Scale each hop `weight_raw` with the dump seed (below); do not attach route-level `RTA_METRICS` to individual nexthops.



### Single-path (no multipath blob)



- `id` = `RTA_NH_ID` when present, otherwise **0**.

- `weight` = **1** (no seed scaling).

- Route-level `RTA_METRICS` attach to the lone nexthop.



## Seed-derived multipath weight scaling



Let `seed` be the UTF-8 header seed string and `raw` the per-hop `weight_raw` byte from `RTA_MULTIPATH`:



```text

scale = (SHA-256(seed)[0] mod 32) + 1

weight = ((raw * scale) mod 255) + 1

```



Use the first digest byte only. Apply scaling only to multipath hops; single-path export weight stays 1.



## IPv6 textual format



IPv4 addresses use dotted decimal. IPv6 addresses (destinations and gateways) use **eight colon-separated 16-bit groups**:



- Split the 16-byte address into eight big-endian `u16` values.

- Render each group as lowercase hexadecimal with **no leading zeros within the group** (`{:x}` style).

- Always emit **all eight groups**. Do **not** apply RFC 5952 `::` compression or elide zero runs.



Example: bytes `20 01 0d b8 00 00 00 00 00 00 00 00 00 00 00 01` → `2001:db8:0:0:0:0:0:1` (not `2001:db8::1`, not zero-padded `2001:0db8:0000:…`).



## Stage ordering



| Stage | Module | Role |

|-------|--------|------|

| 1 | `bind.rs` | Bind rows; preserve dump message order |

| 1b | `snapshot_guard.rs` | Reject multipath routes with per-nexthop metrics |

| 2a | `export_nh.rs` | Sort each route's nexthops by ascending `id` |

| 2b | `export.rs` | Assemble export JSON and `export_digest` from NH snapshot only |

