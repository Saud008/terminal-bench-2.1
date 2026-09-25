package queue

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/asynq-archive-repair/internal/model"
)

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	s := &Store{db: db}
	if err := s.migrate(); err != nil {
		_ = db.Close()
		return nil, err
	}
	return s, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) migrate() error {
	_, err := s.db.Exec(`
CREATE TABLE IF NOT EXISTS pending (
  id TEXT PRIMARY KEY,
  queue TEXT NOT NULL,
  payload TEXT NOT NULL,
  retry INTEGER NOT NULL,
  max_retry INTEGER NOT NULL,
  priority INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS archived (
  id TEXT PRIMARY KEY,
  queue TEXT NOT NULL,
  payload TEXT NOT NULL,
  retry INTEGER NOT NULL,
  max_retry INTEGER NOT NULL,
  priority INTEGER NOT NULL,
  archived_at_ms INTEGER NOT NULL
);
`)
	return err
}

func (s *Store) Reset() error {
	_, err := s.db.Exec(`DELETE FROM pending; DELETE FROM archived;`)
	return err
}

func (s *Store) InsertPending(t model.TaskRecord) error {
	_, err := s.db.Exec(
		`INSERT OR REPLACE INTO pending(id, queue, payload, retry, max_retry, priority) VALUES (?,?,?,?,?,?)`,
		t.ID, t.Queue, t.Payload, t.Retry, t.MaxRetry, t.Priority,
	)
	return err
}

func (s *Store) ListPending() ([]model.TaskRecord, error) {
	rows, err := s.db.Query(`SELECT id, queue, payload, retry, max_retry, priority FROM pending ORDER BY priority ASC, id ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.TaskRecord
	for rows.Next() {
		var t model.TaskRecord
		if err := rows.Scan(&t.ID, &t.Queue, &t.Payload, &t.Retry, &t.MaxRetry, &t.Priority); err != nil {
			return nil, err
		}
		out = append(out, t)
	}
	return out, rows.Err()
}

func (s *Store) DeletePending(ids []string) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	for _, id := range ids {
		if _, err := tx.Exec(`DELETE FROM pending WHERE id = ?`, id); err != nil {
			_ = tx.Rollback()
			return err
		}
	}
	return tx.Commit()
}

func (s *Store) InsertArchived(t model.TaskRecord) error {
	_, err := s.db.Exec(
		`INSERT OR REPLACE INTO archived(id, queue, payload, retry, max_retry, priority, archived_at_ms) VALUES (?,?,?,?,?,?,?)`,
		t.ID, t.Queue, t.Payload, t.Retry, t.MaxRetry, t.Priority, t.ArchivedAtMs,
	)
	return err
}

func (s *Store) PurgeArchivedBefore(cutoffMs int64) (int64, error) {
	res, err := s.db.Exec(`DELETE FROM archived WHERE archived_at_ms < ?`, cutoffMs)
	if err != nil {
		return 0, err
	}
	return res.RowsAffected()
}

func (s *Store) CountArchived() (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM archived`).Scan(&n)
	return n, err
}

func (s *Store) PendingIDs() ([]string, error) {
	rows, err := s.db.Query(`SELECT id FROM pending ORDER BY priority ASC, id ASC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var ids []string
	for rows.Next() {
		var id string
		if err := rows.Scan(&id); err != nil {
			return nil, err
		}
		ids = append(ids, id)
	}
	return ids, rows.Err()
}

func (s *Store) PendingPriority(id string) (int, error) {
	var p int
	err := s.db.QueryRow(`SELECT priority FROM pending WHERE id = ?`, id).Scan(&p)
	if err == sql.ErrNoRows {
		return 0, fmt.Errorf("missing pending task %s", id)
	}
	return p, err
}
