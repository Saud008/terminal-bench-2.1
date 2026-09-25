package export

import (
	"database/sql"
	"encoding/json"
	"os"

	"github.com/terminus/sqlitemigrate/internal/apply"
	"github.com/terminus/sqlitemigrate/internal/lock"
	"github.com/terminus/sqlitemigrate/internal/staging"
	"github.com/terminus/sqlitemigrate/internal/types"
)

const DefaultLedgerPath = "/app/output/version-ledger.json"

// BuildLedger reads DB and stage snapshot, writing version ledger export.
func BuildLedger(dbPath, stagePath, outPath string, exportPass int) error {
	db, err := apply.OpenDB(dbPath)
	if err != nil {
		return err
	}
	defer db.Close()

	st, err := staging.Load(stagePath)
	if err != nil {
		return err
	}

	var ledger types.VersionLedger
	ledger.ExportPass = exportPass
	ledger.StageVersion = st.Version
	ledger.FailedDownRollbacks = st.FailedDownRollbacks

	err = lock.WithExclusive(db, func() error {
		rows, err := db.Query(`SELECT version FROM version_log`)
		if err != nil {
			return err
		}
		defer rows.Close()
		maxV := 0
		for rows.Next() {
			var v int
			if err := rows.Scan(&v); err != nil {
				return err
			}
			if v > maxV {
				maxV = v
			}
		}
		if err := rows.Err(); err != nil {
			return err
		}
		ledger.MaxVersion = maxV
		dirty, err := readDirtyFlag(db)
		if err != nil {
			return err
		}
		ledger.Dirty = dirty
		return nil
	})
	if err != nil {
		return err
	}

	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(outPath, data, 0o644)
}

func readDirtyFlag(db *sql.DB) (bool, error) {
	var d int
	err := db.QueryRow(`SELECT dirty FROM schema_migrations ORDER BY rowid DESC LIMIT 1`).Scan(&d)
	if err == sql.ErrNoRows {
		return false, nil
	}
	return d != 0, err
}
