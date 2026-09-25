package types

// StageFile is the normalized ingest staging artifact.
type StageFile struct {
	Fragments []Fragment `json:"fragments"`
}

// Fragment is one parsed HCL fragment on disk.
type Fragment struct {
	Source         string                 `json:"source"`
	Order          int                    `json:"order"`
	BlockType      string                 `json:"block_type"`
	Labels         []string               `json:"labels"`
	Attributes     map[string]interface{} `json:"attributes"`
	Dynamics       []DynamicBlock         `json:"dynamics"`
	MergeOverrides map[string]interface{} `json:"merge_overrides"`
}

// DynamicBlock describes a dynamic block template before expansion.
type DynamicBlock struct {
	Name     string            `json:"name"`
	Values   []string          `json:"values"`
	Template map[string]string `json:"template"`
}

// MergedBlock is the export-ready merged representation.
type MergedBlock struct {
	BlockType  string                   `json:"block_type"`
	Labels     []string                 `json:"labels"`
	Attributes map[string]interface{}   `json:"attributes"`
	Expanded   []map[string]interface{} `json:"expanded_dynamics,omitempty"`
}

// NormalizedExport is the JSON intermediate used for checksum.
type NormalizedExport struct {
	Blocks []MergedBlock `json:"blocks"`
}
