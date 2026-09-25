package store

import (
	"database/sql"

	_ "github.com/mattn/go-sqlite3"

	"mailindex/internal/model"
)

type Store struct {
	DB *sql.DB
}

func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, err
	}
	return &Store{DB: db}, nil
}

func (s *Store) Apply(indexed []model.IndexedMessage, stats *model.Stats) error {
	for _, msg := range indexed {
		isRoot := 0
		if msg.IsRoot {
			isRoot = 1
		}
		if _, err := s.DB.Exec(
			`INSERT OR REPLACE INTO message_threads (message_id, thread_root_id, date_unix, subject, is_root) VALUES (?, ?, ?, ?, ?)`,
			msg.MessageID, msg.ThreadRootID, msg.DateUnix, msg.Subject, isRoot,
		); err != nil {
			return err
		}
		stats.MessagesIndexed++
	}
	return nil
}

func (s *Store) Close() error {
	return s.DB.Close()
}
