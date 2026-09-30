# Cookie semantics

crumbjar is the user agent side of RFC 6265, "HTTP State Management
Mechanism" (April 2011), section 5: date parsing, `Set-Cookie` parsing, the
storage model and the `Cookie` header. It follows that RFC as published, not
the later rfc6265bis drafts; SameSite and cookie prefixes are ordinary
unknown attributes and names to crumbjar.

Where RFC 6265 leaves a choice to the user agent, crumbjar does this:

- **Representable times.** Expiry-times are whole seconds between
  0001-01-01T00:00:00Z (the earliest representable date) and
  9999-12-31T23:59:59Z (the latest). Out-of-range values are clamped to
  those bounds as section 5.2 describes.
- **Expiry.** A persistent cookie is expired once the clock is at or past
  its expiry-time. Expired cookies are removed before any cookie is stored
  or any `Cookie` header is built, and never show up in a `dump`.
- **Session cookies** keep living for the whole replay (the replay is a
  single session) and are shown with expiry `session`.
- **Empty Domain attribute.** Ignored, as the RFC recommends.
- **Public suffixes.** A domain is a public suffix exactly when it appears
  as a line in `data/public_suffix.dat`. Wildcard and exception rules of the
  upstream list are not supported. Section 5.3 step 5 is applied with this
  list.
- **Creation order.** Cookies created at the same clock value are ordered
  by transcript order.
- **Limits.** The per-site cookie limit is described in `POLICY.md`. There
  is no limit on cookie size and no global limit.
- **Canonical host names** are the lower-cased host of the URL; no IDNA
  processing.
