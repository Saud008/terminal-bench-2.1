# Evacuation zone alert playtest workflow

This task is a **games** evacuation-zone playtest and sealed alert-bundle workflow. County playfield operators reconcile fire-perimeter polygons, evacuation-zone footprints, road-closure graphs, and shelter-capacity assays into a sealed alert bundle with weave-ledger artifacts. The agent extends polygon intersection, ray-cast containment, closed-edge routing, quota scoring, and severity-tier precedence on the working baseline under /app so bundle export matches independent reference helpers.

## Playtest scope

| Stage | Closure invariant | Reference |
|-------|-------------------|-----------|
| Coordinate geometry | Flat-km coordinates, winding, zone centroids | `/app/docs/coordinate-geometry-contract.md` |
| Fire-zone intersection | Ray-cast point-in-polygon and segment intersection (not bbox-only) | `/app/docs/fire-zone-intersection-contract.md` |
| Road routing | Shortest open path with closed segment suppression | `/app/docs/road-closure-routing-contract.md` |
| Shelter quotas | Remaining capacity decrements; nearest reachable shelter | `/app/docs/shelter-quota-contract.md` |
| Severity precedence | Numeric tier ordering for alert ranking | `/app/docs/severity-precedence-contract.md` |
| Weave digest | Deterministic closure over calibrated assignment rows | `/app/docs/lane-ledger-schema.md` |
| Bundle digest | Deterministic closure over sorted alert rows | `/app/docs/output-bundle-contract.md` |

## Three-stage playtest pipeline

Stage 1 (`bind`) admits a scenario pack and binds it to a run id. Stage 2 (`weave`) materializes calibrated intersection, routing, and quota rows at `/app/state/evac-lane-ledger.json`. Stage 3 (`seal`) reads the on-disk weave ledger only and emits alert bundle JSON. Stage order is fixed: geometry and routing before quota assignment, and weave digest before seal so export rows use calibrated ledger bytes.

## Deliverables

- Weave ledger JSON at `/app/state/evac-lane-ledger.json`
- Alert bundle JSON at the caller `--output` path
- Deterministic digests and assignments matching independent reference helpers in pytest

## Tolerance and verification

Pytest recomputes polygon intersection, routing, shelter quotas, severity ordering, and digests with independent reference helpers. Hidden procedural fixtures under `/opt/verifier-fixtures/k7cal/` exercise zone-alias and closure traps not covered by bundled fixtures alone.
