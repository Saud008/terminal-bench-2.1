package model

type StickyGeneration struct {
	Generation int    `json:"generation"`
	Partition  string `json:"partition"`
	AtMs       int64  `json:"at_ms"`
}

type HistoryEvent struct {
	EventID int    `json:"event_id"`
	Seq     int    `json:"seq"`
	Name    string `json:"name"`
	AtMs    int64  `json:"at_ms"`
}

type Heartbeat struct {
	ProgressSeq    int    `json:"progress_seq"`
	AtMs           int64  `json:"at_ms"`
	DecisionTaskID string `json:"decision_task_id"`
}

type QueryTask struct {
	QueryID             string `json:"query_id"`
	IsResetWorkflow     bool   `json:"is_reset_workflow"`
	RequiredProgressSeq int    `json:"required_progress_seq"`
	AtMs                int64  `json:"at_ms"`
}

type Scenario struct {
	WorkflowID            string             `json:"workflow_id"`
	RunID                 string             `json:"run_id"`
	VisibilityTimeoutMs   int64              `json:"visibility_timeout_ms"`
	StartToCloseTimeoutMs int64              `json:"start_to_close_timeout_ms"`
	HeartbeatGraceMs      int64              `json:"heartbeat_grace_ms"`
	DecisionTaskID        string             `json:"decision_task_id"`
	TaskStartMs           int64              `json:"task_start_ms"`
	DecisionPollMs        int64              `json:"decision_poll_ms"`
	StickyGenerations     []StickyGeneration `json:"sticky_generations"`
	HistoryEvents         []HistoryEvent     `json:"history_events"`
	Heartbeats            []Heartbeat        `json:"heartbeats"`
	TimeoutChecksMs       []int64            `json:"timeout_checks_ms"`
	QueryTasks            []QueryTask        `json:"query_tasks"`
}

type QueryResult struct {
	QueryID  string `json:"query_id"`
	Accepted bool   `json:"accepted"`
	Reason   string `json:"reason"`
}

type ReplayReport struct {
	WorkflowID           string        `json:"workflow_id"`
	VisibilityDeadlineMs int64         `json:"visibility_deadline_ms"`
	LastProgressSeq      int           `json:"last_progress_seq"`
	StickyPartition      string        `json:"sticky_partition"`
	HistoryCursorSeq     int           `json:"history_cursor_seq"`
	HistoryEventsApplied []string      `json:"history_events_applied"`
	DuplicateEventsSkipped int         `json:"duplicate_events_skipped"`
	DecisionTaskLost     bool          `json:"decision_task_lost"`
	TimedOut             bool          `json:"timed_out"`
	QueryResults         []QueryResult `json:"query_results"`
	LostDecisionReason   string        `json:"lost_decision_reason"`
	LastHeartbeatMs      int64         `json:"last_heartbeat_ms"`
}

type RuntimeState struct {
	Scenario             Scenario
	VisibilityDeadlineMs int64
	LastProgressSeq      int
	LastHeartbeatMs      int64
	StickyGeneration     int
	StickyPartition      string
	HistoryCursorSeq     int
	SeenEventIDs         map[int]bool
	AppliedNames         []string
	DuplicateSkipped     int
	DecisionTaskLost     bool
	LostDecisionReason   string
	TimedOut             bool
	QueryResults         []QueryResult
}
