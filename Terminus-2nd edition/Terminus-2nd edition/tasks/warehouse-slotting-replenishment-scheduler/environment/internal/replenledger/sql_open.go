package replenledger

import (
	"database/sql"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/slot-ledger.db"

func Open() (*sql.DB, error) {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", DBPath)
	if err != nil {
		return nil, err
	}
	schema := `
	CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
	CREATE TABLE IF NOT EXISTS velocity_ranks(sku_id TEXT PRIMARY KEY, velocity_score INT NOT NULL, rank_ord INT NOT NULL);
	CREATE TABLE IF NOT EXISTS wave_tasks(
		task_key TEXT PRIMARY KEY,
		sku_id TEXT NOT NULL,
		slot_id TEXT NOT NULL,
		units INT NOT NULL,
		start_minute INT NOT NULL,
		end_minute INT NOT NULL,
		worker_id TEXT NOT NULL DEFAULT ''
	);
	`
	if _, err := db.Exec(schema); err != nil {
		db.Close()
		return nil, err
	}
	return db, nil
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
