# ACL block format

ACL files use blocks separated by --- lines. Each block begins with TARGET, SCOPE, and INHERIT lines followed by ALLOW or DENY rules.

ALLOW and DENY lines use the form:

  ALLOW group cn=readers,ou=groups,dc=example,dc=com read,search ATTR *

Rights are comma-separated tokens such as read, write, search, delete. ATTR lists name one attribute or star for all attributes.

DENY rules must be preserved with effect deny during ingest. They are not aliases for allow.

During ingest each rule is flattened into the staging `aces` array. Assign `ace_id` as `{acl_file_stem}:{block_index}:{rule_index}` where `block_index` counts `---`-separated blocks in file order starting at 0 and `rule_index` counts ALLOW/DENY lines within the block starting at 0. Example: the first rule in the first block of `mail.acl` is `mail:0:0`.
