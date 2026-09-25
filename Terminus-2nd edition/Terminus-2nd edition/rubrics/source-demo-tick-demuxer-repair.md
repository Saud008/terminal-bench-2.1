# Platform rubric — source-demo-tick-demuxer-repair

**Task folder:** tasks/source-demo-tick-demuxer-repair/

Agent sorts demo discovery by full relative path not basename only, +3
Agent resolves string table indices with unsigned byte mask not signed cast, +3
Agent applies SIGNON_RESET packets to the running tick base during parse, +3
Agent deduplicates loop replay usercmds across the second packet pass, +3
Agent propagates demux-read exit code two for truncated packet bodies, +3
Agent leaves probe exit code two on truncated demos per exit-codes contract, +2
Agent counts signon_reset events separately in export stats not as usercmds, +2
Agent XOR-masks usercmd args with per-file seed digest before export, +2
Agent repairs shell pipeline modules under /app/lib without editing demux.c, +2
Agent edits fixture demo bytes or seeds under /app/fixtures, -5
Agent hardcodes tick-index JSON without running demo-index build, -3
Agent patches tests or verifier reference instead of lib shell modules, -3
Agent modifies protected docs or gendemo.py generator sources, -3
