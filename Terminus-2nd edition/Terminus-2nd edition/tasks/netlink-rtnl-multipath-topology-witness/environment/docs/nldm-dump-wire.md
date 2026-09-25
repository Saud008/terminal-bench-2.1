# Route dump binary format

Files under `/app/fixtures/dumps/` use magic `NLDM`, version `1`, little-endian fields.

## Header

| Field | Type | Meaning |
|-------|------|---------|
| magic | 4 bytes | `NLDM` |
| version | u16 | Must be `1` |
| seed_len | u8 | UTF-8 seed length |
| seed | bytes | Seed string for weight scaling (see `/app/docs/nexthop-bind-contract.md`) |
| count | u32 | Number of route messages |

## Route message

| Field | Type | Meaning |
|-------|------|---------|
| family | u8 | `2` = IPv4, `10` = IPv6 |
| table_id | u32 | Default route table id |
| dst_plen | u8 | Destination prefix length |
| dst_addr | 4 or 16 bytes | Destination address |
| attr_count | u16 | Number of attributes |

## Attributes

Each attribute: `type` u16, `len` u16, `payload` bytes.

| type | name | payload |
|------|------|---------|
| 4 | RTA_OIF | u32 ifindex |
| 5 | RTA_GATEWAY | 4 or 16 byte gateway matching route family |
| 6 | RTA_PRIORITY | u32 |
| 8 | RTA_MULTIPATH | multipath blob (below) |
| 15 | RTA_TABLE | u32 table override |
| 39 | RTA_METRICS | nested metrics blob (below) |
| 52 | RTA_NH_ID | u32 nexthop id hint (**single-path only**; multipath assigns ids 1..N per route) |

### RTA_MULTIPATH

| Field | Type |
|-------|------|
| hop_count | u8 |
| per hop | see below |

Per hop (6-byte header, little-endian, equivalent to Python `struct.pack("<iBB", ifindex, weight_raw, gw_family)`):

| Field | Type | Size |
|-------|------|------|
| ifindex | i32 | 4 |
| weight_raw | u8 | 1 |
| gw_family | u8 | 1 |

When `gw_family` is non-zero, the gateway address follows immediately: 4 bytes for IPv4 (`2`), 16 bytes for IPv6 (`10`).

### RTA_METRICS nested blob

| Field | Type |
|-------|------|
| nested_count | u8 |
| entries | `nested_count` × 6-byte records |

Each entry is little-endian `type: u16` + `value: u32` (Python `struct.pack("<HI", type, value)`).

Known nested metric types: `2` = `mtu`, `5` = `advmss`.
