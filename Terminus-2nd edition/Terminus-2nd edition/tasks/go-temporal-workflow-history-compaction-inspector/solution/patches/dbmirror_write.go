package dbmirror

import (
    "database/sql"
    "sort"

    _ "modernc.org/sqlite"

    "github.com/terminus/wfhistctl/internal/model"
)

func WriteDB(path string, rows []model.ActivityRow) error {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return err
    }
    defer db.Close()
    if _, err := db.Exec(`CREATE TABLE IF NOT EXISTS activity_inspection (
        run_generation INTEGER NOT NULL,
        activity_id TEXT NOT NULL,
        attempt INTEGER NOT NULL,
        status TEXT NOT NULL,
        risk_score INTEGER NOT NULL
    )`); err != nil {
        return err
    }
    sorted := append([]model.ActivityRow(nil), rows...)
    sort.Slice(sorted, func(i, j int) bool {
        if sorted[i].RunGeneration != sorted[j].RunGeneration {
            return sorted[i].RunGeneration < sorted[j].RunGeneration
        }
        if sorted[i].ActivityID != sorted[j].ActivityID {
            return sorted[i].ActivityID < sorted[j].ActivityID
        }
        return sorted[i].Attempt < sorted[j].Attempt
    })
    for _, row := range sorted {
        if _, err := db.Exec(
            `INSERT INTO activity_inspection (run_generation, activity_id, attempt, status, risk_score) VALUES (?, ?, ?, ?, ?)`,
            row.RunGeneration, row.ActivityID, row.Attempt, row.Status, row.RiskScore,
        ); err != nil {
            return err
        }
    }
    return db.Close()
}

func ReadActivityRows(path string) ([]model.ActivityRow, error) {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, err
    }
    defer db.Close()
    q, err := db.Query(`SELECT run_generation, activity_id, attempt, status, risk_score FROM activity_inspection ORDER BY rowid`)
    if err != nil {
        return nil, err
    }
    defer q.Close()
    var rows []model.ActivityRow
    for q.Next() {
        var r model.ActivityRow
        if err := q.Scan(&r.RunGeneration, &r.ActivityID, &r.Attempt, &r.Status, &r.RiskScore); err != nil {
            return nil, err
        }
        rows = append(rows, r)
    }
    return rows, q.Err()
}
