# Platform rubric — subtitle-srt-rollup-ruby-normalize

**Task folder:** tasks/subtitle-srt-rollup-ruby-normalize/

Agent applies overlap trim before ruby segment caps in stage 1, +3
Agent persists post-ruby cues in normalize-snapshot.json without roll-up merge, +3
Agent seals normalize-ledger.json snapshot_digest over raw snapshot bytes, +3
Agent reads staged snapshot cues in stage 2 instead of re-parsing source SRT, +3
Agent joins roll-up absorbed text with single ASCII space between cues, +3
Agent increments export_seq from export-seq.marker on each successful normalize, +2
Agent emits byte-identical export JSON on repeat normalize with rising export_seq, +2
Agent extends ruby segment ends by 250 ms capped at cue end when an8 present, +3
Agent trims overlapping cue end_ms to next cue start_ms after seed offset, +2
Agent parses SRT timestamps with comma or dot millis separators, +2
Agent writes export format srt-normalized-v1 with 1-based cue index field, +2
Agent honors procedural combo seed overlap and ruby coupling in one file, +2
Agent preserves ruby segments on roll-up merged export rows with space join, +2
Agent rejects ledger when snapshot_digest does not match snapshot file bytes, -3
Agent applies ruby shifts before overlap resolution in stage 1, -3
Agent rebuilds export cues from source SRT path during stage 2 publish, -3
Agent joins roll-up cues with newline instead of ASCII space, -2
Agent leaves export_seq fixed at one across repeat normalize runs, -2
