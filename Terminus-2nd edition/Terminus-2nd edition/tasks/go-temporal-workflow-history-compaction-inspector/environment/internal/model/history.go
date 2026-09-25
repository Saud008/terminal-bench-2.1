package model

type HistoryEvent struct {
    Seq            int    `json:"seq"`
    EventID        int    `json:"event_id"`
    Kind           string `json:"kind"`
    WorkflowID     string `json:"workflow_id"`
    RunID          string `json:"run_id"`
    RunGeneration  int    `json:"run_generation"`
    TimestampMs    int64  `json:"timestamp_ms"`
    ActivityID     string `json:"activity_id"`
    Attempt        int    `json:"attempt"`
    TimerID        string `json:"timer_id"`
    ResultStatus   string `json:"result_status"`
}

type HistoryStaging struct {
    Engine         string         `json:"engine"`
    Namespace      string         `json:"namespace"`
    Scenario       string         `json:"scenario"`
    EventCount     int            `json:"event_count"`
    MaxRunGen      int            `json:"max_run_generation"`
    Events         []HistoryEvent `json:"events"`
    StagingDigest  string         `json:"staging_digest"`
}

type Finding struct {
    Code       string `json:"code"`
    WorkflowID string `json:"workflow_id"`
    Detail     string `json:"detail"`
}

type CompactionAudit struct {
    Scenario       string    `json:"scenario"`
    FindingCount   int       `json:"finding_count"`
    CanBoundaries  int       `json:"can_boundaries"`
    Findings       []Finding `json:"findings"`
}

type CompactionSeal struct {
    CompactionSeal int `json:"compaction_seal"`
}

type ActivityRow struct {
    RunGeneration int    `json:"run_generation"`
    ActivityID    string `json:"activity_id"`
    Attempt       int    `json:"attempt"`
    Status        string `json:"status"`
    RiskScore     int    `json:"risk_score"`
}

type RiskRow struct {
    WorkflowID    string `json:"workflow_id"`
    RunGeneration int    `json:"run_generation"`
    RiskCode      string `json:"risk_code"`
    PendingTimers int    `json:"pending_timers"`
    MaxAttempt    int    `json:"max_attempt"`
}
