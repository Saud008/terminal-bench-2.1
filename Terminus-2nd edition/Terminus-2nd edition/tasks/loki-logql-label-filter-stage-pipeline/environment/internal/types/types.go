package types

// LogLine is one JSONL log batch row.
type LogLine struct {
	LineID int               `json:"line_id"`
	Labels map[string]string `json:"labels"`
	Line   string            `json:"line"`
}

// QueryStage is one parsed LogQL pipeline stage.
type QueryStage struct {
	Kind     string            `json:"kind"`
	Selector map[string]string `json:"selector,omitempty"`
	Template string            `json:"template,omitempty"`
	Field    string            `json:"field,omitempty"`
	GroupBy  []string          `json:"group_by,omitempty"`
}

// QueryAST is the parsed query written to stage.
type QueryAST struct {
	Raw       string       `json:"raw"`
	Canonical string       `json:"canonical"`
	Stages    []QueryStage `json:"stages"`
}

// VectorSample is one evaluated instant vector row.
type VectorSample struct {
	Labels   map[string]string `json:"labels"`
	Value    float64           `json:"value"`
	Checksum uint64            `json:"checksum"`
}

// StageFile is persisted at /app/state/logql-stage.json.
type StageFile struct {
	Query              QueryAST       `json:"query"`
	LabelInsertOrder   []string       `json:"label_insert_order"`
	Vectors            []VectorSample `json:"vectors"`
	SelectedGroupLabels []string      `json:"selected_group_labels"`
}

// FingerprintFile is written to /app/output/query-fingerprint.json.
type FingerprintFile struct {
	Fingerprint     string   `json:"fingerprint"`
	SelectedLabels  []string `json:"selected_labels"`
	VectorChecksum  uint64   `json:"vector_checksum"`
	ExportPass      int      `json:"export_pass"`
}

// WorkingRow is an in-flight pipeline row during eval.
type WorkingRow struct {
	Labels   map[string]string
	Fields   map[string]string
	Value    float64
	Filtered bool
}
