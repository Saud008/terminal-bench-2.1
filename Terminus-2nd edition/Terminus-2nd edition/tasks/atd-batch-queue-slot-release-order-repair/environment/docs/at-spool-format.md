# at spool format

Each job file lives under /app/var/spool/at/jobs/ as LETTER plus zero-padded sequence from .SEQ, for example a0000000042.

The first line is a header with space-separated KEY=VALUE tokens:

ATQ_EPOCH=<unix epoch when job becomes runnable> BATCH=<batch name> JOB=<job id>

Following lines are the shell script body copied from the scenario scripts directory.

A job completes when the spool file is removed. Batch letter slots are released only after the spool file is gone, never immediately after the initial write.
