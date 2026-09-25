package ledger

import (
	"database/sql"
	"encoding/json"

	"github.com/terminus/feast-pit-join/internal/model"
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
	stmts := []string{
		`CREATE TABLE IF NOT EXISTS parity_runs (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			seed TEXT NOT NULL,
			scenario TEXT NOT NULL,
			ingest_seq INTEGER NOT NULL,
			parity_ok INTEGER NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS parity_rows (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			run_id INTEGER NOT NULL,
			as_of_ts INTEGER NOT NULL,
			entity_id TEXT NOT NULL,
			feature TEXT NOT NULL,
			offline_value REAL,
			online_value REAL,
			match_ok INTEGER NOT NULL,
			reason TEXT NOT NULL
		)`,
		`CREATE TABLE IF NOT EXISTS parity_summary (
			run_id INTEGER PRIMARY KEY,
			mismatch_count INTEGER NOT NULL,
			ttl_filtered_count INTEGER NOT NULL,
			duplicate_ts_resolved INTEGER NOT NULL,
			as_of_ts_json TEXT NOT NULL
		)`,
	}
	for _, q := range stmts {
		if _, err := s.db.Exec(q); err != nil {
			return err
		}
	}
	return nil
}

func (s *Store) Reset() error {
	for _, q := range []string{
		`DELETE FROM parity_rows`,
		`DELETE FROM parity_summary`,
		`DELETE FROM parity_runs`,
	} {
		if _, err := s.db.Exec(q); err != nil {
			return err
		}
	}
	return nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) InsertRun(seed, scenario string, ingestSeq int64, ok bool) (int64, error) {
	res, err := s.db.Exec(
		`INSERT INTO parity_runs (seed, scenario, ingest_seq, parity_ok) VALUES (?, ?, ?, ?)`,
		seed, scenario, ingestSeq, boolInt(ok),
	)
	if err != nil {
		return 0, err
	}
	return res.LastInsertId()
}

func (s *Store) InsertRow(runID int64, row model.ParityRow) error {
	var off, on interface{}
	if row.OfflineValue != nil {
		off = *row.OfflineValue
	}
	if row.OnlineValue != nil {
		on = *row.OnlineValue
	}
	_, err := s.db.Exec(
		`INSERT INTO parity_rows (run_id, as_of_ts, entity_id, feature, offline_value, online_value, match_ok, reason) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		runID, row.AsOfTS, row.EntityID, row.Feature, off, on, boolInt(row.MatchOK), row.Reason,
	)
	return err
}

func (s *Store) InsertSummary(runID int64, sum model.RunSummary) error {
	asOfJSON := encodeAsOf(sum.AsOfTSList)
	_, err := s.db.Exec(
		`INSERT INTO parity_summary (run_id, mismatch_count, ttl_filtered_count, duplicate_ts_resolved, as_of_ts_json) VALUES (?, ?, ?, ?, ?)`,
		runID, sum.MismatchCount, sum.TTLFilteredCount, sum.DuplicateTSResolved, asOfJSON,
	)
	return err
}

func (s *Store) LatestRun(seed, scenario string) (int64, bool, error) {
	var id int64
	err := s.db.QueryRow(
		`SELECT id FROM parity_runs WHERE seed = ? AND scenario = ? ORDER BY id DESC LIMIT 1`,
		seed, scenario,
	).Scan(&id)
	if err == sql.ErrNoRows {
		return 0, false, nil
	}
	if err != nil {
		return 0, false, err
	}
	return id, true, nil
}

func (s *Store) RunParityOK(runID int64) (bool, error) {
	var ok int
	err := s.db.QueryRow(`SELECT parity_ok FROM parity_runs WHERE id = ?`, runID).Scan(&ok)
	return ok == 1, err
}

func (s *Store) LoadSummary(runID int64) (model.RunSummary, error) {
	var sum model.RunSummary
	var asOfJSON string
	err := s.db.QueryRow(
		`SELECT mismatch_count, ttl_filtered_count, duplicate_ts_resolved, as_of_ts_json FROM parity_summary WHERE run_id = ?`,
		runID,
	).Scan(&sum.MismatchCount, &sum.TTLFilteredCount, &sum.DuplicateTSResolved, &asOfJSON)
	if err != nil {
		return sum, err
	}
	sum.AsOfTSList = decodeAsOf(asOfJSON)
	return sum, nil
}

func (s *Store) CountRows(runID int64) (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM parity_rows WHERE run_id = ?`, runID).Scan(&n)
	return n, err
}

func boolInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func encodeAsOf(list []int64) string {
	b, _ := json.Marshal(list)
	return string(b)
}

func decodeAsOf(s string) []int64 {
	var out []int64
	_ = json.Unmarshal([]byte(s), &out)
	return out
}
