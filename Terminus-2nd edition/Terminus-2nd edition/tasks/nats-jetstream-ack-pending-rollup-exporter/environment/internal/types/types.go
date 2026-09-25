package types

// JournalEvent is one JSONL offline JetStream journal line.
type JournalEvent struct {
	Seq            int    `json:"seq"`
	Op             string `json:"op"`
	Stream         string `json:"stream,omitempty"`
	Consumer       string `json:"consumer,omitempty"`
	Subject        string `json:"subject,omitempty"`
	FilterSubject  string `json:"filter_subject,omitempty"`
	StreamSeq      uint64 `json:"stream_seq,omitempty"`
	DeliveryNum    int    `json:"delivery_num,omitempty"`
	MaxDeliver     int    `json:"max_deliver,omitempty"`
	RequireAckSync bool   `json:"require_ack_sync,omitempty"`
	AckSync        bool   `json:"ack_sync,omitempty"`
	DelayMS        int64  `json:"delay_ms,omitempty"`
	Tick           int64  `json:"tick,omitempty"`
	TimestampMS    int64  `json:"timestamp_ms,omitempty"`
}

// StreamMessage is one published stream message.
type StreamMessage struct {
	StreamSeq uint64 `json:"stream_seq"`
	Subject   string `json:"subject"`
}

// PendingEntry is one ack-pending item for a consumer.
type PendingEntry struct {
	StreamSeq         uint64 `json:"stream_seq"`
	DeliveryNum       int    `json:"delivery_num"`
	RedeliveryDueTick int64  `json:"redelivery_due_tick,omitempty"`
}

// ConsumerState tracks one durable consumer on a stream.
type ConsumerState struct {
	Name           string                  `json:"name"`
	FilterSubject  string                  `json:"filter_subject"`
	MaxDeliver     int                     `json:"max_deliver"`
	RequireAckSync bool                    `json:"require_ack_sync"`
	TickLedger     int64                   `json:"tick_ledger"`
	HighWaterSeq   uint64                  `json:"high_water_seq"`
	Pending        map[uint64]PendingEntry `json:"pending"`
}

// StreamState holds messages and consumers for one stream.
type StreamState struct {
	Name      string                    `json:"name"`
	Messages  []StreamMessage           `json:"messages"`
	MaxSeq    uint64                    `json:"max_seq"`
	Consumers map[string]*ConsumerState `json:"consumers"`
}

// StageFile is persisted at /app/state/nats-jetstream-stage.json.
type StageFile struct {
	LastAppliedSeq int                        `json:"last_applied_seq"`
	SubjectCatalog []string                   `json:"subject_catalog"`
	Streams        map[string]*StreamState    `json:"streams"`
}

// RollupConsumer is one consumer row in export output.
type RollupConsumer struct {
	Stream         string `json:"stream"`
	Consumer       string `json:"consumer"`
	PendingCount   int    `json:"pending_count"`
	HighWaterSeq   uint64 `json:"high_water_seq"`
	RedeliveryDue  int    `json:"redelivery_due"`
}

// RollupFile is written to /app/output/pending-rollup.json.
type RollupFile struct {
	Consumers  []RollupConsumer `json:"consumers"`
	ExportPass int              `json:"export_pass"`
}
