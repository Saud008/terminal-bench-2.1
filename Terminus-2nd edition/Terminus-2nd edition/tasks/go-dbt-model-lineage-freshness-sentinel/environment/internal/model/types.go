package model

type Config struct {
	StagingPath     string `json:"staging_path"`
	SentinelDBPath  string `json:"sentinel_db_path"`
	BundleDir         string `json:"bundle_dir"`
}

type ModelNode struct {
	UniqueID     string   `json:"unique_id"`
	DependsOn    []string `json:"depends_on"`
	Enabled      bool     `json:"enabled"`
	LastBuiltAt  string   `json:"last_built_at"`
}

type SourceNode struct {
	UniqueID           string `json:"unique_id"`
	LoadedAt           string `json:"loaded_at"`
	WarnAfterMinutes   int    `json:"warn_after_minutes"`
	ErrorAfterMinutes  int    `json:"error_after_minutes"`
}

type ExposureNode struct {
	UniqueID  string   `json:"unique_id"`
	DependsOn []string `json:"depends_on"`
}

type ManifestBundle struct {
	PackName     string         `json:"bundle_name"`
	GeneratedAt  string         `json:"generated_at"`
	EvaluatedAt  string         `json:"evaluated_at"`
	Models       []ModelNode    `json:"models"`
	Sources      []SourceNode   `json:"sources"`
	Exposures     []ExposureNode `json:"exposures"`
}

type StagingSnapshot struct {
	IngestSeq    int64        `json:"ingest_seq"`
	Seed         string       `json:"seed"`
	Pack         string       `json:"bundle"`
	GeneratedAt  string       `json:"generated_at"`
	EvaluatedAt  string       `json:"evaluated_at"`
	Models       []ModelNode  `json:"models"`
	Sources      []SourceNode `json:"sources"`
	Exposures     []ExposureNode `json:"exposures"`
}

type FreshnessStatus struct {
	UniqueID string `json:"unique_id"`
	Minutes   int    `json:"minutes_elapsed"`
	Status    string `json:"status"`
}

type ScanSummary struct {
	EnabledModelCount int  `json:"enabled_model_count"`
	StaleSourceCount  int  `json:"stale_source_count"`
	ExposureCount     int  `json:"exposure_count"`
	DisabledRefOK     bool `json:"disabled_ref_ok"`
}

type AlertRow struct {
	AlertCode string `json:"alert_code"`
	Severity  string `json:"severity"`
	SubjectID string `json:"subject_id"`
	Message   string `json:"message"`
}

type AlertReport struct {
	Seed         string       `json:"seed"`
	Pack         string       `json:"bundle"`
	ScanID       int64        `json:"scan_id"`
	ModelOrder   []string     `json:"model_order"`
	Freshness    []FreshnessStatus `json:"freshness"`
	ExposureRefs map[string][]string `json:"exposure_refs"`
	Alerts       []AlertRow   `json:"alerts"`
	Summary       ScanSummary  `json:"summary"`
	AuditDigest   string       `json:"audit_digest"`
}
