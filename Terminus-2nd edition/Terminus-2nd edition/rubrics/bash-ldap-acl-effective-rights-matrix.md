# Platform rubric — bash-ldap-acl-effective-rights-matrix

**Task folder:** tasks/bash-ldap-acl-effective-rights-matrix/

Agent implements ldaprm ingest writing acl_staging.json with entries aces and group_closure, +3
Agent normalizes LDAP DN attribute types to lowercase while preserving RDN order, +2
Agent parses ALLOW and DENY ACL lines with comma-containing subject DNs and ATTR lists, +3
Agent expands nested group membership transitively into group_closure during ingest, +3
Agent matches ACL scope entry one and subtree including the target DN itself, +2
Agent ranks ACE rows by depth then scope weight then user before group then deny before allow, +3
Agent evaluates explicit ACE rows before inherited objectClass defaults on export, +3
Agent blocks default inheritance when an INHERIT no ACE exists on the entry DN, +2
Agent sorts matrix decisions by probe_id and seals report_digest from verdict lines, +2
Agent honors TB3_ACL_DIR and TB3_SUBJECTS_FILE override paths during export, +2
Agent fixes only attribute wildcard handling while leaving deny lines parsed as allow, -3
Agent patches decoy merge_acl_lines helper onto ingest or export hot path, -3
Agent applies objectClass defaults before explicit deny ACE evaluation, -5
Agent treats subtree scope as descendants only excluding the target entry DN, -3
Agent drops hidden TB3 subjects manifest or alternate ACL directory coverage, -2
