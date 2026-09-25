# Platform rubric — film-edit-decision-list-conform-auditor

**Task folder:** tasks/film-edit-decision-list-conform-auditor/

Agent applies SMPTE drop-frame minute-boundary correction when map marks drop_frame true, +3
Agent resolves reel aliases bidirectionally between vault ids and editorial shorthand, +3
Agent scales 23976 pull-down handle budgets with 24000 over 23976 rational math, +3
Agent checks missing media inventory after alias normalization, +2
Agent includes diagnostics bytes in staging_digest computation, +2
Agent blocks publish from reopening bundle EDL or alias paths after stage, +3
Agent keeps run_seq stable when restaging an unchanged bundle fingerprint, +2
Agent matches conform atlas diagnostics to independent reference_timecode oracle, +3
Agent treats timecode strings as opaque text without frame index conversion, -3
Agent uses linear frame math on drop-frame bundles, -3
Agent resolves aliases in forward direction only, -2
Agent flags alias_orphan before consulting missing media ledger, -3
Agent hashes edits only and omits diagnostics from staging_digest, -2
