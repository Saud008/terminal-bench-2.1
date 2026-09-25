package model

const (
	StatePending  = "pending"
	StateRunning  = "running"
	StateFinished = "finished"
	StatePoison   = "poison"
)

type Job struct {
	ID           string `json:"id"`
	Kind         string `json:"kind"`
	Payload      string `json:"payload"`
	Priority     int    `json:"priority"`
	State        string `json:"state"`
	Attempts     int    `json:"attempts"`
	MaxAttempts  int    `json:"max_attempts"`
	AvailableAt  int64  `json:"available_at_ms"`
	CreatedAt    int64  `json:"created_at_ms"`
	FinishedAt   int64  `json:"finished_at_ms,omitempty"`
	LastError    string `json:"last_error,omitempty"`
}

type Lease struct {
	JobID       string `json:"job_id"`
	WorkerID    string `json:"worker_id"`
	ExpiresAtMs int64  `json:"expires_at_ms"`
	HeartbeatMs int64  `json:"heartbeat_at_ms"`
}

type SeedJob struct {
	ID          string `json:"id,omitempty"`
	Kind        string `json:"kind"`
	Payload     string `json:"payload"`
	Priority    int    `json:"priority"`
	MaxAttempts int    `json:"max_attempts"`
}

type SeedRequest struct {
	Seed string    `json:"seed"`
	Jobs []SeedJob `json:"jobs,omitempty"`
}
