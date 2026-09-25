package store

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/formulatrix/internal/model"
)

const DefaultDBPath = "/app/state/formulary.db"

func Open(path string) (*sql.DB, error) {
    if path == "" {
        path = DefaultDBPath
    }
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, err
    }
    schema := `CREATE TABLE IF NOT EXISTS matrix_rows (
        plan_id TEXT NOT NULL,
        ndc_normalized TEXT NOT NULL,
        preferred_rxnorm TEXT NOT NULL,
        requires_pa INTEGER NOT NULL,
        step_complete INTEGER NOT NULL,
        override_applied INTEGER NOT NULL,
        effective_rule TEXT NOT NULL,
        PRIMARY KEY (plan_id, ndc_normalized)
    )`
    if _, err := db.Exec(schema); err != nil {
        return nil, err
    }
    return db, nil
}

func InsertRows(db *sql.DB, rows []model.MatrixRow) error {
    for _, row := range rows {
        _, err := db.Exec(
            `INSERT INTO matrix_rows (plan_id, ndc_normalized, preferred_rxnorm, requires_pa, step_complete, override_applied, effective_rule)
             VALUES (?, ?, ?, ?, ?, ?, ?)`,
            row.PlanID, row.NDCNormalized, row.PreferredRxNorm,
            boolInt(row.RequiresPA), boolInt(row.StepComplete), boolInt(row.OverrideApplied),
            row.EffectiveRule,
        )
        if err != nil {
            return err
        }
    }
    return nil
}

func ReadRows(db *sql.DB) ([]model.MatrixRow, error) {
    rs, err := db.Query(`SELECT plan_id, ndc_normalized, preferred_rxnorm, requires_pa, step_complete, override_applied, effective_rule FROM matrix_rows`)
    if err != nil {
        return nil, err
    }
    defer rs.Close()
    var out []model.MatrixRow
    for rs.Next() {
        var row model.MatrixRow
        var pa, step, ovr int
        if err := rs.Scan(&row.PlanID, &row.NDCNormalized, &row.PreferredRxNorm, &pa, &step, &ovr, &row.EffectiveRule); err != nil {
            return nil, err
        }
        row.RequiresPA = pa != 0
        row.StepComplete = step != 0
        row.OverrideApplied = ovr != 0
        out = append(out, row)
    }
    return out, rs.Err()
}

func RowCount(db *sql.DB) (int, error) {
    var n int
    err := db.QueryRow(`SELECT COUNT(*) FROM matrix_rows`).Scan(&n)
    return n, err
}

func boolInt(v bool) int {
    if v {
        return 1
    }
    return 0
}

func DeleteAll(db *sql.DB) error {
    _, err := db.Exec(`DELETE FROM matrix_rows`)
    return err
}

func UpsertRows(db *sql.DB, rows []model.MatrixRow) error {
    return fmt.Errorf("not implemented")
}
