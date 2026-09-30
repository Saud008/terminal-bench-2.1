# Transcript format

A transcript is UTF-8 text, one command per line. Blank lines and lines
whose first non-blank character is `#` are ignored. Leading blanks are
ignored; a single space separates a command from its arguments.

| Command | Meaning |
|---|---|
| `at <seconds>` | Set the replay clock (seconds since the epoch, UTC). |
| `set <url> <set-cookie-string>` | A response to a request for `<url>` carried a `Set-Cookie` header whose field value is `<set-cookie-string>`. |
| `get <url>` | The user agent sends an HTTP request to `<url>`. |
| `dump` | Print the cookie store. |

The clock starts at 0 and may never move backwards. It only changes on
`at`; any number of events can happen at the same clock value, and they
happen in transcript order.

For `set`, everything after the space that follows the URL, up to the end of
the line, is the header field value, byte for byte (no `Set-Cookie:` prefix).
Each `set` line is one header; a response with several `Set-Cookie` headers
is written as several `set` lines.

Every `set` and `get` is an HTTP API in the sense of RFC 6265 (there is no
script access to cookies in a replay).

## URLs

Only `http://` and `https://` URLs are accepted (scheme case-insensitive).
`https` is the only secure protocol. The host is lower-cased; a `:port`
suffix is dropped, and cookies do not depend on the port. IPv6 literals and
user information are not supported. The request path is the URL path
without query or fragment, or `/` if the URL has no path.

## Example

```
at 1767225600
set https://www.example.com/account/login sid=31d4d96e; Path=/; Secure; HttpOnly
set https://www.example.com/account/login lang=en-US; Max-Age=86400
get https://www.example.com/account/settings
at 1767312001
get https://www.example.com/account/settings
dump
```
