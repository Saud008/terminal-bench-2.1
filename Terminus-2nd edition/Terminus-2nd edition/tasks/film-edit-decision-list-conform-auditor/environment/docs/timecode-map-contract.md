# Timecode map contract

Bundle tc_map.json contains fps (integer), drop_frame (boolean), and pulldown (string: none or 23976).

When drop_frame is true at 30 fps, use SMPTE drop-frame math: skip two frame numbers at the start of each minute except every tenth minute. Worked examples: tc_to_frames 00:59:58:00 at 30 DF equals 107832 frames; tc_to_frames 01:00:03:00 at 30 DF equals 107982 frames; the span between them is 150 frames.

When drop_frame is false, use linear frame index: ((hours * 3600 + minutes * 60 + seconds) * fps + frames). Worked example: tc_to_frames 01:00:00:00 at 30 non-drop equals 108000 frames; five-second span to 01:00:05:00 equals 150 frames.

Seal digest uses hashlib sha256 over the sorted JSON of edits and diagnostics.

Timecode strings use HH:MM:SS:FF with zero padding.
