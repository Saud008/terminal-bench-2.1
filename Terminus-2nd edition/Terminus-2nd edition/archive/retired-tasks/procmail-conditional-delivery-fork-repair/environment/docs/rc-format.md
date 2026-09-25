# Procmailrc format (simulator subset)

Each suite directory contains `procmail.rc` and `messages.mbox`.

## Variable assignments

Lines `SET NAME=value` assign delivery environment variables. Names are case-sensitive. Leading and trailing whitespace on values is trimmed.

Supported names: HOST, HOSTNAME, ORGMAIL.

## Recipe headers

A recipe begins with `:0` followed by optional flags:

- `h` — conditions match headers only (lines before the first blank line in the message).
- `c` — after a successful delivery at this recipe, continue evaluating sibling recipes at the same block level instead of stopping.
- `lock=NAME` — acquire a lockfile before evaluating this recipe block. NAME is a basename only.

A nested block starts on the line after the header with `{` alone on a line. Inner recipes follow until a line with `}` alone closes the block.

## Conditions

Lines starting with `*` are conditions (all must match):

- `* REGEX` — extended regex match against the selected text (full message or headers when `h` is set on this recipe).
- `* ? $HOSTNAME` — true when the HOSTNAME value appears in the message headers.
- `* ? $HOST` — true when the HOST value appears in the message headers.

## Delivery target

The first non-comment line after conditions that does not start with `:` or `*` or `{` or `}` is the mbox path (absolute).

Recipe ids are assigned in file order as r1, r2, …; nested recipes use dotted ids (r2.1, r2.2).
