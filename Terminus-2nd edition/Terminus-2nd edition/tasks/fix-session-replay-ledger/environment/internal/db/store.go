package db

import (
	"database/sql"
	_ "embed"
	"fmt"
	"os"
	"path/filepath"

	_ "modernc.org/sqlite"

	"github.com/harbor/fix-session-replay-ledger/internal/model"
)

//go:embed schema.sql
var schemaSQL string

type Store struct {
	conn *sql.DB
}

func Open(path string) (*Store, error) {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return nil, err
	}
	conn, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}
	if _, err := conn.Exec(schemaSQL); err != nil {
		_ = conn.Close()
		return nil, err
	}
	return &Store{conn: conn}, nil
}

func (s *Store) Close() error {
	return s.conn.Close()
}

func (s *Store) InsertExecution(ex model.Execution) (bool, error) {
	res, err := s.conn.Exec(
		`INSERT INTO executions (
			session_file, file_offset, cl_ord_id, exec_id, symbol, side,
			last_qty, last_px, order_qty, msg_type, exec_type, sending_time, raw_message
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		ex.SessionFile, ex.FileOffset, ex.ClOrdID, ex.ExecID, ex.Symbol, ex.Side,
		ex.LastQty, ex.LastPx, ex.OrderQty, ex.MsgType, ex.ExecType, ex.SendingTime, ex.Raw,
	)
	if err != nil {
		return false, err
	}
	n, _ := res.RowsAffected()
	return n > 0, nil
}

func (s *Store) AllExecutions() ([]model.Execution, error) {
	rows, err := s.conn.Query(
		`SELECT session_file, file_offset, cl_ord_id, exec_id, symbol, side,
		        last_qty, last_px, order_qty, msg_type, exec_type, sending_time, raw_message
		 FROM executions ORDER BY file_offset ASC, session_file ASC`,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Execution
	for rows.Next() {
		var ex model.Execution
		if err := rows.Scan(
			&ex.SessionFile, &ex.FileOffset, &ex.ClOrdID, &ex.ExecID, &ex.Symbol, &ex.Side,
			&ex.LastQty, &ex.LastPx, &ex.OrderQty, &ex.MsgType, &ex.ExecType, &ex.SendingTime, &ex.Raw,
		); err != nil {
			return nil, err
		}
		out = append(out, ex)
	}
	return out, rows.Err()
}

func (s *Store) Count() (int, error) {
	var n int
	err := s.conn.QueryRow(`SELECT COUNT(*) FROM executions`).Scan(&n)
	return n, err
}

func (s *Store) Exists(clOrdID, execID string) (bool, error) {
	var n int
	err := s.conn.QueryRow(
		`SELECT COUNT(*) FROM executions WHERE cl_ord_id = ? AND exec_id = ?`,
		clOrdID, execID,
	).Scan(&n)
	if err != nil {
		return false, err
	}
	return n > 0, nil
}

func ReplaySortKey(ex model.Execution) string {
	return fmt.Sprintf("%s\x00%s\x00%s", ex.SendingTime, ex.ClOrdID, ex.ExecID)
}
