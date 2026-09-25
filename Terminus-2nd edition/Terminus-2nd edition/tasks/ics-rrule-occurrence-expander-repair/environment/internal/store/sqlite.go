package store

import (
	"database/sql"
	"fmt"
	"time"

	_ "modernc.org/sqlite"

	"github.com/terminus/icalexpand/internal/model"
)

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	s := &Store{db: db}
	if err := s.initSchema(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) initSchema() error {
	_, err := s.db.Exec(`CREATE TABLE IF NOT EXISTS occurrences (
		uid TEXT NOT NULL,
		start_utc TEXT NOT NULL,
		seq INTEGER NOT NULL,
		PRIMARY KEY (uid, start_utc)
	)`)
	return err
}

func (s *Store) ReplaceAll(items []model.Occurrence) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	if _, err := tx.Exec(`DELETE FROM occurrences`); err != nil {
		_ = tx.Rollback()
		return err
	}
	for i, occ := range items {
		if _, err := tx.Exec(
			`INSERT INTO occurrences (uid, start_utc, seq) VALUES (?, ?, ?)`,
			occ.UID, occ.StartUTC.UTC().Format(time.RFC3339), i,
		); err != nil {
			_ = tx.Rollback()
			return err
		}
	}
	return tx.Commit()
}

func (s *Store) List() ([]model.Occurrence, error) {
	rows, err := s.db.Query(`SELECT uid, start_utc FROM occurrences ORDER BY start_utc ASC, uid ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Occurrence
	for rows.Next() {
		var uid, start string
		if err := rows.Scan(&uid, &start); err != nil {
			return nil, err
		}
		t, err := time.Parse(time.RFC3339, start)
		if err != nil {
			return nil, fmt.Errorf("parse start: %w", err)
		}
		out = append(out, model.Occurrence{UID: uid, StartUTC: t.UTC()})
	}
	return out, rows.Err()
}
