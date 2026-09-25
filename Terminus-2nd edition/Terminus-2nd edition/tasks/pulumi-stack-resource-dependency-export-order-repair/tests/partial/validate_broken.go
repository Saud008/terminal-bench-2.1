package validate

import (
	"fmt"

	"github.com/terminus/pulumi-dep-export/internal/model"
)

func ValidateSnapshot(snap model.Snapshot) error {
	if snap.Stack == "" {
		return fmt.Errorf("missing stack name")
	}
	if snap.Version == 0 {
		return fmt.Errorf("unsupported snapshot version")
	}
	if len(snap.Resources) == 0 {
		return fmt.Errorf("empty resource list")
	}
	known := map[string]bool{}
	for _, r := range snap.Resources {
		known[r.URN] = true
	}
	for _, r := range snap.Resources {
		for _, dep := range r.Dependencies {
			if !known[dep] {
				return fmt.Errorf("unknown dependency %s", dep)
			}
		}
	}
	return nil
}
