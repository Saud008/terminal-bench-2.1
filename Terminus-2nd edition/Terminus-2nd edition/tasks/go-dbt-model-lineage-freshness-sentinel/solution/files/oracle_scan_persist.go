package scanstore

import (
	"database/sql"
	"encoding/json"

	"github.com/terminus/dbt-lineage-freshness-sentinel/internal/model"

	_ "modernc.org/sqlite"
)

type DB struct {
	conn *sql.DB
}

func Open(path string) (*DB, error) {
	conn, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := conn.Exec(`CREATE TABLE IF NOT EXISTS scans (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		seed TEXT NOT NULL,
		pack TEXT NOT NULL,
		summary_json TEXT NOT NULL,
		active INTEGER NOT NULL DEFAULT 1
	)`); err != nil {
		conn.Close()
		return nil, err
	}
	return &DB{conn: conn}, nil
}

func (d *DB) Close() error {
	return d.conn.Close()
}

func InsertScan(d *DB, seed, bundle string, summary model.ScanSummary) (int64, error) {
	if _, err := d.conn.Exec(`UPDATE scans SET active=0 WHERE seed=?`, seed); err != nil {
		return 0, err
	}
	body, err := json.Marshal(summary)
	if err != nil {
		return 0, err
	}
	res, err := d.conn.Exec(
		`INSERT INTO scans (seed, pack, summary_json, active) VALUES (?, ?, ?, 1)`,
		seed, bundle, string(body),
	)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func LatestScan(d *DB, seed, bundle string) (int64, model.ScanSummary, error) {
	row := d.conn.QueryRow(
		`SELECT id, summary_json FROM scans WHERE seed=? AND pack=? AND active=1 ORDER BY id DESC LIMIT 1`,
		seed, bundle,
	)
	var id int64
	var body string
	if err := row.Scan(&id, &body); err != nil {
		return 0, model.ScanSummary{}, err
	}
	var summary model.ScanSummary
	if err := json.Unmarshal([]byte(body), &summary); err != nil {
		return 0, model.ScanSummary{}, err
	}
	return id, summary, nil
}
