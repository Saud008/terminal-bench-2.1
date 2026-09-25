package store

import (
	"database/sql"
	"os"

	_ "modernc.org/sqlite"

	"github.com/terminus/sssdcache/internal/model"
)

const DefaultDBPath = "/app/state/sssd-cache.db"

func PersistSnapshot(path string, snap model.Snapshot) (int, error) {
	_ = os.Remove(path)
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return 0, err
	}
	defer db.Close()

	if _, err := db.Exec(`PRAGMA journal_mode=WAL`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`CREATE TABLE negative_cache (
		domain TEXT NOT NULL,
		name TEXT NOT NULL,
		miss_ts INTEGER NOT NULL,
		expires_at INTEGER NOT NULL,
		PRIMARY KEY (domain, name)
	)`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`CREATE TABLE positive_cache (
		domain TEXT NOT NULL,
		name TEXT NOT NULL,
		value TEXT NOT NULL,
		PRIMARY KEY (domain, name)
	)`); err != nil {
		return 0, err
	}

	for _, n := range snap.Negatives {
		if n.ExpiresAt <= snap.EvaluatedAtMS {
			continue
		}
		if _, err := db.Exec(
			`INSERT INTO negative_cache(domain,name,miss_ts,expires_at) VALUES (?,?,?,?)`,
			n.Domain, n.Name, n.MissTS, n.ExpiresAt,
		); err != nil {
			return 0, err
		}
	}
	for _, p := range snap.Positives {
		if _, err := db.Exec(
			`INSERT INTO positive_cache(domain,name,value) VALUES (?,?,?)`,
			p.Domain, p.Name, p.Value,
		); err != nil {
			return 0, err
		}
	}

	checkpoints := 0
	if _, err := db.Exec(`PRAGMA wal_checkpoint(FULL)`); err == nil {
		checkpoints = 1
	}
	return checkpoints, nil
}

func ReadNegatives(path string) ([]model.NegativeExport, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	rows, err := db.Query(`SELECT domain,name,miss_ts,expires_at FROM negative_cache ORDER BY domain,name`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.NegativeExport
	for rows.Next() {
		var n model.NegativeExport
		if err := rows.Scan(&n.Domain, &n.Name, &n.MissTS, &n.ExpiresAt); err != nil {
			return nil, err
		}
		out = append(out, n)
	}
	return out, rows.Err()
}
