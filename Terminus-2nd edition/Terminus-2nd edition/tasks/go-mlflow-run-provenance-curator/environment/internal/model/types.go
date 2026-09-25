package model

type Config struct {
	StagingPath      string `json:"staging_path"`
	ProvenanceDBPath string `json:"provenance_db_path"`
	ScenarioDir      string `json:"scenario_dir"`
}

type MetricPoint struct {
	Key   string  `json:"key"`
	Step  int     `json:"step"`
	Value float64 `json:"value"`
	Epoch int     `json:"epoch"`
}

type Artifact struct {
	RelPath string `json:"rel_path"`
	Content string `json:"content"`
}

type DatasetPin struct {
	Name         string `json:"name"`
	VersionHash  string `json:"version_hash"`
}

type DatasetManifest struct {
	VersionHash string `json:"version_hash"`
	RowCount    int    `json:"row_count"`
}

type RunRecord struct {
	RunID       string            `json:"run_id"`
	ParentRunID string            `json:"parent_run_id"`
	Params      map[string]string `json:"params"`
	Metrics     []MetricPoint     `json:"metrics"`
	Artifacts   []Artifact        `json:"artifacts"`
	DatasetPins []DatasetPin      `json:"dataset_pins"`
}

type ScenarioFile struct {
	ScenarioName     string                       `json:"scenario_name"`
	ExperimentID     string                       `json:"experiment_id"`
	FocusRunID       string                       `json:"focus_run_id"`
	DatasetManifests map[string]DatasetManifest   `json:"dataset_manifests"`
	Runs             []RunRecord                  `json:"runs"`
}

type ScopedRun struct {
	RunID       string            `json:"run_id"`
	ParentRunID string            `json:"parent_run_id"`
	Params      map[string]string `json:"params"`
	Metrics     []MetricPoint     `json:"metrics"`
	Artifacts   []Artifact        `json:"artifacts"`
	DatasetPins []DatasetPin      `json:"dataset_pins"`
}

type StagingSnapshot struct {
	IngestSeq        int64                        `json:"ingest_seq"`
	Seed             string                       `json:"seed"`
	Scenario         string                       `json:"scenario"`
	FocusRunID       string                       `json:"focus_run_id"`
	ExperimentID     string                       `json:"experiment_id"`
	DatasetManifests map[string]DatasetManifest   `json:"dataset_manifests"`
	Runs             []ScopedRun                  `json:"runs"`
}

type ArtifactDigest struct {
	RelPath string `json:"rel_path"`
	Digest  string `json:"digest"`
}

type DatasetBinding struct {
	Name         string `json:"name"`
	VersionHash  string `json:"version_hash"`
	RowCount     int    `json:"row_count"`
	BindOK       bool   `json:"bind_ok"`
}

type SummaryBlock struct {
	BindingOK        bool `json:"binding_ok"`
	EpochMonotonicOK bool `json:"epoch_monotonic_ok"`
	LineageDepth     int  `json:"lineage_depth"`
	ArtifactCount    int  `json:"artifact_count"`
}

type ProvenanceReport struct {
	Seed             string           `json:"seed"`
	Scenario         string           `json:"scenario"`
	FocusRunID       string           `json:"focus_run_id"`
	RunID            int64            `json:"run_id"`
	LineageChain     []string         `json:"lineage_chain"`
	ArtifactDigests  []ArtifactDigest `json:"artifact_digests"`
	MetricEpochs     []MetricPoint    `json:"metric_epochs"`
	DatasetBindings  []DatasetBinding `json:"dataset_bindings"`
	Summary          SummaryBlock     `json:"summary"`
	AuditDigest      string           `json:"audit_digest"`
}
