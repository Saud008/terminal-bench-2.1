package store

import (
	"database/sql"
	"fmt"
	"os"

	_ "github.com/mattn/go-sqlite3"

	"mailindex/internal/model"
)

type Store struct {
	DB *sql.DB
}

func Open(path string) (*Store, error) {
	if _, err := os.Stat(path); err != nil {
		return nil, fmt.Errorf("thread db missing")
	}
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	return &Store{DB: db}, nil
}

func (s *Store) Apply(indexed []model.IndexedMessage, stats *model.Stats) error {
	tx, err := s.DB.Begin()
	if err != nil {
		return err
	}
	defer func() { _ = tx.Rollback() }()

	for _, msg := range indexed {
		isRoot := 0
		if msg.IsRoot {
			isRoot = 1
		}
		if _, err := tx.Exec(
			`INSERT OR REPLACE INTO message_threads (message_id, thread_root_id, date_unix, subject, is_root) VALUES (?, ?, ?, ?, ?)`,
			msg.MessageID, msg.ThreadRootID, msg.DateUnix, msg.Subject, isRoot,
		); err != nil {
			return err
		}
		stats.MessagesIndexed++
	}
	return tx.Commit()
}

func (s *Store) Close() error {
	return s.DB.Close()
}
