package model

type Event struct {
	Seq      int    `json:"seq"`
	Op       string `json:"op"`
	CID      string `json:"cid,omitempty"`
	AliasCID string `json:"alias_cid,omitempty"`
	Peer     string `json:"peer,omitempty"`
	Priority int    `json:"priority,omitempty"`
	Bytes    int    `json:"bytes,omitempty"`
	IdleMS   int    `json:"idle_ms,omitempty"`
	Wants    []Want `json:"wants,omitempty"`
}

type Want struct {
	CID      string `json:"cid"`
	Priority int    `json:"priority"`
}

type InFlight struct {
	Peer    string
	Bytes   int
	Started int
}

type PartialBlock struct {
	Peer  string
	Bytes int
}

type Delivery struct {
	CID      string `json:"cid"`
	Peer     string `json:"peer"`
	Bytes    int    `json:"bytes"`
	Priority int    `json:"priority"`
}

type Session struct {
	Name         string
	Wants        map[string]*WantEntry
	InFlight     map[string]*InFlight
	Partial      map[string]*PartialBlock
	Ledger       map[string]map[string]int
	Canceled     map[string]bool
	Delivered    []Delivery
	LastActivity int
	IdleLimitMS  int
}

type WantEntry struct {
	DisplayCID string
	Priority   int
	Canonical  string
}

type StagingSnapshot struct {
	SessionID      string     `json:"session_id"`
	WantsRemaining []WantSnap `json:"wants_remaining"`
	Delivered      []Delivery `json:"delivered"`
	LedgerTotals   []LedgerRow `json:"ledger_totals"`
	PartialBlocks  int        `json:"partial_blocks"`
	InFlightCount  int        `json:"in_flight_count"`
}

type WantSnap struct {
	CID      string `json:"cid"`
	Priority int    `json:"priority"`
}

type LedgerRow struct {
	Peer   string `json:"peer"`
	CID    string `json:"cid"`
	Credit int    `json:"credit"`
}

type ExportReport struct {
	ReportVersion  int         `json:"report_version"`
	SessionID      string      `json:"session_id"`
	WantsRemaining []WantSnap  `json:"wants_remaining"`
	Delivered      []Delivery  `json:"delivered"`
	LedgerTotals   []LedgerRow `json:"ledger_totals"`
	PartialBlocks  int         `json:"partial_blocks"`
	InFlightCount  int         `json:"in_flight_count"`
	DeliveryCount  int         `json:"delivery_count"`
}

type MetricsReport struct {
	ReportVersion int    `json:"report_version"`
	SessionID     string `json:"session_id"`
	QueueHeadCID  string `json:"queue_head_cid"`
	QueueHeadPri  int    `json:"queue_head_priority"`
	CancelMerged  bool   `json:"cancel_merged"`
}
