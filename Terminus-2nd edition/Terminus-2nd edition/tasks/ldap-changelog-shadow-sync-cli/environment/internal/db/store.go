package db

import (
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"

	"github.com/harbor/ldap-shadow-sync/internal/model"
	_ "modernc.org/sqlite"
)

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	d, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	s := &Store{db: d}
	if err := s.migrate(); err != nil {
		d.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) migrate() error {
	_, err := s.db.Exec(`
CREATE TABLE IF NOT EXISTS shadow_entries (
  normalized_dn TEXT PRIMARY KEY,
  attrs_json TEXT NOT NULL DEFAULT '{}',
  usn_changed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS usn_applied (
  usn_changed INTEGER PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS export_meta (
  key TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);
`)
	return err
}

func (s *Store) UpsertEntry(e model.Entry) error {
	b, err := json.Marshal(e.Attrs)
	if err != nil {
		return err
	}
	_, err = s.db.Exec(`
INSERT INTO shadow_entries(normalized_dn, attrs_json, usn_changed)
VALUES(?,?,?)
ON CONFLICT(normalized_dn) DO UPDATE SET
  attrs_json=excluded.attrs_json,
  usn_changed=excluded.usn_changed
`, e.NormalizedDN, string(b), e.USNChanged)
	return err
}

func (s *Store) DeleteEntry(normDN string) error {
	_, err := s.db.Exec(`DELETE FROM shadow_entries WHERE normalized_dn=?`, normDN)
	return err
}

func (s *Store) MarkUSN(usn int64) error {
	_, err := s.db.Exec(`INSERT OR IGNORE INTO usn_applied(usn_changed) VALUES(?)`, usn)
	return err
}

func (s *Store) USNSeen(usn int64) (bool, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM usn_applied WHERE usn_changed=?`, usn).Scan(&n)
	return n > 0, err
}

func (s *Store) AllUSNs() (map[int64]struct{}, error) {
	rows, err := s.db.Query(`SELECT usn_changed FROM usn_applied`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[int64]struct{}{}
	for rows.Next() {
		var usn int64
		if err := rows.Scan(&usn); err != nil {
			return nil, err
		}
		out[usn] = struct{}{}
	}
	return out, rows.Err()
}

func (s *Store) AllEntries() ([]model.Entry, error) {
	rows, err := s.db.Query(`SELECT normalized_dn, attrs_json, usn_changed FROM shadow_entries ORDER BY normalized_dn`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Entry
	for rows.Next() {
		var e model.Entry
		var attrsJSON string
		if err := rows.Scan(&e.NormalizedDN, &attrsJSON, &e.USNChanged); err != nil {
			return nil, err
		}
		if err := json.Unmarshal([]byte(attrsJSON), &e.Attrs); err != nil {
			return nil, err
		}
		out = append(out, e)
	}
	return out, rows.Err()
}

func (s *Store) UniqueDNCount() (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM shadow_entries`).Scan(&n)
	return n, err
}

func (s *Store) ExportSequence() (int, error) {
	var v int
	err := s.db.QueryRow(`SELECT value FROM export_meta WHERE key='export_sequence'`).Scan(&v)
	if err == sql.ErrNoRows {
		return 0, nil
	}
	return v, err
}

func (s *Store) SetExportSequence(v int) error {
	_, err := s.db.Exec(`INSERT INTO export_meta(key,value) VALUES('export_sequence',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value`, v)
	return err
}

func (s *Store) BumpExportSequence() (int, error) {
	cur, err := s.ExportSequence()
	if err != nil {
		return 0, err
	}
	next := cur + 1
	return next, s.SetExportSequence(next)
}

// MaxUSN returns the max uSNChanged among live shadow rows.
func (s *Store) MaxUSN() (int64, error) {
	var v sql.NullInt64
	err := s.db.QueryRow(`SELECT MAX(usn_changed) FROM shadow_entries`).Scan(&v)
	if err != nil {
		return 0, err
	}
	if !v.Valid {
		return 0, nil
	}
	return v.Int64, nil
}

// MaxAppliedUSN returns the max successfully applied uSNChanged, including deletes.
func (s *Store) MaxAppliedUSN() (int64, error) {
	var v sql.NullInt64
	err := s.db.QueryRow(`SELECT MAX(usn_changed) FROM usn_applied`).Scan(&v)
	if err != nil {
		return 0, err
	}
	if !v.Valid {
		return 0, nil
	}
	return v.Int64, nil
}

func SortEntries(entries []model.Entry) {
	sort.Slice(entries, func(i, j int) bool {
		return entries[i].NormalizedDN < entries[j].NormalizedDN
	})
}
