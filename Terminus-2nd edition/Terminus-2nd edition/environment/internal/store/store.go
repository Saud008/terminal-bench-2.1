package store

import (
	"database/sql"

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
	if _, err := db.Exec(SchemaSQL); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) DB() *sql.DB {
	return s.db
}

func (s *Store) Reset() error {
	_, err := s.db.Exec(`
DELETE FROM idempotency;
DELETE FROM invites;
DELETE FROM members;
DELETE FROM parties;
`)
	return err
}

func (s *Store) CountParties() (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM parties`).Scan(&n)
	return n, err
}

func (s *Store) CountMembers(partyID string) (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM members WHERE party_id=?`, partyID).Scan(&n)
	return n, err
}

func (s *Store) CountConnectedMembers(partyID string) (int, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM members WHERE party_id=? AND status='connected'
`, partyID).Scan(&n)
	return n, err
}

func (s *Store) LeaderConnected(partyID string) (bool, error) {
	var status string
	err := s.db.QueryRow(`
SELECT m.status FROM parties p
JOIN members m ON m.party_id=p.party_id AND m.player_id=p.leader_id
WHERE p.party_id=?
`, partyID).Scan(&status)
	if err == sql.ErrNoRows {
		return false, nil
	}
	if err != nil {
		return false, err
	}
	return status == "connected", nil
}
