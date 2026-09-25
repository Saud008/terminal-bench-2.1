package model

type ChatEvent struct {
	EventID      string         `json:"event_id"`
	RoomID       string         `json:"room_id,omitempty"`
	Sender       string         `json:"sender"`
	Type         string         `json:"type"`
	VectorClock  map[string]int `json:"vector_clock"`
	TimestampMs  int64          `json:"timestamp_ms"`
	Payload      map[string]any `json:"payload"`
}

type StagedEvent struct {
	EventID     string         `json:"event_id"`
	Sender      string         `json:"sender"`
	Type        string         `json:"type"`
	VectorClock map[string]int `json:"vector_clock"`
	TimestampMs int64          `json:"timestamp_ms"`
	Payload     map[string]any `json:"payload"`
}

type ChatStaging struct {
	Engine        string        `json:"engine"`
	Room          string        `json:"room"`
	Scenario      string        `json:"scenario"`
	ShardCount    int           `json:"shard_count"`
	EventCount    int           `json:"event_count"`
	Events        []StagedEvent `json:"events"`
	StagingDigest string        `json:"staging_digest"`
}

type Finding struct {
	Code    string `json:"code"`
	EventID string `json:"event_id"`
	Detail  string `json:"detail"`
}

type ReconcileFindings struct {
	Scenario     string    `json:"scenario"`
	FindingCount int       `json:"finding_count"`
	Findings     []Finding `json:"findings"`
}

type GenerationFile struct {
	ReconcileRevision int `json:"reconcile_revision"`
}

type TimelineRow struct {
	Seq            int            `json:"seq"`
	EventID        string         `json:"event_id"`
	Type           string         `json:"type"`
	Sender         string         `json:"sender"`
	VectorClock    map[string]int `json:"vector_clock"`
	Visible        bool           `json:"visible"`
	TimelineDigest string         `json:"timeline_digest,omitempty"`
}

type ModerationPayload struct {
	Action string `json:"action"`
	Target string `json:"target"`
}

type ReceiptPayload struct {
	RefEventID     string         `json:"ref_event_id"`
	Recipient      string         `json:"recipient"`
	DeliveredClock map[string]int `json:"delivered_clock"`
}

type MutePayload struct {
	Target  string `json:"target"`
	StartMs int64  `json:"start_ms"`
	EndMs   int64  `json:"end_ms"`
}
