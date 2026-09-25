# Platform rubric — ldif-modify-increment-parser-normalizer

**Task folder:** tasks/ldif-modify-increment-parser-normalizer/

Agent rebuilds ldif-apply with cargo build --locked --release after editing ldif-core, +2
Agent implements unfold_lines per RFC 2849 continuation rules in parser.rs, +3
Agent implements decode_value for unpadded base64 tokens in parser.rs, +3
Agent keeps modify operations in LDIF file order inside apply_records, +3
Agent distinguishes value-specific delete from whole-attribute delete in apply.rs, +3
Agent replaces an existing directory entry when a second add targets the same DN, +3
Agent normalizes attribute names case-insensitively and exports lowercase keys, +2
Agent writes audit rows in apply order matching export stats records_applied, +2
Agent patches only apply.rs while parser.rs still drops folded continuation lines, -3
Agent patches only parser.rs while apply.rs still re-sorts modify operations by kind, -3
Agent adds fields to ChangeRecord or ModifyOp in model.rs instead of fixing parser or apply, -3
