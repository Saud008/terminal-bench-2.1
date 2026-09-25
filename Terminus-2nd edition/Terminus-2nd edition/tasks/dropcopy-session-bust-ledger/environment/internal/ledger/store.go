package ledger

import (
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/terminus/fixdropcopy/internal/model"
)

const DefaultDBPath = "/app/work/dropcopy.db"

type Store struct {
	db *sql.DB
}

func Open(path string) (*Store, error) {
	if path == "" {
		path = DefaultDBPath
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
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
	_, err := s.db.Exec(`CREATE TABLE IF NOT EXISTS ledger_rows (
		exec_id TEXT PRIMARY KEY,
		session TEXT NOT NULL,
		cl_ord_id TEXT NOT NULL,
		orig_cl_ord_id TEXT NOT NULL,
		exec_trans_type TEXT NOT NULL,
		exec_type TEXT NOT NULL,
		symbol TEXT NOT NULL,
		signed_qty INTEGER NOT NULL,
		active INTEGER NOT NULL,
		sending_time TEXT NOT NULL,
		stream_file TEXT NOT NULL
	)`)
	return err
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) Reset() error {
	_, err := s.db.Exec(`DELETE FROM ledger_rows`)
	return err
}

func (s *Store) HasExecID(execID string) (bool, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM ledger_rows WHERE exec_id = ?`, execID).Scan(&n)
	return n > 0, err
}

func (s *Store) InsertRow(row model.LedgerRow) error {
	_, err := s.db.Exec(`INSERT INTO ledger_rows (
		exec_id, session, cl_ord_id, orig_cl_ord_id, exec_trans_type, exec_type,
		symbol, signed_qty, active, sending_time, stream_file
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		row.ExecID, row.Session, row.ClOrdID, row.OrigClOrdID, row.ExecTransType, row.ExecType,
		row.Symbol, row.SignedQty, boolToInt(row.Active), row.SendingTime, row.StreamFile,
	)
	return err
}

func (s *Store) DeactivateByClOrdID(clOrdID string) error {
	_, err := s.db.Exec(`UPDATE ledger_rows SET active = 0 WHERE cl_ord_id = ? AND active = 1`, clOrdID)
	return err
}

func (s *Store) DeactivateCancelsForOrig(origClOrdID string) error {
	_, err := s.db.Exec(`UPDATE ledger_rows SET active = 0 WHERE orig_cl_ord_id = ? AND exec_trans_type = '1' AND active = 1`, origClOrdID)
	return err
}

func (s *Store) CountByType() (bust, correct, cancel int, err error) {
	if err = s.db.QueryRow(`SELECT COUNT(*) FROM ledger_rows WHERE exec_type = 'H'`).Scan(&bust); err != nil {
		return
	}
	if err = s.db.QueryRow(`SELECT COUNT(*) FROM ledger_rows WHERE exec_trans_type = '2'`).Scan(&correct); err != nil {
		return
	}
	err = s.db.QueryRow(`SELECT COUNT(*) FROM ledger_rows WHERE exec_trans_type = '1'`).Scan(&cancel)
	return
}

func (s *Store) ActiveRows() ([]model.LedgerRow, error) {
	rows, err := s.db.Query(`SELECT exec_id, session, cl_ord_id, orig_cl_ord_id, exec_trans_type, exec_type,
		symbol, signed_qty, active, sending_time, stream_file
		FROM ledger_rows WHERE active = 1 ORDER BY sending_time, exec_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.LedgerRow
	for rows.Next() {
		var r model.LedgerRow
		var active int
		if err := rows.Scan(&r.ExecID, &r.Session, &r.ClOrdID, &r.OrigClOrdID, &r.ExecTransType, &r.ExecType,
			&r.Symbol, &r.SignedQty, &active, &r.SendingTime, &r.StreamFile); err != nil {
			return nil, err
		}
		r.Active = active == 1
		out = append(out, r)
	}
	return out, rows.Err()
}

func (s *Store) NetPositions() (map[string]int64, error) {
	rows, err := s.db.Query(`SELECT symbol, SUM(signed_qty) FROM ledger_rows WHERE active = 1 GROUP BY symbol`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	out := map[string]int64{}
	for rows.Next() {
		var sym string
		var qty int64
		if err := rows.Scan(&sym, &qty); err != nil {
			return nil, err
		}
		out[sym] = qty
	}
	return out, rows.Err()
}

func (s *Store) CountAll() (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(*) FROM ledger_rows`).Scan(&n)
	return n, err
}

func boolToInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func (s *Store) BeginBatch() (*sql.Tx, error) {
	return s.db.Begin()
}

func InsertRowTx(tx *sql.Tx, row model.LedgerRow) error {
	_, err := tx.Exec(`INSERT INTO ledger_rows (
		exec_id, session, cl_ord_id, orig_cl_ord_id, exec_trans_type, exec_type,
		symbol, signed_qty, active, sending_time, stream_file
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		row.ExecID, row.Session, row.ClOrdID, row.OrigClOrdID, row.ExecTransType, row.ExecType,
		row.Symbol, row.SignedQty, boolToInt(row.Active), row.SendingTime, row.StreamFile,
	)
	return err
}

func HasExecIDTx(tx *sql.Tx, execID string) (bool, error) {
	var n int
	err := tx.QueryRow(`SELECT COUNT(*) FROM ledger_rows WHERE exec_id = ?`, execID).Scan(&n)
	return n > 0, err
}

func DeactivateByClOrdIDTx(tx *sql.Tx, clOrdID string) error {
	_, err := tx.Exec(`UPDATE ledger_rows SET active = 0 WHERE cl_ord_id = ? AND active = 1`, clOrdID)
	return err
}

func DeactivateCancelsForOrigTx(tx *sql.Tx, origClOrdID string) error {
	_, err := tx.Exec(`UPDATE ledger_rows SET active = 0 WHERE orig_cl_ord_id = ? AND exec_trans_type = '1' AND active = 1`, origClOrdID)
	return err
}

func SignedQty(side string, qty float64) int64 {
	sign := int64(1)
	if side == "2" {
		sign = -1
	}
	return int64(qty) * sign
}

func LookupSignedQtyTx(tx *sql.Tx, clOrdID string) (int64, error) {
	var qty int64
	err := tx.QueryRow(`SELECT signed_qty FROM ledger_rows WHERE cl_ord_id = ? AND active = 1 ORDER BY sending_time DESC LIMIT 1`, clOrdID).Scan(&qty)
	if err == sql.ErrNoRows {
		return 0, fmt.Errorf("missing referenced execution")
	}
	return qty, err
}
