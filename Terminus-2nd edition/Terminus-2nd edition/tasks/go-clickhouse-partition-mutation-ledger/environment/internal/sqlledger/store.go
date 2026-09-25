package sqlledger

import (
    "database/sql"

    _ "github.com/mattn/go-sqlite3"
    "github.com/terminus/chmutled/internal/model"
)

func Open(path string) (*sql.DB, error) {
    db, err := sql.Open("sqlite3", path)
    if err != nil {
        return nil, err
    }
    _, err = db.Exec(`CREATE TABLE IF NOT EXISTS mutation_ledger (
        partition_id TEXT NOT NULL,
        mutation_id TEXT NOT NULL,
        mutation_version INTEGER NOT NULL,
        readiness_state TEXT NOT NULL,
        PRIMARY KEY (partition_id, mutation_id)
    )`)
    if err != nil {
        db.Close()
        return nil, err
    }
    return db, nil
}

func Upsert(db *sql.DB, rows []model.StagedMutation) error {
    tx, err := db.Begin()
    if err != nil {
        return err
    }
    stmt, err := tx.Prepare(`INSERT OR REPLACE INTO mutation_ledger
        (partition_id, mutation_id, mutation_version, readiness_state)
        VALUES (?, ?, ?, ?)`)
    if err != nil {
        tx.Rollback()
        return err
    }
    defer stmt.Close()
    for _, r := range rows {
        if _, err := stmt.Exec(r.PartitionID, r.MutationID, r.MutationVersion, r.ReadinessState); err != nil {
            tx.Rollback()
            return err
        }
    }
    return tx.Commit()
}

func Count(db *sql.DB) (int, error) {
    var n int
    err := db.QueryRow(`SELECT COUNT(*) FROM mutation_ledger`).Scan(&n)
    return n, err
}
