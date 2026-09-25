package store

import (
	"database/sql"
	"fmt"
	"os"

	_ "modernc.org/sqlite"
)

const DBPath = "/app/state/ppa-settlement.db"

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
		`CREATE TABLE IF NOT EXISTS settlement_lines (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			meter_id TEXT NOT NULL,
			interval_start_utc TEXT NOT NULL,
			mwh REAL NOT NULL,
			strike_cents INTEGER NOT NULL,
			market_cents INTEGER NOT NULL,
			settlement_cents INTEGER NOT NULL,
			amount_cents INTEGER NOT NULL,
			skipped_curtail INTEGER NOT NULL
		)`,
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

func ReplaceLines(db *sql.DB, rows []struct {
	MeterID, Interval string
	MWh               float64
	Strike, Market, Settlement, Amount int64
	Skipped bool
}) error {
	if _, err := db.Exec(`DELETE FROM settlement_lines`); err != nil {
		return err
	}
	for _, row := range rows {
		skip := 0
		if row.Skipped {
			skip = 1
		}
		if _, err := db.Exec(`INSERT INTO settlement_lines(meter_id,interval_start_utc,mwh,strike_cents,market_cents,settlement_cents,amount_cents,skipped_curtail) VALUES(?,?,?,?,?,?,?,?)`,
			row.MeterID, row.Interval, row.MWh, row.Strike, row.Market, row.Settlement, row.Amount, skip); err != nil {
			return err
		}
	}
	return nil
}
