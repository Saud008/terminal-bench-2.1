# Dirty version guard

The schema_migrations row tracks version and dirty.

When an up step fails, dirty must be set to 1 and remain set until every down rollback step for that version in the journal has been executed.

A second up step must be rejected while dirty is 1.

The version integer must advance only after a successful up commit, never at up start.
