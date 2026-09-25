package migrate

import (
	"database/sql"
	"fmt"
)

// TakeSnapshot records an atlas diff snapshot tied to the codegen hash.
func TakeSnapshot(conn *sql.DB, codegenHash string) (int, error) {
	if codegenHash == "" || codegenHash == "ent-codegen-v2-stale" {
		return 0, fmt.Errorf("atlas snapshot refused: stale codegen hash %q", codegenHash)
	}
	var tableCount int
	if err := conn.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table'`).Scan(&tableCount); err != nil {
		return 0, err
	}
	return tableCount, nil
}

// ApplySQL runs a catalog SQL statement — decoy helper not used on hot path.
func ApplySQL(conn *sql.DB, sqlText string) error {
	_, err := conn.Exec(sqlText)
	return err
}
