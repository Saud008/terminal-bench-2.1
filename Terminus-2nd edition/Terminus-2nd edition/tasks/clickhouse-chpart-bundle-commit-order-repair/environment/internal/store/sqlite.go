package store

import (
	"database/sql"
	"fmt"

	"github.com/clickparts/chparts/internal/model"

	_ "modernc.org/sqlite"
)

const schema = `
CREATE TABLE IF NOT EXISTS parts (
  part_id TEXT PRIMARY KEY,
  batch_id TEXT NOT NULL,
  checksum_ok INTEGER NOT NULL DEFAULT 0,
  committed INTEGER NOT NULL DEFAULT 0,
  min_block INTEGER NOT NULL,
  max_block INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rows (
  id TEXT NOT NULL,
  ver INTEGER NOT NULL,
  value TEXT NOT NULL,
  expire_ts INTEGER NOT NULL,
  part_id TEXT NOT NULL,
  table_name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS commit_log (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  max_block INTEGER NOT NULL DEFAULT 0,
  fsynced INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS ingest_keys (
  idempotency_key TEXT PRIMARY KEY,
  part_id TEXT NOT NULL
);
`

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := db.Exec(schema); err != nil {
		_ = db.Close()
		return nil, err
	}
	if _, err := db.Exec(`INSERT OR IGNORE INTO commit_log(id, max_block, fsynced) VALUES(1, 0, 0)`); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error { return s.db.Close() }

func (s *Store) Reset() error {
	_, err := s.db.Exec(`DELETE FROM rows; DELETE FROM parts; DELETE FROM ingest_keys; UPDATE commit_log SET max_block=0, fsynced=0 WHERE id=1`)
	return err
}

func (s *Store) RegisterPart(meta model.PartMeta, committed bool) error {
	c := 0
	if committed {
		c = 1
	}
	_, err := s.db.Exec(
		`INSERT OR REPLACE INTO parts(part_id, batch_id, checksum_ok, committed, min_block, max_block) VALUES(?,?,0,?,?,?)`,
		meta.PartID, meta.BatchID, c, meta.MinBlock, meta.MaxBlock,
	)
	return err
}

func (s *Store) MarkChecksumOK(partID string, ok bool) error {
	v := 0
	if ok {
		v = 1
	}
	_, err := s.db.Exec(`UPDATE parts SET checksum_ok=? WHERE part_id=?`, v, partID)
	return err
}

func (s *Store) InsertRows(tableName string, rows []model.Row) error {
	tx, err := s.db.Begin()
	if err != nil {
		return err
	}
	for _, r := range rows {
		if _, err := tx.Exec(
			`INSERT INTO rows(id, ver, value, expire_ts, part_id, table_name) VALUES(?,?,?,?,?,?)`,
			r.ID, r.Ver, r.Value, r.ExpireTS, r.PartID, tableName,
		); err != nil {
			_ = tx.Rollback()
			return err
		}
	}
	return tx.Commit()
}

func (s *Store) DeleteExpired(tableName string, cutoff int64) error {
	_, err := s.db.Exec(`DELETE FROM rows WHERE table_name=? AND expire_ts < ?`, tableName, cutoff)
	return err
}

func (s *Store) ListRows(tableName string) ([]model.Row, error) {
	rows, err := s.db.Query(`SELECT id, ver, value, expire_ts, part_id FROM rows WHERE table_name=?`, tableName)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Row
	for rows.Next() {
		var r model.Row
		if err := rows.Scan(&r.ID, &r.Ver, &r.Value, &r.ExpireTS, &r.PartID); err != nil {
			return nil, err
		}
		out = append(out, r)
	}
	return out, rows.Err()
}

func (s *Store) SetMaxBlock(maxBlock int64) error {
	_, err := s.db.Exec(`UPDATE commit_log SET max_block=? WHERE id=1`, maxBlock)
	return err
}

func (s *Store) SetFsynced(fsynced bool) error {
	v := 0
	if fsynced {
		v = 1
	}
	_, err := s.db.Exec(`UPDATE commit_log SET fsynced=? WHERE id=1`, v)
	return err
}

func (s *Store) CommitState() (maxBlock int64, fsynced bool, err error) {
	row := s.db.QueryRow(`SELECT max_block, fsynced FROM commit_log WHERE id=1`)
	var fs int
	if err := row.Scan(&maxBlock, &fs); err != nil {
		return 0, false, err
	}
	return maxBlock, fs == 1, nil
}

func (s *Store) HasIngestKey(key string) (bool, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM ingest_keys WHERE idempotency_key=?`, key).Scan(&n)
	return n > 0, err
}

func (s *Store) RecordIngestKey(key, partID string) error {
	_, err := s.db.Exec(`INSERT INTO ingest_keys(idempotency_key, part_id) VALUES(?,?)`, key, partID)
	return err
}

func (s *Store) PartStats() ([]model.PartStats, error) {
	rows, err := s.db.Query(`SELECT part_id, checksum_ok, committed FROM parts ORDER BY part_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.PartStats
	for rows.Next() {
		var ps model.PartStats
		var ok, committed int
		if err := rows.Scan(&ps.PartID, &ok, &committed); err != nil {
			return nil, err
		}
		ps.ChecksumOK = ok == 1
		ps.Committed = committed == 1
		out = append(out, ps)
	}
	return out, rows.Err()
}

func (s *Store) RowCount(tableName string) (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM rows WHERE table_name=?`, tableName).Scan(&n)
	return n, err
}

func (s *Store) MarkCommitted(partID string) error {
	_, err := s.db.Exec(`UPDATE parts SET committed=1 WHERE part_id=?`, partID)
	return err
}

func (s *Store) MirrorCount(tableName string) (int, error) {
	return s.RowCount(tableName)
}

func (s *Store) EnsureTable(tableName string) error {
	if tableName == "" {
		return fmt.Errorf("empty table")
	}
	return nil
}
