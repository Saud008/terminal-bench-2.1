package reconcile

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/venuetixctl/internal/accessfloor"
    "github.com/terminus/venuetixctl/internal/captureorder"
    "github.com/terminus/venuetixctl/internal/expirygate"
    "github.com/terminus/venuetixctl/internal/model"
    "github.com/terminus/venuetixctl/internal/passseal"
    "github.com/terminus/venuetixctl/internal/rowguard"
    "github.com/terminus/venuetixctl/internal/venuesql"
)

const (
    logPath     = "/app/work/seat-map-pass.json"
    passPath    = "/app/state/map-pass-count.json"
    snapshotPath = "/app/state/seat-hold-snapshot.json"
)

type passCounter struct {
    ReconcilePass int    `json:"map_pass_count"`
    RunStamp      string `json:"run_stamp"`
}

func RunMap(scenario string) error {
    db, err := dbread.Open("/app/state/event-venue.sqlite")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
    if v := os.Getenv("TB3_EVENT_CLOCK"); v != "" {
        meta.EventClock = v
    }
    sections, err := dbread.ReadSections(db)
    if err != nil {
        return err
    }
    sectionMap := map[string]model.Section{}
    for _, s := range sections {
        sectionMap[s.SectionID] = s
    }
    seats, err := dbread.ReadSeats(db)
    if err != nil {
        return err
    }
    seatMap := map[string]model.Seat{}
    for _, s := range seats {
        seatMap[s.SeatID] = s
    }
    orders, err := dbread.ReadOrders(db)
    if err != nil {
        return err
    }
    orderMap := map[string]model.Order{}
    for _, o := range orders {
        orderMap[o.OrderID] = o
    }
    holds, err := dbread.ReadHolds(db)
    if err != nil {
        return err
    }
    snapshotRaw, err := os.ReadFile(snapshotPath)
    if err != nil {
        return err
    }
    var snapshot map[string]any
    if err := json.Unmarshal(snapshotRaw, &snapshot); err != nil {
        return err
    }
    digest, _ := snapshot["hold_snapshot_digest"].(string)
    stamp := passseal.RunStamp(digest)
    var ranked []captureorder.RankedHold
    for _, h := range holds {
        if !expirygate.IsActive(h, meta.EventClock) {
            continue
        }
        ranked = append(ranked, captureorder.RankedHold{Hold: h, Order: orderMap[h.OrderID]})
    }
    captureorder.SortHolds(ranked)
    sort.Slice(ranked, func(i, j int) bool {
        return ranked[i].Hold.HoldID < ranked[j].Hold.HoldID
    })
    assigned := map[string]bool{}
    seatTaken := map[string]string{}
    var assignments []model.Assignment
    var conflicts []model.Conflict
    for _, rh := range ranked {
        seat, ok := seatMap[rh.Hold.SeatID]
        if !ok {
            conflicts = append(conflicts, model.Conflict{
                HoldID: rh.Hold.HoldID, SeatID: rh.Hold.SeatID,
                Reason: "unknown_seat", Severity: 3,
            })
            continue
        }
        if owner, taken := seatTaken[rh.Hold.SeatID]; taken {
            conflicts = append(conflicts, model.Conflict{
                HoldID: rh.Hold.HoldID, SeatID: rh.Hold.SeatID,
                Reason: "seat_taken:" + owner, Severity: 2,
            })
            continue
        }
        sec := sectionMap[seat.SectionID]
        if !rowguard.AllowsAssignment(seat, assigned, seats) {
            conflicts = append(conflicts, model.Conflict{
                HoldID: rh.Hold.HoldID, SeatID: rh.Hold.SeatID,
                Reason: "adjacency_block", Severity: 4,
            })
            continue
        }
        if !accessfloor.AllowsAccessible(seat, sec, assigned, seats) {
            conflicts = append(conflicts, model.Conflict{
                HoldID: rh.Hold.HoldID, SeatID: rh.Hold.SeatID,
                Reason: "a11y_reserve", Severity: 5,
            })
            continue
        }
        assigned[rh.Hold.SeatID] = true
        seatTaken[rh.Hold.SeatID] = rh.Hold.HoldID
        assignments = append(assignments, model.Assignment{
            HoldID: rh.Hold.HoldID, SeatID: rh.Hold.SeatID,
            OrderID: rh.Hold.OrderID, Status: "held",
        })
    }
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    logBody, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "assignments": assignments,
        "conflicts":   conflicts,
        "run_stamp":   stamp,
    })
    if err != nil {
        return err
    }
    if err := os.WriteFile(logPath, logBody, 0o644); err != nil {
        return err
    }
    var counter passCounter
    if raw, err := os.ReadFile(passPath); err == nil {
        _ = json.Unmarshal(raw, &counter)
    }
    counter.ReconcilePass++
    counter.RunStamp = stamp
    passRaw, err := json.Marshal(counter)
    if err != nil {
        return err
    }
    return os.WriteFile(passPath, passRaw, 0o644)
}
