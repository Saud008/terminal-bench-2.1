package model

type Config struct {
	StagingPath              string `json:"staging_path"`
	StagingSeqPath           string `json:"staging_seq_path"`
	CorrelateGenerationPath  string `json:"correlate_generation_path"`
	IncidentBundlePath       string `json:"incident_bundle_path"`
	RejectedEventsPath       string `json:"rejected_events_path"`
	DefaultSeverityTier      string `json:"default_severity_tier"`
}

type RuleRevision struct {
	RuleName    string `json:"rule_name"`
	RevisionID  string `json:"revision_id"`
	EffectiveMs int64  `json:"effective_ms"`
	RetiredMs   int64  `json:"retired_ms"`
}

type SuppressionTicket struct {
	TicketID      string `json:"ticket_id"`
	RuleName      string `json:"rule_name"`
	AssetID       string `json:"asset_id"`
	SampleSHA256  string `json:"sample_sha256"`
	StartMs       int64  `json:"start_ms"`
	EndMs         int64  `json:"end_ms"`
}

type AssetCriticality struct {
	AssetID       string `json:"asset_id"`
	Tier          string `json:"tier"`
	EscalationMs  int64  `json:"escalation_ms"`
}

type QuarantineState struct {
	AssetID      string `json:"asset_id"`
	SampleSHA256 string `json:"sample_sha256"`
	State        string `json:"state"`
	EnteredMs    int64  `json:"entered_ms"`
	ClearedMs    int64  `json:"cleared_ms"`
}

type Policy struct {
	TenantID           string              `json:"tenant_id"`
	RuleRevisions      []RuleRevision      `json:"rule_revisions"`
	SuppressionTickets []SuppressionTicket `json:"suppression_tickets"`
	AssetCriticality   []AssetCriticality  `json:"asset_criticality"`
	QuarantineStates   []QuarantineState   `json:"quarantine_states"`
}

type ScanEvent struct {
	EventID       string `json:"event_id"`
	AssetID       string `json:"asset_id"`
	SampleSHA256  string `json:"sample_sha256"`
	RuleName      string `json:"rule_name"`
	RuleRevision  string `json:"rule_revision"`
	DetectedMs    int64  `json:"detected_ms"`
	ScannerHost   string `json:"scanner_host"`
}

type EventStaging struct {
	Events            []ScanEvent `json:"events"`
	EventsDigest      string      `json:"events_digest"`
	PolicySHA256      string      `json:"policy_sha256"`
	PolicyPath        string      `json:"policy_path"`
	StagingGeneration int         `json:"staging_generation"`
}

type IncidentRow struct {
	EventID           string `json:"event_id"`
	AssetID           string `json:"asset_id"`
	SampleSHA256      string `json:"sample_sha256"`
	RuleName          string `json:"rule_name"`
	RuleRevision      string `json:"rule_revision"`
	DetectedMs        int64  `json:"detected_ms"`
	SeverityTier      string `json:"severity_tier"`
	Actionable        bool   `json:"actionable"`
	Suppressed        bool   `json:"suppressed"`
	SuppressionReason string `json:"suppression_reason"`
}

type CorrelateGeneration struct {
	Generation        int           `json:"generation"`
	StagingGeneration int           `json:"staging_generation"`
	PolicySHA256      string        `json:"policy_sha256"`
	Incidents         []IncidentRow `json:"incidents"`
}

type IncidentBundle struct {
	CorrelateGeneration int           `json:"correlate_generation"`
	StagingGeneration   int           `json:"staging_generation"`
	Incidents           []IncidentRow `json:"incidents"`
	BundleDigest        string        `json:"bundle_digest"`
}

type RejectedEvent struct {
	EventID string `json:"event_id"`
	Reason  string `json:"reason"`
}
