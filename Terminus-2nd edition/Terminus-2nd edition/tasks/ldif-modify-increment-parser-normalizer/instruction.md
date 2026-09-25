The ldif-apply service under /app reads LDIF change files and writes a directory export JSON plus an SQLite audit log. Sample inputs are under /app/fixtures/ldif/. After cargo build --locked --release --bin ldif-apply from /app, running apply on those samples shows several wrong outcomes.

Folded attribute lines are wrong. In continuation-fold.ldif, values that continue on the next physical line (leading space, RFC 2849 style) are truncated or split instead of forming one value.

Base64 syntax is left as literal text. In base64-token.ldif, attributes written with two colons after the name still appear encoded in the export.

Modify batches ignore file order. modify-op-order.ldif ends with a different cn and mail set than the operation sequence in the file implies; results look like operations were grouped by kind instead of applied in order.

Delete is too aggressive. delete-value-vs-attr.ldif drops whole attributes when only one value should be removed.

Repeat add merges instead of replacing. add-replace-dn.ldif keeps stale attributes from an earlier add at the same DN.

Case variants split entries. case-merge.ldif exports mail and Mail as separate keys.

Fix ldif-core so ldif-apply apply and audit-query produce JSON matching /app/docs/directory-export-contract.md and audit dumps matching /app/docs/changetype-audit-contract.md. CLI flags are in /app/docs/cli-reference.md. LDIF record layout (syntax only) is in /app/docs/ldif-input-notes.md. Public functions and per-file module boundaries are in /app/docs/ldif-core-public-api.md.

The types in /app/crates/ldif-core/src/model.rs define the export and audit shapes. Do not add or remove fields on ChangeRecord, ModifyOp, or the serde export structs. Skipped-record counts belong in ApplyStats.records_skipped per the export schema.
