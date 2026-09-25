package store

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/border-validity.db"

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
		`CREATE TABLE IF NOT EXISTS passports (doc_id TEXT PRIMARY KEY, holder_id TEXT, issue_date TEXT, expiry_date TEXT, revoked INTEGER)`,
		`CREATE TABLE IF NOT EXISTS visas (doc_id TEXT PRIMARY KEY, passport_id TEXT, valid_from TEXT, valid_to TEXT, visa_class TEXT, revoked INTEGER)`,
		`CREATE TABLE IF NOT EXISTS stamps (stamp_id TEXT PRIMARY KEY, passport_id TEXT, entry_date TEXT, exit_date TEXT, port_code TEXT)`,
		`CREATE TABLE IF NOT EXISTS rules (rule_id TEXT PRIMARY KEY, scope TEXT, port_code TEXT, max_stay_days INTEGER)`,
		`CREATE TABLE IF NOT EXISTS holds (hold_id TEXT PRIMARY KEY, holder_id TEXT, active INTEGER, reason TEXT)`,
		`CREATE TABLE IF NOT EXISTS decisions (id INTEGER PRIMARY KEY AUTOINCREMENT, holder_id TEXT, passport_id TEXT, visa_id TEXT, allowed_entry INTEGER, deny_reasons TEXT, cumulative_stay_days INTEGER, max_stay_allowed INTEGER, remaining_stay_days INTEGER)`,
		`CREATE TABLE IF NOT EXISTS ledger (id INTEGER PRIMARY KEY AUTOINCREMENT, holder_id TEXT, visa_id TEXT, line_kind TEXT, amount_days INTEGER, pass_num INTEGER)`,
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
