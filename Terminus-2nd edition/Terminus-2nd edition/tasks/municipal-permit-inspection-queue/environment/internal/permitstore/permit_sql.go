package store

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/permit.db"

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
		`CREATE TABLE IF NOT EXISTS permits (permit_id TEXT PRIMARY KEY, district_id TEXT, permit_type TEXT, base_priority INTEGER, requested_day INTEGER, deferred INTEGER)`,
		`CREATE TABLE IF NOT EXISTS inspectors (inspector_id TEXT PRIMARY KEY, cert_level INTEGER, districts TEXT, daily_cap INTEGER, available_day INTEGER)`,
		`CREATE TABLE IF NOT EXISTS zoning_holds (district_id TEXT, hold_rank INTEGER, active INTEGER, reason_code TEXT)`,
		`CREATE TABLE IF NOT EXISTS blackout_windows (district_id TEXT, start_day INTEGER, end_day INTEGER)`,
		`CREATE TABLE IF NOT EXISTS violations (permit_id TEXT, severity INTEGER, days_ago INTEGER)`,
		`CREATE TABLE IF NOT EXISTS permit_routes (permit_type TEXT, inspection_lane TEXT, min_cert_level INTEGER)`,
		`CREATE TABLE IF NOT EXISTS queue_scores (permit_id TEXT PRIMARY KEY, composite_score INTEGER, violation_weight INTEGER, hold_blocked INTEGER)`,
		`CREATE TABLE IF NOT EXISTS queue_entries (permit_id TEXT PRIMARY KEY, inspector_id TEXT, scheduled_day INTEGER, inspection_lane TEXT, status TEXT)`,
		`CREATE TABLE IF NOT EXISTS bind_audit_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, permit_id TEXT, inspector_id TEXT, pass_num INTEGER)`,
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
