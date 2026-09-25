# line_format escape normalization

After json parsing, string fields may contain JSON escape sequences such as backslash-n and backslash-t as two character sequences.

The line_format stage must expand these escapes before substituting into the template and before unwrap reads numeric fields from formatted output.

Supported expansions: backslash-n to newline, backslash-t to tab, backslash-r to carriage return, backslash-quote to quote, backslash-backslash to backslash.
