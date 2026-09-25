package publish

import (
    "database/sql"
    "encoding/json"
    "os"
    "sort"

    _ "modernc.org/sqlite"

    "github.com/terminus/venuetixctl/internal/model"
)

const (
    logPath      = "/app/work/seat-map-pass.json"
    passPath     = "/app/state/map-pass-count.json"
    sqlitePath   = "/app/output/venue-seat-ledger.sqlite"
    conflictPath = "/app/output/hold-conflict-atlas.json"
)

type passCounter struct {
    ReconcilePass int `json:"map_pass_count"`
}

func WriteStatus(scenario string) error {
    var counter passCounter
    raw, err := os.ReadFile(passPath)
    if err != nil {
        return err
    }
    if err := json.Unmarshal(raw, &counter); err != nil {
        return err
    }
    if counter.ReconcilePass <= 0 {
        return os.ErrInvalid
    }
    logRaw, err := os.ReadFile(logPath)
    if err != nil {
        return err
    }
    var logBody struct {
        Scenario    string             `json:"scenario"`
        Assignments []model.Assignment `json:"assignments"`
        Conflicts   []model.Conflict   `json:"conflicts"`
        RunStamp    string             `json:"run_stamp"`
    }
    if err := json.Unmarshal(logRaw, &logBody); err != nil {
        return err
    }
    conflicts := logBody.Conflicts
    sort.SliceStable(conflicts, func(i, j int) bool {
        if conflicts[i].Severity != conflicts[j].Severity {
            return conflicts[i].Severity > conflicts[j].Severity
        }
        return conflicts[i].HoldID < conflicts[j].HoldID
    })
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    if err := writeSQLite(logBody.Assignments, logBody.RunStamp, scenario, counter.ReconcilePass); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario":  scenario,
        "engine":    "venuetixctl",
        "run_stamp": logBody.RunStamp,
        "conflicts": conflicts,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(conflictPath, body, 0o644)
}

func writeSQLite(assignments []model.Assignment, runStamp, scenario string, reconcilePass int) error {
    if _, err := os.Stat(sqlitePath); err == nil {
        _ = os.Remove(sqlitePath)
    }
    db, err := sql.Open("sqlite", sqlitePath)
    if err != nil {
        return err
    }
    defer db.Close()
    if _, err := db.Exec(`CREATE TABLE seat_status (
        seat_id TEXT PRIMARY KEY,
        hold_id TEXT,
        order_id TEXT,
        status TEXT
    )`); err != nil {
        return err
    }
    if _, err := db.Exec(`CREATE TABLE reconcile_meta (
        scenario TEXT,
        run_stamp TEXT,
        map_pass_count INTEGER
    )`); err != nil {
        return err
    }
    if _, err := db.Exec(
        `INSERT INTO reconcile_meta(scenario, run_stamp, map_pass_count) VALUES (?,?,?)`,
        scenario, runStamp, reconcilePass,
    ); err != nil {
        return err
    }
    sort.SliceStable(assignments, func(i, j int) bool {
        return assignments[i].SeatID < assignments[j].SeatID
    })
    for _, a := range assignments {
        if _, err := db.Exec(
            `INSERT INTO seat_status(seat_id, hold_id, order_id, status) VALUES (?,?,?,?)`,
            a.SeatID, a.HoldID, a.OrderID, a.Status,
        ); err != nil {
            return err
        }
    }
    return nil
}
