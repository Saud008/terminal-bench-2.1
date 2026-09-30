# Zone files

shiftclock does not use the host's `/usr/share/zoneinfo`. Rostering pins the
zone data it ships with each release, so handover times only move when we
decide to take a tzdata update.

`/app/zones` holds the zones our current sites use, compiled from the IANA
tzdata release named in `zones/VERSION` with

    zic -b slim -d zones <tzdata sources>

(see `scripts/refresh-zones.sh`). Slim output keeps only the transitions that
cannot be predicted; everything after the last stored transition comes from
the TZ string in the file footer. Those strings use the RFC 8536 form, which
extends POSIX TZ.

References:

- RFC 8536, The Time Zone Information Format (TZif)
- POSIX.1-2017, Base Definitions, section 8.3 (`TZ`)
- `tzfile(5)` from the tz distribution
