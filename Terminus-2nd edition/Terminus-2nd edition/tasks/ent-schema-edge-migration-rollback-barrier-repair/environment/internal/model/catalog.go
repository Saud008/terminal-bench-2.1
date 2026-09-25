package model

import (
	"encoding/json"
	"os"
)

type Catalog struct {
	SchemaVersion int               `json:"schema_version"`
	TargetVersion int               `json:"target_version"`
	EdgeName      string            `json:"edge_name"`
	CodegenSeed   string            `json:"codegen_seed"`
	SQL           map[string]string `json:"sql"`
}

type ReportEvent struct {
	Phase string `json:"phase"`
	Seq   int    `json:"seq"`
}

type Report struct {
	SchemaVersion int           `json:"schema_version"`
	CodegenHash   string        `json:"codegen_hash"`
	SnapshotSeq   int           `json:"snapshot_seq"`
	Events        []ReportEvent `json:"events"`
	Counts        ReportCounts  `json:"counts"`
	Seed          string        `json:"seed,omitempty"`
	Direction     string        `json:"direction,omitempty"`
}

type ReportCounts struct {
	Posts   int `json:"posts"`
	Orphans int `json:"orphans"`
}

func LoadCatalog(path string) (*Catalog, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var cat Catalog
	if err := json.Unmarshal(data, &cat); err != nil {
		return nil, err
	}
	return &cat, nil
}
