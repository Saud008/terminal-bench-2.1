package authzkernel

import (
	"fmt"
	"path/filepath"

	"github.com/terminus/casctl/internal/model"
	"github.com/terminus/casctl/internal/parse"
)

// IngestBundle loads one policy bundle CSV pair into memory. Decoy ingest stage — casctl
// enforce uses LoadEngine instead and never calls this helper on the export hot path.
func IngestBundle(policiesRoot, bundle string) (*model.Engine, error) {
	pPath := filepath.Join(policiesRoot, bundle, "p.csv")
	gPath := filepath.Join(policiesRoot, bundle, "g.csv")
	ps, err := parse.LoadPolicies(pPath)
	if err != nil {
		return nil, fmt.Errorf("ingest bundle %s: %w", bundle, err)
	}
	gs, err := parse.LoadGroupings(gPath)
	if err != nil {
		return nil, fmt.Errorf("ingest bundle %s: %w", bundle, err)
	}
	return &model.Engine{Policies: ps, Groupings: gs}, nil
}
