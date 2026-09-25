# Environment variables

HOST and HOSTNAME are distinct values used in `* ? $HOST` and `* ? $HOSTNAME` conditions. Each passes when the corresponding value appears in the message headers.

Defaults come from suite.meta.json in each suite directory. SET lines in the rc override defaults before recipes run.

ORGMAIL is the fallback mbox path used when a nested block completes without any inner recipe delivering (see fork-orgmail.md). It must be an absolute path.

The snapshot records the effective HOST, HOSTNAME, and ORGMAIL used for the run under `environment`.
