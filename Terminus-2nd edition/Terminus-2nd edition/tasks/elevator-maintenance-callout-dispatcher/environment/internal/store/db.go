package store

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/callout.db"

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
		`CREATE TABLE IF NOT EXISTS faults (fault_id TEXT PRIMARY KEY, building_id TEXT, elevator_bank TEXT, fault_code TEXT, severity_base INTEGER, trapped_passengers INTEGER, reported_minute INTEGER, required_skill INTEGER, cancelled INTEGER)`,
		`CREATE TABLE IF NOT EXISTS technicians (tech_id TEXT PRIMARY KEY, skill_level INTEGER, shift_start INTEGER, shift_end INTEGER, cert_tags TEXT)`,
		`CREATE TABLE IF NOT EXISTS access_windows (building_id TEXT, start_minute INTEGER, end_minute INTEGER)`,
		`CREATE TABLE IF NOT EXISTS sla_contracts (tier TEXT, building_id TEXT, max_response_minutes INTEGER, escalation_weight INTEGER, tier_rank INTEGER)`,
		`CREATE TABLE IF NOT EXISTS urgency_scores (fault_id TEXT PRIMARY KEY, priority_score INTEGER, sla_urgency INTEGER, breach_horizon_min INTEGER)`,
		`CREATE TABLE IF NOT EXISTS assignments (fault_id TEXT PRIMARY KEY, tech_id TEXT, planned_minute INTEGER, status TEXT)`,
		`CREATE TABLE IF NOT EXISTS bind_audit_ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, fault_id TEXT, tech_id TEXT, pass_num INTEGER)`,
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
