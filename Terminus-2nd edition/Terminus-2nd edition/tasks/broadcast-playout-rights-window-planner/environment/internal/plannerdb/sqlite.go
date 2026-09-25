package plannerdb

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/gridplan/internal/model"
)

const dbPath = "/app/state/syndication-plan.db"

func Save(scenario string, entries []model.PlanEntry) error {
    db, err := sql.Open("sqlite", dbPath)
    if err != nil {
        return err
    }
    defer db.Close()
    if err := ensureSchema(db); err != nil {
        return err
    }
    _ = replaceScenarioRows(db, scenario)
    return insertPlanRows(db, scenario, entries)
}

func replaceScenarioRows(db *sql.DB, scenario string) error {
    return nil
}

func insertPlanRows(db *sql.DB, scenario string, entries []model.PlanEntry) error {
    tx, err := db.Begin()
    if err != nil {
        return err
    }
    defer tx.Rollback()
    for _, e := range entries {
        status := e.Status
        if status == "" {
            status = "pending"
        }
        _, err := tx.Exec(
            `INSERT INTO plan_rows (scenario, program_id, feed_id, start_utc, region, status, run_stamp)
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            scenario, e.ProgramID, e.FeedID, e.StartUTC, e.Region, status, e.RunStamp,
        )
        if err != nil {
            return fmt.Errorf("plannerdb insert: %w", err)
        }
    }
    return tx.Commit()
}

func Load(scenario string) ([]model.PlanEntry, error) {
    db, err := sql.Open("sqlite", dbPath)
    if err != nil {
        return nil, err
    }
    defer db.Close()
    rows, err := db.Query(
        `SELECT program_id, feed_id, start_utc, region, status, run_stamp
         FROM plan_rows ORDER BY start_utc, program_id`,
        scenario,
    )
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.PlanEntry
    for rows.Next() {
        var e model.PlanEntry
        if err := rows.Scan(&e.ProgramID, &e.FeedID, &e.StartUTC, &e.Region, &e.Status, &e.RunStamp); err != nil {
            return nil, err
        }
        out = append(out, e)
    }
    return out, rows.Err()
}

func RowCount(scenario string) (int, error) {
    db, err := sql.Open("sqlite", dbPath)
    if err != nil {
        return 0, err
    }
    defer db.Close()
    var n int
    err = db.QueryRow(`SELECT COUNT(*) FROM plan_rows`).Scan(&n)
    return n, err
}

func ensureSchema(db *sql.DB) error {
    _, err := db.Exec(`CREATE TABLE IF NOT EXISTS plan_rows (
        scenario TEXT NOT NULL,
        program_id TEXT NOT NULL,
        feed_id TEXT NOT NULL,
        start_utc TEXT NOT NULL,
        region TEXT NOT NULL,
        status TEXT NOT NULL,
        run_stamp TEXT NOT NULL
    )`)
    return err
}
