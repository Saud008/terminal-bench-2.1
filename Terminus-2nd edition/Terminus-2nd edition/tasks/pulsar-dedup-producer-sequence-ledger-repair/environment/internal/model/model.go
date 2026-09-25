package model

type Scenario struct {
	Tenant      string        `json:"tenant"`
	DedupWindow int           `json:"dedup_window"`
	Streams     []StreamMeta  `json:"streams"`
	Events      []PublishEvent `json:"events"`
}

type StreamMeta struct {
	Producer string `json:"producer"`
	Topic    string `json:"topic"`
	Epoch    int    `json:"epoch"`
}

type PublishEvent struct {
	Producer  string `json:"producer"`
	Topic     string `json:"topic"`
	Epoch     int    `json:"epoch"`
	Sequence  int64  `json:"sequence"`
	MsgID     string `json:"msg_id"`
	BatchID   string `json:"batch_id"`
	BrokerAck bool   `json:"broker_ack"`
}

type StreamStats struct {
	Epoch            int   `json:"epoch"`
	HighWater        int64 `json:"high_water"`
	BrokerAckedMax   int64 `json:"broker_acked_max"`
	DedupMiss        int   `json:"dedup_miss"`
	DuplicateReplay  int   `json:"duplicate_replay"`
	AcceptedCount    int   `json:"accepted_count"`
}

type Snapshot struct {
	Tenant           string                 `json:"tenant"`
	Streams          map[string]StreamStats `json:"streams"`
	StagingWritten   bool                   `json:"staging_written"`
	ExportBeforeAck  bool                   `json:"export_before_ack"`
}

type ExportReport struct {
	Tenant           string                 `json:"tenant"`
	Streams          map[string]StreamStats `json:"streams"`
	ExportBarrierOK  bool                   `json:"export_barrier_ok"`
}
