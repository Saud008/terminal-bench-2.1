package durastore

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"
)

type DB struct {
	SQL *sql.DB
}

func Open(path string) (*DB, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	sqlDB, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	db := &DB{SQL: sqlDB}
	if err := db.migrate(); err != nil {
		_ = sqlDB.Close()
		return nil, err
	}
	return db, nil
}

func (db *DB) migrate() error {
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS documents (
			_id TEXT PRIMARY KEY,
			machine_id TEXT NOT NULL,
			client_seq INTEGER NOT NULL,
			payload_json TEXT NOT NULL,
			claimed_at INTEGER NOT NULL,
			UNIQUE(machine_id, client_seq)
		)`,
		`CREATE TABLE IF NOT EXISTS admit_meta (
			key TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS resume_applied (
			resume_path TEXT NOT NULL,
			line_no INTEGER NOT NULL,
			applied_at INTEGER NOT NULL,
			PRIMARY KEY (resume_path, line_no)
		)`,
	}
	for _, s := range stmts {
		if _, err := db.SQL.Exec(s); err != nil {
			return fmt.Errorf("migrate: %w", err)
		}
	}
	return nil
}

func (db *DB) Close() error {
	return db.SQL.Close()
}
