# Whitespace contract

Sequence grammars may declare sequence_terminator (for example semicolon).

Optional WS tokens are skipped only between sequence items before matching the next item pattern.

Whitespace must not be consumed immediately after a sequence terminator token. A WS token following a terminator is part of the next item boundary, not trailing padding after the terminator.

Expression grammars (calc-style) strip standalone WS tokens from the token stream before climbing.
