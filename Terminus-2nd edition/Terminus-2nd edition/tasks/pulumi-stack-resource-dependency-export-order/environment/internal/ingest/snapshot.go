package ingest

import (
	"github.com/terminus/pulumi-dep-export/internal/model"
	"github.com/terminus/pulumi-dep-export/internal/parse"
)

// LoadSnapshot ingests stack snapshot JSON from disk.
func LoadSnapshot(path string) (model.Snapshot, error) {
	return parse.LoadSnapshot(path)
}
