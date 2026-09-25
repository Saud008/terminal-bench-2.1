package model

type ScenarioFile struct {
	RunDir string `json:"run_dir"`
}

type RunMeta struct {
	RunID     string `json:"run_id"`
	SessionID string `json:"session_id"`
	Resumed   bool   `json:"resumed"`
}

type TaskRecord struct {
	TaskID          string            `json:"task_id"`
	Hash            string            `json:"hash"`
	ParentHashes    []string          `json:"parent_hashes"`
	Container       string            `json:"container"`
	ContainerDigest string            `json:"container_digest"`
	InputGlobs      []string          `json:"input_globs"`
	ExpansionHash   string            `json:"expansion_hash"`
	LineageDigest   string            `json:"lineage_digest,omitempty"`
	Attempt         int               `json:"attempt"`
	Cached          bool              `json:"cached"`
	ExitStatus      int               `json:"exit_status"`
	OutputHashes    map[string]string `json:"output_hashes"`
	PriorDigest     string            `json:"prior_digest,omitempty"`
	PriorExitStatus *int              `json:"prior_exit_status,omitempty"`
}

type CacheMarker struct {
	SessionID     string `json:"session_id"`
	StoredDigest  string `json:"stored_digest"`
	TaskID        string `json:"task_id"`
}

type StagedTask struct {
	TaskID          string   `json:"task_id"`
	Hash            string   `json:"hash"`
	LineageDigest   string   `json:"lineage_digest"`
	ParentHashes    []string `json:"parent_hashes"`
	ContainerDigest string   `json:"container_digest"`
	ExpansionHash   string   `json:"expansion_hash"`
	ComputedExpand  string   `json:"computed_expansion_hash"`
	Attempt         int      `json:"attempt"`
	Cached          bool     `json:"cached"`
	ExitStatus      int      `json:"exit_status"`
	PriorDigest     string   `json:"prior_digest,omitempty"`
	PriorExitStatus *int     `json:"prior_exit_status,omitempty"`
	CacheSessionID  string   `json:"cache_session_id,omitempty"`
}

type StageSnapshot struct {
	Engine      string       `json:"engine"`
	Scenario    string       `json:"scenario"`
	RunID       string       `json:"run_id"`
	SessionID   string       `json:"session_id"`
	Resumed     bool         `json:"resumed"`
	TaskCount   int          `json:"task_count"`
	Tasks       []StagedTask `json:"tasks"`
	AuditGen    int          `json:"audit_generation"`
	RunDigest   string       `json:"run_digest"`
}

type UnsafeFinding struct {
	TaskID string `json:"task_id"`
	Rule   string `json:"rule"`
	Detail string `json:"detail"`
}

type AuditFindings struct {
	Scenario     string          `json:"scenario"`
	UnsafeCount  int             `json:"unsafe_count"`
	Findings     []UnsafeFinding `json:"findings"`
	AuditDigest  string          `json:"audit_digest"`
}

type GenerationFile struct {
	AuditGeneration int `json:"audit_generation"`
}

type ExportReport struct {
	Scenario         string          `json:"scenario"`
	AuditGeneration  int             `json:"audit_generation"`
	UnsafeCount      int             `json:"unsafe_count"`
	Findings         []UnsafeFinding `json:"findings"`
	AuditDigest      string          `json:"audit_digest"`
	SafeForResume    bool            `json:"safe_for_resume"`
}
