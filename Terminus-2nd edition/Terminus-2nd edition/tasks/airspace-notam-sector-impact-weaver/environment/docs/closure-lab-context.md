# Closure lab context

`airclos` is a host-local airspace impact-closure control plane. Given a campaign of NOTAM rows, sector polygons, filed flights, and airway tables, it admits which sectors and route legs close over a single scheduling minute, then seals the result as a reproducible impact-closure atlas. There is no live AIM feed; every input is a fixture bundle under `/app/fixtures/scenarios`.

The lab composes five closure lemmas that must agree with the reference math:

- amendment closure — keep the maximum amendment per `series_id` before anything else (`amendment-closure-lemma.md`).
- chronology window — decide activation over a wrapping minute axis, including windows that cross midnight (`chronology-window-lemma.md`).
- sector spatial — ray-cast point-in-polygon with inclusive boundary for concave sectors (`sector-spatial-lemma.md`).
- runway normalization — canonicalize runway designators before matching closures (`runway-normalization-lemma.md`).
- airway expansion — expand airway tokens into their fix sequences before route matching (`airway-expansion-lemma.md`).

Each lemma feeds the next: bind the campaign, resolve the active chronology (amendment + window), fold the closure lattice (spatial + runway + route), and seal the atlas. Treating NOTAM text as plain substring matching, keeping the first-seen amendment, or skipping the wrapping window all produce a lattice that fails the reference digests. The `/app/internal/wrap` METAR envelope helper is dashboard-only and never contributes to the sealed atlas.
