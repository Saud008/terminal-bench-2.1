package store

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"
)

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	dsn := fmt.Sprintf("file:%s?_pragma=foreign_keys(1)&_pragma=journal_mode(WAL)&_pragma=busy_timeout(10000)", path)
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, err
	}
	if err := db.Ping(); err != nil {
		return nil, err
	}
	st := &Store{db: db}
	if err := st.migrate(); err != nil {
		return nil, err
	}
	return st, nil
}

func (s *Store) migrate() error {
	if _, err := s.db.Exec(SchemaSQL); err != nil {
		return err
	}
	_, _ = s.db.Exec(`INSERT OR IGNORE INTO tx_lock(lock_id) VALUES (1)`)
	return nil
}

func (s *Store) DB() *sql.DB {
	return s.db
}

func (s *Store) Close() error {
	return s.db.Close()
}

// BeginImmediate acquires an immediate SQLite write lock before balance reads.
func (s *Store) BeginImmediate() (*sql.Tx, error) {
	tx, err := s.db.Begin()
	if err != nil {
		return nil, err
	}
	if _, err := tx.Exec(`UPDATE tx_lock SET lock_id=1 WHERE lock_id=1`); err != nil {
		_ = tx.Rollback()
		return nil, err
	}
	return tx, nil
}

func (s *Store) VaultStackQty(guildID string) (int, error) {
	var qty int
	err := s.db.QueryRow(`
SELECT COALESCE(SUM(quantity), 0) FROM item_stacks WHERE guild_id=?
`, guildID).Scan(&qty)
	return qty, err
}

func (s *Store) WithdrawnSliceQty(guildID string) (int, error) {
	var qty int
	err := s.db.QueryRow(`
SELECT COALESCE(SUM(quantity), 0) FROM withdraw_slices WHERE guild_id=?
`, guildID).Scan(&qty)
	return qty, err
}

func (s *Store) CountAudit(guildID string) (committed int, orphan int, err error) {
	if err = s.db.QueryRow(`
SELECT COUNT(1) FROM audit_entries WHERE guild_id=? AND committed=1
`, guildID).Scan(&committed); err != nil {
		return
	}
	if err = s.db.QueryRow(`
SELECT COUNT(1) FROM audit_entries a
WHERE a.guild_id=? AND a.committed=1 AND (
  (a.op_type='withdraw_gold' AND json_extract(a.payload_json,'$.balance') IS NULL)
  OR (
    a.op_type='withdraw_gold'
    AND json_extract(a.payload_json,'$.balance') IS NOT NULL
    AND CAST(json_extract(a.payload_json,'$.balance') AS INTEGER) != (
      SELECT gold_balance FROM guilds WHERE guild_id=a.guild_id
    )
  )
  OR (
    a.op_type='withdraw_stack'
    AND CAST(json_extract(a.payload_json,'$.quantity') AS INTEGER) > (
      SELECT COALESCE(SUM(quantity), 0) FROM withdraw_slices WHERE guild_id=a.guild_id
    )
  )
)
`, guildID).Scan(&orphan); err != nil {
		return
	}
	return
}

func (s *Store) InterestAppliedTotal(guildID string) (int64, error) {
	var total int64
	err := s.db.QueryRow(`
SELECT COALESCE(SUM(interest_amount), 0) FROM interest_journal
WHERE guild_id=? AND status='applied'
`, guildID).Scan(&total)
	return total, err
}
