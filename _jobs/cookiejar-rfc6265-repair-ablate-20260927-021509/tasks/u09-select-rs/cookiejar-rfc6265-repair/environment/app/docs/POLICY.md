# Storage policy

Replays of long crawls used to grow the store without bound, so crumbjar
caps how many cookies one site can keep.

## Sites

A cookie belongs to the site of its domain field (for a host-only cookie
that is the host it was set by). The site of a domain is:

1. the domain itself, if it is an IPv4 address or a public suffix;
2. otherwise the longest public suffix that is a proper suffix of the domain
   (on a label boundary), plus the label directly in front of it
   (`a.b.example.co.uk` belongs to `example.co.uk`);
3. otherwise, when no listed suffix applies, its last two labels (or the
   domain itself if it has fewer).

## Limit

A site may hold at most 6 cookies.

After a cookie has been stored (and expired cookies removed), if its site
holds more than 6 cookies, crumbjar evicts cookies of that site one at a
time until 6 remain. The cookie evicted each time is the one with the
oldest last-access-time; among cookies with the same last-access-time,
the one with the oldest creation-time goes first.

Times compare by clock value first and by transcript order within one clock
value, so two cookies only share a last-access-time when they were last sent
in the same request.

Replacing an existing cookie (same name, domain and path) does not change
the count. Cookies of other sites are never evicted to make room.
