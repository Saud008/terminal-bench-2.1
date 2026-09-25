package store

import (
	"database/sql"
	"fmt"

	"github.com/terminus/livattest-gate/internal/model"
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

func (s *Store) Reset() error {
	_, err := s.db.Exec(`
DELETE FROM sessions;
DELETE FROM breach_seals;
DELETE FROM breach_repaired;
DELETE FROM ban_seals;
DELETE FROM counters;
DELETE FROM accepted_seqs;
`)
	return err
}

func (s *Store) UpsertSession(sess model.SessionState) error {
	_, err := s.db.Exec(`
INSERT INTO sessions (token, session_id, last_seq, has_last_seq, anchor_client_ms, anchor_mono_ms, admission_ticket, skew_rejections, duplicate_rejections, ticket_rejections)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(token, session_id) DO UPDATE SET
    last_seq=excluded.last_seq,
    has_last_seq=excluded.has_last_seq,
    anchor_client_ms=excluded.anchor_client_ms,
    anchor_mono_ms=excluded.anchor_mono_ms,
    admission_ticket=excluded.admission_ticket,
    skew_rejections=excluded.skew_rejections,
    duplicate_rejections=excluded.duplicate_rejections,
    ticket_rejections=excluded.ticket_rejections
`, sess.Token, sess.SessionID, sess.LastSeq, boolToInt(sess.HasLastSeq), sess.AnchorClient, sess.AnchorMono, sess.AdmissionTicket, sess.SkewRejects, sess.DupRejects, sess.TicketRejects)
	return err
}

func (s *Store) GetSession(token, sessionID string) (model.SessionState, error) {
	row := s.db.QueryRow(`
SELECT token, session_id, last_seq, has_last_seq, anchor_client_ms, anchor_mono_ms, admission_ticket, skew_rejections, duplicate_rejections, ticket_rejections
FROM sessions WHERE token=? AND session_id=?
`, token, sessionID)
	var sess model.SessionState
	var has int
	if err := row.Scan(&sess.Token, &sess.SessionID, &sess.LastSeq, &has, &sess.AnchorClient, &sess.AnchorMono, &sess.AdmissionTicket, &sess.SkewRejects, &sess.DupRejects, &sess.TicketRejects); err != nil {
		return model.SessionState{}, err
	}
	sess.HasLastSeq = has != 0
	return sess, nil
}

func (s *Store) SessionExists(token, sessionID string) (bool, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM sessions WHERE token=? AND session_id=?`, token, sessionID).Scan(&n)
	return n > 0, err
}

func (s *Store) OpenBreach(token, sessionID string, fromSeq, toSeq, span uint32, monoMs int64) (int64, error) {
	res, err := s.db.Exec(`
INSERT INTO breach_seals (token, session_id, from_seq, to_seq, missing_span, opened_mono_ms, closed, closed_mono_ms)
VALUES (?, ?, ?, ?, ?, ?, 0, 0)
`, token, sessionID, fromSeq, toSeq, span, monoMs)
	if err != nil {
		return 0, err
	}
	id, err := res.LastInsertId()
	if err != nil {
		return 0, err
	}
	_, err = s.db.Exec(`
INSERT INTO counters (token, session_id, breaches_opened, breaches_closed, missing_span_total, repair_events)
VALUES (?, ?, 1, 0, ?, 0)
ON CONFLICT(token, session_id) DO UPDATE SET
    breaches_opened = breaches_opened + 1,
    missing_span_total = missing_span_total + excluded.missing_span_total
`, token, sessionID, span)
	return id, err
}

func (s *Store) IssueBan(token, sessionID string, breachID int64, monoMs int64) error {
	_, err := s.db.Exec(`
INSERT OR REPLACE INTO ban_seals (breach_id, token, session_id, issued_mono_ms, active)
VALUES (?, ?, ?, ?, 1)
`, breachID, token, sessionID, monoMs)
	return err
}

func (s *Store) DeactivateBan(breachID int64) error {
	_, err := s.db.Exec(`UPDATE ban_seals SET active=0 WHERE breach_id=? AND active=1`, breachID)
	return err
}

func (s *Store) CountActiveBans(token, sessionID string) (int, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM ban_seals WHERE token=? AND session_id=? AND active=1
`, token, sessionID).Scan(&n)
	return n, err
}

func (s *Store) OpenBreaches(token, sessionID string) ([]model.BreachSeal, error) {
	rows, err := s.db.Query(`
SELECT id, from_seq, to_seq, missing_span, opened_mono_ms, closed
FROM breach_seals WHERE token=? AND session_id=? AND closed=0 ORDER BY id
`, token, sessionID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.BreachSeal
	for rows.Next() {
		var b model.BreachSeal
		var closed int
		if err := rows.Scan(&b.ID, &b.FromSeq, &b.ToSeq, &b.MissingSpan, &b.OpenedMonoMs, &closed); err != nil {
			return nil, err
		}
		b.Closed = closed != 0
		out = append(out, b)
	}
	return out, rows.Err()
}

func (s *Store) IsRepaired(breachID int64, seq uint32) (bool, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM breach_repaired WHERE breach_id=? AND seq=?`, breachID, seq).Scan(&n)
	return n > 0, err
}

func (s *Store) MarkRepaired(token, sessionID string, breachID int64, seq uint32) error {
	_, err := s.db.Exec(`INSERT OR IGNORE INTO breach_repaired (breach_id, seq) VALUES (?, ?)`, breachID, seq)
	if err != nil {
		return err
	}
	_, err = s.db.Exec(`
INSERT INTO counters (token, session_id, breaches_opened, breaches_closed, missing_span_total, repair_events)
VALUES (?, ?, 0, 0, 0, 1)
ON CONFLICT(token, session_id) DO UPDATE SET repair_events = repair_events + 1
`, token, sessionID)
	return err
}

func (s *Store) RepairedCount(breachID int64) (int, error) {
	var n int
	err := s.db.QueryRow(`SELECT COUNT(1) FROM breach_repaired WHERE breach_id=?`, breachID).Scan(&n)
	return n, err
}

func (s *Store) CloseBreach(token, sessionID string, breachID int64, monoMs int64) error {
	res, err := s.db.Exec(`
UPDATE breach_seals SET closed=1, closed_mono_ms=? WHERE id=? AND closed=0
`, monoMs, breachID)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return nil
	}
	_, err = s.db.Exec(`
UPDATE counters SET breaches_closed = breaches_closed + 1 WHERE token=? AND session_id=?
`, token, sessionID)
	return err
}

func (s *Store) BreachOpenedMono(breachID int64) (int64, error) {
	var ms int64
	err := s.db.QueryRow(`SELECT opened_mono_ms FROM breach_seals WHERE id=?`, breachID).Scan(&ms)
	return ms, err
}

func (s *Store) Counters(token, sessionID string) (opened, closed, spanTotal, repairs int, err error) {
	err = s.db.QueryRow(`
SELECT breaches_opened, breaches_closed, missing_span_total, repair_events FROM counters WHERE token=? AND session_id=?
`, token, sessionID).Scan(&opened, &closed, &spanTotal, &repairs)
	if err == sql.ErrNoRows {
		return 0, 0, 0, 0, nil
	}
	return opened, closed, spanTotal, repairs, err
}

func (s *Store) RecordAccepted(token, sessionID string, seq uint32) error {
	_, err := s.db.Exec(`
INSERT OR IGNORE INTO accepted_seqs (token, session_id, seq) VALUES (?, ?, ?)
`, token, sessionID, seq)
	return err
}

func (s *Store) HasSeenSeq(token, sessionID string, seq uint32) (bool, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM accepted_seqs WHERE token=? AND session_id=? AND seq=?
`, token, sessionID, seq).Scan(&n)
	return n > 0, err
}

// HasSeenSeqToken is a decoy: token-wide last_seq match — wrong for rebind.
func (s *Store) HasSeenSeqToken(token string, seq uint32) (bool, error) {
	var n int
	err := s.db.QueryRow(`
SELECT COUNT(1) FROM sessions WHERE token=? AND has_last_seq=1 AND last_seq=?
`, token, seq).Scan(&n)
	return n > 0, err
}

func boolToInt(v bool) int {
	if v {
		return 1
	}
	return 0
}

func (s *Store) DumpSession(token, sessionID string) (string, error) {
	sess, err := s.GetSession(token, sessionID)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%s:%s last=%d", sess.Token, sess.SessionID, sess.LastSeq), nil
}
