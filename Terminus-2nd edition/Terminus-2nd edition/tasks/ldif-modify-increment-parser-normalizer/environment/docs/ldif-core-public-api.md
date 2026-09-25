# ldif-core public API

ldif-apply calls ldif-core through runner.rs. Each source file below is an independent contract boundary. Parser behavior belongs in parser.rs, directory apply semantics in apply.rs, and SQLite audit I/O in audit.rs. A fix in one file must not depend on rewriting another module's source.

## parser.rs

| function | contract |
|----------|----------|
| unfold_lines(raw) | Join RFC 2849 continuation lines (physical lines starting with one space continue the previous line; the leading space is dropped). |
| decode_value(base64, value) | Return plain text, or decode unpadded base64 when base64 is true. |
| parse_ldif(raw) | Parse LDIF text into ChangeRecord values. Uses unfold_lines and decode_value. |

## apply.rs

| function | contract |
|----------|----------|
| apply_records(seed, records) | Apply parsed records to an in-memory directory and return the export model plus audit rows. Modify operations run in file order (see /app/docs/ldif-input-notes.md). Add at an existing DN replaces the entry. Value-specific delete removes one value; delete with no values removes the whole attribute. Attribute names export lowercase. |

## audit.rs

| function | contract |
|----------|----------|
| write_audit(path, seed, rows) | Persist audit rows for a seed. |
| query_audit(path, seed) | Read audit rows for audit-query export JSON. |

## runner.rs wiring

apply_file reads the LDIF file, calls parse_ldif, then apply_records, then write_audit.

query_audit reads the SQLite database and writes audit JSON.

Integration tests in ldif-core/tests/module_contracts.rs exercise these public entry points directly. End-to-end verification may substitute canonical or broken per-file implementations from /tests/canonical_ldif to confirm each module boundary independently.
