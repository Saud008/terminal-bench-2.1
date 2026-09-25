package types

// JournalEntry is one JSONL migration journal line.
type JournalEntry struct {
	Seq       int    `json:"seq"`
	Version   int    `json:"version"`
	Direction string `json:"direction"`
	SQL       string `json:"sql"`
}

// StageFile is persisted at /app/state/migrate-stage.json.
type StageFile struct {
	LastSeq              int  `json:"last_seq"`
	Version              int  `json:"version"`
	Dirty                bool `json:"dirty"`
	FailedDownRollbacks  int  `json:"failed_down_rollbacks"`
	AppliedSteps         int  `json:"applied_steps"`
}

// VersionLedger is written to /app/output/version-ledger.json.
type VersionLedger struct {
	MaxVersion          int  `json:"max_version"`
	Dirty               bool `json:"dirty"`
	FailedDownRollbacks int  `json:"failed_down_rollbacks"`
	StageVersion        int  `json:"stage_version"`
	ExportPass          int  `json:"export_pass"`
}
