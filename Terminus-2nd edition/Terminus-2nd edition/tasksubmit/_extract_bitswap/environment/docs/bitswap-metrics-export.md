# Metrics schema

Path: argument to --output on metrics command.

Fields:

report_version — always 1.

session_id — session name.

queue_head_cid — display cid of highest priority active want not tombstoned.

queue_head_priority — priority of queue head.

cancel_merged — always true for bundled metrics fixtures.

Priority queue skips tombstoned canonical keys and picks highest priority then lexicographic display cid.
