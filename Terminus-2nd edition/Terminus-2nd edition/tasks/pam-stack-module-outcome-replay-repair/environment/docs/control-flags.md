# Control flags

Stub modules return a numeric exit code (PAM-style). The replay engine interprets `control` on each entry:

| Control | Behavior |
|---------|----------|
| `required` | On non-zero module exit, remember phase failure and **continue** remaining modules in the same phase |
| `requisite` | On non-zero module exit, **stop the phase immediately** (later modules in that phase do not run) |
| `sufficient` | On zero exit when the phase has no prior failure, **stop the phase immediately** (success). A later `sufficient` success **must not** clear an earlier `required`/`requisite` failure. |
| `optional` | Ignore module exit code; the module **still runs** and is audited even after an earlier `required`/`requisite` failure in the same phase |

Phase succeeds only when no `required`/`requisite` failure was recorded. A phase stopped early by `requisite` failure fails the overall stack unless an earlier `sufficient` already ended the phase successfully.

A later `sufficient` success with exit code `0` **must not** clear an earlier `required`/`requisite` failure in the same phase. When `failed` is already set, `sufficient` must not stop the phase as success.

Treat `requisite` and `required` differently: **`requisite` must short-circuit**; **`required` must not**.
