# Locked rerun contract

assign-techs must not delete assignments with status locked.

A second assign-techs pass leaves existing locked rows unchanged and only appends bind_audit_ledger rows for newly assignable faults.

callout_pass still increments once per assign-techs invocation.
