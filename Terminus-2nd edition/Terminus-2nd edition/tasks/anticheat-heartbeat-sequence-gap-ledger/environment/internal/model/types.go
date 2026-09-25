package model

type BindRequest struct {
	Token     string `json:"token"`
	SessionID string `json:"session_id"`
	ClientMs  int64  `json:"client_ms"`
}

type Beat struct {
	Seq      uint32 `json:"seq"`
	ClientMs int64  `json:"client_ms"`
}

type BatchRequest struct {
	Token            string `json:"token"`
	SessionID        string `json:"session_id"`
	AdmissionTicket  string `json:"admission_ticket"`
	Beats            []Beat `json:"beats"`
}

type ExportRequest struct {
	Token     string `json:"token"`
	SessionID string `json:"session_id"`
}

type ExportReport struct {
	Token               string `json:"token"`
	SessionID           string `json:"session_id"`
	LastSeq             uint32 `json:"last_seq"`
	BreachesOpened      int    `json:"breaches_opened"`
	BreachesClosed      int    `json:"breaches_closed"`
	MissingSpanTotal    int    `json:"missing_span_total"`
	RepairEvents        int    `json:"repair_events"`
	ActiveBanSeals      int    `json:"active_ban_seals"`
	SkewRejections      int    `json:"skew_rejections"`
	DuplicateRejections int    `json:"duplicate_rejections"`
	TicketRejections    int    `json:"ticket_rejections"`
	WitnessSeq          int    `json:"witness_seq"`
	WitnessHead         string `json:"witness_head"`
	AuditDigest         string `json:"audit_digest"`
}

type SessionState struct {
	Token           string
	SessionID       string
	LastSeq         uint32
	HasLastSeq      bool
	AnchorClient    int64
	AnchorMono      int64
	AdmissionTicket string
	SkewRejects     int
	DupRejects      int
	TicketRejects   int
}

type BreachSeal struct {
	ID           int64
	FromSeq      uint32
	ToSeq        uint32
	MissingSpan  uint32
	OpenedMonoMs int64
	Closed       bool
}
