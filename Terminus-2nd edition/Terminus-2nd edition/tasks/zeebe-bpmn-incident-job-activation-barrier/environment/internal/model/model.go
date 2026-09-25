package model

type Scenario struct {
	ProcessID       string          `json:"process_id"`
	PartitionID     int             `json:"partition_id"`
	BrokerClockMs   int64           `json:"broker_clock_ms"`
	ProcessClockMs  int64           `json:"process_clock_ms"`
	JobTimeoutMs    int64           `json:"job_timeout_ms"`
	Incidents       []Incident      `json:"incidents"`
	Jobs            []JobSpec       `json:"jobs"`
	Boundaries      []BoundaryEvent `json:"boundaries"`
	Variables       VariableBlock   `json:"variables"`
	ReplayBatches   []ReplayBatch   `json:"replay_batches"`
}

type Incident struct {
	IncidentKey          string `json:"incident_key"`
	ElementID            string `json:"element_id"`
	JobKey               string `json:"job_key"`
	ResolvedAtMs         int64  `json:"resolved_at_ms"`
	MarkerPersistedAtMs  int64  `json:"marker_persisted_at_ms"`
}

type JobSpec struct {
	JobKey            string `json:"job_key"`
	ElementID         string `json:"element_id"`
	Type              string `json:"type"`
	IntentAtMs        int64  `json:"intent_at_ms"`
	ActivatingUntilMs int64  `json:"activating_until_ms"`
}

type BoundaryEvent struct {
	BoundaryID      string `json:"boundary_id"`
	AttachedElement string `json:"attached_element"`
	FireAtMs        int64  `json:"fire_at_ms"`
	Interrupting    bool   `json:"interrupting"`
}

type VariableBlock struct {
	Inputs         map[string]int `json:"inputs"`
	OutputMapping  map[string]string `json:"output_mapping"`
	IncidentOverlay map[string]int `json:"incident_overlay"`
}

type ReplayBatch struct {
	BatchID    string   `json:"batch_id"`
	JobKeys    []string `json:"job_keys"`
	Idempotent bool     `json:"idempotent"`
}

type Snapshot struct {
	ProcessID                 string            `json:"process_id"`
	PartitionID               int               `json:"partition_id"`
	IncidentMarkerPersistedMs map[string]int64  `json:"incident_marker_persisted_ms"`
	PendingJobKeys            []string          `json:"pending_job_keys"`
	BoundaryEventsFired       []string          `json:"boundary_events_fired"`
	DedupPairs                []string          `json:"dedup_pairs"`
	StagingWritten            bool              `json:"staging_written"`
}

type ActivationRecord struct {
	JobKey        string `json:"job_key"`
	ActivatedAtMs int64  `json:"activated_at_ms"`
	DeadlineMs    int64  `json:"deadline_ms"`
	Barrier       string `json:"barrier"`
	SequenceNo    int    `json:"sequence_no"`
}

type BoundaryRecord struct {
	BoundaryID      string `json:"boundary_id"`
	AttachedElement string `json:"attached_element"`
	FiredAtMs       int64  `json:"fired_at_ms"`
	Interrupting    bool   `json:"interrupting"`
}

type VariableSnapshot struct {
	Working         map[string]int `json:"working"`
	ResolvedOutputs map[string]int `json:"resolved_outputs"`
}

type ExportReport struct {
	ProcessID                   string             `json:"process_id"`
	PartitionID                 int                `json:"partition_id"`
	ActivationSequence          []ActivationRecord `json:"activation_sequence"`
	BoundaryEvents              []BoundaryRecord   `json:"boundary_events"`
	VariableSnapshot            VariableSnapshot   `json:"variable_snapshot"`
	DuplicateActivationsSkipped int                `json:"duplicate_activations_skipped"`
	DeadlineClockSource         string             `json:"deadline_clock_source"`
}
