package reconcile

import (
    "encoding/json"
    "os"

    "github.com/terminus/holdfairctl/internal/branchsel"
    "github.com/terminus/holdfairctl/internal/dbread"
    "github.com/terminus/holdfairctl/internal/passmark"
    "github.com/terminus/holdfairctl/internal/model"
    "github.com/terminus/holdfairctl/internal/patronbar"
    "github.com/terminus/holdfairctl/internal/priqueue"
)

const (
    logPath    = "/app/work/reconcile-log.json"
    passPath   = "/app/state/reconcile-pass.json"
    rollupPath = "/app/state/hold-queue-rollup.json"
)

type passCounter struct {
    ReconcilePass int    `json:"reconcile_pass"`
    RunStamp      string `json:"run_stamp"`
}

func RunFairness(scenario string) error {
    db, err := dbread.Open("/app/state/active-library.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
        if v := os.Getenv("TB3_RECONCILE_DATE"); v != "" {
            meta.ReconcileDate = v
        }
        if v := os.Getenv("RECONCILE_DATE_OVERRIDE"); v != "" {
            meta.ReconcileDate = v
        }
    branches, err := dbread.ReadBranches(db)
    if err != nil {
        return err
    }
    branchMap := map[string]model.Branch{}
    for _, b := range branches {
        branchMap[b.BranchID] = b
    }
    patrons, err := dbread.ReadPatrons(db)
    if err != nil {
        return err
    }
    patronMap := map[string]model.Patron{}
    for _, p := range patrons {
        patronMap[p.PatronID] = p
    }
    holds, err := dbread.ReadHolds(db)
    if err != nil {
        return err
    }
    copies, err := dbread.ReadCopies(db)
    if err != nil {
        return err
    }
    suspensions, err := dbread.ReadSuspensions(db)
    if err != nil {
        return err
    }
    policies, err := dbread.ReadPolicies(db)
    if err != nil {
        return err
    }
    rankMap := map[string]int{}
    for _, pol := range policies {
        rankMap[pol.ClassName] = pol.Rank
    }
    rollupRaw, err := os.ReadFile(rollupPath)
    if err != nil {
        return err
    }
    var rollup map[string]any
    if err := json.Unmarshal(rollupRaw, &rollup); err != nil {
        return err
    }
    digest, _ := rollup["rollup_fingerprint"].(string)
    stamp := passmark.RunStamp(digest)
    var ranked []priqueue.RankedHold
    for _, h := range holds {
        if patronbar.IsSuspended(h.PatronID, meta.ReconcileDate, suspensions) {
            continue
        }
        p := patronMap[h.PatronID]
        ranked = append(ranked, priqueue.RankedHold{
            Hold:     h,
            TierRank: rankMap[p.PriorityClass],
        })
    }
    priqueue.SortHolds(ranked)
    used := map[string]bool{}
    var assignments []model.Assignment
    queuePos := 1
    for _, rh := range ranked {
        avail := []model.ItemCopy{}
        for _, c := range copies {
            if used[c.CopyID] {
                continue
            }
            avail = append(avail, c)
        }
        pick := branchsel.SelectCopy(avail, rh.Hold.ItemID, rh.Hold.PickupBranchID, branchMap)
        if pick == nil {
            continue
        }
        used[pick.CopyID] = true
        assignments = append(assignments, model.Assignment{
            QueuePos:  queuePos,
            PatronID:  rh.Hold.PatronID,
            RequestID: rh.Hold.RequestID,
            CopyID:    pick.CopyID,
            BranchID:  pick.BranchID,
        })
        queuePos++
    }
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    logBody, err := json.Marshal(map[string]any{
        "scenario":    scenario,
        "assignments": assignments,
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
