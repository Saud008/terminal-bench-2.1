package revsnap

import (
    "encoding/json"
    "os"

    "github.com/terminus/overbookctl/internal/sqlpull"
)

const (
    snapshotPath = "/app/state/capacity-snapshot.json"
    planScoresPath  = "/app/work/plan-scores.json"
)

type scoredRow struct {
    ReservationID string  `json:"reservation_id"`
    GuestID       string  `json:"guest_id"`
    DemandScore   float64 `json:"demand_score"`
}

func FreezeSnapshot(scenario string) error {
    db, err := sqlpull.Open("/app/state/active-hotel.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := sqlpull.ReadMeta(db)
    if err != nil {
        return err
    }
    rooms, err := sqlpull.ReadRooms(db)
    if err != nil {
        return err
    }
    maintenance, err := sqlpull.ReadMaintenance(db)
    if err != nil {
        return err
    }
    reservations, err := sqlpull.ReadReservations(db)
    if err != nil {
        return err
    }
    policies, err := sqlpull.ReadLoyalty(db)
    if err != nil {
        return err
    }
    digest := CapacityFingerprint(meta, rooms, maintenance)
    snapPayload, err := json.Marshal(map[string]any{
        "scenario":             scenario,
        "engine":               "walkcostctl",
        "capacity_fingerprint": digest,
        "room_count":           len(rooms),
        "maintenance_count":    0,
    })
    if err != nil {
        return err
    }
    if err := os.WriteFile(snapshotPath, snapPayload, 0o644); err != nil {
        return err
    }
    var rows []scoredRow
    for _, res := range reservations {
        rows = append(rows, scoredRow{
            ReservationID: res.ReservationID,
            GuestID:       res.GuestID,
            DemandScore:   ComputeDemandScore(res, policies),
        })
    }
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    scoreBody, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "demand_rows": rows,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(planScoresPath, scoreBody, 0o644)
}
