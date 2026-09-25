package types

// StreamID is a Redis stream entry id milliseconds-sequence.
type StreamID string

// JournalEvent is one JSONL journal line for offline replay.
type JournalEvent struct {
	Seq         int               `json:"seq"`
	Op          string            `json:"op"`
	Stream      string            `json:"stream,omitempty"`
	Group       string            `json:"group,omitempty"`
	Consumer    string            `json:"consumer,omitempty"`
	ID          string            `json:"id,omitempty"`
	IDs         []string          `json:"ids,omitempty"`
	Fields      map[string]string `json:"fields,omitempty"`
	Sub         string            `json:"sub,omitempty"`
	MKStream    bool              `json:"mkstream,omitempty"`
	MinIdleMS   int64             `json:"min_idle_ms,omitempty"`
	Start       string            `json:"start,omitempty"`
	Count       int               `json:"count,omitempty"`
	TimestampMS int64             `json:"timestamp_ms,omitempty"`
}

// PendingAdvance records when a message entered a consumer PEL during replay.
type PendingAdvance struct {
	Seq       int    `json:"seq"`
	Stream    string `json:"stream"`
	Group     string `json:"group"`
	Consumer  string `json:"consumer"`
	MessageID string `json:"message_id"`
	AckSeq    int    `json:"ack_seq"`
}

// PELMessage is one pending entry list item.
type PELMessage struct {
	ID            string `json:"id"`
	Consumer      string `json:"consumer"`
	DeliveryCount int    `json:"delivery_count"`
	IdleMS        int64  `json:"idle_ms"`
}

// ConsumerGroup state for one stream group.
type ConsumerGroup struct {
	Name         string                `json:"name"`
	LastID       string                `json:"last_id"`
	Pending      map[string]PELMessage `json:"pending"`
	ReclaimTotal int                   `json:"reclaim_total"`
}

// StreamState holds entries and groups for one stream key.
type StreamState struct {
	Name    string                    `json:"name"`
	Entries []StreamEntry             `json:"entries"`
	Groups  map[string]*ConsumerGroup `json:"groups"`
}

// StreamEntry is one stream message with id and fields.
type StreamEntry struct {
	ID     string            `json:"id"`
	Fields map[string]string `json:"fields"`
}

// StageFile is persisted replay state at /app/state/redis-stream-stage.json.
type StageFile struct {
	LastAppliedSeq int                        `json:"last_applied_seq"`
	Streams        map[string]*StreamState    `json:"streams"`
	PendingLog     []PendingAdvance           `json:"pending_log"`
}

// RollupGroup is export rollup for one consumer group.
type RollupGroup struct {
	Stream       string `json:"stream"`
	Group        string `json:"group"`
	PELDistinct  int    `json:"pel_distinct"`
	ReclaimTotal int    `json:"reclaim_total"`
}

// RollupFile is written to /app/output/stream-rollup.json.
type RollupFile struct {
	StreamLengths map[string]int  `json:"stream_lengths"`
	Groups        []RollupGroup `json:"groups"`
	ExportPass    int           `json:"export_pass"`
}
