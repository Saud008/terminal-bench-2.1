package model

type Trace struct {
	TraceID   string      `json:"trace_id"`
	GatewayID string      `json:"gateway_id"`
	Events    []ViciEvent `json:"events"`
}

type ViciEvent struct {
	LogSeq        int      `json:"log_seq"`
	OffsetMS      int      `json:"offset_ms"`
	Type          string   `json:"type"`
	IkeUniqueID   int      `json:"ike_unique_id,omitempty"`
	ChildUniqueID int      `json:"child_unique_id,omitempty"`
	ReqID         int      `json:"req_id,omitempty"`
	SpiIn         uint64   `json:"spi_in,omitempty"`
	SpiOut        uint64   `json:"spi_out,omitempty"`
	LocalTS       []string `json:"local_ts,omitempty"`
	RemoteTS      []string `json:"remote_ts,omitempty"`
}

type EventVerdict struct {
	EventIndex    int    `json:"event_index"`
	LogSeq        int    `json:"log_seq"`
	OffsetMS      int    `json:"offset_ms"`
	EventType     string `json:"event_type"`
	OrderOK       bool   `json:"order_ok"`
	SelectorsOK   bool   `json:"selectors_ok"`
	UidOK         bool   `json:"uid_ok"`
	SeqMonotonic  bool   `json:"seq_monotonic"`
	Accepted      bool   `json:"accepted"`
	RejectReason  string `json:"reject_reason,omitempty"`
	ActiveSpiOut  uint64 `json:"active_spi_out"`
}

type RekeySnapshot struct {
	SnapshotVersion     int            `json:"snapshot_version"`
	TableSuffix         string         `json:"table_suffix"`
	TraceID             string         `json:"trace_id"`
	InitiatorOffset     int            `json:"initiator_offset"`
	Verdicts            []EventVerdict `json:"verdicts"`
	ActiveSpiOut        uint64         `json:"active_spi_out"`
	RekeyViolationCount int            `json:"rekey_violation_count"`
}

type RekeyReport struct {
	ReportVersion       int            `json:"report_version"`
	TableSuffix         string         `json:"table_suffix"`
	TraceID             string         `json:"trace_id"`
	InitiatorOffset     int            `json:"initiator_offset"`
	Verdicts            []EventVerdict `json:"verdicts"`
	ActiveSpiOut        uint64         `json:"active_spi_out"`
	RekeyViolationCount int            `json:"rekey_violation_count"`
	ExportSource        string         `json:"export_source"`
}

type ChildState struct {
	UniqueID  int
	SpiIn     uint64
	SpiOut    uint64
	LocalTS   []string
	RemoteTS  []string
	Deleted   bool
	Active    bool
}
