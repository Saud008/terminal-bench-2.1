package ledger

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const dbPath = "/app/var/ledger/tariff.db"

func Open() (*sql.DB, error) {
	if err := os.MkdirAll("/app/var/ledger", 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}
	if err := initSchema(db); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
}

func initSchema(db *sql.DB) error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)`,
		`CREATE TABLE IF NOT EXISTS lines(line_id TEXT PRIMARY KEY, hs_norm TEXT, declared_origin TEXT, value_cents INTEGER, bom_json TEXT)`,
		`CREATE TABLE IF NOT EXISTS certificates(cert_id TEXT PRIMARY KEY, line_id TEXT, agreement_code TEXT, issued_on TEXT, expires_on TEXT, origin_country TEXT)`,
		`CREATE TABLE IF NOT EXISTS agreement_rules(agreement_code TEXT, hs_prefix TEXT, rvc_min_bps INTEGER, duty_rate_bps INTEGER, priority INTEGER)`,
		`CREATE TABLE IF NOT EXISTS audit_rows(line_id TEXT, event_kind TEXT, detail TEXT, pass_num INTEGER)`,
	}
	for _, s := range stmts {
		if _, err := db.Exec(s); err != nil {
			return err
		}
	}
	return nil
}

func GetMeta(db *sql.DB, key string) (string, error) {
	var v string
	err := db.QueryRow(`SELECT value FROM meta WHERE key=?`, key).Scan(&v)
	if err == sql.ErrNoRows {
		return "", fmt.Errorf("meta %s missing", key)
	}
	return v, err
}

func SetMeta(db *sql.DB, key, value string) error {
	_, err := db.Exec(`INSERT INTO meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`, key, value)
	return err
}
