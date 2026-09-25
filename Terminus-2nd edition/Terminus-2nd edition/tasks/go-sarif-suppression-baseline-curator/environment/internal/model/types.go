package model

type Config struct {
	StagingPath           string `json:"staging_path"`
	StagingSeqPath        string `json:"staging_seq_path"`
	BaselineRevisionPath  string `json:"baseline_revision_path"`
	FindingDeltaPath      string `json:"finding_delta_path"`
	RejectedFindingsPath  string `json:"rejected_findings_path"`
}

type Finding struct {
	FindingID   string `json:"finding_id"`
	Tool        string `json:"tool"`
	RuleID      string `json:"rule_id"`
	Level       string `json:"level"`
	Message     string `json:"message,omitempty"`
	URI         string `json:"uri"`
	StartLine   int    `json:"start_line"`
	StartColumn int    `json:"start_column"`
	Fingerprint string `json:"fingerprint"`
	ObservedAt  string `json:"observed_at"`
}

type FindingStaging struct {
	Findings       []Finding `json:"findings"`
	FindingsDigest string    `json:"findings_digest"`
	SarifSHA256    string    `json:"sarif_sha256"`
	PolicySHA256   string    `json:"policy_sha256"`
	PolicyPath     string    `json:"policy_path"`
	RemapPath      string    `json:"remap_path"`
	BaselinePath   string    `json:"baseline_path"`
	ScanRevision   int       `json:"scan_revision"`
}

type StagingSeq struct {
	ScanRevision int `json:"scan_revision"`
}

type BaselineFinding struct {
	FindingID   string `json:"finding_id"`
	Tool        string `json:"tool"`
	RuleID      string `json:"rule_id"`
	Level       string `json:"level"`
	URI         string `json:"uri"`
	StartLine   int    `json:"start_line"`
	StartColumn int    `json:"start_column"`
	Fingerprint string `json:"fingerprint"`
	ObservedAt  string `json:"observed_at"`
}

type BaselineSnapshot struct {
	Findings []BaselineFinding `json:"findings"`
}

type CuratedEntry struct {
	FindingID      string `json:"finding_id"`
	RuleKey        string `json:"rule_key"`
	Level          string `json:"level"`
	URI            string `json:"uri"`
	StartLine      int    `json:"start_line"`
	StartColumn    int    `json:"start_column"`
	Fingerprint    string `json:"fingerprint"`
	PhysicalFP     string `json:"physical_fingerprint"`
	Suppressed     bool   `json:"suppressed"`
	DriftFromBase  bool   `json:"drift_from_baseline"`
}

type BaselineRevision struct {
	ReconcileRevision int            `json:"reconcile_revision"`
	ScanRevision      int            `json:"scan_revision"`
	SarifSHA256       string         `json:"sarif_sha256"`
	PolicySHA256      string         `json:"policy_sha256"`
	Entries           []CuratedEntry `json:"entries"`
}

type RejectedFinding struct {
	FindingID string `json:"finding_id"`
	Reason    string `json:"reason"`
}

type DeltaRow struct {
	FindingID   string `json:"finding_id"`
	RuleKey     string `json:"rule_key"`
	URI         string `json:"uri"`
	StartLine   int    `json:"start_line"`
	Category    string `json:"category"`
	Fingerprint string `json:"fingerprint,omitempty"`
}

type FindingDelta struct {
	ReconcileRevision int        `json:"reconcile_revision"`
	ScanRevision      int        `json:"scan_revision"`
	Rows              []DeltaRow `json:"rows"`
	DeltaDigest       string     `json:"delta_digest"`
}

type SuppressRule struct {
	RuleKey   string `json:"rule_key"`
	URIPrefix string `json:"uri_prefix"`
	Until     string `json:"until"`
}

type Policy struct {
	Timezone      string            `json:"timezone"`
	RulesCatalog  RulesCatalog      `json:"rules_catalog"`
	SuppressUntil []SuppressRule    `json:"suppress_until"`
}

type RulesCatalog struct {
	Aliases   map[string]string `json:"aliases"`
	Canonical map[string]string `json:"canonical"`
}

type RemapConfig struct {
	PrefixStrip []string          `json:"prefix_strip"`
	Rewrite     map[string]string `json:"rewrite"`
}

type SeverityRank int

const (
	SeverityNone SeverityRank = iota
	SeverityNote
	SeverityWarning
	SeverityError
)

func LevelRank(level string) SeverityRank {
	switch level {
	case "error":
		return SeverityError
	case "warning":
		return SeverityWarning
	case "note":
		return SeverityNote
	default:
		return SeverityNone
	}
}
