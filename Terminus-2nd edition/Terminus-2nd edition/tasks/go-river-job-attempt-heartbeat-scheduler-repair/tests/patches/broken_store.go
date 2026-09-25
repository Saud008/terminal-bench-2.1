package store

import (
	"database/sql"
	"fmt"

	"github.com/terminus/riverbench/internal/model"

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
	if _, err := db.Exec(schemaSQL); err != nil {
		_ = db.Close()
		return nil, err
	}
	return &Store{db: db}, nil
}

func (s *Store) Close() error {
	return s.db.Close()
}

func (s *Store) Reset() error {
	if _, err := s.db.Exec(`DELETE FROM leases; DELETE FROM jobs;`); err != nil {
		return err
	}
	return nil
}

func (s *Store) InsertJob(job model.Job) error {
	_, err := s.db.Exec(
		`INSERT INTO jobs(id, kind, payload, priority, state, attempts, max_attempts, available_at_ms, created_at_ms, finished_at_ms, last_error)
		 VALUES(?,?,?,?,?,?,?,?,?,?,?)`,
		job.ID, job.Kind, job.Payload, job.Priority, job.State, job.Attempts, job.MaxAttempts,
		job.AvailableAt, job.CreatedAt, job.FinishedAt, job.LastError,
	)
	return err
}

func (s *Store) ListJobs(state string) ([]model.Job, error) {
	var rows *sql.Rows
	var err error
	if state == "" {
		rows, err = s.db.Query(`SELECT id, kind, payload, priority, state, attempts, max_attempts, available_at_ms, created_at_ms, finished_at_ms, last_error FROM jobs ORDER BY id`)
	} else {
		rows, err = s.db.Query(`SELECT id, kind, payload, priority, state, attempts, max_attempts, available_at_ms, created_at_ms, finished_at_ms, last_error FROM jobs WHERE state=? ORDER BY id`, state)
	}
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Job
	for rows.Next() {
		var j model.Job
		if err := rows.Scan(&j.ID, &j.Kind, &j.Payload, &j.Priority, &j.State, &j.Attempts, &j.MaxAttempts, &j.AvailableAt, &j.CreatedAt, &j.FinishedAt, &j.LastError); err != nil {
			return nil, err
		}
		out = append(out, j)
	}
	if out == nil {
		out = []model.Job{}
	}
	return out, rows.Err()
}

func (s *Store) GetJob(id string) (model.Job, error) {
	row := s.db.QueryRow(`SELECT id, kind, payload, priority, state, attempts, max_attempts, available_at_ms, created_at_ms, finished_at_ms, last_error FROM jobs WHERE id=?`, id)
	var j model.Job
	if err := row.Scan(&j.ID, &j.Kind, &j.Payload, &j.Priority, &j.State, &j.Attempts, &j.MaxAttempts, &j.AvailableAt, &j.CreatedAt, &j.FinishedAt, &j.LastError); err != nil {
		return model.Job{}, err
	}
	return j, nil
}

func (s *Store) UpdateJob(job model.Job) error {
	_, err := s.db.Exec(
		`UPDATE jobs SET kind=?, payload=?, priority=?, state=?, attempts=?, max_attempts=?, available_at_ms=?, finished_at_ms=?, last_error=? WHERE id=?`,
		job.Kind, job.Payload, job.Priority, job.State, job.Attempts, job.MaxAttempts, job.AvailableAt, job.FinishedAt, job.LastError, job.ID,
	)
	return err
}

func (s *Store) ListPendingReady(nowMs int64) ([]model.Job, error) {
	rows, err := s.db.Query(
		`SELECT id, kind, payload, priority, state, attempts, max_attempts, available_at_ms, created_at_ms, finished_at_ms, last_error
		 FROM jobs WHERE state=? AND available_at_ms <= ?`,
		model.StatePending, nowMs,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Job
	for rows.Next() {
		var j model.Job
		if err := rows.Scan(&j.ID, &j.Kind, &j.Payload, &j.Priority, &j.State, &j.Attempts, &j.MaxAttempts, &j.AvailableAt, &j.CreatedAt, &j.FinishedAt, &j.LastError); err != nil {
			return nil, err
		}
		out = append(out, j)
	}
	return out, rows.Err()
}

func (s *Store) UpsertLease(lease model.Lease) error {
	_, err := s.db.Exec(
		`INSERT INTO leases(job_id, worker_id, expires_at_ms, heartbeat_at_ms) VALUES(?,?,?,?)
		 ON CONFLICT(job_id) DO UPDATE SET worker_id=excluded.worker_id, expires_at_ms=excluded.expires_at_ms, heartbeat_at_ms=excluded.heartbeat_at_ms`,
		lease.JobID, lease.WorkerID, lease.ExpiresAtMs, lease.HeartbeatMs,
	)
	return err
}

func (s *Store) GetLease(jobID string) (model.Lease, error) {
	row := s.db.QueryRow(`SELECT job_id, worker_id, expires_at_ms, heartbeat_at_ms FROM leases WHERE job_id=?`, jobID)
	var l model.Lease
	if err := row.Scan(&l.JobID, &l.WorkerID, &l.ExpiresAtMs, &l.HeartbeatMs); err != nil {
		return model.Lease{}, err
	}
	return l, nil
}

func (s *Store) GetLatestLeaseForWorker(workerID string) (model.Lease, error) {
	row := s.db.QueryRow(
		`SELECT job_id, worker_id, expires_at_ms, heartbeat_at_ms FROM leases WHERE worker_id=? ORDER BY heartbeat_at_ms DESC LIMIT 1`,
		workerID,
	)
	var l model.Lease
	if err := row.Scan(&l.JobID, &l.WorkerID, &l.ExpiresAtMs, &l.HeartbeatMs); err != nil {
		return model.Lease{}, err
	}
	return l, nil
}

func (s *Store) ListLeases() ([]model.Lease, error) {
	rows, err := s.db.Query(`SELECT job_id, worker_id, expires_at_ms, heartbeat_at_ms FROM leases ORDER BY job_id`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []model.Lease
	for rows.Next() {
		var l model.Lease
		if err := rows.Scan(&l.JobID, &l.WorkerID, &l.ExpiresAtMs, &l.HeartbeatMs); err != nil {
			return nil, err
		}
		out = append(out, l)
	}
	if out == nil {
		out = []model.Lease{}
	}
	return out, rows.Err()
}

func (s *Store) DeleteLease(jobID string) error {
	_, err := s.db.Exec(`DELETE FROM leases WHERE job_id=?`, jobID)
	return err
}

// MarkFinished updates job state when a worker acks.
func (s *Store) MarkFinished(job model.Job, nowMs int64) error {
	job.State = model.StateFinished
	job.FinishedAt = nowMs
	if err := s.UpdateJob(job); err != nil {
		return err
	}
	return nil
}

func (s *Store) SetLeaseExpiry(jobID string, expiresAtMs int64) error {
	res, err := s.db.Exec(`UPDATE leases SET expires_at_ms=? WHERE job_id=?`, expiresAtMs, jobID)
	if err != nil {
		return err
	}
	n, _ := res.RowsAffected()
	if n == 0 {
		return fmt.Errorf("lease not found for job %s", jobID)
	}
	return nil
}
