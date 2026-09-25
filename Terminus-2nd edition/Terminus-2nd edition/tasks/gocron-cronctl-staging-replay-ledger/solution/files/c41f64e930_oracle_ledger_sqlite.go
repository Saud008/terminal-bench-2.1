package ledger

import (
	"database/sql"

	"github.com/terminus/gocron-overlap-repair/internal/model"
	_ "modernc.org/sqlite"
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
	if err := s.init(); err != nil {
		db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) init() error {
	_, err := s.db.Exec(`CREATE TABLE IF NOT EXISTS executions (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		job_id TEXT NOT NULL,
		fired_at_ms INTEGER NOT NULL,
		status TEXT NOT NULL,
		lock_held INTEGER NOT NULL,
		deduped INTEGER NOT NULL
	)`)
	return err
}

func (s *Store) Reset() error {
	_, err := s.db.Exec(`DELETE FROM executions`)
	return err
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) Insert(row model.ExecutionRow) error {
	_, err := s.db.Exec(
		`INSERT INTO executions (job_id, fired_at_ms, status, lock_held, deduped) VALUES (?, ?, ?, ?, ?)`,
		row.JobID, row.FiredAtMs, row.Status, boolToInt(row.LockHeld), boolToInt(row.Deduped),
	)
	return err
}

// List returns execution rows ordered by fired_at_ms ASC, then job_id ASC.
// Export executions[] must preserve this order (see run-ledger-export.md).
func (s *Store) List() ([]model.ExecutionRow, error) {
	rows, err := s.db.Query(`SELECT job_id, fired_at_ms, status, lock_held, deduped FROM executions ORDER BY fired_at_ms ASC, job_id ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.ExecutionRow
	for rows.Next() {
		var r model.ExecutionRow
		var lh, dd int
		if err := rows.Scan(&r.JobID, &r.FiredAtMs, &r.Status, &lh, &dd); err != nil {
			return nil, err
		}
		r.LockHeld = lh == 1
		r.Deduped = dd == 1
		out = append(out, r)
	}
	return out, rows.Err()
}

func boolToInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func (s *Store) CountFires() (fires, deduped int, err error) {
	if err := s.db.QueryRow(`SELECT COUNT(*) FROM executions WHERE deduped = 0`).Scan(&fires); err != nil {
		return 0, 0, err
	}
	if err := s.db.QueryRow(`SELECT COUNT(*) FROM executions WHERE deduped = 1`).Scan(&deduped); err != nil {
		return 0, 0, err
	}
	return fires, deduped, nil
}
