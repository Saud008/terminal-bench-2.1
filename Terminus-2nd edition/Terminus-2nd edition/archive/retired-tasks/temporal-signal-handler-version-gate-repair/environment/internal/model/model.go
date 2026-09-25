package model

type Scenario struct {
	WorkflowID         string         `json:"workflow_id"`
	PinnedVersion      string         `json:"pinned_version"`
	MigrationVersion   string         `json:"migration_version"`
	ServerTimeBaseMs   int64          `json:"server_time_base_ms"`
	VersionsRegistered []string       `json:"versions_registered"`
	Signals            []SignalEvent  `json:"signals"`
	Activities         []ActivityBeat `json:"activities"`
}

type SignalEvent struct {
	SignalID      string `json:"signal_id"`
	Name          string `json:"name"`
	TargetVersion string `json:"target_version"`
	ServerTimeMs  int64  `json:"server_time_ms"`
}

type ActivityBeat struct {
	ActivityID        string `json:"activity_id"`
	HeartbeatServerMs int64  `json:"heartbeat_server_ms"`
	WorkerTimeMs      int64  `json:"worker_time_ms"`
}

type Snapshot struct {
	WorkflowID      string   `json:"workflow_id"`
	RoutedVersion   string   `json:"routed_version"`
	AckedSignals    []string `json:"acked_signals"`
	StagingWritten  bool     `json:"staging_written"`
	DedupSeen       []string `json:"dedup_seen"`
	DedupSkipped    int      `json:"dedup_skipped"`
	HeartbeatOffset []int64  `json:"heartbeat_offset_ms"`
}

type HistoryEvent struct {
	SignalID string `json:"signal_id"`
	Name     string `json:"name"`
	Version  string `json:"version"`
	OffsetMs int64  `json:"offset_ms"`
}

type ExportReport struct {
	WorkflowID         string         `json:"workflow_id"`
	EffectiveVersion   string         `json:"effective_version"`
	HistoryEvents      []HistoryEvent `json:"history_events"`
	DuplicateSkipped   int            `json:"duplicate_skipped"`
	HeartbeatClockSrc  string         `json:"heartbeat_clock_source"`
	HeartbeatOffsetsMs []int64        `json:"heartbeat_offsets_ms"`
}
