# SRT fixture format

Each fixture under `/app/fixtures/` is a SubRip (`.srt`) file.

## Block layout

1. **Index line** — decimal cue number from the file (not a synthetic counter).
2. **Timing line** — `HH:MM:SS,mmm --> HH:MM:SS,mmm` (hours, minutes, seconds, milliseconds).
3. **Text lines** — one or more lines until a blank line ends the block.

Blocks are separated by one or more blank lines. Files may begin with a UTF-8 BOM (`EF BB BF`). Lines may use LF or CRLF line endings.

## Millisecond separator

SubRip uses a comma before milliseconds. Input files may use either a comma or a dot; normalized export always uses a comma.

## Inline ruby

Cue text may include ASS-style alignment prefix `{\an8}` and inline ruby pairs written as `base{rt}reading`. The `{rt}` marker is literal in the file. Ruby segments inherit the cue start time with an initial end equal to the segment start; when `{\an8}` is present anywhere in the cue text, each ruby segment’s end time is extended by `ruby_shift_ms` (250 ms), capped at the cue end time after overlap trimming and seed offset.

## Multiline text

Only the timing line matches the timestamp pattern. Text lines may contain the substring `-->` without starting a new cue.
