# Matrix export contract

ldaprm ingest reads LDIF, group membership, ACL directories, and defaults into `/app/state/acl_staging.json` with `staging_fingerprint`.

ldaprm export reads the staging snapshot and a subjects probe manifest to write `/app/output/effective_rights_matrix.json` with sorted decisions and `report_digest`.

Export accepts any absolute `--staging` path under `/app/state/` and any absolute `--out` path under `/app/output/`. Verifier cases may use `/app/state/alt_staging.json`, `/app/output/alt_matrix.json`, `/app/output/bundled_matrix.json`, `/app/output/tb3_matrix.json`, and `/app/output/tb3_acl_matrix.json`.

When `TB3_ACL_DIR` and `TB3_SUBJECTS_FILE` are set to absolute paths, export uses those paths for ACL reload during matrix evaluation while still reading the staging snapshot for entries and group closure.

The decoy `merge_acl_lines` helper under `/app/internal/dirauth/decoy` is not authoritative for ingest or export.

## Staging snapshot schema (`acl_staging.json`)

Top-level JSON object:

| Field | Type | Required |
| --- | --- | --- |
| `schema_version` | integer `1` | yes |
| `entries` | array of `{dn, object_classes}` | yes |
| `group_graph` | object mapping group DN → sorted array of **direct** member DNs from the groups TSV | yes |
| `group_closure` | object mapping group DN → sorted array of **terminal** member DNs after transitive expansion | yes |
| `aces` | array of flattened ACE rule objects (not nested ACL blocks) | yes |
| `defaults` | object parsed from the defaults JSON file | yes |
| `staging_fingerprint` | lowercase hex SHA-256 string | yes |

Each entry uses normalized DNs (`dn-normalization.md`). `object_classes` is a sorted, de-duplicated list of strings.

Each ACE object in `aces`:

| Field | Type | Notes |
| --- | --- | --- |
| `ace_id` | string | `{acl_file_stem}:{block_index}:{rule_index}` — e.g. `mail:0:1` for the second rule in the first block of `mail.acl` |
| `target` | string | normalized target DN |
| `scope` | string | `entry`, `one`, or `subtree` |
| `inherit` | boolean | `true` unless the block has `INHERIT no` |
| `effect` | string | `allow` or `deny` |
| `subject_type` | string | `user` or `group` |
| `subject_dn` | string | normalized subject DN |
| `rights` | array of strings | e.g. `["read","write"]` |
| `attrs` | array of strings | attribute names or `*` |

## `staging_fingerprint` preimage

`staging_fingerprint` is lowercase hex SHA-256 over UTF-8 lines joined by `\n` with **no trailing newline**.

Build lines in this order:

1. **Entries** — one line per LDIF entry, sorted by `dn`:
   `entry;{dn};{object_classes_csv}`
   where `object_classes_csv` is comma-joined sorted objectClass values.

2. **ACEs** — one line per flattened ACE, sorted by `ace_id`:
   `ace;{ace_id};{target};{scope};{inherit_int};{effect};{subject_type};{subject_dn};{rights_csv};{attrs_csv}`
   where `inherit_int` is `1` for true and `0` for false, and rights/attrs are comma-joined in array order.

3. **Group closure** — one line per `(group, member)` pair from `group_closure`, groups sorted by DN, members sorted within each group:
   `member;{group_dn};{member_dn}`

4. **Defaults** — one line per objectClass key in `defaults.by_objectclass`, sorted by objectClass name:
   `default;{objectclass};{rights_csv};{attrs_csv}`

Example fragment:

```text
entry;cn=alice,ou=people,dc=example,dc=com;inetOrgPerson,person
ace;mail:0:0;cn=alice,ou=people,dc=example,dc=com;entry;1;allow;user;cn=alice,ou=people,dc=example,dc=com;write;mail
member;cn=readers,ou=groups,dc=example,dc=com;cn=alice,ou=people,dc=example,dc=com
default;person;read;*
```

## Matrix export schema (`effective_rights_matrix.json`)

Top-level JSON object:

| Field | Type | Required |
| --- | --- | --- |
| `schema_version` | integer `1` | yes |
| `staging_fingerprint` | string | copied from the staging snapshot used for export |
| `decisions` | array of decision rows | yes, sorted ascending by `probe_id` |
| `report_digest` | lowercase hex SHA-256 string | yes |

Each decision row:

| Field | Type | Values |
| --- | --- | --- |
| `probe_id` | string | from the probe manifest |
| `subject_dn` | string | normalized |
| `entry_dn` | string | normalized |
| `attribute` | string | probe attribute |
| `right` | string | probe right |
| `verdict` | string | `allow` or `deny` |
| `reason` | string | `ace_allow`, `ace_deny`, `default_inherit`, or `no_match` |
| `winning_ace_id` | string | winning `ace_id`, or empty string when no ACE won |
| `audit_digest` | string | 64-char lowercase hex SHA-256 |

Use these field names exactly. Do not use aliases such as `decision`, `effect`, or `"explicit-deny"`.

## `report_digest` preimage

Sort decision rows by `probe_id`. Build one line per row:

`{probe_id};{verdict};{reason};{winning_ace_id}`

Fields are semicolon-separated. `winning_ace_id` is the empty string when absent.

`report_digest` is lowercase hex SHA-256 over those lines joined by `\n` with **no trailing newline**.

Example:

```text
p_alice_mail_write;allow;ace_allow;mail:0:0
p_anonymous_person_deny;deny;no_match;
```

## `audit_digest` preimage

Each row's `audit_digest` is lowercase hex SHA-256 over a **pipe-delimited** UTF-8 string:

`{probe_id}|{verdict}|{reason}|{winning_ace_id}|{normalized_entry_dn}`

Use the normalized `entry_dn` (see `dn-normalization.md`). `winning_ace_id` is empty for `default_inherit` and `no_match`.

Examples:

```text
p_alice_mail_write|allow|ace_allow|mail:0:0|cn=alice,ou=people,dc=example,dc=com
p_subtree_self_alice_read|allow|default_inherit||cn=alice,ou=people,dc=example,dc=com
p_anonymous_person_deny|deny|no_match||cn=anonymous,dc=example,dc=com
```

`/app/lib/audit_digest.py` exposes `sha256_hex(text)` for the same digest function.

## Bundled and hidden probes

Bundled subject probes include `p_alice_mail_write`, `p_alice_mail_deny_readers`, `p_subtree_self_alice_read`, and `p_anonymous_person_deny`. Hidden fixtures live at `/opt/verifier-fixtures/ldaprm_hidden/acls` and `/opt/verifier-fixtures/ldaprm_hidden/subjects/probes.json` with probes `h_inherit_block_mail` and `h_contractor_subtree`.
