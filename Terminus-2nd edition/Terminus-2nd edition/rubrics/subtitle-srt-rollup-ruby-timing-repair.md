# Platform rubric — subtitle-srt-rollup-ruby-timing-repair

**Task folder:** tasks/subtitle-srt-rollup-ruby-timing-repair/
**Written:** 2026-06-26T00:45:00Z
**Upload:** copy lines below into Snorkel platform rubric form (not in zip).

Agent parses SRT with BOM, CRLF, comma and dot millis timestamps, +3
Agent applies seed offset from FNV-1a64 before overlap and ruby stages, +3
Agent resolves overlaps before ruby caps on overlap-trimmed cue ends, +3
Agent extends ruby segment ends under an8 by 250 ms capped at cue end, +3
Agent writes normalize snapshot and sealed ledger in stage one, +3
Agent validates snapshot digest and export_seq in publish stage two, +3
Agent rolls up cues with space join preserving ruby segments, +2
Agent exports from staged snapshot without re-parsing source SRT, +3
Agent increments export_seq marker across repeat normalize runs, +2
Agent rebuilds srtctl with cargo before pytest subprocess calls, +2
Agent hardcodes export JSON without running srtctl normalize, -3
Agent routes publish through broken_lib legacy single-pass rebuild, -3
Agent applies ruby shifts before overlap trim on combo fixtures, -3
Agent joins rolled-up cue text with newlines instead of ASCII space, -2
Agent seals ledger snapshot_digest with fixture name instead of bytes, -2
Agent leaves export indices zero-based instead of one-based, -2
