package persist

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/release.db"

func Open() (*sql.DB, error) {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", DBPath)
	if err != nil {
		return nil, err
	}
	if err := migrate(db); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func migrate(db *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
		`CREATE TABLE IF NOT EXISTS patients (patient_id TEXT PRIMARY KEY, abo TEXT, rh TEXT)`,
		`CREATE TABLE IF NOT EXISTS patient_antibodies (patient_id TEXT, antibody TEXT)`,
		`CREATE TABLE IF NOT EXISTS units (unit_id TEXT PRIMARY KEY, abo TEXT, rh TEXT, collected_at TEXT, expires_at TEXT)`,
		`CREATE TABLE IF NOT EXISTS unit_antigens (unit_id TEXT, antigen TEXT)`,
		`CREATE TABLE IF NOT EXISTS overrides (patient_id TEXT, unit_id TEXT, authorizer TEXT, reason TEXT, issued_at TEXT)`,
		`CREATE TABLE IF NOT EXISTS crossmatch_rows (patient_id TEXT, unit_id TEXT, compatible INTEGER, failure_codes TEXT)`,
		`CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id TEXT, unit_id TEXT, pass_num INTEGER)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return fmt.Errorf("migrate: %w", err)
		}
	}
	return nil
}

func SetMeta(db *sql.DB, key, value string) error {
	_, err := db.Exec(`INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`, key, value)
	return err
}

func GetMeta(db *sql.DB, key string) (string, error) {
	var v string
	err := db.QueryRow(`SELECT value FROM meta WHERE key=?`, key).Scan(&v)
	return v, err
}
