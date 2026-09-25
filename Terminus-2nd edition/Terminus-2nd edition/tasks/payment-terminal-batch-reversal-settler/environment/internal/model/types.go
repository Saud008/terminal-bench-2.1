package model

type Transcript struct {
	BatchID       string `json:"batch_id"`
	TerminalKeyID string `json:"terminal_key_id"`
	MerchantID    string `json:"merchant_id"`
	TerminalID    string `json:"terminal_id"`
	TxnID         string `json:"txn_id"`
	AuthCode      string `json:"auth_code"`
	AmountCents   int64  `json:"amount_cents"`
	TxnType       string `json:"txn_type"`
	LinksSaleID   string `json:"links_sale_id"`
	EventMS       int64  `json:"event_ms"`
}

type BatchScenario struct {
	Scenario       string       `json:"scenario"`
	BatchID        string       `json:"batch_id"`
	TerminalKeyID  string       `json:"terminal_key_id"`
	CutoffEventMS  int64        `json:"cutoff_event_ms"`
	TerminalKeyHex string       `json:"terminal_key_hex"`
	Transcripts    []Transcript `json:"transcripts"`
}

type NormalizedTxn struct {
	Transcript
	AuthCodeNorm string
	State        string
}

type JournalLine struct {
	Seq               int    `json:"seq"`
	TxnID             string `json:"txn_id"`
	TerminalID        string `json:"terminal_id"`
	MerchantID        string `json:"merchant_id"`
	TxnType           string `json:"txn_type"`
	AmountCents       int64  `json:"amount_cents"`
	State             string `json:"state"`
	NormalizedDigest  string `json:"normalized_digest"`
}

type JournalFile struct {
	Engine        string `json:"engine"`
	Scenario      string `json:"scenario"`
	BatchID       string `json:"batch_id"`
	JournalDigest string `json:"journal_digest"`
	LineCount     int    `json:"line_count"`
}

type SettlementBundle struct {
	Engine         string `json:"engine"`
	Scenario       string `json:"scenario"`
	BatchID        string `json:"batch_id"`
	TerminalKeyID  string `json:"terminal_key_id"`
	JournalDigest  string `json:"journal_digest"`
	NetAmountCents int64  `json:"net_amount_cents"`
	SettledCount   int    `json:"settled_count"`
	BundleVersion  int    `json:"bundle_version"`
}
