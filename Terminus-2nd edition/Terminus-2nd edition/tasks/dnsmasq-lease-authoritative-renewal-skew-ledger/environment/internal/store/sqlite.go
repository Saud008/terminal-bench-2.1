package store

import (
	"database/sql"
	"fmt"
	"os"
	"sort"

	"dnsmasqledger/internal/model"

	_ "modernc.org/sqlite"
)

const schema = `
CREATE TABLE IF NOT EXISTS leases (
  identity_key TEXT PRIMARY KEY,
  mac TEXT NOT NULL,
  duid TEXT NOT NULL,
  iaid INTEGER NOT NULL,
  hostname TEXT,
  ip TEXT NOT NULL,
  expires_sec INTEGER NOT NULL,
  authoritative INTEGER NOT NULL
);
`

func Persist(dbPath string, cat *model.Catalog) error {
	if err := os.MkdirAll("/app/work", 0o755); err != nil {
		return err
	}
	_ = os.Remove(dbPath)
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(schema); err != nil {
		return err
	}
	keys := make([]string, 0, len(cat.Leases))
	for k := range cat.Leases {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	for _, k := range keys {
		l := cat.Leases[k]
		if !l.Authoritative {
			continue
		}
		auth := 0
		if l.Authoritative {
			auth = 1
		}
		_, err := db.Exec(
			`INSERT INTO leases(identity_key, mac, duid, iaid, hostname, ip, expires_sec, authoritative)
			 VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
			l.IdentityKey, l.MAC, l.DUID, l.IAID, l.Hostname, l.IP, l.ExpiresSec, auth,
		)
		if err != nil {
			return err
		}
	}
	return nil
}

func CountAuthoritative(dbPath string) (int, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return 0, err
	}
	defer db.Close()
	var n int
	err = db.QueryRow(`SELECT COUNT(*) FROM leases WHERE authoritative = 1`).Scan(&n)
	return n, err
}

func ReadRows(dbPath string) ([]model.LeaseRow, error) {
	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	rows, err := db.Query(`SELECT identity_key, mac, duid, iaid, hostname, ip, expires_sec, authoritative FROM leases ORDER BY identity_key`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.LeaseRow
	for rows.Next() {
		var r model.LeaseRow
		var auth int
		if err := rows.Scan(&r.IdentityKey, &r.MAC, &r.DUID, &r.IAID, &r.Hostname, &r.IP, &r.ExpiresSec, &auth); err != nil {
			return nil, err
		}
		r.Authoritative = auth == 1
		out = append(out, r)
	}
	return out, rows.Err()
}

func VerifyPath(dbPath string) error {
	if dbPath == "" {
		return fmt.Errorf("empty db path")
	}
	return nil
}
