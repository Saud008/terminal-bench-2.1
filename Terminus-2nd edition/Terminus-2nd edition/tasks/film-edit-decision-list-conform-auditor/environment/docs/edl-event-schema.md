# EDL event schema

CMX-style events contain eight whitespace-separated fields: edit number, reel name, track, transition, record in, record out, source in, source out.

AWK parsing emits tab-separated rows with those eight columns. Stage stores JSON objects with edit, reel, resolved_reel, record and source timecodes, frame counts, record and source span frames, and handle_budget_frames.

Record span frames must equal source span frames after correct drop-frame conversion for conforming edits unless a finding marks timecode_mismatch.
