package model

type StreamRow struct {
	Session     string `json:"session"`
	MsgSeq      int    `json:"msg_seq"`
	SendingTime string `json:"sending_time"`
	FixBody     string `json:"fix_body"`
}

type StageEvent struct {
	Session        string  `json:"session"`
	MsgSeq         int     `json:"msg_seq"`
	SendingTime    string  `json:"sending_time"`
	ResetSeq       bool    `json:"reset_seq"`
	ClOrdID        string  `json:"cl_ord_id"`
	OrigClOrdID    string  `json:"orig_cl_ord_id"`
	ExecID         string  `json:"exec_id"`
	ExecTransType  string  `json:"exec_trans_type"`
	ExecType       string  `json:"exec_type"`
	Symbol         string  `json:"symbol"`
	Side           string  `json:"side"`
	LastQty        float64 `json:"last_qty"`
	LastPx         float64 `json:"last_px"`
	StreamFile     string  `json:"stream_file"`
}

type StageSnapshot struct {
	Engine       string       `json:"engine"`
	Scenario     string       `json:"scenario"`
	EventCount   int          `json:"event_count"`
	Events       []StageEvent `json:"events"`
	ReplayGen    int64        `json:"replay_generation"`
	StreamDigest string       `json:"stream_digest"`
}

type LedgerRow struct {
	ExecID        string
	Session       string
	ClOrdID       string
	OrigClOrdID   string
	ExecTransType string
	ExecType      string
	Symbol        string
	SignedQty     int64
	Active        bool
	SendingTime   string
	StreamFile    string
}

type ScenarioManifest struct {
	ScenarioID string   `json:"scenario_id"`
	Streams    []string `json:"streams"`
}

type ComplianceExport struct {
	Scenario         string           `json:"scenario"`
	ReplayGeneration int64            `json:"replay_generation"`
	NetPositions     map[string]int64 `json:"net_positions"`
	BustCount        int              `json:"bust_count"`
	CorrectionCount  int              `json:"correction_count"`
	CancelCount      int              `json:"cancel_count"`
	ActiveExecIDs    []string         `json:"active_exec_ids"`
	AuditDigest      string           `json:"audit_digest"`
}

type GenerationFile struct {
	ReplayGeneration int64 `json:"replay_generation"`
}

type ScenarioFile struct {
	ScenarioID string   `json:"scenario_id"`
	Streams    []string `json:"streams"`
}

type SeedsFile struct {
	Seeds []string `json:"seeds"`
}
