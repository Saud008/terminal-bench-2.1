package db

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	_ "modernc.org/sqlite"
)

const schemaSQL = `
CREATE TABLE IF NOT EXISTS berth_assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  voyage_id TEXT NOT NULL,
  mmsi INTEGER NOT NULL,
  berth_id TEXT NOT NULL,
  arrival_utc TEXT NOT NULL,
  departure_utc TEXT NOT NULL,
  idempotency_key TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS replay_stats (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  accepted INTEGER NOT NULL DEFAULT 0,
  duplicate_rejected INTEGER NOT NULL DEFAULT 0
);
INSERT OR IGNORE INTO replay_stats (id, accepted, duplicate_rejected) VALUES (1, 0, 0);
`

type Store struct {
	DB *sql.DB
}

func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := db.Exec(schemaSQL); err != nil {
		return nil, err
	}
	return &Store{DB: db}, nil
}

func (s *Store) Close() error {
	return s.DB.Close()
}

func IdempotencyKey(voyageID, berthID, arrival string) string {
	return fmt.Sprintf("%s:%s:%s", voyageID, berthID, arrival)
}

type Assignment struct {
	VoyageID     string
	MMSI         int64
	BerthID      string
	ArrivalUTC   string
	DepartureUTC string
}

func (s *Store) InsertAssignment(a Assignment, key string) (inserted bool, err error) {
	tx, err := s.DB.Begin()
	if err != nil {
		return false, err
	}
	defer tx.Rollback()

	res, err := tx.Exec(
		`INSERT INTO berth_assignments (voyage_id, mmsi, berth_id, arrival_utc, departure_utc, idempotency_key)
		 VALUES (?, ?, ?, ?, ?, ?)`,
		a.VoyageID, a.MMSI, a.BerthID, a.ArrivalUTC, a.DepartureUTC, key,
	)
	if err != nil {
		if strings.Contains(strings.ToUpper(err.Error()), "UNIQUE") {
			if _, derr := tx.Exec(`UPDATE replay_stats SET duplicate_rejected = duplicate_rejected + 1 WHERE id = 1`); derr != nil {
				return false, derr
			}
			if cerr := tx.Commit(); cerr != nil {
				return false, cerr
			}
			return false, nil
		}
		return false, err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return false, nil
	}
	if _, err := tx.Exec(`UPDATE replay_stats SET accepted = accepted + 1 WHERE id = 1`); err != nil {
		return false, err
	}
	if err := tx.Commit(); err != nil {
		return false, err
	}
	return true, nil
}

func (s *Store) RecordDuplicate() error {
	_, err := s.DB.Exec(`UPDATE replay_stats SET duplicate_rejected = duplicate_rejected + 1 WHERE id = 1`)
	return err
}

func (s *Store) ReplayStats() (accepted, duplicate int, err error) {
	row := s.DB.QueryRow(`SELECT accepted, duplicate_rejected FROM replay_stats WHERE id = 1`)
	err = row.Scan(&accepted, &duplicate)
	return
}

func (s *Store) AllAssignments() ([]Assignment, error) {
	rows, err := s.DB.Query(`SELECT voyage_id, mmsi, berth_id, arrival_utc, departure_utc FROM berth_assignments ORDER BY berth_id, arrival_utc, voyage_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []Assignment
	for rows.Next() {
		var a Assignment
		if err := rows.Scan(&a.VoyageID, &a.MMSI, &a.BerthID, &a.ArrivalUTC, &a.DepartureUTC); err != nil {
			return nil, err
		}
		out = append(out, a)
	}
	return out, rows.Err()
}

func IsUniqueViolation(err error) bool {
	return err != nil && strings.Contains(strings.ToUpper(err.Error()), "UNIQUE")
}
