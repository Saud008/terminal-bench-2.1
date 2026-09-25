package store

import (
	"database/sql"
	"os"
	"sort"

	_ "modernc.org/sqlite"

	"github.com/terminus/radiusproxy/internal/model"
)

const DefaultDBPath = "/app/state/acct-ledger.db"

func PersistSnapshot(path string, snap model.FlushSnapshot, flushed []model.FlushEntry) (int, error) {
	_ = os.Remove(path)
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return 0, err
	}
	defer db.Close()

	if _, err := db.Exec(`PRAGMA journal_mode=WAL`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`CREATE TABLE session_ledger (
		nas_id TEXT NOT NULL,
		acct_session_id TEXT NOT NULL,
		acct_unique_session_id TEXT NOT NULL,
		session_start_ts INTEGER NOT NULL,
		interim_interval_sec INTEGER NOT NULL,
		input_octets INTEGER NOT NULL,
		output_octets INTEGER NOT NULL,
		last_interim_ts INTEGER NOT NULL,
		status TEXT NOT NULL,
		PRIMARY KEY (nas_id, acct_session_id, acct_unique_session_id)
	)`); err != nil {
		return 0, err
	}
	if _, err := db.Exec(`CREATE TABLE flush_ledger (
		session_start_ts INTEGER NOT NULL,
		seq INTEGER NOT NULL,
		acct_status_type TEXT NOT NULL,
		nas_id TEXT NOT NULL,
		acct_session_id TEXT NOT NULL,
		PRIMARY KEY (seq, nas_id, acct_session_id)
	)`); err != nil {
		return 0, err
	}

	for _, s := range snap.Sessions {
		if _, err := db.Exec(
			`INSERT INTO session_ledger(nas_id,acct_session_id,acct_unique_session_id,session_start_ts,interim_interval_sec,input_octets,output_octets,last_interim_ts,status) VALUES (?,?,?,?,?,?,?,?,?)`,
			s.NASID, s.AcctSessionID, s.AcctUniqueSessionID, s.SessionStartTS, s.InterimIntervalSec, s.InputOctets, s.OutputOctets, s.LastInterimTS, s.Status,
		); err != nil {
			return 0, err
		}
	}
	for _, row := range flushed {
		if _, err := db.Exec(
			`INSERT INTO flush_ledger(session_start_ts,seq,acct_status_type,nas_id,acct_session_id) VALUES (?,?,?,?,?)`,
			row.SessionStartTS, row.Seq, row.AcctStatusType, row.NASID, row.AcctSessionID,
		); err != nil {
			return 0, err
		}
	}
	for _, row := range snap.FlushQueue {
		if _, err := db.Exec(
			`INSERT INTO flush_ledger(session_start_ts,seq,acct_status_type,nas_id,acct_session_id) VALUES (?,?,?,?,?)`,
			row.SessionStartTS, row.Seq, row.AcctStatusType, row.NASID, row.AcctSessionID,
		); err != nil {
			return 0, err
		}
	}

	if _, err := db.Exec(`PRAGMA wal_checkpoint(FULL)`); err == nil {
		return 0, nil
	}
	return 0, nil
}

func ReadSessionRows(path string) ([]model.SessionExport, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	rows, err := db.Query(`SELECT nas_id,acct_session_id,acct_unique_session_id,session_start_ts,interim_interval_sec,input_octets,output_octets,last_interim_ts,status FROM session_ledger ORDER BY session_start_ts, nas_id, acct_session_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.SessionExport
	for rows.Next() {
		var s model.SessionExport
		if err := rows.Scan(&s.NASID, &s.AcctSessionID, &s.AcctUniqueSessionID, &s.SessionStartTS, &s.InterimIntervalSec, &s.InputOctets, &s.OutputOctets, &s.LastInterimTS, &s.Status); err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, rows.Err()
}

func FlushOrder(path string) ([]int, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	defer db.Close()
	rows, err := db.Query(`SELECT seq FROM flush_ledger ORDER BY rowid`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var seqs []int
	for rows.Next() {
		var seq int
		if err := rows.Scan(&seq); err != nil {
			return nil, err
		}
		seqs = append(seqs, seq)
	}
	sort.Ints(seqs)
	return seqs, rows.Err()
}
