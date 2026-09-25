# Platform rubric — nmea0183-multipart-talker-checksum-merge

**Task folder:** tasks/nmea0183-multipart-talker-checksum-merge/

Agent XORs NMEA checksum bytes after the leading dollar sign only, +2
Agent splits quoted payload fields without stripping surrounding double quotes, +3
Agent normalizes GP and GN talker IDs to GN before multipart grouping, +2
Agent concatenates multipart payload from field index three onward in message-number order, +3
Agent buffers incomplete multipart groups in session state without reporting them, +2
Agent resolves duplicate message numbers on session replay by keeping the later fragment, +3
Agent validates snapshot groups use canonical talker prefixes before export, +2
Agent finalizes snapshot_digest from sorted compact JSON of groups and rejected lines, +3
Agent publishes merge reports from merge-snapshot.json without re-parsing the input stream, +3
Agent ignores active RMC lines whose navigation status is not A for date context, +2
Agent advances UTC calendar across month and year boundaries on midnight rollover, +2
Agent patches only talker normalization while leaving multipart field merge broken, -3
Agent fixes ingest compose but skips export digest verification and validate gate, -3
Agent routes multipart merge through legacy accumulate.rs instead of compose.rs, -2
Agent keeps orphan multipart fragment two in session pending without fragment one, -2
