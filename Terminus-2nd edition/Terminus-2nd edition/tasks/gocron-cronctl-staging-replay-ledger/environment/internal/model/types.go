package model

type Config struct {
	LedgerPath      string `json:"ledger_path"`
	StagingPath     string `json:"staging_path"`
	DefaultLocation string `json:"default_location"`
	LockLeaseMs     int64  `json:"lock_lease_ms"`
	TickMs          int64  `json:"tick_ms"`
}

type JobSpec struct {
	ID       string            `json:"id"`
	Cron     string            `json:"cron"`
	Location string            `json:"location"`
	Tags     map[string]string `json:"tags"`
	Singleton bool             `json:"singleton"`
}

type Scenario struct {
	WindowStart string    `json:"window_start"`
	WindowEndMs int64     `json:"window_end_ms"`
	Jobs        []JobSpec `json:"jobs"`
	Events      []Event   `json:"events"`
}

type Event struct {
	AtMs    int64  `json:"at_ms"`
	JobID   string `json:"job_id"`
	Action  string `json:"action"`
	Panic   bool   `json:"panic"`
}

type PlannedFire struct {
	JobID string `json:"job_id"`
	AtMs  int64  `json:"at_ms"`
}

type Snapshot struct {
	Seed              string        `json:"seed"`
	Scenario          string        `json:"scenario"`
	Location          string        `json:"location"`
	Engine            string        `json:"engine"`
	FiresDigest       string        `json:"fires_digest"`
	ReplayGeneration  int           `json:"replay_generation"`
	PlannedFires      []PlannedFire `json:"planned_fires"`
}

type ExecutionRow struct {
	JobID      string `json:"job_id"`
	FiredAtMs  int64  `json:"fired_at_ms"`
	Status     string `json:"status"`
	LockHeld   bool   `json:"lock_held"`
	Deduped    bool   `json:"deduped"`
}

type LedgerExport struct {
	Seed       string         `json:"seed"`
	Scenario   string         `json:"scenario"`
	Executions []ExecutionRow `json:"executions"`
	FireCount  int            `json:"fire_count"`
	DedupCount int            `json:"dedup_count"`
}
