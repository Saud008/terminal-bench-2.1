package model

type Config struct {
	StagingPath   string `json:"staging_path"`
	ParityDBPath  string `json:"parity_db_path"`
	ScenarioDir   string `json:"scenario_dir"`
}

type AsOfEntry struct {
	AsOfTS           int64  `json:"as_of_ts"`
	ActivePartition  string `json:"active_partition"`
}

type RawEvent struct {
	EntityBase  string  `json:"entity_base"`
	DeviceBase  string  `json:"device_base,omitempty"`
	SessionBase string  `json:"session_base,omitempty"`
	EventTS     int64   `json:"event_ts"`
	Feature     string  `json:"feature"`
	Value       float64 `json:"value"`
	Source      string  `json:"source"`
	Partition   string  `json:"partition"`
	Seq         int     `json:"seq"`
}

type ScenarioFile struct {
	ScenarioID   string      `json:"scenario_id"`
	EntityKeys   []string    `json:"entity_keys"`
	TTLSeconds   int64       `json:"ttl_seconds"`
	Partitions   []string    `json:"partitions"`
	AsOfEntries  []AsOfEntry `json:"as_of_entries"`
	Events       []RawEvent  `json:"events"`
}

type MaterializedEvent struct {
	EntityID  string  `json:"entity_id"`
	DeviceID  string  `json:"device_id,omitempty"`
	SessionID string  `json:"session_id,omitempty"`
	EventTS   int64   `json:"event_ts"`
	Feature   string  `json:"feature"`
	Value     float64 `json:"value"`
	Source    string  `json:"source"`
	Partition string  `json:"partition"`
	Seq       int     `json:"seq"`
}

type StagingSnapshot struct {
	IngestSeq   int64               `json:"ingest_seq"`
	Seed        string              `json:"seed"`
	Scenario    string              `json:"scenario"`
	EntityKeys  []string            `json:"entity_keys"`
	TTLSeconds  int64               `json:"ttl_seconds"`
	Partitions  []string            `json:"partitions"`
	AsOfEntries []AsOfEntry         `json:"as_of_entries"`
	Events      []MaterializedEvent `json:"events"`
}

type ParityRow struct {
	EntityID      string
	Feature       string
	AsOfTS        int64
	OfflineValue  *float64
	OnlineValue   *float64
	MatchOK       bool
	Reason        string
}

type RunSummary struct {
	MismatchCount        int
	TTLFilteredCount     int
	DuplicateTSResolved  int
	AsOfTSList           []int64
}

type ReportExport struct {
	Seed        string     `json:"seed"`
	Scenario    string     `json:"scenario"`
	RunID       int64      `json:"run_id"`
	ParityOK    bool       `json:"parity_ok"`
	Summary     ReportSum  `json:"summary"`
	AuditDigest string     `json:"audit_digest"`
}

type ReportSum struct {
	MismatchCount       int     `json:"mismatch_count"`
	TTLFilteredCount    int     `json:"ttl_filtered_count"`
	DuplicateTSResolved int     `json:"duplicate_ts_resolved"`
	AsOfTS              []int64 `json:"as_of_ts"`
}
