package nightopt

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/overbookctl/internal/sqlpull"
    "github.com/terminus/overbookctl/internal/guestshield"
    "github.com/terminus/overbookctl/internal/blackoutcal"
    "github.com/terminus/overbookctl/internal/model"
    "github.com/terminus/overbookctl/internal/tierlift"
    "github.com/terminus/overbookctl/internal/costmin"
)

const (
    planScoresPath = "/app/work/overbook-plan-scores.json"
    planPath    = "/app/work/overbook-plan.json"
    passPath   = "/app/state/solve-pass.json"
)

type scoreRow struct {
    ReservationID string  `json:"reservation_id"`
    GuestID       string  `json:"guest_id"`
    DemandScore   float64 `json:"demand_score"`
}

type passCounter struct {
    SolvePass int    `json:"solve_pass"`
    RunStamp   string `json:"run_stamp"`
}

func RunPlan(scenario string) error {
    db, err := sqlpull.Open("/app/state/active-hotel.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := sqlpull.ReadMeta(db)
    if err != nil {
        return err
    }
    if v := os.Getenv("TB3_NIGHT_DATE"); v != "" {
        meta.NightDate = v
    }
    roomTypes, err := sqlpull.ReadRoomTypes(db)
    if err != nil {
        return err
    }
    typeMap := map[string]model.RoomType{}
    for _, rt := range roomTypes {
        typeMap[rt.RoomTypeID] = rt
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
    loyaltyPolicies, err := sqlpull.ReadLoyalty(db)
    if err != nil {
        return err
    }
    substRules, err := sqlpull.ReadSubstitutions(db)
    if err != nil {
        return err
    }
    walkCosts, err := sqlpull.ReadWalkCosts(db)
    if err != nil {
        return err
    }
    scoreRaw, err := os.ReadFile(planScoresPath)
    if err != nil {
        return err
    }
    var scoreBody struct {
        Scores []scoreRow `json:"scores"`
    }
    if err := json.Unmarshal(scoreRaw, &scoreBody); err != nil {
        return err
    }
    scoreMap := map[string]float64{}
    for _, s := range scoreBody.Scores {
        scoreMap[s.ReservationID] = s.DemandScore
    }
    snapRaw, err := os.ReadFile("/app/state/capacity-snapshot.json")
    if err != nil {
        return err
    }
    var snapMap map[string]any
    _ = json.Unmarshal(snapRaw, &snapMap)
    digest, _ := snapMap["capacity_fingerprint"].(string)
    stamp := digest[:16]

    var queue []ranked
    for _, res := range reservations {
        queue = append(queue, ranked{Res: res, Score: scoreMap[res.ReservationID]})
    }
    sortDemandQueue(queue)

    usedRooms := map[string]bool{}
    var assignments []model.RoomAssignment
    var walks []model.WalkEntry

    for _, item := range queue {
        res := item.Res
        assigned := false
        for _, room := range rooms {
            if usedRooms[room.RoomID] {
                continue
            }
            if room.RoomTypeID != res.RoomTypeID {
                continue
            }
            if room.Status != "available" {
                continue
            }
            if blackoutcal.RoomBlocked(room.RoomID, meta.NightDate, maintenance) {
                continue
            }
            usedRooms[room.RoomID] = true
            assignments = append(assignments, model.RoomAssignment{
                ReservationID: res.ReservationID,
                GuestID:       res.GuestID,
                RoomID:        room.RoomID,
                RoomTypeID:    room.RoomTypeID,
            })
            assigned = true
            break
        }
        if assigned {
            continue
        }
        for _, room := range rooms {
            if usedRooms[room.RoomID] {
                continue
            }
            if !tierlift.AllowedUpgrade(res.RoomTypeID, room.RoomTypeID, typeMap, substRules) {
                continue
            }
            if room.Status != "available" {
                continue
            }
            if blackoutcal.RoomBlocked(room.RoomID, meta.NightDate, maintenance) {
                continue
            }
            usedRooms[room.RoomID] = true
            assignments = append(assignments, model.RoomAssignment{
                ReservationID: res.ReservationID,
                GuestID:       res.GuestID,
                RoomID:        room.RoomID,
                RoomTypeID:    room.RoomTypeID,
            })
            assigned = true
            break
        }
        if assigned {
            continue
        }
        pick := costmin.PickWalk(res.RoomTypeID, typeMap, substRules, walkCosts)
        if pick == nil {
            continue
        }
        walks = append(walks, model.WalkEntry{
            ReservationID: res.ReservationID,
            GuestID:       res.GuestID,
            FromTypeID:    res.RoomTypeID,
            ToTypeID:      pick.ToTypeID,
            WalkCostCents: pick.WalkCostCents,
        })
        _ = guestshield.ShouldWalkFirst(res.LoyaltyTier, "standard", loyaltyPolicies)
    }

    sort.Slice(assignments, func(i, j int) bool {
        return assignments[i].ReservationID < assignments[j].ReservationID
    })
    sortPlanWalks(walks)

    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    logBody, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "assignments": assignments,
        "walks":       walks,
        "run_stamp":   stamp,
    })
    if err != nil {
        return err
    }
    if err := os.WriteFile(planPath, logBody, 0o644); err != nil {
        return err
    }
    var counter passCounter
    if raw, err := os.ReadFile(passPath); err == nil {
        _ = json.Unmarshal(raw, &counter)
    }
    counter.SolvePass++
    counter.RunStamp = stamp
    passRaw, err := json.Marshal(counter)
    if err != nil {
        return err
    }
    return os.WriteFile(passPath, passRaw, 0o644)
}
