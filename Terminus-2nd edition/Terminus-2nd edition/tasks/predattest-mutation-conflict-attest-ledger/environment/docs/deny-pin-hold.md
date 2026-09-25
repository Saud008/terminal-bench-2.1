# Deny-pin hold

`config.hold_attrs` is a list of pinned attribute names. An edit whose `attr`
is pinned is **held**: it is never written to the graph and appears in the
outcomes with reason `policy_hold`.

Matching is whole-attr **exact string equality**. A pinned name is not a
prefix or substring rule: with `hold_attrs = ["drain_token", "raw_secret"]`,
an edit on `drain_token_scope` is a different attribute and is admitted
normally.

Every distinct held attr contributes to the atlas field `held_attrs`
(sorted, de-duplicated). A held edit still resolves its target node identity
(so its `node` uid is reported in the outcome) but performs no write and does
not count toward `applied_edits`.
